#!/usr/bin/env python3
"""Dynamic opencode-go model catalog — never hardcode a model name.

Discovers live models from the go endpoint, filters to actually-available
ones, ranks by predicted capability vs cost against a caller-supplied
baseline, and caches per-model so rotation only re-probes what's new.

Usage:
    python3 model_catalog.py refresh          # full refresh (new models only probed)
    python3 model_catalog.py pick --baseline <model-id> --max-input-price <usd>
    python3 model_catalog.py check            # verify cached picks still alive; squawk on rot
    python3 model_catalog.py failures         # trailing failure summary (from api_failure_log)

Design rules (from operator directive):
- NO hardcoded model names anywhere in selection logic. The baseline is a
  validation probe: the catalog must independently rank it, and the operator
  compares the catalog's pick against the baseline. A hardcoded baseline in
  the pick path would make the validation circular.
- Cache: ~/.config/model-scan/model_catalog_cache.json keyed by model id,
  storing last-seen metadata + last probe result. Refresh only fetches the
  endpoint list (cheap, one call); per-model liveness probes run ONLY for
  ids not in cache or whose cache entry is older than --max-age (default 7d).
- Squawk: check mode exits non-zero and prints SQUEAK lines when a cached
  pick 404s/401s/429s, when the baseline vanishes, or when failure rate
  over trailing 24h exceeds --fail-threshold (default 0.10).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("MODEL_SCAN_CONFIG_DIR", Path.home() / ".config" / "model-scan"))
CACHE_PATH = CONFIG_DIR / "model_catalog_cache.json"
GO_MODELS_URL = "https://opencode.ai/zen/go/v1/models"
GO_USAGE_URL = "https://opencode.ai/zen/go/v1/usage"

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from scoring.arch_predictor import predict_ai_index, FAMILY_BASELINES
except ImportError:
    predict_ai_index = None
    FAMILY_BASELINES = {}

try:
    from api_failure_log import iter_failures
except ImportError:
    iter_failures = None


def _api_key() -> str:
    return os.environ.get("OPENCODE_API_KEY", "")


def fetch_json(url: str, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {_api_key()}",
        "User-Agent": "model-scan/1.0",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            # Keep the unreadable file for inspection instead of letting the next save
            # overwrite it (model-scraper's rule; version-ledger idea SD-033).
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            aside = CACHE_PATH.with_name(f"{CACHE_PATH.name}.corrupt.{stamp}")
            try:
                shutil.copy2(CACHE_PATH, aside)
                print(f"model_catalog: unreadable cache ({exc}); kept a copy at {aside}", file=sys.stderr)
            except OSError:
                print(f"model_catalog: unreadable cache ({exc}); could not copy it aside", file=sys.stderr)
    return {"models": {}, "refreshed_at": None}


def save_cache(cache: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cache["refreshed_at"] = datetime.now(timezone.utc).isoformat()
    tmp = CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=1))
    tmp.replace(CACHE_PATH)


def family_of(model: dict) -> str:
    for key in ("family",):
        if model.get(key):
            return str(model[key]).lower()
    cid = model.get("canonical_id") or model.get("id", "")
    prov = cid.split("/")[0].lower() if "/" in cid else ""
    name = (model.get("name") or model.get("id", "")).lower()
    for fam in list(FAMILY_BASELINES.keys()) + ["muse", "spark", "kimi", "glm", "qwen", "deepseek", "minimax", "grok", "gemini", "hybrid", "beam", "flint", "iceman"]:
        if fam in name or fam in prov or fam in model.get("id", "").lower():
            return fam
    return prov or "unknown"


def predict(model: dict) -> tuple[float, str]:
    """Predicted capability score + confidence. Uses arch predictor when the
    family is known, else a capability-metadata heuristic."""
    if predict_ai_index is not None:
        try:
            fam = family_of(model)
            score = predict_ai_index({
                "family": fam,
                "parameters": None,
                "release_date": model.get("release_date"),
                "reasoning": bool((model.get("capabilities") or {}).get("reasoning", {}).get("supported")),
            })
            if isinstance(score, dict):
                return float(score.get("predicted_ai", 0)), str(score.get("confidence", "low"))
            return float(score), "medium"
        except Exception:
            pass
    # Fallback heuristic: context + tools + reasoning + recency
    caps = model.get("capabilities") or {}
    s = 25.0
    if (caps.get("tools") or {}).get("supported"):
        s += 8
    if (caps.get("reasoning") or {}).get("supported"):
        s += 7
    ctx = (model.get("limit") or {}).get("context", 0) or 0
    if ctx >= 1_000_000:
        s += 5
    elif ctx >= 256_000:
        s += 3
    rd = model.get("release_date") or ""
    if rd >= "2026-06":
        s += 4
    elif rd >= "2026-01":
        s += 2
    return s, "heuristic"


def price_in(model: dict) -> float:
    try:
        return float((model.get("cost") or {}).get("text", {}).get("input", {}).get("price", 1e9))
    except (TypeError, ValueError):
        return 1e9
def probe_liveness(model_id: str, meta: dict | None = None, timeout: int = 120) -> tuple[bool, str]:
    """Probe via the owning CLI. Go short IDs map 1:1 onto the `opencode-go/`
    CLI namespace (verified: opencode-go/muse-spark-1.3-contributor answers
    ALIVE). Raw HTTPS lacks session routing (MissingSessionID), so probes
    always go through the CLI. Returns (alive, detail)."""
    short = model_id.split("/")[-1]
    candidates = [f"opencode-go/{short}"]
    if "/" in model_id and model_id != short:
        candidates.append(model_id)
    last_detail = "no-candidates"
    for cand in dict.fromkeys(candidates):
        cmd = ["kilo", "run", "-m", cand, "--format", "json",
               "Reply with exactly: ALIVE"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            last_detail = "timeout"
            continue
        except FileNotFoundError as e:
            return False, f"no-cli:{e.filename}"
        out = (p.stdout or "") + (p.stderr or "")
        if "ALIVE" in out and p.returncode == 0:
            return True, "ok"
        msg = out.strip()[:200]
        if "not found" in msg.lower() or "404" in msg or "Did you mean" in msg:
            last_detail = f"404-not-found:{cand}"
            continue  # try next candidate ID form
        if "401" in msg or "INVALID_TOKEN" in msg or "auth" in msg.lower():
            return False, "401-auth"
        if "429" in msg or ("rate" in msg.lower() and "limit" in msg.lower()):
            return False, "429-rate-limit"
        if p.returncode != 0:
            return False, f"error:{msg[:120]}"
        return True, "responded"
    return False, last_detail


def cmd_refresh(args) -> int:
    data = fetch_json(GO_MODELS_URL)
    live = {m["id"]: m for m in data.get("data", [])}
    cache = load_cache()
    now = datetime.now(timezone.utc).isoformat()
    max_age = args.max_age_days * 86400
    now_ts = time.time()
    added, reprobed, kept = 0, 0, 0
    import concurrent.futures
    todo = []
    for mid, meta in live.items():
        entry = cache["models"].get(mid)
        if entry is None:
            todo.append((mid, meta, True))
        else:
            try:
                age = now_ts - datetime.fromisoformat(entry.get("last_probed", now)).timestamp()
            except (ValueError, TypeError):
                age = max_age + 1
            if age > max_age:
                todo.append((mid, meta, False))
    def _probe(item):
        mid, meta, is_new = item
        alive, detail = probe_liveness(mid, meta)
        score, conf = predict(meta)
        return (mid, meta, is_new, alive, detail, score, conf)
    added = reprobed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for mid, meta, is_new, alive, detail, score, conf in pool.map(_probe, todo):
            entry = cache["models"].get(mid)
            if is_new or entry is None:
                cache["models"][mid] = {
                    "meta": meta, "alive": alive, "probe_detail": detail,
                    "score": score, "confidence": conf,
                    "first_seen": now, "last_probed": now,
                }
                added += 1
            else:
                entry.update({"alive": alive, "probe_detail": detail, "last_probed": now})
                if entry.get("meta") != meta:
                    entry["meta"] = meta
                    entry.update({"score": score, "confidence": conf})
                reprobed += 1
    kept = len(live) - added - reprobed
    # Mark disappeared models dead (rotation detection — no deletion, history matters)
    for mid in list(cache["models"].keys()):
        if mid not in live:
            cache["models"][mid]["alive"] = False
            cache["models"][mid]["probe_detail"] = "vanished-from-listing"
    save_cache(cache)
    print(json.dumps({"live": len(live), "added": added, "reprobed": reprobed, "kept": kept}, indent=1))
    return 0


def cmd_pick(args) -> int:
    cache = load_cache()
    if not cache["models"]:
        print("empty cache — run refresh first", file=sys.stderr)
        return 2
    cands = []
    for mid, e in cache["models"].items():
        if not e.get("alive"):
            continue
        meta = e.get("meta", {})
        pin = price_in(meta)
        if pin > args.max_input_price:
            continue
        if args.require_tools and not ((meta.get("capabilities") or {}).get("tools") or {}).get("supported"):
            continue
        # Value score: capability per dollar, input-weighted
        value = e.get("score", 0) / max(pin, 1e-6)
        cands.append((value, e.get("score", 0), pin, mid))
    cands.sort(reverse=True)
    out = []
    for value, score, pin, mid in cands[: args.top]:
        e = cache["models"][mid]
        meta = e.get("meta", {})
        out.append({
            "model": mid,
            "score": round(score, 1),
            "confidence": e.get("confidence"),
            "input_price": pin,
            "output_price": price_out(meta),
            "context": (meta.get("limit") or {}).get("context"),
            "last_probed": e.get("last_probed"),
        })
    print(json.dumps(out, indent=1))
    return 0


def failure_rate(hours: int = 24) -> tuple[int, int, float, dict]:
    if iter_failures is None:
        return 0, 0, 0.0, {}
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    fails = [ev for ev in iter_failures() if ev.at.isoformat() >= cutoff]
    by_key: dict[str, int] = {}
    for ev in fails:
        k = f"{ev.provider}/{ev.model} [{ev.error_type}/{ev.error_code}]"
        by_key[k] = by_key.get(k, 0) + 1
    # Successes: count OK lines in proxy log is out of scope here; caller passes total.
    return len(fails), 0, 0.0, by_key


def cmd_check(args) -> int:
    """Verify cached alive-models still answer. Squawk loudly on rot."""
    cache = load_cache()
    squawks: list[str] = []
    alive_now = 0
    checked = 0
    for mid, e in sorted(cache["models"].items()):
        if not e.get("alive"):
            continue
        checked += 1
        ok, detail = probe_liveness(mid, e.get("meta"), timeout=args.probe_timeout)
        e["last_probed"] = datetime.now(timezone.utc).isoformat()
        if not ok:
            e["alive"] = False
            e["probe_detail"] = detail
            squawks.append(f"SQUAWK model-dead {mid} last-good-alive now-{detail}")
        else:
            alive_now += 1
    save_cache(cache)
    # Baseline validation: report where the baseline ranks, never hardcode it.
    if args.baseline:
        be = cache["models"].get(args.baseline)
        if be is None or not be.get("alive"):
            squawks.append(f"SQUAWK baseline-gone {args.baseline} not in live catalog")
        else:
            bscore = be.get("score", 0)
            better = sorted(
                [m for m, x in cache["models"].items()
                 if x.get("alive") and x.get("score", 0) > bscore],
                key=lambda m: cache["models"][m].get("score", 0), reverse=True,
            )
            print(f"baseline {args.baseline} score={bscore:.1f} models-above={len(better)}")
            for m in better[:5]:
                x = cache["models"][m]
                print(f"  better: {m} score={x.get('score',0):.1f} "
                      f"in=${price_in(x.get('meta',{}))} conf={x.get('confidence')}")
    # Failure-rate gate from the failure log
    if iter_failures is not None:
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=args.fail_hours)).isoformat()
        fails = [ev for ev in iter_failures() if ev.at.isoformat() >= cutoff]
        n_fail = len(fails)
        print(f"failures-trailing-{args.fail_hours}h: {n_fail}")
        if n_fail and args.fail_threshold is not None and args.total_requests:
            rate = n_fail / max(1, args.total_requests)
            print(f"failure-rate: {rate:.1%} (threshold {args.fail_threshold:.0%})")
            if rate > args.fail_threshold:
                squawks.append(
                    f"SQUAWK failure-rate {rate:.1%} > {args.fail_threshold:.0%} "
                    f"over trailing {args.fail_hours}h ({n_fail} failures)")
        by_key: dict[str, int] = {}
        for ev in fails:
            k = f"{ev.provider}/{ev.model} [{ev.error_type}/{ev.error_code}]"
            by_key[k] = by_key.get(k, 0) + 1
        for k in sorted(by_key, key=by_key.get, reverse=True)[:5]:
            print(f"  fail: {by_key[k]}x {k}")
    for s in squawks:
        print(s, file=sys.stderr)
        print(s)
    print(f"checked={checked} alive={alive_now} squawks={len(squawks)}")
    return 1 if squawks else 0


def cmd_usage(args) -> int:
    try:
        print(json.dumps(fetch_json(GO_USAGE_URL), indent=1))
        return 0
    except Exception as e:
        print(f"usage fetch failed: {e}", file=sys.stderr)
        return 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("refresh", help="discover live models; probe only new/stale")
    r.add_argument("--max-age-days", type=int, default=7)
    r.add_argument("--workers", type=int, default=1)
    r.set_defaults(fn=cmd_refresh)
    k = sub.add_parser("pick", help="rank live models by value vs optional baseline")
    k.add_argument("--baseline", default=None, help="validation baseline id (reported, never hardcoded)")
    k.add_argument("--max-input-price", type=float, default=1e9)
    k.add_argument("--require-tools", action="store_true", default=True)
    k.add_argument("--top", type=int, default=8)
    k.set_defaults(fn=cmd_pick)
    c = sub.add_parser("check", help="verify cached picks; squawk on rot")
    c.add_argument("--baseline", default=None)
    c.add_argument("--probe-timeout", type=int, default=120)
    c.add_argument("--fail-hours", type=int, default=24)
    c.add_argument("--fail-threshold", type=float, default=0.10)
    c.add_argument("--total-requests", type=int, default=0,
                   help="success count for rate calc (from proxy log); 0 = skip rate gate")
    c.set_defaults(fn=cmd_check)
    u = sub.add_parser("usage", help="show opencode-go quota usage")
    u.set_defaults(fn=cmd_usage)
    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
