"""Independent current ARDF calculation. Offline build uses pinned primary snapshots.

The comparison provider never supplies ARDF scores or API costs. Effort and
fallback tracks remain distinct. Missing data stays missing; zero is a price.
"""
from __future__ import annotations
import csv
import functools
import gzip
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'sources/current'
# id: (primary field/evaluation, weight, subjective image tier)
BENCHMARKS = {
    'briefcase': ('aa-briefcase', 15, 'Unrated'),
    'automation': ('automationbench-aa', 5, 'Unrated'),
    'terminal': ('terminalbench-4-0', 10, 'A'),
    'coding': ('frontiercode-2-0', 15, 'C'),
    'accuracy': ('omniscienceAccuracy', 10, 'B'),
    'nonhallucination': ('omniscienceHallucinationRate', 5, 'B'),
    'pdf': ('gdp-pdf', 5, 'C'),
    'hle': ('hle-diamond', 10, 'C'),
    'physics': ('critpt-v2-hard', 10, 'C'),
    'science': ('terminal-bench-science', 15, 'S'),
}

def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

def identity(name, effort):
    # Explicit brand-only aliases. Do not strip version, dates, or effort.
    name = re.sub(r'^(Claude |NVIDIA: |NVIDIA )', '', name, flags=re.I)
    name = name.replace('Qwen3.', 'Qwen 3.')
    name = re.sub(r'\s*\((?:High|Max)\)$', '', name, flags=re.I)
    return re.sub(r'[^a-z0-9]', '', name.lower()) + '@' + ('none' if effort in (None, 'default') else effort).lower()

def comparable(r, score='score', cost='cost'):
    """Eligible for dominance: a score, a known cost (zero is a price) and not an unverified $0.

    An AA price of exactly $0 is only trusted as a price when a free route with the same name exists in a
    pinned catalog (cost_state 'zero-verified'). Otherwise it is held out as 'zero-unverified': it can neither
    dominate nor be dominated, and is reported in its own band. Priors rows carry no cost_state and are unaffected.
    """
    return finite(r.get(score)) and finite(r.get(cost)) and r[cost] >= 0 and r.get('cost_state') != 'zero-unverified'

def dominates(a, b, score='score', cost='cost'):
    return (comparable(a, score, cost) and comparable(b, score, cost)
            and a[cost] <= b[cost] and a[score] >= b[score]
            and (a[cost] < b[cost] or a[score] > b[score]))

def frontier(rows, score='score', cost='cost'):
    eligible = [r for r in rows if comparable(r, score, cost)]
    return sorted([r for r in eligible if not any(dominates(o, r, score, cost) for o in eligible)],
                  key=lambda r: (r[cost], -r[score], r['id']))

def components(m):
    ev = {e['slug']: e for e in m.get('intelligenceIndexEvaluations') or []}
    result = {}
    for key, (field, _, _) in BENCHMARKS.items():
        value = m.get(field) if key in ('accuracy', 'nonhallucination') else ev.get(field, {}).get('score')
        if finite(value):
            if key == 'briefcase': value = min(1, max(0, (value - 500) / 2000))
            elif key == 'nonhallucination': value = 1 - value
            result[key] = value * 100
        else: result[key] = None
    return result

def score_components(comp, multipliers=None):
    multipliers = multipliers or {}
    weights = {k: w * multipliers.get(t, 1) for k, (_, w, t) in BENCHMARKS.items()}
    if any(not finite(w) or w < 0 for w in weights.values()):
        raise ValueError('Weights must be finite and nonnegative')
    total = sum(weights.values())
    if total <= 0: return None
    if any(not finite(comp.get(k)) for k, w in weights.items() if w > 0): return None
    return sum(comp[k] * w for k, w in weights.items() if w > 0) / total

def _norm_name(text):
    # '+' is part of a model name (Command A+ is not Command A); every other symbol is dropped.
    return re.sub(r'[^a-z0-9]', '', str(text).lower().replace('+', 'plus'))

def _route_key(name):
    name = re.sub(r'^[^:]*:\s*', '', name)
    return _norm_name(re.sub(r'\(free\)|\bfree\b', '', name, flags=re.I))

