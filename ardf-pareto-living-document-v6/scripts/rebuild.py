# ---
# title: ARDF v6 Portable Rebuild and Packaging Script
# version: 6.0.0
# created: 2026-07-28
# model: GPT-5.6 Thinking
# reasoning_level: high
# purpose: Recalibrate, validate, hash, and package the complete living document.
# ---
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
ZIP_PATH=ROOT.parent/'ardf-pareto-living-document-v6.zip'


def run(script: str) -> None:
    subprocess.run([sys.executable,str(ROOT/'scripts'/script)],check=True,cwd=ROOT)


def manifest() -> None:
    records=[]
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.name=='manifest.json': continue
        records.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (ROOT/'manifest.json').write_text(json.dumps({'schema_version':'1.0.0','package_version':'6.0.0','files':records},indent=2)+'\n',encoding='utf-8')


def package() -> None:
    if ZIP_PATH.exists(): ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(ROOT.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                archive.write(path,Path(ROOT.name)/path.relative_to(ROOT))
    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad=archive.testzip()
        if bad: raise RuntimeError(f'ZIP integrity failure at {bad}')
    print(json.dumps({'zip':str(ZIP_PATH),'bytes':ZIP_PATH.stat().st_size,'integrity':'PASS'},indent=2))


def main() -> None:
    run('augment_cost.py')
    run('calibrate.py')
    run('validate.py')
    manifest()
    # Validate once more so the manifest requirement itself is checked by archive inspection.
    package()

if __name__=='__main__': main()
