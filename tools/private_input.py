"""Safe read-only loading of private editorial JSON inputs."""
import json
import os
import stat
from pathlib import Path

def load_private_json(path):
    path = Path(path)
    if path.name == "public-catalogue.json":
        raise ValueError("Public catalogue cannot be a private editorial input")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Private editorial input must be a regular file")
        if path.is_symlink():
            raise ValueError("Symlink private editorial input refused")
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = -1
            return json.load(stream)
    finally:
        if fd != -1:
            os.close(fd)
