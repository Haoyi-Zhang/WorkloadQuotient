"""Explicit finite encodings for the eight hand-written public CQ adapters.

This module does not parse SQL.  It validates the retained adapter contract,
encodes the 64 finite SQL databases into the integer-only CQ domain, and
normalizes non-NULL SQL output values for set comparison with the CQ evaluator.
SQL NULL is outside the paper's theory: each NULL input cell receives a fresh
ordinary integer used only for this finite cross-check, and no claim about SQL
NULL semantics follows from the comparison.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


RELATION_COLUMNS = {
    "DEPT": ("DEPTNO", "NAME"),
    "EMP": ("EMPNO", "ENAME", "JOB", "MGR", "HIREDATE", "SAL", "COMM", "DEPTNO", "SLACKER"),
}


def load_contract(root: Path) -> dict[str, Any]:
    return json.loads((root / "inputs/public/adapter-contracts.json").read_text(encoding="utf-8"))


def load_models(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((root / "inputs/public/cases").glob("public-*.json"))
    }


def validate_contract(root: Path) -> dict[str, Any]:
    """Check that the prose-level contract exactly names the executable adapters."""
    contract = load_contract(root)
    manifest = json.loads((root / "inputs/public/manifest.json").read_text(encoding="utf-8"))
    models = load_models(root)
    if contract.get("source_commit") != manifest.get("commit"):
        raise AssertionError("adapter contract commit differs from public manifest")
    declared = contract.get("relations", {})
    for relation, names in RELATION_COLUMNS.items():
        columns = declared.get(relation)
        if not isinstance(columns, list) or tuple(column.get("name") for column in columns) != names:
            raise AssertionError(f"adapter contract column order differs for {relation}")
        if tuple(column.get("position") for column in columns) != tuple(range(len(names))):
            raise AssertionError(f"adapter contract positions differ for {relation}")
    adapters = contract.get("adapters", [])
    if [item.get("id") for item in adapters] != [pair["id"] for pair in manifest["pairs"]]:
        raise AssertionError("adapter contract IDs/order differ from manifest")
    for item, pair in zip(adapters, manifest["pairs"]):
        model = models[item["id"]]
        if item.get("hand_written") is not True:
            raise AssertionError(f"{item['id']}: adapter must be labelled hand-written")
        if item.get("sql") != pair["sql"]:
            raise AssertionError(f"{item['id']}: contract SQL differs from immutable manifest text")
        sides = item.get("sides", [])
        if len(sides) != 2:
            raise AssertionError(f"{item['id']}: expected two adapter sides")
        for index, side in enumerate(sides):
            if side.get("cq_query") != model["queries"][index]:
                raise AssertionError(f"{item['id']} side {index}: contract differs from executable CQ")
            if side.get("sql_text") != pair["sql"][index]:
                raise AssertionError(f"{item['id']} side {index}: side SQL differs from manifest")
    return contract


@dataclass
class FiniteSQLToCQEncoding:
    """Inject SQL scalar values into integers for one finite database.

    Existing SQL integers are preserved so rigid constants such as 1 and 10
    retain their intended meaning.  Text values receive distinct negative
    integers.  Every NULL input cell receives its own fresh negative integer;
    these sentinels are not a model of SQL NULL and are never accepted in an
    output row used for a SQL--CQ comparison.
    """

    database: dict[str, list[tuple[Any, ...]]]
    text_values: dict[str, int] = field(init=False)
    _next_fresh: int = field(init=False)
    null_cells: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        integers = {
            value
            for rows in self.database.values()
            for row in rows
            for value in row
            if type(value) is int
        }
        strings = sorted({
            value
            for rows in self.database.values()
            for row in rows
            for value in row
            if isinstance(value, str)
        })
        cursor = min(integers | {0, 1, 10}) - 1
        self.text_values = {}
        for value in strings:
            self.text_values[value] = cursor
            cursor -= 1
        self._next_fresh = cursor

    def _fresh(self) -> int:
        value = self._next_fresh
        self._next_fresh -= 1
        return value

    def scalar(self, value: Any, *, allow_null: bool) -> int:
        if type(value) is int:
            return value
        if isinstance(value, str):
            if value not in self.text_values:
                self.text_values[value] = self._fresh()
            return self.text_values[value]
        if value is None and allow_null:
            self.null_cells += 1
            return self._fresh()
        if value is None:
            raise AssertionError("selected SQL output unexpectedly contains NULL")
        raise TypeError(f"unsupported SQL scalar type: {type(value).__name__}")

    def cq_database(self) -> dict[str, list[list[int]]]:
        encoded: dict[str, list[list[int]]] = {}
        for relation, rows in self.database.items():
            expected = len(RELATION_COLUMNS[relation])
            encoded_rows = []
            for row in rows:
                if len(row) != expected:
                    raise AssertionError(f"{relation}: unexpected row width")
                encoded_rows.append([self.scalar(value, allow_null=True) for value in row])
            encoded[relation] = encoded_rows
        return encoded

    def output_set(self, rows: list[tuple[Any, ...]]) -> set[tuple[int, ...]]:
        return {
            tuple(self.scalar(value, allow_null=False) for value in row)
            for row in rows
        }
