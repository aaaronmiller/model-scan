#!/usr/bin/env python3
"""model-scan overall — CLI to get best model for a given tier.
Uses AI Index (from AA cache) as primary sort.
The -a flag means "A-tier quality" (AI Index > 45), not "tier label = A".
Returns model_id as plain text (for piping into scripts).
"""
import argparse, sqlite3, json, re
from pathlib import Path

DB = Path.home() / ".config" / "model-scan" / "model_scan.db"
AA_CACHE = Path.home() / ".config" / "model-scan" / "aa_cache.json"

def _load_aa_scores():
    """Load AA scores. Returns dict of model_key -> ai_index."""
    try:
        data = json.loads(AA_CACHE.read_text())
        lookup = data.get("lookup", data) if isinstance(data, dict) else data
        items = lookup.values() if isinstance(lookup, dict) else lookup
        scores = {}
        for m in items:
            if isinstance(m, dict) and m.get("ai_index") is not None:
                ai = m["ai_index"]
                slug = (m.get("slug") or "").lower().replace("-", "")
                name = (m.get("name") or "").lower().replace("-", "").replace(" ", "")
                scores[slug] = ai
                scores[name] = ai
        return scores
    except:
        return {}

def _get_aa_score(model_id, aa_scores):
    """Match a model_id against AA cache with fuzzy key matching."""
    mid = model_id.lower().replace("-", "").replace("/", "").replace(":", "")
    mid2 = model_id.lower().replace("/", "-").replace(":", "")
    
    # Direct match
    if mid in aa_scores:
        return aa_scores[mid]
    if mid2 in aa_scores:
        return aa_scores[mid2]
    
    # Partial match: find any AA key contained in or containing this model_id
    for key, val in aa_scores.items():
        if key in mid or mid in key:
            return val
        # Try with stripped prefixes
        key_stripped = key.replace("nvidia", "").replace("openrouter", "")
        mid_stripped = mid.replace("nvidia", "").replace("openrouter", "")
        if key_stripped and mid_stripped and (key_stripped in mid_stripped or mid_stripped in key_stripped):
            return val
    return None

def best_model(tier="ANY", free_only=False, top_n=3):
    if not DB.exists():
        return ["no-scan-data"]
    
    aa = _load_aa_scores()
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    
    if free_only:
        q = "SELECT model_id, provider, ai_index, composite, tier FROM models WHERE scan_id = (SELECT MAX(scan_id) FROM scans) AND (model_id LIKE '%:free' OR model_id LIKE '%-free' OR model_id LIKE '%free')"
    else:
        q = "SELECT model_id, provider, ai_index, composite, tier FROM models WHERE scan_id = (SELECT MAX(scan_id) FROM scans)"
    
    rows = conn.execute(q).fetchall()
    conn.close()
    
    scored = []
    for r in rows:
        aa_score = _get_aa_score(r["model_id"], aa)
        ai = aa_score if aa_score is not None else (r["ai_index"] or 0)
        
        # -a flag: AI > 45 = A-tier quality
        if tier == "A_QUALITY" and ai < 45:
            continue
        # -t flag: explicit tier label filter
        if tier not in ("ANY", "A_QUALITY") and (r["tier"] or "").upper() != tier:
            continue
        
        scored.append((ai, r["model_id"], r["provider"] or ""))
    
    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:top_n]]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-a", "--a-tier", action="store_true", help="A-tier quality (AI > 45)")
    p.add_argument("-t", "--tier", help="Specific tier by LABEL (S, A, B, C)")
    p.add_argument("--free", action="store_true", help="Free models only")
    p.add_argument("-n", "--count", type=int, default=1, help="Number of results")
    args = p.parse_args()
    
    tier = "A_QUALITY" if args.a_tier else (args.tier or "ANY")
    results = best_model(tier.upper(), args.free, args.count)
    for r in results:
        print(r)

if __name__ == "__main__":
    main()
