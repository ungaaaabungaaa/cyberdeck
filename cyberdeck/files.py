"""Bounded config reads and exclusive output bundles."""

import json
import os
from pathlib import Path
import stat


def read_config(path):
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_size > 16384:
        raise ValueError("Config must be a regular UTF-8 JSON file at most 16 KiB.")
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0),
    )
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Config must be a regular file.")
        raw = stream.read(16385)
    if len(raw) > 16384:
        raise ValueError("Config exceeded 16 KiB while reading.")
    try:

        def invalid_constant(_value):
            raise ValueError("Nonfinite JSON numbers are unsupported.")

        value = json.loads(raw.decode("utf-8-sig"), parse_constant=invalid_constant)
    except (UnicodeError, RecursionError) as error:
        raise ValueError("Config must contain bounded UTF-8 JSON.") from error
    if not isinstance(value, dict):
        raise ValueError("Config must contain a JSON object.")
    stack = [(value, 0)]
    nodes = 0
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if depth > 8 or nodes > 4096:
            raise ValueError("Config exceeds depth 8 or 4096 nodes.")
        children = (
            node.values()
            if isinstance(node, dict)
            else node if isinstance(node, list) else ()
        )
        stack.extend((child, depth + 1) for child in children)
    return value


def write_bundle(destination, files):
    destination = Path(destination)
    destination.mkdir()
    owned = []
    try:
        for name, content in files.items():
            path = destination / name
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                owned.append(path)
                stream.write(content)
    except Exception:
        for path in owned:
            path.unlink(missing_ok=True)
        try:
            destination.rmdir()
        except OSError:
            pass
        raise
