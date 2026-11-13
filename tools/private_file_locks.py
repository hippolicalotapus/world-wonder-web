"""Advisory read locks for private migration operations (POSIX only).

Locks the opened file descriptors, verifies path identity, and refuses
symlinks. All cooperating writers must honor flock; this is not mandatory
locking and does not prevent uncooperative directory replacements.
"""
import contextlib
import json
import os
import stat
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None

@contextlib.contextmanager
def locked_inputs(paths):
    if fcntl is None:
        raise RuntimeError("POSIX advisory locking unavailable; refusing unsafe operation")
    paths = [Path(p) for p in paths]
    if len({str(p.absolute()) for p in paths}) != len(paths):
        raise ValueError("Locked input paths must be distinct")
    opened = []
    try:
        for path in sorted(paths, key=lambda p: str(p.absolute())):
            if path.name == "public-catalogue.json":
                raise ValueError("Public catalogue cannot be private input")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            fd = os.open(path, flags)
            opened.append((path, fd))
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or path.is_symlink():
                raise ValueError("Private input must be a non-symlink regular file")
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("Private input locked by another process") from exc
            current = path.stat()
            if (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino):
                raise ValueError("Private input replaced while acquiring lock")
        yield
        for path, fd in opened:
            current = path.stat()
            info = os.fstat(fd)
            if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) != (
                current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns
            ):
                raise ValueError("Private input changed while locked")
    finally:
        for _, fd in reversed(opened):
            os.close(fd)