@functools.lru_cache(maxsize=None)
def catalog_routes():
    """Flat route records from the pinned OpenRouter, Kilo and OpenCode Zen catalogs (checksums verified).

    Each record: surface, route_id, name, input_per_m / output_per_m (USD per million tokens, None when absent),
    free (both listed prices are zero), may_train, modalities, and the effort the route itself lists:
    efforts (levels the catalog names, 'none' included when reasoning can be switched off), can_disable,
    default_effort (None unless the catalog states one).
    """
    manifest = read_snapshot('manifest.json')
    def load(name):
        raw = (SOURCES / name).read_bytes()
        expected = manifest.get('sha256', {}).get(name)
        if expected and hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Snapshot checksum mismatch: ' + name)
        return json.loads(gzip.decompress(raw))['data']
    def per_m(v):
        try: return round(float(v) * 1e6, 6)
        except (TypeError, ValueError): return None
    routes = []
    for m in load('openrouter-catalog.json.gz'):
        p = m.get('pricing') or {}; r = m.get('reasoning') or {}
        eff = [e for e in (r.get('supported_efforts') or [])]
        routes.append({'surface': 'OpenRouter', 'route_id': m['id'], 'name': m['name'],
            'input_per_m': per_m(p.get('prompt')), 'output_per_m': per_m(p.get('completion')), 'may_train': None,
            'modalities': (m.get('architecture') or {}).get('output_modalities', []),
            'efforts': sorted(set(eff)), 'can_disable': r.get('mandatory') is False or 'none' in eff, 'default_effort': r.get('default_effort')})
    for m in load('kilo-catalog.json.gz'):
        p = m.get('pricing') or {}; o = m.get('opencode') or {}
        variants = [(v.get('reasoning') or {}) for v in (o.get('variants') or {}).values()]
        eff = {v['effort'] for v in variants if v.get('effort')}
        for opt in o.get('reasoning_options') or []:
            if opt.get('type') == 'effort': eff |= set(opt.get('values') or [])
        off = any(v.get('enabled') is False for v in variants) or any(opt.get('type') == 'toggle' for opt in o.get('reasoning_options') or [])
        routes.append({'surface': 'Kilo', 'route_id': m['id'], 'name': m['name'],
            'input_per_m': per_m(p.get('prompt')), 'output_per_m': per_m(p.get('completion')), 'may_train': m.get('mayTrainOnYourPrompts'),
            'modalities': (m.get('architecture') or {}).get('output_modalities', []),
            'efforts': sorted(eff), 'can_disable': off or 'none' in eff, 'default_effort': None})
    for m in load('zen-catalog.json.gz'):
        try: c = m['cost']['text']; inp, out = c['input']['price'], c['output']['price']
        except (KeyError, TypeError): inp = out = None
        rs = (m.get('capabilities') or {}).get('reasoning') or {}
        eff = list(rs.get('effort') or [])
        routes.append({'surface': 'OpenCode Zen', 'route_id': 'opencode/' + m['id'], 'name': m['name'],
            'input_per_m': inp, 'output_per_m': out, 'may_train': None,
            'modalities': (m.get('modalities') or {}).get('output', []),
            'efforts': sorted(set(eff) | ({'none'} if rs.get('toggle') else set())), 'can_disable': bool(rs.get('toggle')) or 'none' in eff, 'default_effort': None})
    for r in routes:
        r['free'] = r['input_per_m'] == 0 and r['output_per_m'] == 0
        r['key'] = _route_key(r['name'])
    return routes

def _price_text(r):
    return f"${r['input_per_m']:.4g}/M in, ${r['output_per_m']:.4g}/M out"

def classify_cost_states(rows):
    """Set cost_state and cost_evidence on every row (dicts with 'name' and 'cost').

    priced: cost above 0.  unknown: no cost.  zero-verified: cost 0 and a free route with the same name is listed in a
    pinned catalog.  zero-unverified: cost 0 with no such route; the evidence says whether a catalog lists a paid route
    that contradicts AA's $0 or none at all.  Only exact names count (no suffix or alias matching).
    """
    routes = catalog_routes()
    for r in rows:
        c = r.get('cost')
        if not finite(c):
            r['cost_state'] = 'unknown'; r['cost_evidence'] = ''
        elif c > 0:
            r['cost_state'] = 'priced'; r['cost_evidence'] = ''
        else:
            key = _norm_name(re.sub(r'\s*\(.*\)$', '', r['name']))
            free = [x for x in routes if x['free'] and x['key'] == key]
            paid = [x for x in routes if not x['free'] and x['key'] == key and finite(x['input_per_m']) and finite(x['output_per_m'])]
            if free:
                r['cost_state'] = 'zero-verified'
                r['cost_evidence'] = 'free route listed: ' + '; '.join(f"{x['surface']} {x['route_id']}" for x in free)
            elif paid:
                r['cost_state'] = 'zero-unverified'
                r['cost_evidence'] = "AA lists $0 but the catalogs list a paid route: " + '; '.join(f"{x['surface']} {x['route_id']} {_price_text(x)}" for x in paid)
            else:
                r['cost_state'] = 'zero-unverified'
                r['cost_evidence'] = 'AA lists $0 and no route with this name exists in the pinned OpenRouter, Kilo or OpenCode Zen catalogs'
    return rows

