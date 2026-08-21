"""Command line entry point for the quota-aware routing pipeline.

Subcommands:

    refresh     recompute provider quota from recorded spend and observations
    resolve     resolve the slot grid and print the redirect table
    publish     refresh, resolve, and write gateway override config
    utilization report how fully each budget window is being used
    preflight   report exactly what is missing before a gateway can run

Everything is offline. No subcommand makes a provider request, starts a
service, or writes a credential. ``preflight`` reports what a human must
authorize; it never performs those steps itself.

Run with ``python3 gateway_cli.py <subcommand>``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import adaptive_limiter as al
import gateway_bridge as gb
import quota_meter as qm
import slot_grid as sg
import slot_resolver as sr
from gateway_rank_map import RankMapRejected, build_rank_map, validate_rank_map
from routing_snapshot import RoutingSnapshotRejected, validate_gateway_snapshot

# The Claude Code grid, as vendor model plus effort pairs. Vendor ids are family
# tokens so a version bump does not break the mapping.
DEFAULT_PAIRS: tuple[tuple[str, str | None], ...] = (
    ("claude-haiku-4-5", None),
    ("claude-sonnet-5", "low"),
    ("claude-sonnet-5", "medium"),
    ("claude-sonnet-5", "high"),
    ("claude-sonnet-5", "xhigh"),
    ("claude-opus-5", "low"),
    ("claude-opus-5", "medium"),
    ("claude-opus-5", "high"),
    ("claude-opus-5", "xhigh"),
    ("claude-opus-5", "max"),
    ("claude-fable-5", "low"),
    ("claude-fable-5", "medium"),
    ("claude-fable-5", "high"),
    ("claude-fable-5", "xhigh"),
    ("claude-fable-5", "max"),
)

LITELLM_CONFIG_CANDIDATES = (
    Path.home() / ".litellm" / "hermes-gateway.yaml",
    Path.home() / "scripts" / "hermes-gateway.yaml",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _load_snapshot(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: could not read snapshot {path}: {exc}", file=sys.stderr)
        return {}


def _load_rank_document(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        raw = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _validate_gateway_snapshot(snapshot: Mapping[str, Any], *, now: datetime) -> None:
    try:
        validate_gateway_snapshot(snapshot, now=now)
    except RoutingSnapshotRejected as exc:
        raise RankMapRejected(str(exc)) from exc


def cmd_refresh(args: argparse.Namespace) -> int:
    payload = gb.refresh_quota(
        spend_path=args.spend,
        ledger_path=args.ledger,
        quota_path=args.quota,
        now=_utcnow(),
    )
    limiter = al.AdaptiveLimiter.load(args.limits)
    inferred = [r for r in limiter.quota_readings(now=_utcnow()) if r.is_known()]
    if inferred:
        merged = dict(payload)
        for provider, state in qm.build_provider_quota(inferred).items():
            merged.setdefault(provider, state)
        qm.write_provider_quota(merged, args.quota)
        payload = merged

    if not payload:
        print("no quota state: nothing recorded yet, and nothing was invented")
        return 0
    for provider, state in sorted(payload.items()):
        print(
            f"{provider:<16} remaining={state['remaining_fraction']:.4f} "
            f"unit={state.get('unit', '?')} source={state.get('source', '?')}"
        )
    return 0


def _resolve(args: argparse.Namespace) -> tuple[dict[str, str], dict[str, sr.Resolution]]:
    snapshot = _load_snapshot(args.snapshot)
    now = _utcnow()
    _validate_gateway_snapshot(snapshot, now=now)
    ranks = validate_rank_map(
        _load_rank_document(args.ranks), snapshot, now=now,
    )
    if args.quota and Path(args.quota).expanduser().exists():
        from routing_snapshot import load_provider_quota

        snapshot["provider_quota"] = load_provider_quota(args.quota)
    return gb.build_redirect_table(
        snapshot,
        DEFAULT_PAIRS,
        candidate_ranks=ranks,
        now=now,
    )


def cmd_resolve(args: argparse.Namespace) -> int:
    try:
        table, resolutions = _resolve(args)
    except RankMapRejected as exc:
        print(f"input rejected: {exc}")
        return 1

    print(f"{'SLOT':<20} {'MODE':<10} {'FLOOR':<6} RESOLVED TO")
    print("-" * 74)
    for slot in sg.SLOTS:
        res = resolutions.get(slot.slot_id)
        target = res.chosen.get("api_model") if (res and res.resolved) else "(vendor default)"
        print(f"{slot.slot_id:<20} {slot.eval_mode:<10} {slot.min_rank:<6} {target}")

    coverage = sg.coverage(resolutions)
    print(f"\ncoverage {coverage.resolved}/{coverage.total}")
    if coverage.unresolved:
        print("unresolved (these keep the vendor default):")
        for slot_id in coverage.unresolved:
            res = resolutions.get(slot_id)
            reasons = sorted({e.reason for e in res.excluded}) if res else []
            print(f"  {slot_id}: {', '.join(reasons) or 'no candidates'}")
    print(f"\nredirects: {len(table)}")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    cmd_refresh(args)
    try:
        table, resolutions = _resolve(args)
    except RankMapRejected as exc:
        print(f"input rejected: {exc}")
        return 1
    if not table:
        print("\nno redirects to publish")
        return 0
    providers = gb.redirect_provider_map(
        resolutions,
        sg.alias_table(DEFAULT_PAIRS),
    )
    try:
        target = gb.write_litellm_overrides(
            table,
            args.out,
            provider_by_alias=providers,
        )
    except ValueError as exc:
        print(f"projection rejected: {exc}")
        return 1
    print(f"\nwrote {len(table)} redirect(s) to {target}")
    print("this file is for a human or gateway to merge; nothing was applied")
    return 0


def cmd_rank_map(args: argparse.Namespace) -> int:
    snapshot = _load_snapshot(args.snapshot)
    try:
        _validate_gateway_snapshot(snapshot, now=_utcnow())
        raw = _load_rank_document(args.rank_input)
        if not args.ranks or not args.evidence_ref or not args.evidence_sha256:
            raise RankMapRejected("--ranks, --evidence-ref, and --evidence-sha256 are required")
        document = build_rank_map(
            raw,
            snapshot,
            generated_at=_utcnow().isoformat().replace("+00:00", "Z"),
            evidence_ref=args.evidence_ref,
            evidence_sha256=args.evidence_sha256,
        )
    except RankMapRejected as exc:
        print(f"input rejected: {exc}")
        return 1
    target = Path(args.ranks).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote provenance-bound rank map to {target}")
    return 0


def cmd_utilization(args: argparse.Namespace) -> int:
    rows = gb.utilization_report(spend_path=args.spend, now=_utcnow())
    if not rows:
        print("no budget windows configured")
        return 0
    print(f"{'PROVIDER':<16} {'WINDOW':<8} {'SPENT':>10} {'PACE':>8} {'WASTE':>8}")
    print("-" * 56)
    for row in rows:
        print(
            f"{row['provider']:<16} {row['window']:<8} "
            f"{row['spent']:>10.4f} {row['pace']:>+8.3f} {row['projected_waste'] * 100:>7.1f}%"
        )
    print("\npace: positive means burning faster than the clock.")
    print("waste: fraction expected to expire unused at the current rate.")
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    """Report what is missing before a gateway can run. Changes nothing."""

    checks: list[tuple[str, bool, str]] = []

    config = next((p for p in LITELLM_CONFIG_CANDIDATES if p.exists()), None)
    checks.append(("litellm config present", config is not None, str(config or "not found")))

    binary = shutil.which("litellm") or str(Path.home() / ".litellm/venv/bin/litellm")
    has_binary = Path(binary).exists() if binary else False
    checks.append(("litellm binary installed", has_binary, binary if has_binary else "not found"))

    required_env: list[str] = []
    if config is not None:
        import re

        try:
            required_env = sorted(
                set(re.findall(r"os\.environ/([A-Z_0-9]+)", config.read_text(encoding="utf-8")))
            )
        except OSError:
            required_env = []
    # DATABASE_URL is unset by decision, 2026-07-30: spend history comes from
    # the local ledger and `disable_spend_logs` is true. Reporting it as missing
    # would keep flagging a settled choice as an outstanding blocker.
    spend_logs_disabled = False
    if config is not None:
        try:
            spend_logs_disabled = "disable_spend_logs: true" in config.read_text(encoding="utf-8")
        except OSError:
            spend_logs_disabled = False

    for name in required_env:
        if name == "DATABASE_URL" and spend_logs_disabled:
            checks.append(("env DATABASE_URL", True, "unset by choice; spend logs disabled"))
            continue
        checks.append((f"env {name}", bool(os.environ.get(name)), "set" if os.environ.get(name) else "MISSING"))

    listening = False
    for port in (4000, 8000, 8080):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                listening = True
                checks.append((f"port {port} listening", True, "a service is up"))
                break
    if not listening:
        checks.append(("gateway listening", False, "no service on 4000/8000/8080"))

    quota_path = Path(args.quota).expanduser() if args.quota else qm.PROVIDER_QUOTA_PATH
    checks.append(("provider_quota.json", quota_path.exists(), str(quota_path)))

    spend_path = Path(args.spend).expanduser() if args.spend else None
    from spend_ledger import SPEND_LOG_PATH

    spend_path = spend_path or SPEND_LOG_PATH
    # Absent before any traffic, which is normal rather than a blocker. It is
    # created by the first recorded spend event.
    checks.append((
        "spend ledger",
        True,
        str(spend_path) if spend_path.exists() else "not created yet; appears on first recorded spend",
    ))

    width = max(len(name) for name, _, _ in checks)
    blockers = 0
    for name, ok, detail in checks:
        mark = "OK  " if ok else "MISS"
        if not ok:
            blockers += 1
        print(f"[{mark}] {name:<{width}}  {detail}")

    print()
    if blockers == 0:
        print("preflight clean")
        return 0

    print(f"{blockers} item(s) outstanding.")
    print("\nThese require a human decision and are deliberately not performed here:")
    print("  - setting LITELLM_MASTER_KEY is a credential change")
    print("  - starting a service is a deployment action")
    print("  - DATABASE_URL selects where spend history persists")
    return 1


def _add_shared_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quota", default=None, help="path to provider_quota.json")
    parser.add_argument("--spend", default=None, help="path to spend_log.jsonl")
    parser.add_argument("--ledger", default=None, help="path to quota_ledger.jsonl")
    parser.add_argument("--limits", default=None, help="path to adaptive_limits.json")
    parser.add_argument("--snapshot", default=None, help="path to a routing snapshot json")
    parser.add_argument("--ranks", default=None, help="path to {api_model: ladder_rank} json")
    parser.add_argument("--rank-input", default=None, help="plain {api_model: rank} evidence input for rank-map")
    parser.add_argument("--evidence-ref", default=None, help="immutable evidence reference for rank-map")
    parser.add_argument("--evidence-sha256", default=None, help="sha256:<digest> of rank-map evidence")
    parser.add_argument("--out", default="gateway-overrides.json", help="override output path")


def build_parser() -> argparse.ArgumentParser:
    # Shared options are attached to both the top level and every subcommand, so
    # `gateway_cli refresh --quota x` works as naturally as
    # `gateway_cli --quota x refresh`. Argparse otherwise accepts only the
    # latter, which is not the form anyone reaches for first.
    parser = argparse.ArgumentParser(prog="gateway_cli", description=__doc__)
    _add_shared_options(parser)

    sub = parser.add_subparsers(dest="command", required=True)
    for name, func, help_text in (
        ("refresh", cmd_refresh, "recompute and publish provider quota"),
        ("resolve", cmd_resolve, "resolve the slot grid"),
        ("publish", cmd_publish, "refresh, resolve, and write overrides"),
        ("utilization", cmd_utilization, "report window utilization"),
        ("preflight", cmd_preflight, "report deployment blockers"),
        ("rank-map", cmd_rank_map, "publish a provenance-bound rank map"),
    ):
        s = sub.add_parser(name, help=help_text)
        _add_shared_options(s)
        s.set_defaults(func=func)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
