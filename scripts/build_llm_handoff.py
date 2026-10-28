#!/usr/bin/env python3
"""Build one portable source handoff directly; never relocate working files."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables'
SKIP_DIRS = {
    '.venv', 'venv', 'node_modules', '.next', '.git', '__pycache__',
    '.pytest_cache', '.ruff_cache', '.mypy_cache', '.cache', 'storage', 'deliverables',
}
TEXT_SUFFIXES = {
    '.py', '.md', '.txt', '.ts', '.tsx', '.js', '.mjs', '.json', '.html', '.css',
    '.toml', '.sh', '.yml', '.yaml', '.sql', '.ini', '.mako', '.csv', '.tsv', '.example',
}
SECRET_PATTERNS = {
    'Google API key': re.compile(r'AIza[0-9A-Za-z_-]{35}'),
    'OpenAI/Anthropic key': re.compile(r'\bsk-(?:proj-|ant-api\d\d?-)?[A-Za-z0-9_-]{24,}'),
    'GitHub token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})'),
    'AWS access ID': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'JWT token': re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}
CONTEXT_PARTS = [
    '00_START_HERE.md', 'handoff/CURRENT_STATE.md', 'handoff/FILE_MAP.md',
    'handoff/DECISIONS_AND_LIMITS.md', 'handoff/SETUP_AND_TESTS.md',
    'handoff/MAP_PROVIDER_NOTES.md', 'handoff/PRODUCT_SCOPE.md', 'handoff/UPGRADE_PROMPT.md',
]


def private_config_values():
    """Also catch real credentials embedded in prose/unquoted example assignments."""
    env_file = ROOT / 'Projects/Muqayyim-Downloads/.env'
    if not env_file.exists():
        return []
    values = []
    for line in env_file.read_text().splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        value = value.strip().strip('\"\'')
        if re.search(r'PASSWORD|API_KEY|SECRET|EMAIL', key) and len(value) >= 6:
            if not any(s in value.lower() for s in ['change', 'your', 'example', 'dev-secret', 'placeholder']):
                values.append(value)
    return values


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def excluded_file(path):
    name = path.name.lower()
    if name == '.ds_store' or name.endswith(('.pyc', '.pyo', '.tsbuildinfo', '.log')):
        return 'generated metadata/cache/log'
    if (name == '.env' or name.startswith('.env.')) and name != '.env.example':
        return 'private environment configuration'
    if name.endswith(('.db', '.db-journal', '.db-wal', '.db-shm', '.sqlite', '.sqlite3', '.sqlite-journal', '.sqlite3-journal')):
        return 'private database or journal'
    if name.endswith(('.pem', '.key', '.p12', '.pfx', '.har')):
        return 'credential/key or network capture'
    if (('session' in name or 'cookie' in name) and name.endswith('.json')):
        return 'private authenticated browser/provider session'
    return None


def source_paths(exclusions):
    for parent, dirs, files in os.walk(ROOT):
        keep = []
        for name in sorted(dirs):
            path = Path(parent) / name
            if path.is_symlink() or name in SKIP_DIRS or name.endswith('.egg-info'):
                reason = ('private runtime storage/uploads/backups' if name == 'storage' else
                          'generated deliverables (included separately where intended)' if name == 'deliverables' else
                          'symlink excluded' if path.is_symlink() else 'installed dependency/build/cache/VCS directory')
                exclusions.append({'path': path.relative_to(ROOT).as_posix() + '/', 'reason': reason})
            else:
                keep.append(name)
        dirs[:] = keep
        for name in sorted(files):
            path = Path(parent) / name
            reason = 'symlink excluded' if path.is_symlink() else excluded_file(path)
            if reason:
                exclusions.append({'path': path.relative_to(ROOT).as_posix(), 'reason': reason})
            else:
                yield path


def sanitize(path, data, redactions):
    relative = path.relative_to(ROOT).as_posix()
    if relative == 'Projects/Muqayyim-Downloads/.env.example':
        data = b'''# Portable LOCAL DEVELOPMENT example. No real credentials are transferred.
# The root launcher configures its own absolute SQLite path.
DATABASE_URL=sqlite+aiosqlite:///./storage/mizan.db
DATABASE_URL_SYNC=sqlite:///./storage/mizan.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=dev-secret-change-in-production-immediately
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
ANTHROPIC_API_KEY=
AQARSAS_EMAIL=
AQARSAS_PASSWORD=
PASEETAH_EMAIL=
PASEETAH_PASSWORD=
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./storage
API_HOST=127.0.0.1
API_PORT=8000
FRONTEND_URL=http://127.0.0.1:3100
API_URL=http://127.0.0.1:8000
ENV=development
DEBUG=false
'''
        redactions.append({'path': relative, 'category': 'portable empty-credential development template', 'count': 1})
    if path.suffix.lower() in TEXT_SUFFIXES or path.name in {'Makefile', '.gitignore'}:
        try:
            content = data.decode('utf-8')
        except UnicodeDecodeError:
            return data
        for category, pattern in SECRET_PATTERNS.items():
            content, count = pattern.subn('REDACTED_CREDENTIAL', content)
            if count:
                redactions.append({'path': relative, 'category': category, 'count': count})
        for value in private_config_values():
            count = content.count(value)
            if count:
                content = content.replace(value, 'REDACTED_PRIVATE_CONFIGURATION')
                redactions.append({'path': relative, 'category': 'private local credential value', 'count': count})
        data = content.encode('utf-8')
    return data


def main():
    OUT.mkdir(exist_ok=True)
    context = ('# Mizan — portable LLM context\n\n'
               'Prepared 28 October 2026. This document contains the handoff and full requested '
               'upgrade brief. Complete source/tests/data are in Mizan-LLM-Handoff.zip; this text '
               'is not a substitute for inspecting them. Private databases/credentials are excluded.\n\n')
    for relative in CONTEXT_PARTS:
        context += '\n\n---\n\nSource: `' + relative + '`\n\n' + (ROOT / relative).read_text()
    context_path = OUT / 'MIZAN_LLM_CONTEXT.md'
    context_path.write_text(context)
    exclusions, redactions, manifest = [], [], []
    archive = OUT / 'Mizan-LLM-Handoff.zip'
    temporary = OUT / 'Mizan-LLM-Handoff.zip.partial'
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=7) as bundle:
        def add(relative, data, source=None):
            info = zipfile.ZipInfo('Mizan/' + relative)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = stat.S_IMODE(source.stat().st_mode) if source else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            bundle.writestr(info, data)
            item = {'path': relative, 'bytes': len(data), 'sha256': sha(data)}
            if source:
                item['original_relative_path'] = source.relative_to(ROOT).as_posix()
            manifest.append(item)

        for path in source_paths(exclusions):
            add(path.relative_to(ROOT).as_posix(), sanitize(path, path.read_bytes(), redactions), path)
        add('MIZAN_LLM_CONTEXT.md', context_path.read_bytes())
        add('PACKAGE_EXCLUSIONS.json', json_bytes(exclusions))
        add('PACKAGE_REDACTIONS.json', json_bytes(redactions))
        bundle.writestr('Mizan/PACKAGE_MANIFEST.json', json_bytes({
            'format': 1, 'prepared_date': '2026-10-28',
            'scope': 'portable source, reference datasets, context and original-location provenance',
            'manifest_note': 'Hashes describe archive payloads. This manifest does not hash itself.',
            'files': manifest,
        }))
    temporary.replace(archive)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('ZIP integrity check failed')
        for item in manifest:
            if sha(bundle.read('Mizan/' + item['path'])) != item['sha256']:
                raise RuntimeError('Payload digest mismatch: ' + item['path'])
    digest = sha(archive.read_bytes())
    (OUT / 'Mizan-LLM-Handoff.zip.sha256').write_text(digest + '  ' + archive.name + '\n')
    report = {
        'created_utc': datetime.now(timezone.utc).isoformat(), 'archive': archive.name,
        'archive_bytes': archive.stat().st_size, 'sha256': digest,
        'included_files': len(manifest) + 1, 'uncompressed_bytes': sum(f['bytes'] for f in manifest),
        'exclusion_entries': len(exclusions), 'exclusion_categories': dict(Counter(e['reason'] for e in exclusions)),
        'redactions': redactions, 'zip_crc_and_payload_sha256': 'passed',
        'originals': 'All working files, private databases and original-location history remain on the Mac.',
    }
    verified = ROOT / 'handoff/PACKAGE_VERIFICATION.json'
    if verified.exists():
        report['verification'] = json.loads(verified.read_text())
    (OUT / 'PACKAGE_REPORT.json').write_bytes(json_bytes(report))
    print(json.dumps({k: report[k] for k in ['archive_bytes', 'included_files', 'exclusion_entries', 'sha256', 'zip_crc_and_payload_sha256']}))
    print('Credential patterns redacted:', sum(r['count'] for r in redactions if 'template' not in r['category']))


if __name__ == '__main__':
    main()
