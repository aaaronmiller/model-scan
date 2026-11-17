# ---
# title: ARDF Multipoint Calibration and Display-Data Engine
# version: 7.5.0
# refined: 2026-11-09 (v7.5.0 consolidated audit, cost-priority fix in aggregate_sets, lineage + 4-tier + pinch-point integration)
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
    eps=1e-12; result=[]
    for m in candidates:
        mx=float(m[cost_field]); my=float(m[capability_field])
        dominated=False
        for q in candidates:
            if q['model_key']==m['model_key']: continue
            qx=float(q[cost_field]); qy=float(q[capability_field])
            if (qx<=mx+eps and qy>=my-eps) and (qx<mx-eps or qy>my+eps):
                dominated=True; break
        if not dominated:
            result.append(m['model_key'])
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
            if r.get('metric_axis')=='cost':
                if value<=0: continue
                per_model[r['model_key']]['cost'].append((value,weight,r))
            elif r.get('metric_axis')=='capability':
                per_model[r['model_key']]['capability'].append((value,weight,r))
            per_model[r['model_key']]['sources'].add(r['source_id'])
        agg=[]
        for m in models:
            d=per_model[m['model_key']]
            cap_items,_=ana_scale_filter(d['capability'],m['model_key'])
            cap=weighted_mean([(v,w) for v,w,_ in cap_items])
            if d['cost']:
                max_p=max(ana_cost_priority(r) for _,_,r in d['cost'])
                used_cost=[(v,w) for v,w,r in d['cost'] if ana_cost_priority(r)==max_p]
                cost=weighted_geometric_mean(used_cost)
            else:
                cost=None
            agg.append({**m,'capability':cap,'cost':cost,'source_count':len(d['sources']),'capability_observations':len(cap_items),'cost_observations':len(d['cost'])})
        frontier=set(pareto(agg,'capability','cost'))
        for m in agg: m['frontier']=m['model_key'] in frontier
        aggregate_sets[algorithm['id']]=agg

    sources=[]
    by_source=defaultdict(lambda:{'rows':0,'capability':0,'cost':0,'label':'','url':'','date':''})
    for r in observation_rows:
        d=by_source[r['source_id']]; d['rows']+=1; axis=r.get('metric_axis','other'); d[axis]=d.get(axis,0)+1; d['label']=r['source_label']; d['url']=r['source_url']; d['date']=r.get('source_date','')
    for source_id,d in sorted(by_source.items()): sources.append({'source_id':source_id,**d})

    generated_at = TODAY  # date stamp only: keeps rebuilds byte-identical (see _build_date)
    payload={'generated_at':generated_at,'config':config,'algorithms':algorithms,'sources':sources,'models':models,'observations':compact_obs,'aggregate_sets':aggregate_sets,'calibration_reports':reports}
    return {'row_count':len(rows),'observation_count':len(observation_rows),'model_count':len(models),'algorithm_count':len(algorithms),'calibration_group_count':len(groups),'reports':reports,'models':models,'aggregate_sets':aggregate_sets,'payload':payload, 'generated_at': generated_at}




ROOT=Path(__file__).resolve().parent
CSV_PATH=ROOT/'data/unified-model-evidence.csv'
CONFIG_PATH=ROOT/'project-config.json'
DASHBOARD_PATH=ROOT/'dashboard.html'
PARETO_PATH=ROOT/'pareto-frontier-cheatsheet.md'
TIERS_PATH=ROOT/'model-tiers-and-contenders.md'
INDEX_PATH=ROOT/'INDEX.md'
def _build_date() -> str:
    """The only wall-clock value in a build: a calendar date (UTC).

    Two builds on the same day are byte-identical. SOURCE_DATE_EPOCH, when set,
    pins the date so a rebuild on another day can be compared byte for byte.
    """
    epoch=os.environ.get('SOURCE_DATE_EPOCH','').strip()
    if epoch.isdigit(): return datetime.fromtimestamp(int(epoch),timezone.utc).date().isoformat()
    return datetime.now(timezone.utc).date().isoformat()
TODAY=_build_date()
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
            'source_version':'7.4.0','source_date':TODAY,'source_url':'project-config.json','retrieved_at':'2026-08-08T10:46:00-07:00',
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

def ana_dispersion(values):
    """Spread statistics for one model's calibrated observations.

    ANNOTATION ONLY. Nothing here feeds back into the capability value or into
    the Pareto computation. Confidence must not distort the estimate: weighting
    by inverse variance would shrink thinly-measured models toward the mean and
    move points on the graph for reasons unrelated to the models. The estimate
    stays where the measurements put it; this describes how well we know it.

    Added 2026-08-20 after an audit found 510 of 616 models resting on a single
    observation, with `source_count` computed and then used only as a display
    column. Selection code may consume `std_err`; the plot must not.
    """
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n == 0:
        return {"n": 0, "std_dev": None, "std_err": None, "spread": None,
                "provisional": True}
    if n == 1:
        return {"n": 1, "std_dev": None, "std_err": None, "spread": 0.0,
                "provisional": True}
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)
    sd = math.sqrt(var)
    return {"n": n, "std_dev": sd, "std_err": sd / math.sqrt(n),
            "spread": max(vals) - min(vals),
            # Fewer than three observations cannot support a spread estimate
            # worth trusting, so the point is flagged rather than excluded.
            "provisional": n < 3}


# A calibrated observation this many robust deviations from the model's own
# median is treated as a scale error rather than a disagreement. Set from the
# observed failure: kimi-k3-max carried a spread of 1346 calibrated points with
# one value at 30.8, which can only mean a source was on a different scale
# entirely. A robust fitter suppresses an outlier's influence on the FIT; it
# does nothing to stop a mis-scaled value entering the AGGREGATE.
SCALE_OUTLIER_MADS = 6.0


def ana_scale_filter(items, model_key, problems=None):
    """Drop observations that cannot be on the same scale as their siblings.

    Uses median absolute deviation, which does not itself collapse in the
    presence of the outlier it is looking for. Quarantined values are reported,
    never silently discarded, because a quarantine is a data-quality finding
    about a source and needs to be visible.
    """
    vals = [v for v, w, r in items if v is not None]
    if len(vals) < 4:
        return items, []
    med = statistics.median(vals)
    devs = sorted(abs(v - med) for v in vals)
    mad = statistics.median(devs)
    if mad <= 0:
        return items, []
    keep, dropped = [], []
    for v, w, r in items:
        if v is not None and abs(v - med) > SCALE_OUTLIER_MADS * mad:
            dropped.append({"model": model_key, "value": v, "median": med,
                            "source_id": r.get("source_id"),
                            "metric": r.get("metric_name")})
            if problems is not None:
                problems.append({
                    "path": f"scale:{model_key}",
                    "reason": (f"observation {v:.4g} is more than "
                               f"{SCALE_OUTLIER_MADS:g} MADs from the model "
                               f"median {med:.4g}; quarantined as a probable "
                               f"scale error from source "
                               f"{r.get('source_id')}")})
        else:
            keep.append((v, w, r))
    return keep, dropped


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
    scale_dropped_total=0
    scale_problems=[]
    for key,meta in catalog.items():
        g=groups[key]
        # Quarantine mis-scaled observations BEFORE aggregating. This changes
        # the estimate, and it is meant to: a value on the wrong scale is not a
        # disagreement to average in, it is bad data.
        cap_items, cap_dropped = ana_scale_filter(g['cap'], key, scale_problems)
        scale_dropped_total += len(cap_dropped)
        cap=ana_wmean([(v,w) for v,w,r in cap_items])
        cap_disp=ana_dispersion([v for v,w,r in cap_items])
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
            'capability':cap,
            # Annotation only. See ana_dispersion.
            'capability_std_err':cap_disp['std_err'],
            'capability_std_dev':cap_disp['std_dev'],
            'capability_spread':cap_disp['spread'],
            'capability_provisional':cap_disp['provisional'],
            'capability_scale_dropped':len(cap_dropped),
            'aa_reference':max(g['aa']) if g['aa'] else None,'cost':cost,'raw_standardized_cost':raw_proxy,
            'cost_method':' + '.join(sorted({ana_cost_label(r) for v,w,r in used})) if used else 'unpriced',
            'cost_sources':sorted({r.get('source_id') for v,w,r in used}),
            'source_count':len({r.get('source_id') for r in g['all'] if r.get('source_id')}),
            'capability_rows':len(cap_items),'cost_rows':len(g['cost']),
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
        if r.get('record_type')!='observation' or r.get('source_id') not in ('artificial-analysis-current','aa-primary-current'):continue
        if not ana_truthy(r.get('use_in_aggregate')):continue
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
        if not m['current'] or m.get('capability') is None or not m['model_key'].startswith(prefixes):continue
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
    order={'none':0,'non-reasoning':0,'low':1,'medium':2,'high':3,'xhigh':4,'max':5,'default':3}
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
        if r.get('record_type')!='observation' or r.get('source_id') not in ('artificial-analysis-current','aa-primary-current'):continue
        if not ana_truthy(r.get('use_in_aggregate')):continue
        v=ana_number(r.get('raw_value'));
        if v is None:continue
        if r.get('metric_name')=='aa_intelligence_index':aa[r['model_key']]['capability']=v
        elif r.get('metric_name')=='aa_cost_per_task_usd':aa[r['model_key']]['cost']=v
    aa_pts=[]
    for k,d in aa.items():
        if 'capability' not in d or 'cost' not in d or d['cost']<=0:continue
        label=catalog.get(k,{}).get('display_name',k)
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
                                   'note':'Exact current AA v4.2 Intelligence Index vs public numeric Cost per Intelligence Index Task rows in the package (114 positively priced configurations, 21 strict Pareto points).'},
            'kilo':{'points':sorted(kp,key=lambda x:x['cost']),'frontier_keys':sorted(kk),
                    'note':'Independent coding-agent completion vs cost per attempt; not calibrated into the AA task-cost plane.'},
            'vals':{'points':vals,'frontier_keys':sorted(vk),'note':'Current Vals Index accuracy vs Cost/Test; independent source-specific Pareto cross-check, not an AA task-cost substitute.'}}

PRIMARY_SOURCE_ID='aa-primary-current'
PRIMARY_LABELS={'briefcase':'AA-Briefcase','automation':'AutomationBench-AA','terminal':'Terminal-Bench 4.0','coding':'FrontierCode 2.0',
    'accuracy':'AA-Omniscience accuracy','nonhallucination':'AA-Omniscience non-hallucination','pdf':'GDP.pdf','hle':'HLE (diamond)',
    'physics':'CritPt v2 hard','science':'Terminal-Bench Science'}

