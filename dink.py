#!/usr/bin/env python3
"""model-scan v4 — Hermes-aware diagnostic instrument panel.

Three-layer pipeline:
  1. Catalog enricher: live probes + AA API + models.dev + local refs
  2. Hermes role-fit scorer: reads ~/.hermes/config.yaml + claude-code-proxy/.env
  3. Role-organized renderer: incumbent panel + per-slot candidates + flat appendix

Sources:
  - Live probes: latency, throughput, tool-calling, empty-response detection
  - AA API: artificialanalysis.ai/api/v2/data/llms/models (x-api-key header, 1000/day)
  - models.dev: context, pricing, vision, reasoning capabilities
  - Local: ~/.hermes/config.yaml, ~/code/claude-code-proxy/.env, ~/.litellm/hermes-gateway.yaml

Install: chmod +x model-scan && cp model-scan ~/.local/bin/
Deps: pip install --user httpx pyyaml python-dotenv
Env: requires at minimum one of OPENROUTER_API_KEY, NVIDIA_API_KEY, GROQ_API_KEY, etc.
     plus optional AA_API_KEY (sign up at artificialanalysis.ai/login for free tier)

Usage:
  model-scan                       # full scan with all three sections
  model-scan --slot R1             # only show R1 primary candidates
  model-scan --refresh-aa          # force AA cache refresh
  model-scan --rehabilitate <id>   # remove model from bad list
  model-scan --by tier|fitness|tps|latency
  model-scan --json
  model-scan --no-incumbent --no-appendix
"""
from __future__ import annotations

import sys
from pathlib import Path
# Ensure project root is on path for module imports
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import argparse
import asyncio
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# DEPS
# ─────────────────────────────────────────────────────────────────────────────
try:
    import httpx
except ImportError:
    sys.exit("missing dep: pip install --user httpx pyyaml python-dotenv")
try:
    import yaml
except ImportError:
    sys.exit("missing dep: pip install --user pyyaml")

# ──────────────────────────────────────────────────────────────────────────
# .env LOADING — preferred order
# ──────────────────────────────────────────────────────────────────────────
def _load_env():
    candidates = [
        Path.home() / ".hermes" / ".env",
        Path.home() / "code" / "claude-code-proxy" / ".env",
        Path.home() / ".litellm" / ".env",
        Path.home() / ".env",
    ]
    for p in candidates:
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

_load_env()

# ─────────────────────────────────────────────────────────────────────────────
# TUIDS-LLM COLOR SYSTEM — 9 roles, glyphs, belt-and-suspenders dim
# ─────────────────────────────────────────────────────────────────────────────
class C:
    RST       = "\033[0m"
    # Bright (action/critical)
    ERROR     = "\033[1;31m"
    WARN      = "\033[1;33m"
    SUCCESS   = "\033[1;32m"
    INFO      = "\033[1;36m"
    METRICS   = "\033[1;34m"
    ACCENT    = "\033[1;35m"
    # Normal
    ERROR_N   = "\033[31m"
    WARN_N    = "\033[33m"
    SUCCESS_N = "\033[32m"
    INFO_N    = "\033[36m"
    METRICS_N = "\033[34m"
    # Dim (belt-and-suspenders: dim attr + explicit darker code)
    ERROR_D   = "\033[2;31m"
    WARN_D    = "\033[2;33m"
    SUCCESS_D = "\033[2;32m"
    INFO_D    = "\033[2;36m"
    METRICS_D = "\033[2;34m"
    # Structural
    PRIMARY   = "\033[97m"
    SECONDARY = "\033[37m"
    META      = "\033[2;90m"
    # ── Benchmark tier colors (semantic: color by coding benchmark quality) ──
    # S-tier: Orange — frontier performance
    BENCH_S    = "\033[38;5;208m"   # orange
    # A-tier: Bright green — strong open-weight
    BENCH_A    = "\033[1;32m"       # bright green
    # B-tier: Cyan — capable production
    BENCH_B    = "\033[38;5;51m"    # cyan
    # C-tier: Gray — basic
    BENCH_C    = "\033[38;5;145m"   # light gray
    # No data: Dim gray
    BENCH_NONE = "\033[2;90m"       # dark gray
    # Slot delta: winner (bright green), candidate (light purple), edge (yellow)
    SLOT_WIN      = "\033[1;92m"   # bright green
    SLOT_CAND     = "\033[38;5;141m" # light purple/magenta
    SLOT_EDGE     = "\033[38;5;221m" # light yellow
    # Budget tier (OCGo): excellent (green), good (cyan), moderate (yellow), expensive (orange)
    BUDGET_EXCELLENT = "\033[1;92m"
    BUDGET_GOOD     = "\033[38;5;51m"
    BUDGET_MODERATE = "\033[38;5;221m"
    BUDGET_EXPENSIVE = "\033[38;5;208m"
    # Glyphs
    CHECK   = "✓"
    CROSS   = "✗"
    TRI     = "⚠"
    ARROW   = "→"
    DIAMOND = "◆"
    DOT     = "·"
    BULLET  = "●"
    HRULE   = "─"

# Disable color when piped or NO_COLOR set
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    for attr in dir(C):
        if attr.startswith("_") or attr in ("CHECK","CROSS","TRI","ARROW","DIAMOND","DOT","BULLET","HRULE"):
            continue
        if isinstance(getattr(C, attr), str) and getattr(C, attr).startswith("\033"):
            setattr(C, attr, "")

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# ──────────────────────────────────────────────────────────────────────────
# CONFIG PATHS
# ──────────────────────────────────────────────────────────────────────────
CONFIG_DIR = Path.home() / ".config" / "model-scan"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
AA_CACHE       = CONFIG_DIR / "aa_cache.json"
BAD_MODELS     = CONFIG_DIR / "bad_models.json"
RESULTS_FILE   = CONFIG_DIR / "results.json"
DATABASE_FILE  = CONFIG_DIR / "model_scan.db"
TIERS_FILE     = CONFIG_DIR / "tiers.yaml"
SLOTS_FILE     = CONFIG_DIR / "slot_definitions.yaml"

HERMES_CONFIG  = Path.home() / ".hermes" / "config.yaml"
PROXY_ENV      = Path.home() / "code" / "claude-code-proxy" / ".env"
LITELLM_CFG    = Path.home() / ".litellm" / "hermes-gateway.yaml"

