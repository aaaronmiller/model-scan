"""Human table output — D2.7: compact one-screen lane table + --json for agents.

Healthy / throttled / unknown visible in one screen.

Usage:
  python -m registry.table            # human table
  python -m registry.table --json     # machine JSON
  python -m registry.table --lane routine  # filter
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from registry import load_registry, is_unknown

# Status derived from quota + health, per lane binding


def derive_row_status(binding: dict) -> str:
    health = binding.get("provider_health")
    quota = binding.get("quota_state")
    if health in ("unhealthy", "down"):
        return "throttled"
    if health == "degraded":
        return "throttled"
    if is_unknown(health) or is_unknown(quota):
        return "unknown"
    if isinstance(quota, dict) and quota.get("remaining_fraction", 1.0) < 0.15:
        return "throttled"
    if health == "healthy":
        return "healthy"
    return "unknown"


STATUS_GLYPH = {"healthy": "✓", "throttled": "⚠", "unknown": "?"}


def build_rows(registry: dict) -> list[dict]:
    rows = []
    for b in registry.get("bindings", []):
        # model rename touches only registry data — table reads model_id from registry
        rows.append({
            "lane": b.get("lane"),
            "binding_id": b.get("binding_id"),
            "provider": b.get("provider"),
            "model_id": b.get("model_id"),
            "adapter_id": b.get("adapter_id"),
            "capacity": b.get("capacity_slots"),
            "price_class": b.get("price_class"),
            "cost_per_task": b.get("observed_cost_per_task"),
            "status": derive_row_status(b),
            "health": b.get("provider_health"),
            "quota": b.get("quota_state"),
        })
    return rows


def render_human(rows: list[dict], lane_filter: str | None = None) -> str:
    if lane_filter:
        rows = [r for r in rows if r["lane"] == lane_filter]
    # sort by lane then healthy first
    order = {"healthy": 0, "throttled": 1, "unknown": 2}
    rows = sorted(rows, key=lambda r: (r["lane"], order.get(r["status"], 9), r["binding_id"]))

    # column widths
    headers = ["LANE", "BINDING", "PROVIDER", "MODEL", "ADAPTER", "CAP", "PRICE", "COST", "STATUS"]
    # format rows
    lines = []
    # header
    lines.append(f"{'LANE':<12} {'BINDING':<18} {'PROVIDER':<14} {'MODEL':<22} {'ADAPTER':<7} {'CAP':<3} {'PRICE':<9} {'COST':<6} {'STATUS':<10}")
    lines.append("-" * 120)
    for r in rows:
        cost = r["cost_per_task"]
        cost_s = f"{cost:.3f}" if isinstance(cost, (int, float)) else "unknown"
        cap = r["capacity"] if not is_unknown(r["capacity"]) else "?"
        status = f"{STATUS_GLYPH.get(r['status'], '?')} {r['status']}"
        lines.append(
            f"{r['lane']:<12} {r['binding_id']:<18} {str(r['provider']):<14} {str(r['model_id']):<22} {str(r['adapter_id']):<7} {str(cap):<3} {str(r['price_class']):<9} {cost_s:<6} {status:<10}"
        )
    # summary line
    counts = {"healthy": 0, "throttled": 0, "unknown": 0}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines.append("-" * 120)
    lines.append(f"healthy={counts['healthy']} throttled={counts['throttled']} unknown={counts['unknown']}  (✓=healthy ⚠=throttled ?=unknown)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Registry lane table")
    p.add_argument("--json", action="store_true", help="machine JSON output")
    p.add_argument("--lane", type=str, default=None, help="filter by lane")
    p.add_argument("--registry", type=str, default=None, help="path to registry.json")
    args = p.parse_args(argv)

    reg_path = Path(args.registry) if args.registry else None
    if reg_path:
        reg = json.loads(Path(reg_path).read_text())
    else:
        reg = load_registry()

    rows = build_rows(reg)
    if args.lane:
        rows = [r for r in rows if r["lane"] == args.lane]

    if args.json:
        json.dump({"registry_version": reg.get("registry_version"), "generated_at": reg.get("generated_at"), "rows": rows}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_human(rows) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
