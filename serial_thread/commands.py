# coding: utf-8
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import itertools


class CommandKind(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    SD_DIR = "sd_dir"
    CD = "cd"
    PLAY = "play"
    STOP = "stop"
    HELP = "help"
    RAW = "raw"


_command_id_counter = itertools.count(1)


@dataclass(frozen=True)
class CommandRequest:
    kind: CommandKind
    payload: dict[str, Any] = field(default_factory=dict)
    command_id: int = field(default_factory=lambda: next(_command_id_counter))


@dataclass(frozen=True)
class CommandResult:
    command_id: int
    kind: CommandKind
    ok: bool
    message: str = ""
    data: Any = None
