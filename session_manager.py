"""Concurrent Session Management for model-scan / Hermes.

Provides:
- Session priority queue (active, idle, paused, completed, failed)
- Quota ledger (per-session, per-provider token tracking)
- Preemption logic (idle/low-priority sessions → preempt for high-priority work)
- Provider usage limits (max concurrent sessions per tier)
- Integration with gateway API and dink.py
"""
import json
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "model-scan"
HERMES_DIR = Path.home() / ".hermes"
SESSIONS_DIR = HERMES_DIR / "sessions"
STATE_FILE = CONFIG_DIR / "session_manager_state.json"
QUOTA_DB = CONFIG_DIR / "quota_ledger.db"

# ── Priority / Preemption Configuration ───────────────────────────────

SESSION_PRIORITIES = {
    "hermes_primary": 90,   # Main interactive session
    "claude_code": 80,      # Claude Code coding agent
    "codex": 70,            # OpenAI Codex
    "opencode": 60,         # OpenCode
    "pi_agent": 50,         # Pi agent
    "kiro": 40,             # Kiro (monitoring)
    "batch": 30,            # Batch/background jobs
    "maintenance": 20,      # Maintenance tasks
}

SESSION_STATES = {
    "active": "session is currently running and using provider resources",
    "idle": "session is alive but not actively making API calls",
    "paused": "session was preempted or suspended",
    "completed": "session finished normally",
    "failed": "session terminated with error",
    "zombie": "session crashed with resources still allocated",
}

PROVIDER_CONCURRENCY_LIMITS = {
    "openai": {"S": 3, "A": 5, "B": 10, "C": 20},
    "anthropic": {"S": 2, "A": 4, "B": 8, "C": 15},
    "openrouter": {"S": 5, "A": 10, "B": 20, "C": 40},
    "google": {"S": 3, "A": 5, "B": 10, "C": 20},
    "groq": {"S": 5, "A": 10, "B": 20, "C": 40},
    "deepseek": {"S": 3, "A": 5, "B": 10, "C": 20},
    "kimi": {"S": 2, "A": 4, "B": 8, "C": 15},
    "qwen": {"S": 2, "A": 4, "B": 8, "C": 15},
}

PREEMPTION_CONFIG = {
    "idle_timeout_s": 300,         # Preempt if idle > 5 min
    "low_priority_threshold": 40,  # Sessions below this priority are preemptable
    "max_preemptions_per_cycle": 3,  # Don't preempt too many at once
    "preemption_cooldown_s": 60,   # Wait 1 min between preemption cycles
}


# ═════════════════════════════════════════════════════════════════════════
# Session Discovery
# ═════════════════════════════════════════════════════════════════════════

def discover_sessions(limit: int = 200) -> list[dict]:
    """Scan ~/.hermes/sessions/ and return session metadata.

    Returns sessions sorted by last-modified descending.
    """
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    for entry in sorted(SESSIONS_DIR.iterdir(),
                        key=lambda x: x.stat().st_mtime, reverse=True):
        if not entry.name.endswith(".json"):
            continue
        if entry.name.startswith(".tmp") or entry.name.startswith("."):
            continue

        stats = entry.stat()
        info = {
            "session_id": entry.stem,
            "path": str(entry),
            "modified": datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
            "size_kb": round(stats.st_size / 1024, 1),
            "state": _infer_session_state(entry),
            "priority": 50,  # default
        }

        # Try to parse session metadata
        meta = _parse_session_meta(entry)
        if meta:
            info.update(meta)
            info["program"] = _classify_program(entry.name, meta)
            info["priority"] = SESSION_PRIORITIES.get(info["program"], 50)

        sessions.append(info)

    return sessions[:limit]


def _infer_session_state(path: Path) -> str:
    """Infer session state from filename patterns and content."""
    name = path.stem

    # Try to peek at the file for state info — don't shortcut on size
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            state = data.get("state", data.get("status", ""))
            if state and state.lower() in SESSION_STATES:
                return state.lower()
            # Check for error fields
            if data.get("error") or data.get("exception"):
                return "failed"
            # Check timestamps
            ended = data.get("ended_at") or data.get("closed_at")
            if ended:
                return "completed"
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        pass

    # If recently modified (< 5 min ago), assume active
    age_s = time.time() - path.stat().st_mtime
    try:
        if path.stat().st_size < 100:
            return "completed"
    except OSError:
        pass
    if age_s < 300:
        return "active"
    elif age_s < 3600:
        return "idle"

    return "completed"


