"""Verify that a build is byte-identical across Python versions, apart from the date stamp.

Run from anywhere:   python3 tests/verify_determinism.py [--pythons 3.11 3.12 3.13 3.14] [--keep]

Copies this package into scratch directories (the working tree is never touched), builds each copy with
`calibrate.py` under every requested interpreter that is installed, pins the date with SOURCE_DATE_EPOCH so a
rebuild on another day is comparable, then compares every generated file byte for byte. A second build with a
different pinned date on the first interpreter must differ only in the date stamp.

Why: Python 3.12 made the built-in sum() of floats compensated (3.11 is naive), which moved the last digits of
calibrated values; the build now uses math.fsum and rounds floats when it serializes them.

Interpreters that are not installed are reported as SKIPPED (the script never downloads one). It exits 0 only when
at least two interpreters were really compared, 3 when fewer were available ("NOT VERIFIED"), 1 on any difference.
Standard library only; uses `uv python find --offline` to locate interpreters when uv is present.
"""
from __future__ import annotations
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ['data/unified-model-evidence.csv', 'dashboard.html', 'pareto-frontier-cheatsheet.md', 'model-tiers-and-contenders.md',
           'docs/routing-rules.md', 'docs/full-frontier.md', 'docs/free-routes.md', 'docs/priors-deltas.md']
EPOCH_A, EPOCH_B = '1700000000', '1700086400'   # 2023-11-14 and 2023-11-15 UTC
DATES = ('2023-11-14', '2023-11-15')


def find_python(spec: str) -> str | None:
    p = shutil.which('python' + spec)
    if p: return p
    if shutil.which('uv'):
        r = subprocess.run(['uv', 'python', 'find', '--offline', spec], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip(): return r.stdout.strip()
    return None


def version_of(exe: str) -> str:
    return subprocess.run([exe, '-c', 'import sys;print(".".join(map(str,sys.version_info[:3])))'], capture_output=True, text=True).stdout.strip()


def build(exe: str, epoch: str, work: Path) -> Path:
    dst = work / ('build-' + hashlib.sha1((exe + epoch).encode()).hexdigest()[:8])
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns('__pycache__', 'dashboard.html', '.git', 'tests'))
    env = dict(os.environ, SOURCE_DATE_EPOCH=epoch)
    r = subprocess.run([exe, 'calibrate.py'], cwd=dst, env=env, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print('BUILD FAILED', exe, epoch); print(r.stderr[-1500:]); raise SystemExit(1)
    return dst


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--pythons', nargs='+', default=['3.11', '3.12', '3.13', '3.14'])
    ap.add_argument('--keep', action='store_true', help='keep the scratch directory')
    args = ap.parse_args()
    found, seen = [], set()
    for spec in args.pythons:
        exe = find_python(spec)
        if not exe:
            print(f'SKIPPED Python {spec}: not installed (this script does not download interpreters)'); continue
        v = version_of(exe)
        if v in seen: continue
        seen.add(v); found.append((v, exe))
    for v, exe in found: print(f'using Python {v} at {exe}')
    if len(found) < 2:
        print('NOT VERIFIED: fewer than two interpreters available, so no cross-version comparison was made'); return 3
    work = Path(tempfile.mkdtemp(prefix='ardf-determinism-'))
    failed = 0
    try:
        builds = [(v, build(exe, EPOCH_A, work)) for v, exe in found]
        ref_v, ref = builds[0]
        for v, d in builds[1:]:
            for rel in OUTPUTS:
                same = (ref / rel).read_bytes() == (d / rel).read_bytes()
                print(('PASS ' if same else 'FAIL ') + f'{rel}: Python {ref_v} vs {v} byte-identical [{sha(ref / rel)[:12]}]')
                failed += not same
        # Date stamp: the same interpreter, another pinned date. Only the date may differ.
        other = build(found[0][1], EPOCH_B, work)
        for rel in OUTPUTS:
            a, b = (ref / rel).read_text(encoding='utf-8'), (other / rel).read_text(encoding='utf-8')
            ok = a.replace(DATES[0], '<DATE>') == b.replace(DATES[1], '<DATE>')
            print(('PASS ' if ok else 'FAIL ') + f'{rel}: a build on another date differs only in the date stamp ({DATES[0]} vs {DATES[1]}; identical: {a == b})')
            failed += not ok
        if not any((ref / r).read_text(encoding='utf-8') != (other / r).read_text(encoding='utf-8') for r in OUTPUTS):
            print('FAIL the date stamp did not change anything: SOURCE_DATE_EPOCH is not being honoured'); failed += 1
    finally:
        if args.keep: print('scratch kept at', work)
        else: shutil.rmtree(work, ignore_errors=True)
    print('RESULT', 'FAILED' if failed else 'OK', f'({len(found)} interpreters: ' + ', '.join(v for v, _ in found) + ')')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
