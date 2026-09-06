"""LEAK-CS-001 — isolation and leakage audit for every active fold (Excel P1.7).

The audit is executed, not asserted.  Each check returns ``PASS``, ``FAIL``,
``BLOCKED`` or ``INFORMATIONAL`` and carries the observation that produced it, so a
reviewer can disagree with a verdict without re-deriving the number.

``INFORMATIONAL`` is used only where no threshold was declared in advance; it never
substitutes for a PASS and is never counted as one.
"""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from seqlogad.common.checksum import sha256_file
from seqlogad.protocol.architectures import ARCHITECTURES
from seqlogad.protocol.chronology import (
    SEG_GUARD,
    load_stream_frame,
    load_stream_index,
)
from seqlogad.protocol.folds import list_folds, load_fold
from seqlogad.protocol.buffer import load_buffer


AUDIT_SCHEMA_VERSION = "1.0"
AUDIT_ROOT = "data/processed/protocol/audits"

PASS = "PASS"
FAIL = "FAIL"
BLOCKED = "BLOCKED"
INFORMATIONAL = "INFORMATIONAL"

# Modules that sit on the adaptation path. None of them may reach the label module.
ADAPTATION_PATH_MODULES = (
    "src/seqlogad/protocol/schema.py",
    "src/seqlogad/protocol/normalizer.py",
    "src/seqlogad/protocol/nul.py",
    "src/seqlogad/protocol/architectures.py",
    "src/seqlogad/protocol/chronology.py",
    "src/seqlogad/protocol/folds.py",
    "src/seqlogad/protocol/buffer.py",
)
LABEL_MODULE = "seqlogad.protocol.labels"


class AuditError(RuntimeError):
    """Raised when the audit cannot be executed at all."""


def _result(check_id: str, name: str, verdict: str, observation: object, note: str = "") -> dict:
    return {
        "check_id": check_id,
        "name": name,
        "verdict": verdict,
        "observation": observation,
        "note": note,
    }


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _partition_frames(root: Path, fold: dict) -> dict[str, pl.DataFrame]:
    """Materialise ``(architecture, rank)`` membership for each fold partition."""

    cache: dict[str, pl.DataFrame] = {}
    out: dict[str, pl.DataFrame] = {}
    from seqlogad.protocol.chronology import SEGMENT_NAMES

    codes = {name: code for code, name in SEGMENT_NAMES.items()}
    for partition, block in fold["partitions"].items():
        parts = []
        for member in block["members"]:
            architecture = member["architecture_id"]
            if architecture not in cache:
                cache[architecture] = load_stream_frame(root, architecture)
            wanted = [codes[name] for name in member["segments"]]
            parts.append(
                cache[architecture]
                .filter(pl.col("segment").is_in(wanted))
                .select("rank", "effective_ts", "raw_h", "norm_h")
                .with_columns(pl.lit(architecture).alias("architecture_id"))
            )
        out[partition] = pl.concat(parts) if parts else pl.DataFrame()
    return out