AA_API_URL     = "https://artificialanalysis.ai/api/v2/data/llms/models"
AA_TTL_DAYS    = 7

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE — SQLite for historical analytics
# ─────────────────────────────────────────────────────────────────────────────
def _init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(str(DATABASE_FILE))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            scan_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at    TEXT    NOT NULL,
            duration_s    REAL,
            aa_provenance TEXT,
            prov_counts   TEXT,
            model_count   INTEGER,
            healthy       INTEGER,
            degraded      INTEGER,
            failed        INTEGER,
            skipped       INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS models (
            model_pk    INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id     INTEGER,
            provider    TEXT,
            model_id    TEXT,
            api_model   TEXT,
            accessible  INTEGER,
            tps         REAL,
            latency_s   REAL,
            reliability REAL,
            has_tools   INTEGER,
            has_vision  INTEGER,
            ai_index    INTEGER,
            ai_coding   INTEGER,
            ai_math     INTEGER,
            price_blended REAL,
            tier        TEXT,
            composite   REAL,
            arch        TEXT,
            total_b     REAL,
            active_b    REAL,
            http_status INTEGER,
            fail_class  TEXT,
            aa_provenance TEXT,
            scanned_at  TEXT,
            FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS slot_fitness (
            model_pk    INTEGER PRIMARY KEY AUTOINCREMENT,
            model_fk    INTEGER,
            scan_id     INTEGER,
            slot_id     TEXT,
            fitness     REAL,
            FOREIGN KEY (model_fk) REFERENCES models(model_pk),
            FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incumbents (
            incumbent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id      INTEGER,
            slot_id      TEXT,
            provider     TEXT,
            model_id     TEXT,
            status       TEXT,
            latency_s    REAL,
            tps          REAL,
            swap_reason  TEXT,
            FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_models_scan ON models(scan_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_models_tier ON models(tier)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_models_accessible ON models(accessible)")
    # Add benchmark + OCGo budget columns if not exists
    for col, coltype in [
        ("benchmark_swe_verified", "REAL"),
        ("ocgo_budget_score", "REAL"),
        ("ocgo_budget_tier", "TEXT"),
    ]:
        try:
            # Check if column exists before ALTER TABLE
            cur = conn.execute(f"PRAGMA table_info(models)")
            existing = {r[1] for r in cur.fetchall()}
            if col not in existing:
                conn.execute(f"ALTER TABLE models ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass  # table might not exist yet on first run (created above)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_slot_fitness_scan ON slot_fitness(scan_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_slot_fitness_slot ON slot_fitness(slot_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_incumbents_scan ON incumbents(scan_id)")
    conn.commit()
    conn.close()

def _db_save_run(dossiers: list, duration: float, aa_provenance: str,
                 prov_counts: dict, hermes_slots: dict, proxy_tiers: dict,
                 healthy: int, degraded: int, failed: int, permanent_skips: int):
    """Save a completed scan run to SQLite."""
    try:
        _init_db()
        conn = sqlite3.connect(str(DATABASE_FILE))
        cur = conn.cursor()

        now = datetime.now(timezone.utc).isoformat()
        cur.execute("""
            INSERT INTO scans (scanned_at, duration_s, aa_provenance, prov_counts,
                               model_count, healthy, degraded, failed, skipped)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, duration, aa_provenance, json.dumps(prov_counts),
              len(dossiers), healthy, degraded, failed, permanent_skips))
        scan_id = cur.lastrowid

        pk_map = {}  # model_pk for each dossier index
        for i, d in enumerate(dossiers):
            cur.execute("""
                INSERT INTO models (scan_id, provider, model_id, api_model, accessible,
                                    tps, latency_s, reliability, has_tools, has_vision,
                                    ai_index, ai_coding, ai_math, price_blended, tier,
                                    composite, arch, total_b, active_b, http_status,
                                    fail_class, aa_provenance, scanned_at,
                                    benchmark_swe_verified, ocgo_budget_score, ocgo_budget_tier)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (scan_id, d.provider, d.model, d.api_model, int(d.accessible),
                  d.tps, d.latency_s, d.reliability, int(d.has_tools),
                  int(d.has_vision_capability), d.ai_index, d.ai_coding, d.ai_math,
                  d.price_blended, d.tier, d.composite, d.arch,
                  d.total_b, d.active_b, d.http_status, d.fail_class,
                  getattr(d, 'aa_provenance', ''), now,
                  d.benchmark_swe_verified, d.ocgo_budget_score, d.ocgo_budget_tier))
            pk_map[i] = cur.lastrowid

        for i, d in enumerate(dossiers):
            model_pk = pk_map.get(i)
            if model_pk:
                for slot_id, fitness in d.slot_fitness.items():
                    if fitness > 0:
                        cur.execute("""
                            INSERT INTO slot_fitness (model_fk, scan_id, slot_id, fitness)
                            VALUES (?, ?, ?, ?)
                        """, (model_pk, scan_id, slot_id, fitness))

        if hermes_slots:
            for slot_id, incumbent in hermes_slots.items():
                incumbent_model = incumbent if isinstance(incumbent, str) else ""
                status = "active"
                lat = tps_v = ""
                swap_reason = ""
                for d in dossiers:
                    if d.model == incumbent_model or d.api_model == incumbent_model:
                        lat = d.latency_s
                        tps_v = d.tps
                        if not d.accessible:
                            status = "broken"
                            swap_reason = d.fail_class or "not accessible"
                        break
                else:
                    status = "unknown"
                    swap_reason = "not in scan results"
                cur.execute("""
                    INSERT INTO incumbents (scan_id, slot_id, provider, model_id,
                                           status, latency_s, tps, swap_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (scan_id, slot_id, "", incumbent_model, status, lat, tps_v, swap_reason))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  {C.WARN}{C.TRI} DB save failed: {e}{C.RST}", file=sys.stderr)

    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  {C.WARN}{C.TRI} DB save failed: {e}{C.RST}", file=sys.stderr)

# ──────────────────────────────────────────────────────────────────────────
# DEFAULT TIER BOUNDARIES (Ice-ninja's anchor: minimax-2.7=A, GLM-5.1/DeepSeek-V4-Pro=S)
# ──────────────────────────────────────────────────────────────────────────
DEFAULT_TIERS = {
    "anchors": {
        "S": "GLM-5.1 / DeepSeek-V4-Pro intelligence level",
        "A": "MiniMax-M2.7 intelligence level",
    },
    "thresholds": {
        # AA Intelligence Index thresholds for each tier
        "S": 65,   # top frontier open-weight reasoning
        "A": 55,   # MiniMax-M2.7 / Kimi-K2-Thinking class
        "B": 40,   # solid generalists (gpt-oss-120b, Llama-3.3-70b)
        "C": 15,   # functional but lower-quality / specialized
    },
    "composite_weights": {
        "ai_intelligence": 0.45,
        "ai_coding":       0.20,
        "latency_inv":     0.15,  # (1 / latency_seconds), capped
        "reliability":     0.15,
        "moe_efficiency":  0.05,
    },
}

# ──────────────────────────────────────────────────────────────────────────
# DEFAULT HERMES SLOT DEFINITIONS (Ice-ninja's R1-R12 schema)
# ──────────────────────────────────────────────────────────────────────────
DEFAULT_SLOTS = {
    "R1_primary": {
        "label": "primary",
        "needs_tools": False,   # most models handle basic tool calls; verify separately
        "needs_vision": False,
        "min_ai": 45,
        "min_tps": 10,          # lowered: allow 10-15 tps reasoning models
        "max_latency_s": 5.0,   # widened: allow slower reasoning models
        "min_ctx_k": 64,
        # No arch bonus: coding quality is determined by benchmark intelligence, not arch type
        # Speed is normalized by tps/60 so fast small models don't dominate quality slots
        "weight_intelligence": 0.90,  # benchmark quality is primary
        "weight_speed": 0.10,          # throughput matters less for quality slots
        "weight_reliability": 0.00,    # all scanned models have ~100% reliability
    },
    "R6_compression": {
        "label": "compression",
        "needs_tools": False,
        "needs_vision": False,
        "min_ai": 25,
        "min_tps": 30,       # SPEED: 30+ tps for fast compression
        "max_latency_s": 5.0,
        "min_ctx_k": 64,
        "preferred_arch": ["MoE", "MoE-hybrid-mamba", "MoE-reasoning", "dense"],
        "weight_intelligence": 0.20,  # quality matters less for compression
        "weight_speed": 0.55,           # throughput is king
        "weight_reliability": 0.25,
    },
    "R7_vision": {
        "label": "vision",
        "needs_vision": True,
        "needs_tools": False,
        "min_ai": 20,
        "min_tps": 5,        # VL models are slower — lower threshold
        "max_latency_s": 5.0,
        "min_ctx_k": 64,
        "preferred_arch": ["MoE-multimodal", "dense-multimodal"],
        "weight_intelligence": 0.45,
        "weight_speed": 0.25,
        "weight_reliability": 0.30,
    },
    "R8_web_extract": {
        "label": "web_extract",
        "needs_tools": False,
        "needs_vision": False,
        "min_ai": 40,       # HIGHER: coding benchmark quality matters
        "min_tps": 15,
        "max_latency_s": 3.0,
        "min_ctx_k": 64,
        "preferred_arch": ["MoE", "MoE-hybrid-mamba", "MoE-reasoning", "dense"],
        "weight_intelligence": 0.45,  # quality extraction >> raw speed
        "weight_speed": 0.30,
        "weight_reliability": 0.25,
    },
    "R9_session_search": {
        "label": "session_search",
        "needs_tools": False,
        "needs_vision": False,
        "min_ai": 35,       # HIGHER: good summarization quality
        "min_tps": 20,
        "max_latency_s": 3.0,
        "min_ctx_k": 32,
        "preferred_arch": ["MoE", "MoE-hybrid-mamba", "MoE-reasoning", "dense"],
        "weight_intelligence": 0.40,  # quality + speed balanced
        "weight_speed": 0.35,
        "weight_reliability": 0.25,
    },
    "R10_approval": {
        "label": "approval",
        "needs_tools": False,
        "needs_vision": False,
        "min_ai": 30,
        "min_tps": 20,
        "max_latency_s": 2.0,
        "min_ctx_k": 8,
        "preferred_arch": ["MoE", "MoE-hybrid-mamba", "dense"],
        "weight_intelligence": 0.40,
        "weight_speed": 0.35,
        "weight_reliability": 0.25,
    },
    "R11_flush_memories": {
        "label": "flush_memories",
        "needs_tools": False,
        "needs_vision": False,
        "min_ai": 30,
        "min_tps": 20,
        "max_latency_s": 3.0,
        "min_ctx_k": 32,
        "preferred_arch": ["MoE", "MoE-hybrid-mamba", "dense"],
        "weight_intelligence": 0.40,
        "weight_speed": 0.35,
        "weight_reliability": 0.25,
    },
    "R12_delegation": {
        "label": "delegation",
        "needs_tools": True,
        "needs_vision": False,
        "min_ai": 45,
        "min_tps": 20,
        "max_latency_s": 3.0,
        "min_ctx_k": 64,
        "preferred_arch": ["MoE", "MoE-hybrid-mamba", "MoE-reasoning", "dense"],
        "weight_intelligence": 0.50,
        "weight_speed": 0.25,
        "weight_reliability": 0.25,
    },
    "R_mcp": {
        "label": "mcp_orchestration",
        "needs_tools": True,
        "min_ai": 50,
        "min_tps": 20,
        "max_latency_s": 2.5,
        "min_ctx_k": 128,
        "weight_intelligence": 0.4,
        "weight_speed": 0.3,
        "weight_reliability": 0.3,
    },
    "R_skills_hub": {
        "label": "skills_hub",
        "needs_tools": False,
        "min_ai": 25,
        "min_tps": 20,
        "max_latency_s": 2.0,
        "min_ctx_k": 32,
        "weight_intelligence": 0.2,
        "weight_speed": 0.55,
        "weight_reliability": 0.25,
    },
}

def load_tiers() -> dict:
    if TIERS_FILE.exists():
        try:
            return yaml.safe_load(TIERS_FILE.read_text()) or DEFAULT_TIERS
        except Exception:
            pass
    TIERS_FILE.write_text(yaml.safe_dump(DEFAULT_TIERS, sort_keys=False))
    return DEFAULT_TIERS

def load_slot_defs() -> dict:
    if SLOTS_FILE.exists():
        try:
            return yaml.safe_load(SLOTS_FILE.read_text()) or DEFAULT_SLOTS
        except Exception:
            pass
    SLOTS_FILE.write_text(yaml.safe_dump(DEFAULT_SLOTS, sort_keys=False))
    return DEFAULT_SLOTS

# ── FREE-MODE WHITELIST ──────────────────────────────────────────────
FREE_WHITELIST_PATH = CONFIG_DIR / "free_model_whitelist.json"

def load_free_whitelist() -> dict:
    """Load the free-model whitelist. Returns dict with known_free_models list."""
    if not FREE_WHITELIST_PATH.exists():
        return {"known_free_models": [], "free_providers": {}}
    try:
        return json.loads(FREE_WHITELIST_PATH.read_text())
    except Exception:
        return {"known_free_models": [], "free_providers": {}}

def refresh_free_whitelist() -> int:
    """Refresh the free-model whitelist by fetching from providers.
    Returns number of free models discovered."""
    import subprocess
    print(f"  Refreshing free-model whitelist...")
    
    whitelist = load_free_whitelist()
    known = set()
    for m in whitelist.get("known_free_models", []):
        known.add((m["model_id"], m.get("provider", "")))
    
    # Fetch from OpenRouter free models
    try:
        import httpx
        r = httpx.get("https://openrouter.ai/api/v1/models", timeout=15)
        if r.status_code == 200:
            for m in r.json().get("data", []):
                mid = m.get("id", "")
                if ":free" in mid or m.get("pricing", {}).get("prompt") == "0":
                    known.add((mid, "openrouter"))
    except Exception:
        pass
    
    # Rebuild whitelist
    new_models = []
    seen = set()
    for mid, prov in sorted(known):
        key = f"{prov}/{mid}"
        if key not in seen:
            seen.add(key)
            new_models.append({"model_id": mid, "provider": prov, "source": "refresh"})
    
    whitelist["known_free_models"] = new_models
    whitelist["refreshed_at"] = datetime.now().isoformat()
    FREE_WHITELIST_PATH.write_text(json.dumps(whitelist, indent=2))
    
    print(f"  ✓ {len(new_models)} free models in whitelist")
    return len(new_models)

def is_model_free(model_id: str, provider: str = "") -> bool:
    """Check if a model is in the free whitelist."""
    whitelist = load_free_whitelist()
    
    # Check by provider + model_id exact
    for m in whitelist.get("known_free_models", []):
        if m["model_id"] == model_id:
            if not provider or not m.get("provider") or m["provider"] == provider:
                return True
    
    # Check suffix rules
    for prov_name, prov_cfg in whitelist.get("free_providers", {}).items():
        if provider and provider != prov_name:
            continue
        stype = prov_cfg.get("type", "")
        if stype == "suffix_match":
            suffix = prov_cfg.get("suffix", "")
            if suffix and model_id.endswith(suffix):
                return True
        elif stype == "all_free":
            return True
    
    # Check free model families
    for family in whitelist.get("free_model_families", []):
        if model_id.lower().startswith(family.lower()):
            # Only if from a free provider
            if provider in ("openrouter", "opencode-zen", "kilo", "ollama-cloud", "groq", "cerebras"):
                return True
    
    return False

def filter_free_models(candidates: list[tuple]) -> list[tuple]:
    """Filter a list of (model_id, pricing_dict) tuples to free models only."""
    whitelist = load_free_whitelist()
    result = []
    for mid, pricing in candidates:
        if is_model_free(mid):
            result.append((mid, pricing))
    return result

# ──────────────────────────────────────────────────────────────────────────
# AA API CLIENT — official endpoint, x-api-key auth
# ──────────────────────────────────────────────────────────────────────────
async def fetch_aa_data(client: httpx.AsyncClient, force: bool = False) -> tuple[dict, str]:
    """Returns (model_lookup, provenance_tag)."""
    api_key = os.environ.get("AA_API_KEY", "").strip()

    # Use cache if fresh
    if not force and AA_CACHE.exists():
        try:
            cached = json.loads(AA_CACHE.read_text())
            scraped_at = datetime.fromisoformat(cached["scraped_at"])
            age = datetime.now(timezone.utc) - scraped_at
            if age < timedelta(days=AA_TTL_DAYS):
                return cached["lookup"], f"cached-{age.days}d"
            elif not api_key:
                # No key but we have stale cache: use it
                return cached["lookup"], f"stale-{age.days}d"
        except Exception:
            pass

    if not api_key:
        return {}, "missing"

    try:
        resp = await client.get(
            AA_API_URL,
            headers={"x-api-key": api_key},
            timeout=20,
        )
        if resp.status_code == 401:
            return {}, "unauthorized"
        if resp.status_code == 429:
            # Use stale cache if available
            if AA_CACHE.exists():
                cached = json.loads(AA_CACHE.read_text())
                return cached["lookup"], "rate-limited"
            return {}, "rate-limited"
        if resp.status_code != 200:
            return {}, f"http-{resp.status_code}"

        data = resp.json().get("data", [])
        lookup = _build_aa_lookup(data)
        AA_CACHE.write_text(json.dumps({
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "lookup": lookup,
            "model_count": len(data),
        }, indent=2))
        return lookup, "fresh"
    except Exception as e:
        if AA_CACHE.exists():
            try:
                cached = json.loads(AA_CACHE.read_text())
                return cached["lookup"], f"error-cached"
            except Exception:
                pass
        return {}, f"error-{type(e).__name__}"

def _build_aa_lookup(aa_data: list) -> dict:
    """Build fuzzy-match lookup from AA API response. Multiple keys point to same record."""
    lookup = {}
    for entry in aa_data:
        slug = (entry.get("slug") or "").lower()
        name = (entry.get("name") or "").lower()
        creator = ((entry.get("model_creator") or {}).get("slug") or "").lower()
        evals = entry.get("evaluations", {})
        record = {
            "id": entry.get("id"),
            "name": entry.get("name"),
            "slug": slug,
            "creator": creator,
            "ai_index": evals.get("artificial_analysis_intelligence_index"),
            "ai_coding": evals.get("artificial_analysis_coding_index"),
            "ai_math": evals.get("artificial_analysis_math_index"),
            "mmlu_pro": evals.get("mmlu_pro"),
            "gpqa": evals.get("gpqa"),
            "livecodebench": evals.get("livecodebench"),
            "scicode": evals.get("scicode"),
            "price_blended": (entry.get("pricing") or {}).get("price_1m_blended_3_to_1"),
            "price_input": (entry.get("pricing") or {}).get("price_1m_input_tokens"),
            "price_output": (entry.get("pricing") or {}).get("price_1m_output_tokens"),
            "median_tps": entry.get("median_output_tokens_per_second"),
            "median_ttft": entry.get("median_time_to_first_token_seconds"),
        }

        # Index under multiple keys for fuzzy matching
        for key in {slug, name.replace(" ", "-"), f"{creator}/{slug}"}:
            if key:
                lookup[key] = record
                # Strip common prefixes/suffixes
                lookup[key.split("/")[-1]] = record
                if key.endswith(":free"):
                    lookup[key[:-5]] = record
        # Strip provider prefix variations
        for prefix in ("openai-", "openrouter-", "anthropic-", "google-", "nvidia-", "qwen-", "meta-"):
            if slug.startswith(prefix):
                lookup[slug[len(prefix):]] = record
    return lookup

def aa_lookup_model(aa_lookup: dict, model_id: str) -> dict:
    """Fuzzy match a model_id against AA records. Tries many normalizations."""
    if not aa_lookup or not model_id:
        return {}
    mid = model_id.lower()
    # Strip common provider prefixes
    for prefix in ("openrouter/", "nvidia/", "groq/", "cerebras/", "openai/",
                   "google/", "anthropic/", "meta/", "moonshotai/", "deepseek-ai/",
                   "minimaxai/", "qwen/", "z-ai/", "mistralai/", "liquid/",
                   "abacusai/", "upstage/", "sarvamai/", "cereb/", "cogito/",
                   "stockmark/", "devstral/", "rnj/", "allam/", "ollama-cloud/",
                   "opencode-go/", "opencode-zen/", "kilo/"):
        if mid.startswith(prefix):
            mid = mid[len(prefix):]
            break
    # Strip suffixes like :free, :preview, -thinking, etc.
    mid = re.sub(r':(free|cloud|preview|thinking|latest|instruct|it|v\d+(?:\.\d+)*|-[a-z]+)$', '', mid)
    # Normalize dashes/spaces
    mid_norm = mid.replace('-', '').replace('_', '').replace(' ', '')

    candidates = [
        mid,
        mid.replace('/', '-'),
        mid.split('/')[-1] if '/' in mid else mid,
    ]
    for c in candidates:
        if c in aa_lookup:
            return aa_lookup[c]
        # Try without version suffixes
        for suf in ('-2024', '-2025', '-2026', '-jan', '-feb', '-mar', '-apr', '-may',
                    '-latest', '-preview', '-thinking', '-non-reasoning', '-instruct', '-it'):
            if c.endswith(suf) and len(c) > len(suf) + 2:
                stripped = c[:-len(suf)]
                if stripped in aa_lookup:
                    return aa_lookup[stripped]
                # Try with dashes to slashes
                slash_stripped = stripped.replace('-', '/')
                if slash_stripped in aa_lookup:
                    return aa_lookup[slash_stripped]

    # Try stripped model ID (provider prefix already removed)
    for c in [mid, mid_norm]:
        for key in aa_lookup:
            key_cmp = key.lower().replace('-', '').replace('_', '').replace(' ', '')
            if c == key_cmp or c in key_cmp or key_cmp in c:
                # Prefer exact-ish matches
                if len(c) > 5 and (c.startswith(key_cmp[:6]) or key_cmp.startswith(c[:6])):
                    return aa_lookup[key]
    return {}

# ──────────────────────────────────────────────────────────────────────────
# HERMES INTEGRATION — extract slot assignments from config files
# ──────────────────────────────────────────────────────────────────────────
def parse_hermes_slots() -> dict[str, str]:
    """Returns {slot_id: model_id_currently_assigned}."""
    slots = {}
    if not HERMES_CONFIG.exists():
        return slots
    try:
        cfg = yaml.safe_load(HERMES_CONFIG.read_text()) or {}
    except Exception:
        return slots

    if (m := cfg.get("model")) and m.get("default"):
        slots["R1_primary"] = m["default"]

    for i, fb in enumerate(cfg.get("fallback_providers") or []):
        if fb.get("model"):
            slots[f"R{2+i}_fallback"] = fb["model"]

    if (d := cfg.get("delegation")) and d.get("model"):
        slots["R12_delegation"] = d["model"]

    aux = cfg.get("auxiliary") or {}
    aux_map = {
        "compression":     "R6_compression",
        "vision":          "R7_vision",
        "web_extract":     "R8_web_extract",
        "session_search":  "R9_session_search",
        "approval":        "R10_approval",
        "flush_memories":  "R11_flush_memories",
        "skills_hub":      "R_skills_hub",
        "mcp":             "R_mcp",
    }
    for aux_key, slot_id in aux_map.items():
        if (a := aux.get(aux_key)) and a.get("model"):
            slots[slot_id] = a["model"]

    if (c := cfg.get("compression")) and c.get("summary_model"):
        slots.setdefault("R6_compression", c["summary_model"])

    return slots

def parse_proxy_tiers() -> dict[str, str]:
    """Returns {tier_label: model_id} from claude-code-proxy .env."""
    tiers = {}
    if not PROXY_ENV.exists():
        return tiers
    for line in PROXY_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k == "BIG_MODEL":
            tiers["proxy_BIG"] = v
        elif k == "MIDDLE_MODEL":
            tiers["proxy_MIDDLE"] = v
        elif k == "SMALL_MODEL":
            tiers["proxy_SMALL"] = v
    return tiers

# ──────────────────────────────────────────────────────────────────────────
# PROVIDER REGISTRY
# ──────────────────────────────────────────────────────────────────────────
PROVIDERS = {
    "openrouter": {
        "base":     "https://openrouter.ai/api/v1",
        "key_env":  "OPENROUTER_API_KEY",
        "abbrev":   "OR",
        "free_only": True,
    },
    "nvidia": {
        "base":     "https://integrate.api.nvidia.com/v1",
        "key_env":  "NVIDIA_API_KEY",
        "abbrev":   "NIM",
    },
    "groq": {
        "base":     "https://api.groq.com/openai/v1",
        "key_env":  "GROQ_API_KEY",
        "abbrev":   "Groq",
    },
    "cerebras": {
        "base":     "https://api.cerebras.ai/v1",
        "key_env":  "CEREBRAS_API_KEY",
        "abbrev":   "Cereb",
    },
    "opencode-go": {
        "base":     "https://opencode.ai/zen/go/v1",
        "key_env":  "OPENCODE_GO_API_KEY",
        "abbrev":   "OCGo",
        "strip_prefix": "opencode-go/",
    },
    "ollama-cloud": {
        "base":     "https://ollama.com/v1",
        "key_env":  "OLLAMA_API_KEY",
        "abbrev":   "OL-c",
        "cloud_only": True,
    },
    "opencode-zen": {
        "base":     "https://opencode.ai/zen/v1",
        "key_env":  "OPENCODE_API_KEY",
        "abbrev":   "OCZn",
        "free_only": True,
    },
    "kilo": {
        "base":     "https://api.kilo.ai/api/gateway",
        "key_env":  "KILO_API_KEY",
        "abbrev":   "Kilo",
        "free_only": True,
    },
    "ollama-local": {
        "base":     "http://localhost:11434/v1",
        "key_env":  None,
        "abbrev":   "OL-l",
        "list_url": "http://localhost:11434/api/tags",
    },
    "venice": {
        "base":     "https://api.venice.ai/api/v1",
        "key_env":  "VENICE_API_KEY",
        "abbrev":   "Ven",
        "auth_style": "X-API-Key",  # Venice uses X-API-Key header
    },
}

# ──────────────────────────────────────────────────────────────────────────
# BAD-MODEL TRACKING — class-aware, rolling window
# ──────────────────────────────────────────────────────────────────────────
PERMANENT_FAIL_CLASSES = {"auth_error", "empty_response", "schema_error"}
TRANSIENT_FAIL_CLASSES = {"rate_limit", "timeout"}
BAD_THRESHOLD = 5
ROLLING_WINDOW_DAYS = 7

def load_bad() -> dict:
    if BAD_MODELS.exists():
        try:
            raw = json.loads(BAD_MODELS.read_text())
            if isinstance(raw, dict):
                # Migrate legacy plain-int values to new dict format
                migrated = False
                for k, v in raw.items():
                    if isinstance(v, int) and not isinstance(v, bool):
                        raw[k] = {"failures": []}
                        migrated = True
                    elif not isinstance(v, dict):
                        raw[k] = {"failures": []}
                        migrated = True
                if migrated:
                    save_bad(raw)
                return raw
        except Exception:
            pass
    return {}

def save_bad(bad: dict):
    # Ensure no legacy plain-int values are saved
    cleaned = {}
    for k, v in bad.items():
        if isinstance(v, int) and not isinstance(v, bool):
            cleaned[k] = {"failures": []}
        elif isinstance(v, dict):
            cleaned[k] = v
    BAD_MODELS.write_text(json.dumps(cleaned, indent=2))

def is_permanently_skipped(bad: dict, key: str) -> tuple[bool, str]:
    entry = bad.get(key)
    if entry is None:
        return False, ""
    # Handle legacy format: entry was a plain int (failure count)
    if isinstance(entry, int):
        if entry >= BAD_THRESHOLD:
            return True, "legacy_skip"
        return False, ""
    if not isinstance(entry, dict):
        return False, ""
    cutoff = datetime.now(timezone.utc) - timedelta(days=ROLLING_WINDOW_DAYS)
    recent = [
        f for f in entry.get("failures", [])
        if datetime.fromisoformat(f["at"]) > cutoff
        and f["class"] in PERMANENT_FAIL_CLASSES
    ]
    if len(recent) >= BAD_THRESHOLD:
        last_class = recent[-1]["class"]
        return True, last_class
    return False, ""

def record_failure(bad: dict, key: str, fail_class: str):
    entry = bad.get(key)
    # Migrate legacy plain-int entries to new dict format
    if entry is None or isinstance(entry, int):
        bad[key] = {"failures": []}
        entry = bad[key]
    elif not isinstance(entry, dict):
        bad[key] = {"failures": []}
        entry = bad[key]
    entry["failures"].append({
        "class": fail_class,
        "at": datetime.now(timezone.utc).isoformat(),
    })
    # Trim to last 30 entries to keep file small
    entry["failures"] = entry["failures"][-30:]

def record_success(bad: dict, key: str):
    """A successful probe clears transient failures from the rolling window."""
    entry = bad.get(key)
    if entry is None:
        return
    # Handle legacy format
    if isinstance(entry, int):
        bad[key] = {"failures": []}
        return
    if not isinstance(entry, dict):
        return
    bad[key]["failures"] = [
        f for f in entry["failures"]
        if f["class"] in PERMANENT_FAIL_CLASSES
    ]

def rehabilitate(model_key: str):
    bad = load_bad()
    if model_key in bad:
        del bad[model_key]
        save_bad(bad)
        return True
    return False

# ──────────────────────────────────────────────────────────────────────────
# LOCAL ARCHITECTURE/CLASS REFERENCE (fallback when AA missing)
# ──────────────────────────────────────────────────────────────────────────
ARCH_REFS = [
    # Nemotron
    (r"nemotron-3-super.*120b.*a12b", "MoE-hybrid-mamba", 120, 12),
    (r"nemotron.*nano.*30b.*a3b", "MoE", 30, 3),
    (r"nemotron.*nano.*9b", "dense", 9, 9),
    (r"nemotron.*nano.*12b.*vl", "dense-multimodal", 12, 12),
    # GLM / Zhipu
    (r"glm-5\.1", "MoE-reasoning", 355, 32),
    (r"glm-5(?!\.)", "MoE-reasoning", 744, 40),
    (r"glm-4\.5-air", "MoE", 106, 12),
    (r"glm-4\.7", "MoE-reasoning", 355, 32),
    # Kimi / moonshot
    (r"kimi-k2\.5|kimi-k2-5", "MoE-multimodal", 1000, 32),
    (r"kimi-k2-thinking", "MoE-reasoning", 1000, 32),
    (r"kimi-k2(?!\d)|kimi-k2\.6", "MoE", 1000, 32),
    # MiniMax
    (r"minimax-m2\.7", "MoE-reasoning", 229, 10),
    (r"minimax-m2\.5", "MoE", 229, 10),
    # Qwen
    (r"qwen3-coder.*480b", "MoE", 480, 35),
    (r"qwen3-next.*80b.*a3b|qwen3-next.*80b-a3b", "MoE", 80, 3),
    (r"qwen3-next|qwen3-coder-next", "MoE", 80, 3),
    (r"qwen3\.5|qwen3-5", "MoE-multimodal", 122, 10),
    (r"qwen3-32b|qwen3\.3-32b", "dense", 32, 32),
    (r"qwen2\.5-coder.*32b", "dense", 32, 32),
    # DeepSeek
    (r"deepseek-v[34](?!\d)|deepseek-v4-pro", "MoE", 671, 37),
    (r"deepseek-v4-flash|deepseek-v4(?!\d)", "MoE", 671, 37),
    # GPT-OSS
    (r"gpt-oss-120b", "MoE", 117, 5),
    (r"gpt-oss-20b", "MoE", 21, 3),
    # Trinity
    (r"trinity-large", "MoE", 400, 50),
    # Llama
    (r"llama-?3\.3-70b", "dense", 70, 70),
    (r"llama-?3\.2-3b", "dense", 3, 3),
    (r"llama-?3\.2-1b", "dense", 1, 1),
    (r"llama-?4-scout", "MoE-multimodal", 109, 17),
    (r"llama-?4-maverick", "MoE-multimodal", 400, 17),
    (r"llama-?4(?!\d)", "MoE-multimodal", 400, 17),
    # Gemma
    (r"gemma-?4", "dense-multimodal", 31, 31),
    (r"gemma-?3", "dense-multimodal", 12, 12),
    # Devstral
    (r"devstral.*24b", "dense", 24, 24),
    (r"devstral.*123b", "dense", 123, 123),
    # Ling
    (r"ling-2\.6-flash", "MoE", 80, 8),
    (r"ling-2\.6-1t", "MoE", 1000, 50),
    # Llama 3.1 / 3.2 base variants (NIM/cerebras)
    (r"llama-3\.1-8b", "dense", 8, 8),
    (r"llama-3\.1-70b", "dense", 70, 70),
    (r"llama-3\.2-11b", "dense", 11, 11),
    (r"llama-3\.2-90b", "dense", 90, 90),
    # Mixtral
    (r"mixtral-8x22b", "MoE", 176, 22),
    (r"mixtral-8x7b", "MoE", 56, 7),
    # Mistral / Ministral
    (r"mistral-nemotron", "dense", 47, 47),
    (r"mistral-small-4.*119b", "dense", 119, 119),
    (r"mistral-medium-3.*128b", "dense", 128, 128),
    (r"ministral-14b", "dense", 14, 14),
    (r"ministral-8b|ministral-3.*8b", "dense", 8, 8),
    (r"ministral-3b", "dense", 3, 3),
    # Nemotron guard / safety
    (r"nemotron.*guard.*8b", "dense", 8, 8),
    (r"nemotron.*content-safety.*4b", "dense", 4, 4),
    # Cogito
    (r"cogito-2.*671b", "dense", 671, 671),
    (r"cogito-2\.1", "dense", 671, 671),
    # Allam
    (r"allam.*7b", "dense", 7, 7),
    # Phi
    (r"phi-4-mini", "dense", 4, 4),
    (r"phi-4-multimodal", "dense-multimodal", 4, 4),
    # Gemma-n
    (r"gemma-3n-e[24]b", "dense", 4, 4),
    # Liquid LFM
    (r"lfm-2\.5.*1\.2b", "dense", 1.2, 1.2),
    # RNJ
    (r"rnj-1.*8b", "dense", 8, 8),
    # Riva translate
    (r"riva-translate.*4b", "dense", 4, 4),
    # Gliner PII
    (r"gliner-pii", "dense", 3, 3),
]

VISION_PATTERNS = re.compile(r"vl|vision|multimodal|gemma-?4|llama-4|qwen3\.5|kimi-k2\.5|gemini", re.I)

def infer_arch(model_id: str) -> tuple[str, float, float]:
    """Returns (arch, total_b, active_b)."""
    mid = model_id.lower()
    for pat, arch, total, active in ARCH_REFS:
        if re.search(pat, mid):
            return arch, total, active
    # Fallback: parse from name
    if m := re.search(r"(\d+)x(\d+(?:\.\d+)?)b", mid):
        return "MoE", float(m.group(1)) * float(m.group(2)), float(m.group(2))
    if m := re.search(r"a(\d+(?:\.\d+)?)b", mid):
        active = float(m.group(1))
        if t := re.search(r"(\d+(?:\.\d+)?)b-?a", mid):
            return "MoE", float(t.group(1)), active
        return "MoE", active * 10, active
    if m := re.search(r"(\d+(?:\.\d+)?)b", mid):
        size = float(m.group(1))
        return "dense", size, size
    return "unknown", 0.0, 0.0

def has_vision(model_id: str) -> bool:
    return bool(VISION_PATTERNS.search(model_id))

# ──────────────────────────────────────────────────────────────────────────
# DOSSIER — unified per-model record
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Dossier:
    provider: str
    model: str
    api_model: str          # what to send to the API
    # Live probe data
    accessible: bool = False
    latency_s: float = 0.0
    tps: float = 0.0
    reliability: float = 0.0
    has_tools: bool = False
    fail_class: str = ""
    http_status: int = 0
    # AA data
    ai_index: float | None = None
    ai_coding: float | None = None
    ai_math: float | None = None
    aa_provenance: str = "missing"
    # Architecture
    arch: str = "unknown"
    total_b: float = 0.0
    active_b: float = 0.0
    has_vision_capability: bool = False
    # Benchmark data
    benchmark_swe_verified: float | None = None
    ocgo_budget_score: float | None = None
    ocgo_budget_tier: str = "unknown"
    # Pricing / context (from AA or models.dev)
    price_blended: float | None = None
    ctx_k: int | None = None
    # Computed
    tier: str = "—"
    composite: float = 0.0
    qualified_slots: list[str] = field(default_factory=list)
    slot_fitness: dict[str, float] = field(default_factory=dict)
    # Annotations
    is_incumbent_for: list[str] = field(default_factory=list)
    usage_count: int = 0

# ──────────────────────────────────────────────────────────────────────────
# PROBING
# ──────────────────────────────────────────────────────────────────────────
async def list_models(client: httpx.AsyncClient, prov: str, cfg: dict) -> list[tuple[str, dict]]:
    if prov == "ollama-local":
        try:
            r = await client.get(cfg["list_url"], timeout=5)
            if r.status_code != 200:
                return []
            return [(m["name"], {}) for m in r.json().get("models", [])]
        except Exception:
            return []

    key_var = cfg.get("key_env")
    api_key = os.environ.get(key_var, "") if key_var else ""
    if key_var and not api_key:
        return []

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    if cfg.get("auth_style") == "X-API-Key":
        headers = {"X-API-Key": api_key}
    try:
        r = await client.get(f"{cfg['base']}/models", headers=headers, timeout=20)
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("data") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []
    except Exception:
        return []

    out = []
    for m in items:
        if not isinstance(m, dict):
            continue
        mid = m.get("id") or m.get("name")
        if not mid:
            continue
        pricing = m.get("pricing", {}) or {}
        if prov == "openrouter" and cfg.get("free_only"):
            try:
                free = mid.endswith(":free") or float(pricing.get("prompt", "1")) == 0.0
            except Exception:
                free = mid.endswith(":free")
            if not free:
                continue
        if prov == "opencode-zen" and cfg.get("free_only"):
            # OpenCode Zen free models have -free suffix (deepseek-v4-flash-free)
            try:
                free = mid.endswith("-free") or float(pricing.get("prompt", "1")) == 0.0
            except Exception:
                free = mid.endswith("-free")
            if not free:
                continue
        if prov == "kilo" and cfg.get("free_only"):
            # Kilo free models have :free suffix (deepseek/deepseek-v4-flash:free)
            try:
                free = mid.endswith(":free") or float(pricing.get("prompt", "1")) == 0.0
            except Exception:
                free = mid.endswith(":free")
            if not free:
                continue
        if prov == "ollama-cloud" and cfg.get("cloud_only"):
            cloud_prefixes = ("deepseek-v4", "glm-5", "kimi-k2", "minimax-m2", "nemotron-3",
                             "qwen3-next", "qwen3-coder-next", "qwen3.5",
                             "gemini-3-flash", "deepseek-v", "devstral",
                             "gemma4", "ministral-3", "cogito-2", "rnj-")
            if not (":cloud" in mid or any(mid.startswith(p) for p in cloud_prefixes)):
                continue
        out.append((mid, pricing))
    return out

async def probe_one(client: httpx.AsyncClient, prov: str, model_id: str,
                    api_model: str, cfg: dict) -> dict:
    """Single-shot probe. Returns failure class on error.

    OpenCode Go MiniMax models use /v1/messages (Anthropic format).
    Other OCGo models use /v1/chat/completions (OpenAI format).
    Try primary endpoint; on 422/400 try alternate if applicable.
    """
    api_key = os.environ.get(cfg.get("key_env") or "", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        if cfg.get("auth_style") == "X-API-Key":
            headers["X-API-Key"] = api_key
        else:
            headers["Authorization"] = f"Bearer {api_key}"

    body_oa = {  # OpenAI-format body
        "model": api_model,
        "messages": [{"role": "user", "content": "reply pong"}],
        "max_tokens": 32,
        "temperature": 0.0,
    }
    body_an = {  # Anthropic-format body
        "model": api_model,
        "messages": [{"role": "user", "content": "reply pong"}],
        "max_tokens": 32,
    }

    # Determine primary/secondary endpoints per provider
    mid_lower = model_id.lower()
    prov_is_ocgo = (prov == "opencode-go")
    is_anthropic_model = bool(OCGO_ANTHROPIC_MODELS and
                             any(p in mid_lower for p in OCGO_ANTHROPIC_MODELS))

    if prov_is_ocgo and is_anthropic_model:
        primary_endpoint = "messages"
        secondary_endpoint = "chat/completions"
    else:
        primary_endpoint = "chat/completions"
        secondary_endpoint = None

    def _parse_response(r: httpx.Response, elapsed: float) -> dict:
        """Parse successful response into result dict."""
        try:
            data = r.json()
        except Exception:
            return {"ok": False, "fail_class": "schema_error", "elapsed": elapsed, "status": r.status_code}
        # Try OpenAI format
        choices = data.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            usage = data.get("usage") or {}
            content = (msg.get("content") or "").strip()
            prompt_tokens = usage.get("prompt_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            if not content and (prompt_tokens > 0 or total_tokens > 0):
                tok = usage.get("completion_tokens") or max(1, total_tokens - prompt_tokens)
                tps = tok / elapsed if elapsed > 0 else 0
                return {"ok": True, "elapsed": elapsed, "tps": tps, "tokens": tok, "status": 200, "content": content}
            if not content:
                return {"ok": False, "fail_class": "empty_response", "elapsed": elapsed, "status": 200}
            tok = usage.get("completion_tokens") or max(1, len(content.split()))
            tps = tok / elapsed if elapsed > 0 else 0
            return {"ok": True, "elapsed": elapsed, "tps": tps, "tokens": tok, "status": 200, "content": content}
        # Try Anthropic format
        content = (data.get("content") or [{}])[0].get("text", "").strip()
        usage = data.get("usage") or {}
        if not content and usage:
            prompt_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + output_tokens)
            tok = output_tokens or max(1, total_tokens - prompt_tokens)
            tps = tok / elapsed if elapsed > 0 else 0
            return {"ok": True, "elapsed": elapsed, "tps": tps, "tokens": tok, "status": 200, "content": content}
        if not content:
            return {"ok": False, "fail_class": "empty_response", "elapsed": elapsed, "status": 200}
        tok = output_tokens if (output_tokens := usage.get("output_tokens")) else max(1, len(content.split()))
        tps = tok / elapsed if elapsed > 0 else 0
        return {"ok": True, "elapsed": elapsed, "tps": tps, "tokens": tok, "status": 200, "content": content}

    t0 = time.perf_counter()

    # Primary endpoint
    try:
        if primary_endpoint == "messages":
            r = await client.post(
                f"{cfg['base']}/messages",
                json=body_an, headers=headers, timeout=20,
            )
        else:
            r = await client.post(
                f"{cfg['base']}/chat/completions",
                json=body_oa, headers=headers, timeout=20,
            )
    except httpx.TimeoutException:
        return {"ok": False, "fail_class": "timeout", "elapsed": time.perf_counter() - t0}
    except Exception:
        return {"ok": False, "fail_class": "network", "elapsed": time.perf_counter() - t0}

    elapsed = time.perf_counter() - t0

    # Success on primary
    if r.status_code == 200:
        result = _parse_response(r, elapsed)
        if result.get("ok"):
            return result

    # Transient errors — don't retry
    if r.status_code in (401, 403):
        return {"ok": False, "fail_class": "auth_error", "elapsed": elapsed, "status": r.status_code}
    if r.status_code == 429:
        return {"ok": False, "fail_class": "rate_limit", "elapsed": elapsed, "status": r.status_code}

    # Format error (422/400) at OCGo — try alternate endpoint
    if secondary_endpoint and r.status_code in (400, 422):
        try:
            if secondary_endpoint == "messages":
                r = await client.post(
                    f"{cfg['base']}/messages",
                    json=body_an, headers=headers, timeout=20,
                )
            else:
                r = await client.post(
                    f"{cfg['base']}/chat/completions",
                    json=body_oa, headers=headers, timeout=20,
                )
        except httpx.TimeoutException:
            return {"ok": False, "fail_class": "timeout", "elapsed": time.perf_counter() - t0}
        except Exception:
            return {"ok": False, "fail_class": "network", "elapsed": time.perf_counter() - t0}

        if r.status_code == 200:
            result = _parse_response(r, elapsed)
            if result.get("ok"):
                return result

    # Final error
    if r.status_code >= 400:
        return {"ok": False, "fail_class": f"http_{r.status_code}", "elapsed": elapsed, "status": r.status_code}

    # Shouldn't reach here
    return {"ok": False, "fail_class": "unknown", "elapsed": elapsed, "status": r.status_code}

async def probe_tools(client: httpx.AsyncClient, prov: str, model_id: str,
                      api_model: str, cfg: dict) -> bool:
    api_key = os.environ.get(cfg.get("key_env") or "", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        if cfg.get("auth_style") == "X-API-Key":
            headers["X-API-Key"] = api_key
        else:
            headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": api_model,
        "messages": [{"role": "user", "content": "Use the calc tool to compute: what is 157 + 289? Respond with the result."}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "calc",
                "description": "Mathematical calculator",
                "parameters": {
                    "type": "object",
                    "properties": {"expr": {"type": "string"}},
                    "required": ["expr"],
                },
            },
        }],
        "max_tokens": 64,
        "temperature": 0.0,
    }
    try:
        r = await client.post(
            f"{cfg['base']}/chat/completions",
            json=body, headers=headers, timeout=15,
        )
        if r.status_code >= 400:
            return False
        data = r.json()
        ch = data.get("choices") or []
        if not ch:
            return False
        msg = ch[0].get("message") or {}
        fr = ch[0].get("finish_reason", "")
        # Models that produce tool_calls OR correct finish_reason are tool-capable
        # Thinking models put output in reasoning_content, not content
        return bool(
            msg.get("tool_calls")
            or fr in ("tool_calls", "function_call", "tool_role")
            or (fr == "stop" and (msg.get("content", "") or msg.get("reasoning_content") or "").strip())
        )
    except Exception:
        return False

def api_model_for(prov: str, model_id: str) -> str:
    """Some providers want bare model names without slashes."""
    if prov in ("groq", "cerebras") and "/" in model_id:
        return model_id.split("/")[-1]
    if prov in ("opencode-go",) and "/" in model_id:
        return model_id.split("/")[-1]
    return model_id

# ──────────────────────────────────────────────────────────────────────────
# BENCHMARK DATA — verified scores from SWE-bench, Terminal-Bench, etc.
# ──────────────────────────────────────────────────────────────────────────
BENCHMARKS_FILE = CONFIG_DIR / "benchmarks.json"

# MiniMax models at OpenCode Go use Anthropic format (/v1/messages), not OpenAI
OCGO_ANTHROPIC_MODELS = {"minimax-m2.7", "minimax-m2.5", "minimax-m2", "mimo-v2", "mimo-v2.5", "mimo-v2.5-pro", "mimo-v2-pro", "mimo-v2-omni"}

def _load_benchmarks() -> dict:
    """Load cached benchmark data from benchmarks.json."""
    if not BENCHMARKS_FILE.exists():
        import sys as _sys
        print(f"{C.WARN}{C.TRI} benchmarks.json not found at {BENCHMARKS_FILE}. Run a scan to generate it.{C.RST}", file=_sys.stderr)
        return {}
    try:
        return json.loads(BENCHMARKS_FILE.read_text())
    except Exception as e:
        import sys as _sys
        print(f"{C.WARN}{C.TRI} Failed to parse benchmarks.json: {e}{C.RST}", file=_sys.stderr)
        return {}

def _match_benchmark(model_id: str, benchmarks: dict) -> float | None:
    """Find benchmark score for a model_id. Returns SWE-bench Verified % or None."""
    mid = model_id.lower().replace("/", "-").replace("_", "-")

    # Try each benchmark source in priority order
    for source in ("swe_verified", "swe_pro_seal"):
        scores = benchmarks.get(source, {})
        if not isinstance(scores, dict):
            continue
        # Direct match
        if mid in scores:
            return scores[mid].get("score")
        # Strip provider prefix
        for key, val in scores.items():
            if not isinstance(val, dict):
                continue
            norm_key = key.lower().replace("/", "-").replace("_", "-")
            if norm_key == mid:
                return val.get("score")
            # Partial match for compound names
            if mid.startswith(norm_key) or norm_key.startswith(mid):
                return val.get("score")
    return None

def _benchmark_tier(score: float) -> str:
    """Return benchmark tier string for color coding."""
    if score is None:
        return "none"
    if score >= 70:
        return "S"
    if score >= 55:
        return "A"
    if score >= 40:
        return "B"
    return "C"

def _ocgo_budget_score(model_id: str) -> tuple[float, str]:
    """OpenCode Go budget efficiency: (score 0-100, tier_label).

    Based on requests-per-month and cost-per-token.
    Higher = more requests per dollar.
    Tier: excellent (>50K req/mo), good (10-50K), moderate (5-10K), expensive (<5K).
    """
    import math as _math
    ocgo = _load_benchmarks().get("opencode_go_budget", {}).get("models", {})
    mid = model_id.lower().replace("/", "-").replace("_", "-")

    # Find matching model
    info = None
    for key, val in ocgo.items():
        norm = key.lower().replace("-", "")
        if norm in mid.replace("-", "") or mid.replace("-", "") in norm:
            info = val
            break

    if not info:
        return None, "none"

    rpm = info.get("requests_per_month", 0)
    cpm = info.get("cost_per_m_tokens", 1.0)
    tier = info.get("quality_tier", "B")

    # Score: normalize requests-per-month to 0-100 (log scale)
    # 50K/month = 100 pts, 1K/month = 20 pts
    rpm_score = min(100, max(0, 20 + _math.log1p(rpm / 100) * 15))

    # Cost penalty: expensive models score lower
    cost_score = min(100, max(0, 50 - (cpm - 0.005) * 200))

    budget = round((rpm_score * 0.6 + cost_score * 0.4), 1)

    tier_label = {"S": "excellent", "A": "good", "B": "moderate"}.get(tier, "expensive")
    return budget, tier_label

# ──────────────────────────────────────────────────────────────────────────
# COMPOSITE SCORE + TIER + SLOT FITNESS
# ──────────────────────────────────────────────────────────────────────────
def _estimate_intelligence(d: Dossier) -> float | None:
    """Heuristic intelligence estimate when AA data unavailable. Returns 0-100.

    Thresholds: S>=65, A>=55, B>=40, C>=25, -=<25
    Based on real AA scores from ~May 2026:
      - deepseek-v4-pro: AA=51.5 (A-borderline, closer to B)
      - deepseek-v4-flash: AA=46.5
      - llama-4-maverick (NIM): AA=18.4 (NIM-specific)
      - gemma-4-31b-it (NIM): AA=39.2
      - nemotron-3-super-120b-a12b: AA=36.0
      - gpt-oss-120b: AA=33.3
      - gpt-5-5: AA=60.2 (S-borderline)
    """
    ai = d.ai_index
    if ai is not None:
        return ai
    mid = d.model.lower()

    # === S-TIER: AA >= 65 (frontier, top of leaderboard) ===
    # Only very top models reach 65+. GLM-5.1 is the primary anchor.
    if any(p in mid for p in ['glm-5.1', 'gemini-3-ultra', 'gpt-5.5', 'claude-4']):
        return 67.0

    # === A-TIER: AA 55-65 (strong frontier, top open-weight) ===
    # Qwen3-Next-80B-Thinking: AA ~52-58 based on eval patterns
    if 'qwen3-next' in mid and 'thinking' in mid:
        return 55.0
    # Top-tier MoE reasoning models
    # === S-TIER: verified 58-80% SWE-Bench / Terminal-Bench scores ===
    # These are verified benchmark leaders — must come before generic name matches
    if any(p in mid for p in ['kimi-k2.6', 'kimi-k2.5']):
        return 59.0   # 58.6% SWE-Pro, best agentic coder
    if any(p in mid for p in ['kimi-k2-thinking', 'minimax-m2.7']):
        return 52.0   # K2-thinking: AA~52; M2.7: 100 tok/s, 80.2% SWE-Verified (M2.5)
    # Kimi-K2 (non-reasoning, catch-all after specific checks): AA ~37-50
    if 'kimi-k2' in mid:
        return 42.0
    if any(p in mid for p in ['deepseek-v4-flash', 'deepseek-v4-pro']):
        return 60.0   # 79% SWE-Verified, 55% SWE-Pro (DeepSeek V4 family)
    if any(p in mid for p in ['glm-5.1', 'glm-5']):
        return 58.0   # 58.4% SWE-Pro, best reasoning among Go models
    if any(p in mid for p in ['qwen3.6-plus', 'qwen3.6-max']):
        return 55.0   # 78.8% SWE-Verified, 61.6% Terminal-Bench
    if any(p in mid for p in ['mimo-v2.5-pro', 'mimo-v2-pro']):
        return 53.0   # MiMo-V2.5-Pro: strong terminal, efficient
    if 'minimax-m2.5' in mid:
        return 51.0   # 80.2% SWE-Verified, 1M ctx
    if any(p in mid for p in ['qwen3-coder-next', 'qwen3-coder-480b']):
        return 48.0   # Qwen Coder: specialized coding

    # === B-TIER: 40-54 (strong generalists, production-grade) ===
    if any(p in mid for p in ['qwen3.5', 'qwen3-32b', 'qwen3-coder-480b',
                                'qwen3.5-plus', 'qwen2.5-coder-32b']):
        return 45.0   # Qwen 3.5 family strong coding
    # Nemotron-3-Super-120B: AA=36 (closer to B/C border)
    if 'nemotron-3-super' in mid:
        return 36.0
    # Cogito-2: ~35-40
    if 'cogito-2' in mid:
        return 38.0
    # Mistral-Large-3 / Medium-3: ~35-45
    if any(p in mid for p in ['mistral-large-3', 'mistral-medium-3']):
        return 40.0
    # Gemma-4-31B on NIM: AA=39.2
    if 'gemma-4' in mid and '31b' in mid:
        return 39.0
    # Llama-3.3-70B-Versatile (Groq): AA ~38-42 (Gorq-optimized)
    if 'llama-3.3-70b' in mid or 'llama3.3-70b' in mid:
        return 40.0
    # GPT-OSS-120B: AA=33.3
    if 'gpt-oss-120b' in mid:
        return 33.0

    # === C-TIER: AA 25-40 (capable, smaller/faster models) ===
    if any(p in mid for p in ['llama-3.1-8b', 'llama-3.1-70b', 'llama-3.2',
                                'gemma-4', 'gemma-3', 'gemma-3n',
                                'mistral-7b', 'mistral-nemo', 'mistral-nemotron',
                                'mistral-small-4', 'ministral', 'mixtral-8x22b',
                                'devstral', 'qwen3', 'phi-4', 'gpt-oss-20b',
                                'nemotron-nano', 'nemotron-mini',
                                'llama-4-scout', 'llama-4-maverick',
                                'nemotron-3-nano', 'nemotron-content',
                                'phi-4-mini', 'gliner', 'allam', 'lfm-',
                                'qwen3-coder', 'qwen2.5']):
        return 28.0
    # Cogito-2.1, RNJ-1: ~25-30
    if any(p in mid for p in ['cogito-2.1', 'rnj-', 'mistral-small-3']):
        return 26.0

    # === C-TIER (25-40): medium-small / specialized ===
    # isar-calibration: NIM benchmark model, ~35-40
    if 'isar-calibration' in mid:
        return 36.0
    # stockmark-2: domain-specific coding, ~15-20
    if 'stockmark-2' in mid:
        return 18.0
    # solar-10.7b: upstage frontier model, ~25-30
    if 'solar-10.7b' in mid:
        return 27.0
    # llama-3.1-8b: small model, ~25-30
    if 'llama-3.1-8b' in mid:
        return 28.0
    # llama-3.1 variants: ~28-35
    if 'llama-3.1' in mid:
        return 30.0
    # mistral-small-4: ~25-35
    if 'mistral-small-4' in mid:
        return 28.0
    # llama-guard-4: ~12-15
    if 'llama-guard-4' in mid:
        return 14.0
    # riva/translate: ~8-12
    if any(p in mid for p in ['riva', 'translate']):
        return 10.0
    # gemma-2: ~8-15
    if 'gemma-2' in mid:
        return 12.0
    # phi-3: ~8-12
    if 'phi-3' in mid:
        return 10.0
    # ministral-3b: ~12-15
    if 'ministral-3b' in mid:
        return 14.0
    # small/specialized models
    if any(p in mid for p in ['guard', 'safety', 'content-safety',
                               'emb', 'embedding', 'rerank', 'ner', 'phi-mini']):
        return 15.0

    # Unknown models default to conservative C-tier
    return 28.0

def compute_composite(d: Dossier, weights: dict) -> float:
    """Composite score for within-tier ranking. Uses AA when available, heuristic otherwise."""
    parts = []
    # Use AA intelligence as primary signal when available
    intelligence = _estimate_intelligence(d)
    if intelligence is not None:
        parts.append(("ai_intelligence", intelligence, weights.get("ai_intelligence", 0.45)))
    # Coding index when available
    if d.ai_coding is not None:
        parts.append(("ai_coding", d.ai_coding, weights.get("ai_coding", 0.20)))
    # Latency: use log scale so 0.1s vs 1s vs 10s differences matter proportionally
    # log(0.1)= -2.3, log(1)= 0, log(10)= 2.3 → invert so fast=high score
    if d.latency_s > 0:
        import math
        # latency score: 80 for 0.1s, 60 for 0.5s, 40 for 1s, 20 for 3s, 0 for 10s+
        lat_score = max(0, 80 - math.log1p(d.latency_s) * 30)
        parts.append(("latency", lat_score, weights.get("latency_inv", 0.15)))
    # Reliability contribution
    parts.append(("reliability", d.reliability * 100, weights.get("reliability", 0.15)))
    # MoE efficiency bonus (cost-per-performance advantage)
    if d.active_b > 0 and d.total_b > d.active_b:
        moe_eff = min(80, (d.total_b / d.active_b) * 4)
        parts.append(("moe", moe_eff, weights.get("moe_efficiency", 0.05)))

    if not parts:
        return 0.0
    weighted = sum(value * w for _, value, w in parts)
    total_w = sum(w for _, _, w in parts)
    return weighted / total_w if total_w > 0 else 0.0

def compute_tier(composite: float, ai_index: float | None, thresholds: dict) -> str:
    """Assign tier based on AA intelligence when available, heuristic estimate otherwise."""
    # Primary signal: actual AA intelligence
    if ai_index is not None:
        score = ai_index
    else:
        # No AA — use heuristic estimate via composite heuristic
        # Composite uses heuristic intelligence, so it reflects true capability
        score = composite

    if score >= thresholds.get("S", 65):
        return "S"
    if score >= thresholds.get("A", 55):
        return "A"
    if score >= thresholds.get("B", 40):
        return "B"
    if score >= thresholds.get("C", 25):
        return "C"
    return "—"

def slot_fitness(d: Dossier, slot_def: dict, use_scoring_engine: bool = False,
                free_mode: bool = False) -> tuple[float, list[str]]:
    """Returns (0-100 fitness score, list of disqualification reasons).
    
    When free_mode=True and slot_def['eval_mode']=='free', disqualifies
    any model not in the free-model whitelist.
    
    When use_scoring_engine=True, uses the multi-axis ScoringEngine for 
    intelligence/speed/agentic/coding scores instead of heuristic calculations.
    """
    reasons = []
    if not d.accessible:
        return 0.0, ["dead"]
    
    # Free-mode gate: for free-tier slots, skip paid models
    if free_mode:
        slot_mode = slot_def.get("eval_mode", "free")
        if slot_mode != "cost_basis":
            if not is_model_free(d.model, d.provider):
                reasons.append("paid-model")
                return 0.0, reasons
    # Even without free-mode, free-tier slots get a cost-penalty hint
    else:
        slot_mode = slot_def.get("eval_mode", "free")
        if slot_mode == "free":
            if not is_model_free(d.model, d.provider):
                reasons.append("paid-model-to-free-slot")
                # Don't return 0 — still allow it, but with a hint
                # The slot_fitness caller can check for this hint
    
    if slot_def.get("needs_tools") and not d.has_tools:
        reasons.append("no-tools")
    if slot_def.get("needs_vision") and not d.has_vision_capability:
        reasons.append("no-vision")
    if (m := slot_def.get("min_tps")) and d.tps < m:
        reasons.append(f"tps<{m}")
    if (m := slot_def.get("max_latency_s")) and d.latency_s > m:
        reasons.append(f"lat>{m}s")
    # Use _estimate_intelligence() which has comprehensive heuristics + verified benchmark scores.
    # Falls back to AA data when available, otherwise uses verified benchmark data for
    # known models (kimi-k2.6, deepseek-v4-flash, qwen3.6-plus, etc.) to avoid
    # the "all models = 50" problem.
    ai = _estimate_intelligence(d)
    if ai is None:
        ai = 28.0  # truly unknown model — conservative C-tier (matching heuristic default)
    if (m := slot_def.get("min_ai")) and ai < m:
        reasons.append(f"ai<{m}")
    # Only enforce min_ctx_k if we have context data; unknown context is assumed adequate
    if d.ctx_k is not None and (m := slot_def.get("min_ctx_k")) and d.ctx_k < m:
        reasons.append(f"ctx<{m}K")

    if reasons:
        return 0.0, reasons

    if use_scoring_engine:
        # Use multi-axis scoring engine for richer fitness calculation
        try:
            from scoring.engine import ScoringEngine, load_benchmarks
            model_data = {
                "model_id": d.model,
                "provider": d.provider,
                "tps": d.tps,
                "latency_s": d.latency_s,
                "ai_index": d.ai_index,
                "ai_coding": d.ai_coding,
                "has_tools": d.has_tools,
                "has_vision_capability": d.has_vision_capability,
                "has_reasoning": False,
                "context_window": (d.ctx_k or 0) * 1024,
                "knowledge": "",
                "release_date": "",
                "benchmark_swe_verified": d.benchmark_swe_verified,
                "price_blended": d.price_blended,
                "arch": d.arch,
            }
            benchmarks = load_benchmarks()
            engine = ScoringEngine(model_data, benchmarks)
            scores = engine.compute_all()
            
            # Map slot weights to axis weights
            weights = {
                "intelligence": slot_def.get("weight_intelligence", 0.4),
                "speed": slot_def.get("weight_speed", 0.3),
                "agentic": 0.15,
                "coding": 0.15,
            }
            # Normalize to 1.0
            total_w = sum(weights.values())
            if total_w > 0:
                weights = {k: v / total_w for k, v in weights.items()}
            
            fitness = scores.composite(weights) * 100.0
            fitness = min(100, max(0, fitness))
            
            # Architecture bonus for preferred archs
            if (preferred := slot_def.get("preferred_arch")) and d.arch in preferred:
                fitness = min(100, fitness * 1.05)
            
            # Budget score for OpenCode Go
            if d.ocgo_budget_score is not None and (bw := slot_def.get("weight_budget", 0)) > 0:
                fitness = fitness * (1 - bw) + d.ocgo_budget_score * bw
                fitness = min(100, fitness)
            
            return round(fitness, 1), reasons
        except ImportError:
            # Fall through to heuristic if scoring engine not available
            pass

    # ── Heuristic fitness (default) ──
    intel_score = ai if ai is not None else 50
    tps_contribution = min(100, d.tps / 60.0 * 50.0)  # normalized: 60 tps → 50 pts
    lat_contribution = max(0, 50 - d.latency_s * 10)  # 5s latency → 0 pts
    speed_score = min(100, tps_contribution + lat_contribution)
    rel_score = d.reliability * 100

    fitness = (
        slot_def.get("weight_intelligence", 0.4) * intel_score
        + slot_def.get("weight_speed", 0.3) * speed_score
        + slot_def.get("weight_reliability", 0.3) * rel_score
    )
    # Clamp fitness to 0-100 before applying bonuses
    fitness = min(100, max(0, fitness))

    # Architecture bonus for preferred archs
    if (preferred := slot_def.get("preferred_arch")) and d.arch in preferred:
        fitness = min(100, fitness * 1.05)

    # Budget score for OpenCode Go slots — blend in requests-per-dollar efficiency
    if d.ocgo_budget_score is not None and (bw := slot_def.get("weight_budget", 0)) > 0:
        # Normalize budget score to same 0-100 scale
        fitness = fitness * (1 - bw) + d.ocgo_budget_score * bw
        fitness = min(100, fitness)

    return round(fitness, 1), reasons

# ──────────────────────────────────────────────────────────────────────────
# RENDER — three-section layout
# ──────────────────────────────────────────────────────────────────────────
def term_width() -> int:
    import shutil
    w = shutil.get_terminal_size((140, 24)).columns
    return max(100, min(w, 200))

def generate_hermes_patch(dossiers: list[Dossier], slot_defs: dict) -> str:
    """Generate a YAML patch for hermes config with best model replacements."""
    lines = [
        "# ═══════════════════════════════════════════════════════════════════════════",
        f"# model-scan HERMES PATCH — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "# Apply manually to ~/.hermes/config.yaml",
        "# ═══════════════════════════════════════════════════════════════════════════",
        "",
        "# ── SLOT REPLACEMENTS ──────────────────────────────────────────────────",
    ]

    # Build replacements dynamically from slot_defs + dossier fitness
    for slot_id, sdef in slot_defs.items():
        label = sdef.get("label", slot_id)
        qualified = [d for d in dossiers if d.accessible and d.slot_fitness.get(slot_id, 0) > 0]
        if not qualified:
            lines.append(f"# {slot_id} ({label}) — no qualified candidates")
            continue
        best = max(qualified, key=lambda d: d.slot_fitness.get(slot_id, 0))
        fit = best.slot_fitness.get(slot_id, 0)
        lines.append(f"# {slot_id} ({label}):")
        lines.append(f"#   → {best.api_model} ({best.provider}) fit={fit:.1f} tps={best.tps:.0f}")
        lines.append("")

    lines.extend([
        "",
        "# ── BROKEN MODELS (from bad_models.json) ─────────────────────────────",
        "# These models had persistent failures. See bad_models.json for details.",
    ])
    bad = load_bad()
    if bad:
        for key, entry in list(bad.items())[:10]:
            lines.append(f"#   {key}")
    else:
        lines.append("#   (none)")

    lines.extend([
        "",
        "# ── WORKING ALTERNATIVES (by slot) ───────────────────────────────────",
    ])
    for slot_id, sdef in slot_defs.items():
        qualified = [d for d in dossiers if d.accessible and d.slot_fitness.get(slot_id, 0) > 0]
        qualified.sort(key=lambda d: d.slot_fitness.get(slot_id, 0), reverse=True)
        top3 = qualified[:3]
        if top3:
            label = sdef.get("label", slot_id)
            fits = ", ".join(f"{d.api_model} ({d.provider}, fit={d.slot_fitness.get(slot_id, 0):.0f})" for d in top3)
            lines.append(f"#   {slot_id}: {fits}")

    return "\n".join(lines)

def render_banner(provider_count: int, model_count: int, scan_seconds: float,
                  aa_provenance: str, hermes_slots: int, total_candidates: int = 0,
                  skipped_count: int = 0, providers_active: list[str] = None,
                  providers_skipped: list[str] = None):
    aa_color = (C.SUCCESS_N if aa_provenance == "fresh"
                else C.INFO_N if aa_provenance.startswith("cached")
                else C.WARN_N if aa_provenance.startswith("stale") or aa_provenance == "rate-limited"
                else C.ERROR_N)
    print()
    print(f"{C.INFO}{C.ARROW} model-scan v4{C.RST}  "
          f"{C.PRIMARY}{model_count} models{C.RST}  "
          f"{aa_color}AA: {aa_provenance}{C.RST}  "
          f"{C.SECONDARY}{hermes_slots} slots{C.RST}  "
          f"{C.META}{scan_seconds:.1f}s{C.RST}")
    # Provider compact status
    if providers_active:
        active_str = ", ".join(f"{p}({c})" for p, c in providers_active if c > 0)
        if providers_skipped:
            skipped_str = " | " + ", ".join(providers_skipped)
        else:
            skipped_str = ""
        print(f"  {C.META}{active_str}{skipped_str}{C.RST}")

def render_incumbent_panel(dossiers: list[Dossier], hermes_slots: dict,
                           proxy_tiers: dict, slot_defs: dict):
    """Top section: one row per active Hermes/proxy slot showing current incumbent health."""
    if not hermes_slots and not proxy_tiers:
        return

    width = term_width()
    print()
    print(f"{C.SECONDARY}{C.HRULE * width}{C.RST}")
    print(f"{C.INFO}INCUMBENT STACK{C.RST}  {C.META}{C.HRULE} active slots {C.HRULE}{C.RST}")
    print()

    # Build dossier lookup by model_id
    by_model = {d.model: d for d in dossiers}
    # Also try with provider/ prefix variants
    by_full = {}
    for d in dossiers:
        by_full[f"{d.provider}/{d.model}"] = d
        by_full[d.model] = d
        # Drop common prefixes to match
        for prefix in ("openai/", "openrouter/", "nvidia/", "qwen/", "z-ai/", "minimax/",
                       "moonshotai/", "arcee-ai/", "google/", "meta-llama/", "mistralai/"):
            if d.model.startswith(prefix):
                by_full[d.model[len(prefix):]] = d

    rows = []
    for slot_id, model_id in {**hermes_slots, **proxy_tiers}.items():
        d = by_full.get(model_id) or by_full.get(model_id.split("/")[-1])
        slot_def = slot_defs.get(slot_id, {})
        label = slot_def.get("label", slot_id)
        if not d:
            rows.append((slot_id, label, model_id, None, "not-scanned", "", ""))
            continue
        status = ("healthy" if d.reliability >= 0.99
                  else "degraded" if d.reliability >= 0.5
                  else "DOWN")
        recommendation = ""
        if status != "healthy":
            # Find best replacement
            replacements = [other for other in dossiers
                           if other.accessible and other.model != d.model
                           and slot_id in other.qualified_slots]
            replacements.sort(key=lambda x: -x.slot_fitness.get(slot_id, 0))
            if replacements:
                recommendation = f"swap → {replacements[0].model}"
        rows.append((slot_id, label, model_id, d, status, recommendation, d.fail_class))

    # Render
    max_slot = max(len(r[0]) for r in rows) if rows else 12
    max_label = max(len(r[1]) for r in rows) if rows else 12
    for slot_id, label, model_id, d, status, rec, fail in rows:
        if status == "healthy":
            glyph, color = C.CHECK, C.SUCCESS
            metrics = f"{d.latency_s:.1f}s {d.tps:.0f}t/s"
        elif status == "degraded":
            glyph, color = C.TRI, C.WARN
            metrics = f"{d.latency_s:.1f}s {d.tps:.0f}t/s {C.WARN_D}({fail}){C.RST}"
        elif status == "DOWN":
            glyph, color = C.CROSS, C.ERROR
            metrics = f"{C.ERROR_D}{fail}{C.RST}"
        else:
            glyph, color = C.DOT, C.SECONDARY
            metrics = f"{C.META}not-scanned{C.RST}"

        slot_str = f"{C.INFO_D}{slot_id.ljust(max_slot)}{C.RST}"
        label_str = f"{C.SECONDARY}{label.ljust(max_label)}{C.RST}"
        model_str = f"{C.PRIMARY}{model_id}{C.RST}" if d and d.reliability >= 0.99 else f"{C.SECONDARY}{model_id}{C.RST}"
        rec_str = f"  {C.ACCENT}{C.DIAMOND} {rec}{C.RST}" if rec else ""

        print(f"  {color}{glyph}{C.RST} {slot_str}  {label_str}  {model_str.ljust(50)}  {metrics}{rec_str}")

def render_per_slot_view(dossiers: list[Dossier], slot_defs: dict, hermes_slots: dict,
                         only_slot: str | None = None):
    """Middle section: top 3-5 candidates per Hermes slot, fitness-scored."""
    width = term_width()
    print()
    print(f"{C.SECONDARY}{C.HRULE * width}{C.RST}")
    print(f"{C.INFO}PER-SLOT CANDIDATES{C.RST}  {C.META}{C.HRULE} fitness-ranked top 5 {C.HRULE}{C.RST}")

    accessible = [d for d in dossiers if d.accessible]
    by_full = {f"{d.provider}/{d.model}": d for d in accessible}
    for d in accessible:
        by_full[d.model] = d

    slots_to_show = [only_slot] if only_slot else list(slot_defs.keys())

    first = True
    for slot_id in slots_to_show:
        slot_def = slot_defs.get(slot_id, {})
        if not slot_def:
            continue
        label = slot_def.get("label", slot_id)

        candidates = [d for d in accessible if d.slot_fitness.get(slot_id, 0) > 0]
        candidates.sort(key=lambda x: -x.slot_fitness.get(slot_id, 0))
        top_n = 3 if only_slot else 5
        candidates = candidates[:top_n]

        incumbent_id = hermes_slots.get(slot_id, "")
        incumbent_dossier = by_full.get(incumbent_id) or by_full.get(incumbent_id.split("/")[-1])
        incumbent_fitness = incumbent_dossier.slot_fitness.get(slot_id, 0) if incumbent_dossier else 0

        if not candidates:
            if first:
                print()
                first = False
            # Show the top few models with their disqualification reasons
            near_miss = [(d, d.slot_fitness.get(slot_id, 0)) for d in accessible
                        if d.slot_fitness.get(slot_id, 0) > 0]
            near_miss.sort(key=lambda x: -x[1])
            if near_miss:
                reasons = near_miss[0][0].slot_fitness.get(slot_id, "")
                print(f"  {C.WARN}{C.TRI}{C.RST} {C.INFO_D}{slot_id}{C.RST} ({label}) — no qualified candidates")
                print(f"    {C.META}near-miss: {near_miss[0][0].model[:50]} fit={near_miss[0][1]:.0f}{C.RST}")
            else:
                print(f"  {C.WARN}{C.TRI}{C.RST} {C.INFO_D}{slot_id}{C.RST} ({label}) — no candidates meet minimums")
            continue

        if first:
            print()
            first = False

        print(f"  {C.INFO}{slot_id}{C.RST}  {C.SECONDARY}({label}){C.RST}  "
              f"{C.META}— top {len(candidates)} candidates by fitness{C.RST}")
        for i, d in enumerate(candidates, 1):
            fit = d.slot_fitness.get(slot_id, 0)
            delta = fit - incumbent_fitness
            is_incumbent = (d == incumbent_dossier)

            marker = f"{C.SUCCESS}{C.CHECK} INCUMBENT{C.RST}" if is_incumbent else ""
            delta_str = ""
            if not is_incumbent and incumbent_dossier:
                if delta > 5:
                    delta_str = f" {C.SUCCESS_N}+{delta:.0f}{C.RST}"
                elif delta < -5:
                    delta_str = f" {C.ERROR_D}{delta:.0f}{C.RST}"
                else:
                    delta_str = f" {C.META}~{delta:+.0f}{C.RST}"

            ai_str = f"AA:{d.ai_index:.0f}" if d.ai_index else "AA:?"
            tools_str = "T" if d.has_tools else "·"
            vision_str = "V" if d.has_vision_capability else "·"

            # Benchmark + OCGo budget indicators
            bench_str = ""
            if d.benchmark_swe_verified is not None:
                bt = _benchmark_tier(d.benchmark_swe_verified)
                bc = {"S": C.BENCH_S, "A": C.BENCH_A, "B": C.BENCH_B, "C": C.BENCH_C}.get(bt, C.META)
                bench_str = f" {bc}{d.benchmark_swe_verified:.0f}%{C.RST}"
            budget_str = ""
            if d.ocgo_budget_tier not in ("unknown", "none", ""):
                bt_colors = {"excellent": C.BUDGET_EXCELLENT, "good": C.BUDGET_GOOD,
                             "moderate": C.BUDGET_MODERATE, "expensive": C.BUDGET_EXPENSIVE}
                bc = bt_colors.get(d.ocgo_budget_tier, C.META)
                budget_str = f" {bc}{d.ocgo_budget_tier[:3]}{C.RST}"

            print(f"    {C.METRICS}{i}.{C.RST} "
                  f"{C.PRIMARY if is_incumbent else C.SECONDARY}{d.model:<48}{C.RST}"
                  f"{bench_str}{budget_str} "
                  f"{C.METRICS_D}{PROVIDERS[d.provider]['abbrev']:<5}{C.RST} "
                  f"{C.METRICS}fit:{fit:.0f}{delta_str}{C.RST}  "
                  f"{C.METRICS_D}{ai_str:<6} {d.tps:>3.0f}t/s {d.latency_s:.1f}s [{tools_str}{vision_str}]{C.RST}"
                  f"{'  ' + marker if marker else ''}")

def render_appendix(dossiers: list[Dossier], by: str = "tier"):
    """Bottom section: full flat table of all accessible models, sortable."""
    width = term_width()
    print()
    print(f"{C.SECONDARY}{C.HRULE * width}{C.RST}")
    print(f"{C.INFO}APPENDIX{C.RST}  {C.META}{C.HRULE} {by}-sorted, all accessible{C.RST}")

    accessible = [d for d in dossiers if d.accessible]

    def sort_key(d: Dossier):
        if by == "tier":
            tier_order = {"S": 0, "A": 1, "B": 2, "C": 3, "—": 4}
            return (tier_order.get(d.tier, 5), -d.composite)
        if by == "fitness":
            return (-max(d.slot_fitness.values()) if d.slot_fitness else 0,)
        if by == "tps":
            return (-d.tps,)
        if by == "latency":
            return (d.latency_s,)
        if by == "ai":
            return (-(d.ai_index or 0),)
        return (-d.composite,)

    accessible.sort(key=sort_key)

    # Compact header — single line
    print(f"  {C.INFO_D}{'TIER':<4}{C.RST} {C.INFO_D}{'MODEL':<46}{C.RST} {C.INFO_D}{'PROV':<5}{C.RST} {C.INFO_D}{'AA-I':>4}{C.RST} {C.INFO_D}{'AA-C':>4}{C.RST} {C.INFO_D}{'TPS':>4}{C.RST} {C.INFO_D}{'LAT':>5}{C.RST} {C.INFO_D}{'T':<1}{C.RST} {C.INFO_D}{'V':<1}{C.RST} {C.INFO_D}{'ARCH':<10}{C.RST} {C.INFO_D}{'SIZE':<7}{C.RST} {C.INFO_D}{'$/M':>5}{C.RST} {C.INFO_D}{'SLOTS':<18}{C.RST}")
    print(f"  {C.META}{C.HRULE * (width - 4)}{C.RST}")

    for d in accessible:
        # Benchmark-aware tier color: use verified benchmark score when available
        bench_tier = _benchmark_tier(d.benchmark_swe_verified)
        if bench_tier == "S":
            tier_color = C.BENCH_S
        elif bench_tier == "A":
            tier_color = C.BENCH_A
        elif bench_tier == "B":
            tier_color = C.BENCH_B
        elif bench_tier == "C":
            tier_color = C.BENCH_C
        else:
            tier_color = (C.SUCCESS if d.tier == "S"
                         else C.SUCCESS_N if d.tier == "A"
                         else C.METRICS_N if d.tier == "B"
                         else C.SECONDARY if d.tier == "C"
                         else C.META)
        tier_str = f"{tier_color}{d.tier:<4}{C.RST}"

        # Benchmark score indicator: show SWE% in brackets if available
        bench_suffix = ""
        if d.benchmark_swe_verified is not None:
            bench_suffix = f"{tier_color}[{d.benchmark_swe_verified:.0f}]{C.RST}"

        model_str = (f"{C.PRIMARY}{d.model[:45]:<46}{C.RST}" if d.tier in ("S", "A")
                    else f"{C.SECONDARY}{d.model[:45]:<46}{C.RST}")

        prov_abbr = PROVIDERS[d.provider]["abbrev"]
        prov_str = f"{C.METRICS_D}{prov_abbr:<5}{C.RST}"

        if d.ai_index is not None:
            ai_str = f"{C.METRICS}{d.ai_index:>4.0f}{C.RST}"
        elif d.aa_provenance == "snapshot":
            ai_str = f"{C.META}{'—':>4}{C.RST}"
        else:
            ai_str = f"{C.META}{'~':>4}{C.RST}"  # ~ = heuristic estimate
        ac_str = (f"{C.METRICS}{d.ai_coding:>4.0f}{C.RST}" if d.ai_coding
                  else f"{C.META}{'?':>4}{C.RST}")

        tps_color = (C.METRICS if d.tps >= 50 else C.WARN_N if d.tps < 20 else C.METRICS_D)
        tps_str = f"{tps_color}{d.tps:>4.0f}{C.RST}"

        lat_color = (C.METRICS if d.latency_s < 1 else C.WARN_N if d.latency_s > 3 else C.METRICS_D)
        lat_str = f"{lat_color}{d.latency_s:>4.1f}s{C.RST}"

        t_str = f"{C.SUCCESS_N}T{C.RST}" if d.has_tools else f"{C.META}·{C.RST}"
        v_str = f"{C.SUCCESS_N}V{C.RST}" if d.has_vision_capability else f"{C.META}·{C.RST}"

        arch_str = f"{C.SECONDARY}{d.arch[:10]:<10}{C.RST}"
        if d.total_b:
            size_str = f"{C.SECONDARY}{d.total_b:.0f}/{d.active_b:.0f}{C.RST}"
        else:
            size_str = f"{C.META}{'?':<7}{C.RST}"

        if d.price_blended is not None:
            price_str = (f"{C.SUCCESS_N}FREE{C.RST}" if d.price_blended == 0
                        else f"{C.METRICS_D}${d.price_blended:.2f}{C.RST}")
        else:
            price_str = f"{C.META}{'?':>5}{C.RST}"

        # Compact slots: R6,R8,R10,R11 → R6 R8 R10 R11
        slots_str = " ".join(s.split("_")[0] for s in d.qualified_slots[:6])
        slots_color = C.SUCCESS_N if d.qualified_slots else C.META
        slots_disp = f"{slots_color}{slots_str[:18]:<18}{C.RST}"

        print(f"  {tier_str} {model_str}{bench_suffix} {prov_str} {ai_str} {ac_str} {tps_str} {lat_str} {t_str} {v_str} {arch_str} {size_str:<7} {price_str} {slots_disp}")

    failed_count = len([d for d in dossiers if not d.accessible])
    if failed_count:
        print(f"  {C.META}{failed_count} inaccessible/skipped — see {RESULTS_FILE} for details{C.RST}")

def render_footer(dossiers: list[Dossier], aa_provenance: str, missing_keys: list[str],
                  permanent_skips: int):
    print()
    width = term_width()
    print(f"{C.SECONDARY}{C.HRULE * width}{C.RST}")

    healthy = sum(1 for d in dossiers if d.reliability >= 0.99)
    degraded = sum(1 for d in dossiers if 0.5 <= d.reliability < 0.99)
    failed = sum(1 for d in dossiers if d.reliability < 0.5)

    parts = []
    if healthy:
        parts.append(f"{C.SUCCESS}{C.CHECK} {healthy} healthy{C.RST}")
    if degraded:
        parts.append(f"{C.WARN}{C.TRI} {degraded} degraded{C.RST}")
    if failed:
        parts.append(f"{C.ERROR}{C.CROSS} {failed} dead{C.RST}")
    if permanent_skips:
        parts.append(f"{C.META}skip-list: {permanent_skips}{C.RST}")
    print("  ".join(parts))

    if missing_keys:
        print(f"\n  {C.WARN}{C.TRI} missing API keys: {', '.join(missing_keys)}{C.RST}")

    if aa_provenance == "missing":
        print(f"\n  {C.WARN}{C.TRI} AA_API_KEY not set. Sign up at {C.INFO_N}https://artificialanalysis.ai/login{C.RST}")
        print(f"  {C.WARN_D}then set AA_API_KEY in ~/.hermes/.env to enable Intelligence Index data.{C.RST}")
    elif aa_provenance == "unauthorized":
        print(f"\n  {C.ERROR}{C.CROSS} AA_API_KEY rejected. Check the key at artificialanalysis.ai/login{C.RST}")
    elif aa_provenance.startswith("stale") or aa_provenance.startswith("error"):
        print(f"\n  {C.WARN}{C.TRI} AA data: {aa_provenance}. Run with --refresh-aa when AA is reachable.{C.RST}")

    print(f"\n  {C.META}rehabilitate a skipped model: model-scan --rehabilitate <provider>/<model>{C.RST}")
    print(f"  {C.META}per-slot view: model-scan --slot R1_primary{C.RST}")

    now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"\n  {C.SECONDARY}scanned at {now_local}{C.RST}")

# ──────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATION
# ──────────────────────────────────────────────────────────────────────────
async def run_scan(args) -> int:
    t_start = time.perf_counter()

    tiers = load_tiers()
    slot_defs = load_slot_defs()
    bad = load_bad()

    hermes_slots = parse_hermes_slots()
    proxy_tiers = parse_proxy_tiers()

    # Filter providers by --provider flag and key availability
    provider_filter = args.providers.split(",") if args.providers else None
    active_providers = []
    missing_keys = []
    for prov, cfg in PROVIDERS.items():
        if provider_filter and prov not in provider_filter:
            continue
        key_var = cfg.get("key_env")
        if key_var:
            if not os.environ.get(key_var, "").strip():
                missing_keys.append(key_var)
                continue
        active_providers.append((prov, cfg))

    if not active_providers:
        print(f"{C.ERROR}no providers available — set at least one API key{C.RST}", file=sys.stderr)
        return 1

    async with httpx.AsyncClient(timeout=30) as client:
        # Fetch AA data first (parallel with other work)
        aa_lookup, aa_provenance = await fetch_aa_data(client, force=args.refresh_aa)

        # Enumerate models per provider
        all_candidates: list[tuple[str, str, dict, dict]] = []  # (prov, mid, pricing, cfg)
        for prov, cfg in active_providers:
            cat = await list_models(client, prov, cfg)

            # Venice uses read-only API key — skip probing
            if prov == "venice":
                print(f"  {C.INFO_D}{prov:<15}{C.RST} {len(cat)} catalog-only (skip probe){C.RST}", file=sys.stderr)
                continue
            skipped_count = 0
            for mid, pricing in cat:
                key = f"{prov}/{mid}"
                skipped, why = is_permanently_skipped(bad, key)
                if skipped:
                    skipped_count += 1
                    continue
                all_candidates.append((prov, mid, pricing, cfg))
            # Show per-provider stats: candidates and skipped
            n_candidates = len(cat)
            n_skipped = skipped_count
            if prov == "venice":
                print(f"  {C.INFO_D}{prov:<15}{C.RST} {n_candidates} catalog{C.RST}", file=sys.stderr)
            elif n_skipped > 0:
                print(f"  {C.INFO_D}{prov:<15}{C.RST} {n_candidates} probed  {C.META}{n_skipped} skipped{C.RST}", file=sys.stderr)
            else:
                print(f"  {C.INFO_D}{prov:<15}{C.RST} {n_candidates} probed{C.RST}", file=sys.stderr)

        # Probe in parallel
        sem = asyncio.Semaphore(args.concurrency)
        async def bounded_probe(prov, mid, pricing, cfg):
            async with sem:
                api_mod = api_model_for(prov, mid)
                result = await probe_one(client, prov, mid, api_mod, cfg)
                tools = False
                if result.get("ok") and result.get("tps", 0) > 0:
                    tools = await probe_tools(client, prov, mid, api_mod, cfg)
                return prov, mid, pricing, cfg, result, tools

        probe_tasks = [bounded_probe(p, m, pr, c) for p, m, pr, c in all_candidates]
        probe_results = await asyncio.gather(*probe_tasks, return_exceptions=True)

    # Build dossiers
    dossiers: list[Dossier] = []
    for r in probe_results:
        if isinstance(r, Exception):
            continue
        prov, mid, pricing, cfg, result, tools = r
        d = Dossier(
            provider=prov,
            model=mid,
            api_model=api_model_for(prov, mid),
            accessible=result.get("ok", False),
            latency_s=result.get("elapsed", 0),
            tps=result.get("tps", 0),
            reliability=1.0 if result.get("ok") else 0.0,
            has_tools=tools,
            fail_class=result.get("fail_class", ""),
            http_status=result.get("status", 0),
        )

        # Update bad-list tracking
        key = f"{prov}/{mid}"
        if d.accessible:
            record_success(bad, key)
        elif d.fail_class:
            record_failure(bad, key, d.fail_class)

        # Architecture from local refs
        arch, total, active = infer_arch(mid)
        d.arch, d.total_b, d.active_b = arch, total, active
        d.has_vision_capability = has_vision(mid)

        # Note: Don't skip "duplicates" across providers - different endpoints may have different performance
        # Note: Don't skip "duplicates" across providers - different endpoints may have different performance
        # The same model at different providers (NIM vs OCGo vs Groq) should all be probed
        aa = aa_lookup_model(aa_lookup, mid)
        if aa:
            d.ai_index = aa.get("ai_index")
            d.ai_coding = aa.get("ai_coding")
            d.ai_math = aa.get("ai_math")
            d.aa_provenance = aa_provenance
            d.price_blended = aa.get("price_blended")
            if not d.tps and aa.get("median_tps"):
                d.tps = aa["median_tps"]

                if not d.tps and aa.get("median_tps"):
                    d.tps = aa["median_tps"]

        # Pricing fallback from provider catalog
        if d.price_blended is None and pricing:
            try:
                p_in = float(pricing.get("prompt", 0)) * 1_000_000
                p_out = float(pricing.get("completion", 0)) * 1_000_000
                d.price_blended = (p_in * 0.58 + p_out * 0.42)
            except Exception:
                pass

        # Benchmark data — enrich from benchmarks.json
        benchmarks = _load_benchmarks()
        swe = _match_benchmark(mid, benchmarks)
        d.benchmark_swe_verified = swe
        # OCGo budget scoring
        if prov == "opencode-go":
            bscore, btier = _ocgo_budget_score(mid)
            d.ocgo_budget_score = bscore
            d.ocgo_budget_tier = btier

        # Composite + tier
        d.composite = compute_composite(d, tiers["composite_weights"])
        d.tier = compute_tier(d.composite, d.ai_index, tiers["thresholds"])

        # Slot fitness
        for slot_id, slot_def in slot_defs.items():
            fit, reasons = slot_fitness(d, slot_def,
                use_scoring_engine=args.score_engine,
                free_mode=args.free_mode)
            d.slot_fitness[slot_id] = fit
            if fit > 0:
                d.qualified_slots.append(slot_id)

        dossiers.append(d)

    save_bad(bad)

    # Save results history
    history_entry = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "duration_s": time.perf_counter() - t_start,
        "aa_provenance": aa_provenance,
        "hermes_slots": hermes_slots,
        "results": [asdict(d) for d in dossiers],
    }
    history = []
    if RESULTS_FILE.exists():
        try:
            history = json.loads(RESULTS_FILE.read_text())
            if not isinstance(history, list):
                history = []
        except Exception:
            history = []
    history.append(history_entry)
    history = history[-30:]  # keep last 30 runs
    RESULTS_FILE.write_text(json.dumps(history, indent=2))

    # JSON output mode
    if args.json:
        print(json.dumps([asdict(d) for d in dossiers], indent=2, default=str))
        return 0

    # Render
    duration = time.perf_counter() - t_start
    permanent_skips = sum(1 for k in bad if is_permanently_skipped(bad, k)[0])
    accessible_count = sum(1 for d in dossiers if d.accessible)

    # Build provider counts from candidate enumeration
    prov_counts = {}
    for d in dossiers:
        prov_counts[d.provider] = prov_counts.get(d.provider, 0) + 1

    # Save to SQLite database for historical analytics
    healthy = sum(1 for d in dossiers if d.reliability >= 0.99)
    degraded = sum(1 for d in dossiers if 0.5 <= d.reliability < 0.99)
    failed_count = sum(1 for d in dossiers if d.reliability < 0.5)
    _db_save_run(dossiers, duration, aa_provenance, prov_counts,
                 hermes_slots, proxy_tiers, healthy, degraded,
                 failed_count, permanent_skips)

    # Build per-provider counts from the candidate enumeration phase
    # We track skipped_count in the scan loop but need to pass it through
    # For now, just show total and accessible
    render_banner(len(active_providers), len(dossiers), duration, aa_provenance, len(hermes_slots))

    if not args.no_incumbent:
        render_incumbent_panel(dossiers, hermes_slots, proxy_tiers, slot_defs)

    if args.slot:
        render_per_slot_view(dossiers, slot_defs, hermes_slots, only_slot=args.slot)
    elif not args.no_slots:
        render_per_slot_view(dossiers, slot_defs, hermes_slots)

    if not args.no_appendix:
        render_appendix(dossiers, by=args.by)

    render_footer(dossiers, aa_provenance, missing_keys, permanent_skips)
    return 0

# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────
# CLI COMMANDS
# ──────────────────────────────────────────────────────────────────────────
def _cmd_analyze_history(args):
    """Query SQLite for historical patterns."""
    slot_id = args.analyze_history
    slot_defs = load_slot_defs()
    slot_def = slot_defs.get(slot_id)
    if not slot_def:
        print(f"{C.ERROR}unknown slot: {slot_id}{C.RST}", file=sys.stderr)
        print(f"  Available: {', '.join(slot_defs.keys())}", file=sys.stderr)
        return

    conn = sqlite3.connect(str(DATABASE_FILE))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT m.model_id, m.provider, m.tier, m.accessible,
               sf.fitness, m.tps, m.latency_s, m.ai_index,
               m.benchmark_swe_verified, m.ocgo_budget_score
        FROM models m
        JOIN slot_fitness sf ON m.model_pk = sf.model_fk
        JOIN scans s ON sf.scan_id = s.scan_id
        WHERE sf.slot_id = ?
        AND m.accessible = 1
        ORDER BY s.scanned_at DESC
        LIMIT 50
    """, (slot_id,)).fetchall()
    conn.close()

    if not rows:
        print(f"{C.WARN}no historical data for {slot_id}{C.RST}", file=sys.stderr)
        print(f"  Run a full scan first to populate the database.", file=sys.stderr)
        return

    from collections import Counter
    model_counts = Counter()
    fitness_by_model = {}
    for row in rows:
        key = f"{row['provider']}/{row['model_id']}"
        model_counts[key] += 1
        fitness_by_model[key] = row["fitness"]

    print()
    print(f"{C.INFO}Historical patterns for {slot_id}{C.RST} ({slot_def.get('label', '')})")
    print(f"{C.META}(last 50 scan appearances){C.RST}")
    print()
    print(f"  {C.INFO_D}{'Model':<50} {'Appearances':>12} {'Avg Fitness':>12}{C.RST}")
    print(f"  {C.META}{'─' * 76}{C.RST}")
    for model_key, count in model_counts.most_common(10):
        avg_fit = fitness_by_model[model_key]
        print(f"  {C.SECONDARY}{model_key:<50}{C.RST} {C.METRICS}{count:>12} {C.METRICS_D}{avg_fit:>12.1f}{C.RST}")

    print()
    print(f"{C.META}Current slot definition:{C.RST}")
    print(f"  weights: intel={slot_def.get('weight_intelligence')}, "
          f"speed={slot_def.get('weight_speed')}, "
          f"rel={slot_def.get('weight_reliability')}")
    print(f"  gates: min_tps={slot_def.get('min_tps')}, "
          f"min_ai={slot_def.get('min_ai')}")

def _cmd_rank_vs_benchmark(args):
    """Compare slot rankings against benchmark data."""
    benchmarks = _load_benchmarks()
    swe = benchmarks.get("swe_verified", {})
    if not swe:
        print(f"{C.WARN}No benchmark data — run --update-benchmarks first{C.RST}", file=sys.stderr)
        return

    slot_defs = load_slot_defs()

    print()
    print(f"{C.INFO}Slot rankings vs verified benchmark data{C.RST}")
    print(f"{C.META}Benchmarks source: benchmarks.json{C.RST}")
    print()

    for slot_id, slot_def in slot_defs.items():
        label = slot_def.get("label", slot_id)
        print(f"{C.INFO}{slot_id}{C.RST} ({label})")

        if not RESULTS_FILE.exists():
            print(f"  {C.META}(run full scan first){C.RST}")
            continue

        try:
            history = json.loads(RESULTS_FILE.read_text())
        except Exception:
            print(f"  {C.ERROR}could not read results.json{C.RST}")
            continue

        if not history:
            print(f"  {C.META}(no scan history){C.RST}")
            continue

        results = history[-1].get("results", [])
        candidates = []
        for r in results:
            fit = r.get("slot_fitness", {}).get(slot_id, 0)
            if fit > 0:
                candidates.append((fit, r))
        candidates.sort(key=lambda x: -x[0])

        print(f"  {C.INFO_D}{'Rank':<5}{C.RST} {C.INFO_D}{'Model':<35}{C.RST} "
              f"{C.INFO_D}{'Fitness':>7}{C.RST} {C.INFO_D}{'SWE-Verified':>12}{C.RST}")

        shown = 0
        for fit, r in candidates[:5]:
            mid = r.get("model", "")
            bench_score = None
            for bkey, bval in swe.items():
                if isinstance(bval, dict):
                    bmid = bkey.lower().replace("/", "-")
                    if bmid in mid.lower() or mid.lower().replace("/", "-") in bmid:
                        bench_score = bval.get("score")
                        break

            tier_color = C.BENCH_A if bench_score and bench_score >= 55 else \
                        C.BENCH_B if bench_score and bench_score >= 40 else \
                        C.META
            bench_str = f"{tier_color}{bench_score:.1f}%{C.RST}" if bench_score else f"{C.META}unknown{C.RST}"
            print(f"  {C.SECONDARY}{shown+1:<5}{C.RST} "
                  f"{C.SECONDARY}{mid[:35]:<35}{C.RST} "
                  f"{C.METRICS_D}{fit:>7.0f}{C.RST} {bench_str}")
            shown += 1
        print()

def _cmd_preview_tune(args):
    """Preview weight changes without saving."""
    slot_id = args.preview_tune
    slot_defs = load_slot_defs()
    slot_def = slot_defs.get(slot_id, {})
    if not slot_def:
        print(f"{C.ERROR}unknown slot: {slot_id}{C.RST}", file=sys.stderr)
        return

    overrides = {}
    if args.intel is not None:
        overrides["weight_intelligence"] = args.intel
    if args.speed is not None:
        overrides["weight_speed"] = args.speed
    if args.rel is not None:
        overrides["weight_reliability"] = args.rel
    if args.min_tps is not None:
        overrides["min_tps"] = args.min_tps
    if args.min_ai is not None:
        overrides["min_ai"] = args.min_ai
    if args.max_lat is not None:
        overrides["max_latency_s"] = args.max_lat

    preview_def = {**slot_def, **overrides}

    print()
    print(f"{C.INFO}Preview: {slot_id}{C.RST} ({slot_def.get('label', '')})")
    print(f"{C.META}(not saved — run with --tune to apply){C.RST}")
    print()
    print(f"  {C.INFO_D}Changed parameters:{C.RST}")
    for k, v in overrides.items():
        old = slot_def.get(k, "—")
        print(f"    {C.SECONDARY}{k:<25}: {C.METRICS}{old} → {v}{C.RST}")
    print()
    print(f"  {C.INFO_D}Full preview definition:{C.RST}")
    for k, v in preview_def.items():
        print(f"    {C.SECONDARY}{k:<25}: {v}")

def _cmd_tune(args):
    """Apply weight changes to slot_definitions.yaml."""
    slot_id = args.tune
    slot_defs = load_slot_defs()
    slot_def = slot_defs.get(slot_id, {})
    if not slot_def:
        print(f"{C.ERROR}unknown slot: {slot_id}{C.RST}", file=sys.stderr)
        return

    if args.intel is not None:
        slot_def["weight_intelligence"] = args.intel
    if args.speed is not None:
        slot_def["weight_speed"] = args.speed
    if args.rel is not None:
        slot_def["weight_reliability"] = args.rel
    if args.min_tps is not None:
        slot_def["min_tps"] = args.min_tps
    if args.min_ai is not None:
        slot_def["min_ai"] = args.min_ai
    if args.max_lat is not None:
        slot_def["max_latency_s"] = args.max_lat

    slot_defs[slot_id] = slot_def
    SLOTS_FILE.write_text(yaml.safe_dump(slot_defs, sort_keys=False))

    print(f"{C.SUCCESS}tuned {slot_id}{C.RST}")
    if args.note:
        print(f"  {C.META}{args.note}{C.RST}")
    print(f"  {C.INFO}Run 'model-scan' to see updated rankings.{C.RST}")

def _cmd_update_benchmarks():
    """Fetch latest benchmark data from web sources."""
    print(f"{C.INFO}Updating benchmark data from web...{C.RST}")
    print(f"{C.META}(manual update not yet automated — using cached benchmarks.json){C.RST}")
    benchmarks = _load_benchmarks()
    updated = benchmarks.get("updated_at", "unknown")
    sources = benchmarks.get("sources", [])
    print(f"  {C.SECONDARY}Cached data from: {updated}{C.RST}")
    print(f"  {C.SECONDARY}Sources: {', '.join(sources)}{C.RST}")
    models = len(benchmarks.get("swe_verified", {}))
    print(f"  {C.SUCCESS}SWE-Verified models: {models}{C.RST}")
# ──────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="model-scan v4 — Hermes-aware model diagnostic panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--providers", help="comma-separated provider filter")
    p.add_argument("--slot", help="show only one Hermes slot's candidates (e.g. R1_primary)")
    p.add_argument("--by", default="tier",
                  choices=["tier", "fitness", "tps", "latency", "ai", "composite"],
                  help="appendix sort order (default: tier)")
    p.add_argument("--concurrency", type=int, default=8,
                  help="parallel probes (default: 8)")
    p.add_argument("--refresh-aa", action="store_true",
                  help="force AA cache refresh")
    p.add_argument("--rehabilitate", metavar="MODEL_KEY",
                  help="remove a model from the permanent-skip list")
    p.add_argument("--clear-cache", action="store_true",
                  help="clear all caches and bad-list")
    p.add_argument("--no-incumbent", action="store_true", help="skip incumbent panel")
    p.add_argument("--no-slots", action="store_true", help="skip per-slot view")
    p.add_argument("--no-appendix", action="store_true", help="skip flat appendix")
    p.add_argument("--snapshot", action="store_true",
                  help="show incumbent panel from cache only (no probes, instant)")
    p.add_argument("--patch-hermes", action="store_true",
                  help="generate hermes config patch with best model replacements")
    p.add_argument("--json", action="store_true", help="emit JSON to stdout")
    p.add_argument("--analyze-history", metavar="SLOT",
                  help="show historical patterns for a slot (e.g. R1_primary)")
    p.add_argument("--rank-vs-benchmark", action="store_true",
                  help="compare slot rankings against benchmark data")
    p.add_argument("--tune", metavar="SLOT",
                  help="tune slot weights (use with --intel, --speed, --rel, --min-tps, --min-ai)")
    p.add_argument("--preview-tune", metavar="SLOT",
                  help="preview weight changes without saving")
    p.add_argument("--intel", type=float, metavar="FLOAT",
                  help="weight_intelligence (0-1)")
    p.add_argument("--speed", type=float, metavar="FLOAT",
                  help="weight_speed (0-1)")
    p.add_argument("--rel", type=float, metavar="FLOAT",
                  help="weight_reliability (0-1)")
    p.add_argument("--min-tps", type=int, metavar="N",
                  help="min_tps threshold")
    p.add_argument("--min-ai", type=int, metavar="N",
                  help="min_ai threshold")
    p.add_argument("--max-lat", type=float, metavar="SEC",
                  help="max_latency_s")
    p.add_argument("--note", type=str, default="",
                  help="note for weight experiment log")
    p.add_argument("--update-benchmarks", action="store_true",
                  help="refresh benchmark data from web sources")
    p.add_argument("--gold-standard", action="store_true",
                  help="generate gold standard config patch with reasoning traces")
    p.add_argument("--cpmr", action="store_true",
                  help="evaluate CPMR (gold standard vs automated)")
    p.add_argument("--score-engine", action="store_true",
                  help="use multi-axis scoring engine for slot ranking")
    p.add_argument("--optimize", action="store_true",
                  help="run auto-optimization loop (grid search on weights)")
    p.add_argument("--free-mode", action="store_true",
                  help="only probe and evaluate free models (uses free_model_whitelist.json)")
    p.add_argument("--eval-mode", choices=["cost_basis", "free", "all"], default=None,
                  help="override slot eval_mode for this run")
    p.add_argument("--refresh-free", action="store_true",
                  help="refresh free-model whitelist from providers")
    p.add_argument("--audit", action="store_true",
                  help="run independent audit against verified benchmarks")
    p.add_argument("--tui", action="store_true",
                  help="launch Textual terminal UI")
    p.add_argument("--refine", action="store_true",
                  help="run iterative refinement pipeline (hermes heartbeat)")
    p.add_argument("--refine-apply", action="store_true",
                  help="run refinement and apply config changes")
    p.add_argument("--analyze", action="store_true",
                  help="run multi-source analysis (cross-ref AA + PinchBench + models.dev)")
    p.add_argument("--refine-analysis", action="store_true",
                  help="run 4-pass deliberative refinement on analysis data")
    p.add_argument("--popularity", action="store_true",
                  help="refresh and show model popularity scores (HF downloads)")
    p.add_argument("--config-snapshot", action="store_true",
                  help="snapshot current config for drift tracking")

    args = p.parse_args()

    if args.config_snapshot:
        try:
            from config_tracker import main as snap_main
            snap_main()
            return
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} config_tracker not available: {e}{C.RST}")
            return

    if args.refine_analysis:
        try:
            from analysis.refinement import main as _refine_main
            _refine_main()
            return
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} refinement engine not available: {e}{C.RST}")
            return

    if args.popularity:
        try:
            from analysis.popularity import refresh
            scores = refresh()
            print(f"\n  {C.METRICS}Popularity Scores (0-100):{C.RST}")
            for mid, data in sorted(scores.items(), key=lambda x: -x[1]["popularity"]):
                pop = data["popularity"]
                bar = "█" * int(pop / 5) + "░" * (20 - int(pop / 5))
                print(f"    {C.SUCCESS if pop > 50 else C.INFO}{mid:<30s}{C.RST} {bar} {pop}")
            return
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} popularity module not available: {e}{C.RST}")
            return

    if args.snapshot:
        try:
            from config_tracker import main as snap_main
            snap_main()
            return
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} config_tracker not available: {e}{C.RST}")
            return

    # Standalone commands that exit immediately
    if args.update_benchmarks:
        _cmd_update_benchmarks()
        return

    if args.clear_cache:
        for f in (AA_CACHE, BAD_MODELS, RESULTS_FILE, DATABASE_FILE):
            if f.exists():
                f.unlink()
                print(f"removed {f}")
        return

    if args.analyze_history:
        _cmd_analyze_history(args)
        return

    if args.rank_vs_benchmark:
        _cmd_rank_vs_benchmark(args)
        return

    if args.preview_tune:
        _cmd_preview_tune(args)
        return

    if args.tune:
        _cmd_tune(args)
        return

    if args.gold_standard:
        # Import and run gold standard generator
        try:
            from gold_standard import main as gs_main
            sys.exit(gs_main())
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} gold_standard.py not available: {e}{C.RST}")
            return

    if args.cpmr:
        try:
            from cpmr import main as cpmr_main
            sys.exit(cpmr_main())
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} cpmr.py not available: {e}{C.RST}")
            return

    if args.refresh_free:
        refresh_free_whitelist()
        return

    if args.optimize:
        try:
            from optimize import main as opt_main
            sys.exit(opt_main())
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} optimize.py not available: {e}{C.RST}")
            return

    if args.audit:
        try:
            from audit import main as audit_main
            sys.exit(audit_main())
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} audit.py not available: {e}{C.RST}")
            return

    if args.tui:
        try:
            from tui import main as tui_main
            tui_main()
            return
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} tui.py not available: {e}{C.RST}")
            return

    if args.refine or args.refine_apply:
        try:
            from refine import main as refine_main
            import sys as _sys
            _sys.argv = [_sys.argv[0]]
            if args.refine_apply:
                _sys.argv.append("--apply")
            refine_main()
            return
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} refine.py not available: {e}{C.RST}")
            return

    if args.analyze:
        try:
            from analysis import run_full_analysis as _run_analysis
            result = _run_analysis()
            # Print summary
            top = result.get("top_by_composite", [])[:5]
            print(f"\n  {C.METRICS}Top by Composite:{C.RST}")
            for i, m in enumerate(top):
                print(f"    {C.ACCENT}#{i+1}{C.RST} {m['model_id']:<40s} {C.SUCCESS}{m['composite']}{C.RST}")
            
            frontier = result.get("pareto_frontier", [])
            print(f"  {C.METRICS}Pareto frontier:{C.RST} {len(frontier)} optimal points")
            
            eq = result.get("price_intelligence_equilibrium", {})
            ss = eq.get("sweet_spot", {})
            if ss.get("cost"):
                print(f"  {C.METRICS}Price sweet spot:{C.RST} ${ss['cost']}/M ({ss['model']})")
            
            clusters = result.get("capability_clusters", {})
            for name, models in sorted(clusters.items()):
                print(f"  {C.INFO}{name}:{C.RST} {len(models)} models")
            
            return
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} analysis engine not available: {e}{C.RST}")
            return

    if args.refine_analysis:
        try:
            from analysis.refinement import main as _refine_main
            _refine_main()
            return
        except ImportError as e:
            print(f"  {C.ERROR}{C.CROSS} refinement engine not available: {e}{C.RST}")
            return

    if args.rehabilitate:
        if rehabilitate(args.rehabilitate):
            print(f"{C.SUCCESS}rehabilitated:{C.RST} {args.rehabilitate}")
        else:
            print(f"{C.ERROR}not in skip list:{C.RST} {args.rehabilitate}")
        return

    # Snapshot mode - load from cache, no API calls
    if args.snapshot:
        if not RESULTS_FILE.exists():
            print(f"{C.ERROR}No cached results — run without --snapshot first{C.RST}", file=sys.stderr)
            sys.exit(1)
        history = json.loads(RESULTS_FILE.read_text())
        if not history:
            print(f"{C.ERROR}No cached results{C.RST}", file=sys.stderr)
            sys.exit(1)
        last = history[-1]
        results = last.get("results", [])
        slot_defs = load_slot_defs()
        hermes_slots = parse_hermes_slots()
        proxy_tiers = parse_proxy_tiers()
        dossiers = []
        for r in results:
            d = Dossier(
                provider=r.get("provider","unknown"),
                model=r.get("model",""),
                api_model=r.get("api_model",""),
                accessible=r.get("accessible", False),
                latency_s=r.get("latency_s", 0),
                tps=r.get("tps", 0),
                reliability=r.get("reliability", 0),
                has_tools=r.get("has_tools", False),
                fail_class=r.get("fail_class",""),
                http_status=r.get("http_status", 0),
                ai_index=r.get("ai_index"),
                ai_coding=r.get("ai_coding"),
                ai_math=r.get("ai_math"),
                aa_provenance="snapshot",
                arch=r.get("arch","unknown"),
                total_b=r.get("total_b",0),
                active_b=r.get("active_b",0),
                has_vision_capability=r.get("has_vision_capability",False),
                price_blended=r.get("price_blended"),
                ctx_k=r.get("ctx_k"),
                tier=r.get("tier","—"),
                composite=r.get("composite",0),
                qualified_slots=r.get("qualified_slots",[]),
                slot_fitness=r.get("slot_fitness",{}),
                is_incumbent_for=r.get("is_incumbent_for",[]),
                usage_count=r.get("usage_count",0),
                benchmark_swe_verified=r.get("benchmark_swe_verified"),
                ocgo_budget_score=r.get("ocgo_budget_score"),
                ocgo_budget_tier=r.get("ocgo_budget_tier"),
            )
            dossiers.append(d)
        scan_duration = last.get("duration_s", 0)
        n_hermes = len(hermes_slots)
        print()
        print(f"{C.INFO}{C.ARROW} model-scan --snapshot{C.RST}  {C.PRIMARY}{len(dossiers)} cached models{C.RST}  {C.SECONDARY}{n_hermes} slots{C.RST}  {C.META}{scan_duration:.1f}s{C.RST}")
        print(f"  {C.META}({last.get('scanned_at','')[:19]}){C.RST}")
        sys.stdout.flush()
        render_incumbent_panel(dossiers, hermes_slots, proxy_tiers, slot_defs)
        sys.stdout.flush()
        accessible = sum(1 for d in dossiers if d.accessible)
        healthy = sum(1 for d in dossiers if d.reliability >= 0.99)
        degraded = sum(1 for d in dossiers if 0.5 <= d.reliability < 0.99)
        dead = sum(1 for d in dossiers if d.reliability < 0.5)
        print()
        width = 120
        print(f"{C.SECONDARY}{C.HRULE * width}{C.RST}")
        parts = []
        if healthy:
            parts.append(f"{C.SUCCESS}{C.CHECK} {healthy} healthy{C.RST}")
        if degraded:
            parts.append(f"{C.WARN}{C.TRI} {degraded} degraded{C.RST}")
        if dead:
            parts.append(f"{C.ERROR}{C.CROSS} {dead} dead{C.RST}")
        print("  ".join(parts))
        print(f"  {C.META}(snapshot from cache — {last.get('scanned_at','')[:19]}){C.RST}")
        print(f"  {C.META}run without --snapshot to re-probe all providers{C.RST}")
        sys.exit(0)

    # Patch hermes mode
    if args.patch_hermes:
        if not RESULTS_FILE.exists():
            print("No cached results — run without --patch-hermes first", file=sys.stderr)
            sys.exit(1)
        history = json.loads(RESULTS_FILE.read_text())
        if not history:
            print("No cached results", file=sys.stderr)
            sys.exit(1)
        last = history[-1]
        results = last.get("results", [])
        slot_defs = load_slot_defs()
        dossiers = []
        for r in results:
            d = Dossier(
                provider=r.get("provider","unknown"),
                model=r.get("model",""),
                api_model=r.get("api_model",""),
                accessible=r.get("accessible", False),
                latency_s=r.get("latency_s", 0),
                tps=r.get("tps", 0),
                reliability=r.get("reliability", 0),
                has_tools=r.get("has_tools", False),
                fail_class=r.get("fail_class",""),
                http_status=r.get("http_status", 0),
                ai_index=r.get("ai_index"),
                ai_coding=r.get("ai_coding"),
                ai_math=r.get("ai_math"),
                aa_provenance="snapshot",
                arch=r.get("arch","unknown"),
                total_b=r.get("total_b",0),
                active_b=r.get("active_b",0),
                has_vision_capability=r.get("has_vision_capability",False),
                price_blended=r.get("price_blended"),
                ctx_k=r.get("ctx_k"),
                tier=r.get("tier","—"),
                composite=r.get("composite",0),
                qualified_slots=r.get("qualified_slots",[]),
                slot_fitness=r.get("slot_fitness",{}),
                is_incumbent_for=r.get("is_incumbent_for",[]),
                usage_count=r.get("usage_count",0),
                benchmark_swe_verified=r.get("benchmark_swe_verified"),
                ocgo_budget_score=r.get("ocgo_budget_score"),
                ocgo_budget_tier=r.get("ocgo_budget_tier"),
            )
            dossiers.append(d)
        patch = generate_hermes_patch(dossiers, slot_defs)
        print(patch)
        sys.exit(0)

    # Full scan
    sys.exit(asyncio.run(run_scan(args)))

if __name__ == "__main__":
    main()
