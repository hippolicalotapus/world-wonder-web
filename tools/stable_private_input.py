"""Read-only private JSON snapshots with concurrent-change detection.

Checks metadata and content before/after reads. This reduces accidental races
but cannot replace exclusive access or a trusted filesystem.
"""
import hashlib
from pathlib import Path
from private_input import load_private_json

def fingerprint(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Private input symlink refused")
    info = path.stat()
    if not path.is_file():
        raise ValueError("Private input must be a regular file")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)

def read_stable(path):
    before = fingerprint(path)
    data = load_private_json(path)
    after = fingerprint(path)
    if before != after:
        raise ValueError("Private input changed during verification")
    return data, after

def assert_unchanged(path, expected, data):
    if fingerprint(path) != expected:
        raise ValueError("Private input changed during verification")
    again, latest = read_stable(path)
    if latest != expected or again != data:
        raise ValueError("Private input changed during verification")
