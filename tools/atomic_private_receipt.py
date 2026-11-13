"""Create-only private receipt writes pinned to a verified directory descriptor.

POSIX-only. Uses an exclusive random temporary inode, fsync, hard-link
publication with no replacement, directory fsync, and descriptor-relative
cleanup. No public files or existing destination files are modified.
"""
import json
import os
import secrets
import stat
from pathlib import Path

def write_new_receipt(path, payload):
    path = Path(path).absolute()
    if path.name == "public-catalogue.json" or path.name in ("", ".", ".."):
        raise ValueError("Invalid private receipt name")
    if os.name != "posix" or not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("Secure directory-relative receipt creation requires POSIX")
    if path.parent.is_symlink():
        raise ValueError("Receipt parent symlink refused")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open(path.parent, flags)
    temporary = None
    try:
        opened = os.fstat(directory)
        current = path.parent.stat()
        if not stat.S_ISDIR(opened.st_mode) or (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("Receipt directory changed before creation")
        for _ in range(8):
            candidate = ".wonder-receipt-" + secrets.token_hex(16)
            try:
                fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
                temporary = candidate
                break
            except FileExistsError:
                continue
        else:
            raise FileExistsError("Unable to reserve private receipt temporary name")
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        current = path.parent.stat()
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("Receipt directory replaced during creation")
        os.link(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        os.fsync(directory)
    finally:
        if temporary is not None:
            os.unlink(temporary, dir_fd=directory)
        os.close(directory)
