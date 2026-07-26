"""In-memory async document store (Motor subset for hermetic tests)."""

from __future__ import annotations

import copy
from typing import Any


def _matches(doc: dict[str, Any], flt: dict[str, Any]) -> bool:
    for key, cond in flt.items():
        val = doc.get(key)
        if isinstance(cond, dict):
            for op, operand in cond.items():
                if op == "$in" and val not in operand:
                    return False
                if op == "$ne" and val == operand:
                    return False
                if op == "$exists" and (key in doc) != operand:
                    return False
        elif val != cond:
            return False
    return True


class _Cursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self._docs = docs

    def sort(self, *_args: Any, **_kwargs: Any) -> _Cursor:
        return self

    def limit(self, n: int) -> _Cursor:
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        docs = self._docs if length is None else self._docs[:length]
        return [copy.deepcopy(d) for d in docs]


class InMemoryCollection:
    def __init__(self) -> None:
        self._docs: list[dict[str, Any]] = []
        self.indexes: list[Any] = []

    async def find_one(self, flt: dict[str, Any]) -> dict[str, Any] | None:
        for doc in self._docs:
            if _matches(doc, flt):
                return copy.deepcopy(doc)
        return None

    def find(self, flt: dict[str, Any] | None = None) -> _Cursor:
        flt = flt or {}
        return _Cursor([copy.deepcopy(d) for d in self._docs if _matches(d, flt)])

    async def count_documents(self, flt: dict[str, Any]) -> int:
        return sum(1 for d in self._docs if _matches(d, flt))

    async def insert_one(self, doc: dict[str, Any]) -> None:
        self._docs.append(copy.deepcopy(doc))

    async def replace_one(
        self, flt: dict[str, Any], doc: dict[str, Any], upsert: bool = False
    ) -> bool:
        for i, existing in enumerate(self._docs):
            if _matches(existing, flt):
                self._docs[i] = copy.deepcopy(doc)
                return True
        if upsert:
            self._docs.append(copy.deepcopy(doc))
        return False

    async def update_one(self, flt: dict[str, Any], update: dict[str, Any]) -> bool:
        for doc in self._docs:
            if _matches(doc, flt):
                for op, fields in update.items():
                    if op == "$set":
                        doc.update(copy.deepcopy(fields))
                    if op == "$inc":
                        for key, delta in fields.items():
                            doc[key] = int(doc.get(key, 0)) + int(delta)
                return True
        return False

    async def delete_many(self, flt: dict[str, Any]) -> int:
        before = len(self._docs)
        self._docs = [d for d in self._docs if not _matches(d, flt)]
        return before - len(self._docs)

    async def create_index(self, *_args: Any, **_kwargs: Any) -> None:
        self.indexes.append((_args, _kwargs))

    async def create_indexes(self, models: list[Any]) -> None:
        self.indexes.extend(models)


class InMemoryDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, InMemoryCollection] = {}

    def __getitem__(self, name: str) -> InMemoryCollection:
        return self._collections.setdefault(name, InMemoryCollection())

    def get_collection(self, name: str) -> InMemoryCollection:
        return self[name]
