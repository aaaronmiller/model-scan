#!/usr/bin/env python3
"""Classify stalled batch items without ever letting a model type a quote.

The archive holds 252 ``verifier_disagreement`` observations, every one of them
"verbatim not found in source turn". That failure is structural: a model asked
to reproduce a span will normalise punctuation, fix a typo, or trim whitespace,
and the merge gate then rejects a verdict that was substantively correct.

The corpus's own retrospective proposed the fix: deterministic span-offset
capture. This implements it. Each source turn is split into numbered segments
and the model returns a **segment index**, never text. The verbatim is then
sliced from the source by index, so it is exact by construction and cannot fail
the provenance gate.

The model still supplies judgement: the intent type, a one-line statement, the
scope, and which segment carries the intent. It just never transcribes.

Writes only a verdicts JSON file. It does not touch ``archaeology.db``; the
pipeline's own ``05-merge.py`` remains the only sanctioned writer.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

VALID_TYPES = (
    "directive.feature",
    "directive.constraint",
    "question",
    "bugreport",
    "correction.behavior",
    "correction.factual",
    "meta.harness",
    "preference.style",
    "noise",
)

MIN_SEGMENT_CHARS = 12
MAX_SEGMENTS = 40

PROMPT = """You classify a user's prompt from a software project's history.

Return ONLY a JSON object, no prose, no code fence:
{"type": "<type>", "statement": "<one sentence>", "segment": <int>, "scope": "<scope>"}

type must be exactly one of:
  directive.feature     asks for something to be built or changed
  directive.constraint  imposes a rule, limit, or prohibition
  question              asks for information
  bugreport             reports something broken, with evidence
  correction.behavior   corrects how the agent is working
  correction.factual    corrects a stated fact
  meta.harness          about the tooling or agent itself
  preference.style      a stated preference of taste or format
  noise                 no durable intent

Classify as "noise" whenever the turn is any of these. This is the most common
correct answer and under-using it pollutes the record:
  - a slash command or its echo, e.g. text containing <command-name>,
    <command-message>, <command-args>, or a bare /word invocation
  - a system or tool message, a task notification, or an interruption notice
  - pasted terminal output, logs, stack traces, or a transcript with no request
  - continuation filler: "continue", "go on", "ok", "yes", "thanks"
  - a fragment too short or garbled to carry a durable instruction

scope must be one of: project, feature, global, file

statement: one sentence, imperative, in the user's own framing. No preamble.
It MUST be supported by the segment you select. If the best segment is a
question, the type is "question" and the statement says what was asked. Do not
invent a directive that the selected segment does not state.

segment: the index of the ONE numbered segment below that best carries the
intent. Choose a segment that is substantive; never choose a segment that is
only a greeting or fragment. If type is "noise", use segment 0.

If you are unsure whether a turn carries durable intent, answer "noise".

Do NOT quote or retype any text. Only give the index.