def primary_score(components, weights):
    """Weighted mean of components (0-100) for weights > 0; None unless every weighted component is present.

    Identical rule to current_frontier.score_components and to the dashboard's offline tier weighting.
    """
    total=sum(w for w in weights.values() if w>0)
    if total<=0: return None
    if any(components.get(k) is None for k,w in weights.items() if w>0): return None
    return sum(components[k]*w for k,w in weights.items() if w>0)/total

def ana_current_primary(rows):
    """Compact, offline-reweightable view of the primary AA v4.2 recomputation (source aa-primary-current).

    Every catalog row of the primary source is kept: scored or not, priced or not.
    Missing stays None (JSON null); a cost of 0 stays 0 but is only treated as a price when it is verified
    (cost_state 'zero-verified'); an unverified $0 ('zero-unverified') is kept visible and held out of dominance.
    No Priors value enters this block.
    """
    sys_path_added=False
    import sys
    if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT)); sys_path_added=True
    try:
        import current_frontier as cf
        BENCHMARKS=cf.BENCHMARKS
    finally:
        if sys_path_added: sys.path.remove(str(ROOT))
    benchmarks=[{'id':k,'label':PRIMARY_LABELS[k],'weight':w,'tier':t} for k,(_,w,t) in BENCHMARKS.items()]
    weights={b['id']:b['weight'] for b in benchmarks}
    cat={}; obs=defaultdict(dict)
    for r in rows:
        if r.get('source_id')!=PRIMARY_SOURCE_ID: continue
        key=r['model_key']
        if r.get('record_type')=='catalog': cat[key]=r
        elif r.get('record_type')=='observation':
            name=r.get('metric_name','')
            if name in obs[key]: raise RuntimeError(f'duplicate primary observation {key} {name}')
            obs[key][name]=ana_number(r.get('raw_value'))
    out=[]; mismatches=[]
    for key in sorted(cat):
        r=cat[key]; o=obs.get(key,{})
        comps={b['id']:o.get('aa_component_'+b['id']) for b in benchmarks}
        score=primary_score(comps,weights); published=o.get('aa_intelligence_index')
        if score is not None and published is not None and abs(score-published)>1e-6: mismatches.append(key)
        name=r.get('display_name','')
        out.append({'id':key,'name':name,'provider':r.get('provider',''),'family':r.get('family',''),'effort':r.get('effort',''),
            'fallback':'fallback' in name.lower(),'release':r.get('release_date','') or None,
            'components':comps,'score':score,'cost':o.get('aa_cost_per_task_usd'),'url':r.get('source_url','')})
    if mismatches: raise RuntimeError('primary composite differs from the recomputed one for: '+', '.join(mismatches[:5]))
    cf.classify_cost_states(out)  # zero is a price only when a free route with the same name is listed; see current_frontier.comparable
    retrieved=sorted({r.get('retrieved_at','') for r in cat.values() if r.get('retrieved_at')})
    return {'source_id':PRIMARY_SOURCE_ID,'retrieved_at':retrieved[-1] if retrieved else None,'benchmarks':benchmarks,'rows':out,
        'note':'Artificial Analysis v4.2 10-benchmark composite recomputed by ARDF from AA components; costs are AA workload costs per task. No Priors value enters this block.'}

# ---------------------------------------------------------------------------
# ARDF-REC-03: routing rules of thumb, full frontier for all models, free routes.
# Everything below is computed from the primary AA block and the pinned snapshots
# in sources/current/; no number in the generated documents is typed by hand.
# ---------------------------------------------------------------------------
FREE_ROUTE_ALIASES={'nemotron3ultra':'Nemotron 3 Ultra 550B A55B'}  # route-name key -> primary model-name prefix (identity still flagged)
MAX_RULES=12

def _norm_key(text: str) -> str:
    return re.sub(r'[^a-z0-9]','',text.lower())

def _dominates(a,b):
    return a['cost']<=b['cost'] and a['score']>=b['score'] and (a['cost']<b['cost'] or a['score']>b['score'])

def _frontier(pool):
    return sorted([r for r in pool if not any(_dominates(o,r) for o in pool if o is not r)],key=lambda r:(r['cost'],-r['score'],r['id']))

def _money(v):
    if v is None: return 'unknown'
    if v==0: return '$0'
    return f'${v:.3g}' if v<1 else f'${v:.2f}'

def _label(r):
    return r['name']

def _median(vals):
    vals=sorted(vals); n=len(vals)
    if not n: return None
    return vals[n//2] if n%2 else (vals[n//2-1]+vals[n//2])/2

def _read_pinned(name, manifest):
    p=ROOT/'sources/current'/name
    expected=manifest.get('sha256',{}).get(name)
    raw=p.read_bytes()
    if expected and hashlib.sha256(raw).hexdigest()!=expected: raise RuntimeError('Snapshot checksum mismatch: '+name)
    import gzip
    return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw.decode('utf-8'))

def ana_free_routes(cp, pool, frontier):
    """Evaluate zero-price routes listed in the pinned Kilo, OpenRouter and OpenCode Zen catalogs against scored configurations."""
    sys_path_added=False
    import sys
    if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT)); sys_path_added=True
    try: import current_frontier as cf
    finally:
        if sys_path_added: sys.path.remove(str(ROOT))
    routes=[dict(x) for x in cf.catalog_routes() if x['free']]
    def kind(r):
        n=r['route_id'].lower()
        if 'free' in n and ('router' in r['name'].lower() or n in ('openrouter/free','kilo-auto/free')): return 'router (not a stable model)'
        if n.startswith('stealth/') or 'alpha' in n or 'glyph' in n: return 'stealth or preview (identity unverified)'
        if 'safety' in n: return 'safety classifier'
        if any(x in n for x in ('lyria',)) or r['modalities']!=['text'] and r['modalities']: return 'non-text output'
        return 'chat model'
    primary_names={}
    for r in cp['rows']: primary_names.setdefault(_norm_key(re.sub(r'\s*\(.*\)$','',r['name'])),[]).append(r)
    def clean(n):
        n=re.sub(r'^[^:]*:\s*','',n); n=re.sub(r'\(free\)|\bfree\b','',n,flags=re.I); return _norm_key(n)
    def match(route):
        key=clean(route['name']); hit=[]; how=''
        for pk,rows in primary_names.items():
            if pk==key: hit+=rows; how='name match'
            elif pk.startswith(key) and pk[len(key):].isdigit() and key: hit+=rows; how='name match, snapshot or version suffix ignored (identity unverified)'
        if not hit and key in FREE_ROUTE_ALIASES:
            pref=_norm_key(FREE_ROUTE_ALIASES[key]); hit=[r for r in cp['rows'] if _norm_key(r['name']).startswith(pref)]; how='explicit alias (identity unverified)'
        return hit,how
    def aa_effort(r):
        # AA's effort slug as something a catalog effort list can be compared with: a literal level; 'none' only when AA's own
        # name says non-reasoning; otherwise None (AA records no level for this configuration, so no catalog level matches it).
        e=r['effort']
        if e not in (None,'','none','default'): return e
        return 'none' if 'non-reasoning' in r['name'].lower() else None
    groups={}; unscored=[]
    for rt in routes:
        rt['kind']=kind(rt)
        hit,how=match(rt)
        scored=[h for h in hit if h['score'] is not None]
        if not scored:
            unscored.append({**rt,'why':'no matching primary configuration' if not hit else 'matching primary configuration has no complete score'}); continue
        best=max(scored,key=lambda h:(h['score'],h['id'])); fam=best['family'] or best['name']
        g=groups.setdefault(fam,{'rows':{},'routes':[],'how':how,'efforts':set(),'can_disable':False,'defaults':set()})
        for h in scored:
            if (h['family'] or h['name'])==fam: g['rows'][h['id']]=h
        g['routes'].append(rt); g['efforts']|=set(rt['efforts']); g['can_disable']|=bool(rt['can_disable'])
        if rt['default_effort']: g['defaults'].add(rt['default_effort'])
        if 'unverified' in how: g['how']=how
    by_model={}
    for fam,g in groups.items():
        levels={e for e in g['efforts'] if e!='none'}; off_ok=g['can_disable'] or 'none' in g['efforts']
        variants=[]
        for h in g['rows'].values():
            lab=aa_effort(h)
            support='assumed' if lab is None else ('listed' if (lab in levels or (lab=='none' and off_ok)) else 'not offered')
            variants.append({'name':h['name'],'effort':h['effort'],'score':h['score'],'cost':h['cost'],'support':support,'id':h['id'],'row':h})
        listed=[v for v in variants if v['support']=='listed']; assumed=[v for v in variants if v['support']=='assumed']
        use=listed or assumed
        if not use:
            for rt in g['routes']:
                unscored.append({**rt,'why':'AA measured this model only at efforts the route does not list ('+', '.join(sorted({v['effort'] for v in variants}))+')'})
            continue
        lo=min(use,key=lambda v:(v['score'],v['id'])); hi=max(use,key=lambda v:(v['score'],v['id']))
        head=hi if listed else lo
        cat_levels=', '.join(sorted(levels|({'none'} if off_ok else set()),key=lambda e:['none','minimal','low','medium','high','xhigh','max'].index(e) if e in ['none','minimal','low','medium','high','xhigh','max'] else 99)) or 'no effort levels'
        default_txt=('the catalog default is '+'/'.join(sorted(g['defaults']))) if g['defaults'] else 'the catalog states no default effort'
        if listed:
            if lo is hi: note=f"AA measured only {hi['effort']}, which the catalog lists (catalog efforts: {cat_levels}); {default_txt}, so the score applies when that effort is selected."
            else: note=f"Ceiling at {hi['effort']} (highest catalog-listed effort AA measured); floor {lo['score']:.2f} at {lo['effort']}. Catalog efforts: {cat_levels}; {default_txt}, so a route used at its default can land anywhere in {lo['score']:.2f} to {hi['score']:.2f}."
            if any(v['support']=='assumed' for v in variants): note+=' Variants with no AA effort level are not used.'
        else:
            note=f"Assumption: AA records no effort level for this configuration, so no catalog level can be matched to it (catalog: {cat_levels}). The score holds only if the route runs AA's measured configuration, which is unverified."
            if lo is not hi: note+=f" Several AA configurations qualify; the lowest ({lo['score']:.2f}) is shown and {hi['score']:.2f} is an unverified ceiling."
        excluded=[v for v in variants if v['support']=='not offered']
        if excluded: note+=' Not offered by the route, excluded: '+', '.join(f"{v['name']} {v['score']:.2f}" for v in sorted(excluded,key=lambda v:v['score']))+'.'
        by_model[fam]={'model':head['name'],'provider':head['row']['provider'],'effort':head['effort'],'score':head['score'],'aa_workload_cost':head['cost'],'how':g['how'],
            'effort_basis':'catalog-listed' if listed else 'assumed','score_low':lo['score'],'score_high':hi['score'],'effort_note':note,
            'variants':[{k:v[k] for k in ('name','effort','score','support')} for v in sorted(variants,key=lambda v:(v['score'],v['id']))],
            'routes':[{k:rt[k] for k in ('surface','route_id','kind','may_train')} for rt in g['routes']]}
    out=[]
    for e in by_model.values():
        paid=[r for r in pool if r['cost'] and r['cost']>0 and r['score']>=e['score']-1e-12]
        cheaper=min(paid,key=lambda r:(r['cost'],-r['score'],r['id'])) if paid else None
        e['cheapest_paid_at_least']= {'name':cheaper['name'],'cost':cheaper['cost'],'score':cheaper['score']} if cheaper else None
        e['model_row_on_frontier']=any(f['name']==e['model'] for f in frontier)
        out.append(e)
    out.sort(key=lambda e:(-e['score'],e['model']))
    zero=sorted([r for r in cp['rows'] if r['score'] is not None and r['cost']==0],key=lambda r:(-r['score'],r['id']))
    top=max((r['score'] for r in pool),default=None)
    best=out[0] if out else None
    return {'models':out,'unscored_routes':sorted(unscored,key=lambda r:(r['surface'],r['route_id'])),'route_count':len(routes),
        'aa_zero_cost':[{'name':r['name'],'score':r['score'],'cost':0,'cost_state':r['cost_state'],'evidence':r['cost_evidence']} for r in zero],'top_score':top,
        'best_free_score':best['score'] if best else None,'best_free_share_of_top':(best['score']/top if best and top else None)}

