"""Benchmark source adapters. Each one turns a raw snapshot into observation records.

An observation is a dict with: ``benchmark`` (a key from ``config.json``), ``value`` (0 to 100
scale), ``independent`` (bool), ``source`` (adapter name), ``host``, ``url``, ``date``,
``setting`` (harness, effort or column, as the source states it), ``variant`` (a label that
groups the observations of one evaluated configuration) and either ``identities`` (for the
matcher) or ``route`` (a ``gateway:route_id`` key, when the source is already keyed by route).

Adapters know the page structure of their source, never the models on it.
"""
from __future__ import annotations

import gzip
import html as htmllib
import json
import re
from urllib.parse import urlparse

from . import REPO, load_config
from . import flight
from .matcher import Identity

CFG = load_config()
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def benchmark_key(name: str) -> str | None:
    """Map a source's benchmark name onto a configured benchmark key, or None."""
    low = name.lower()
    for pat in CFG["exclude_benchmark_name_matches"]:
        if re.search(pat, low):
            return None
    for key, spec in CFG["benchmarks"].items():
        if any(re.search(p, low) for p in spec["patterns"]):
            return key
    return None


def _num(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*%?\s*$", str(value or ""))
    return float(m.group(1)) if m else None


# --- Artificial Analysis ------------------------------------------------------------------

def _aa_record_obs(rec: dict, scores: dict, date: str, url: str, source: str) -> list[dict]:
    name = rec.get("name") or ""
    release = rec.get("release") or {}
    vendor = rec.get("modelCreatorName") or (rec.get("creator") or {}).get("name") or ""
    identities = [Identity(release.get("slug", ""), "id", vendor),
                  Identity(release.get("name", ""), "name", vendor),
                  Identity(name, "name", vendor)]
    obs = []
    fields = CFG["aa_fields"]
    index = rec.get("intelligenceIndex")
    values = dict(scores)
    if index is not None:
        values["intelligenceIndex"] = index
    for field_name, raw in values.items():
        spec = fields.get(field_name)
        val = _num(raw)
        if not spec or val is None:
            continue
        obs.append({"benchmark": spec["benchmark"], "value": val * spec["scale"], "independent": True,
                    "source": source, "host": "artificialanalysis.ai", "url": url, "date": date,
                    "setting": name, "variant": source + ":" + (rec.get("id") or name),
                    "variant_index": index, "identities": identities})
    return obs


def aa_leaderboard(raw: bytes, entry: dict) -> list[dict]:
    text = flight.stream(raw.decode("utf-8", "replace"))
    records = flight.objects(text, r'\{"id":"' + _UUID + r'","release":', require=("scores",))
    seen, obs = set(), []
    for rec in records:
        if rec["id"] in seen:
            continue
        seen.add(rec["id"])
        obs += _aa_record_obs(rec, rec.get("scores") or {}, entry["fetched_at"][:10], entry["url"], "aa-leaderboard")
    return obs


def aa_snapshot(path, date: str) -> list[dict]:
    """The pinned frontier snapshot (same AA payload, older date), used when the live page fails."""
    data = json.loads(gzip.decompress(path.read_bytes()))
    obs = []
    for rec in data.get("models", []):
        scores = {e.get("slug"): e.get("score") for e in rec.get("intelligenceIndexEvaluations") or []}
        obs += _aa_record_obs(rec, scores, date, "https://artificialanalysis.ai/models", "aa-snapshot")
    return obs


def aa_coding_agents(raw: bytes, entry: dict) -> list[dict]:
    text = flight.stream(raw.decode("utf-8", "replace"))
    obs, seen = [], set()
    for rec in flight.objects(text, r'\{"id":"[0-9a-f]{32}","isDefault"', require=("indexScore",)):
        if rec["id"] in seen or rec.get("indexScore") is None:
            continue
        seen.add(rec["id"])
        model = rec.get("model") or {}
        creators = rec.get("modelCreators") or []
        vendor = creators[0].get("name", "") if creators and isinstance(creators[0], dict) else ""
        identities = [Identity((model.get("release") or {}).get("shortName", ""), "name", vendor),
                      Identity(model.get("name", ""), "name", vendor)]
        obs.append({"benchmark": "aa_coding_agent_index", "value": rec["indexScore"] * 100, "independent": True,
                    "source": "aa-coding-agents", "host": "artificialanalysis.ai", "url": entry["url"],
                    "date": entry["fetched_at"][:10], "setting": rec.get("displayLabel", ""),
                    "variant": "aa-coding-agents:" + rec["id"], "identities": identities})
    return obs


# --- Vals, Terminal-Bench board, KiloBench -----------------------------------------------

def vals_table(raw: bytes, entry: dict, benchmark: str) -> list[dict]:
    page = raw.decode("utf-8", "replace")
    obs = []
    row_re = re.compile(r'<th scope="row">\s*<a href="/models/([^"]+)">([^<]+)</a>\s*</th>\s*<td>([^<]*)</td>\s*<td>([\d.]+)%</td>')
    for slug, name, harness, score in row_re.findall(page):
        vendor, _, model_part = slug.partition("_")
        identities = [Identity(model_part, "id", vendor), Identity(htmllib.unescape(name), "name", vendor)]
        obs.append({"benchmark": benchmark, "value": float(score), "independent": True,
                    "source": "vals", "host": urlparse(entry["url"]).netloc, "url": entry["url"],
                    "date": entry["fetched_at"][:10], "setting": harness.strip(),
                    "variant": "vals:" + slug + ":" + harness.strip(), "identities": identities})
    return obs


def tbench_board(raw: bytes, entry: dict, benchmark: str) -> list[dict]:
    text = flight.stream(raw.decode("utf-8", "replace"))
    obs = []
    for rec in flight.objects(text, r'\{"id":"' + _UUID + r'","leaderboard_id"', require=("metrics", "metadata")):
        meta, metrics = rec["metadata"], rec["metrics"]
        acc = _num(metrics.get("accuracy"))
        model = meta.get("model_display") or {}
        if acc is None or not model:
            continue
        vendor = (meta.get("model_org") or {}).get("label", "")
        identities = [Identity(model.get("label", ""), "name", vendor)]
        link = model.get("url") or ""
        path = urlparse(link).path.strip("/")
        if path.count("/") == 1:
            identities.insert(0, Identity(path, "id", vendor))
        agent = (meta.get("agent_display") or {}).get("label", "")
        obs.append({"benchmark": benchmark, "value": acc, "independent": True, "source": "tbench",
                    "host": urlparse(entry["url"]).netloc, "url": entry["url"],
                    "date": meta.get("date") or entry["fetched_at"][:10],
                    "setting": f"{agent}, effort {meta.get('reasoning_effort')}",
                    "variant": "tbench:" + rec["id"], "identities": identities})
    return obs


def kilobench(raw: bytes, entry: dict, benchmark: str) -> list[dict]:
    text = flight.stream(raw.decode("utf-8", "replace"))
    obs, seen = [], set()
    for rec in flight.objects(text, r'\{"id":"' + _UUID + r'","slug":', require=("completionPercentage", "eval")):
        if rec["id"] in seen:
            continue
        seen.add(rec["id"])
        vendor = rec.get("provider", "")
        identities = [Identity(rec.get("slug", ""), "id", vendor), Identity(rec.get("name", ""), "name", vendor)]
        obs.append({"benchmark": benchmark, "value": float(rec["completionPercentage"]), "independent": True,
                    "source": "kilobench", "host": urlparse(entry["url"]).netloc, "url": entry["url"],
                    "date": entry["fetched_at"][:10], "setting": (rec.get("eval") or {}).get("label", ""),
                    "variant": "kilobench:" + rec["id"], "identities": identities})
    return obs


# --- Transcribed evidence files ----------------------------------------------------------

def evidence_file(spec: dict) -> list[dict]:
    """Records from a hand-transcribed evidence file, keyed by gateway route.

    Only benchmark records are read (name, score, unit, source URL, date, setting). A record
    counts as independent when its source host is an independent evaluator in config.
    """
    data = json.loads((REPO / spec["path"]).read_text())
    gateways = spec["gateway_names"]
    independent_hosts = set(CFG["independent_hosts"])
    aliases = CFG["host_aliases"]
    exclude = [re.compile(p, re.I) for p in CFG["exclude_record_if_setting_matches"]]
    obs = []
    for row in data:
        gateway = gateways.get(row.get("gateway"))
        if not gateway:
            continue
        for b in row.get("benchmarks") or []:
            key = benchmark_key(b.get("benchmark", ""))
            val = _num(b.get("score"))
            if key is None or val is None:
                continue
            setting = b.get("setting") or ""
            if any(p.search(setting) for p in exclude):
                continue
            if b.get("unit") in CFG["evidence_skip_units"]:
                continue
            val *= CFG["evidence_unit_scale"].get(b.get("unit"), 1)
            host = urlparse(b.get("source_url", "")).netloc
            host = aliases.get(host, host)
            obs.append({"benchmark": key, "value": val, "independent": host in independent_hosts,
                        "source": "evidence-file", "host": host, "url": b.get("source_url", ""),
                        "date": b.get("date", ""), "setting": setting,
                        "variant": "evidence:" + host + ":" + setting,
                        "benchmark_name": b.get("benchmark"), "route": f"{gateway}:{row['model_id']}"})
    return obs
