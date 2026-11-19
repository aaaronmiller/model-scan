"""One command: python3 -m free_rank [--refresh] [--compare tiers.md] [--copy-to DIR]."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import PACKAGE, load_config
from . import agreement, pipeline, report

OUT = PACKAGE / "out"
ITERATIONS = OUT / "agreement-iterations.jsonl"


def _render_iterations() -> str:
    lines = ["---", "title: Agreement iterations", "---", "", "# Agreement iterations", "",
             "Each run with `--compare` appends one entry to `agreement-iterations.jsonl`; this page is rendered",
             "from it. Only weights, normalisation and cut-offs change between iterations, never per-model rules.", ""]
    for raw in ITERATIONS.read_text().splitlines():
        e = json.loads(raw)
        tau = e.get("kendall_tau")
        lines += [f"## Iteration {e['iteration']} ({e['date']})", "",
                  f"- Change: {e['change']}",
                  f"- Kendall tau {tau if tau is None else round(tau, 3)}, Spearman rho"
                  f" {e.get('spearman_rho') if e.get('spearman_rho') is None else round(e['spearman_rho'], 3)},"
                  f" tiers {e.get('tier_agreement')}, same Tier 1 set {e.get('tier1_same_set')}",
                  f"- Scoring: `{json.dumps(e.get('scoring'))}`",
                  f"- Tier cut-offs: `{json.dumps(e.get('tiers'))}`"]
        if e.get("disagreements"):
            lines.append("- Disagreements: " + "; ".join(e["disagreements"]))
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m free_rank", description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="fetch catalogues and benchmark pages into a dated snapshot first")
    ap.add_argument("--snapshot", help="snapshot date folder to read (default: latest)")
    ap.add_argument("--compare", type=Path, help="reference tier list (Markdown) to measure agreement against")
    ap.add_argument("--change", default="rerun", help="one line describing this iteration, for the iteration log")
    ap.add_argument("--out", type=Path, default=OUT, help="output folder (default: free_rank/out)")
    ap.add_argument("--copy-to", type=Path, help="also copy the outputs into this folder")
    args = ap.parse_args(argv)

    if args.refresh:
        status = pipeline.refresh(args.snapshot)
        failed = [k for k, v in status["status"].items() if v.get("status") != 200]
        print(f"snapshot {status['folder']}: {len(status['status']) - len(failed)} fetched, failed: {failed or 'none'}")
    result = pipeline.build(args.snapshot)
    rec = report.build_records(result)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    written = []

    def write(name, text):
        (out / name).write_text(text)
        written.append(out / name)

    write("ranking.json", json.dumps(rec, indent=2) + "\n")
    write("ranking.md", report.ranking_markdown(rec))
    rows = report.routes_records(rec)
    write("routes-l6.json", json.dumps(rows, indent=2) + "\n")
    write("routes-l6.md", report.routes_markdown(rows, rec["generated_at"]))

    if args.compare:
        c = agreement.compare(result["models"], agreement.parse_reference(args.compare))
        slim = {k: v for k, v in c.items() if k != "rows"}
        write("agreement.json", json.dumps(slim, indent=2, default=str) + "\n")
        write("agreement.md", report.agreement_markdown(c, rec))
        if out == OUT:
            prior = ITERATIONS.read_text().splitlines() if ITERATIONS.exists() else []
            cfg = load_config()
            entry = {"iteration": len(prior) + 1, "date": rec["generated_at"], "change": args.change,
                     "kendall_tau": c["kendall_tau"], "spearman_rho": c["spearman_rho"],
                     "tier_agreement": c["tier_agreement"], "tier1_same_set": c["tier1_same_set"],
                     "scoring": {k: v for k, v in cfg["scoring"].items() if not k.startswith("_")},
                     "tiers": cfg["tiers"]["thresholds"],
                     "disagreements": [f"{d['name']}: reference {d['ref_tier']}, formula {d['tier']}" for d in c["disagreements"]]}
            with ITERATIONS.open("a") as fh:
                fh.write(json.dumps(entry) + "\n")
            write("agreement-iterations.md", _render_iterations())
            written.append(ITERATIONS)
        print(f"agreement: tau {c['kendall_tau']:.3f} rho {c['spearman_rho']:.3f} tiers {c['tier_agreement']}"
              f" same Tier 1 set {c['tier1_same_set']}")

    for m in rec["ranked"]:
        print(f"  T{m['tier']} {m['rank']:>2} {m['score']:.3f} {m['name']}")
    if args.copy_to:
        args.copy_to.mkdir(parents=True, exist_ok=True)
        for p in written:
            shutil.copy2(p, args.copy_to / p.name)
    print("wrote", ", ".join(str(p) for p in written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