def _prior_ratio_rows():
    """Per-lab Priors API vs subscription cost ratios for identically named model and effort rows."""
    sys_path_added=False
    import sys
    if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT)); sys_path_added=True
    try: import current_frontier as cf
    finally:
        if sys_path_added: sys.path.remove(str(ROOT))
    api=cf.priors_rows('api'); sub={r['identity']:r for r in cf.priors_rows('subscription')}
    by_lab=defaultdict(list)
    for a in api:
        s=sub.get(a['identity'])
        if s and a['cost'] and s['cost'] and a['cost']>0 and s['cost']>0: by_lab[a['lab']].append(a['cost']/s['cost'])
    return {lab:_median(v) for lab,v in by_lab.items() if len(v)>=3}, cf, api

def ana_routing(cp):
    """Rules of thumb (at most MAX_RULES), the full all-model frontier and the free-route evaluation."""
    rows=cp['rows']
    known=[r for r in rows if r['score'] is not None and r['cost'] is not None and r['cost']>=0]
    # An AA price of $0 enters dominance only when a free route with the same name is listed in a pinned catalog.
    held=sorted([r for r in known if r['cost_state']=='zero-unverified'],key=lambda r:(-r['score'],r['id']))
    pool=[r for r in known if r['cost_state']!='zero-unverified']
    priced=[r for r in pool if r['cost']>0]
    frontier=_frontier(pool); fids={r['id'] for r in frontier}
    paid_frontier=_frontier(priced)
    dominated=[r for r in pool if r['id'] not in fids]
    def cheapest_at_least(t,src=priced):
        c=[r for r in src if r['score']>=t]
        return min(c,key=lambda r:(r['cost'],-r['score'],r['id'])) if c else None
    # full frontier: global, and each provider's own frontier
    by_provider=defaultdict(list)
    for r in pool: by_provider[r['provider']].append(r)
    provider_frontiers=[]
    for prov,items in by_provider.items():
        pf=_frontier(items)
        provider_frontiers.append({'provider':prov,'scored_configurations':len(items),'frontier':[{**{k:r[k] for k in ('id','name','effort','score','cost','fallback')},'on_global_frontier':r['id'] in fids} for r in pf]})
    provider_frontiers.sort(key=lambda p:(-p['scored_configurations'],p['provider']))
    free=ana_free_routes(cp,pool,frontier)
    rules=[]
    def rule(text,data): rules.append({'n':len(rules)+1,'rule':text,'data':data})
    # 1 frontier first
    worst=max(dominated,key=lambda r:r['cost']) if dominated else None
    if worst:
        dom=min([f for f in frontier if _dominates(f,worst)],key=lambda f:(f['cost'],-f['score']))
        ex=f"{_label(worst)} ({worst['score']:.2f}, {_money(worst['cost'])}) is dominated by {_label(dom)} ({dom['score']:.2f}, {_money(dom['cost'])})."
    else: ex='no dominated configuration'
    rule('Choose from the frontier first; a dominated configuration has a cheaper or equal and at least as good alternative.',f"{len(frontier)} of {len(pool)} scored configurations with a trusted cost are undominated ({len(paid_frontier)} of {len(priced)} when only prices above $0 count); {len(held)} scored configurations with an unverified AA price of $0 are held out of both (full lists: docs/full-frontier.md). Example: {ex}")
    # 2 cheapest to reach a score
    ts=[20,30,40,50,55,60]; steps=[(t,cheapest_at_least(t)) for t in ts]
    steps=[(t,c) for t,c in steps if c]
    rule('To reach a target score, start with the cheapest configuration that clears it.','Cheapest priced configuration at or above each score: '+'; '.join(f"{t}: {_label(c)} {_money(c['cost'])}" for t,c in steps)+'.')
    # 3 cost of next points
    lo,hi=cheapest_at_least(40),cheapest_at_least(60)
    if lo and hi: rule('Each extra point at the top costs far more than at the bottom; buy the top tier only when the task needs it.',f"Cheapest config at 40 or more is {_money(lo['cost'])}; at 60 or more it is {_money(hi['cost'])}, {hi['cost']/lo['cost']:.1f}x as much ({_label(lo)} versus {_label(hi)}).")
    # 4 max versus xhigh
    # Effort ladders per model family (provider, name without its trailing parenthetical, fallback track). A family is used only
    # when every effort in it has exactly one row, so no step compares an ambiguous pair.
    order=['none','minimal','low','medium','high','xhigh','max']
    fam=defaultdict(lambda:defaultdict(list))
    for r in priced:
        base=re.sub(r'\s*\((?:[^)]*)\)\s*$','',r['name'])
        fam[(r['provider'],base,r['fallback'])][r['effort']].append(r)
    ladders={k:{e:v[0] for e,v in d.items()} for k,d in fam.items() if all(len(v)==1 for v in d.values())}
    def money_x(a,b): return f"{b['cost']/a['cost']:.2f}x cost"
    pairs=[(v['xhigh'],v['max']) for v in ladders.values() if 'xhigh' in v and 'max' in v]
    if pairs:
        ratios=[b['cost']/a['cost'] for a,b in pairs]; gains=[b['score']-a['score'] for a,b in pairs]
        onf=sum(1 for a,b in pairs if b['id'] in fids)
        worse=[(a,b) for a,b in pairs if b['score']<a['score']-1e-9]
        wtxt=('; '.join(f"{_label(b)} scores {b['score']:.2f} against {_label(a)} {a['score']:.2f} ({b['score']-a['score']:+.2f}) at {money_x(a,b)}" for a,b in worse) or 'none')
        rule('Treat max effort as an exception: price it against xhigh on your task before using it.',f"Across {len(pairs)} families with both settings, max costs a median {_median(ratios):.2f}x xhigh (range {min(ratios):.2f}x to {max(ratios):.2f}x) for a median {_median(gains):+.2f} points (range {min(gains):+.2f} to {max(gains):+.2f}). Max scored lower than xhigh in {len(worse)} of {len(pairs)}: {wtxt}. {onf} of {len(pairs)} max configurations are on the frontier.")
    # 5 effort steps inside a family: the only evidence that a higher setting does not always score higher
    steps=[]
    for v in ladders.values():
        es=[e for e in order if e in v]
        steps+=[(v[a],v[b]) for a,b in zip(es,es[1:])]
    regress=sorted([(a,b) for a,b in steps if b['score']<a['score']-1e-9],key=lambda p:p[1]['score']-p[0]['score'])
    eff=defaultdict(int)
    for r in frontier: eff[r['effort']]+=1
    if steps:
        rtxt='; '.join(f"{_label(b)} {b['score']:.2f} against {_label(a)} {a['score']:.2f} ({b['score']-a['score']:+.2f}, {money_x(a,b)})" for a,b in regress) or 'none'
        rule('A higher effort setting does not always score higher: compare the step you are buying inside the same model before paying for it.',
            f"Across {len(ladders)} model families, {len(steps)} adjacent effort steps (for example low to medium); the higher setting scored lower in {len(regress)}: {rtxt}. Context only, and not evidence of non-monotonicity because it compares different models: frontier members by effort are "+', '.join(f"{e} {eff[e]}" for e in order if eff.get(e))+f" of {len(frontier)} ({', '.join(e for e in order if not eff.get(e)) or 'every effort'} appear on no frontier row).")
    # 6 fallback tracks
    fb=[r for r in pool if r['fallback']]
    fb_all=[r for r in rows if r['fallback']]
    fb_unscored=[r for r in fb_all if r['score'] is None]
    pairs_fb=[]
    stdmap={(r['provider'],re.sub(r',?\s*Default Fallback','',r['name']),r['effort']):r for r in pool if not r['fallback']}
    for r in fb:
        s=stdmap.get((r['provider'],re.sub(r',?\s*Default Fallback','',r['name']),r['effort']))
        if s and s['cost'] and r['cost']: pairs_fb.append((s,r))
    if fb:
        extra=f" Compared with their standard track ({len(pairs_fb)} pairs) the fallback track costs a median {_median([b['cost']/a['cost'] for a,b in pairs_fb]):.2f}x with a median score difference of {_median([b['score']-a['score'] for a,b in pairs_fb]):+.2f}." if pairs_fb else ''
        fbprov=defaultdict(int)
        for r in fb: fbprov[r['provider']]+=1
        allprov=defaultdict(int); fbfront=defaultdict(int)
        for r in frontier:
            allprov[r['provider']]+=1
            if r['fallback']: fbfront[r['provider']]+=1
        nf_front=_frontier([r for r in pool if not r['fallback']])
        rule('Treat default-fallback tracks as their own configurations, not as the standalone model; the pinned data does not say what the fallback covers.',
            f"AA lists {len(fb_all)} fallback tracks, {len(fb)} scored ({', '.join(f'{p} {n}' for p,n in sorted(fbprov.items()))}) and {len(fb_unscored)} unscored ({', '.join(_label(r) for r in fb_unscored) or 'none'}); {('none of them has' if not pairs_fb else f'only {len(pairs_fb)} of them have')} a scored standard-track counterpart, so {('none can' if not pairs_fb else 'most cannot')} be compared with a standard track.{extra} Fallback tracks are {sum(fbfront.values())} of {len(frontier)} frontier members ({', '.join(f'{p} {fbfront[p]} of {allprov[p]}' for p in sorted(fbfront)) or 'none'}). Without them the frontier has {len(nf_front)} members (fallback-free frontier in docs/full-frontier.md), and every fallback track is tagged in that document.")
    # 7 providers: each provider's frontier members and the score band they cover
    prov=defaultdict(list)
    for r in frontier: prov[r['provider']].append(r)
    def band(p):
        m=prov[p]; fbm=[r for r in m if r['fallback']]
        s=f"{p} {len(m)} ({min(r['score'] for r in m):.2f} to {max(r['score'] for r in m):.2f}"
        if fbm and len(fbm)==len(m): s+=', all fallback tracks'
        elif fbm:
            top_std=max(r['score'] for r in m if not r['fallback']); above=[r for r in m if r['score']>top_std]
            s+=f", {len(fbm)} fallback tracks"+(f"; every member above {top_std:.2f} is a fallback track" if above and all(r['fallback'] for r in above) else '')
        return s+')'
    rule('No single provider holds the whole frontier: before locking to one, check that it is on the frontier at the score you need.',
        'Frontier members by provider, with the lowest and highest score of those members (the span between first and last member, not a guarantee that every score in between is covered): '+'; '.join(band(p) for p in sorted(prov,key=lambda p:(-len(prov[p]),p)))+f". Frontier score range overall: {min(r['score'] for r in frontier):.2f} to {max(r['score'] for r in frontier):.2f}. Each provider's own frontier is in docs/full-frontier.md.")
    # 8 zero cost
    zc=free['aa_zero_cost']
    if zc:
        ver=[z for z in zc if z['cost_state']=='zero-verified']; unv=[z for z in zc if z['cost_state']=='zero-unverified']
        best0=max(zc,key=lambda z:z['score']); paid0=cheapest_at_least(best0['score'])
        rule('Do not trust an AA price of $0 until a free route with the same name is listed; unverified $0 configurations stay out of the frontier, and a verified one still needs its rate limits and terms checked.',
            f"AA lists {len(zc)} scored $0 configurations. Verified free route: "+('; '.join(f"{z['name']} {z['score']:.2f} ({z['evidence']})" for z in ver) or 'none')
            +". Unverified, held out of dominance: "+('; '.join(f"{z['name']} {z['score']:.2f} ({z['evidence']})" for z in unv) or 'none')
            +f". For scale, the best of all three ({best0['score']:.2f}) is matched by a paid configuration at {_money(paid0['cost']) if paid0 else 'n/a'} ({_label(paid0) if paid0 else 'n/a'}).")
    # 9 free routes
    fm=free['models']
    if fm:
        b=fm[0]; pc=b['cheapest_paid_at_least']
        n_listed=sum(1 for e in fm if e['effort_basis']=='catalog-listed')
        if b['effort_basis']=='catalog-listed':
            basis=(f"a ceiling: it is the score at {b['effort']}, the highest effort its route lists that AA measured"+(f", with a floor of {b['score_low']:.2f}" if b['score_low']!=b['score'] else '')+'; the catalog states no default, so default use can score lower')
        else: basis="an assumption: AA records no effort level for it, so the score holds only if the route runs AA's measured configuration"
        rule('Use free routes for bounded, verifiable work; their scores are ceilings or assumptions, and even the ceiling is well below the paid frontier.',
            f"{len(fm)} free-route models have a measured score ({free['route_count']} free catalog entries in total); {n_listed} are scored at an effort their route lists and {len(fm)-n_listed} on the assumption that the route runs AA's configuration. Highest: {b['model']} at {b['score']:.2f}{' (identity unverified)' if 'unverified' in b['how'] else ''}, {basis}; that is at most {free['best_free_share_of_top']*100:.0f}% of the top frontier score {free['top_score']:.2f}. The cheapest paid configuration at or above it is {_label_dict(pc)}. See docs/free-routes.md.")
    # 10 cost basis
    ratios,cf,priors_api=_prior_ratio_rows()
    if ratios:
        labs=sorted(ratios.items(),key=lambda x:-x[1])
        rule('Never mix cost bases: Priors subscription-equivalent costs sit below API workload costs by a lab-dependent factor.',"Median Priors API to subscription cost ratio by lab: "+', '.join(f"{l} {v:.1f}x" for l,v in labs)+'. ARDF costs are API workload costs.')
    # 11 source deltas
    deltas=ana_priors_deltas(cp,cf,priors_api)
    if deltas['matched']:
        rule('Keep each comparison within one source and one cost basis, even though ARDF and Priors scores agree closely.',f"On {deltas['matched']} of {deltas['priors_rows']} Priors API rows the independently recomputed ARDF score differs from Priors by a median {deltas['median_abs_score_delta']:.4f} and at most {deltas['max_abs_score_delta']:.4f} points; API cost differs by a median {deltas['median_abs_cost_delta']:.4f} and at most {deltas['max_abs_cost_delta']:.4f} USD per task. Exact table: docs/priors-deltas.md.")
    # 12 unscored
    uns=[r for r in rows if r['score'] is None]
    rule('No score is not a low score; it means the benchmark set is incomplete.',f"{len(uns)} of {len(rows)} primary configurations have no complete 10-benchmark score and are not ranked; they are listed on the dashboard's unscored shelf.")
    if len(rules)>MAX_RULES: raise RuntimeError('too many routing rules')
    cols=('id','name','provider','effort','score','cost','fallback')
    nofb=_frontier([r for r in pool if not r['fallback']])
    return {'rules':rules,'full_frontier':{'frontier':[{k:r[k] for k in cols} for r in frontier],'paid_frontier':[{k:r[k] for k in cols} for r in paid_frontier],'fallback_free_frontier':[{k:r[k] for k in cols} for r in nofb],
        'unverified_free':[{**{k:r[k] for k in cols},'evidence':r['cost_evidence']} for r in held],'by_provider':provider_frontiers,'pool_size':len(pool),'priced_size':len(priced)},'free':free,'priors_deltas':deltas}

