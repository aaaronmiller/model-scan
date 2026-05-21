"""
model-scan v5 — FastAPI REST Backend
Serves scan results from SQLite database to the Svelte frontend.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="model-scan API", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path.home() / ".config" / "model-scan" / "model_scan.db"
CACHE_PATH = Path.home() / ".config" / "model-scan" / "results.json"


def get_db() -> sqlite3.Connection:
    """Get SQLite connection with row factory."""
    if not DB_PATH.exists():
        raise HTTPException(503, f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert SQLite row to dict."""
    if row is None:
        return None
    return dict(row)


# ── Endpoints ──────────────────────────────────────────────────────────


@app.get("/api/v1/scan/latest")
def get_latest_scan():
    """Return latest scan results with models, slots, and incumbents."""
    try:
        conn = get_db()
        cur = conn.execute("SELECT scan_id, scanned_at, model_count FROM scans ORDER BY scan_id DESC LIMIT 1")
        scan = row_to_dict(cur.fetchone())
        if not scan:
            return {"scan": None, "models": [], "slots": [], "error": "no scans yet"}

        cur = conn.execute("""
            SELECT m.*, sf.fitness as slot_fitness, s.slot_id as slot_name
            FROM models m
            LEFT JOIN slot_fitness sf ON sf.model_fk = m.model_pk AND sf.scan_id = m.scan_id
            LEFT JOIN (SELECT model_fk, slot_id FROM slot_fitness WHERE scan_id = ?) s ON s.model_fk = m.model_pk
            WHERE m.scan_id = ?
            ORDER BY m.composite DESC
        """, (scan["scan_id"], scan["scan_id"]))
        models = [row_to_dict(r) for r in cur.fetchall()]

        cur = conn.execute("""
            SELECT slot_id, provider, model_id, status, latency_s, tps
            FROM incumbents WHERE scan_id = ?
        """, (scan["scan_id"],))
        incumbents = [row_to_dict(r) for r in cur.fetchall()]

        conn.close()
        return {"scan": scan, "models": models, "incumbents": incumbents}
    except HTTPException:
        raise
    except Exception as e:
        # Fallback: load from cached JSON
        if CACHE_PATH.exists():
            data = json.loads(CACHE_PATH.read_text())
            return {"scan": {"scanned_at": data.get("scanned_at", "unknown"), "model_count": len(data.get("models", []))},
                    "models": data.get("models", []), "incumbents": data.get("incumbents", []), "source": "cache"}
        return {"scan": None, "models": [], "incumbents": [], "error": str(e)}


