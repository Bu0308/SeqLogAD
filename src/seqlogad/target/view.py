"""Build one label-free target-fold view (TV-001): buffer, calibration sample, LATE evaluation units."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import yaml

from seqlogad.common.checksum import sha256_file
from seqlogad.semantic.contracts import membership
from seqlogad.target.diagnostics import drift_report, memory
from seqlogad.target.materialize import materialize
from seqlogad.target.units import build_units, build_windows, hash_sample, unit_ids

BURN_IN, EVALUATION = "TARGET_BURN_IN", "TARGET_EVALUATION"


def load_config(root: Path, path: str) -> tuple[dict, str]:
    return yaml.safe_load((root / path).read_text())["target_view"], sha256_file(root / path)


def _inputs(root: Path, cfg: dict, fold_id: str) -> tuple[dict, dict]:
    """Bind the signed fold and buffer artifacts; refuse anything the contracts forbid."""
    if fold_id not in cfg["folds"]:
        raise ValueError(f"{fold_id} is not a TV-001 fold")
    fold = json.loads((root / "data/processed/protocol/folds" / f"{fold_id}.json").read_text())
    if not fold["invariants_all_hold"] or fold["target_labels_read"]:
        raise ValueError(f"{fold_id}: fold invariants do not hold")
    if sha256_file(root / cfg["split_contract"]) != fold["split_contract"]["sha256"]:
        raise ValueError("split contract changed since the fold was signed")
    arch = fold["target_architecture"]
    buffer = json.loads((root / "data/processed/protocol/buffers" / f"BUFFER-{arch}.json").read_text())
    if buffer["readiness"] != "READY" or buffer["target_labels_read"]:
        raise ValueError(f"{arch}: buffer is not READY (BUFFER-REJECT-001)")
    if buffer["buffer_membership_sha256"] != fold["partitions"][BURN_IN]["members"][0]["membership_sha256"]:
        raise ValueError(f"{arch}: buffer membership differs from the fold")
    return fold, buffer


def _check_records(buffer_rows: pl.DataFrame, late: pl.DataFrame, buffer: dict) -> dict:
    if membership(buffer_rows["rank"]) != buffer["buffer_membership_sha256"] or buffer_rows.height != buffer["records"]:
        raise ValueError("materialized buffer membership mismatch")
    checks = {"BUFFER_MEMBERSHIP_MATCHES_SIGNED_BUFFER": True,
              "BUFFER_STRICTLY_PRECEDES_EVALUATION_RANK": int(buffer_rows["rank"].max()) < int(late["rank"].min()),
              "BUFFER_STRICTLY_PRECEDES_EVALUATION_TIME":
                  int(buffer_rows["effective_ts"].max()) <= int(late["effective_ts"].min()),
              "NO_LABEL_COLUMN": not any(c in late.columns for c in ("label", "anomaly", "is_anomaly"))}
    if not all(checks.values()):
        raise ValueError(f"target view invariant failed: {checks}")
    return checks


def _evaluation(late: pl.DataFrame, arch: str, cfg: dict) -> tuple[pl.DataFrame, pl.DataFrame]:
    units = build_units(late, arch, EVALUATION, cfg["strata"], cfg["chunk_lines"], cfg["embargo_seconds"] * 1_000_000)
    total = cfg["evaluation_sample_units"][arch]
    units = units.with_columns(hash_sample(units, total, f"{cfg['selection_tag']}|EVAL").alias("in_sample"))
    windows = build_windows(late, arch, EVALUATION, cfg["context_records"])
    return units, windows


def _calibration(early: pl.DataFrame, arch: str, cfg: dict) -> tuple[pl.DataFrame, pl.DataFrame]:
    units = build_units(early, arch, BURN_IN, cfg["strata"], cfg["chunk_lines"], 0).drop("embargo", "chunk")
    n, recent_from = cfg["calibration"]["units"], round(cfg["strata"] * (1 - cfg["calibration"]["recent_fraction"]))
    tag = cfg["selection_tag"]
    uniform = hash_sample(units, n, f"{tag}|CAL-UNIFORM")
    recent_units = units.filter(pl.col("stratum") >= recent_from)
    recent_ids = set(recent_units.filter(hash_sample(recent_units, n, f"{tag}|CAL-RECENT"))["unit_id"].to_list())
    units = units.with_columns(uniform.alias("cal_uniform"), pl.col("unit_id").is_in(list(recent_ids)).alias("cal_recent")
                               ).filter(pl.col("cal_uniform") | pl.col("cal_recent"))
    windows = build_windows(early, arch, BURN_IN, cfg["context_records"], keep=set(units["unit_id"].to_list()))
    return units, windows


def _line_strata(late: pl.DataFrame, units: pl.DataFrame, arch: str) -> pl.Series:
    ids = late.select(unit_ids(late, arch, EVALUATION))
    return ids.join(units.select("unit_id", "stratum"), on="unit_id", how="left")["stratum"]


def _summary(units: pl.DataFrame, windows: pl.DataFrame, sampled: set[str] | None = None) -> dict:
    if sampled is not None:
        windows = windows.filter(pl.col("unit_id").is_in(list(sampled)))
        units = units.filter(pl.col("unit_id").is_in(list(sampled)))
    return {"units": units.height, "lines": int(units["n_lines"].sum()), "windows": windows.height,
            "distinct_windows": windows["dedupe_key"].n_unique()}


def build_view(root: Path, config_path: str, fold_id: str, out: Path) -> dict:
    cfg, cfg_sha = load_config(root, config_path)
    fold, buffer = _inputs(root, cfg, fold_id)
    arch = fold["target_architecture"]
    records, index = materialize(root, arch, ["EARLY", "LATE"], cfg["template_min_digits"])
    early, late = records.filter(pl.col("segment") == 0), records.filter(pl.col("segment") == 3)
    checks = _check_records(early, late, buffer)
    eval_units, eval_windows = _evaluation(late, arch, cfg)
    cal_units, cal_windows = _calibration(early, arch, cfg)
    sampled = set(eval_units.filter(pl.col("in_sample"))["unit_id"].to_list())
    manifest = {
        "artifact_id": "TV-001", "fold_id": fold_id, "target_architecture": arch,
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "target_labels_read": False,
        "config": {"path": config_path, "sha256": cfg_sha, "values": cfg},
        "bindings": {"fold_sha256": sha256_file(root / "data/processed/protocol/folds" / f"{fold_id}.json"),
                     "buffer_membership_sha256": buffer["buffer_membership_sha256"],
                     "stream_parquet_sha256": index["stream_parquet_sha256"],
                     "normalizer_rule_file_sha256": index["normalizer"]["rule_file_sha256"],
                     "builder_code_sha256": {p.name: sha256_file(p) for p in sorted(Path(__file__).parent.glob("*.py"))}},
        "invariants": checks,
        "segments": {"buffer": {"records": early.height}, "evaluation_late": {"records": late.height}},
        "evaluation": {"full": _summary(eval_units, eval_windows), "sample": _summary(eval_units, eval_windows, sampled),
                       "embargo_units": int(eval_units["embargo"].sum())},
        "calibration": {"uniform": int(cal_units["cal_uniform"].sum()), "recent": int(cal_units["cal_recent"].sum()),
                        "windows": cal_windows.height, "distinct_windows": cal_windows["dedupe_key"].n_unique()},
        "drift": drift_report(early, late, _line_strata(late, eval_units, arch)),
    }
    _write(out / fold_id, early, late, eval_units, eval_windows, cal_units, cal_windows, manifest)
    return manifest


def _write(base: Path, early, late, eval_units, eval_windows, cal_units, cal_windows, manifest: dict) -> None:
    if base.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {base}")
    files = {"buffer/records.parquet": early.drop("segment"), "buffer/memory.parquet": memory(early),
             "buffer/calibration_units.parquet": cal_units, "buffer/calibration_windows.parquet": cal_windows,
             "evaluation/events.parquet": late.drop("segment"), "evaluation/units.parquet": eval_units,
             "evaluation/windows.parquet": eval_windows}
    for name, frame in files.items():
        (base / name).parent.mkdir(parents=True, exist_ok=True)
        frame.write_parquet(base / name, compression="zstd")
    manifest["files"] = {name: sha256_file(base / name) for name in files}
    (base / "manifests").mkdir()
    (base / "manifests/view.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