SEGMENTS:
{segments}
"""


NOISE_MARKERS = (
    "<command-name>", "<command-message>", "<command-args>",
    "<task-notification>", "<local-command-stdout>",
    "[request interrupted", "system message:", "caveat: the messages below",
)


def is_structural_noise(text: str) -> bool:
    """Detect non-turns deterministically, before any model call.

    A slash-command echo or a task notification is not a judgement call. Sending
    it to a model wastes a call and invites a spurious classification, which is
    how `<command-name>/status</command-name>` became a "question" on the first
    pass.
    """

    low = (text or "").strip().lower()
    if len(low) < 15:
        return True
    if any(marker in low for marker in NOISE_MARKERS):
        return True
    # A bare slash command with nothing else.
    if low.startswith("/") and len(low.split()) <= 3:
        return True
    return False


def split_segments(text: str) -> list[str]:
    """Split a turn into candidate verbatim spans, longest-lived first.

    Sentence-ish splitting on terminators and newlines. Segments shorter than
    the merge's practical floor are dropped, because an eight-character span is
    not evidence of anything.
    """

    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    segments = [p.strip() for p in parts if len(p.strip()) >= MIN_SEGMENT_CHARS]
    if not segments and (text or "").strip():
        segments = [text.strip()]
    return segments[:MAX_SEGMENTS]


# Headless invocations. Both CLIs run non-interactively; the bare `kilo`
# command launches a TUI and must never be used here.
#
# Model preference, per the 2026-07-30 directive: deepseek-v4-flash first, then
# the other capable free models. All are zero marginal cost.
FALLBACK_MODELS = (
    "opencode/deepseek-v4-flash-free",
    "kilo/stepfun/step-3.7-flash:free",
    "kilo/nvidia/nemotron-3-ultra-550b-a55b:free",
    "kilo/inclusionai/ling-3.0-flash:free",
    "opencode/minimax-m3",
    "opencode/laguna-s-2.1-free",
)

ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def run_model(prompt: str, model: str, timeout: int) -> str:
    """Run a prompt headlessly on the CLI that owns the model.

    A ``kilo/`` prefix routes to the kilo CLI, which takes the message as a
    positional and emits JSON events; anything else routes to opencode. Both are
    non-interactive.
    """

    if model.startswith("kilo/"):
        cmd = ["kilo", "run", "-m", model[len("kilo/"):], "--format", "json", prompt]
    else:
        cmd = ["opencode", "run", "--model", model, prompt]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return ANSI.sub("", proc.stdout or "")


def parse_reply(raw: str) -> dict[str, Any] | None:
    """Pull the first JSON object out of a model reply."""

    if not raw:
        return None
    # Strip ANSI and any surrounding chatter.
    clean = re.sub(r"\x1b\[[0-9;]*m", "", raw)
    match = re.search(r"\{.*?\}", clean, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def classify_item(item: dict, model: str, timeout: int) -> dict[str, Any]:
    """Classify one item, returning a merge-ready verdict."""

    text = item.get("text", "")
    if is_structural_noise(text):
        return {"id": item["id"], "type": "noise", "_via": "structural"}

    segments = split_segments(text)
    if not segments:
        return {"id": item["id"], "type": "noise", "_via": "structural"}

    listing = "\n".join(f"[{i}] {s}" for i, s in enumerate(segments))
    reply = parse_reply(run_model(PROMPT.replace("{segments}", listing), model, timeout))

    if not reply:
        # A failed call is not a classification. Leaving it pending is honest;
        # guessing "noise" would silently discard a real directive.
        return {"id": item["id"], "type": None, "_error": "no parseable reply"}

    vtype = str(reply.get("type") or "").strip()
    if vtype not in VALID_TYPES:
        return {"id": item["id"], "type": None, "_error": f"bad type {vtype!r}"}
    if vtype == "noise":
        return {"id": item["id"], "type": "noise"}

    try:
        index = int(reply.get("segment", -1))
    except (TypeError, ValueError):
        index = -1
    if not 0 <= index < len(segments):
        index = max(range(len(segments)), key=lambda i: len(segments[i]))

    statement = " ".join(str(reply.get("statement") or "").split())
    if not statement:
        return {"id": item["id"], "type": None, "_error": "empty statement"}

    scope = str(reply.get("scope") or "project").strip()
    if scope not in ("project", "feature", "global", "file"):
        scope = "project"

    return {
        "id": item["id"],
        "type": vtype,
        "statement": statement[:400],
        # Sliced from the source by index. Exact by construction.
        "verbatim": segments[index],
        "scope": scope,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ia_classify", description=__doc__)
    ap.add_argument("--items", required=True, help="output of ia_repair.py extract")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="opencode/deepseek-v4-flash-free")
    ap.add_argument("--fallback", action="store_true",
                    help="on an unparseable reply, retry on the next free model")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    args = ap.parse_args(argv)

    payload = json.loads(Path(args.items).expanduser().read_text(encoding="utf-8"))
    items = payload.get("items") or []
    if args.start:
        items = items[args.start:]
    if args.limit:
        items = items[: args.limit]

    out_path = Path(args.out).expanduser()
    existing: dict[str, dict] = {}
    if out_path.exists():
        try:
            prior = json.loads(out_path.read_text(encoding="utf-8"))
            for v in prior.get("verdicts", []):
                if v.get("id"):
                    existing[v["id"]] = v
        except json.JSONDecodeError:
            pass

    for n, item in enumerate(items, 1):
        if item["id"] in existing and existing[item["id"]].get("type"):
            continue
        models = [args.model]
        if args.fallback:
            models += [m for m in FALLBACK_MODELS if m != args.model]
        verdict = {"id": item["id"], "type": None, "_error": "not attempted"}
        for candidate_model in models:
            try:
                verdict = classify_item(item, candidate_model, args.timeout)
            except subprocess.TimeoutExpired:
                verdict = {"id": item["id"], "type": None, "_error": "timeout"}
            if verdict.get("type"):
                if candidate_model != args.model:
                    verdict["_model"] = candidate_model
                break
        existing[item["id"]] = verdict
        marker = verdict.get("type") or f"PENDING({verdict.get('_error')})"
        print(f"[{n}/{len(items)}] {item['id']} -> {marker}", flush=True)
        # Persist after every item so a crash loses at most one call.
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps({"verdicts": list(existing.values())}, indent=1, ensure_ascii=False),
            encoding="utf-8",
        )

    done = sum(1 for v in existing.values() if v.get("type"))
    print(f"\nclassified {done}/{len(existing)}; wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