def primary_rows(models):
    result = []
    for m in models:
        effort = (m.get('effort') or {}).get('slug') or 'none'
        name = (m.get('release') or {}).get('name') or m['name']
        comp = components(m)
        ev = {e['slug']: e for e in m.get('intelligenceIndexEvaluations') or []}
        cost_parts = {}
        for k, (field, w, _) in BENCHMARKS.items():
            v = ev.get('omniscience' if k in ('accuracy', 'nonhallucination') else field, {}).get('costPerTask')
            cost_parts[k] = v
        cost = (sum(cost_parts[k] * BENCHMARKS[k][1] for k in BENCHMARKS) / 100
                if all(finite(v) and v >= 0 for v in cost_parts.values()) else None)
        published_cost = ((m.get('intelligenceIndexCostPerTask') or {}).get('cost') or {}).get('total')
        result.append({
            'id': m['slug'], 'identity': identity(name, effort), 'model': name,
            'name': m['name'], 'lab': m['creator']['name'], 'effort': effort,
            'score': score_components(comp), 'published_score': m.get('intelligenceIndex'),
            'cost': cost, 'published_cost': published_cost, 'components': comp,
            'component_costs': cost_parts, 'coverage': sum(BENCHMARKS[k][1] for k,v in comp.items() if finite(v)),
            'input_price': m.get('price1mInputTokens'), 'output_price': m.get('price1mOutputTokens'),
            'cache_read': m.get('cacheHitPrice'), 'cache_write': m.get('cacheWritePrice'),
            'time': m.get('intelligenceIndexTimePerTask'),
            'tokens': (m.get('intelligenceIndexOutputTokensPerTask') or {}).get('output'),
            'latency': (m.get('headline') or {}).get('timeToFirstAnswerToken'),
            'context': m.get('contextWindowTokens'), 'release': m.get('releaseDate'),
            'deprecated': m.get('deprecated'),
            'fallback': 'fallback' in m['name'].lower(),
            'url': 'https://artificialanalysis.ai/models/' + m['slug'],
            'specialties': {k: m.get(k) for k in ['mlcrOverall','lcr','itBenchSre','frontierCode','gdpval','aa3dElo','code2videoElo','analystAgent','enterpriseOpsGym']},
        })
    return classify_cost_states(result)

def read_snapshot(name):
    p = SOURCES / name
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_text())

def priors_rows(basis):
    rows = read_snapshot('priors-' + basis + '.json')['response']['rows']
    return [{'id': identity(r['model'], r['effort']), 'identity': identity(r['model'],r['effort']),
             'model':r['model'], 'name':r['model']+' ('+r['effort']+')', 'effort':r['effort'], 'lab':r['lab'],
             'score':r.get('Index score'), 'cost':r.get('Cost per task'), 'time':r.get('Time per task'),
             'latency':r.get('Time to first token'), 'tokens':r.get('Output tokens per task'),
             'coverage':r['measuredPct']} for r in rows]

