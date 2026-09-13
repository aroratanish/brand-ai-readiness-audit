"""Static final-submission validator for the Adobe marketplace bundle."""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    checks=[]
    manifest=ROOT/'marketplace.json'
    checks.append(("marketplace.json exists", manifest.is_file()))
    data=json.loads(manifest.read_text(encoding='utf-8'))
    skills=data.get('skills',[])
    entry=[s for s in skills if s.get('entrypoint') is True]
    checks.append(("exactly one entrypoint", len(entry)==1))
    checks.append(("README exists", (ROOT/'README.md').is_file()))
    legacy = [ROOT/'PROGRESS.md', ROOT/'P1_ADAPTER_CHANGES.md'] + list(ROOT.rglob('SKILL_P3.md'))
    checks.append(("no legacy development docs", not any(p.is_file() for p in legacy)))
    checks.append(("requirements exists", (ROOT/'requirements.txt').is_file()))
    for s in skills:
        folder=ROOT/s['path']; skill=folder/'SKILL.md'
        checks.append((f"SKILL.md: {s['id']}", skill.is_file()))
        if skill.is_file():
            text=skill.read_text(encoding='utf-8')
            checks.append((f"frontmatter: {s['id']}", text.startswith('---') and '\n---' in text[3:]))
    checks.append(("no ZIP inside bundle", not any(p.suffix.lower()=='.zip' for p in ROOT.rglob('*'))))
    checks.append(("no obvious secret files", not any(p.name in {'.env','.env.local','.env.production'} for p in ROOT.rglob('*'))))
    passed=sum(ok for _,ok in checks)
    print(json.dumps({"passed":passed,"total":len(checks),"checks":[{"check":n,"passed":ok} for n,ok in checks]},indent=2))
    return 0 if passed==len(checks) else 1
if __name__=='__main__': sys.exit(main())
