"""Gateway API — model-scan v5 Gateway Endpoints

Provides FastAPI endpoints for:
  /health         — provider health summary
  /models         — list accessible models with IQ/TC
  /route          — best model for a slot
  /quota          — remaining credits per provider
  /programs       — monitored program status
  /swap           — recommend alternative model for a slot
  /iqtc           — IQ and TC scores for a specific model

Run standalone:  python3 gateway.py
Or mount in FastAPI:  app.mount("/api/v1/gateway", gateway_app)
"""
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from fastapi import FastAPI, Query
    from fastapi.responses import JSONResponse, FileResponse
    import uvicorn
except ImportError:
    FastAPI = None

CONFIG_DIR = Path.home() / ".config" / "model-scan"
DATABASE_FILE = CONFIG_DIR / "model_scan.db"
PROGRAM_ASSIGNMENTS_FILE = CONFIG_DIR / "program_assignments.json"
PROVIDER_HOURS_FILE = CONFIG_DIR / "provider_hour_windows.yaml"

# ── DB helpers ──────────────────────────────────────────────────────────

def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DATABASE_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def _load_programs() -> dict:
    if PROGRAM_ASSIGNMENTS_FILE.exists():
        try:
            return json.loads(PROGRAM_ASSIGNMENTS_FILE.read_text())
        except Exception:
            pass
    return {}

def _load_provider_hours() -> dict:
    if PROVIDER_HOURS_FILE.exists():
        try:
            import yaml
            return yaml.safe_load(PROVIDER_HOURS_FILE.read_text()) or {}
        except Exception:
            pass
    return {}

