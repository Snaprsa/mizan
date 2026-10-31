"""Local secrets. On macOS they live in the login Keychain (encrypted at rest); never in files or Git.

MIZAN_ARCGIS_API_KEY overrides the Keychain for hosts without one. Values are never logged or returned by the API.
"""
import os
import re
import subprocess
import sys

ACCOUNT, SERVICE = 'mizan', 'mizan-arcgis-key'
KEY_SHAPE = re.compile(r'^[A-Za-z0-9._~\-]{20,4000}$')
_cached: str | None = None


class SecretStoreError(Exception):
    """Carries a safe message only; it never contains the secret."""


def read_arcgis_key() -> str | None:
    global _cached
    env = os.environ.get('MIZAN_ARCGIS_API_KEY', '').strip()
    if env:
        return env
    if _cached:
        return _cached
    if sys.platform != 'darwin':
        return None
    try:
        out = subprocess.run(['security', 'find-generic-password', '-a', ACCOUNT, '-s', SERVICE, '-w'],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    _cached = out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None
    return _cached


def store_arcgis_key(key: str) -> None:
    global _cached
    if not KEY_SHAPE.match(key):  # Also keeps the value safe inside the quoted `security -i` command below.
        raise SecretStoreError('That doesn’t look like an Esri API key.')
    if sys.platform != 'darwin':
        raise SecretStoreError('No Keychain on this system. Set MIZAN_ARCGIS_API_KEY in the server environment.')
    # Sent over stdin so the key never appears in the process list.
    command = f'add-generic-password -U -a {ACCOUNT} -s {SERVICE} -T /usr/bin/security -w "{key}"\n'
    try:
        done = subprocess.run(['security', '-i'], input=command, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        raise SecretStoreError('The Keychain could not be reached.') from None
    if done.returncode != 0:
        raise SecretStoreError('The Keychain refused to save the key. Is it locked?')
    _cached = key


def delete_arcgis_key() -> None:
    global _cached
    _cached = None
    if sys.platform == 'darwin':
        subprocess.run(['security', 'delete-generic-password', '-a', ACCOUNT, '-s', SERVICE], capture_output=True, timeout=10)
