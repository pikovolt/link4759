# coding: utf-8
from __future__ import annotations

import re

from .dir_item import DirItem, DirList
from .commands import CommandKind, CommandRequest


PTN_FILENAME = re.compile(
    r"^(?P<filename>((\.{2})|((?!\.).{1,11}(\.vgm|\.s98|\.mdx)*)))\s+"
    r"(?P<size_type>(\d+|<dir>))\s{2}"
    r"\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2}"
    r"(\s+(?P<longname>.*))*",
    re.IGNORECASE,
)


def command_to_text(req: CommandRequest) -> str:
    """Convert a typed command request into a 4759Player command string."""
    kind = req.kind
    payload = req.payload

    if kind == CommandKind.SD_DIR:
        return "sd dir"
    if kind == CommandKind.CD:
        return f"cd {payload['dirname']}"
    if kind == CommandKind.PLAY:
        return f"play {payload['filename']}"
    if kind == CommandKind.STOP:
        return "stop"
    if kind == CommandKind.HELP:
        return "help"
    if kind == CommandKind.RAW:
        return payload["text"]

    raise ValueError(f"Command kind cannot be converted to raw text: {kind}")


def parse_dir_list(text: str) -> DirList:
    """Parse a directory listing response into DirList."""
    dirlist = DirList()
    for line in text.splitlines():
        match = PTN_FILENAME.search(line)
        if not match:
            continue
        filename = "".join(match.group("filename").split())
        longname = match.group("longname")
        size_type = match.group("size_type")
        dirlist.add(DirItem.from_response(filename, longname, size_type))
    return dirlist


def looks_like_playing_status(line: str) -> bool:
    return "playing..." in line.lower()


def looks_like_error(line: str) -> bool:
    lowered = line.lower()
    return "error" in lowered or "not found" in lowered or "failed" in lowered


def is_dir_command(req: CommandRequest) -> bool:
    return req.kind in (CommandKind.SD_DIR, CommandKind.CD)


def classify_line(line: str) -> str:
    if looks_like_playing_status(line):
        return "status"
    if PTN_FILENAME.search(line):
        return "dir_entry"
    if looks_like_error(line):
        return "error"
    return "log"
