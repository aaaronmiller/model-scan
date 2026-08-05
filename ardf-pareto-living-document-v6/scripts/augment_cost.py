# ---
# title: ARDF Derived Task-Cost Observation Builder
# version: 6.0.0
# created: 2026-07-28
# model: GPT-5.6 Thinking
# reasoning_level: high
# purpose: Generate transparent token-price cost observations before multipoint calibration.
# ---
"""Add reproducible cost-proxy observations to the single canonical CSV.

Why this file exists
====================
The original dashboard only plotted configurations having both a benchmark
capability row and an independently published cost row. That inner join erased
most of the model universe. This script expands *cost coverage* without hiding
how the value was produced.

Two derived sources are emitted:

1. ``aa-token-price-proxy-v6`` uses each Artificial Analysis configuration's
   own evaluation token total and its published 7:2 blended token price.
2. ``standard-task-price-proxy-v6`` uses catalog input/output prices and an
   editable standardized task token profile. It is a low-weight fallback for
   configurations whose model-specific token total is unavailable.

Neither source is treated as ground truth. ``scripts/calibrate.py`` maps both
onto the configured task-cost reference through strict multipoint overlaps.
Rerunning this script is idempotent: previously generated rows are removed
before fresh rows are created.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent.parent
CSV_PATH=ROOT/'data/unified-model-evidence.csv'
CONFIG_PATH=ROOT/'config/calibration-algorithms.json'
SNAPSHOT_PATH=ROOT/'sources/attached-source-snapshots.json'
GENERATED_SOURCE_IDS={'aa-token-price-proxy-v6','standard-task-price-proxy-v6'}


def number(value: Any) -> float | None:
    """Parse a finite number while preserving blanks as missing values."""
    if value is None or str(value).strip().lower() in {'','null','none','n/a','na','-'}:
        return None
    try:
        result=float(str(value).replace(',','').replace('$','').strip())
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def stable_id(*parts: str) -> str:
    """Create deterministic IDs so repeated rebuilds produce byte-stable rows."""
    return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()[:16]


def read_csv(path: Path) -> tuple[list[dict[str,str]],list[str]]:
    with path.open(encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle)
        return list(reader),list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str,Any]], fields: list[str]) -> None:
    """Write atomically so an interrupted rebuild cannot corrupt the evidence ledger."""
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='',delete=False,dir=path.parent,suffix='.tmp') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({field:'' if row.get(field) is None else row.get(field) for field in fields})
        temporary=Path(handle.name)
    temporary.replace(path)


def observation_row(meta: dict[str,str], *, source_id: str, source_label: str,
                    metric_name: str, raw_value: float, raw_unit: str,
                    source_url: str, quality: str, confidence: str,
                    base_weight: float, identity_mapping: str, notes: str,
                    source_date: str='2026-07-20') -> dict[str,Any]:
    """Construct a complete atomic cost observation from catalog metadata."""
    row={key:meta.get(key,'') for key in meta}
    row.update({
        'record_type':'observation',
        'observation_id':stable_id(source_id,meta['model_key'],metric_name),
        'source_id':source_id,
        'source_label':source_label,
        'source_publisher':'ARDF derived from structured upstream fields',
        'source_version':'6.0.0',
        'source_date':source_date,
        'source_url':source_url,
        'source_mirror_url':'sources/attached-source-snapshots.json',
        'retrieved_at':'2026-07-28T00:00:00-07:00',
        'metric_axis':'cost',
        'metric_name':metric_name,
        'raw_value':raw_value,
        'raw_unit':raw_unit,
        'raw_direction':'lower',
        'is_reference_scale':'0',
        'quality':quality,
        'confidence':confidence,
        'base_weight':base_weight,
        'use_in_aggregate':'1',
        'is_historical':'0',
        'identity_mapping':identity_mapping,
        'notes':notes,
    })
    # Calibration outputs are intentionally blank here. calibrate.py owns them.
    for key in list(row):
        if key.startswith('cal_') or key in {'calibrated_score','calibrated_score_unit','calibrated_score_algorithm'}:
            row[key]=''
    return row


def main() -> None:
    rows,fields=read_csv(CSV_PATH)
    config=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    snapshots=json.loads(SNAPSHOT_PATH.read_text(encoding='utf-8'))

    # Remove only rows generated by this script. Raw evidence and catalog rows are immutable.
    rows=[row for row in rows if row.get('source_id') not in GENERATED_SOURCE_IDS]
    catalog={row['model_key']:row for row in rows if row.get('record_type')=='catalog'}

    # Exact display-name/provider crosswalk from the existing AA snapshot import.
    aa_identity=defaultdict(list)
    for row in rows:
        if row.get('record_type')=='observation' and row.get('source_id')=='aa-snapshot-2026-07' and row.get('metric_axis')=='capability':
            key=(row.get('display_name','').strip().casefold(),row.get('provider','').strip().casefold())
            aa_identity[key].append(row['model_key'])

    generated=[]
    token_cfg=config.get('token_price_proxy',{})
    if token_cfg.get('enabled',True):
        raw_rows=snapshots['files']['raw_artificial_analysis_all_models(2).csv']['rows']
        for raw in raw_rows:
            identity=(raw.get('name','').strip().casefold(),raw.get('creator_name','').strip().casefold())
            candidates=aa_identity.get(identity,[])
            if len(candidates)!=1:
                continue
            model_key=candidates[0]
            meta=catalog.get(model_key)
            token_count=number(raw.get(token_cfg.get('token_count_field','indexTokensTotal')))
            blended_price=number(raw.get(token_cfg.get('blended_price_field','price_1m_blended_7_2_1')))
            if not meta or token_count is None or token_count<=0 or blended_price is None or blended_price<=0:
                continue
            proxy=token_count/1_000_000.0*blended_price
            generated.append(observation_row(
                meta,
                source_id=token_cfg['source_id'],
                source_label=token_cfg['source_label'],
                metric_name='aa_token_price_full_suite_proxy_usd',
                raw_value=proxy,
                raw_unit='USD token-price proxy for complete AA evaluation',
                source_url=raw.get('aa_source_url') or 'https://artificialanalysis.ai/',
                quality='derived from structured model-specific token count and price',
                confidence=token_cfg.get('confidence','derived'),
                base_weight=float(token_cfg.get('base_weight',0.65)),
                identity_mapping='Exact AA display-name + provider crosswalk to canonical model_key.',
                notes=(f"Formula: {token_count:g} total evaluation tokens / 1e6 × "
                       f"${blended_price:g} per 1M blended tokens = ${proxy:.12g}. "
                       "The calibration engine maps this full-suite proxy to task-level USD."),
            ))

    task_cfg=config.get('task_cost_estimator',{})
    if task_cfg.get('enabled',True):
        base_in=float(task_cfg.get('base_input_tokens',12000))
        base_out=float(task_cfg.get('base_output_tokens',2500))
        in_mult=task_cfg.get('effort_input_multipliers',{})
        out_mult=task_cfg.get('effort_output_multipliers',{})
        for model_key,meta in sorted(catalog.items()):
            input_price=number(meta.get('input_price_per_m'))
            output_price=number(meta.get('output_price_per_m'))
            if input_price is None or output_price is None or input_price<0 or output_price<0 or (input_price==0 and output_price==0):
                continue
            effort=(meta.get('effort') or 'default').lower()
            input_tokens=base_in*float(in_mult.get(effort,in_mult.get('default',1.0)))
            output_tokens=base_out*float(out_mult.get(effort,out_mult.get('default',1.0)))
            proxy=input_tokens/1_000_000.0*input_price+output_tokens/1_000_000.0*output_price
            generated.append(observation_row(
                meta,
                source_id=task_cfg['source_id'],
                source_label=task_cfg['source_label'],
                metric_name='standardized_task_token_price_proxy_usd',
                raw_value=proxy,
                raw_unit='USD per standardized task token profile',
                source_url='config/calibration-algorithms.json',
                quality='estimated from catalog price and configurable token profile',
                confidence=task_cfg.get('confidence','estimated'),
                base_weight=float(task_cfg.get('base_weight',0.35)),
                identity_mapping='Exact catalog model_key; no cross-effort substitution.',
                notes=(f"Formula: {input_tokens:g} input tokens × ${input_price:g}/1M + "
                       f"{output_tokens:g} output/reasoning-equivalent tokens × ${output_price:g}/1M "
                       f"= ${proxy:.12g}. Effort profile={effort}."),
                source_date='2026-07-28',
            ))

    # Ensure any new fields are represented even when an older CSV lacks them.
    for row in generated:
        for key in row:
            if key not in fields:
                fields.append(key)
    rows.extend(generated)
    write_csv(CSV_PATH,rows,fields)
    counts=defaultdict(int)
    for row in generated:
        counts[row['source_id']]+=1
    print(json.dumps({'rows_after':len(rows),'generated_rows':len(generated),'by_source':dict(counts)},indent=2))


if __name__=='__main__':
    main()
