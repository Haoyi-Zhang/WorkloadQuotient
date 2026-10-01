"""Evidence comparison with scientific and environmental fields separated.

Measured timing/RSS fields are volatile.  Engine versions are retained and
reported as environment metadata, but a version-only change does not turn an
otherwise identical semantic replay into a scientific mismatch.  Any change to
result fields still fails exact comparison.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

VOLATILE_FIELDS = frozenset({"cpu_seconds", "wall_seconds", "peak_rss_kib"})
ENVIRONMENT_FIELDS = frozenset({"engine_version"})


def _strip(value: Any, fields: frozenset[str]) -> Any:
    if isinstance(value, dict):
        return {k: _strip(v, fields) for k, v in value.items() if k not in fields}
    if isinstance(value, list):
        return [_strip(v, fields) for v in value]
    return value


def scientific_view(value: Any) -> Any:
    """Return the claim-bearing view used for exact scientific comparison."""
    return _strip(_strip(value, VOLATILE_FIELDS), ENVIRONMENT_FIELDS)


def _environment_entries(value: Any, prefix: str = "$") -> dict[str, Any]:
    entries: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}"
            if key in ENVIRONMENT_FIELDS:
                entries[path] = child
            entries.update(_environment_entries(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            entries.update(_environment_entries(child, f"{prefix}[{index}]"))
    return entries


def read_value(path: Path) -> Any:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if path.suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    return path.read_bytes()


def compare_files(expected: Path, actual: Path) -> list[dict[str, Any]]:
    """Compare one evidence file and return version/environment drift records."""
    left = read_value(expected)
    right = read_value(actual)
    if scientific_view(left) != scientific_view(right):
        raise AssertionError(f"Scientific evidence differs: {expected}")
    if expected.suffix not in {".json", ".jsonl", ".csv"}:
        return []
    left_env = _environment_entries(left)
    right_env = _environment_entries(right)
    drift = []
    for path in sorted(set(left_env) | set(right_env)):
        if left_env.get(path) != right_env.get(path):
            drift.append({
                "field_path": path,
                "expected": left_env.get(path),
                "actual": right_env.get(path),
            })
    return drift


def compare_tree(expected: Path, actual: Path) -> tuple[int, list[dict[str, Any]]]:
    left = {p.relative_to(expected) for p in expected.rglob("*") if p.is_file()}
    right = {p.relative_to(actual) for p in actual.rglob("*") if p.is_file()}
    if left != right:
        raise AssertionError(
            f"Different evidence files: missing={sorted(left-right)}, extra={sorted(right-left)}"
        )
    environment_drift: list[dict[str, Any]] = []
    for rel in sorted(left):
        for item in compare_files(expected / rel, actual / rel):
            environment_drift.append({"file": str(rel), **item})
    return len(left), environment_drift