def build():
    manifest = read_snapshot('manifest.json')
    for name, expected in manifest['sha256'].items():
        if hashlib.sha256((SOURCES/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Snapshot checksum mismatch: ' + name)
    rows = primary_rows(read_snapshot('aa-primary.json.gz')['models'])
    api, sub = priors_rows('api'), priors_rows('subscription')
    by_identity = {r['identity']:r for r in rows}
    comparisons = []
    for p in api:
        a = by_identity.get(p['identity'])
        comparisons.append({'identity':p['identity'], 'name':p['name'], 'matched':bool(a),
            'ardf_id':a['id'] if a else None, 'ardf_score':a['score'] if a else None,
            'priors_score':p['score'], 'score_delta':a['score']-p['score'] if a and finite(a['score']) else None,
            'ardf_cost':a['cost'] if a else None, 'priors_cost':p['cost'],
            'cost_delta':a['cost']-p['cost'] if a and finite(a['cost']) and finite(p['cost']) else None})
    out={'manifest':manifest, 'benchmarks':BENCHMARKS, 'rows':rows, 'priors_api':api,
         'priors_subscription':sub, 'comparisons':comparisons,
         'frontier':frontier(rows), 'published_frontier':frontier(rows,score='published_score',cost='published_cost'),
         'priors_api_frontier':frontier(api), 'priors_subscription_frontier':frontier(sub)}
    return out

def ledger_refresh(payload):
    """Preserve old observations as history; current rows are direct primary data.

    Components are evidence, not independent replicated measurements. Only the
    recomputed composite and workload cost enter the general aggregate.
    """
    p = ROOT/'data/unified-model-evidence.csv'
    with p.open(newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;old=list(reader)
    old=[r for r in old if r.get('source_id')!='aa-primary-current']
    for r in old:
        if r.get('record_type')=='observation':r.update(use_in_aggregate='0',is_historical='1')
    fresh=[]
    for m in payload['rows']:
        # Prefix avoids silently merging a historical alias or fallback track.
        base={f:'' for f in fields}
        base.update(model_key='aa-current:'+m['id'],display_name=m['name'],provider=m['lab'],family=m['model'],
            effort=m['effort'],harness='AA published evaluation track',release_date=m['release'] or '',
            availability='observed',source_id='aa-primary-current',source_label='AA primary current, ARDF recomputation',
            source_publisher='Artificial Analysis',source_version=payload['manifest']['retrieved_at'],source_url=m['url'],
            retrieved_at=payload['manifest']['retrieved_at'],is_historical='0',quality='primary',confidence='direct',
            input_price_per_m=m['input_price'] if m['input_price'] is not None else '',
            output_price_per_m=m['output_price'] if m['output_price'] is not None else '',
            context_window_tokens=m['context'] or '',base_weight='1',identity_mapping='exact-primary-slug-and-effort',
            notes='Current primary track. Composite recomputed from displayed components. Default fallback preserved in display name.')
        fresh.append({**base,'record_type':'catalog'})
        metrics=[('aa_intelligence_index','capability',m['score'],'1'),('aa_cost_per_task_usd','cost',m['cost'],'1')]
        metrics += [('aa_component_'+k,'capability',v,'0') for k,v in m['components'].items()]
        for metric,axis,v,aggregate in metrics:
            if not finite(v):continue
            fresh.append({**base,'record_type':'observation','observation_id':'current:'+m['id']+':'+metric,
                'metric_name':metric,'metric_axis':axis,'raw_value':v,'raw_unit':'USD per task' if axis=='cost' else 'score / 100',
                'raw_direction':'lower' if axis=='cost' else 'higher','use_in_aggregate':aggregate,
                'is_reference_scale':aggregate})
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(old+fresh)

def write_reports(data):
    def table(rows):
        return '\n'.join(['| Model / effort | Score | USD / task |','|---|---:|---:|']+
            [f"| {r['name']} | {r['score']:.6f} | {r['cost']:.9g} |" for r in rows])
    text='''---
title: Independently recomputed current ARDF frontiers
status: verified-calculation
---

# Full all-model frontier

Computed from primary Artificial Analysis model payload, not Priors scores.
Each point is a model/effort/evaluation track. Dominance uses full precision;
ties are retained and missing prices are excluded with disclosure. A zero cost
stays eligible only when a free route with the same name is listed in a pinned
catalog (verified free); an unverified $0 is held out of dominance and listed in its own
band below. This is the measured universe, not a claim to benchmark every
available model. Prices are benchmark workload estimates, not subscription bills.

'''
    text+=f"Snapshot: {data['manifest']['retrieved_at']}. Catalog: {len(data['rows'])}; complete component score: {sum(finite(r['score']) for r in data['rows'])}; paired score/cost: {sum(finite(r['score']) and finite(r['cost']) for r in data['rows'])}.\n\n"
    held=[r for r in data['rows'] if finite(r['score']) and r.get('cost_state')=='zero-unverified']
    text+=table(data['frontier'])
    text+='\n\n## Unverified free ($0 listed by AA, held out of dominance)\n\n| Model / effort | Score | Evidence |\n|---|---:|---|\n'
    text+=''.join(f"| {r['name']} | {r['score']:.6f} | {r['cost_evidence']} |\n" for r in sorted(held,key=lambda r:(-r['score'],r['id']))) or '| none | | |\n'
    text+='\n## Priors API cross-check\n\n'+table(data['priors_api_frontier'])
    text+='\n\n## Priors subscription estimates (different objective)\n\n'+table(data['priors_subscription_frontier'])
    text+='\n\n## Exact matched-row differences\n\n| Model / effort | ARDF score | Priors score | Delta | ARDF API cost | Priors API cost |\n|---|---:|---:|---:|---:|---:|\n'
    for c in data['comparisons']:
        text+='| '+' | '.join(str(c[k]) for k in ['name','ardf_score','priors_score','score_delta','ardf_cost','priors_cost'])+' |\n'
    (ROOT/'docs/current-frontier.md').write_text(text)
    (ROOT/'data/current-frontier.json').write_text(json.dumps(data,indent=2,allow_nan=False))
    with (ROOT/'data/current-comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data['comparisons'][0]));w.writeheader();w.writerows(data['comparisons'])

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--refresh-ledger',action='store_true');args=p.parse_args()
    d=build();write_reports(d)
    if args.refresh_ledger:ledger_refresh(d)
    print(json.dumps({'catalog':len(d['rows']),'complete':sum(finite(r['score']) for r in d['rows']),
        'frontier':[(r['name'],r['score'],r['cost']) for r in d['frontier']],
        'unmatched':[r['name'] for r in d['comparisons'] if not r['matched']]},indent=2))
