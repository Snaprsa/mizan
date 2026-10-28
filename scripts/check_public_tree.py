#!/usr/bin/env python3
"""Check committed/staged source without printing secret values. Standard library only."""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'provider API key': re.compile(rb'AIza[0-9A-Za-z_-]{35}|\bsk-(?:proj-|ant-api\d\d?-)?[A-Za-z0-9_-]{24,}'),
    'GitHub token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})'),
    'AWS credential ID': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'private key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'personal home directory': re.compile(rb'/(?:Users|home)/[A-Za-z0-9_.-]+/'),
    'personal email example': re.compile(rb'[\w.+-]+@(?:gmail|hotmail|yahoo|outlook|icloud)\.com'),
}


def main():
    entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT).split(b'\0')
    failures = []
    files = 0
    # Compare against private local config too, when available. Never emit values.
    private_values = []
    local_env = ROOT / 'Projects/Muqayyim-Downloads/.env'
    if local_env.exists():
        for line in local_env.read_text().splitlines():
            if '=' not in line or line.lstrip().startswith('#'):
                continue
            key, value = line.split('=', 1)
            value = value.strip().strip('"\'')
            if re.search(r'PASSWORD|API_KEY|SECRET|EMAIL', key) and len(value) >= 6:
                if not any(s in value.lower() for s in ['change', 'your', 'example', 'dev-secret', 'placeholder']):
                    private_values.append(value.encode())
    for entry in entries:
        if not entry:
            continue
        meta, raw_path = entry.split(b'\t', 1)
        path = raw_path.decode()
        mode, oid, stage = meta.decode().split()
        parts = Path(path).parts
        name = parts[-1].lower()
        files += 1
        forbidden = (
            any(p in {'node_modules', '.venv', 'venv', 'storage', 'deliverables', 'Backups', 'Saved-Pages', 'Screenshots', 'Related-Materials-To-Review'} for p in parts)
            or (name.startswith('.env') and name != '.env.example')
            or name.endswith(('.db', '.sqlite', '.sqlite3', '.csv', '.xlsx', '.xls', '.joblib', '.parquet', '.docx', '.png', '.pem', '.key', '.har'))
            or '.db-' in name or '.sqlite-' in name
            or ('session' in name and name.endswith('.json'))
            or name in {'original-locations.tsv', 'move-history.json', 'collection-manifest.json'}
        )
        if forbidden or mode == '120000' or stage != '0':
            failures.append({'path': path, 'reason': 'private/generated/unreviewed path, symlink or unresolved merge'})
        data = subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=ROOT)
        for category, pattern in PATTERNS.items():
            if pattern.search(data):
                failures.append({'path': path, 'reason': category})
        if any(value in data for value in private_values):
            failures.append({'path': path, 'reason': 'matches a private local configuration value'})
    print(json.dumps({'checked_files': files, 'failures': failures}, indent=2))
    return bool(failures)


if __name__ == '__main__':
    sys.exit(main())
