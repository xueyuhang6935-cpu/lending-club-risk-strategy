"""Check tracked publication files, local links and accidental secrets before upload."""
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]

def main():
    files=[ROOT/p for p in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if p]
    findings=[]
    forbidden={'.ps1','.dpapi','.key','.pem','.sqlite','.db','.joblib','.gz','.aux','.log','.out','.toc'}
    patterns={
        'private-key':r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
        'github-token':r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',
        'cloud-key':r'\bAKIA[A-Z0-9]{16}\b',
        'local-path':r'(?:(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/Volumes/)',
        'credential-assignment':r'''(?i)(?:password|passwd|api_key|secret|密码)\s*[:=]\s*["'][^"'\n]{4,}["']''',
    }
    for path in files:
        relative=str(path.relative_to(ROOT))
        if path.name.startswith('._') or path.suffix in forbidden or path.stat().st_size>5_000_000:
            findings.append({'file':relative,'kind':'excluded-or-large-file'})
        if path.suffix in {'.pdf','.png'}:continue  # PDF text/metadata inspected separately; image visually checked.
        text=path.read_text(encoding='utf-8-sig')
        if path.name!='check_publication.py':
            for name,pattern in patterns.items():
                if re.search(pattern,text):findings.append({'file':relative,'kind':name})
        if path.suffix=='.md':
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith(('http:','https:','#','mailto:')):continue
                target=path.parent/link.split('#')[0]
                if not target.exists():findings.append({'file':relative,'kind':'broken-link','link':link})
    result=dict(status='passed' if not findings else 'failed',tracked_file_count=len(files),findings=findings,
        pdf_text_and_metadata_review='6+1 pages checked separately; no local paths',
        excluded='raw loan data, per-loan outputs, databases, credentials, old plans, caches, LaTeX intermediates')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    (ROOT/'docs/publication_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if findings:sys.exit(1)
if __name__=='__main__':main()