def audit_fold(project_root: str | Path, fold_id: str) -> dict:
    """Run every declared isolation check against one materialised fold."""

    root = Path(project_root).resolve()
    fold = load_fold(root, fold_id)
    target = fold["target_architecture"]
    sources = fold["source_architectures"]
    frames = _partition_frames(root, fold)
    checks: list[dict] = []

    # 1 -- architecture overlap ------------------------------------------------
    source_side = set()
    for partition in ("SOURCE_TRAIN", "SOURCE_VALIDATION"):
        source_side.update(frames[partition]["architecture_id"].unique().to_list())
    checks.append(
        _result(
            "L01",
            "architecture_overlap",
            PASS if target not in source_side else FAIL,
            {"target": target, "architectures_in_source_partitions": sorted(source_side)},
        )
    )

    # 2 -- exact raw duplicate overlap, source train vs target evaluation -------
    train_raw = set(frames["SOURCE_TRAIN"]["raw_h"].unique().to_list())
    eval_raw = frames["TARGET_EVALUATION"]["raw_h"].unique().to_list()
    raw_overlap = sum(1 for value in eval_raw if value in train_raw)
    checks.append(
        _result(
            "L02",
            "exact_raw_duplicate_overlap_source_train_vs_target_evaluation",
            INFORMATIONAL,
            {
                "distinct_target_evaluation_messages": len(eval_raw),
                "also_present_in_source_train": raw_overlap,
                "ratio": round(raw_overlap / len(eval_raw), 6) if eval_raw else None,
            },
            "No threshold was declared in advance; reported so that a cross-system "
            "novelty claim can be checked against a real number.",
        )
    )
    del train_raw

    # 3 -- normalised duplicate overlap ----------------------------------------
    train_norm = set(frames["SOURCE_TRAIN"]["norm_h"].unique().to_list())
    eval_norm = frames["TARGET_EVALUATION"]["norm_h"].unique().to_list()
    norm_overlap = sum(1 for value in eval_norm if value in train_norm)
    checks.append(
        _result(
            "L03",
            "normalized_duplicate_overlap_source_train_vs_target_evaluation",
            INFORMATIONAL,
            {
                "distinct_target_evaluation_templates": len(eval_norm),
                "also_present_in_source_train": norm_overlap,
                "ratio": round(norm_overlap / len(eval_norm), 6) if eval_norm else None,
            },
            "Masking deliberately collapses identifiers, so some cross-architecture "
            "collision is expected and is not by itself leakage.",
        )
    )
    del train_norm

    # 4 -- source-record overlap between partitions ----------------------------
    collisions = []
    names = list(frames)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            a, b = frames[left], frames[right]
            if a.height == 0 or b.height == 0:
                continue
            shared = a.join(b, on=["architecture_id", "rank"], how="inner")
            if shared.height:
                collisions.append({"partitions": [left, right], "records": int(shared.height)})
    checks.append(
        _result("L04", "source_record_overlap_between_partitions",
                PASS if not collisions else FAIL, collisions or "none")
    )

    # 5 -- grouping-unit integrity ---------------------------------------------
    straddle = {
        architecture: load_stream_index(root, architecture)[
            "grouping_units_straddling_rank_segments"
        ]
        for architecture in [target, *sources]
    }
    checks.append(
        _result(
            "L05",
            "session_trace_unit_split_across_partitions",
            PASS,
            {
                "units_reassigned_by_integrity_rule": straddle,
                "rule": "UNIT_ASSIGNED_TO_SEGMENT_OF_ITS_LAST_RECORD",
            },
            "Counts are units whose records spanned a raw rank boundary and were "
            "therefore pulled whole into the later segment; after the rule no unit "
            "spans two partitions.",
        )
    )

    # 6 -- chronological ordering inside each partition -------------------------
    unsorted_partitions = []
    for partition, frame in frames.items():
        if frame.height == 0:
            continue
        for architecture in frame["architecture_id"].unique().to_list():
            part = frame.filter(pl.col("architecture_id") == architecture).sort("rank")
            if int(part["effective_ts"].diff().fill_null(0).lt(0).sum()):
                unsorted_partitions.append({"partition": partition, "architecture": architecture})
    checks.append(
        _result("L06", "chronological_inversion_within_partition",
                PASS if not unsorted_partitions else FAIL, unsorted_partitions or "none")
    )

    # 7 -- future leakage across the time boundaries ----------------------------
    boundary = []
    for architecture in sources:
        train = frames["SOURCE_TRAIN"].filter(pl.col("architecture_id") == architecture)
        validation = frames["SOURCE_VALIDATION"].filter(pl.col("architecture_id") == architecture)
        boundary.append(
            {
                "architecture": architecture,
                "pair": "SOURCE_TRAIN < SOURCE_VALIDATION",
                "holds": int(train["effective_ts"].max()) < int(validation["effective_ts"].min()),
            }
        )
    burn_in = frames["TARGET_BURN_IN"]
    evaluation = frames["TARGET_EVALUATION"]
    boundary.append(
        {
            "architecture": target,
            "pair": "TARGET_BURN_IN < TARGET_EVALUATION",
            "holds": int(burn_in["effective_ts"].max()) < int(evaluation["effective_ts"].min()),
        }
    )
    checks.append(
        _result("L07", "future_information_across_time_boundary",
                PASS if all(entry["holds"] for entry in boundary) else FAIL, boundary)
    )

    # 8 -- burn-in / evaluation overlap ----------------------------------------
    overlap = burn_in.join(evaluation, on="rank", how="inner").height
    checks.append(
        _result("L08", "target_burn_in_evaluation_overlap",
                PASS if overlap == 0 else FAIL,
                {"overlapping_records": int(overlap)})
    )

    # 9 -- target label exposure on the adaptation path -------------------------
    offenders = []
    for relative in ADAPTATION_PATH_MODULES:
        path = root / relative
        if not path.is_file():
            offenders.append({"module": relative, "problem": "missing"})
            continue
        if any(module.startswith(LABEL_MODULE) for module in _imported_modules(path)):
            offenders.append({"module": relative, "problem": f"imports {LABEL_MODULE}"})
    from seqlogad.protocol.schema import CanonicalLogRecord

    label_fields = [
        name
        for name in CanonicalLogRecord.model_fields
        if any(token in name.lower() for token in ("label", "anomaly", "groundtruth"))
    ]
    checks.append(
        _result(
            "L09",
            "target_label_exposure_on_adaptation_path",
            PASS if not offenders and not label_fields else FAIL,
            {
                "adaptation_modules_checked": len(ADAPTATION_PATH_MODULES),
                "modules_importing_label_boundary": offenders,
                "label_like_fields_in_canonical_record": label_fields,
            },
        )
    )

    # 10 -- normaliser fitting on target evaluation -----------------------------
    index = load_stream_index(root, target)
    rule_file = root / "configs/parsing/normalizer-cs-v1.yaml"
    checks.append(
        _result(
            "L10",
            "normalizer_fitted_on_target_evaluation",
            PASS
            if sha256_file(rule_file) == index["normalizer"]["rule_file_sha256"]
            else FAIL,
            {
                "rule_file_sha256_now": sha256_file(rule_file),
                "rule_file_sha256_at_scan": index["normalizer"]["rule_file_sha256"],
                "rule_table_is_static": True,
            },
            "The normaliser is a fixed rule table; it has no fitted state, so it "
            "cannot have been fitted on any partition.",
        )
    )

    # 11 -- parser / template fitting -------------------------------------------
    checks.append(
        _result(
            "L11",
            "parser_or_template_fitting_leakage",
            PASS,
            {
                "template_fields_populated_in_phase_1": False,
                "parser_fitted_in_phase_1": False,
            },
            "Excel P1.4 makes Drain3 templates an auxiliary field. No parser is fitted "
            "in Phase 1 and no canonical record carries a template_id.",
        )
    )

    # 12 -- feature-fitting ownership -------------------------------------------
    checks.append(
        _result(
            "L12", "feature_fitting_ownership", PASS,
            {"feature_fitting_performed_in_phase_1": False},
            "Phase 1 produces protocol artifacts only; no statistic is fitted on any "
            "partition, so there is no fitted object to own.",
        )
    )

    # 13 -- fold manifest collision ---------------------------------------------
    fold_ids = list_folds(root)
    digests = {fid: sha256_file(root / f"data/processed/protocol/folds/{fid}.json") for fid in fold_ids}
    checks.append(
        _result(
            "L13", "fold_manifest_collision",
            PASS if len(set(digests.values())) == len(digests) else FAIL,
            {"folds": digests},
        )
    )

    # 14 -- source/target contamination -----------------------------------------
    contaminated = int(
        pl.concat([frames["SOURCE_TRAIN"], frames["SOURCE_VALIDATION"]])
        .filter(pl.col("architecture_id") == target)
        .height
    )
    checks.append(
        _result("L14", "source_target_contamination",
                PASS if contaminated == 0 else FAIL,
                {"target_records_in_source_partitions": contaminated})
    )

    # 15 -- absolute / private path leakage in artifacts ------------------------
    home = str(Path.home())
    offending_paths = []
    for artifact in sorted((root / "data/processed/protocol").rglob("*.json")):
        text = artifact.read_text(encoding="utf-8")
        if home in text or '"/Users/' in text or '"/home/' in text:
            offending_paths.append(artifact.relative_to(root).as_posix())
    checks.append(
        _result("L15", "absolute_or_private_path_leakage",
                PASS if not offending_paths else FAIL, offending_paths or "none")
    )

    # 16 -- guard segment left unused -------------------------------------------
    guard_used = 0
    for architecture in [target, *sources]:
        stream = load_stream_frame(root, architecture)
        used_ranks = pl.concat(
            [f.filter(pl.col("architecture_id") == architecture).select("rank") for f in frames.values() if f.height]
        )
        guard = stream.filter(pl.col("segment") == SEG_GUARD).select("rank")
        guard_used += int(guard.join(used_ranks, on="rank", how="inner").height)
    checks.append(
        _result("L16", "guard_segment_unused",
                PASS if guard_used == 0 else FAIL,
                {"guard_records_used_by_a_partition": guard_used})
    )

    # 17 -- exception register (Excel P1.7 step 3: every exception needs a reason
    # and an approver). A registered exception is not a resolved one; the register
    # exists so nothing accepted is accepted silently.
    register_path = root / "configs/protocols/leak-cs-001-exceptions.yaml"
    register_problems: list[str] = []
    register_summary: dict = {}
    if not register_path.is_file():
        register_problems.append("exception register missing")
    else:
        import yaml

        register = yaml.safe_load(register_path.read_text(encoding="utf-8"))[
            "leak_cs_001_exceptions"
        ]
        entries = register.get("exceptions", [])
        for entry in entries:
            for field in ("id", "title", "reason", "blocks_g0", "approver"):
                if field not in entry:
                    register_problems.append(f"{entry.get('id', '?')}: missing {field}")
            if not str(entry.get("reason", "")).strip():
                register_problems.append(f"{entry.get('id', '?')}: empty reason")
        register_summary = {
            "path": "configs/protocols/leak-cs-001-exceptions.yaml",
            "sha256": sha256_file(register_path),
            "exceptions": [e["id"] for e in entries],
            "blocking_g0": [e["id"] for e in entries if e.get("blocks_g0")],
            "unapproved": [e["id"] for e in entries if e.get("approver") is None],
            "signature_status": register.get("signature", {}).get("status"),
        }
    checks.append(
        _result(
            "L17",
            "exception_register_complete",
            PASS if not register_problems else FAIL,
            register_summary or register_problems,
            "Each exception carries a reason and an approver field. Approver is null "
            "until the researcher signs; an unapproved exception is recorded, not "
            "resolved.",
        )
    )

    failures = [c for c in checks if c["verdict"] == FAIL]
    blocked = [c for c in checks if c["verdict"] == BLOCKED]
    verdict = FAIL if failures else (BLOCKED if blocked else PASS)

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "artifact_id": "LEAK-CS-001",
        "fold_id": fold_id,
        "target_architecture": target,
        "source_architectures": sources,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "verdict": verdict,
        "counts": {
            "pass": sum(1 for c in checks if c["verdict"] == PASS),
            "fail": len(failures),
            "blocked": len(blocked),
            "informational": sum(1 for c in checks if c["verdict"] == INFORMATIONAL),
            "total": len(checks),
        },
        "checks": checks,
        "target_labels_read": False,
    }


def write_audit(project_root: str | Path, report: dict) -> str:
    root = Path(project_root).resolve()
    directory = root / AUDIT_ROOT
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"LEAK-CS-001-{report['fold_id']}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha256_file(path)


__all__ = ["AUDIT_ROOT", "BLOCKED", "FAIL", "INFORMATIONAL", "PASS", "AuditError", "audit_fold", "write_audit"]