@app.get("/api/v1/models")
def list_models(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    tier: str | None = Query(None),
    sort: str = Query("composite", regex="^(composite|tps|latency_s|ai_index|tier)$"),
):
    """List all models from the latest scan with optional filters."""
    try:
        conn = get_db()
        cur = conn.execute("SELECT MAX(scan_id) FROM scans")
        scan_id = cur.fetchone()[0]
        if not scan_id:
            return []

        where = "WHERE m.scan_id = ?"
        params: list[Any] = [scan_id]
        if tier:
            where += " AND m.tier = ?"
            params.append(tier)

        order = {"composite": "m.composite DESC", "tps": "m.tps DESC",
                 "latency_s": "m.latency_s ASC", "ai_index": "m.ai_index DESC",
                 "tier": "m.tier ASC"}.get(sort, "m.composite DESC")

        cur = conn.execute(f"""
            SELECT m.* FROM models m {where}
            ORDER BY {order} LIMIT ? OFFSET ?
        """, [*params, limit, offset])
        models = [row_to_dict(r) for r in cur.fetchall()]
        conn.close()
        return models
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/models/{model_id:path}")
def get_model(model_id: str):
    """Get single model detail."""
    try:
        conn = get_db()
        cur = conn.execute("SELECT MAX(scan_id) FROM scans")
        scan_id = cur.fetchone()[0]
        if not scan_id:
            raise HTTPException(404, "No scans found")

        # Try exact match first, then LIKE for prefix matches
        cur = conn.execute(
            "SELECT * FROM models WHERE scan_id = ? AND model_id = ? LIMIT 1",
            [scan_id, model_id]
        )
        model = row_to_dict(cur.fetchone())
        
        # If not found, try LIKE for partial/URL-encoded variants
        if not model:
            # Remove any leading/trailing junk from URL encoding
            clean = model_id.strip().replace("%2F", "/").replace("%20", " ")
            cur = conn.execute(
                "SELECT * FROM models WHERE scan_id = ? AND (model_id = ? OR model_id LIKE ?) LIMIT 1",
                [scan_id, clean, f"%{clean.split('/')[-1]}"]
            )
            model = row_to_dict(cur.fetchone())
        
        if not model:
            raise HTTPException(404, f"Model {model_id} not found")
        
        conn.close()
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/v1/slots")
def list_slots():
    """Return slot definitions with current incumbents."""
    try:
        conn = get_db()
        cur = conn.execute("SELECT MAX(scan_id) FROM scans")
        scan_id = cur.fetchone()[0]
        if not scan_id:
            return []

        cur = conn.execute(
            "SELECT DISTINCT slot_id FROM incumbents WHERE scan_id = ?", (scan_id,))
        slots = [r["slot_id"] for r in cur.fetchall()]

        cur = conn.execute(
            "SELECT slot_id, provider, model_id, status, tps, latency_s FROM incumbents WHERE scan_id = ?",
            (scan_id,))
        incumbents = {r["slot_id"]: row_to_dict(r) for r in cur.fetchall()}

        conn.close()
        return [{"slot_id": s, "incumbent": incumbents.get(s)} for s in slots]
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/scan/history")
def scan_history(limit: int = Query(30, ge=1, le=200)):
    """Return scan history summary."""
    try:
        conn = get_db()
        cur = conn.execute(
            "SELECT scan_id, scanned_at, model_count, healthy, degraded, failed FROM scans ORDER BY scan_id DESC LIMIT ?",
            (limit,))
        scans = [row_to_dict(r) for r in cur.fetchall()]
        conn.close()
        return scans
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/providers")
def list_providers():
    """Return provider health summary from latest scan."""
    try:
        conn = get_db()
        cur = conn.execute("SELECT MAX(scan_id) FROM scans")
        scan_id = cur.fetchone()[0]
        if not scan_id:
            return []

        cur = conn.execute(
            "SELECT provider, COUNT(*) as model_count, SUM(accessible) as accessible FROM models WHERE scan_id = ? GROUP BY provider",
            (scan_id,))
        providers = [row_to_dict(r) for r in cur.fetchall()]
        conn.close()
        return providers
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/slots/{slot_id}")
def get_slot(slot_id: str):
    """Return slot detail with candidate rankings."""
    try:
        conn = get_db()
        cur = conn.execute("SELECT MAX(scan_id) FROM scans")
        scan_id = cur.fetchone()[0]
        if not scan_id:
            raise HTTPException(404, "No scans found")
        cur = conn.execute(
            "SELECT * FROM incumbents WHERE scan_id = ? AND slot_id = ?",
            (scan_id, slot_id))
        incumbent = row_to_dict(cur.fetchone())
        cur = conn.execute("""
            SELECT m.*, sf.fitness
            FROM models m
            JOIN slot_fitness sf ON sf.model_fk = m.model_pk
            WHERE m.scan_id = ? AND sf.slot_id = ? AND m.accessible = 1
            ORDER BY sf.fitness DESC LIMIT 10
        """, (scan_id, slot_id))
        candidates = [row_to_dict(r) for r in cur.fetchall()]
        conn.close()
        return {"slot_id": slot_id, "incumbent": incumbent, "candidates": candidates}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/v1/compare")