def _get_available_providers() -> list[str]:
    """Get list of providers from latest scan."""
    try:
        conn = _db()
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT m.provider
            FROM models m
            JOIN scans s ON m.scan_id = s.scan_id
            WHERE s.scan_id = (SELECT MAX(scan_id) FROM scans)
            ORDER BY m.provider
        """)
        rows = c.fetchall()
        conn.close()
        return [r["provider"] for r in rows]
    except Exception:
        return []

def _get_latest_scan_id(require_fitness: bool = False) -> int | None:
    try:
        conn = _db()
        c = conn.cursor()
        if require_fitness:
            c.execute("""
                SELECT MAX(sf.scan_id) FROM slot_fitness sf
                JOIN scans s ON sf.scan_id = s.scan_id
            """)
        else:
            c.execute("SELECT MAX(scan_id) FROM scans")
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None

def _get_models(accessible_only: bool = True) -> list[dict]:
    """Get models from the latest scan."""
    scan_id = _get_latest_scan_id()
    if not scan_id:
        return []
    try:
        conn = _db()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if accessible_only:
            c.execute("""
                SELECT m.* FROM models m
                WHERE m.scan_id = ? AND m.accessible = 1
                ORDER BY m.tier, m.model_id
            """, (scan_id,))
        else:
            c.execute("""
                SELECT m.* FROM models m
                WHERE m.scan_id = ?
                ORDER BY m.tier, m.model_id
            """, (scan_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

# ── FastAPI app ────────────────────────────────────────────────────────

app = FastAPI(
    title="model-scan Gateway API",
    version="5.0.0",
    description="Gateway endpoints for model-scan multi-program monitoring",
)

# CORS for web dashboard
try:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except ImportError:
    pass


@app.get("/health")
async def gateway_health():
    """Provider health summary from latest scan data."""
    programs = _load_programs()
    kiro = programs.get("kiro", {})
    oc = programs.get("opencode", {})
    
    # Get provider health from DB
    scan_id = _get_latest_scan_id()
    providers = _get_available_providers()
    
    health_data = {}
    for prov in providers:
        try:
            conn = _db()
            c = conn.cursor()
            c.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN accessible=1 THEN 1 ELSE 0 END) as healthy,
                       SUM(CASE WHEN accessible=0 THEN 1 ELSE 0 END) as failed
                FROM models WHERE scan_id=? AND provider=?
            """, (scan_id, prov))
            row = c.fetchone()
            conn.close()
            total = row["total"] if row else 0
            healthy = row["healthy"] if row else 0
            failed = row["failed"] if row else 0
            status = "healthy" if failed == 0 and healthy > 0 else (
                "degraded" if failed <= healthy else "unstable"
            ) if total > 0 else "unknown"
            health_data[prov] = {
                "status": status,
                "total": total,
                "healthy": healthy,
                "failed": failed,
                "fail_rate": round(failed / total, 3) if total > 0 else 0,
            }
        except Exception:
            health_data[prov] = {"status": "unknown", "total": 0, "healthy": 0, "failed": 0}

    return JSONResponse({
        "provider_health": health_data,
        "kiro_credits": kiro.get("credits_remaining"),
        "kiro_total": kiro.get("credits_total"),
        "kiro_model": kiro.get("model_available"),
        "opencode_go_status": oc.get("go_status"),
        "opencode_go_refill": oc.get("go_estimated_refill"),
        "opencode_zen_status": oc.get("zen_status"),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/models")
async def gateway_models(
    tier: str = Query(None, description="Filter by tier (S/A/B/C)"),
    min_iq: float = Query(None, ge=0, le=100, description="Minimum IQ score"),
    min_tc: float = Query(None, ge=0, le=100, description="Minimum TC score"),
    provider: str = Query(None, description="Filter by provider"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
):
    """List accessible models with IQ/TC scores from latest scan."""
    models = _get_models(accessible_only=True)
    results = []
    for m in models:
        # Build IQ/TC (simplified — uses stored composite/ai_index)
        iq = m.get("ai_index") or m.get("composite", 0)
        tc = 75 if m.get("has_tools") else (
            50 if m.get("accessible") else 0
        )
        entry = {
            "model_id": m["model_id"],
            "provider": m["provider"],
            "api_model": m.get("api_model", ""),
            "tier": m.get("tier", "—"),
            "iq": round(iq, 1) if iq else None,
            "tc": tc,
            "tps": m.get("tps", 0),
            "latency_s": m.get("latency_s", 0),
            "has_tools": bool(m.get("has_tools")),
            "has_vision": bool(m.get("has_vision")),
            "arch": m.get("arch", "unknown"),
            "price_blended": m.get("price_blended"),
        }
        # Apply filters
        if tier and entry["tier"] != tier:
            continue
        if min_iq is not None and (entry["iq"] is None or entry["iq"] < min_iq):
            continue
        if min_tc is not None and entry["tc"] < min_tc:
            continue
        if provider and entry["provider"] != provider:
            continue
        results.append(entry)
    return JSONResponse({"count": len(results), "models": results[:limit]})


@app.get("/route")
async def gateway_route(
    slot: str = Query(..., description="Slot ID (e.g. R1_primary)"),
):
    """Best model for a given slot from latest scan."""
    # Load slot definitions
    slots_file = CONFIG_DIR / "slot_definitions.yaml"
    slot_defs = {}
    if slots_file.exists():
        try:
            import yaml
            slot_defs = yaml.safe_load(slots_file.read_text()) or {}
        except Exception:
            pass
    
    if slot not in slot_defs:
        return JSONResponse(
            {"error": f"Unknown slot: {slot}. Available: {list(slot_defs.keys())}"},
            status_code=404,
        )
    
    slot_def = slot_defs[slot]
    models = _get_models(accessible_only=True)
    
    # Load slot fitness from DB for this slot
    scan_id = _get_latest_scan_id(require_fitness=True)
    try:
        conn = _db()
        c = conn.cursor()
        c.execute("""
            SELECT m.model_id, m.provider, m.api_model, m.tps, m.latency_s,
                   m.tier, m.has_tools, m.has_vision, m.arch, m.price_blended,
                   sf.fitness,
                   m.ai_index, m.composite
            FROM slot_fitness sf
            JOIN models m ON sf.model_fk = m.model_pk
            WHERE sf.scan_id = ? AND sf.slot_id = ?
            ORDER BY sf.fitness DESC LIMIT 10
        """, (scan_id, slot))
        rows = c.fetchall()
        conn.close()
        
        candidates = []
        for r in rows:
            d = dict(r)
            entry = {
                "model_id": d["model_id"],
                "provider": d["provider"],
                "api_model": d.get("api_model", ""),
                "tier": d.get("tier", "—"),
                "fitness": round(d["fitness"], 1) if d.get("fitness") else 0,
                "tps": d.get("tps", 0),
                "latency_s": d.get("latency_s", 0),
                "has_tools": bool(d.get("has_tools")),
                "has_vision": bool(d.get("has_vision")),
                "arch": d.get("arch", "unknown"),
                "price_blended": d.get("price_blended"),
                "iq": d.get("ai_index") or d.get("composite", 0),
                "tc": 75 if d.get("has_tools") else 50,
            }
            candidates.append(entry)
        
        return JSONResponse({
            "slot": slot,
            "label": slot_def.get("label", slot),
            "eval_mode": slot_def.get("eval_mode", "free"),
            "candidates_count": len(candidates),
            "best": candidates[0] if candidates else None,
            "candidates": candidates,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/quota")
async def gateway_quota():
    """Remaining credits/quota per provider."""
    programs = _load_programs()
    kiro = programs.get("kiro", {})
    oc = programs.get("opencode", {})
    
    # Get model counts per provider from latest scan
    scan_id = _get_latest_scan_id()
    provider_counts = {}
    if scan_id:
        try:
            conn = _db()
            c = conn.cursor()
            c.execute("""
                SELECT provider,
                       COUNT(*) as total,
                       SUM(CASE WHEN accessible=1 THEN 1 ELSE 0 END) as accessible
                FROM models WHERE scan_id=?
                GROUP BY provider ORDER BY provider
            """, (scan_id,))
            rows = c.fetchall()
            conn.close()
            for r in rows:
                provider_counts[r["provider"]] = {
                    "total_models": r["total"],
                    "accessible_models": r["accessible"],
                }
        except Exception:
            pass
    
    return JSONResponse({
        "kiro": {
            "credits_remaining": kiro.get("credits_remaining", "?"),
            "credits_total": kiro.get("credits_total", "?"),
            "status": kiro.get("status", "unknown"),
            "resets": kiro.get("resets", "?"),
            "model_available": kiro.get("model_available", "?"),
        },
        "opencode_go": {
            "status": oc.get("go_status", "unknown"),
            "estimated_refill": oc.get("go_estimated_refill", "?"),
        },
        "opencode_zen": {
            "status": oc.get("zen_status", "unknown"),
        },
        "provider_model_counts": provider_counts,
    }, status_code=200)


@app.get("/programs")
async def gateway_programs():
    """Monitored program status (from program_assignments.json)."""
    programs = _load_programs()
    if not programs or not any(k not in ("version", "last_updated") for k in programs):
        return JSONResponse({"error": "No program assignments found"}, status_code=404)
    
    # Filter out metadata keys
    result = {}
    for k, v in programs.items():
        if k not in ("version", "last_updated"):
            result[k] = v
    
    # Detect cross-program conflicts
    conflicts = []
    provider_model_map: dict[str, list[str]] = {}
    for prog_name, prog_data in result.items():
        if not isinstance(prog_data, dict):
            continue
        for slot_key, model_val in prog_data.items():
            if slot_key in ("provider_conflicts", "zen_status", "go_status",
                           "go_estimated_refill", "zen_estimated_refill"):
                continue
            if isinstance(model_val, str) and model_val and model_val != "?":
                p_key = f"{slot_key}:{model_val}"
                if p_key not in provider_model_map:
                    provider_model_map[p_key] = []
                if prog_name not in provider_model_map[p_key]:
                    provider_model_map[p_key].append(prog_name)
    
    for p_key, progs in provider_model_map.items():
        if len(progs) > 1:
            conflicts.append({"programs": progs, "slot_model": p_key})
    
    return JSONResponse({
        "programs": result,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
    })


@app.get("/swap")
async def gateway_swap(
    model_id: str = Query(..., description="Model to swap out"),
    slot: str = Query(None, description="Target slot (optional)"),
    max_price: float = Query(None, ge=0, description="Max price per million tokens"),
):
    """Recommend alternative model for a model (and optionally slot)."""
    models = _get_models(accessible_only=True)
    
    # Find the model being swapped
    source = None
    for m in models:
        if m["model_id"] == model_id:
            source = m
            break
    
    if not source:
        return JSONResponse({"error": f"Model not found: {model_id}"}, status_code=404)
    
    # Find alternatives: same tier, different provider
    alternatives = []
    for m in models:
        if m["model_id"] == model_id:
            continue
        if m.get("tier") != source.get("tier"):
            continue
        if m.get("provider") == source.get("provider"):
            # Prefer different provider for diversity
            alt_score = 0.8
        else:
            alt_score = 1.0
        
        # Price filter
        if max_price is not None:
            price = m.get("price_blended") or 0
            if price > max_price:
                continue
        
        # IQ approximation
        iq = m.get("ai_index") or m.get("composite", 0)
        
        entry = {
            "model_id": m["model_id"],
            "provider": m["provider"],
            "tier": m.get("tier", "—"),
            "tps": m.get("tps", 0),
            "latency_s": m.get("latency_s", 0),
            "iq": iq,
            "diversity_score": round(alt_score, 2),
            "price_blended": m.get("price_blended"),
        }
        alternatives.append(entry)
    
    # Sort by diversity (different provider first), then IQ
    alternatives.sort(key=lambda x: (-x["diversity_score"], -x.get("iq", 0)))
    
    return JSONResponse({
        "source_model": model_id,
        "source_tier": source.get("tier", "—"),
        "source_provider": source.get("provider"),
        "alternatives": alternatives[:10],
        "total_alternatives": len(alternatives),
    })


@app.get("/iqtc")
async def gateway_iqtc(
    model_id: str = Query(..., description="Model ID to look up"),
    provider: str = Query(None, description="Provider filter"),
):
    """IQ and TC scores for a specific model from latest scan."""
    models = _get_models(accessible_only=False)
    
    matches = []
    for m in models:
        if m["model_id"] != model_id:
            continue
        if provider and m["provider"] != provider:
            continue
        
        iq = m.get("ai_index") or m.get("composite", 0)
        tc = 75 if m.get("has_tools") else (
            50 if m.get("accessible") else 0
        )
        
        matches.append({
            "model_id": m["model_id"],
            "provider": m["provider"],
            "api_model": m.get("api_model", ""),
            "tier": m.get("tier", "—"),
            "iq": round(iq, 1) if iq else None,
            "tc": tc,
            "has_tools": bool(m.get("has_tools")),
            "accessible": bool(m.get("accessible")),
            "tps": m.get("tps", 0),
            "latency_s": m.get("latency_s", 0),
            "fail_class": m.get("fail_class", ""),
            "scanned_at": m.get("scanned_at", ""),
        })
    
    if not matches:
        return JSONResponse({"error": f"Model not found: {model_id}"}, status_code=404)
    
    return JSONResponse({
        "count": len(matches),
        "results": matches,
    })


# ── Session Management ──────────────────────────────────────────────────

@app.get("/sessions")
async def gateway_sessions(
    limit: int = Query(20, ge=1, le=100, description="Max sessions to return"),
    state: str = Query(None, description="Filter by state (active/idle/paused/completed)"),
):
    """List Hermes sessions with priority, state, and resource tracking."""
    try:
        from session_manager import SessionManager
        sm = SessionManager()
        summary = sm.get_session_summary()
        
        sessions = summary.get("top_sessions", [])
        if state:
            sessions = [s for s in sessions if s.get("state") == state]
        
        return JSONResponse({
            "total": summary["total_sessions"],
            "active": summary["active"],
            "idle": summary["idle"],
            "paused": summary["paused"],
            "by_program": summary["by_program"],
            "provider_slots": summary["provider_slots"],
            "quota_summary": summary["quota_summary"],
            "recommendations": sm.get_recommendations(),
            "sessions": sessions[:limit],
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/sessions/{session_id}")
async def gateway_session_detail(session_id: str):
    """Get detailed info for a specific session — combines filesystem + quota ledger."""
    try:
        from session_manager import get_session_quota
        
        # Quota ledger data
        ledger = get_session_quota(session_id)
        
        # Filesystem session
        session_path = Path.home() / ".hermes" / "sessions" / f"{session_id}.json"
        session_dir = Path.home() / ".hermes" / "sessions" / session_id
        
        info = {}
        
        if session_path.exists():
            try:
                data = json.loads(session_path.read_text())
                info["filedata"] = data
            except (json.JSONDecodeError, OSError):
                pass
        
        if session_dir.exists():
            info["path"] = str(session_dir)
            info["modified"] = datetime.fromtimestamp(
                session_dir.stat().st_mtime, tz=timezone.utc
            ).isoformat()
            # logs/
            logs_dir = session_dir / "logs"
            if logs_dir.exists():
                log_files = []
                for f in sorted(logs_dir.iterdir(), key=lambda x: x.stat().st_mtime):
                    if f.is_file():
                        log_files.append({
                            "name": f.name,
                            "size_kb": round(f.stat().st_size / 1024, 1),
                        })
                info["logs"] = log_files
        
        # Merge with quota ledger
        if ledger:
            info["quota"] = ledger
        
        if not info:
            return JSONResponse({"error": f"Session not found: {session_id}"}, status_code=404)
        
        return JSONResponse({"session_id": session_id, **info})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/quota/ledger")
async def gateway_quota_ledger(
    provider: str = Query(None, description="Filter by provider"),
    session_id: str = Query(None, description="Filter by session"),
):
    """Query the quota ledger for token usage and cost tracking."""
    try:
        from session_manager import get_quota_summary, get_session_quota, init_quota_db, get_provider_slot_usage
        
        init_quota_db()
        
        if session_id:
            result = get_session_quota(session_id)
            if not result:
                return JSONResponse({"error": f"No quota data for session: {session_id}"}, status_code=404)
            return JSONResponse({"type": "session_detail", "data": result})
        
        summary = get_quota_summary(provider)
        slots = get_provider_slot_usage(provider)
        
        return JSONResponse({
            "type": "ledger_summary",
            "provider_summary": summary,
            "provider_slots": slots,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/sessions/{session_id}/release")
async def gateway_session_release(session_id: str):
    """Release all provider slots for a session."""
    try:
        from session_manager import SessionManager
        sm = SessionManager()
        sm.release_session(session_id)
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "message": "Resources released",
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/session-recommendations")
async def gateway_session_recommendations():
    """Get session management recommendations."""
    try:
        from session_manager import SessionManager
        sm = SessionManager()
        recs = sm.get_recommendations()
        return JSONResponse({
            "count": len(recs),
            "recommendations": recs,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Config Management ──────────────────────────────────────────────────

@app.get("/configs")
async def gateway_configs():
    """List generated configs from changelog and templates."""
    config_dir = CONFIG_DIR / "templates"
    changelog_path = CONFIG_DIR / "config_changelog.jsonl"
    
    # Load changelog
    history = []
    if changelog_path.exists():
        with open(changelog_path) as f:
            for line in f:
                try:
                    history.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    # List templates
    templates = []
    if config_dir.exists():
        for f in sorted(config_dir.glob("template-*.yaml")):
            templates.append({
                "name": f.stem.replace("template-", ""),
                "path": str(f),
                "size_kb": round(f.stat().st_size / 1024, 1),
                "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
    
    # Load issue scores summary
    issue_scores_path = CONFIG_DIR / "model_issue_scores.json"
    issue_summary = {}
    if issue_scores_path.exists():
        try:
            data = json.loads(issue_scores_path.read_text())
            scores = data.get("scores", {})
            for model, cats in scores.items():
                issue_summary[model] = len(cats.get("_global", {}))
        except (json.JSONDecodeError, OSError):
            pass
    
    return JSONResponse({
        "templates": templates,
        "history": history[-20:],  # last 20 changes
        "history_count": len(history),
        "models_with_issues": len(issue_summary),
        "issue_summary": issue_summary,
    })


@app.get("/configs/{template_name}")
async def gateway_config_detail(template_name: str):
    """Get the latest generated config for a template."""
    valid_templates = ["primary", "worker-a", "worker-b"]
    if template_name not in valid_templates:
        return JSONResponse({"error": f"Unknown template: {template_name}. Valid: {valid_templates}"}, status_code=404)
    
    # Generate on demand
    try:
        sys.path.insert(0, str(CONFIG_DIR / "templates"))
        from config_generator import main as cfg_main, generate_config, load_models_from_db, load_issue_scores, load_slot_defs, load_db, get_latest_scan, compute_hash, load_previous_hash, log_change, generate_summary
        
        conn = load_db()
        scan_id = get_latest_scan(conn)
        if not scan_id:
            return JSONResponse({"error": "No scan data available"}, status_code=503)
        
        models = load_models_from_db(conn, scan_id)
        issue_scores = load_issue_scores()
        slot_defs = load_slot_defs()
        conn.close()
        
        config_yaml = generate_config(template_name, models, issue_scores, slot_defs)
        if not config_yaml:
            return JSONResponse({"error": "Config generation failed"}, status_code=500)
        
        content_hash = compute_hash(config_yaml)
        prev_hash = load_previous_hash(template_name)
        summary = generate_summary({})
        changed = content_hash != prev_hash
        
        return JSONResponse({
            "template": template_name,
            "hash": content_hash,
            "prev_hash": prev_hash,
            "changed": changed,
            "scan_id": scan_id,
            "models_available": len(models),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config_yaml": config_yaml,
        })
    except ImportError as e:
        return JSONResponse({"error": f"config_generator not available: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/configs/{template_name}/diff")
async def gateway_config_diff(template_name: str):
    """Show diff between current generated config and last cached version."""
    changelog_path = CONFIG_DIR / "config_changelog.jsonl"
    if not changelog_path.exists():
        return JSONResponse({"error": "No changelog found"}, status_code=404)
    
    # Find the last two entries for this template
    entries = []
    with open(changelog_path) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("template") == template_name:
                    entries.append(entry)
            except json.JSONDecodeError:
                pass
    
    if len(entries) < 2:
        return JSONResponse({
            "template": template_name,
            "entries": len(entries),
            "prev_config": None,
            "curr_config": None,
            "note": "Need at least 2 entries for diff",
        })
    
    prev_entry = entries[-2]
    curr_entry = entries[-1]
    
    return JSONResponse({
        "template": template_name,
        "prev_hash": prev_entry.get("hash", ""),
        "curr_hash": curr_entry.get("hash", ""),
        "changed": prev_entry.get("hash", "") != curr_entry.get("hash", ""),
        "prev_timestamp": prev_entry.get("timestamp", ""),
        "curr_timestamp": curr_entry.get("timestamp", ""),
        "prev_summary": prev_entry.get("summary", ""),
        "curr_summary": curr_entry.get("summary", ""),
    })


@app.post("/configs/generate/{template_name}")
async def gateway_config_generate(template_name: str):
    """Trigger config generation for a template and write to file."""
    valid_templates = ["primary", "worker-a", "worker-b"]
    if template_name not in valid_templates:
        return JSONResponse({"error": f"Unknown template: {template_name}"}, status_code=404)
    
    # Create output path
    output_dir = CONFIG_DIR / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"config-{template_name}.yaml"
    
    try:
        sys.path.insert(0, str(CONFIG_DIR / "templates"))
        from config_generator import main as cfg_main
        
        import subprocess
        result = subprocess.run(
            [sys.executable, str(CONFIG_DIR / "templates" / "config_generator.py"),
             "--template", template_name, "--output", str(output_path)],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode != 0:
            return JSONResponse({
                "error": f"Generation failed: {result.stderr}",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }, status_code=500)
        
        if output_path.exists():
            content = output_path.read_text()
            return JSONResponse({
                "success": True,
                "template": template_name,
                "output_path": str(output_path),
                "size_bytes": len(content),
                "stdout": result.stdout.strip(),
            })
        else:
            return JSONResponse({
                "error": "No output file generated",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Cron status API ────────────────────────────────────────────────────

@app.get("/cron")
async def gateway_cron():
    """Return cron auto-deployment status."""
    try:
        from cron_manager import show_status, load_config
        cfg = load_config()
        return JSONResponse({
            "config": cfg,
            "status_text": show_status(),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Static dashboard ──────────────────────────────────────────────────

DASHBOARD_DIR = Path(__file__).parent

@app.get("/")
async def gateway_dashboard():
    """Serve the gateway dashboard HTML."""
    dashboard_path = DASHBOARD_DIR / "gateway_dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return JSONResponse({"error": "dashboard not found"}, status_code=404)


# ── Standalone runner ──────────────────────────────────────────────────

def main():
    if FastAPI is None:
        print("ERROR: fastapi and uvicorn required. pip install fastapi uvicorn")
        sys.exit(1)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8124
    print(f"Gateway API starting on http://0.0.0.0:{port}")
    print(f"Endpoints:")
    print(f"  GET /health          — Provider health summary")
    print(f"  GET /models          — List accessible models with IQ/TC")
    print(f"  GET /route?slot=     — Best model for a slot")
    print(f"  GET /quota           — Remaining credits per provider")
    print(f"  GET /programs        — Monitored program status")
    print(f"  GET /swap?model_id=  — Recommend alternative model")
    print(f"  GET /iqtc?model_id=  — IQ/TC for a model")
    print(f"  GET /sessions            — List Hermes sessions (priority, state, quota)")
    print(f"  GET /sessions/{'{session_id}'}       — Session details + quota ledger")
    print(f"  POST /sessions/{'{session_id}'}/release — Release session resources")
    print(f"  GET /session-recommendations — Session management recommendations")
    print(f"  GET /quota/ledger         — Quota ledger (token usage, cost, provider slots)")
    print(f"  GET /configs              — Config templates, history, issue summary")
    print(f"  GET /configs/{'{template}'}      — Generate config on demand")
    print(f"  GET /configs/{'{template}'}/diff  — Show config diff vs last version")
    print(f"  POST /configs/generate/{'{template}'} — Generate config and write to file")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
