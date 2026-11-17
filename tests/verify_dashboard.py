"""Verify the rebuilt dashboard: offline panel logic, zero/unknown costs, filters, tier weighting, browser render.

Run from ardf/ after `python3 calibrate.py`:   python3 tests/verify_dashboard.py [--screenshot out.png]

Standard library only. Needs a Chromium/Chrome binary for the in-page self-test; without one the script says so
and exits 3 (it never reports a pass it did not run). Cross-checks the page against current_frontier.py:
the default frontier, tier-weighted scores and the weighted frontier must equal the Python reference exactly.
"""
from __future__ import annotations
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import current_frontier as cf  # noqa: E402


def browser():
    for name in ('chromium', 'chromium-browser', 'google-chrome-stable', 'google-chrome'):
        p = shutil.which(name)
        if p: return p
    return None


def run_browser(exe, args, out=None):
    prof = tempfile.mkdtemp(prefix='ardf-verify-')
    try:
        cmd = [exe, '--headless=new', '--disable-gpu', '--no-sandbox', '--user-data-dir=' + prof, '--virtual-time-budget=40000'] + args
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        return r.stdout
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--screenshot', help='also write a 1500x2500 screenshot of the top of the page')
    args = ap.parse_args()
    dash = ROOT / 'dashboard.html'
    if not dash.exists():
        print('dashboard.html missing: run python3 calibrate.py first'); return 2
    exe = browser()
    if not exe:
        print('NOT VERIFIED: no Chromium/Chrome binary found, so the browser self-test did not run'); return 3
    dom = run_browser(exe, ['--dump-dom', dash.as_uri() + '?selftest=1'])
    m = re.search(r'<pre id="pc-selftest"[^>]*>(.*?)</pre>', dom, re.S)
    if not m:
        print('FAIL: no self-test output in the rendered page'); return 1
    res = json.loads(html.unescape(m.group(1)))
    failed = 0
    for c in res['checks']:
        print(('PASS ' if c['pass'] else 'FAIL ') + c['name'] + (' [' + str(c['detail']) + ']' if c['detail'] != '' else ''))
        failed += not c['pass']
    if res.get('error'):
        print('ERROR', res['error']); failed += 1
    rows = cf.build()['rows']
    pid = lambda r: 'aa-current:' + r['id']

    def check(name, cond, detail=''):
        nonlocal failed
        print(('PASS ' if cond else 'FAIL ') + name + (' [' + detail + ']' if detail else ''))
        failed += not cond
    check('default frontier equals current_frontier.frontier()', set(map(pid, cf.frontier(rows))) == set(res['default_frontier']), str(len(res['default_frontier'])))
    mult = res['weighted_case']
    bad = n = 0
    for r in rows:
        s = cf.score_components(r['components'], mult); ps = res['weighted_scores'].get(pid(r))
        if s is None and ps is None: continue
        n += 1; bad += (s is None or ps is None or abs(s - ps) > 1e-9)
    check('tier-weighted scores equal current_frontier.score_components()', bad == 0 and n == len(res['weighted_scores']), f'{n} compared, {bad} mismatches')
    wrows = [dict(r, score=cf.score_components(r['components'], mult)) for r in rows]
    check('weighted frontier equals the Python reference', set(map(pid, cf.frontier(wrows))) == set(res['weighted_frontier']))
    bonly = {'S': 0, 'A': 0, 'B': 1, 'C': 0, 'Unrated': 0}
    check('B-only scored count equals the Python reference', sum(cf.score_components(r['components'], bonly) is not None for r in rows) == res['bonly_scored'], str(res['bonly_scored']))
    if args.screenshot:
        run_browser(exe, ['--window-size=1500,2500', '--screenshot=' + args.screenshot, dash.as_uri()])
        print('screenshot', args.screenshot, Path(args.screenshot).exists())
    print('RESULT', 'FAILED' if failed else 'OK')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
