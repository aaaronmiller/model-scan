# ---
# title: ARDF Multipoint Calibration and Display-Data Engine
# version: 6.0.0
# created: 2026-07-28
# model: GPT-5.6 Thinking
# reasoning_level: high
# purpose: Add configurable calibration columns to the single evidence CSV and generate display-ready data.
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
3.11+ is available. It writes atomically and can safely target the input path.
"""
from __future__ import annotations

import argparse
import csv
import json
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


def calibrate(input_path: Path, output_path: Path, config_path: Path, generated_dir: Path) -> dict[str,Any]:
    rows,fields=read_rows(input_path)
    config=json.loads(config_path.read_text(encoding='utf-8'))
    refs={axis:reference_values(rows,axis,spec['metric_name']) for axis,spec in config['reference_scales'].items()}
    algorithms=[a for a in config['algorithms'] if a.get('enabled',True)]
    for algorithm in algorithms:
        base=algorithm['output_column']
        for suffix in ['', '_status','_anchor_count','_rmse','_group_key']:
            name=base+suffix
            if name not in fields: fields.append(name)
    for name in ['calibrated_score','calibrated_score_unit','calibrated_score_algorithm']:
        if name not in fields: fields.append(name)

    groups: dict[tuple[str,str,str],list[int]] = defaultdict(list)
    for index,row in enumerate(rows):
        if row.get('record_type')=='observation' and row.get('metric_axis') in refs:
            groups[(row['metric_axis'],row['source_id'],row['metric_name'])].append(index)

    reports=[]
    for (axis,source_id,metric_name),indices in sorted(groups.items()):
        group_key=f'{axis}|{source_id}|{metric_name}'
        ref_metric=config['reference_scales'][axis]['metric_name']
        is_identity=metric_name==ref_metric
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

        for algorithm in algorithms:
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
            reports.append({'group_key':group_key,'axis':axis,'source_id':source_id,'metric_name':metric_name,'algorithm_id':algorithm['id'],
                            'output_column':base,'status':status,'anchor_count':len(transformed),'automatic_anchor_count':len(auto),
                            'manual_anchor_count':len(anchors)-len(auto),'rmse_transformed':None if not math.isfinite(error) else error,
                            'diagnostics':diagnostics,'anchors':[{'source_value':x,'reference_value':y,'weight':w,'label':label} for x,y,w,label in anchors]})

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
        item={k:meta.get(k,'') for k in ['model_key','display_name','provider','family','effort','harness','release_date','availability','is_open_weights','context_window_tokens','input_price_per_m','output_price_per_m','official_model_id','quality','confidence']}
        item['model_key']=key
        if not item.get('display_name'):
            first=next(r for r in observation_rows if r['model_key']==key)
            for k in ['display_name','provider','family','effort','harness']: item[k]=first.get(k,'')
        models.append(item)

    compact_obs=[]
    dynamic_columns=[a['output_column'] for a in algorithms]
    for r in observation_rows:
        compact={k:r.get(k,'') for k in ['observation_id','model_key','display_name','provider','family','effort','harness','release_date','availability','is_open_weights','context_window_tokens','input_price_per_m','output_price_per_m','official_model_id','source_id','source_label','source_publisher','source_version','source_date','source_url','source_mirror_url','retrieved_at','metric_axis','metric_name','raw_value','raw_unit','raw_direction','quality','confidence','base_weight','use_in_aggregate','is_historical','identity_mapping','notes']+dynamic_columns+[name for name in fields if name.startswith(tuple(a['output_column'] for a in algorithms)) and name not in dynamic_columns]}
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
        d=by_source[r['source_id']]; d['rows']+=1; d[r['metric_axis']]+=1; d['label']=r['source_label']; d['url']=r['source_url']; d['date']=r.get('source_date','')
    for source_id,d in sorted(by_source.items()): sources.append({'source_id':source_id,**d})

    generated_dir.mkdir(parents=True,exist_ok=True)
    payload={'generated_at':'2026-07-28T21:30:00-07:00','config':config,'algorithms':algorithms,'sources':sources,'models':models,'observations':compact_obs,'aggregate_sets':aggregate_sets,'calibration_reports':reports}
    (generated_dir/'dashboard-data.js').write_text('/* ---\n title: Generated ARDF Dashboard Data\n version: 6.0.0\n generated_by: scripts/calibrate.py\n --- */\nwindow.ARDF_DATA='+json.dumps(payload,separators=(',',':'))+';\n',encoding='utf-8')
    (generated_dir/'calibration-report.json').write_text(json.dumps({'generated_at':payload['generated_at'],'reports':reports},indent=2),encoding='utf-8')
    # Embed an exact copy of the canonical CSV for file:// Calibration Studio use.
    # Browsers often block fetch() across local files, but loading a sibling script is reliable.
    csv_text=output_path.read_text(encoding='utf-8')
    (generated_dir/'unified-evidence-csv.js').write_text('/* ---\n title: Embedded Canonical CSV\n version: 6.0.0\n generated_by: scripts/calibrate.py\n --- */\nwindow.ARDF_UNIFIED_CSV='+json.dumps(csv_text)+';\n',encoding='utf-8')
    return {'row_count':len(rows),'observation_count':len(observation_rows),'model_count':len(models),'algorithm_count':len(algorithms),'calibration_group_count':len(groups),'reports':reports,'models':models,'aggregate_sets':aggregate_sets}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    root=Path(__file__).resolve().parent.parent
    parser.add_argument('--input',type=Path,default=root/'data/unified-model-evidence.csv')
    parser.add_argument('--output',type=Path,default=root/'data/unified-model-evidence.csv')
    parser.add_argument('--config',type=Path,default=root/'config/calibration-algorithms.json')
    parser.add_argument('--generated-dir',type=Path,default=root/'generated')
    args=parser.parse_args()
    result=calibrate(args.input,args.output,args.config,args.generated_dir)
    summary={k:v for k,v in result.items() if k not in {'reports','models','aggregate_sets'}}
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
