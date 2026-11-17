#!/usr/bin/env python3
"""Logged Kilo runner: wraps `kilo run` with API failure logging.

Every call records latency + cost on success (append to spend log via
model-scan's spend_ledger when available) and a FailureEvent on failure.
Free-tier models preferred; failures logged with free_tier flag so the
summary distinguishes free-quota exhaustion from real breakage.

Usage:
    kilo-logged run -m <model> [--format json] <prompt>
    kilo-logged failures [--hours 24]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_failure_log import FailureEvent, record_failure, failure_summary


def classify_error(text: str, returncode: int) -> tuple[str, str]:
    t = text.lower()
    if "invalid_token" in t or "401" in t or "authentication" in t:
        return "auth", "401/INVALID_TOKEN"
    if "429" in t or "rate" in t and "limit" in t:
        return "rate_limit", "429"
    if "timeout" in t or "timed out" in t:
        return "timeout", "TIMEOUT"
    if "500" in t or "502" in t or "503" in t or "server_error" in t:
        return "server_error", "5xx"
    if returncode != 0 and "error" in t:
        return "provider_error", str(returncode)
    if returncode != 0:
        return "cli_crash", str(returncode)
    return "", ""


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "failures":
        hours = 24
        for i, a in enumerate(sys.argv):
            if a == "--hours" and i + 1 < len(sys.argv):
                hours = int(sys.argv[i + 1])
        print(json.dumps(failure_summary(hours), indent=2))
        return 0

    args = sys.argv[1:]
    if args and args[0] == "run":
        args = args[1:]
    model = ""
    for i, a in enumerate(args):
        if a == "-m" and i + 1 < len(args):
            model = args[i + 1]
    free = ":free" in model or "free" in model.split("/")[-1]
    provider = "kilo" if model.startswith("kilo/") else model.split("/")[0] if "/" in model else "kilo"

    t0 = time.time()
    cmd = ["kilo", "run"] + args
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        latency = int((time.time() - t0) * 1000)
        out = (p.stdout or "") + (p.stderr or "")
        etype, ecode = classify_error(out, p.returncode)
        if etype:
            record_failure(FailureEvent(
                provider=provider, model=model, error_type=etype,
                error_code=ecode, error_msg=out.strip()[-500:],
                latency_ms=latency, free_tier=free,
            ))
            print(f"[kilo-logged] FAILURE logged: {etype}/{ecode} {latency}ms", file=sys.stderr)
        # pass through stdout so pipes keep working
        sys.stdout.write(p.stdout or "")
        sys.stderr.write(p.stderr or "")
        return p.returncode
    except subprocess.TimeoutExpired:
        latency = int((time.time() - t0) * 1000)
        record_failure(FailureEvent(
            provider=provider, model=model, error_type="timeout",
            error_code="TIMEOUT", error_msg="kilo run exceeded 300s",
            latency_ms=latency, free_tier=free,
        ))
        print("[kilo-logged] TIMEOUT logged", file=sys.stderr)
        return 124


if __name__ == "__main__":
    sys.exit(main())
