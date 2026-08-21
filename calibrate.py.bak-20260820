# ---
# title: ARDF Multipoint Calibration and Display-Data Engine
# version: 7.3-refined
# refined: 2026-08-09 — policy top_end diagnostic alignment, typo fixes, empty-field documentation
# created: 2026-08-04
# model: GPT-5.6 Sol
# reasoning_level: high
# purpose: Calibrate the canonical ledger, rebuild decision documents, embed dashboard data, and validate the consolidated package.
# ---
"""Calibrate heterogeneous model evidence onto common capability and cost axes.

Design contract
===============
The CSV is the canonical evidence ledger. This script performs every scale
transformation outside the dashboards. The dashboards may filter and aggregate
already-calibrated observations, but they never estimate calibration mappings.

A calibration group is ``metric_axis × source_id × metric_name``. Its automatic
anchors are exact ``model_key`` overlaps with the configured reference metric.
Manual anchors from the JSON configuration are added explicitly and remain
inspectable. Missing or insufficient anchors produce blank calibration fields,
never zeros or invented coordinates.

The script is standard-library-only so future agents can run it anywhere Python
3.11+ is available. It writes atomically and can safely target the input path. Derived browser payloads are embedded directly into dashboard.html; no generated sidecar directory exists.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
import math
import statistics
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

NUMBER_BLANKS = {'', 'null', 'none', 'na', 'n/a', '-'}


def number(value: Any) -> float | None:
    """Parse a finite floating-point value without treating blanks as zero."""
    if value is None or str(value).strip().lower() in NUMBER_BLANKS:
        return None
    try:
        result = float(str(value).strip().replace(',', '').replace('$', '').replace('%', ''))
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}


def weighted_mean(values: Iterable[tuple[float, float]]) -> float | None:
    pairs=[(v,max(w,0.0)) for v,w in values if math.isfinite(v) and math.isfinite(w) and w>0]
    total=sum(w for _,w in pairs)
    return sum(v*w for v,w in pairs)/total if total else None


def weighted_geometric_mean(values: Iterable[tuple[float, float]]) -> float | None:
    pairs=[(v,max(w,0.0)) for v,w in values if v>0 and math.isfinite(v) and math.isfinite(w) and w>0]
    total=sum(w for _,w in pairs)
    return math.exp(sum(math.log(v)*w for v,w in pairs)/total) if total else None


def weighted_median(values: list[tuple[float, float]]) -> float:
    ordered=sorted((v,max(w,0.0)) for v,w in values)
    total=sum(w for _,w in ordered)
    if total<=0: return statistics.median(v for v,_ in ordered)
    cursor=0.0
    for value,weight in ordered:
        cursor += weight
        if cursor >= total/2: return value
    return ordered[-1][0]


def transform(value: float, axis: str) -> float:
    """Cost relationships are multiplicative, so fit them in log space."""
    if axis == 'cost':
        if value <= 0: raise ValueError('Cost anchors must be positive for log10 calibration.')
        return math.log10(value)
    return value


def inverse_transform(value: float, axis: str) -> float:
    return 10 ** value if axis == 'cost' else value


def clip_output(value: float, axis: str, params: dict[str, Any]) -> float:
    if axis == 'capability':
        return min(float(params.get('clip_capability_max', 100.0)), max(float(params.get('clip_capability_min', 0.0)), value))
    return max(float(params.get('cost_floor', 1e-9)), value)


def solve_weighted_line(points: list[tuple[float,float,float]]) -> tuple[float,float]:
    """Closed-form weighted least-squares line; falls back to a flat median."""
    sw=sum(w for _,_,w in points)
    if sw<=0: return 0.0, statistics.median(y for _,y,_ in points)
    mx=sum(x*w for x,_,w in points)/sw
    my=sum(y*w for _,y,w in points)/sw
    sxx=sum(w*(x-mx)**2 for x,_,w in points)
    if sxx <= 1e-18: return 0.0, my
    slope=sum(w*(x-mx)*(y-my) for x,y,w in points)/sxx
    return slope, my-slope*mx


def fit_theil_sen(points: list[tuple[float,float,float]], params: dict[str,Any]) -> tuple[Callable[[float],float],dict[str,Any]]:
    limit=int(params.get('maximum_pairwise_slopes',30000))
    slopes=[]
    n=len(points)
    # Deterministic stride sampling bounds O(n²) memory for future large anchor sets.
    total_pairs=n*(n-1)//2
    stride=max(1, math.ceil(total_pairs/max(limit,1)))
    pair_index=0
    for i in range(n):
        xi,yi,_=points[i]
        for j in range(i+1,n):
            xj,yj,_=points[j]
            if pair_index % stride == 0 and abs(xj-xi)>1e-15:
                slopes.append((yj-yi)/(xj-xi))
            pair_index += 1
    slope=statistics.median(slopes) if slopes else 0.0
    intercept=weighted_median([(y-slope*x,w) for x,y,w in points])
    return lambda x:slope*x+intercept, {'slope':slope,'intercept':intercept,'sampled_slopes':len(slopes)}


def fit_huber(points: list[tuple[float,float,float]], params: dict[str,Any]) -> tuple[Callable[[float],float],dict[str,Any]]:
    slope,intercept=solve_weighted_line(points)
    delta=float(params.get('huber_delta',1.35))
    tolerance=float(params.get('convergence_tolerance',1e-8))
    max_iter=int(params.get('maximum_iterations',80))
    iterations=0
    for iterations in range(1,max_iter+1):
        residuals=[y-(slope*x+intercept) for x,y,_ in points]
        center=statistics.median(residuals)
        mad=statistics.median(abs(r-center) for r in residuals)
        scale=max(1.4826*mad,1e-9)
        adjusted=[]
        for (x,y,base),residual in zip(points,residuals):
            z=abs(residual)/scale
            robust=1.0 if z<=delta else delta/z
            adjusted.append((x,y,base*robust))
        new_slope,new_intercept=solve_weighted_line(adjusted)
        if abs(new_slope-slope)+abs(new_intercept-intercept)<tolerance:
            slope,intercept=new_slope,new_intercept
            break
        slope,intercept=new_slope,new_intercept
    return lambda x:slope*x+intercept, {'slope':slope,'intercept':intercept,'iterations':iterations,'huber_delta':delta}


def isotonic_knots(points: list[tuple[float,float,float]]) -> list[tuple[float,float,float]]:
    """Weighted pool-adjacent-violators followed by one knot per source value."""
    grouped: dict[float,list[tuple[float,float]]] = defaultdict(list)
    for x,y,w in points: grouped[x].append((y,w))
    blocks=[]
    for x in sorted(grouped):
        weight=sum(w for _,w in grouped[x])
        mean=weighted_mean(grouped[x])
        blocks.append({'xs':[x],'weight':weight,'mean':float(mean)})
        while len(blocks)>=2 and blocks[-2]['mean']>blocks[-1]['mean']:
            right=blocks.pop(); left=blocks.pop()
            weight=left['weight']+right['weight']
            mean=(left['mean']*left['weight']+right['mean']*right['weight'])/weight
            blocks.append({'xs':left['xs']+right['xs'],'weight':weight,'mean':mean})
    knots=[]
    for block in blocks:
        per_weight=block['weight']/len(block['xs'])
        for x in block['xs']: knots.append((x,block['mean'],per_weight))
    return sorted(knots)


def fit_monotone(points: list[tuple[float,float,float]], params: dict[str,Any]) -> tuple[Callable[[float],float],dict[str,Any]]:
    knots=isotonic_knots(points)
    slopes=[]
    for (x1,y1,_),(x2,y2,_) in zip(knots,knots[1:]):
        if x2>x1: slopes.append((y2-y1)/(x2-x1))
    nonnegative=[s for s in slopes if s>=0]
    typical=statistics.median(nonnegative) if nonnegative else 0.0
    cap=float(params.get('edge_slope_cap_multiplier',2.0))*typical
    left_slope=min(max(slopes[0] if slopes else 0.0,0.0),cap) if cap>0 else max(slopes[0] if slopes else 0.0,0.0)
    right_slope=min(max(slopes[-1] if slopes else 0.0,0.0),cap) if cap>0 else max(slopes[-1] if slopes else 0.0,0.0)
    def predict(x: float) -> float:
        if len(knots)==1: return knots[0][1]
        if x<=knots[0][0]: return knots[0][1]+left_slope*(x-knots[0][0])
        if x>=knots[-1][0]: return knots[-1][1]+right_slope*(x-knots[-1][0])
        for (x1,y1,_),(x2,y2,_) in zip(knots,knots[1:]):
            if x1<=x<=x2:
                if x2==x1: return (y1+y2)/2
                return y1+(y2-y1)*(x-x1)/(x2-x1)
        return knots[-1][1]
    return predict, {'knot_count':len(knots),'edge_slopes':[left_slope,right_slope],'knots':[[x,y] for x,y,_ in knots]}

FITTERS={'theil_sen_affine':fit_theil_sen,'huber_irls_affine':fit_huber,'monotone_piecewise_linear':fit_monotone}

# auto_best_rmse is synthetic: per group it copies the real algorithm with lowest RMSE, handled separately in calibrate()


def read_rows(path: Path) -> tuple[list[dict[str,str]],list[str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); return list(reader),list(reader.fieldnames or [])


def write_rows_atomic(path: Path, rows: list[dict[str,Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='',delete=False,dir=path.parent,suffix='.tmp') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); writer.writeheader()
        for row in rows: writer.writerow({k:'' if row.get(k) is None else row.get(k) for k in fields})
        temporary=Path(f.name)
    temporary.replace(path)


def reference_values(rows: list[dict[str,str]], axis: str, metric: str) -> dict[str,float]:
    """Collapse repeated direct reference observations by weighted median per model."""
    grouped: dict[str,list[tuple[float,float]]] = defaultdict(list)
    for row in rows:
        if row.get('record_type')!='observation' or row.get('metric_axis')!=axis or row.get('metric_name')!=metric: continue
        raw=number(row.get('raw_value')); weight=number(row.get('base_weight')) or 1.0
        if raw is not None: grouped[row['model_key']].append((raw,weight))
    return {key:weighted_median(vals) for key,vals in grouped.items()}


def manual_anchor_points(config: dict[str,Any], group_key: str, axis: str) -> list[tuple[float,float,float,str]]:
    points=[]
    for anchor in config.get('manual_anchors',[]):
        if not anchor.get('enabled',True): continue
        if anchor.get('group_key')!=group_key or anchor.get('metric_axis')!=axis: continue
        x=number(anchor.get('source_value')); y=number(anchor.get('reference_value')); w=number(anchor.get('weight')) or 1.0
        if x is not None and y is not None: points.append((x,y,w,'manual:'+str(anchor.get('label','anchor'))))
    return points


def rmse(points: list[tuple[float,float,float]], predict: Callable[[float],float]) -> float:
    sw=sum(w for _,_,w in points)
    return math.sqrt(sum(w*(predict(x)-y)**2 for x,y,w in points)/sw) if sw else float('nan')


def pareto(models: list[dict[str,Any]], capability_field: str, cost_field: str) -> list[str]:
    candidates=[m for m in models if number(m.get(capability_field)) is not None and number(m.get(cost_field)) is not None and number(m.get(cost_field))>0]
    candidates.sort(key=lambda m:(float(m[cost_field]),-float(m[capability_field]),m['model_key']))
    best=-float('inf'); result=[]
    for model in candidates:
        score=float(model[capability_field])
        if score>best+1e-12:
            result.append(model['model_key']); best=score
    return result


def calibrate(input_path: Path, output_path: Path, config_path: Path) -> dict[str,Any]:
    rows,fields=read_rows(input_path)
    project=json.loads(config_path.read_text(encoding='utf-8'))
    config=project['calibration']
    refs={axis:reference_values(rows,axis,spec['metric_name']) for axis,spec in config['reference_scales'].items()}
    algorithms=[a for a in config['algorithms'] if a.get('enabled',True)]
    for algorithm in algorithms:
        base=algorithm['output_column']
        for suffix in ['', '_status','_anchor_count','_rmse','_group_key']:
            name=base+suffix
            if name not in fields: fields.append(name)
    for name in ['calibrated_score','calibrated_score_unit','calibrated_score_algorithm']:
        if name not in fields: fields.append(name)

    # Comparable benchmark rows may be published by different sites.  The optional
    # calibration_group field says that the raw scales are semantically identical
    # (for example Terminal-Bench 2.1 percentages) while preserving each row's
    # original source_id.  Rows without that field remain isolated by source.
    groups: dict[tuple[str,str],list[int]] = defaultdict(list)
    for index,row in enumerate(rows):
        if row.get('record_type')=='observation' and row.get('metric_axis') in refs:
            calibration_key=(row.get('calibration_group') or '').strip() or f"{row.get('source_id','')}|{row.get('metric_name','')}"
            groups[(row['metric_axis'],calibration_key)].append(index)

    reports=[]
    for (axis,calibration_key),indices in sorted(groups.items()):
        group_key=f'{axis}|{calibration_key}'
        ref_metric=config['reference_scales'][axis]['metric_name']
        metric_names=sorted({rows[i].get('metric_name','') for i in indices})
        source_ids=sorted({rows[i].get('source_id','') for i in indices})
        is_identity=calibration_key==ref_metric or metric_names==[ref_metric]
        source_by_model: dict[str,list[tuple[float,float]]] = defaultdict(list)
        for i in indices:
            raw=number(rows[i].get('raw_value')); weight=number(rows[i].get('base_weight')) or 1.0
            if raw is not None: source_by_model[rows[i]['model_key']].append((raw,weight))
        auto=[]
        if is_identity:
            for key,vals in source_by_model.items():
                raw=weighted_median(vals); auto.append((raw,raw,sum(w for _,w in vals),key))
        else:
            for key,vals in source_by_model.items():
                if key in refs[axis]: auto.append((weighted_median(vals),refs[axis][key],sum(w for _,w in vals),key))
        anchors=auto+manual_anchor_points(config,group_key,axis)
        # Work in transformed space. Invalid nonpositive cost anchors are excluded explicitly.
        transformed=[]
        for x,y,w,label in anchors:
            try: transformed.append((transform(x,axis),transform(y,axis),w,label))
            except ValueError: pass

        real_algorithms=[a for a in algorithms if a.get('kind')!='auto_best_rmse']
        auto_algorithms=[a for a in algorithms if a.get('kind')=='auto_best_rmse']
        # First pass: real fitters
        group_reports={}
        for algorithm in real_algorithms:
            base=algorithm['output_column']; params=algorithm.get('parameters',{}); minimum=int(params.get('minimum_anchors',4))
            status='identity' if is_identity else ('calibrated' if len(transformed)>=minimum else 'insufficient-anchors')
            predictor=None; diagnostics={}
            if is_identity:
                predictor=lambda x:x
            elif len(transformed)>=minimum:
                fitter=FITTERS[algorithm['kind']]
                predictor,diagnostics=fitter([(x,y,w) for x,y,w,_ in transformed],params)
            error=rmse([(x,y,w) for x,y,w,_ in transformed],predictor) if predictor and transformed else float('nan')
            for i in indices:
                row=rows[i]; raw=number(row.get('raw_value'))
                row[base+'_status']=status; row[base+'_anchor_count']=len(transformed); row[base+'_rmse']='' if not math.isfinite(error) else error; row[base+'_group_key']=group_key
                if raw is None or predictor is None: row[base]=''; continue
                try:
                    result=inverse_transform(predictor(transform(raw,axis)),axis)
                    row[base]=clip_output(result,axis,params)
                except (ValueError,OverflowError): row[base]=''
            report={'group_key':group_key,'axis':axis,'source_id':','.join(source_ids),'metric_name':calibration_key,'algorithm_id':algorithm['id'],
                            'output_column':base,'status':status,'anchor_count':len(transformed),'automatic_anchor_count':len(auto),
                            'manual_anchor_count':len(anchors)-len(auto),'rmse_transformed':None if not math.isfinite(error) else error,
                            'diagnostics':diagnostics,'anchors':[{'source_value':x,'reference_value':y,'weight':w,'label':label} for x,y,w,label in anchors]}
            reports.append(report)
            group_reports[algorithm['id']]=report
        # Second pass: synthetic auto-best (lowest RMSE among real)
        for algorithm in auto_algorithms:
            base=algorithm['output_column']; params=algorithm.get('parameters',{})
            # Pick real algorithm with lowest valid RMSE for this group (identity groups all tied)
            best_id=None; best_rmse=float('inf'); best_report=None
            for rid, rep in group_reports.items():
                rmse_v=rep['rmse_transformed']
                if rep['status']=='insufficient-anchors' or rmse_v is None or not math.isfinite(rmse_v):
                    continue
                if rmse_v < best_rmse:
                    best_rmse=rmse_v; best_id=rid; best_report=rep
            if best_report is None:
                # No valid real mapping: mark insufficient and leave blank
                for i in indices:
                    row=rows[i]
                    row[base+'_status']='insufficient-anchors'; row[base+'_anchor_count']=len(transformed); row[base+'_rmse']=''; row[base+'_group_key']=group_key; row[base]=''
                reports.append({'group_key':group_key,'axis':axis,'source_id':','.join(source_ids),'metric_name':calibration_key,'algorithm_id':algorithm['id'],
                            'output_column':base,'status':'insufficient-anchors','anchor_count':len(transformed),'automatic_anchor_count':len(auto),
                            'manual_anchor_count':len(anchors)-len(auto),'rmse_transformed':None,
                            'diagnostics':{'chosen_from':None,'reason':'no valid real algorithm'},'anchors':[{'source_value':x,'reference_value':y,'weight':w,'label':label} for x,y,w,label in anchors]})
            else:
                best_col=next(a['output_column'] for a in real_algorithms if a['id']==best_id)
                best_rmse_val=best_report['rmse_transformed']; best_status=best_report['status']
                for i in indices:
                    row=rows[i]
                    row[base+'_status']=best_status; row[base+'_anchor_count']=len(transformed); row[base+'_rmse']=best_rmse_val; row[base+'_group_key']=group_key
                    raw=number(row.get('raw_value'))
                    # copy calibrated value from best real column
                    val=row.get(best_col,'')
                    if raw is None or val in ('',None):
                        row[base]=''
                    else:
                        try:
                            # re-clip with auto params (same bounds)
                            v=float(val)
                            row[base]=clip_output(v,axis,params)
                        except: row[base]=val
                reports.append({'group_key':group_key,'axis':axis,'source_id':','.join(source_ids),'metric_name':calibration_key,'algorithm_id':algorithm['id'],
                            'output_column':base,'status':best_status,'anchor_count':len(transformed),'automatic_anchor_count':len(auto),
                            'manual_anchor_count':len(anchors)-len(auto),'rmse_transformed':best_rmse_val,
                            'diagnostics':{'chosen_from':best_id,'chosen_column':best_col,'real_rmses':{k:v['rmse_transformed'] for k,v in group_reports.items()}},'anchors':[{'source_value':x,'reference_value':y,'weight':w,'label':label} for x,y,w,label in anchors]})

    active=config['active_algorithm_by_axis']
    algorithm_by_id={a['id']:a for a in algorithms}
    for row in rows:
        axis=row.get('metric_axis')
        if axis not in active: continue
        alg=algorithm_by_id[active[axis]]; value=row.get(alg['output_column'],'')
        row['calibrated_score']=value
        row['calibrated_score_unit']=config['reference_scales'][axis]['unit'] if value not in ('',None) else ''
        row['calibrated_score_algorithm']=alg['id'] if value not in ('',None) else ''

    write_rows_atomic(output_path,rows,fields)

    # Build display payload. Catalog rows provide metadata; observation rows provide evidence.
    catalog={r['model_key']:r for r in rows if r.get('record_type')=='catalog'}
    observation_rows=[r for r in rows if r.get('record_type')=='observation']
    models=[]
    for key in sorted(set(catalog)|{r['model_key'] for r in observation_rows}):
        meta=catalog.get(key,{})
        static_fields=['model_key','display_name','provider','family','effort','harness','release_date','availability','is_open_weights','context_window_tokens','input_price_per_m','output_price_per_m','official_model_id','quality','confidence']
        static_fields += [name for name in fields if name.startswith('models_dev_')]
        item={k:meta.get(k,'') for k in static_fields}
        item['model_key']=key
        if not item.get('display_name'):
            first=next(r for r in observation_rows if r['model_key']==key)
            for k in ['display_name','provider','family','effort','harness']: item[k]=first.get(k,'')
        models.append(item)

    compact_obs=[]
    dynamic_columns=[a['output_column'] for a in algorithms]
    for r in observation_rows:
        compact_base=['observation_id','model_key','display_name','provider','family','effort','harness','release_date','availability','is_open_weights','context_window_tokens','input_price_per_m','output_price_per_m','official_model_id','source_id','source_label','source_publisher','source_version','source_date','source_url','source_mirror_url','retrieved_at','metric_axis','metric_name','raw_value','raw_unit','raw_direction','quality','confidence','base_weight','use_in_aggregate','is_historical','identity_mapping','notes','calibration_group','source_refresh_status','source_original_id','benchmark_domain','benchmark_harness','benchmark_version_exact','is_vendor_reported','is_independent_source','data_freshness_class']
        compact_base += [name for name in fields if name.startswith('models_dev_')]
        compact={k:r.get(k,'') for k in compact_base+dynamic_columns+[name for name in fields if name.startswith(tuple(a['output_column'] for a in algorithms)) and name not in dynamic_columns]}
        compact_obs.append(compact)

    # Default aggregates are precomputed as a fast startup path. The dashboard may
    # recompute weighted means from already-calibrated observations after filters change.
    aggregate_sets={}
    for algorithm in algorithms:
        column=algorithm['output_column']; per_model=defaultdict(lambda:{'capability':[],'cost':[],'sources':set()})
        for r in observation_rows:
            if not truthy(r.get('use_in_aggregate')): continue
            value=number(r.get(column)); weight=number(r.get('base_weight')) or 1.0
            if value is None: continue
            per_model[r['model_key']][r['metric_axis']].append((value,weight)); per_model[r['model_key']]['sources'].add(r['source_id'])
        agg=[]
        for m in models:
            d=per_model[m['model_key']]
            cap=weighted_mean(d['capability']); cost=weighted_geometric_mean(d['cost'])
            agg.append({**m,'capability':cap,'cost':cost,'source_count':len(d['sources']),'capability_observations':len(d['capability']),'cost_observations':len(d['cost'])})
        frontier=set(pareto(agg,'capability','cost'))
        for m in agg: m['frontier']=m['model_key'] in frontier
        aggregate_sets[algorithm['id']]=agg

    sources=[]
    by_source=defaultdict(lambda:{'rows':0,'capability':0,'cost':0,'label':'','url':'','date':''})
    for r in observation_rows:
        d=by_source[r['source_id']]; d['rows']+=1; axis=r.get('metric_axis','other'); d[axis]=d.get(axis,0)+1; d['label']=r['source_label']; d['url']=r['source_url']; d['date']=r.get('source_date','')
    for source_id,d in sorted(by_source.items()): sources.append({'source_id':source_id,**d})

    generated_at = datetime.now(timezone.utc).isoformat()
    payload={'generated_at':generated_at,'config':config,'algorithms':algorithms,'sources':sources,'models':models,'observations':compact_obs,'aggregate_sets':aggregate_sets,'calibration_reports':reports}
    return {'row_count':len(rows),'observation_count':len(observation_rows),'model_count':len(models),'algorithm_count':len(algorithms),'calibration_group_count':len(groups),'reports':reports,'models':models,'aggregate_sets':aggregate_sets,'payload':payload, 'generated_at': generated_at}




ROOT=Path(__file__).resolve().parent
CSV_PATH=ROOT/'data/unified-model-evidence.csv'
CONFIG_PATH=ROOT/'project-config.json'
DASHBOARD_PATH=ROOT/'dashboard.html'
PARETO_PATH=ROOT/'pareto-frontier-cheatsheet.md'
TIERS_PATH=ROOT/'model-tiers-and-contenders.md'
INDEX_PATH=ROOT/'INDEX.md'
TODAY=datetime.now(timezone.utc).date().isoformat()
DEFAULT_TOP_END_PREFIXES=('claude-opus-5-','claude-fable-5-','gpt-5-6-sol-','qwen3-8-max-','kimi-k3-')


MD_DEFAULT_API='https://models.dev/catalog.json'
MD_USER_AGENT='ARDF-Pareto-Living-Document/consolidated (+offline research artifact)'
MD_MODELS_DEV_FIELDS = [
    "models_dev_model_id", "models_dev_name", "models_dev_lab", "models_dev_family",
    "models_dev_description", "models_dev_release_date", "models_dev_last_updated",
    "models_dev_knowledge_cutoff", "models_dev_attachment", "models_dev_reasoning",
    "models_dev_reasoning_options_json", "models_dev_tool_call",
    "models_dev_structured_output", "models_dev_temperature", "models_dev_open_weights",
    "models_dev_license", "models_dev_status", "models_dev_experimental",
    "models_dev_context_tokens", "models_dev_input_limit_tokens", "models_dev_output_limit_tokens",
    "models_dev_input_modalities_json", "models_dev_output_modalities_json",
    "models_dev_interleaved", "models_dev_interleaved_field", "models_dev_provider_count",
    "models_dev_provider_names_json", "models_dev_first_party_input_price_per_m",
    "models_dev_first_party_output_price_per_m", "models_dev_reasoning_price_per_m",
    "models_dev_cache_read_price_per_m", "models_dev_cache_write_price_per_m",
    "models_dev_input_audio_price_per_m", "models_dev_output_audio_price_per_m",
    "models_dev_min_provider_input_price_per_m", "models_dev_max_provider_input_price_per_m",
    "models_dev_min_provider_output_price_per_m", "models_dev_max_provider_output_price_per_m",
    "models_dev_total_parameters", "models_dev_active_parameters", "models_dev_weights_json",
    "models_dev_links_json", "models_dev_benchmarks_json", "models_dev_provider_rows_json",
    "models_dev_match_status", "models_dev_match_method", "models_dev_candidate_id",
    "models_dev_source_url", "models_dev_retrieved_at", "models_dev_sync_notes",
]
def md_compact_json(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def md_as_bool(value: Any) -> str:
    if value is True or value in (1, "1", "true", "yes", "supported"):
        return "1"
    if value is False or value in (0, "0", "false", "no", "unsupported"):
        return "0"
    return ""


def md_first(obj: dict[str, Any], *paths: str, default: Any = "") -> Any:
    """Return the md_first non-empty value from dotted paths."""
    for path in paths:
        cur: Any = obj
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                cur = None
                break
            cur = cur[part]
        if cur not in (None, "", [], {}):
            return cur
    return default


def md_normalize(text: Any) -> str:
    text = str(text or "").lower()
    # Strip provider prefixes and common UI punctuation without removing dated
    # checkpoint identifiers such as 0731 or 20260731.
    text = re.sub(r"^[a-z0-9_.-]+/", "", text)
    text = text.replace("claude-", "claude ").replace("gpt-", "gpt ")
    return re.sub(r"[^a-z0-9]+", "", text)


def md_effortless_key(text: Any) -> str:
    normalized = md_normalize(text)
    for suffix in ("nonreasoning", "minimal", "medium", "xhigh", "high", "default", "low", "max"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def md_fetch_json(url: str, timeout: int) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": MD_USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def md_walk_json(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from md_walk_json(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from md_walk_json(child, path + (str(index),))


def md_looks_like_model(obj: dict[str, Any]) -> bool:
    keys = {str(k).lower() for k in obj}
    has_identity = bool(keys & {"id", "model_id", "modelid", "slug"}) and bool(keys & {"name", "display_name", "displayname"})
    has_specs = bool(keys & {"context", "context_window", "limit", "modalities", "reasoning", "tool_call", "toolcall", "release_date", "release"})
    return has_identity and has_specs


def md_model_records(payload: Any) -> list[dict[str, Any]]:
    """Extract provider-agnostic and provider-specific records from any catalog shape."""
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for path, obj in md_walk_json(payload):
        if not md_looks_like_model(obj):
            continue
        model_id = str(md_first(obj, "id", "model_id", "modelId", "slug"))
        name = str(md_first(obj, "name", "display_name", "displayName", default=model_id))
        provider_hint = ""
        # The nearest non-numeric path component is often a provider or lab ID.
        for component in reversed(path[:-1]):
            if not component.isdigit() and component.lower() not in {"models", "catalog", "data", "providers", "labs"}:
                provider_hint = component
                break
        provider = str(md_first(obj, "provider.id", "provider", "provider_id", default=provider_hint))
        key = (provider, model_id)
        if key in seen:
            continue
        seen.add(key)
        clone = dict(obj)
        clone["__provider_hint"] = provider
        clone["__path"] = list(path)
        records.append(clone)
    return records


def md_number(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip().lower()
    mult = 1.0
    for suffix, factor in (("t", 1e12), ("b", 1e9), ("m", 1e6), ("k", 1e3)):
        if text.endswith(suffix):
            mult = factor
            text = text[:-1]
            break
    try:
        return float(text) * mult
    except ValueError:
        return None


def md_maybe_int(value: Any) -> str:
    n = md_number(value)
    if n is None:
        return ""
    return str(int(n)) if n.is_integer() else str(n)


def md_price(obj: dict[str, Any], kind: str) -> str:
    candidates = {
        "input": ("cost.input", "pricing.input", "md_price.input", "input_price", "inputPrice"),
        "output": ("cost.output", "pricing.output", "md_price.output", "output_price", "outputPrice"),
        "reasoning": ("cost.reasoning", "pricing.reasoning", "reasoning_price", "reasoningPrice"),
        "cache_read": ("cost.cache_read", "pricing.cache_read", "cache_read_price", "cacheReadPrice"),
        "cache_write": ("cost.cache_write", "pricing.cache_write", "cache_write_price", "cacheWritePrice"),
        "input_audio": ("cost.input_audio", "pricing.input_audio", "input_audio_price"),
        "output_audio": ("cost.output_audio", "pricing.output_audio", "output_audio_price"),
    }[kind]
    value = md_first(obj, *candidates)
    return "" if value in (None, "") else str(value)


def md_canonical_id(obj: dict[str, Any]) -> str:
    return str(md_first(obj, "md_canonical_id", "canonicalId", "id", "model_id", "modelId", "slug"))


def md_lab_name(obj: dict[str, Any]) -> str:
    value = md_first(obj, "lab.name", "lab", "organization", "author", "creator", "owned_by")
    if isinstance(value, dict):
        value = md_first(value, "name", "id")
    return str(value or obj.get("__provider_hint", ""))


def md_flatten_model(obj: dict[str, Any], provider_rows: list[dict[str, Any]], retrieved_at: str, source_url: str) -> dict[str, str]:
    providers = sorted({str(md_first(r, "provider.name", "provider.id", "provider", default=r.get("__provider_hint", ""))) for r in provider_rows if md_first(r, "provider.name", "provider.id", "provider", default=r.get("__provider_hint", ""))})
    input_prices = [md_number(md_price(r, "input")) for r in provider_rows]
    output_prices = [md_number(md_price(r, "output")) for r in provider_rows]
    input_prices = [v for v in input_prices if v is not None and v >= 0]
    output_prices = [v for v in output_prices if v is not None and v >= 0]

    limits = md_first(obj, "limit", "limits", default={})
    modalities = md_first(obj, "modalities", default={})
    input_modalities = md_first(obj, "modalities.input", "input_modalities", "inputModalities", default=[])
    output_modalities = md_first(obj, "modalities.output", "output_modalities", "outputModalities", default=[])
    if isinstance(modalities, list) and not input_modalities:
        input_modalities = modalities
    reasoning_options = md_first(obj, "reasoning.options", "reasoning_options", "reasoningOptions", default=[])
    weights = md_first(obj, "weights", "architecture", default={})
    total_parameters = md_first(obj, "parameters.total", "total_parameters", "totalParameters", "params.total")
    active_parameters = md_first(obj, "parameters.active", "active_parameters", "activeParameters", "params.active")
    links = md_first(obj, "links", default={})
    benchmarks = md_first(obj, "benchmarks", default={})

    return {
        "models_dev_model_id": md_canonical_id(obj),
        "models_dev_name": str(md_first(obj, "name", "display_name", "displayName")),
        "models_dev_lab": md_lab_name(obj),
        "models_dev_family": str(md_first(obj, "family", "series", "model_family")),
        "models_dev_description": str(md_first(obj, "description", "summary")),
        "models_dev_release_date": str(md_first(obj, "release_date", "releaseDate", "release")),
        "models_dev_last_updated": str(md_first(obj, "last_updated", "lastUpdated", "updated_at", "updated")),
        "models_dev_knowledge_cutoff": str(md_first(obj, "knowledge_cutoff", "knowledgeCutoff", "knowledge")),
        "models_dev_attachment": md_as_bool(md_first(obj, "attachment", "attachments", "capabilities.attachment")),
        "models_dev_reasoning": md_as_bool(md_first(obj, "reasoning", "capabilities.reasoning")),
        "models_dev_reasoning_options_json": md_compact_json(reasoning_options),
        "models_dev_tool_call": md_as_bool(md_first(obj, "tool_call", "toolCall", "capabilities.tools", "tools")),
        "models_dev_structured_output": md_as_bool(md_first(obj, "structured_output", "structuredOutput", "capabilities.structured")),
        "models_dev_temperature": md_as_bool(md_first(obj, "temperature", "capabilities.temperature")),
        "models_dev_open_weights": md_as_bool(md_first(obj, "open_weights", "openWeights", "weights.open")),
        "models_dev_license": str(md_first(obj, "license", "weights.license")),
        "models_dev_status": str(md_first(obj, "status")),
        "models_dev_experimental": md_as_bool(md_first(obj, "experimental")),
        "models_dev_context_tokens": md_maybe_int(md_first(obj, "context", "context_window", "contextWindow", "limit.context", "limits.context")),
        "models_dev_input_limit_tokens": md_maybe_int(md_first(obj, "limit.input", "limits.input", "input_limit", "inputLimit")),
        "models_dev_output_limit_tokens": md_maybe_int(md_first(obj, "limit.output", "limits.output", "output_limit", "outputLimit", "max_output_tokens")),
        "models_dev_input_modalities_json": md_compact_json(input_modalities),
        "models_dev_output_modalities_json": md_compact_json(output_modalities),
        "models_dev_interleaved": md_as_bool(md_first(obj, "interleaved", "capabilities.interleaved")),
        "models_dev_interleaved_field": str(md_first(obj, "interleaved_field", "interleavedField")),
        "models_dev_provider_count": str(len(providers) or len(provider_rows)),
        "models_dev_provider_names_json": md_compact_json(providers),
        "models_dev_first_party_input_price_per_m": md_price(obj, "input"),
        "models_dev_first_party_output_price_per_m": md_price(obj, "output"),
        "models_dev_reasoning_price_per_m": md_price(obj, "reasoning"),
        "models_dev_cache_read_price_per_m": md_price(obj, "cache_read"),
        "models_dev_cache_write_price_per_m": md_price(obj, "cache_write"),
        "models_dev_input_audio_price_per_m": md_price(obj, "input_audio"),
        "models_dev_output_audio_price_per_m": md_price(obj, "output_audio"),
        "models_dev_min_provider_input_price_per_m": "" if not input_prices else str(min(input_prices)),
        "models_dev_max_provider_input_price_per_m": "" if not input_prices else str(max(input_prices)),
        "models_dev_min_provider_output_price_per_m": "" if not output_prices else str(min(output_prices)),
        "models_dev_max_provider_output_price_per_m": "" if not output_prices else str(max(output_prices)),
        "models_dev_total_parameters": str(total_parameters or ""),
        "models_dev_active_parameters": str(active_parameters or ""),
        "models_dev_weights_json": md_compact_json(weights),
        "models_dev_links_json": md_compact_json(links),
        "models_dev_benchmarks_json": md_compact_json(benchmarks),
        "models_dev_provider_rows_json": md_compact_json(provider_rows),
        "models_dev_match_status": "exact-live-api",
        "models_dev_match_method": "models.dev live/offline catalog exact or conservative normalized match",
        "models_dev_candidate_id": md_canonical_id(obj),
        "models_dev_source_url": source_url,
        "models_dev_retrieved_at": retrieved_at,
        "models_dev_sync_notes": "Live models.dev metadata synchronized; empirical benchmark columns were not modified.",
    }


def md_choose_match(row: dict[str, str], records: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    ids = [row.get("models_dev_model_id"), row.get("official_model_id"), row.get("models_dev_candidate_id")]
    ids = [md_normalize(v) for v in ids if v]
    exact_by_id = [r for r in records if md_normalize(md_canonical_id(r)) in ids]
    if len(exact_by_id) == 1:
        return exact_by_id[0], "exact-id"

    target_full = {md_normalize(row.get(k)) for k in ("model_key", "display_name", "models_dev_name") if row.get(k)}
    exact_name = [r for r in records if md_normalize(md_canonical_id(r)) in target_full or md_normalize(md_first(r, "name", "display_name", "displayName")) in target_full]
    if len(exact_name) == 1:
        return exact_name[0], "exact-normalized-name"

    target = md_effortless_key(row.get("model_key") or row.get("display_name"))
    provider = md_normalize(row.get("provider") or row.get("models_dev_lab"))
    candidates = []
    for record in records:
        rid = md_effortless_key(md_canonical_id(record) or md_first(record, "name"))
        rlab = md_normalize(md_lab_name(record))
        if target and rid == target and (not provider or not rlab or provider in rlab or rlab in provider):
            candidates.append(record)
    if len(candidates) == 1:
        return candidates[0], "exact-base-model-plus-lab"
    return None, "ambiguous-or-unmatched"


def md_write_atomic(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=path.parent, prefix=path.name + ".", suffix=".tmp") as temp:
        writer = csv.DictWriter(temp, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        temp_path = Path(temp.name)
    os.replace(temp_path, path)



def sync_models_dev(csv_path: Path, api_url: str=MD_DEFAULT_API, offline_json: Path|None=None, timeout: int=45, strict: bool=False) -> dict[str,Any]:
    """Synchronize catalog/static metadata from models.dev without touching benchmark values.

    This consolidates the former source-specific sync_models_dev.py into an optional
    acquisition phase of the single executable. It is not run by default because
    network acquisition is intentionally distinct from deterministic calibration.
    """
    if offline_json:
        payload=json.loads(offline_json.read_text(encoding='utf-8'))
        source_url=offline_json.resolve().as_uri()
    else:
        try:
            payload=md_fetch_json(api_url,timeout)
        except (urllib.error.URLError,TimeoutError,OSError) as exc:
            raise RuntimeError(f'models.dev sync failed: {exc}. Use --models-dev-offline-json with a downloaded catalog snapshot.') from exc
        source_url=api_url
    retrieved_at=datetime.now(timezone.utc).isoformat()
    extracted=md_model_records(payload)
    if not extracted: raise RuntimeError('No model-like records recognized in models.dev payload; refusing to modify CSV.')
    groups: dict[str,list[dict[str,Any]]]=defaultdict(list)
    for record in extracted: groups[md_effortless_key(md_canonical_id(record))].append(record)
    with csv_path.open(encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle); rows=list(reader); fields=list(reader.fieldnames or [])
    for field in MD_MODELS_DEV_FIELDS:
        if field not in fields: fields.append(field)
    catalogs=[row for row in rows if row.get('record_type')=='catalog']
    matched=unmatched=0
    for row in catalogs:
        record,method=md_choose_match(row,extracted)
        if record is None:
            unmatched+=1; row['models_dev_sync_notes']=f'Live sync attempted {retrieved_at}; {method}. Existing metadata retained.'; continue
        provider_rows=groups.get(md_effortless_key(md_canonical_id(record)),[record])
        row.update(md_flatten_model(record,provider_rows,retrieved_at,source_url)); row['models_dev_match_method']=method; matched+=1
    by_key={row['model_key']:row for row in catalogs}
    for row in rows:
        if row.get('record_type')!='observation' or row.get('model_key') not in by_key: continue
        catalog=by_key[row['model_key']]
        for field in MD_MODELS_DEV_FIELDS: row[field]=catalog.get(field,'')
    if strict:
        missing_current=[row['model_key'] for row in catalogs if row.get('models_dev_match_status') in {'exact-current-snapshot','exact-live-api'} and not row.get('models_dev_model_id')]
        if missing_current: raise RuntimeError(f'Strict models.dev sync failed for {len(missing_current)} rows: {missing_current[:10]}')
    md_write_atomic(csv_path,rows,fields)
    return {'catalog_records_seen':len(extracted),'catalog_rows_matched':matched,'catalog_rows_unmatched':unmatched,'source':source_url}

def augment_standardized_cost(csv_path: Path, config_path: Path) -> dict[str,Any]:
    """Regenerate the low-weight standardized task-price fallback in the canonical ledger.

    This consolidates the former augment_cost.py. Direct/observed task cost and the
    model-specific AA token-price proxy are preserved; only the standardized fallback
    source is replaced from current catalog list prices and the project policy.
    """
    source_id='standard-task-price-proxy-v7'
    with csv_path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); rows=list(reader); fields=list(reader.fieldnames or [])
    project=json.loads(config_path.read_text(encoding='utf-8'))
    cfg=project['calibration']['task_cost_estimator']
    rows=[r for r in rows if r.get('source_id')!=source_id]
    catalog={r['model_key']:r for r in rows if r.get('record_type')=='catalog'}
    base_in=float(cfg.get('base_input_tokens',12000)); base_out=float(cfg.get('base_output_tokens',2500))
    im=cfg.get('effort_input_multipliers',{}); om=cfg.get('effort_output_multipliers',{})
    generated=[]
    def oid(key: str)->str:
        return hashlib.sha1(f'{source_id}|{key}|standardized_task_price_proxy_usd'.encode()).hexdigest()[:16]
    for key,meta in sorted(catalog.items()):
        ip=number(meta.get('input_price_per_m')); op=number(meta.get('output_price_per_m'))
        if ip is None or op is None or ip<0 or op<0 or (ip==0 and op==0): continue
        effort=(meta.get('effort') or 'default').lower()
        it=base_in*float(im.get(effort,im.get('default',1.0))); ot=base_out*float(om.get(effort,om.get('default',1.0)))
        cost=it/1e6*ip+ot/1e6*op
        row={f:meta.get(f,'') for f in fields}
        row.update({
            'record_type':'observation','observation_id':'obs-'+oid(key),'source_id':source_id,
            'source_original_id':source_id,'source_label':'Standardized task token-price proxy','source_publisher':'ARDF derived',
            'source_version':'7.3-consolidated','source_date':TODAY,'source_url':'project-config.json','retrieved_at':'2026-08-08T10:46:00-07:00',
            'metric_axis':'cost','metric_name':'standardized_task_price_proxy_usd','raw_value':f'{cost:.12g}',
            'raw_unit':'estimated USD per standardized task','raw_direction':'lower','is_reference_scale':'0',
            'quality':'estimated-current-list-price','confidence':str(cfg.get('confidence','estimated')),
            'base_weight':str(cfg.get('base_weight',0.35)),'use_in_aggregate':'1','is_historical':'0','identity_mapping':'exact catalog model_key',
            'notes':f'Current catalog-price formula: {it:g} input × ${ip:g}/M + {ot:g} output/reasoning-equivalent × ${op:g}/M = ${cost:.12g}; effort={effort}.',
            'calibration_group':'','source_refresh_status':'current-2026-08-08','is_vendor_reported':'0','is_independent_source':'0','data_freshness_class':'current',
        })
        for field in fields:
            if field.startswith('cal_') or field in {'calibrated_score','calibrated_score_unit','calibrated_score_algorithm'}: row[field]=''
        generated.append(row)
    rows.extend(generated)
    rows.sort(key=lambda r:(0 if r.get('record_type')=='catalog' else 1,r.get('model_key',''),r.get('source_id',''),r.get('metric_name',''),r.get('observation_id','')))
    write_rows_atomic(csv_path,rows,fields)
    return {'source':source_id,'generated':len(generated),'rows_after':len(rows)}


def ana_number(v: Any):
    try:
        x=float(str(v).replace(',','').replace('$','').strip())
        return x if math.isfinite(x) else None
    except (TypeError,ValueError): return None

def ana_truthy(v: Any): return str(v).strip().lower() in {'1','true','yes','y'}

def ana_wmean(items):
    if not items:return None
    sw=sum(w for v,w in items if v is not None and w>0)
    return sum(v*w for v,w in items if v is not None and w>0)/sw if sw else None

def ana_wgmean(items):
    usable=[(v,w) for v,w in items if v is not None and v>0 and w>0]
    if not usable:return None
    sw=sum(w for v,w in usable)
    return math.exp(sum(math.log(v)*w for v,w in usable)/sw)

def ana_cost_priority(r):
    # This order mirrors dashboard.html exactly.  If the dashboard changes,
    # update this function and the regression tests together.
    if r.get('metric_name')=='aa_cost_per_task_usd':return 5
    if r.get('source_id')=='aa-token-price-proxy-v7':return 3
    if r.get('source_id')=='standard-task-price-proxy-v7':return 2
    unit=(r.get('raw_unit') or '').lower(); metric=(r.get('metric_name') or '').lower()
    if 'per successful' in unit or 'per task' in unit or 'cost_per_success' in metric or 'cost_per_task' in metric:return 4
    return 1

def ana_aggregate(rows, policy):
    catalog={r['model_key']:r for r in rows if r.get('record_type')=='catalog'}
    groups=defaultdict(lambda:{'cap':[],'cost':[],'all':[],'aa':[]})
    for r in rows:
        if r.get('record_type')!='observation':continue
        groups[r['model_key']]['all'].append(r)
        if not ana_truthy(r.get('use_in_aggregate')):continue
        v=ana_number(r.get('cal_robust_affine')); w=ana_number(r.get('base_weight')) or 1.0
        if r.get('metric_name')=='aa_intelligence_index' and ana_number(r.get('raw_value')) is not None:
            groups[r['model_key']]['aa'].append(ana_number(r['raw_value']))
        if v is None:continue
        if r.get('metric_axis')=='capability':groups[r['model_key']]['cap'].append((v,w,r))
        elif r.get('metric_axis')=='cost' and v>0:groups[r['model_key']]['cost'].append((v,w,r))
    out=[]
    cutoff=policy['current_release_cutoff']
    for key,meta in catalog.items():
        g=groups[key]
        cap=ana_wmean([(v,w) for v,w,r in g['cap']])
        cost=None; used=[]
        if g['cost']:
            p=max(ana_cost_priority(r) for v,w,r in g['cost'])
            used=[(v,w,r) for v,w,r in g['cost'] if ana_cost_priority(r)==p]
            cost=ana_wgmean([(v,w) for v,w,r in used])
        release=meta.get('models_dev_release_date') or meta.get('release_date') or ''
        current=bool(release and release>=cutoff and (meta.get('models_dev_status') or '').lower()!='deprecated')
        raw_proxy=next((ana_number(r.get('raw_value')) for v,w,r in used if r.get('source_id')=='standard-task-price-proxy-v7'),None)
        item={
            'model_key':key,'display_name':meta.get('display_name') or key,'provider':meta.get('provider',''),
            'family':meta.get('family',''),'effort':meta.get('effort',''),'release_date':release,'current':current,
            'capability':cap,'aa_reference':max(g['aa']) if g['aa'] else None,'cost':cost,'raw_standardized_cost':raw_proxy,
            'cost_method':' + '.join(sorted({ana_cost_label(r) for v,w,r in used})) if used else 'unpriced',
            'cost_sources':sorted({r.get('source_id') for v,w,r in used}),
            'source_count':len({r.get('source_id') for r in g['all'] if r.get('source_id')}),
            'capability_rows':len(g['cap']),'cost_rows':len(g['cost']),
            'input_price_per_m':ana_number(meta.get('input_price_per_m')),'output_price_per_m':ana_number(meta.get('output_price_per_m')),
            'context_tokens':ana_number(meta.get('models_dev_context_tokens') or meta.get('context_window_tokens')),
            'output_limit_tokens':ana_number(meta.get('models_dev_output_limit_tokens')),
            'models_dev_lab':meta.get('models_dev_lab',''),'models_dev_status':meta.get('models_dev_status',''),
            'models_dev_open_weights':meta.get('models_dev_open_weights') or meta.get('is_open_weights',''),
            'models_dev_license':meta.get('models_dev_license',''),'models_dev_provider_count':ana_number(meta.get('models_dev_provider_count')),
            'models_dev_tool_call':meta.get('models_dev_tool_call',''),'models_dev_reasoning':meta.get('models_dev_reasoning',''),
            'models_dev_structured_output':meta.get('models_dev_structured_output',''),
            'notes':meta.get('notes','')
        }
        out.append(item)
    return out

def ana_cost_label(r):
    p=ana_cost_priority(r)
    return {5:'direct / repriced AA task cost',4:'observed benchmark task cost',3:'model-specific token × price',2:'standardized token-price estimate',1:'other calibrated cost'}[p]

def ana_tier_for(value, policy):
    if value is None:return {'id':'?','label':'Unscored'}
    for tier in policy['capability_tiers']:
        if value>=tier['min']:return {'id':tier['id'],'label':tier['label']}
    return {'id':'?','label':'Unscored'}

def ana_dominates(a, b, x_key='cost', y_key='capability', eps=1e-12):
    """True Pareto dominance: no worse on either axis and strictly better on >=1.

    Exact coordinate ties are Pareto-equivalent. They must not silently knock one
    another off the frontier merely because of lexical sort order.
    """
    ax,ay,bx,by=a.get(x_key),a.get(y_key),b.get(x_key),b.get(y_key)
    if None in (ax,ay,bx,by): return False
    no_worse=(ax<=bx+eps and ay>=by-eps)
    strictly_better=(ax<bx-eps or ay>by+eps)
    return no_worse and strictly_better

def ana_pareto(points):
    valid=[p for p in points if p['current'] and p['capability'] is not None and p['cost'] is not None and p['cost']>0]
    frontier=[p for p in valid if not any(ana_dominates(q,p) for q in valid if q['model_key']!=p['model_key'])]
    return sorted(frontier,key=lambda p:(p['cost'],-p['capability'],p['model_key']))

def ana_closest_dominator(point, frontier):
    candidates=[f for f in frontier if f['model_key']!=point['model_key'] and ana_dominates(f,point)]
    if not candidates:return None
    def dist(f):
        cap=(f['capability']-point['capability'])/5.0
        price=math.log10(point['cost']/f['cost']) if f['cost'] and point['cost'] else 99
        return math.hypot(cap,price)
    return min(candidates,key=dist)

def ana_near_label(cap_gap,cost_premium, policy):
    p=policy['near_frontier']
    if cap_gap<=p['razor_capability_gap_max'] and cost_premium<=p['razor_cost_premium_max_pct']:return 'razor-edge miss'
    if cap_gap<=p['near_capability_gap_max'] and cost_premium<=p['near_cost_premium_max_pct']:return 'near-frontier'
    if cap_gap<=p['near_capability_gap_max']:return 'capability-close / price-heavy'
    if cost_premium<=p['near_cost_premium_max_pct']:return 'price-close / capability-behind'
    return 'economically dominated'


def ana_current_aa_by_model(rows):
    """Return exact current AA observations keyed by model/configuration.

    This is intentionally separate from the multi-source ARDF ana_aggregate. The top-end
    effort audit needs a single-source apples-to-apples diagnostic so that an effort
    level with more third-party coverage is not rewarded merely for having more rows.
    """
    out=defaultdict(dict)
    for r in rows:
        if r.get('record_type')!='observation' or r.get('source_id')!='artificial-analysis-current':continue
        val=ana_number(r.get('raw_value'))
        if val is None:continue
        out[r['model_key']][r.get('metric_name','')]=val
    return out

def ana_simple_frontier(points, x_key, y_key):
    """Strict observed Pareto set for any source-native cost/capability plane."""
    pts=[p for p in points if p.get(x_key) is not None and p.get(y_key) is not None and p[x_key]>0]
    out=[p for p in pts if not any(ana_dominates(q,p,x_key,y_key) for q in pts if q is not p)]
    return sorted(out,key=lambda p:(p[x_key],-p[y_key],p.get('model_key','')))

def ana_top_end_analysis(models, rows, policy):
    """Compare the expensive frontier families at configuration granularity.

    Two views are emitted:
    - ARDF operational task-cost plane (multi-source capability vs task cost).
    - AA same-source diagnostic (exact AA Intelligence Index vs direct Cost per Task when available; full-evaluation cost only as fallback).

    The second view is *not* substituted for the primary graph. It is a consistency
    check that is especially useful for pruning dominated reasoning levels.
    """
    aa=ana_current_aa_by_model(rows); selected=[]
    for m in models:
        prefixes=tuple(policy.get('top_end',{}).get('model_key_prefixes',DEFAULT_TOP_END_PREFIXES))
        if not m['current'] or not m['model_key'].startswith(prefixes):continue
        a=aa.get(m['model_key'],{})
        task=a.get('aa_cost_per_task_usd'); full=a.get('aa_full_suite_cost_usd')
        row={**m,'aa_score_exact':a.get('aa_intelligence_index'),
             'aa_full_eval_cost':full,'aa_task_cost_exact':task,
             'aa_economic_cost':task if task is not None else full,
             'aa_economic_cost_basis':'direct AA cost/task' if task is not None else ('full AA evaluation cost fallback' if full is not None else '')}
        selected.append(row)
    # Primary operational frontier within this expensive cohort.
    op_front=ana_simple_frontier(selected,'cost','capability'); op_keys={x['model_key'] for x in op_front}
    # Prefer AA's source-native Cost per Intelligence Index Task. Full-evaluation
    # cost is retained only as an explicit fallback when a task-cost ana_number is absent.
    aa_front=ana_simple_frontier(selected,'aa_economic_cost','aa_score_exact'); aa_keys={x['model_key'] for x in aa_front}
    by_family=defaultdict(list)
    for x in selected:by_family[x['family']].append(x)
    for fam,items in by_family.items():
        ff=ana_simple_frontier(items,'aa_economic_cost','aa_score_exact'); fkeys={x['model_key'] for x in ff}
        for x in items:
            x['within_family_aa_frontier']=x['model_key'] in fkeys
            if x['aa_score_exact'] is not None and x['aa_economic_cost'] is not None and x['model_key'] not in fkeys:
                ds=[d for d in ff if ana_dominates(d,x,'aa_economic_cost','aa_score_exact')]
                x['within_family_dominated_by']=min(ds,key=lambda d:d['aa_economic_cost'])['display_name'] if ds else ''
            else:x['within_family_dominated_by']=''
    for x in selected:
        x['top_end_operational_frontier']=x['model_key'] in op_keys
        x['top_end_aa_frontier']=x['model_key'] in aa_keys
        x['operational_cost_per_capability']=(x['cost']/x['capability']) if x['cost'] and x['capability'] else None
        x['aa_cost_per_point']=(x['aa_economic_cost']/x['aa_score_exact']) if x['aa_economic_cost'] and x['aa_score_exact'] else None
    order={'low':1,'medium':2,'high':3,'xhigh':4,'max':5,'default':3,'non-reasoning':0}
    selected.sort(key=lambda x:(x['family'],order.get(x['effort'],99),x['model_key']))
    return {'configurations':selected,'operational_frontier_keys':sorted(op_keys),'aa_same_source_frontier_keys':sorted(aa_keys)}

def ana_external_frontier_comparisons(rows):
    """Build independent frontier cross-checks that do not feed the ARDF ana_aggregate.

    AA is represented by its current direct task-cost rows where numeric task cost is
    public in the package. Kilo is a completely independent coding-agent plane. Vals
    is retained as a capability/cost-per-test comparison when both values are present.
    """
    catalog={r['model_key']:r for r in rows if r.get('record_type')=='catalog'}
    # AA direct current task cost + exact current score.
    aa=defaultdict(dict)
    for r in rows:
        if r.get('record_type')!='observation' or r.get('source_id')!='artificial-analysis-current':continue
        v=ana_number(r.get('raw_value'));
        if v is None:continue
        if r.get('metric_name')=='aa_intelligence_index':aa[r['model_key']]['capability']=v
        elif r.get('metric_name')=='aa_cost_per_task_usd':aa[r['model_key']]['cost']=v
    aa_pts=[]
    for k,d in aa.items():
        if 'capability' not in d or 'cost' not in d:continue
        label=catalog.get(k,{}).get('display_name',k)
        # The project routes Muse on Contributor pricing, but this source-native AA
        # cross-check is AA's Standard-priced evaluation. Make that distinction
        # visible instead of inheriting the catalog's Contributor routing label.
        if k=='muse-spark-1-2-xhigh': label='Muse Spark 1.2 (AA Standard-priced evaluation)'
        aa_pts.append({'model_key':k,'display_name':label,**d})
    aa_front=ana_simple_frontier(aa_pts,'cost','capability');aa_keys={x['model_key'] for x in aa_front}
    for x in aa_pts:x['frontier']=x['model_key'] in aa_keys
    # Kilo completion/cost per attempt.
    kilo=defaultdict(dict)
    for r in rows:
        if r.get('source_id')!='kilo-leaderboard-current-2026-08-08':continue
        v=ana_number(r.get('raw_value'));
        if v is None:continue
        if r.get('metric_name')=='kilo_completion_pct':kilo[r['model_key']]['completion']=v
        elif r.get('metric_name')=='kilo_cost_per_attempt_usd':kilo[r['model_key']]['cost']=v
    kp=[{'model_key':k,'display_name':catalog.get(k,{}).get('display_name',k),**d} for k,d in kilo.items() if 'completion' in d and 'cost' in d]
    kf=ana_simple_frontier(kp,'cost','completion');kk={x['model_key'] for x in kf}
    for x in kp:x['frontier']=x['model_key'] in kk
    # Vals current public slice currently stores capability. Cost/Test is being expanded
    # incrementally; emit what is present without inventing values.
    vals_map=defaultdict(dict)
    for r in rows:
        if r.get('source_id')!='vals-index-current-2026-08-06':continue
        v=ana_number(r.get('raw_value'))
        if v is None:continue
        if r.get('metric_name')=='vals_index_accuracy_pct':vals_map[r['model_key']]['accuracy']=v
        elif r.get('metric_name')=='vals_index_cost_per_test_usd':vals_map[r['model_key']]['cost']=v
    vals=[{'model_key':k,'display_name':catalog.get(k,{}).get('display_name',k),**d} for k,d in vals_map.items()]
    vf=ana_simple_frontier(vals,'cost','accuracy');vk={x['model_key'] for x in vf}
    for x in vals:x['frontier']=x['model_key'] in vk
    vals.sort(key=lambda x:(x.get('cost') if x.get('cost') is not None else math.inf,-(x.get('accuracy') or -1)))
    return {'artificial_analysis':{'points':sorted(aa_pts,key=lambda x:x['cost']),'frontier_keys':sorted(aa_keys),
                                   'note':'Exact current AA Intelligence Index vs public numeric Cost per Intelligence Index Task rows in the package. AA public explorer currently renders a 26-model Pareto view; this extracted graph is a reproducible subset, not a pixel scrape. Muse here is the AA Standard-priced evaluation, not the ARDF Contributor route.'},
            'kilo':{'points':sorted(kp,key=lambda x:x['cost']),'frontier_keys':sorted(kk),
                    'note':'Independent coding-agent completion vs cost per attempt; not calibrated into the AA task-cost plane.'},
            'vals':{'points':vals,'frontier_keys':sorted(vk),'note':'Current Vals Index accuracy vs Cost/Test; independent source-specific Pareto cross-check, not an AA task-cost substitute.'}}

def ana_build():
    project=json.loads(CONFIG_PATH.read_text(encoding='utf-8')); policy=project['analysis']
    with CSV_PATH.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    models=ana_aggregate(rows,policy)
    for m in models:m['tier']=ana_tier_for(m['capability'],policy)
    frontier=ana_pareto(models); fkeys={m['model_key'] for m in frontier}
    for m in models:m['frontier']=m['model_key'] in fkeys
    major=[]
    by_key={m['model_key']:m for m in models}
    for key in policy['near_frontier']['major_model_keys']:
        m=by_key.get(key)
        if not m or m['capability'] is None or m['cost'] is None:continue
        d=ana_closest_dominator(m,frontier)
        row={k:m[k] for k in m}
        if d:
            gap=d['capability']-m['capability']; premium=(m['cost']/d['cost']-1)*100
            row.update({'dominated_by':d['display_name'],'dominated_by_key':d['model_key'],'capability_gap':gap,'cost_premium_pct':premium,'cost_ratio':m['cost']/d['cost'],'near_status':ana_near_label(gap,premium,policy)})
        else:row.update({'dominated_by':'','dominated_by_key':'','capability_gap':0,'cost_premium_pct':0,'cost_ratio':1,'near_status':'STRICT FRONTIER'})
        major.append(row)
    # General near-frontier table: include every non-frontier current model whose
    # dominance is genuinely close by either capability or cost.
    near=[]
    for m in models:
        if not m['current'] or m['frontier'] or m['capability'] is None or m['cost'] is None:continue
        d=ana_closest_dominator(m,frontier)
        if not d:continue
        gap=d['capability']-m['capability']; premium=(m['cost']/d['cost']-1)*100
        status=ana_near_label(gap,premium,policy)
        if status!='economically dominated':
            near.append({**m,'dominated_by':d['display_name'],'dominated_by_key':d['model_key'],'capability_gap':gap,'cost_premium_pct':premium,'cost_ratio':m['cost']/d['cost'],'near_status':status})
    near.sort(key=lambda x:(0 if x['near_status']=='razor-edge miss' else 1 if x['near_status']=='near-frontier' else 2,x['capability_gap'],x['cost_premium_pct']))
    # Executor price/performance is deliberately separate from Pareto membership.
    # Pareto is a dominance relation; it does not rank survivors by a scalar ratio.
    # The user explicitly requested literal task-price per calibrated capability.
    e=policy['executor']; candidates=[]; global_value=[]
    executor_floor=number(e.get('minimum_aggregate_capability'))
    for m in models:
        if not m['current'] or m['cost'] is None or m['cost']<=0 or m['capability'] is None or m['capability']<=0:continue
        ref=m['aa_reference'] if m['aa_reference'] is not None else None
        cost_per_cap=m['cost']/m['capability']
        cap_per_dollar=m['capability']/m['cost']
        cost_per_aa=(m['cost']/ref) if ref is not None and ref>0 else None
        valued={**m,'executor_reference_capability':ref,'cost_per_capability':cost_per_cap,
                'capability_per_dollar':cap_per_dollar,'cost_per_aa_point':cost_per_aa}
        global_value.append(valued)
        if executor_floor is None or m['capability']>=executor_floor:
            candidates.append(valued)
    # Lower $/capability is better. No exponent, capability subtraction, or forced slot.
    global_value.sort(key=lambda x:(x['cost_per_capability'],-x['capability'],x['cost']))
    candidates.sort(key=lambda x:(x['cost_per_capability'],-x['capability'],x['cost']))
    # The user asked for five executor *models*, not five effort configurations.
    # Collapse reasoning/effort siblings by model family and keep the best literal ratio
    # from each family. The full effort/configuration ranking remains in executor_candidates.
    best_by_family={}
    for c in candidates:
        fam=c.get('family') or c['model_key']
        if fam not in best_by_family: best_by_family[fam]=c
    shortlist=list(best_by_family.values())[:e['top_n']]
    # Luna effort comparison uses the same literal ratio. High is presently the best
    # value setting; xhigh can still be called a marginal-capability knee, but it is
    # not the lowest-price-per-capability executor setting.
    luna_curve=sorted([{**x,'marginal_note':''} for x in candidates if x['model_key'].startswith('gpt-5-6-luna-') and x['effort'] in {'high','xhigh','max'}],key=lambda x:['high','xhigh','max'].index(x['effort']))
    for i,x in enumerate(luna_curve):
        if i:
            prev=luna_curve[i-1]
            x['aa_gain_vs_previous']=(x['aa_reference'] or x['capability'])-(prev['aa_reference'] or prev['capability'])
            x['cost_increase_vs_previous_pct']=(x['cost']/prev['cost']-1)*100
    top_end=ana_top_end_analysis(models,rows,policy); external=ana_external_frontier_comparisons(rows)
    data={'generated_at': datetime.now(timezone.utc).isoformat(),'policy':policy,'counts':{'catalog':len(models),'current_paired':sum(1 for m in models if m['current'] and m['capability'] is not None and m['cost'] is not None),'frontier':len(frontier),'near_frontier':len(near)},'frontier':frontier,'near_frontier':near,'major_near_frontier':major,'executor_top5':shortlist,'executor_candidates':candidates[:20],'global_value_top20':global_value[:20],'luna_effort_curve':luna_curve,'top_end':top_end,'ana_external_frontier_comparisons':external}
    PARETO_PATH.write_text(ana_render_md(data),encoding='utf-8')
    print(json.dumps(data['counts'],indent=2))
    print('executor $/cap:',[(x['display_name'],round(x['cost_per_capability'],8)) for x in shortlist])
    return data

def ana_money(v):return '—' if v is None else f'${v:.5g}'
def ana_f2(v):return '—' if v is None else f'{v:.2f}'
def ana_render_md(d):
    executor_floor=number(d['policy']['executor'].get('minimum_aggregate_capability'))
    executor_eligibility=(
        'No global capability floor. Named roles may apply visible, role-specific gates.'
        if executor_floor is None
        else f'Calibrated capability ≥ {executor_floor:.0f}.'
    )
    lines=['# ARDF Pareto Frontier + Price/Performance Cheatsheet','',f"Generated {TODAY}. Canonical source: `data/unified-model-evidence.csv`. Generated by `calibrate.py`; edit policy in `project-config.json`, not these tables by hand.",'','## Read this first','',
    '- **Strict Pareto frontier** and **price/performance ranking are different calculations.** A Pareto point is simply not dominated by a configuration that is both cheaper and at least as capable. Pareto does not assign a single best model or sort by a capability/price ratio.',
    '- **Calibrated capability** is the multi-source AA-equivalent Y coordinate used by the main graph. It is not literal human IQ.',
    '- **Task price** is the dashboard X coordinate using the best-available cost hierarchy.',
    '- **Literal price/performance** is `task_price / calibrated_capability`; **lower is better**. Its inverse, capability points per dollar, is also shown.',
    f"- **Executor eligibility:** {executor_eligibility}",
    '- **AA $/point** is a secondary same-source diagnostic where exact AA Intelligence Index exists. It never replaces the multi-source primary ranking.',
    '- Muse Spark 1.2 uses **Contributor/data-sharing pricing as its primary economic coordinate**. Standard/no-sharing pricing is retained as secondary evidence.','','## Strict current Pareto frontier','', '| Tier | Model/configuration | Provider | Effort | Capability | Task price | $/capability point | $/M in/out | Released | Context | Weights | Sources |','|---|---|---|---|---:|---:|---:|---:|---|---:|---|---:|']
    for m in d['frontier']:
        ratio=m['cost']/m['capability'] if m['capability'] and m['cost'] else None
        lines.append(f"| {m['tier']['id']} | {m['display_name']} | {m['provider']} | {m['effort']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {ana_money(ratio)} | {ana_money(m['input_price_per_m'])} / {ana_money(m['output_price_per_m'])} | {m['release_date'] or '—'} | {int(m['context_tokens']) if m['context_tokens'] else '—'} | {'open' if str(m['models_dev_open_weights'])=='1' else 'closed/API'} | {m['source_count']} |")
    lines += ['','## Muse Spark 1.2 economics','','The project deliberately uses the **Contributor/data-sharing** Meta SKU as Muse Spark 1.2’s primary economic coordinate. The Standard/no-sharing tier remains in the canonical CSV and hover metadata.','','| Tier | Input / M | Cache read / M | Output / M | AA-equivalent task cost | Role |','|---|---:|---:|---:|---:|---|','| Contributor / data-sharing | $0.10 | $0.002 | $0.20 | **$0.02123 derived/repriced** | **Primary ARDF coordinate** |','| Standard / no-sharing | $1.25 | $0.15 | $4.25 | $0.40 measured by AA | Secondary metadata/evidence |','','The Contributor task coordinate is not a direct AA billing observation. It reprices the same AA workload using the lower published Meta tier, preserving the workload while changing only the token-price schedule.','','## Major models that miss the frontier','', '| Model/configuration | Tier | Capability | Task price | Dominated by | Capability gap | Price premium | Verdict |','|---|---|---:|---:|---|---:|---:|---|']
    for m in d['major_near_frontier']:
        lines.append(f"| {m['display_name']} | {m['tier']['id']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {m['dominated_by'] or '—'} | {m['capability_gap']:.2f} | {m['cost_premium_pct']:.1f}% | {m['near_status']} |")
    lines += ['','## Closest near-frontier misses (all families)','', 'This table is algorithmic rather than hand-picked: the first 20 current non-frontier configurations with the smallest configured dominance regret are shown. It catches alternatives that a strict frontier necessarily excludes.','', '| Model/configuration | Tier | Capability | Task price | Dominated by | Capability gap | Price premium | Verdict |','|---|---|---:|---:|---|---:|---:|---|']
    for m in d['near_frontier'][:20]:
        lines.append(f"| {m['display_name']} | {m['tier']['id']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {m['dominated_by']} | {m['capability_gap']:.2f} | {m['cost_premium_pct']:.1f}% | {m['near_status']} |")
    lines += ['','## Capability-tier interpretation','','Tier thresholds classify calibrated **capability only**. They do not overwrite Pareto status or price/performance rank.','']
    for t in d['policy']['capability_tiers']:
        lines.append(f"- **{t['id']}**: ≥ {t['min']:.0f} — {t['label']}")
    lines += ['','## Global raw price/performance leaders','','This table has **no executor capability floor**. It is included to make the denominator policy visible: cheap mid/low-capability models can outrank frontier-class models on raw `$ / capability` alone.','', '| Rank | Model/configuration | Tier | Capability | Task price | $/capability | Capability/$ | Pareto? |','|---:|---|---|---:|---:|---:|---:|---|']
    for i,m in enumerate(d['global_value_top20'][:10],1):
        lines.append(f"| {i} | {m['display_name']} | {m['tier']['id']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {ana_money(m['cost_per_capability'])} | {m['capability_per_dollar']:.1f} | {'YES' if m['frontier'] else 'no'} |")
    lines += ['','## Top five executor-grade price/performance candidates','', f"Eligibility: current, priced, positive calibrated capability. {executor_eligibility} Ranked strictly by `task_price / calibrated_capability`, ascending. No exponent, capability subtraction, or forced provider/model slot.",'', '| Rank | Model/configuration | Provider | Multi-source capability | AA reference | Task price | $/capability ↓ | Capability/$ ↑ | $/AA point | Pareto? | Cost vs Muse |','|---:|---|---|---:|---:|---:|---:|---:|---:|---|---:|']
    muse=next((x for x in d['executor_top5'] if x['model_key']=='muse-spark-1-2-xhigh'),None); mc=muse['cost'] if muse else min(x['cost'] for x in d['executor_top5'])
    for i,m in enumerate(d['executor_top5'],1):
        aa_ratio=ana_money(m.get('cost_per_aa_point')) if m.get('cost_per_aa_point') is not None else '—'
        lines.append(f"| {i} | {m['display_name']} | {m['provider']} | {ana_f2(m['capability'])} | {ana_f2(m['executor_reference_capability'])} | {ana_money(m['cost'])} | {ana_money(m['cost_per_capability'])} | {m['capability_per_dollar']:.1f} | {aa_ratio} | {'YES' if m['frontier'] else 'no'} | {m['cost']/mc:.2f}× |")
    lines += ['','**Important:** Muse remains #1 **within the executor-eligible set** under the corrected literal ratio. It is not necessarily #1 across the unrestricted model universe; the no-floor table above deliberately shows cheaper lower-capability configurations that can have an even lower raw `$ / capability` ratio.','','**MiMo identity correction:** MiMo-V2.5 and MiMo-V2.5-Pro are distinct. Current AA scores are 38 and 43 respectively. The former dated `mimo-v2-5-0424` alias is merged into MiMo-V2.5; no Pro/preview score is borrowed across identities.','','### GPT-5.6 Luna price/performance by effort','', '| Effort | Multi-source capability | AA reference | Task price | $/capability ↓ | $/AA point | Gain vs prior effort | Cost increase |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in d['luna_effort_curve']:
        cost_inc='—' if m.get('cost_increase_vs_previous_pct') is None else f"{m['cost_increase_vs_previous_pct']:.1f}%"
        aa_ratio=ana_money(m.get('cost_per_aa_point')) if m.get('cost_per_aa_point') is not None else '—'
        lines.append(f"| {m['effort']} | {ana_f2(m['capability'])} | {ana_f2(m['aa_reference'])} | {ana_money(m['cost'])} | {ana_money(m['cost_per_capability'])} | {aa_ratio} | {ana_f2(m.get('aa_gain_vs_previous'))} | {cost_inc} |")
    best_luna=min(d['luna_effort_curve'], key=lambda x:x['cost_per_capability']) if d['luna_effort_curve'] else None
    if best_luna:
        lines += ['',f"**Literal price/performance winner for Luna: `{best_luna['effort']}`.** Its `$ / calibrated-capability` ratio is {ana_money(best_luna['cost_per_capability'])}. Xhigh remains a reasonable *capability knee* if extra quality is worth paying for, but it is not the lowest-cost-per-capability setting. Primary API economics use Standard / short-context $0.20 input and $1.20 output per million tokens; Batch remains secondary asynchronous pricing."]
    lines += ['','## Top-end configuration audit','', 'This is the high-cost/high-capability zone the project is meant to prune aggressively. The **operational** columns use the multi-source ARDF task-cost plane. The **AA same-source** columns use current Artificial Analysis Intelligence Index and direct Cost per Intelligence Index Task wherever AA exposes it. Full-evaluation cost is shown separately and used only as an explicit fallback, so reasoning levels are compared without source-density bias.','','| Model/configuration | Effort | ARDF cap | ARDF task cost | $/cap | AA score | AA task cost | AA full-eval cost | AA $/score | AA cost basis | Op. frontier? | AA top-end frontier? | Within-family AA optimal? |','|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|']
    for m in d['top_end']['configurations']:
        lines.append(f"| {m['display_name']} | {m['effort']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {ana_money(m['operational_cost_per_capability'])} | {ana_f2(m['aa_score_exact'])} | {ana_money(m['aa_task_cost_exact'])} | {ana_money(m['aa_full_eval_cost'])} | {ana_money(m['aa_cost_per_point'])} | {m['aa_economic_cost_basis'] or '—'} | {'YES' if m['top_end_operational_frontier'] else 'no'} | {'YES' if m['top_end_aa_frontier'] else 'no'} | {'YES' if m.get('within_family_aa_frontier') else ('dominated by '+m.get('within_family_dominated_by','') if m.get('within_family_dominated_by') else 'unscored')} |")
    lines += ['','**Key pruning rule:** an effort configuration that is dominated within its own family on exact AA score/cost should normally be eliminated from default routing unless another task-specific benchmark demonstrates a compensating specialty. Opus 5 max is the canonical example when xhigh has the same AA Intelligence Index at lower direct AA task cost.','','### Current top-end routing cuts','','- **Hard prune from general default routing:** Opus 5 max. Xhigh has the same exact AA score (63) at lower direct AA task cost.','- **Keep as explicit Opus cost/quality rungs:** medium, high, xhigh. Low also remains same-source Pareto-efficient but is below the primary high-end quality band.','- **Sol:** its effort curve is internally monotone, so there is no same-family hard prune from AA alone. However, Sol xhigh/max can be cross-family dominated in the AA direct-task-cost plane; keep Sol where coding/agent benchmarks such as Kilo justify it rather than because of general cost efficiency.','- **Qwen3.8 Max xhigh:** is currently dominated on both the ARDF operational top-end plane and the AA direct-task-cost plane by cheaper configurations with equal or higher capability. Keep it only when a Qwen-specific workload, provider constraint, or specialist benchmark justifies the premium.','- **Kimi K3 max:** remains on the audited operational and AA top-end frontiers and is especially strong on coding-agent economics. Preserve it as a first-class high-end alternative rather than treating it as merely an almost-frontier model.','- **Fable 5 max:** remains near the capability ceiling but is strongly price-heavy in general economic planes. Preserve it for benchmark/task areas where it demonstrably wins; do not default-route it merely because it is a flagship.','','## External Pareto cross-checks','', 'These are diagnostic planes, not extra votes in the calibrated aggregate. Agreement increases confidence; disagreement tells us where benchmark/harness semantics matter.','','### Artificial Analysis direct task-cost subset','', '| Model | AA capability | AA cost/task | AA Pareto within extracted subset? |','|---|---:|---:|---|']
    for x in d['ana_external_frontier_comparisons']['artificial_analysis']['points']:
        lines.append(f"| {x['display_name']} | {ana_f2(x['capability'])} | {ana_money(x['cost'])} | {'YES' if x['frontier'] else 'no'} |")
    lines += ['','### Kilo coding-agent frontier','', '| Model | Completion | Cost/attempt | Kilo Pareto? |','|---|---:|---:|---|']
    for x in d['ana_external_frontier_comparisons']['kilo']['points']:
        lines.append(f"| {x['display_name']} | {x['completion']:.1f}% | {ana_money(x['cost'])} | {'YES' if x['frontier'] else 'no'} |")
    lines += ['','Kilo currently retains Grok 4.5 → Kimi K3 → GPT-5.5 → GPT-5.6 Sol as the observed completion/cost frontier among its public top-10 table. Fable 5 and Opus 5 are dominated there despite being near the capability ceiling, which reinforces the need to separate **maximum quality** from **economic efficiency**.','','### Vals Index cost/test frontier','', '| Model | Vals Index | Cost/Test | Vals Pareto? |','|---|---:|---:|---|']
    for x in d['ana_external_frontier_comparisons']['vals']['points']:
        if x.get('cost') is not None:
            lines.append(f"| {x['display_name']} | {x['accuracy']:.2f}% | {ana_money(x['cost'])} | {'YES' if x['frontier'] else 'no'} |")
    lines += ['','Vals is a second independent cost/performance plane. Its Cost/Test is benchmark-specific; it is calibrated through overlaps when used in ARDF, but the raw Vals frontier is preserved here for comparison.']
    lines += ['','## Near-frontier interpretation','', '- **razor-edge miss:** ≤0.75 capability points behind and ≤25% more expensive than its closest dominating frontier point.', '- **near-frontier:** ≤2 capability points behind and ≤50% more expensive.', '- **capability-close / price-heavy:** capability is close but the price penalty is substantial.', '- **price-close / capability-behind:** price is close, but capability gives up more than the near band.', '- **economically dominated:** neither condition is close.','']
    return '\n'.join(lines)




def render_tiers_document(data: dict[str,Any], calibrated_payload: dict[str,Any]) -> str:
    """Render capability tiers separately from the economic Pareto cheatsheet."""
    policy=data['policy']
    active=calibrated_payload['config']['active_algorithm_by_axis']['capability']
    models=[dict(m) for m in calibrated_payload['aggregate_sets'][active]]
    near={m['model_key']:m for m in data.get('near_frontier',[])}
    frontier={m['model_key'] for m in data.get('frontier',[])}
    def tf(v): return ana_tier_for(v,policy)
    def money(v): return '—' if v is None else f'${v:.5g}'
    def f2(v): return '—' if v is None else f'{v:.2f}'
    for m in models:
        m['tier']=tf(m.get('capability')); m['frontier']=m['model_key'] in frontier
    current=[m for m in models if m.get('capability') is not None and (m.get('models_dev_status') or '').lower()!='deprecated']
    lines=['# ARDF Model Tiers + Contested Regions','',
           'This document answers a different question from the Pareto cheatsheet: **tiers classify calibrated capability**, while Pareto membership classifies economic non-dominance.','',
           'Canonical data: `data/unified-model-evidence.csv`. Policy: `project-config.json`. Regenerate with `python calibrate.py`.','',
           '## Capability tier policy','', '| Tier | Minimum calibrated capability | Interpretation |','|---|---:|---|']
    for t in policy['capability_tiers']:
        lines.append(f"| {t['id']} | {t['min']:.0f} | {t['label']} |")
    lines += ['','## Current scored configurations by tier','']
    for t in policy['capability_tiers']:
        members=sorted((m for m in current if m['tier']['id']==t['id']),key=lambda x:(-(x.get('capability') or -1),x.get('display_name','')))
        lines += [f"### {t['id']} · {t['label']} ({len(members)})",'', '| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |','|---|---:|---:|---|---|']
        for m in members:
            n=near.get(m['model_key'],{})
            lines.append(f"| {m.get('display_name') or m['model_key']} | {f2(m.get('capability'))} | {money(m.get('cost'))} | {'YES' if m['frontier'] else 'no'} | {n.get('near_status','—')} |")
        lines.append('')
    lines += ['## Top contested region','',
              'The upper contest zone includes configurations at capability ≥50, spanning the A+/S/S+ boundary neighborhood where small capability differences can carry large cost penalties.','',
              '| Model/configuration | Tier | Capability | Cost | Pareto | Closest economic verdict |','|---|---|---:|---:|---|---|']
    for m in sorted((m for m in current if (m.get('capability') or -1)>=50),key=lambda x:(-(x.get('capability') or -1),x.get('cost') if x.get('cost') is not None else math.inf)):
        n=near.get(m['model_key'],{}); verdict='STRICT FRONTIER' if m['frontier'] else n.get('near_status','dominated / outside near band')
        lines.append(f"| {m.get('display_name') or m['model_key']} | {m['tier']['id']} | {f2(m.get('capability'))} | {money(m.get('cost'))} | {'YES' if m['frontier'] else 'no'} | {verdict} |")
    lines += ['','## Bottom contested region','',
              'The lower end is contested by cost compression rather than flagship quality. This section combines the cheapest eight Pareto configurations with models within ±2 capability points of the D↔C (30) and C↔B (40) boundaries.','',
              '| Model/configuration | Tier | Capability | Cost | Pareto | Why included |','|---|---|---:|---:|---|---|']
    low_front=sorted((m for m in current if m['frontier']),key=lambda x:x.get('cost') if x.get('cost') is not None else math.inf)[:8]
    boundary=sorted((m for m in current if any(abs((m.get('capability') or -999)-b)<=2 for b in (30,40))),key=lambda x:(x.get('capability') or -1,x.get('cost') if x.get('cost') is not None else math.inf))
    seen=set()
    for m in low_front+boundary:
        if m['model_key'] in seen: continue
        seen.add(m['model_key']); reasons=[]
        if any(x['model_key']==m['model_key'] for x in low_front): reasons.append('low-cost Pareto segment')
        c=m.get('capability')
        if c is not None and abs(c-30)<=2: reasons.append('near D/C boundary')
        if c is not None and abs(c-40)<=2: reasons.append('near C/B boundary')
        if m['model_key'] in near: reasons.append(near[m['model_key']]['near_status'])
        lines.append(f"| {m.get('display_name') or m['model_key']} | {m['tier']['id']} | {f2(c)} | {money(m.get('cost'))} | {'YES' if m['frontier'] else 'no'} | {'; '.join(reasons) or 'boundary neighborhood'} |")
    lines += ['','## Closest competitors to the strict Pareto frontier','',
              '| Model/configuration | Tier | Capability | Cost | Dominated by | Capability gap | Cost premium | Status |','|---|---|---:|---:|---|---:|---:|---|']
    for m in data.get('near_frontier',[])[:20]:
        lines.append(f"| {m['display_name']} | {m['tier']['id']} | {f2(m['capability'])} | {money(m['cost'])} | {m['dominated_by']} | {m['capability_gap']:.2f} | {m['cost_premium_pct']:.1f}% | {m['near_status']} |")
    lines += ['','## Named high-interest competitors','',
              'These entries come from the explicit analysis-policy watchlist and remain visible even when they are not among the twenty numerically closest misses.','',
              '| Model/configuration | Tier | Capability | Cost | Status |','|---|---|---:|---:|---|']
    for m in data.get('major_near_frontier',[]):
        lines.append(f"| {m['display_name']} | {m['tier']['id']} | {f2(m['capability'])} | {money(m['cost'])} | {m['near_status']} |")
    return '\n'.join(lines)+'\n'


def embed_dashboard(payload: dict[str,Any], analysis: dict[str,Any]) -> None:
    """Replace only the embedded generated payload block in the standalone dashboard."""
    text=DASHBOARD_PATH.read_text(encoding='utf-8')
    begin='<!-- ARDF_DATA_BEGIN -->'; end='<!-- ARDF_DATA_END -->'
    if begin not in text or end not in text:
        raise RuntimeError('dashboard.html is missing ARDF_DATA_BEGIN/END markers')
    block=(begin+'\n<script>\n'
           'window.ARDF_DATA='+json.dumps(payload,separators=(',',':'))+';\n'
           'window.ARDF_ANALYSIS='+json.dumps(analysis,separators=(',',':'))+';\n'
           '</script>\n'+end)
    text=text[:text.index(begin)]+block+text[text.index(end)+len(end):]
    DASHBOARD_PATH.write_text(text,encoding='utf-8')


def _validate_embedded_dashboard(html_path):
    text=html_path.read_text(encoding='utf-8')
    assert 'window.ARDF_DATA' in text, 'dashboard must embed ARDF_DATA'
    assert 'window.ARDF_ANALYSIS' in text, 'dashboard must embed ARDF_ANALYSIS'
    assert 'generated/dashboard-data.js' not in text, 'refined dashboard must not depend on external generated/'
    return True

def validate_package(cal_result: dict[str,Any], analysis: dict[str,Any]) -> None:
    """Fail fast on structural regressions without emitting extra report files."""
    required=[CSV_PATH,CONFIG_PATH,DASHBOARD_PATH,PARETO_PATH,TIERS_PATH,ROOT/'user-prompt-aggregation.md',ROOT/'ardf-research-paper.md',INDEX_PATH,Path(__file__).resolve()]
    missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing: raise RuntimeError('Missing required files: '+', '.join(missing))
    # The immutable export has exactly nine authoritative files. Supporting
    # provenance and transition records may coexist in the working tree, but
    # they are outside that export and cannot replace a required authority.
    export_files={str(p.relative_to(ROOT)) for p in required}
    if len(export_files)!=9: raise RuntimeError(f'Expected 9 authoritative export files, found {len(export_files)}')
    if cal_result['model_count']<600: raise RuntimeError(f'Unexpected model-count collapse: {cal_result["model_count"]}')
    if cal_result['observation_count']<1000: raise RuntimeError(f'Unexpected observation-count collapse: {cal_result["observation_count"]}')
    if not analysis.get('frontier'): raise RuntimeError('Strict Pareto frontier is empty')
    dash=DASHBOARD_PATH.read_text(encoding='utf-8')
    if 'window.ARDF_DATA=' not in dash or 'window.ARDF_ANALYSIS=' not in dash: raise RuntimeError('Dashboard payload embedding failed')
    # Guard the single-ledger/single-policy architecture.
    forbidden=['generated/','config/calibration-algorithms.json','analysis-data.json','dashboard-data.js']
    for f in forbidden:
        if f in INDEX_PATH.read_text(encoding='utf-8') and 'former' not in INDEX_PATH.read_text(encoding='utf-8').lower():
            raise RuntimeError(f'INDEX appears to restore superseded path {f}')


def main() -> None:
    parser=argparse.ArgumentParser(description='Calibrate the canonical ARDF ledger and rebuild all derived working artifacts in place.')
    parser.add_argument('--input',type=Path,default=CSV_PATH)
    parser.add_argument('--output',type=Path,default=CSV_PATH)
    parser.add_argument('--config',type=Path,default=CONFIG_PATH)
    parser.add_argument('--no-docs',action='store_true',help='Calibrate CSV only; do not rebuild decision docs/dashboard payloads.')
    parser.add_argument('--skip-cost-augmentation',action='store_true',help='Do not regenerate the standardized task-cost fallback before calibration.')
    parser.add_argument('--sync-models-dev',action='store_true',help='Refresh models.dev catalog metadata before derivation/calibration.')
    parser.add_argument('--models-dev-api-url',default=MD_DEFAULT_API)
    parser.add_argument('--models-dev-offline-json',type=Path)
    parser.add_argument('--models-dev-timeout',type=int,default=45)
    parser.add_argument('--models-dev-strict',action='store_true')
    args=parser.parse_args()
    sync_result=None
    if args.sync_models_dev:
        sync_result=sync_models_dev(args.input,args.models_dev_api_url,args.models_dev_offline_json,args.models_dev_timeout,args.models_dev_strict)
    augmentation=None
    if not args.skip_cost_augmentation and args.input.resolve()==args.output.resolve():
        augmentation=augment_standardized_cost(args.input,args.config)
    result=calibrate(args.input,args.output,args.config)
    summary={k:v for k,v in result.items() if k not in {'reports','models','aggregate_sets','payload'}}
    if sync_result is not None: summary['models_dev_sync']=sync_result
    if augmentation is not None: summary['cost_augmentation']=augmentation
    if not args.no_docs:
        analysis=ana_build()
        TIERS_PATH.write_text(render_tiers_document(analysis,result['payload']),encoding='utf-8')
        embed_dashboard(result['payload'],analysis)
        validate_package(result,analysis)
        summary.update({'frontier_count':len(analysis['frontier']),'near_frontier_count':len(analysis['near_frontier']),'working_files':9})
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
