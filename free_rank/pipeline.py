"""Snapshot, discover, ingest, match and score in one call."""
from __future__ import annotations

from datetime import date as _date

from . import REPO, load_config
from . import discovery, fetch, rank, sources

CFG = load_config()

ADAPTERS = {
    "aa-leaderboard": lambda raw, e, spec: sources.aa_leaderboard(raw, e),
    "aa-coding-agents": lambda raw, e, spec: sources.aa_coding_agents(raw, e),
    "vals-terminal-bench-4": lambda raw, e, spec: sources.vals_table(raw, e, spec["benchmark"]),
    "tbench-leaderboard": lambda raw, e, spec: sources.tbench_board(raw, e, spec["benchmark"]),
    "kilobench": lambda raw, e, spec: sources.kilobench(raw, e, spec["benchmark"]),
}


def refresh(day: str | None = None) -> dict:
    folder = fetch.snapshot_dir(day or _date.today().isoformat())
    status = {}
    for name, spec in CFG["catalogues"].items():
        status["catalogue:" + name] = fetch.fetch("catalogue-" + name, spec["url"], folder)
    for name, spec in CFG["benchmark_sources"].items():
        status["source:" + name] = fetch.fetch("source-" + name, spec["url"], folder)
    return {"folder": str(folder), "status": status}


def build(day: str | None = None) -> dict:
    folder = fetch.snapshot_dir(day)
    notes = []
    routes = []
    for name in CFG["catalogues"]:
        raw, entry = fetch.read("catalogue-" + name, folder)
        if not fetch.ok(entry):
            notes.append(f"catalogue {name}: fetch failed ({entry.get('status')}); its routes are missing")
            continue
        routes += discovery.parse(name, raw)
    models = rank.group_routes(routes)

    identity_obs = []
    for name, spec in CFG["benchmark_sources"].items():
        raw, entry = fetch.read("source-" + name, folder)
        obs = ADAPTERS[name](raw, entry, spec) if fetch.ok(entry) else []
        if not obs and spec.get("fallback_snapshot"):
            path = REPO / spec["fallback_snapshot"]
            obs = sources.aa_snapshot(path, "pinned snapshot")
            notes.append(f"{name}: live page unusable, used {spec['fallback_snapshot']}")
        if not obs:
            notes.append(f"{name}: no observations ({entry.get('status')})")
        identity_obs += obs
    match_log = rank.attach_identity_observations(models, identity_obs)

    live_hosts = {}
    for m in models:
        live_hosts[m.key] = {o["host"] for o in m.observations}
    route_obs = []
    for spec in CFG["evidence_files"]:
        route_obs += sources.evidence_file(spec)
    rank.attach_route_observations(models, route_obs, live_hosts)
    rank.score(models)
    return {"folder": folder, "routes": routes, "models": models, "match_log": match_log, "notes": notes,
            "observation_counts": {"identity": len(identity_obs), "route": len(route_obs)}}