def compare_models(models: str = Query(None, description="Comma-separated model IDs")):
    """Compare multiple models side by side."""
    if not models:
        return []
    model_ids = [m.strip() for m in models.split(",") if m.strip()]
    if len(model_ids) < 2:
        return []
    try:
        conn = get_db()
        cur = conn.execute("SELECT MAX(scan_id) FROM scans")
        scan_id = cur.fetchone()[0]
        if not scan_id:
            return []
        results = []
        for mid in model_ids:
            cur = conn.execute(
                "SELECT * FROM models WHERE scan_id = ? AND (model_id LIKE ? OR api_model LIKE ?) LIMIT 1",
                (scan_id, f"%{mid}%", f"%{mid}%"))
            row = row_to_dict(cur.fetchone())
            if row:
                results.append(row)
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/v1/config/preview")
def config_preview():
    """Generate config patch preview."""
    try:
        conn = get_db()
        cur = conn.execute("SELECT MAX(scan_id) FROM scans")
        scan_id = cur.fetchone()[0]
        if not scan_id:
            return {"patch": "# No scan data available"}
        cur = conn.execute("""
            SELECT i.slot_id, i.model_id as current, m2.model_id as recommended
            FROM incumbents i
            JOIN slot_fitness sf ON sf.slot_id = i.slot_id AND sf.scan_id = i.scan_id
            JOIN models m ON m.model_pk = sf.model_fk
            JOIN models m2 ON m2.model_pk = sf.model_fk AND m2.scan_id = i.scan_id
            WHERE i.scan_id = ?
            GROUP BY i.slot_id
            HAVING sf.fitness = (SELECT MAX(fitness) FROM slot_fitness WHERE slot_id = i.slot_id AND scan_id = i.scan_id)
        """, (scan_id,))
        rows = cur.fetchall()
        conn.close()
        lines = ["# model-scan config patch preview", f"# generated: {datetime.now().isoformat()}", ""]
        for r in rows:
            d = dict(r)
            lines.append(f"# {d['slot_id']}:")
            lines.append(f"#   current:    {d['current']}")
            lines.append(f"#   recommended: {d['recommended']}")
            lines.append("")
        return {"patch": "\n".join(lines)}
    except Exception as e:
        return {"patch": f"# Error: {e}"}


@app.get("/api/v1/analysis")
def get_analysis():
    """Run multi-source analysis: cross-references AA API, Models.dev, PinchBench."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from analysis.engine import run_full_analysis
    return run_full_analysis()


@app.get("/api/v1/popularity")
def get_popularity():
    """Return model popularity scores from HuggingFace."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from analysis.popularity import load
    scores = load()
    result = [{"model_id": k, "popularity": v.get("popularity", 0), 
               "downloads": v.get("downloads", 0), "likes": v.get("likes", 0)}
              for k, v in sorted(scores.items(), key=lambda x: -x[1].get("popularity", 0))]
    return result


@app.get("/api/v1/refinement/history")
def get_refinement_history():
    """Return refinement session history."""
    import json
    ref_log = Path(__file__).resolve().parent.parent / "refinement_log"
    ref_log.mkdir(parents=True, exist_ok=True)
    
    log_path = Path.home() / ".config" / "model-scan" / "refinement_log.json"
    if log_path.exists():
        return json.loads(log_path.read_text())
    
    # Also check analysis/refinement directory
    analysis_ref = Path.home() / ".config" / "model-scan" / "refinement"
    sessions = []
    if analysis_ref.exists():
        for f in sorted(analysis_ref.glob("refinement_*.json"), reverse=True)[:20]:
            try:
                data = json.loads(f.read_text())
                sessions.append({
                    "file": f.name,
                    "generated_at": data.get("generated_at", ""),
                    "overall": data.get("overall", {}),
                    "passes": len(data.get("passes", [])),
                })
                sessions.append(data)
            except:
                pass
    
    return sessions


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8123)