def _label_dict(d):
    return f"{d['name']} at {_money(d['cost'])} ({d['score']:.2f})" if d else 'none (no paid configuration scores that high)'

def ana_priors_deltas(cp, cf, priors_api):
    """Exact ARDF minus Priors (API basis) score and cost differences, from current_frontier's own identity matching.

    Priors never enters ARDF scores; this only reports how the independent recomputation differs from it.
    """
    comps=cf.build()['comparisons']
    out=[]
    for c in comps:
        if not c['matched'] or c['score_delta'] is None: continue
        out.append({'name':c['name'],'match':'exact identity','ardf_score':c['ardf_score'],'priors_score':c['priors_score'],'delta':c['score_delta'],'ardf_cost':c['ardf_cost'],'priors_cost':c['priors_cost'],'cost_delta':c['cost_delta']})
    # Second pass, flagged: Priors rows whose model name embeds the effort (for example "Muse Ember (Xhigh)") fail the strict
    # identity; match them on the name without its trailing parenthetical plus the effort, only when that is unambiguous.
    strip=lambda s:re.sub(r'\s*\([^)]*\)\s*$','',s)
    eff=lambda e:'none' if e in (None,'','default') else str(e).lower()
    loose=defaultdict(list)
    for r in cp['rows']:
        if r['score'] is not None: loose[_norm_key(strip(r['name']))+'@'+eff(r['effort'])].append(r)
    prior_by_name={p['name']:p for p in priors_api}
    for c in comps:
        if c['matched']: continue
        p=prior_by_name.get(c['name'])
        if not p or p['score'] is None: continue
        hits=loose.get(_norm_key(strip(p['model']))+'@'+eff(p['effort']),[])
        if len(hits)!=1: continue
        a=hits[0]
        out.append({'name':c['name'],'match':'loose name plus effort (identity unverified)','ardf_score':a['score'],'priors_score':p['score'],'delta':a['score']-p['score'],'ardf_cost':a['cost'],'priors_cost':p['cost'],'cost_delta':(a['cost']-p['cost']) if a['cost'] is not None and p['cost'] is not None else None})
    out.sort(key=lambda d:(-abs(d['delta']),d['name']))
    cd=[abs(d['cost_delta']) for d in out if d['cost_delta'] is not None]
    matched_names={d['name'] for d in out}
    unmatched=[c['name'] for c in comps if c['name'] not in matched_names]
    return {'priors_rows':len(comps),'matched':len(out),'exact':sum(1 for d in out if d['match']=='exact identity'),'unmatched':unmatched,'rows':out,
        'median_abs_score_delta':_median([abs(d['delta']) for d in out]) if out else None,
        'max_abs_score_delta':max((abs(d['delta']) for d in out),default=None),
        'median_abs_cost_delta':_median(cd) if cd else None,'max_abs_cost_delta':max(cd,default=None),
        'largest':out[0] if out else None}

