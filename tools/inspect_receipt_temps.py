"""Read-only inspection of interrupted private receipt temporary files.

Never opens temporary contents, changes files, or automatically deletes them.
"""
import os
import stat
from pathlib import Path

PREFIX = ".wonder-receipt-"

def inspect_receipt_temps(directory):
    directory = Path(directory).absolute()
    if directory.is_symlink():
        raise ValueError("Receipt directory symlink refused")
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("Secure directory inspection requires POSIX")
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISDIR(opened.st_mode):
            raise ValueError("Receipt directory is not a directory")
        entries = []
        for name in sorted(os.listdir(fd)):
            if not name.startswith(PREFIX):
                continue
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            kind = "regular" if stat.S_ISREG(info.st_mode) else "unsafe"
            entries.append({"name": name, "kind": kind, "bytes": info.st_size})
        current = directory.stat()
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("Receipt directory replaced during inspection")
        return entries
    finally:
        os.close(fd)