def _parse_session_meta(path: Path) -> dict | None:
    """Extract agent, model, turn_count from session JSON."""
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return None
        return {
            "agent": data.get("agent", data.get("name", "")),
            "model": data.get("model", data.get("model_id", "")),
            "turn_count": data.get("turn_count", data.get("turns", 0)),
            "provider": data.get("provider", ""),
        }
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


def _classify_program(session_name: str, meta: dict) -> str:
    """Classify a session into a monitored program."""
    # Check session.json agent field
    agent = (meta.get("agent") or "").lower()
    model = (meta.get("model") or "").lower()

    if "codex" in agent or "codex" in session_name:
        return "codex"
    if "claude" in agent and "code" in agent:
        return "claude_code"
    if "opencode" in agent or "ocgo" in agent:
        return "opencode"
    if "pi" in agent or "pi_agent" in agent:
        return "pi_agent"
    if "kiro" in agent or "hermes" in agent:
        return "hermes_primary"
    if "batch" in agent:
        return "batch"

    return "hermes_primary"  # default


# ═════════════════════════════════════════════════════════════════════════
# Quota Ledger
# ═════════════════════════════════════════════════════════════════════════

def init_quota_db():
    """Create/verify the quota ledger database."""
    QUOTA_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(QUOTA_DB))
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS quota_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            model_id TEXT,
            tokens_in INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            cost REAL DEFAULT 0,
            timestamp TEXT NOT NULL,
            state TEXT DEFAULT 'pending',
            UNIQUE(session_id, provider, timestamp)
        );
        CREATE TABLE IF NOT EXISTS session_quota (
            session_id TEXT PRIMARY KEY,
            program TEXT,
            priority INTEGER DEFAULT 50,
            total_tokens_in INTEGER DEFAULT 0,
            total_tokens_out INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0,
            started_at TEXT,
            last_active_at TEXT,
            state TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS provider_slots (
            provider TEXT NOT NULL,
            session_id TEXT NOT NULL,
            slot_tier TEXT DEFAULT 'B',
            allocated_at TEXT,
            PRIMARY KEY (provider, session_id)
        );
        CREATE INDEX IF NOT EXISTS idx_quota_provider ON quota_entries(provider);
        CREATE INDEX IF NOT EXISTS idx_quota_session ON quota_entries(session_id);
    """)
    conn.commit()
    conn.close()


def record_quota_usage(
    session_id: str,
    provider: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost: float = 0.0,
    model_id: str = "",
):
    """Record token usage for a session-provider pair."""
    init_quota_db()
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(str(QUOTA_DB))
    c = conn.cursor()

    # Insert usage entry
    c.execute("""
        INSERT OR REPLACE INTO quota_entries
            (session_id, provider, model_id, tokens_in, tokens_out, cost, timestamp, state)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'recorded')
    """, (session_id, provider, model_id, tokens_in, tokens_out, cost, now))

    # Update session aggregate
    c.execute("""
        INSERT INTO session_quota
            (session_id, total_tokens_in, total_tokens_out, total_cost, last_active_at, state)
        VALUES (?, ?, ?, ?, ?, 'active')
        ON CONFLICT(session_id) DO UPDATE SET
            total_tokens_in = total_tokens_in + ?,
            total_tokens_out = total_tokens_out + ?,
            total_cost = total_cost + ?,
            last_active_at = ?,
            state = 'active'
    """, (session_id, tokens_in, tokens_out, cost, now,
          tokens_in, tokens_out, cost, now))

    conn.commit()
    conn.close()


def get_quota_summary(provider: str | None = None) -> dict:
    """Get quota usage summary, optionally filtered by provider."""
    init_quota_db()
    conn = sqlite3.connect(str(QUOTA_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if provider:
        c.execute("""
            SELECT provider, COUNT(*) as calls,
                   SUM(tokens_in) as total_in, SUM(tokens_out) as total_out,
                   SUM(cost) as total_cost, COUNT(DISTINCT session_id) as sessions
            FROM quota_entries WHERE provider = ?
            GROUP BY provider
        """, (provider,))
    else:
        c.execute("""
            SELECT provider, COUNT(*) as calls,
                   SUM(tokens_in) as total_in, SUM(tokens_out) as total_out,
                   SUM(cost) as total_cost, COUNT(DISTINCT session_id) as sessions
            FROM quota_entries
            GROUP BY provider ORDER BY total_cost DESC
        """)

    rows = c.fetchall()
    conn.close()

    summary = {}
    for r in rows:
        summary[r["provider"]] = {
            "calls": r["calls"],
            "tokens_in": r["total_in"] or 0,
            "tokens_out": r["total_out"] or 0,
            "total_cost": round(r["total_cost"] or 0, 6),
            "sessions": r["sessions"],
        }
    return summary


def get_session_quota(session_id: str) -> dict | None:
    """Get quota details for a specific session."""
    init_quota_db()
    conn = sqlite3.connect(str(QUOTA_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT * FROM session_quota WHERE session_id = ?
    """, (session_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return None

    # Get per-provider breakdown
    c.execute("""
        SELECT provider, COUNT(*) as calls,
               SUM(tokens_in) as in_t, SUM(tokens_out) as out_t,
               SUM(cost) as cost
        FROM quota_entries WHERE session_id = ?
        GROUP BY provider
    """, (session_id,))
    providers = {}
    for pr in c.fetchall():
        providers[pr["provider"]] = {
            "calls": pr["calls"],
            "tokens_in": pr["in_t"] or 0,
            "tokens_out": pr["out_t"] or 0,
            "cost": round(pr["cost"] or 0, 6),
        }

    conn.close()
    return {
        "session_id": row["session_id"],
        "program": row["program"],
        "priority": row["priority"],
        "total_tokens_in": row["total_tokens_in"],
        "total_tokens_out": row["total_tokens_out"],
        "total_cost": round(row["total_cost"] or 0, 6),
        "started_at": row["started_at"],
        "last_active_at": row["last_active_at"],
        "state": row["state"],
        "providers": providers,
    }


# ═════════════════════════════════════════════════════════════════════════
# Provider Slot Allocation
# ═════════════════════════════════════════════════════════════════════════

def allocate_provider_slot(
    session_id: str, provider: str, slot_tier: str = "B"
) -> bool:
    """Allocate a provider slot for a session. Returns False if limit reached."""
    limits = PROVIDER_CONCURRENCY_LIMITS.get(provider,
                                             PROVIDER_CONCURRENCY_LIMITS["openai"])
    max_slots = limits.get(slot_tier, limits.get("B", 10))

    init_quota_db()
    conn = sqlite3.connect(str(QUOTA_DB))
    c = conn.cursor()

    # Count current allocations
    c.execute("""
        SELECT COUNT(*) FROM provider_slots WHERE provider = ?
    """, (provider,))
    current = c.fetchone()[0]

    if current >= max_slots:
        conn.close()
        return False

    # Allocate slot
    now = datetime.now(timezone.utc).isoformat()
    c.execute("""
        INSERT OR REPLACE INTO provider_slots (provider, session_id, slot_tier, allocated_at)
        VALUES (?, ?, ?, ?)
    """, (provider, session_id, slot_tier, now))

    # Update session_quota with tier
    c.execute("""
        UPDATE session_quota SET state = 'active', last_active_at = ?
        WHERE session_id = ?
    """, (now, session_id))

    conn.commit()
    conn.close()
    return True


def release_provider_slot(session_id: str, provider: str):
    """Release a provider slot for a session."""
    init_quota_db()
    conn = sqlite3.connect(str(QUOTA_DB))
    c = conn.cursor()
    c.execute("""
        DELETE FROM provider_slots WHERE provider = ? AND session_id = ?
    """, (provider, session_id))
    conn.commit()
    conn.close()


def get_provider_slot_usage(provider: str | None = None) -> dict:
    """Get current provider slot usage."""
    init_quota_db()
    conn = sqlite3.connect(str(QUOTA_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if provider:
        c.execute("""
            SELECT provider, COUNT(*) as used
            FROM provider_slots WHERE provider = ?
            GROUP BY provider
        """, (provider,))
    else:
        c.execute("""
            SELECT provider, COUNT(*) as used
            FROM provider_slots GROUP BY provider ORDER BY used DESC
        """)

    rows = c.fetchall()
    conn.close()

    result = {}
    for r in rows:
        limits = PROVIDER_CONCURRENCY_LIMITS.get(
            r["provider"], PROVIDER_CONCURRENCY_LIMITS["openai"]
        )
        result[r["provider"]] = {
            "used": r["used"],
            "limits": limits,
            "available": limits.get("B", 10) - r["used"],
        }
    return result


# ═════════════════════════════════════════════════════════════════════════
# Session Priority Queue
# ═════════════════════════════════════════════════════════════════════════

def build_priority_queue() -> list[dict]:
    """Build and sort the session priority queue.

    Returns sessions sorted by (state_weight, priority, last_active).
    Active sessions first, then idle, then paused/completed.
    """
    sessions = discover_sessions(limit=100)

    state_order = {"active": 0, "idle": 1, "paused": 2,
                   "completed": 3, "failed": 4, "zombie": 5}

    def _safe_ts(val: str | None) -> float:
        """Safely parse an ISO timestamp string, returning 0 on failure."""
        if not val:
            return 0
        try:
            return datetime.fromisoformat(val).timestamp()
        except (ValueError, TypeError, AttributeError):
            return 0

    for s in sessions:
        s["state_order"] = state_order.get(s.get("state", "completed"), 99)

    # Sort: active first, then by priority desc, then by most recently modified
    sessions.sort(key=lambda x: (x["state_order"], -x.get("priority", 50),
                                 -_safe_ts(x.get("modified"))))

    return sessions


def has_capacity_for(session_id: str, provider: str, slot_tier: str = "B") -> dict:
    """Check if the system has capacity for a new session on a provider.

    Returns dict with allowed (bool), reason (str), and current_usage details.
    """
    usage = get_provider_slot_usage(provider)
    limits = PROVIDER_CONCURRENCY_LIMITS.get(provider,
                                             PROVIDER_CONCURRENCY_LIMITS["openai"])
    max_slots = limits.get(slot_tier, limits.get("B", 10))
    used = usage.get(provider, {}).get("used", 0)

    if used >= max_slots:
        # Check preemption candidates
        candidates = find_preemption_candidates(provider, count=1)
        if candidates:
            return {
                "allowed": True,
                "reason": f"at capacity ({used}/{max_slots}), can preempt {candidates[0]['session_id']}",
                "preempt_session": candidates[0]["session_id"],
                "current_usage": used,
                "max_slots": max_slots,
            }
        else:
            return {
                "allowed": False,
                "reason": f"provider {provider} at capacity ({used}/{max_slots})",
                "preempt_session": None,
                "current_usage": used,
                "max_slots": max_slots,
            }

    return {
        "allowed": True,
        "reason": "capacity available",
        "preempt_session": None,
        "current_usage": used,
        "max_slots": max_slots,
    }


# ═════════════════════════════════════════════════════════════════════════
# Preemption Logic
# ═════════════════════════════════════════════════════════════════════════

def _safe_ts(val: str | None) -> float:
    """Safely parse an ISO timestamp string, returning 0 on failure."""
    if not val:
        return 0
    try:
        return datetime.fromisoformat(val).timestamp()
    except (ValueError, TypeError, AttributeError):
        return 0


def find_preemption_candidates(
    provider: str,
    count: int = 1,
    min_priority: int | None = None,
) -> list[dict]:
    """Find sessions that could be preempted on a provider.

    Candidates are sessions that are:
    - Idle for > idle_timeout_s
    - Lower priority than the requester
    - Not in a critical state (active + recently used)

    Returns up to `count` candidates sorted by preemption suitability.
    """
    queue = build_priority_queue()
    threshold = min_priority or PREEMPTION_CONFIG["low_priority_threshold"]
    idle_timeout = PREEMPTION_CONFIG["idle_timeout_s"]
    now = time.time()

    candidates = []
    for s in queue:
        if s.get("session_id") == "__main__":
            continue
        if s.get("priority", 50) > threshold:
            continue
        if s.get("state") == "active":
            # Check how long it's been idle
            modified_ts = _safe_ts(s.get("modified"))
            age_s = now - modified_ts
            if age_s < idle_timeout:
                continue

        # Check if this session uses this provider
        q = get_session_quota(s["session_id"])
        if q and "providers" in q:
            if provider not in q["providers"]:
                continue

        candidates.append(s)

    return candidates[:count]


def execute_preemption(session_id: str, reason: str = "capacity") -> bool:
    """Preempt a session — mark it as paused and release its slots.

    Returns True if preemption was successful.
    """
    init_quota_db()
    conn = sqlite3.connect(str(QUOTA_DB))
    c = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()

    # Mark session as paused
    c.execute("""
        UPDATE session_quota SET state = 'paused', last_active_at = ?
        WHERE session_id = ?
    """, (now, session_id))

    # Release all provider slots
    c.execute("""
        DELETE FROM provider_slots WHERE session_id = ?
    """, (session_id,))

    conn.commit()
    conn.close()

    # Record preemption to log
    log_path = CONFIG_DIR / "preemption_log.jsonl"
    entry = {
        "timestamp": now,
        "session_id": session_id,
        "reason": reason,
        "success": True,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return True


# ═════════════════════════════════════════════════════════════════════════
# Session Manager (coordinator)
# ═════════════════════════════════════════════════════════════════════════

class SessionManager:
    """Coordinates session discovery, quota tracking, and preemption."""

    def __init__(self):
        init_quota_db()
        self._state_cache: dict = {}
        self._last_preemption_time: float = 0
        self._load_state()

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                self._state_cache = json.loads(STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                self._state_cache = {}
        else:
            self._state_cache = {}

    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self._state_cache, indent=2))

    def get_active_sessions(self) -> list[dict]:
        """Return all active session summaries."""
        all_sessions = discover_sessions(limit=50)
        return [s for s in all_sessions if s.get("state") == "active"]

    def get_session_summary(self) -> dict:
        """Return a complete session management summary."""
        queue = build_priority_queue()

        active = [s for s in queue if s["state"] == "active"]
        idle = [s for s in queue if s["state"] == "idle"]
        paused = [s for s in queue if s["state"] == "paused"]

        # Aggregate by program
        by_program: dict[str, int] = defaultdict(int)
        for s in queue:
            by_program[s.get("program", "unknown")] += 1

        # Provider usage
        provider_usage = get_provider_slot_usage()

        # Quota summary
        quota_summary = get_quota_summary()

        return {
            "total_sessions": len(queue),
            "active": len(active),
            "idle": len(idle),
            "paused": len(paused),
            "by_program": dict(by_program),
            "provider_slots": provider_usage,
            "quota_summary": quota_summary,
            "preemption_available": self._preemption_available(),
            "top_sessions": queue[:10],
        }

    def _preemption_available(self) -> bool:
        """Check if we're allowed to preempt (cooldown check)."""
        cooldown = PREEMPTION_CONFIG["preemption_cooldown_s"]
        return (time.time() - self._last_preemption_time) > cooldown

    def request_session_slot(
        self,
        session_id: str,
        provider: str,
        slot_tier: str = "B",
        priority: int = 50,
    ) -> dict:
        """Request a session slot, potentially triggering preemption."""
        capacity = has_capacity_for(session_id, provider, slot_tier)

        if capacity["allowed"]:
            allocated = allocate_provider_slot(session_id, provider, slot_tier)
            if allocated:
                self._save_state()
                return {
                    "granted": True,
                    "reason": "slot allocated",
                    "provider": provider,
                    "slot_tier": slot_tier,
                }
            else:
                return {
                    "granted": False,
                    "reason": "allocation failed",
                    "provider": provider,
                }

        # Capacity check — try preemption
        if (capacity.get("preempt_session")
                and self._preemption_available()):
            preempt_id = capacity["preempt_session"]
            success = execute_preemption(preempt_id,
                                         reason=f"slot needed for {session_id}")
            if success:
                self._last_preemption_time = time.time()
                # Retry allocation
                allocated = allocate_provider_slot(session_id, provider, slot_tier)
                if allocated:
                    self._save_state()
                    return {
                        "granted": True,
                        "reason": f"preempted {preempt_id}",
                        "provider": provider,
                        "preempted": preempt_id,
                    }
                else:
                    return {
                        "granted": False,
                        "reason": f"preempted {preempt_id} but allocation failed",
                        "provider": provider,
                    }

        return {
            "granted": False,
            "reason": capacity.get("reason", "no capacity available"),
            "provider": provider,
        }

    def release_session(self, session_id: str):
        """Release all resources for a session."""
        quota = get_session_quota(session_id)
        if quota and "providers" in quota:
            for provider in quota["providers"]:
                release_provider_slot(session_id, provider)
        self._save_state()

    def get_recommendations(self) -> list[dict]:
        """Return actionable recommendations for session management."""
        recommendations = []
        queue = build_priority_queue()
        now = time.time()

        # Check for zombie sessions (older than 24h, still marked active)
        for s in queue:
            if s.get("state") == "active":
                modified_ts = _safe_ts(s.get("modified"))
                age_hours = (now - modified_ts) / 3600
                if age_hours > 24:
                    recommendations.append({
                        "type": "zombie_detected",
                        "session_id": s["session_id"],
                        "message": f"Session active for {age_hours:.0f}h — likely zombie",
                    })

        # Check for preemption opportunities
        provider_usage = get_provider_slot_usage()
        for provider, usage in provider_usage.items():
            limits = PROVIDER_CONCURRENCY_LIMITS.get(provider,
                                                     PROVIDER_CONCURRENCY_LIMITS["openai"])
            max_slots = limits.get("B", 10)
            used = usage.get("used", 0)
            if used >= max_slots * 0.8:
                candidates = find_preemption_candidates(provider, count=2)
                if candidates:
                    recommendations.append({
                        "type": "preemption_suggested",
                        "provider": provider,
                        "usage": f"{used}/{max_slots}",
                        "candidates": [c["session_id"] for c in candidates],
                        "message": f"{provider} at {used}/{max_slots} — {len(candidates)} preemption candidates",
                    })

        return recommendations