def render_routing_docs(routing, cp):
    stamp=f"Generated {TODAY} by `calibrate.py` from `sources/current/` (AA snapshot {str(cp['retrieved_at'])[:10]}). Do not edit by hand."
    L=['# ARDF routing rules of thumb','',stamp,'',
       'Short list. Every rule cites the data behind it. Scores are the AA v4.2 composite recomputed by ARDF; costs are AA workload costs per task in USD, not subscription bills. Starting hypotheses, not guarantees: verify availability, quota and terms at dispatch, and check a rule on your own task before relying on it.','']
    for r in routing['rules']:
        L+=[f"{r['n']}. **{r['rule']}**  ",f"   Data: {r['data']}"]
    L+=['','Related: `docs/full-frontier.md` (every frontier), `docs/free-routes.md` (free routes), `pareto-frontier-cheatsheet.md` (multi-source ledger frontier), `docs/current-frontier.md` (AA vs Priors).','']
    (ROOT/'docs/routing-rules.md').write_text('\n'.join(L),encoding='utf-8')
    F=routing['full_frontier']
    L=['# Full frontier for all models','',stamp,'',
       f"Primary AA v4.2 recomputation. Pool: {F['pool_size']} configurations with a complete score and a trusted cost: prices above $0, plus a $0 only when a free route with the same name is listed in a pinned catalog (verified free). Unknown cost is excluded. An AA $0 with no such route is unverified: it is held out of dominance and listed in its own band below, so it can neither dominate a paid model nor drop one from the frontier. A configuration is on the frontier when no other is at least as cheap and at least as good with one strict improvement; exact ties are kept. This is the measured universe, not every model that exists.",'',
       '**Warning on default-fallback tracks.** Rows marked FALLBACK are AA default-fallback tracks. The pinned data does not say what the fallback covers, and most have no scored standard-track counterpart, so read them as their own configurations, not as the standalone model. The fallback-free frontier is listed after the paid-only frontier.','',
       f"## All providers: {len(F['frontier'])} frontier configurations",'','| Cost / task | Score | Model | Track | Provider | Effort |','|---:|---:|---|---|---|---|']
    track=lambda r:'FALLBACK' if r['fallback'] else 'standard'
    L+=[f"| {_money(r['cost'])} | {r['score']:.2f} | {r['name']} | {track(r)} | {r['provider']} | {r['effort']} |" for r in F['frontier']]
    L+=['',f"## Paid-only frontier: {len(F['paid_frontier'])} configurations (prices above $0 only, {F['priced_size']} configurations)",'','Same rule with every $0 configuration removed, so it does not depend on whether any free route is real. `pareto-frontier-cheatsheet.md` applies the same cost above $0 rule to the multi-source ledger.','','| Cost / task | Score | Model | Track | Provider | Effort |','|---:|---:|---|---|---|---|']
    L+=[f"| {_money(r['cost'])} | {r['score']:.2f} | {r['name']} | {track(r)} | {r['provider']} | {r['effort']} |" for r in F['paid_frontier']]
    L+=['',f"## Fallback-free frontier: {len(F['fallback_free_frontier'])} configurations (standard tracks only, $0 rule as in the all-provider frontier)",'','The same pool with every default-fallback track removed, so each row is a standard AA track.','','| Cost / task | Score | Model | Provider | Effort |','|---:|---:|---|---|---|']
    L+=[f"| {_money(r['cost'])} | {r['score']:.2f} | {r['name']} | {r['provider']} | {r['effort']} |" for r in F['fallback_free_frontier']]
    L+=['',f"## Unverified free: {len(F['unverified_free'])} configurations (AA lists $0, held out of dominance)",'','These have a score and an AA price of exactly $0 but no free route with the same name in the pinned OpenRouter, Kilo or OpenCode Zen catalogs. They are not compared with any paid model.','','| Score | Model | Provider | Evidence |','|---:|---|---|---|']
    L+=[f"| {r['score']:.2f} | {r['name']} | {r['provider']} | {r['evidence']} |" for r in F['unverified_free']] or ['| | none | | |']
    L+=['','## Each provider\'s own frontier','','A provider\'s frontier is computed over that provider\'s configurations only. "Global" marks members that are also on the all-provider frontier above.','']
    for p in F['by_provider']:
        L+=[f"### {p['provider']} ({p['scored_configurations']} scored configurations, {len(p['frontier'])} on its frontier)",'','| Cost / task | Score | Model | Track | Effort | Global |','|---:|---:|---|---|---|:--:|']
        L+=[f"| {_money(r['cost'])} | {r['score']:.2f} | {r['name']} | {track(r)} | {r['effort']} | {'yes' if r['on_global_frontier'] else ''} |" for r in p['frontier']]
        L+=['']
    (ROOT/'docs/full-frontier.md').write_text('\n'.join(L),encoding='utf-8')
    R=routing['free']
    L=['# Free-route evaluation','',stamp,'',
       f"Source: zero-price entries in the pinned OpenRouter, Kilo and OpenCode Zen catalogs ({R['route_count']} entries), matched to the primary AA scores by model name. A match ignores snapshot or version suffixes and is marked unverified when it does; zero listed price does not remove rate limits, privacy terms or availability changes. Scores are the AA v4.2 composite recomputed by ARDF. A score is used only at an effort the route's own catalog lists (AA's effort `none` counts as reasoning off only when AA's name says non-reasoning). When the catalog lists effort levels and AA measured several, the table shows the ceiling at the highest listed effort with the floor beside it; the catalogs do not state which effort a route runs by default, so a ceiling is a best case, not the expected score. When AA records no effort level, the score is an explicit assumption that the route runs AA's measured configuration.",'',
       '## Free routes with a measured score','','| Headline score | Floor to ceiling | Model (headline configuration) | Effort evidence | Match | Routes | Cheapest paid configuration at or above the headline | Model on frontier at its paid price |','|---:|---:|---|---|---|---|---|:--:|']
    for e in R['models']:
        rts='; '.join(f"{x['surface']} `{x['route_id']}`"+(' (may train on prompts)' if x['may_train'] else '') for x in e['routes'])
        label='CEILING' if e['effort_basis']=='catalog-listed' and e['score_low']!=e['score_high'] else 'LISTED' if e['effort_basis']=='catalog-listed' else 'ASSUMED'
        rng=f"{e['score_low']:.2f} to {e['score_high']:.2f}" if e['score_low']!=e['score_high'] else f"{e['score']:.2f}"
        L.append(f"| {e['score']:.2f} | {rng} | {e['model'] if e['model'].endswith(')') else e['model']+' ('+e['effort']+')'} | **{label}**: {e['effort_note']} | {e['how']} | {rts} | {_label_dict(e['cheapest_paid_at_least'])} | {'yes' if e['model_row_on_frontier'] else 'no'} |")
    L+=['','The paid price of these models (AA workload cost per task, headline configuration) is: '+'; '.join(f"{e['model']} {_money(e['aa_workload_cost'])}" for e in R['models'])+'.','',
        '## AA lists a $0 price: verified or not','','A $0 price from AA counts as verified only when a free route with the same name is listed in a pinned catalog. Unverified rows are held out of the frontier (see `docs/full-frontier.md`).','','| Score | Model | Status | Evidence |','|---:|---|---|---|']
    L+=[f"| {z['score']:.2f} | {z['name']} | {'verified free route' if z['cost_state']=='zero-verified' else 'unverified'} | {z['evidence']} |" for z in R['aa_zero_cost']]
    L+=['','## Free routes with no measured score','','No usable score exists in the pinned data, so they are not ranked. Names do not establish identity.','','| Surface | Route | Kind | Why |','|---|---|---|---|']
    L+=[f"| {r['surface']} | `{r['route_id']}` | {r['kind']} | {r['why']} |" for r in R['unscored_routes']]
    L+=['']
    (ROOT/'docs/free-routes.md').write_text('\n'.join(L),encoding='utf-8')
    D=routing['priors_deltas']
    L=['# ARDF recomputation versus Priors: exact deltas','',stamp,'',
       f"ARDF scores and costs are recomputed independently from the primary Artificial Analysis snapshot ({str(cp['retrieved_at'])[:10]}, {len(cp['rows'])} configurations preserved, {sum(1 for r in cp['rows'] if r['score'] is not None)} with a complete 10-benchmark score). Priors (API cost basis, snapshot in `sources/current/priors-api.json`) is a cross-check only; no Priors value enters any ARDF score or cost. Delta = ARDF minus Priors.",'',
       f"Matched {D['matched']} of {D['priors_rows']} Priors rows ({D['exact']} by exact identity, {D['matched']-D['exact']} by a flagged loose name-plus-effort pass). Score delta: median |d| {D['median_abs_score_delta']:.6f}, max |d| {D['max_abs_score_delta']:.6f}. Priors publishes two decimals, so a score delta up to 0.005 is rounding. Cost delta (USD per task): median |d| {D['median_abs_cost_delta']:.6f}, max |d| {D['max_abs_cost_delta']:.6f}.",'',
       '## Matched rows, largest absolute score delta first','','| Model / effort | Match | ARDF score | Priors score | Score delta | ARDF cost | Priors cost | Cost delta |','|---|---|---:|---:|---:|---:|---:|---:|']
    fmt=lambda v:'-' if v is None else repr(float(v))
    L+=[f"| {d['name']} | {d['match']} | {fmt(d['ardf_score'])} | {fmt(d['priors_score'])} | {fmt(d['delta'])} | {fmt(d['ardf_cost'])} | {fmt(d['priors_cost'])} | {fmt(d['cost_delta'])} |" for d in D['rows']]
    L+=['','## Priors rows not compared','','No ARDF configuration matched, or the matched ARDF configuration has no complete score.','']+([f"- {n}" for n in D['unmatched']] or ['None.'])+['']
    (ROOT/'docs/priors-deltas.md').write_text('\n'.join(L),encoding='utf-8')

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
    e=policy['executor']; candidates=[]; global_value=[]; t3_candidates=[]
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
        if m['capability']>=47.0:
            t3_candidates.append(valued)
    # Lower $/capability is better. No exponent, capability subtraction, or forced slot.
    global_value.sort(key=lambda x:(x['cost_per_capability'],-x['capability'],x['cost']))
    candidates.sort(key=lambda x:(x['cost_per_capability'],-x['capability'],x['cost']))
    t3_candidates.sort(key=lambda x:(x['cost_per_capability'],-x['capability'],x['cost']))
    # Collapse reasoning/effort siblings by model family and keep the best literal ratio from each family.
    best_by_family={}
    for c in candidates:
        fam=c.get('family') or c['model_key']
        if fam not in best_by_family: best_by_family[fam]=c
    shortlist=list(best_by_family.values())[:e['top_n']]
    t3_best_by_family={}
    for c in t3_candidates:
        fam=c.get('family') or c['model_key']
        if fam not in t3_best_by_family: t3_best_by_family[fam]=c
    t3_shortlist=list(t3_best_by_family.values())[:e['top_n']]
    # GPT-6 Luna effort curve across all 6 effort configurations.
    luna_order=['none','non-reasoning','low','medium','high','xhigh','max']
    luna_curve=sorted([{**x,'marginal_note':''} for x in global_value if x.get('family')=='GPT-6 Luna' and x.get('effort') in luna_order],key=lambda x:(luna_order.index(x['effort']),x['cost']))
    for i,x in enumerate(luna_curve):
        if i:
            prev=luna_curve[i-1]
            x['aa_gain_vs_previous']=(x['aa_reference'] or x['capability'])-(prev['aa_reference'] or prev['capability'])
            x['cost_increase_vs_previous_pct']=(x['cost']/prev['cost']-1)*100
    # Pinch-point contested pairs: configurations within 2.0 capability points and 25% cost of each other.
    pinch_points=[]
    scored_current=sorted([m for m in models if m['current'] and m['capability'] is not None and m['cost'] is not None and m['cost']>0],key=lambda x:(-x['capability'],x['cost']))
    for i,a in enumerate(scored_current):
        for b in scored_current[i+1:]:
            if a.get('family')==b.get('family'):continue
            cap_diff=abs(a['capability']-b['capability'])
            if cap_diff>2.0:continue
            min_c=min(a['cost'],b['cost']); max_c=max(a['cost'],b['cost'])
            cost_diff_pct=(max_c/min_c-1)*100 if min_c>0 else 999
            if cost_diff_pct<=25.0 and (a['frontier'] or b['frontier'] or a['capability']>=45.0):
                pinch_points.append({
                    'model_a':a['display_name'],'tier_a':a['tier']['id'],'cap_a':a['capability'],'cost_a':a['cost'],'frontier_a':a['frontier'],
                    'model_b':b['display_name'],'tier_b':b['tier']['id'],'cap_b':b['capability'],'cost_b':b['cost'],'frontier_b':b['frontier'],
                    'cap_delta':cap_diff,'cost_delta_pct':cost_diff_pct
                })
    pinch_points.sort(key=lambda x:(-max(x['cap_a'],x['cap_b']),x['cost_delta_pct']))
    top_end=ana_top_end_analysis(models,rows,policy); external=ana_external_frontier_comparisons(rows)
    data={'generated_at': TODAY,'current_primary':ana_current_primary(rows),'policy':policy,'counts':{'catalog':len(models),'current_paired':sum(1 for m in models if m['current'] and m['capability'] is not None and m['cost'] is not None and m['cost']>0),'frontier':len(frontier),'near_frontier':len(near)},'frontier':frontier,'near_frontier':near,'major_near_frontier':major,'executor_top5':shortlist,'executor_t3_top5':t3_shortlist,'executor_candidates':candidates[:20],'global_value_top20':global_value[:20],'luna_effort_curve':luna_curve,'pinch_points':pinch_points[:20],'top_end':top_end,'external_frontier_comparisons':external}
    PARETO_PATH.write_text(ana_render_md(data),encoding='utf-8')
    data['routing']=ana_routing(data['current_primary'])
    render_routing_docs(data['routing'],data['current_primary'])
    print(json.dumps(data['counts'],indent=2))
    print('executor $/cap (unrestricted):',[(x['display_name'],round(x['cost_per_capability'],8)) for x in shortlist])
    print('executor $/cap (T3+ floor>=47):',[(x['display_name'],round(x['cost_per_capability'],8)) for x in t3_shortlist])
    return data

