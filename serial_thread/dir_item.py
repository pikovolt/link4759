# coding: utf-8
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Optional


@dataclass(frozen=True)
class DirItem:
    """One entry in a 4759Player SD directory listing."""

    filename: str
    dispname: str
    size: int = 0
    is_dir: bool = False

    @classmethod
    def from_response(cls, filename: str, longname: Optional[str], size_type: str) -> "DirItem":
        is_dir = size_type == "<dir>"
        size = 0 if is_dir else int(size_type)
        dispname = longname if longname else filename
        return cls(filename=filename, dispname=dispname, size=size, is_dir=is_dir)

    def matches_exact(self, keyword: str) -> bool:
        return keyword in (self.filename, self.dispname)

    def __str__(self) -> str:
        return f"{self.filename}, {self.dispname}, {'<dir>' if self.is_dir else '<file>'}"


class DirList:
    """Small model used by the UI."""

    def __init__(self, items: Optional[Iterable[DirItem]] = None, dirname: Optional[str] = None):
        self.dirname = dirname
        self._items = list(items or [])

    @property
    def items(self) -> list[DirItem]:
        return list(self._items)

    def add(self, item: DirItem) -> None:
        self._items.append(item)

    def find_item(self, keyword: str) -> Optional[DirItem]:
        for item in self._items:
            if item.matches_exact(keyword):
                return item
        return None

    def __iter__(self) -> Iterator[DirItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)
