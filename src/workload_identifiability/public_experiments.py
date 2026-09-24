"""Pinned public-query certificate campaign.

The SQL text is not parsed by this module.  Each selected upstream SQL pair has
an explicit, inspectable column-to-CQ adapter in inputs/public/cases.  The
selection rule and exact unchanged SQL are retained in inputs/public/manifest.json.
"""
from __future__ import annotations
from pathlib import Path
import csv
import json
from .core import produce
from .verify import verify


def campaign(root: Path, output: Path) -> dict:
    cases = root / "inputs" / "public" / "cases"
    output.mkdir(parents=True, exist_ok=False)
    (output / "certificates").mkdir()
    rows = []
    total_containment = total_separators = 0
    for path in sorted(cases.glob("public-*.json")):
        model = json.loads(path.read_text(encoding="utf-8"))
        certificate = produce(model)
        checked = verify(model, certificate)
        if checked["quotient_states"] != 1:
            raise AssertionError(f"{path.stem}: public equivalent pair did not collapse")
        if certificate["containment"]["0,1"] is None or certificate["containment"]["1,0"] is None:
            raise AssertionError(f"{path.stem}: both containment directions are required")
        (output / "certificates" / path.name).write_text(
            json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        total_containment += len(certificate["containment"])
        total_separators += len(certificate["separators"])
        rows.append({
            "id": path.stem,
            "source_line_a": model["provenance"]["source_lines"][0],
            "source_line_b": model["provenance"]["source_lines"][1],
            "query_a_atoms": len(model["queries"][0]["atoms"]),
            "query_b_atoms": len(model["queries"][1]["atoms"]),
            "reachable_states": checked["reachable_states"],
            "quotient_states": checked["quotient_states"],
            "equivalent_both_directions": True,
            "admission_reason": model["provenance"]["admission_reason"],
        })
    with (output / "cases.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = {
        "status": "PUBLIC_FRAGMENT_CERTIFICATES_PASSED",
        "source": "SQLSolver Calcite equivalence tests at pinned commit",
        "cases": len(rows),
        "unchanged_sql_queries": 2 * len(rows),
        "all_pairs_equivalent": True,
        "all_quotients_singleton": True,
        "directed_containment_entries": total_containment,
        "block_pair_separators": total_separators,
        "scope": "Eight sequentially selected native equality-SPJ pairs under the published Calcite EMP/DEPT key and foreign-key schema; not a census of SQLSolver or general SQL.",
    }
    (output / "campaign.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