def ana_money(v):return '-' if v is None else f'${v:.5g}'
def ana_f2(v):return '-' if v is None else f'{v:.2f}'
def ana_render_md(d):
    executor_floor=number(d['policy']['executor'].get('minimum_aggregate_capability'))
    executor_eligibility=(
        'No global capability floor. Named roles may apply visible, role-specific gates.'
        if executor_floor is None
        else f'Calibrated capability >= {executor_floor:.0f}.'
    )
    lines=['# ARDF Pareto Frontier + Price/Performance Cheatsheet (v7.5.0)','',f"Generated {TODAY}. Canonical source: `data/unified-model-evidence.csv`. Generated by `calibrate.py`; edit policy in `project-config.json`, not these tables by hand.",'','## Read this first','',
    '- **Strict Pareto frontier** and **price/performance ranking are different calculations.** A Pareto point is simply not dominated by a configuration that is both cheaper and at least as capable. Pareto does not assign a single best model or sort by a capability/price ratio.',
    '- **This ledger frontier is paid-only.** It requires a task price above $0, so a $0 price (verified or not) never enters it. The AA-only frontier, which admits a $0 only when a free route with the same name is listed in a pinned catalog, and the paid-only AA frontier are in `docs/full-frontier.md`; the two ledgers can differ because this one blends sources through calibration.',
    '- **Calibrated capability** is the multi-source AA v4.2-equivalent Y coordinate used by the main graph. It is not literal human IQ.',
    '- **Task price** is the dashboard X coordinate using the best-available cost hierarchy (`best_evidence_then_weighted_geometric_mean`).',
    '- **Literal price/performance** is `task_price / calibrated_capability`; **lower is better**. Its inverse, capability points per dollar, is also shown.',
    f"- **Executor eligibility:** {executor_eligibility}",
    '- **AA $/point** is a secondary same-source diagnostic where exact AA Intelligence Index exists. It never replaces the multi-source primary ranking.',
    '- Muse Spark 1.2 (historical August v4.0 reference) used Contributor/data-sharing pricing ($0.02123) as its primary economic coordinate; in the November 2026 v4.2 suite, Meta is represented on the active frontier by **Muse Ember (Xhigh)** ($0.1162, cap 34.11) and **Muse Ember (Max)** ($0.1359, cap 36.02).','','## Strict current Pareto frontier (21 points)','', '| Tier | Model/configuration | Provider | Effort | Capability | Task price | $/capability point | $/M in/out | Released | Context | Weights | Sources |','|---|---|---|---|---:|---:|---:|---:|---|---:|---|---:|']
    for m in d['frontier']:
        ratio=m['cost']/m['capability'] if m['capability'] and m['cost'] else None
        lines.append(f"| {m['tier']['id']} | {m['display_name']} | {m['provider']} | {m['effort']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {ana_money(ratio)} | {ana_money(m['input_price_per_m'])} / {ana_money(m['output_price_per_m'])} | {m['release_date'] or '-'} | {int(m['context_tokens']) if m['context_tokens'] else '-'} | {'open' if str(m['models_dev_open_weights'])=='1' else 'closed/API'} | {m['source_count']} |")
    lines += ['','## Muse economics and lineage notes','','In the August 2026 v4.0 baseline, **Muse Spark 1.2** used the **Contributor/data-sharing** Meta SKU ($0.10 input / $0.20 output per M, $0.02123 repriced task cost) vs Standard ($1.25 / $4.25 per M, $0.40 direct AA cost). In the November 2026 v4.2 evaluation suite, **Muse Ember (Xhigh)** ($0.1162 task cost, capability 34.11) and **Muse Ember (Max)** ($0.1359 task cost, capability 36.02) sit directly on the strict 21-point Pareto frontier, while **Muse Wonder (Max)** reaches capability 43.57 ($6.95 task cost) and **Muse Wonder Full (Max)** reaches capability 50.08 (unpriced on direct task cost).','','## Major models that miss the frontier','', '| Model/configuration | Tier | Capability | Task price | Dominated by | Capability gap | Price premium | Verdict |','|---|---|---:|---:|---|---:|---:|---|']
    for m in d['major_near_frontier']:
        lines.append(f"| {m['display_name']} | {m['tier']['id']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {m['dominated_by'] or '-'} | {m['capability_gap']:.2f} | {m['cost_premium_pct']:.1f}% | {m['near_status']} |")
    lines += ['','## Closest near-frontier misses (all families)','', 'This table is algorithmic rather than hand-picked: the first 20 current non-frontier configurations with the smallest configured dominance regret are shown. It catches alternatives that a strict frontier necessarily excludes.','', '| Model/configuration | Tier | Capability | Task price | Dominated by | Capability gap | Price premium | Verdict |','|---|---|---:|---:|---|---:|---:|---|']
    for m in d['near_frontier'][:20]:
        lines.append(f"| {m['display_name']} | {m['tier']['id']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {m['dominated_by']} | {m['capability_gap']:.2f} | {m['cost_premium_pct']:.1f}% | {m['near_status']} |")
    lines += ['','## Capability-tier interpretation','','Tier thresholds classify calibrated **capability only**. They do not overwrite Pareto status or price/performance rank.','']
    for t in d['policy']['capability_tiers']:
        lines.append(f"- **{t['id']}**: >= {t['min']:.0f} ({t['label']})")
    lines += ['','## Global raw price/performance leaders (unrestricted)','', 'This table has **no executor capability floor**. It makes the denominator policy visible: ultra-cheap utility models outrank frontier-class models on raw `$ / capability` alone.','', '| Rank | Model/configuration | Tier | Capability | Task price | $/capability | Capability/$ | Pareto? |','|---:|---|---|---:|---:|---:|---:|---|']
    for i,m in enumerate(d['global_value_top20'][:10],1):
        lines.append(f"| {i} | {m['display_name']} | {m['tier']['id']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {ana_money(m['cost_per_capability'])} | {m['capability_per_dollar']:.1f} | {'YES' if m['frontier'] else 'no'} |")
    lines += ['','## Top five unrestricted price/performance families (collapsed by family)','', f"Eligibility: current, positively priced, positive calibrated capability. {executor_eligibility} Ranked strictly by `task_price / calibrated_capability`, ascending, keeping the best effort configuration per model family.",'', '| Rank | Model/configuration | Provider | Multi-source capability | AA reference | Task price | $/capability | Capability/$ | $/AA point | Pareto? | Cost vs #1 |','|---:|---|---|---:|---:|---:|---:|---:|---:|---|---:|']
    mc=min((x['cost'] for x in d['executor_top5']),default=1.0)
    for i,m in enumerate(d['executor_top5'],1):
        aa_ratio=ana_money(m.get('cost_per_aa_point')) if m.get('cost_per_aa_point') is not None else '-'
        lines.append(f"| {i} | {m['display_name']} | {m['provider']} | {ana_f2(m['capability'])} | {ana_f2(m['executor_reference_capability'])} | {ana_money(m['cost'])} | {ana_money(m['cost_per_capability'])} | {m['capability_per_dollar']:.1f} | {aa_ratio} | {'YES' if m['frontier'] else 'no'} | {m['cost']/mc:.2f}x |")
    lines += ['','## Role-gated T3+ executor price/performance shortlist (capability >= 47)','', 'When routing autonomous coding or tool-calling subagents that require at least **T3 Workhorse capability (>= 47.0 on the v4.2 scale)**, applying a visible role-specific gate yields the top five high-capability executor families by literal `task_price / calibrated_capability`:','', '| Rank | Model/configuration | Provider | Multi-source capability | AA reference | Task price | $/capability | Capability/$ | Pareto? | Cost vs T3 #1 |','|---:|---|---|---:|---:|---:|---:|---:|---|---:|']
    t3_mc=min((x['cost'] for x in d.get('executor_t3_top5',[])),default=1.0)
    for i,m in enumerate(d.get('executor_t3_top5',[]),1):
        lines.append(f"| {i} | {m['display_name']} | {m['provider']} | {ana_f2(m['capability'])} | {ana_f2(m['executor_reference_capability'])} | {ana_money(m['cost'])} | {ana_money(m['cost_per_capability'])} | {m['capability_per_dollar']:.1f} | {'YES' if m['frontier'] else 'no'} | {m['cost']/t3_mc:.2f}x |")
    lines += ['','### GPT-6 Luna price/performance by effort','', '| Effort | Multi-source capability | AA reference | Task price | $/capability | $/AA point | Gain vs prior effort | Cost increase |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in d['luna_effort_curve']:
        cost_inc='-' if m.get('cost_increase_vs_previous_pct') is None else f"{m['cost_increase_vs_previous_pct']:.1f}%"
        aa_ratio=ana_money(m.get('cost_per_aa_point')) if m.get('cost_per_aa_point') is not None else '-'
        lines.append(f"| {m['effort']} | {ana_f2(m['capability'])} | {ana_f2(m['aa_reference'])} | {ana_money(m['cost'])} | {ana_money(m['cost_per_capability'])} | {aa_ratio} | {ana_f2(m.get('aa_gain_vs_previous'))} | {cost_inc} |")
    best_luna=min(d['luna_effort_curve'], key=lambda x:x['cost_per_capability']) if d['luna_effort_curve'] else None
    if best_luna:
        lines += ['',f"**Literal price/performance winner for GPT-6 Luna: `{best_luna['effort']}`.** Its `$ / calibrated-capability` ratio is {ana_money(best_luna['cost_per_capability'])}. Both `low` ($0.00512, cap 9.67) and `medium` ($0.04220, cap 18.43) sit on the strict 21-point Pareto frontier, while `non-reasoning` ($0.07142, cap 9.44) is strictly dominated within its own family by `low` and `medium`."]
    lines += ['','## Top-end configuration audit','', 'This is the high-cost/high-capability zone the project is meant to prune aggressively. The **operational** columns use the multi-source ARDF task-cost plane. The **AA same-source** columns use current Artificial Analysis v4.2 Intelligence Index and direct Cost per Intelligence Index Task wherever AA exposes it.','','| Model/configuration | Effort | ARDF cap | ARDF task cost | $/cap | AA score | AA task cost | AA full-eval cost | AA $/score | AA cost basis | Op. frontier? | AA top-end frontier? | Within-family AA optimal? |','|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|']
    for m in d['top_end']['configurations']:
        lines.append(f"| {m['display_name']} | {m['effort']} | {ana_f2(m['capability'])} | {ana_money(m['cost'])} | {ana_money(m['operational_cost_per_capability'])} | {ana_f2(m['aa_score_exact'])} | {ana_money(m['aa_task_cost_exact'])} | {ana_money(m['aa_full_eval_cost'])} | {ana_money(m['aa_cost_per_point'])} | {m['aa_economic_cost_basis'] or '-'} | {'YES' if m['top_end_operational_frontier'] else 'no'} | {'YES' if m['top_end_aa_frontier'] else 'no'} | {'YES' if m.get('within_family_aa_frontier') else ('dominated by '+m.get('within_family_dominated_by','') if m.get('within_family_dominated_by') else 'unscored')} |")
    lines += ['','**Key pruning rule:** an effort configuration that is dominated within its own family on exact AA score/cost or cross-family dominated at a tiny capability margin should be pruned from default routing unless a specialized benchmark justifies it.','','### Current November 2026 top-end routing cuts','','- **Claude Fable 5.2 (Max / Xhigh / High / Medium):** Dominates the upper capability frontier from 56.37 (`medium`, $3.80) through 61.82 (`high`, $9.08) and 62.22 (`xhigh`, $14.83) to the absolute ceiling at 64.56 (`max`, $26.54). Note that `Claude Fable 5.2 (Low)` (53.89, $3.10) is dominated by `GPT-6.1 Sol (Max)` (54.54, $1.27).','- **Gemini 4 Carbon (High / Medium):** Holds the T1/T2 transition knee of the Pareto frontier at 58.28 (`medium`, $6.59) and 60.02 (`high`, $7.76), while `Gemini 4 Carbon (Low)` (54.22, $7.19) is dominated within its own family by `Gemini 4 Carbon (Medium)`.','- **Claude Opus 5.5 & GPT-6 Astra:** `Claude Opus 5.5 (Xhigh)` (57.29, $6.05) and `GPT-6 Astra (Xhigh)` (55.30, $3.66) / `GPT-6 Astra (High)` (54.83, $3.24) sit on the strict Pareto frontier, while `GPT-6 Astra (Max)` (56.85, $6.24, razor-edge miss) and `Claude Opus 5.5 (Max)` (58.95, $10.04, near-frontier) sit just inside the frontier. Route to Max when subscription quota (Claude Max / ChatGPT Pro) makes marginal API cost zero.','- **GPT-6.1 Sol vs GPT-6.1 Terra:** `GPT-6.1 Sol` sweeps the T3 workhorse Pareto frontier from `medium` (46.31, $0.359) through `high` (50.31, $0.591) and `xhigh` (52.43, $0.764) to `max` (54.54, $1.272), while `GPT-6.1 Terra` sweeps the lower T4 frontier at `low` (29.42, $0.071), `medium` (38.15, $0.169), and `high` (42.43, $0.259), with `GPT-6.1 Terra (Max)` (51.32, $0.961) as the #2 T3+ executor contender.','- **Claude Fable 5.1 (Max):** Dominated within its own family by `Claude Fable 5.1 (Xhigh)` (49.87 at $10.85 vs 49.09 at $12.99); hard-prune from default routing.','','## External Pareto cross-checks','', 'These are diagnostic planes, not extra votes in the calibrated aggregate. Agreement increases confidence; disagreement tells us where benchmark/harness semantics matter.','','### Artificial Analysis direct task-cost subset','', '| Model | AA capability | AA cost/task | AA Pareto within extracted subset? |','|---|---:|---:|---|']
    for x in d['external_frontier_comparisons']['artificial_analysis']['points']:
        lines.append(f"| {x['display_name']} | {ana_f2(x['capability'])} | {ana_money(x['cost'])} | {'YES' if x['frontier'] else 'no'} |")
    lines += ['','### Kilo coding-agent frontier','', '| Model | Completion | Cost/attempt | Kilo Pareto? |','|---|---:|---:|---|']
    for x in d['external_frontier_comparisons']['kilo']['points']:
        lines.append(f"| {x['display_name']} | {x['completion']:.1f}% | {ana_money(x['cost'])} | {'YES' if x['frontier'] else 'no'} |")
    lines += ['','Kilo retains Grok 4.5 -> Kimi K3 -> GPT-5.5 -> GPT-5.6 Sol as the observed completion/cost frontier among its public top-10 table.','','### Vals Index cost/test frontier','', '| Model | Vals Index | Cost/Test | Vals Pareto? |','|---|---:|---:|---|']
    for x in d['external_frontier_comparisons']['vals']['points']:
        if x.get('cost') is not None:
            lines.append(f"| {x['display_name']} | {x['accuracy']:.2f}% | {ana_money(x['cost'])} | {'YES' if x['frontier'] else 'no'} |")
    lines += ['','Vals is a second independent cost/performance plane. Its Cost/Test is benchmark-specific; it is calibrated through overlaps when used in ARDF, but the raw Vals frontier is preserved here for comparison.']
    lines += ['','## Near-frontier interpretation','', '- **razor-edge miss:** <= 0.75 capability points behind and <= 25% more expensive than its closest dominating frontier point.', '- **near-frontier:** <= 2 capability points behind and <= 50% more expensive.', '- **capability-close / price-heavy:** capability is close but the price penalty is substantial.', '- **price-close / capability-behind:** price is close, but capability gives up more than the near band.', '- **economically dominated:** neither condition is close.','']
    return '\n'.join(lines)




def render_tiers_document(data: dict[str,Any], calibrated_payload: dict[str,Any]) -> str:
    """Render capability tiers separately from the economic Pareto cheatsheet."""
    policy=data['policy']
    active=calibrated_payload['config']['active_algorithm_by_axis']['capability']
    models=[dict(m) for m in calibrated_payload['aggregate_sets'][active]]
    near={m['model_key']:m for m in data.get('near_frontier',[])}
    frontier={m['model_key'] for m in data.get('frontier',[])}
    def tf(v): return ana_tier_for(v,policy)
    def money(v): return '-' if v is None else f'${v:.5g}'
    def f2(v): return '-' if v is None else f'{v:.2f}'
    for m in models:
        m['tier']=tf(m.get('capability')); m['frontier']=m['model_key'] in frontier
    current=[m for m in models if m.get('capability') is not None and (m.get('models_dev_status') or '').lower()!='deprecated']
    lines=['# ARDF Model Tiers + Contested Regions (v7.5.0)','',
           'This document answers a different question from the Pareto cheatsheet: **tiers classify calibrated capability**, while Pareto membership classifies economic non-dominance.','',
           'Canonical data: `data/unified-model-evidence.csv`. Policy: `project-config.json`. Regenerate with `python calibrate.py`.','',
           '## Fine-grained capability tier policy (S+ through D)','', '| Tier | Minimum calibrated capability | Interpretation |','|---|---:|---|']
    for t in policy['capability_tiers']:
        lines.append(f"| {t['id']} | {t['min']:.0f} | {t['label']} |")
    lines += ['',
              '## Operational 4-tier routing policy (T1 to T4)','',
              'For day-to-day multi-agent orchestration, the capability space is partitioned into four operational routing tiers:','',
              '| Operational Tier | Capability Band (v4.2) | Primary Routing Role | Canonical Frontier & Near-Frontier Representatives |',
              '|---|---|---|---|',
              '| **T1 · Frontier Ceiling** | **>= 60.0** | Deep architectural judgment, hard verification, adversarial audits, final arbitration | `Claude Fable 5.2 (Max)` (64.56, $26.54), `Claude Fable 5.2 (Xhigh)` (62.22, $14.83), `Claude Fable 5.2 (High)` (61.82, $9.08), `Gemini 4 Carbon (High)` (60.02, $7.76) |',
              '| **T2 · Frontier** | **56.0 to 59.9** | Complex multi-file synthesis, refactoring, spec-to-code implementation | `Claude Opus 5.5 (Max)` (58.95, $10.04, near-frontier), `Gemini 4 Carbon (Medium)` (58.28, $6.59), `Claude Opus 5.5 (Xhigh)` (57.29, $6.05), `GPT-6 Astra (Max)` (56.85, $6.24, razor-edge miss), `Claude Fable 5.2 (Medium)` (56.37, $3.80) |',
              '| **T3 · Executor** | **47.0 to 55.9** | High-throughput subagent fan-outs, test generation, doc synthesis, autonomous coding | `GPT-6 Astra (Xhigh)` (55.30, $3.66), `GPT-6 Astra (High)` (54.83, $3.24), `GPT-6.1 Sol (Max)` (54.54, $1.27), `GPT-6.1 Sol (Xhigh)` (52.43, $0.76), `GPT-6.1 Terra (Max)` (51.32, $0.96, near-frontier), `GPT-6.1 Sol (High)` (50.31, $0.59) |',
              '| **T4 · Utility (Bottom-4 Interchangeable)** | **< 47.0** | Classification, extraction, routing probes, high-volume batch filtering | `GPT-6.1 Sol (Medium)` (46.31, $0.36), `GPT-6.1 Terra (High)` (42.43, $0.26), `GPT-6.1 Terra (Medium)` (38.15, $0.17), `Muse Ember (Max)` (36.02, $0.14), `Muse Ember (Xhigh)` (34.11, $0.12), `GPT-6.1 Terra (Low)` (29.42, $0.071), `Claude Haiku 5.5 (Low)` (18.64, $0.044), `GPT-6 Luna (Low)` (9.67, $0.005) |',
              '','## Current scored configurations by tier','']
    for t in policy['capability_tiers']:
        members=sorted((m for m in current if m['tier']['id']==t['id']),key=lambda x:(-(x.get('capability') or -1),x.get('display_name','')))
        lines += [f"### {t['id']} · {t['label']} ({len(members)})",'', '| Model/configuration | Capability | Calibrated aggregate cost | Pareto | Near-frontier status |','|---|---:|---:|---|---|']
        for m in members:
            n=near.get(m['model_key'],{})
            lines.append(f"| {m.get('display_name') or m['model_key']} | {f2(m.get('capability'))} | {money(m.get('cost'))} | {'YES' if m['frontier'] else 'no'} | {n.get('near_status','-')} |")
        lines.append('')
    lines += ['## Top contested region','',
              'The upper contest zone includes configurations at capability >= 50, spanning the A+/S/S+ boundary neighborhood where small capability differences can carry large cost penalties.','',
              '| Model/configuration | Tier | Capability | Cost | Pareto | Closest economic verdict |','|---|---|---:|---:|---|---|']
    for m in sorted((m for m in current if (m.get('capability') or -1)>=50),key=lambda x:(-(x.get('capability') or -1),x.get('cost') if x.get('cost') is not None else math.inf)):
        n=near.get(m['model_key'],{}); verdict='STRICT FRONTIER' if m['frontier'] else n.get('near_status','dominated / outside near band')
        lines.append(f"| {m.get('display_name') or m['model_key']} | {m['tier']['id']} | {f2(m.get('capability'))} | {money(m.get('cost'))} | {'YES' if m['frontier'] else 'no'} | {verdict} |")
    lines += ['','## Pinch-point contested pairs (delta capability <= 2.0, delta cost <= 25%)','',
              'Pinch points identify cross-family pairs that sit within 2.0 capability points and 25% task cost of one another. Within a pinch point, benchmark noise exceeds the capability gap, so harness fit, latency, context window, and subscription quota should decide routing.','',
              '| Model A | Tier A | Cap A | Cost A | Model B | Tier B | Cap B | Cost B | Cap Delta | Cost Delta |','|---|---|---:|---:|---|---|---:|---:|---:|---:|']
    for p in data.get('pinch_points',[]):
        lines.append(f"| {p['model_a']} | {p['tier_a']} | {f2(p['cap_a'])} | {money(p['cost_a'])} | {p['model_b']} | {p['tier_b']} | {f2(p['cap_b'])} | {money(p['cost_b'])} | {f2(p['cap_delta'])} | {p['cost_delta_pct']:.1f}% |")
    lines += ['','## Bottom contested region','',
              'The lower end is contested by cost compression rather than flagship quality. This section combines the cheapest eight Pareto configurations with models within +/- 2 capability points of the D/C (30) and C/B (40) boundaries.','',
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
    lines += ['',
              '## Bottom-4 (T4 Utility) interchangeability matrix by use case','',
              'Below capability 47 (T4), specialized operational traits (latency, open-weights self-hosting, structured output reliability, and context window) dominate selection across interchangeable Pareto and near-frontier peers:','',
              '| Workload / Use Case | Primary T4 Pick | Drop-in Interchangeable Peers | Selection Rationale |',
              '|---|---|---|---|',
              '| **Upper-T4 code & CLI worker (42 to 46 cap)** | `GPT-6.1 Sol (Medium)` (46.31, $0.359) | `GPT-6.1 Terra (Xhigh)` (45.28, $0.401), `GPT-6.1 Terra (High)` (42.43, $0.259), `Kimi K3.1 Pro` (46.43, $3.681, open-weights) | Sol Medium and Terra High sit on the strict Pareto frontier under $0.36/task; Kimi K3.1 Pro provides the highest open-weights capability in this band. |',
              '| **Low-cost synthesis & reasoning (34 to 38 cap)** | `GPT-6.1 Terra (Medium)` (38.15, $0.169) | `Muse Ember (Max)` (36.02, $0.136), `GPT-6.1 Sol (Low)` (34.77, $0.161), `Muse Ember (Xhigh)` (34.11, $0.116), `Claude Haiku 5.5 (Max)` (36.44, $0.411) | Three strict Pareto points (`Muse Ember Xhigh`, `Muse Ember Max`, `GPT-6.1 Terra Medium`) cluster tightly between $0.116 and $0.169/task. |',
              '| **Sub-$0.10 batch extraction & classification (18 to 30 cap)** | `GPT-6.1 Terra (Low)` (29.42, $0.071) | `Claude Haiku 5.5 (Medium)` (24.58, $0.092), `Claude Haiku 5.5 (Low)` (18.64, $0.044), `GPT-6 Luna (Medium)` (18.43, $0.042) | Strict Pareto rungs for high-volume JSON/schema extraction where T3 reasoning is unnecessary overhead. |',
              '| **Ultra-floor micro-triage (< $0.045/task)** | `GPT-6 Luna (Low)` (9.67, $0.0051) | `Mistral Small 4 (Reasoning)` (4.30, $0.040), `Granite 4.2 8B` (5.10, $0.040), `GPT-6 Luna (Medium)` (18.43, $0.042) | `GPT-6 Luna (Low)` achieves the lowest literal $/capability ($0.000529/pt) in the entire current dataset. |',
              '','## Closest competitors to the strict Pareto frontier','',
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
    # The rendered dashboard is gitignored and is never a build input: the
    # tracked template is the single presentation source, so template edits
    # always reach the rebuilt dashboard.
    template = ROOT / 'dashboard-template.html'
    if not template.exists():
        raise RuntimeError('dashboard-template.html is missing; it is the presentation source for dashboard.html')
    text=template.read_text(encoding='utf-8')
    begin='<!-- ARDF_DATA_BEGIN -->'; end='<!-- ARDF_DATA_END -->'
    if begin not in text or end not in text:
        raise RuntimeError('dashboard-template.html is missing ARDF_DATA_BEGIN/END markers')
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
    # Primary current block: every primary-catalog configuration is preserved, missing stays missing, zero stays a price.
    cp=analysis.get('current_primary') or {}
    prim=cp.get('rows') or []
    if len(prim)<725: raise RuntimeError(f'Primary AA catalog collapsed: {len(prim)} configurations (expected at least 725)')
    if len({r['id'] for r in prim})!=len(prim): raise RuntimeError('Duplicate primary configuration ids')
    if sum(1 for r in prim if r['score'] is not None)<100: raise RuntimeError('Primary scored count collapsed')
    for r in prim:
        if r['cost'] is not None and not (r['cost']>=0): raise RuntimeError('Invalid primary cost for '+r['id'])
        if r['score'] is not None and any(v is None for v in r['components'].values()): raise RuntimeError('Scored row missing a component: '+r['id'])
    # Routing deliverables: short rules, each citing data; the full frontier must equal an independent recomputation.
    routing=analysis.get('routing') or {}
    rl=routing.get('rules') or []
    if not (1<=len(rl)<=MAX_RULES): raise RuntimeError(f'Routing rules must number 1 to {MAX_RULES}, found {len(rl)}')
    if any(not r.get('data') for r in rl): raise RuntimeError('Every routing rule must cite data')
    sys_path_added=False
    import sys
    if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT)); sys_path_added=True
    try: import current_frontier as _cf
    finally:
        if sys_path_added: sys.path.remove(str(ROOT))
    expected={r['id'] for r in _cf.frontier(prim)}
    got={r['id'] for r in routing.get('full_frontier',{}).get('frontier',[])}
    if expected!=got: raise RuntimeError('Full frontier differs from current_frontier.frontier(): '+str(sorted(expected^got))[:200])
    # Unverified $0 prices must never silently dominate: held out of every frontier, listed in their own band.
    ff=routing['full_frontier']
    if any(r.get('cost_state') not in ('priced','unknown','zero-verified','zero-unverified') for r in prim): raise RuntimeError('Primary row without a valid cost_state')
    held={r['id'] for r in prim if r['cost_state']=='zero-unverified' and r['score'] is not None}
    in_frontiers={r['id'] for r in ff['frontier']}|{r['id'] for r in ff['paid_frontier']}|{r['id'] for p in ff['by_provider'] for r in p['frontier']}
    if held&in_frontiers: raise RuntimeError('Unverified $0 configuration entered a frontier: '+str(sorted(held&in_frontiers))[:200])
    if {r['id'] for r in ff['unverified_free']}!=held: raise RuntimeError('Unverified-free band differs from the unverified $0 rows')
    paid_expected={r['id'] for r in _cf.frontier([r for r in prim if r['cost'] is not None and r['cost']>0])}
    if paid_expected!={r['id'] for r in ff['paid_frontier']}: raise RuntimeError('Paid-only frontier differs from current_frontier.frontier() over prices above $0')
    if _cf.frontier([r for r in prim if r['cost_state']=='zero-unverified']): raise RuntimeError('Unverified $0 rows formed a frontier on their own')
    for doc in ('routing-rules.md','full-frontier.md','free-routes.md','priors-deltas.md'):
        if not (ROOT/'docs'/doc).exists(): raise RuntimeError('Missing generated document docs/'+doc)
    if not routing.get('free',{}).get('models'): raise RuntimeError('Free-route evaluation matched no scored model')
    for e in routing['free']['models']:
        if e['effort_basis'] not in ('catalog-listed','assumed') or not (e['score_low']-1e-12<=e['score']<=e['score_high']+1e-12) or not e.get('effort_note'):
            raise RuntimeError('Free-route entry without an explicit effort basis: '+e['model'])
        used=[v for v in e['variants'] if v['support']==('listed' if e['effort_basis']=='catalog-listed' else 'assumed')]
        if not used or any(v['score']<e['score_low']-1e-12 or v['score']>e['score_high']+1e-12 for v in used): raise RuntimeError('Free-route score range includes a variant the catalog does not support: '+e['model'])
    if routing.get('priors_deltas',{}).get('max_abs_score_delta',1)>0.0051:
        import sys as _s; print('WARNING: ARDF recomputation differs from the pinned Priors snapshot by more than its two-decimal rounding; see docs/priors-deltas.md',file=_s.stderr)
    csv_primary=sum(1 for r in csv.DictReader(CSV_PATH.open(newline='',encoding='utf-8-sig')) if r.get('source_id')==PRIMARY_SOURCE_ID and r.get('record_type')=='catalog')
    if csv_primary!=len(prim): raise RuntimeError(f'Primary catalog rows in CSV ({csv_primary}) differ from the embedded payload ({len(prim)})')
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
