#!/usr/bin/env python3
"""Refresh Artificial Analysis observations into the ARDF ledger.

Authorization
-------------
AA is the privileged reference scale for the whole ARDF calibration, and its
data was already in use while REQ-2.1's "when authorized" clause sat formally
unresolved. Resolved 2026-08-20: the operator authorized retrieval, and the
official route is the documented v2 API with an `x-api-key` header and a free
tier of 1000 calls per day. No scraping is performed, and none is needed.

    https://artificialanalysis.ai/api/v2/data/llms/models

The key comes from `AA_API_KEY` in the environment. It is never written to disk
and never printed.

What it emits
-------------
Observation rows in the canonical ledger schema, one per (model, metric):

  capability   aa_intelligence_index, artificial_analysis_coding_index,
               artificial_analysis_math_index
  cost         input_price_per_m, output_price_per_m

The calibration columns are deliberately left empty. `calibrate.py` owns them,
and an empty `cal_robust_affine` is precisely how this pipeline marks a metric
it has not yet calibrated. Writing a value there by hand would corrupt exactly
the distinction that keeps uncalibrated metrics out of the aggregate.

Why this matters
----------------
The prior AA snapshot was retrieved 2026-08-04. ARDF scores roughly 176 of the
791 models reachable on this machine, so most of the field has never been
measured at all.

Usage
-----
    refresh_aa.py                 dry run, prints what would change
    refresh_aa.py --apply         append to the ledger
    refresh_aa.py --out FILE      write the new rows to a separate CSV
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "data" / "unified-model-evidence.csv"
API = "https://artificialanalysis.ai/api/v2/data/llms/models"

SOURCE_ID = "artificial-analysis-api-v2"

# metric_name -> (axis, evaluations key, unit, is_reference_scale)
CAPABILITY_METRICS = {
    "aa_intelligence_index": ("artificial_analysis_intelligence_index",
                              "AA Intelligence Index", "1"),
    "aa_coding_index":       ("artificial_analysis_coding_index",
                              "AA Coding Index", "0"),
    "aa_math_index":         ("artificial_analysis_math_index",
                              "AA Math Index", "0"),
}


def fetch() -> list[dict]:
    key = os.environ.get("AA_API_KEY", "").strip()
    if not key:
        sys.exit("AA_API_KEY is not set. Sign in at artificialanalysis.ai/login "
                 "for a free-tier key, then export it.")
    req = urllib.request.Request(API, headers={"x-api-key": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = json.loads(r.read())
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def obs_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]


def rows_for(model: dict, now: str, fields: list[str]) -> list[dict]:
    slug = (model.get("slug") or "").strip()
    name = (model.get("name") or slug).strip()
    if not slug:
        return []
    creator = model.get("model_creator")
    creator = (creator.get("name") if isinstance(creator, dict) else creator) or ""
    pricing = model.get("pricing") or {}
    evals = model.get("evaluations") or {}
    out = []

    def base(metric, axis, value, unit, ref, direction="higher"):
        r = {f: "" for f in fields}
        r.update({
            "record_type": "observation",
            "observation_id": obs_id(SOURCE_ID, slug, metric),
            "model_key": slug,
            "display_name": name,
            "provider": creator,
            "family": name,
            "effort": "default",
            "harness": "general-api",
            "release_date": model.get("release_date") or "",
            "availability": "observed",
            "input_price_per_m": pricing.get("price_1m_input_tokens") or "",
            "output_price_per_m": pricing.get("price_1m_output_tokens") or "",
            "official_model_id": model.get("id") or slug,
            "source_id": SOURCE_ID,
            "source_label": "Artificial Analysis API v2",
            "source_publisher": "Artificial Analysis",
            "source_version": f"api v2 retrieved {now[:10]}",
            "source_url": f"https://artificialanalysis.ai/models/{slug}",
            "retrieved_at": now,
            "metric_axis": axis,
            "metric_name": metric,
            "raw_value": value,
            "raw_unit": unit,
            "raw_direction": direction,
            "is_reference_scale": ref,
            "quality": "structured-attached",
            "confidence": "direct",
            "base_weight": "1.0",
            "use_in_aggregate": "1",
            "is_historical": "0",
            "identity_mapping": "aa-slug",
            "is_vendor_reported": "0",
            "is_independent_source": "1",
            "data_freshness_class": "current",
            "notes": "Retrieved from the authorized AA v2 API. Calibration "
                     "columns intentionally empty; calibrate.py owns them.",
        })
        return r

    for metric, (evkey, unit, ref) in CAPABILITY_METRICS.items():
        v = evals.get(evkey)
        if v is not None:
            out.append(base(metric, "capability", v, unit, ref))

    for metric, pkey, unit in (
        ("input_price_per_m", "price_1m_input_tokens", "USD per 1M tokens"),
        ("output_price_per_m", "price_1m_output_tokens", "USD per 1M tokens"),
    ):
        v = pricing.get(pkey)
        if v is not None and v != "":
            out.append(base(metric, "cost", v, unit, "0", direction="lower"))

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()

    with LEDGER.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        existing = list(reader)

    have = {(r.get("model_key"), r.get("metric_name")) for r in existing
            if r.get("source_id") == SOURCE_ID}
    known_models = {r.get("model_key") for r in existing}

    models = fetch()
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    new_rows, new_models = [], set()
    for m in models:
        for r in rows_for(m, now, fields):
            if (r["model_key"], r["metric_name"]) in have:
                continue
            new_rows.append(r)
            if r["model_key"] not in known_models:
                new_models.add(r["model_key"])

    print(f"AA API returned      : {len(models)} models")
    print(f"ledger rows before   : {len(existing)}")
    print(f"new observation rows : {len(new_rows)}")
    print(f"models never seen    : {len(new_models)}")
    if new_models:
        print("  e.g. " + ", ".join(sorted(new_models)[:8]))

    if a.out:
        p = Path(a.out)
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(new_rows)
        print(f"wrote {p}")

    if not a.apply:
        print("\nDRY RUN. Re-run with --apply to append to the ledger.")
        return 0

    backup = LEDGER.with_suffix(f".csv.bak-{dt.datetime.now():%Y%m%dT%H%M%S}")
    shutil.copy2(LEDGER, backup)
    with LEDGER.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=fields).writerows(new_rows)
    print(f"\nAPPENDED {len(new_rows)} rows. Backup at {backup.name}")
    print("Now run: python3 calibrate.py --skip-cost-augmentation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
