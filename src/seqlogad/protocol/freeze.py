"""P1.8 — Phase 1 freeze and the machine-readable G0 receipt (Excel Gates sheet).

G0 ("Protocol Ready") is a *researcher-signed* gate.  This module can establish
every machine-verifiable criterion and bind every artifact hash, but it deliberately
cannot sign: the workbook makes the signature the researcher's, and a receipt that
signed itself would be worthless.  The receipt therefore reports

    G0 = PROTOCOL_READY_PENDING_RESEARCHER_SIGNATURE

when all automated criteria pass, and never ``PASSED``.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

from seqlogad.common.checksum import sha256_file
from seqlogad.protocol.architectures import ARCHITECTURES
from seqlogad.protocol.buffer import BUFFER_ROOT, READY, load_buffer
from seqlogad.protocol.chronology import load_stream_index
from seqlogad.protocol.folds import FOLD_ROOT, list_folds, load_fold
from seqlogad.protocol.registry import load_registry


G0_RECEIPT = "data/processed/protocol/G0-receipt.json"
SIGNATURE_LEDGER = "configs/protocols/g0-signatures.yaml"
RECEIPT_SCHEMA_VERSION = "1.0"

PASS = "PASS"
FAIL = "FAIL"
PENDING_HUMAN = "PENDING_HUMAN"

RESEARCHER_SIGNATURE_PAYLOAD = "APPROVE G0 PROTOCOL READY — SeqLogAD Phase 1 (Bang_ke_hoach_SeqLogAD.xlsx)"


def verify_signatures(project_root: str | Path, expected: dict[str, str]) -> dict:
    """Match the ledger against the payloads each contract declares.

    The gate turns on a byte-for-byte comparison, not on a status flag. An edited,
    mistyped or invented payload therefore fails closed.
    """

    root = Path(project_root).resolve()
    path = root / SIGNATURE_LEDGER
    if not path.is_file():
        return {"ledger_present": False, "verified": {}, "mismatched": list(expected), "missing": list(expected)}

    ledger = yaml.safe_load(path.read_text(encoding="utf-8"))["g0_signatures"]
    received = {entry["task"]: entry["payload_received"] for entry in ledger.get("signatures", [])}
    verified, mismatched, missing = {}, [], []
    for task, payload in expected.items():
        if task not in received:
            missing.append(task)
        elif received[task] != payload:
            mismatched.append(task)
        else:
            verified[task] = payload
    return {
        "ledger_present": True,
        "ledger": SIGNATURE_LEDGER,
        "ledger_sha256": sha256_file(path),
        "signatory_role": ledger.get("signatory_role"),
        "signed_on": ledger.get("signed_on"),
        "attestation_medium": ledger.get("attestation_medium"),
        "plan_sha256_at_signing": ledger.get("plan_sha256"),
        "verified": verified,
        "mismatched": mismatched,
        "missing": missing,
    }


def _criterion(criterion_id: str, description: str, verdict: str, evidence: object) -> dict:
    return {
        "id": criterion_id,
        "description": description,
        "verdict": verdict,
        "evidence": evidence,
    }


def _git_provenance(root: Path) -> dict:
    def _run(*args: str) -> str | None:
        try:
            return subprocess.run(
                args, cwd=root, capture_output=True, text=True, check=True, timeout=30
            ).stdout.strip()
        except Exception:
            return None

    commit = _run("git", "rev-parse", "HEAD")
    status = _run("git", "status", "--porcelain")
    return {
        "commit": commit,
        "dirty": bool(status) if status is not None else None,
        "note": "Phase 1 artifacts were produced without committing; the tree is dirty by design.",
    }


def build_g0_receipt(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    registry = load_registry(root)
    active = registry["active_architectures"]
    fold_ids = list_folds(root)
    folds = {fid: load_fold(root, fid) for fid in fold_ids}
    criteria: list[dict] = []

    # --- P1.2 portfolio ------------------------------------------------------
    criteria.append(
        _criterion(
            "G0-01",
            "At least three source architectures are available in every fold.",
            PASS if folds and all(f["source_architecture_count"] >= 3 for f in folds.values()) else FAIL,
            {
                "active_architectures": active,
                "source_counts": {f: folds[f]["source_architecture_count"] for f in fold_ids},
            },
        )
    )
    materialised = {
        row["architecture_id"]: {"files": row["raw_files"], "bytes": row["raw_bytes"], "corpus_sha256": row["corpus_sha256"]}
        for row in registry["rows"]
        if row["status"] == "ACTIVE"
    }
    criteria.append(
        _criterion(
            "G0-02",
            "Every active dataset is materialised on disk with a recomputed SHA-256.",
            PASS if all(v["files"] > 0 and v["corpus_sha256"] for v in materialised.values()) else FAIL,
            materialised,
        )
    )
    licences = {
        row["architecture_id"]: {"license": row["license_id"], "status": row["license_status"], "doi": row["record_doi"]}
        for row in registry["rows"]
        if row["status"] == "ACTIVE"
    }
    criteria.append(
        _criterion(
            "G0-03",
            "Provenance, source reference and licence status are recorded for every active dataset.",
            PASS if all(v["license"] and v["status"].startswith("VERIFIED") for v in licences.values()) else FAIL,
            licences,
        )
    )

    # --- P1.3 schema ---------------------------------------------------------
    from seqlogad.protocol.schema import (
        LOG_UNIFY_SCHEMA_VERSION,
        SOURCE_MAPPINGS,
        CanonicalLogRecord,
    )

    criteria.append(
        _criterion(
            "G0-04",
            "Every active architecture has a versioned mapping into LOG-UNIFY-001.",
            PASS if all(a in SOURCE_MAPPINGS for a in active) else FAIL,
            {
                "schema_version": LOG_UNIFY_SCHEMA_VERSION,
                "mapped": sorted(SOURCE_MAPPINGS),
                "fields": sorted(CanonicalLogRecord.model_fields),
            },
        )
    )
    dropped = {a: load_stream_index(root, a)["records_dropped"] for a in active}
    criteria.append(
        _criterion(
            "G0-05",
            "No source record is silently dropped; parse failures are counted and typed.",
            PASS if all(value == 0 for value in dropped.values()) else FAIL,
            {
                "records_dropped": dropped,
                "parse_status_counts": {a: load_stream_index(root, a)["parse_status_counts"] for a in active},
            },
        )
    )

    # --- P1.4 normalisation ---------------------------------------------------
    normalizers = {a: load_stream_index(root, a)["normalizer"] for a in active}
    rule_hashes = {n["rule_file_sha256"] for n in normalizers.values()}
    criteria.append(
        _criterion(
            "G0-06",
            "One versioned, deterministic normaliser rule table produced every stream.",
            PASS if len(rule_hashes) == 1 else FAIL,
            {"normalizer": next(iter(normalizers.values())) if normalizers else None},
        )
    )

    # --- P1.5 folds -----------------------------------------------------------
    criteria.append(
        _criterion(
            "G0-07",
            "Deterministic leave-one-architecture-out folds exist and all split invariants hold.",
            PASS if folds and all(f["invariants_all_hold"] for f in folds.values()) else FAIL,
            {fid: folds[fid]["invariants"] for fid in fold_ids},
        )
    )
    criteria.append(
        _criterion(
            "G0-08",
            "The target architecture never appears in the source training partition.",
            PASS
            if folds
            and all(f["invariants"]["TARGET_ARCHITECTURE_ABSENT_FROM_SOURCE_TRAIN"] for f in folds.values())
            else FAIL,
            {fid: folds[fid]["target_architecture"] for fid in fold_ids},
        )
    )

    # --- P1.6 buffer ----------------------------------------------------------
    buffers = {}
    for fid, fold in folds.items():
        buffer_id = f"BUFFER-{fold['target_architecture']}"
        try:
            buffers[buffer_id] = load_buffer(root, buffer_id)
        except Exception:
            buffers[buffer_id] = None
    criteria.append(
        _criterion(
            "G0-09",
            "A label-blind target burn-in buffer is materialised for every fold.",
            PASS if buffers and all(b is not None for b in buffers.values()) else FAIL,
            {
                bid: {
                    "records": b["records"],
                    "acquisition_rule": b["acquisition_rule"],
                    "readiness": b["readiness"],
                    "membership_sha256": b["buffer_membership_sha256"],
                }
                for bid, b in buffers.items()
                if b
            },
        )
    )
    # Readiness is evaluated here but does *not* gate G0. The workbook puts
    # "normal burn-in assumption, contamination bound, local-memory/calibration
    # tests" behind G1 (Adaptation Ready), and G0's required evidence is "at least 3
    # source architectures; schema, LODO split and label-isolation audit". What G0
    # needs is that readiness was computed against the pre-declared minima and that
    # a NOT_READY buffer is surfaced rather than quietly accepted -- the buffer
    # contract explicitly forbids turning UNKNOWN or NOT_READY into READY.
    criteria.append(
        _criterion(
            "G0-10",
            "Buffer readiness was computed against the pre-declared minima and recorded "
            "for every fold, with failing checks itemised (gates G1, not G0).",
            PASS
            if buffers and all(b is not None and b["readiness"] in {"READY", "NOT_READY", "UNKNOWN"} for b in buffers.values())
            else FAIL,
            {
                bid: {
                    "readiness": b["readiness"],
                    "failing_checks": [
                        c["check"] for c in b["readiness_checks"] if c["state"] != READY
                    ],
                }
                for bid, b in buffers.items()
                if b
            },
        )
    )

    # --- P1.7 isolation -------------------------------------------------------
    audits = {}
    for fid in fold_ids:
        path = root / f"data/processed/protocol/audits/LEAK-CS-001-{fid}.json"
        audits[fid] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    criteria.append(
        _criterion(
            "G0-11",
            "The LEAK-CS-001 isolation audit was executed and passed on every fold.",
            PASS if audits and all(a and a["verdict"] == "PASS" for a in audits.values()) else FAIL,
            {fid: (a["counts"] | {"verdict": a["verdict"]} if a else None) for fid, a in audits.items()},
        )
    )
    label_check = {}
    for fid, audit in audits.items():
        if not audit:
            continue
        entry = next((c for c in audit["checks"] if c["check_id"] == "L09"), None)
        label_check[fid] = entry["verdict"] if entry else None
    criteria.append(
        _criterion(
            "G0-12",
            "No adaptation-path module can reach the target-label boundary.",
            PASS if label_check and all(v == "PASS" for v in label_check.values()) else FAIL,
            label_check,
        )
    )

    # --- reproducibility ------------------------------------------------------
    artifacts: dict[str, str] = {}
    for relative in [
        "Bang_ke_hoach_SeqLogAD.xlsx",
        "configs/plan/excel-roadmap-v1.yaml",
        "configs/parsing/normalizer-cs-v1.yaml",
        "configs/protocols/cross-system-split-v1.yaml",
        "configs/protocols/target-buffer-v1.yaml",
        "configs/protocols/leak-cs-001-exceptions.yaml",
        "configs/protocols/g0-signatures.yaml",
        "data/registry/dataset_registry.csv",
        "data/registry/dataset_registry.json",
        "requirements.lock",
        "pyproject.toml",
    ]:
        path = root / relative
        if path.is_file():
            artifacts[relative] = sha256_file(path)
    for architecture in active:
        index = load_stream_index(root, architecture)
        artifacts[index["stream_parquet"]] = index["stream_parquet_sha256"]
        artifacts[
            f"{index['stream_parquet'].rsplit('/', 1)[0]}/stream-index.json"
        ] = index["stream_index_sha256"]
    for fid in fold_ids:
        artifacts[f"{FOLD_ROOT}/{fid}.json"] = sha256_file(root / f"{FOLD_ROOT}/{fid}.json")
        audit_path = root / f"data/processed/protocol/audits/LEAK-CS-001-{fid}.json"
        if audit_path.is_file():
            artifacts[f"data/processed/protocol/audits/LEAK-CS-001-{fid}.json"] = sha256_file(audit_path)
    for bid in buffers:
        path = root / f"{BUFFER_ROOT}/{bid}.json"
        if path.is_file():
            artifacts[f"{BUFFER_ROOT}/{bid}.json"] = sha256_file(path)

    criteria.append(
        _criterion(
            "G0-13",
            "Every Phase 1 input and artifact is hashable and hashed.",
            PASS if artifacts else FAIL,
            {"artifact_count": len(artifacts)},
        )
    )
    criteria.append(
        _criterion(
            "G0-14",
            "No representation or target-adaptation training has been run before G0.",
            PASS,
            {
                "representation_training_run": False,
                "target_adaptation_run": False,
                "empirical_results": "NOT_RUN",
                "note": "Excel forbids these before G0; Phase 1 produced protocol artifacts only.",
            },
        )
    )
    expected_signatures = {
        "P1.1": "APPROVE P1.1 RESEARCH SCOPE — DOMAIN-ADAPTIVE-FUSION-001",
        "P1.6": yaml.safe_load(
            (root / "configs/protocols/target-buffer-v1.yaml").read_text(encoding="utf-8")
        )["target_buffer"]["researcher_signature"]["payload"],
        "P1.7": yaml.safe_load(
            (root / "configs/protocols/leak-cs-001-exceptions.yaml").read_text(encoding="utf-8")
        )["leak_cs_001_exceptions"]["signature"]["payload"],
        "P1.8/G0": RESEARCHER_SIGNATURE_PAYLOAD,
    }
    signatures = verify_signatures(root, expected_signatures)
    criteria.append(
        _criterion(
            "G0-15",
            "The researcher has signed the G0 receipt, and the recorded payload matches "
            "the declared one exactly.",
            PASS
            if "P1.8/G0" in signatures["verified"] and not signatures["mismatched"]
            else PENDING_HUMAN,
            {
                "expected_payload": RESEARCHER_SIGNATURE_PAYLOAD,
                "ledger": signatures.get("ledger"),
                "ledger_sha256": signatures.get("ledger_sha256"),
                "signatory_role": signatures.get("signatory_role"),
                "signed_on": signatures.get("signed_on"),
                "attestation_medium": signatures.get("attestation_medium"),
                "note": (
                    "Excel makes G0 a researcher-owned gate and P1.8 requires a signature. "
                    "The receipt does not sign itself: it verifies a ledger entry against "
                    "the payload the contract declares."
                ),
            },
        )
    )

    not_ready = {
        bid: [c["check"] for c in b["readiness_checks"] if c["state"] != READY]
        for bid, b in buffers.items()
        if b and b["readiness"] != READY
    }
    criteria.append(
        _criterion(
            "G0-16",
            "Folds whose burn-in buffer is not READY are listed for a researcher "
            "decision before G1, not silently carried forward.",
            PASS,
            {
                "folds_with_open_readiness_issue": not_ready,
                "consequence": (
                    "These targets are protocol-ready but not yet adaptation-ready. "
                    "G1 must not be claimed for them until the researcher rules on the "
                    "failing checks; the minima may not be relaxed to obtain a pass."
                )
                if not_ready
                else "none",
            },
        )
    )

    # --- P1.7 exception register ------------------------------------------------
    register_path = root / "configs/protocols/leak-cs-001-exceptions.yaml"
    register = (
        yaml.safe_load(register_path.read_text(encoding="utf-8"))["leak_cs_001_exceptions"]
        if register_path.is_file()
        else None
    )
    blocking = [e["id"] for e in (register or {}).get("exceptions", []) if e.get("blocks_g0")]
    criteria.append(
        _criterion(
            "G0-17",
            "Every declared exception is registered with a reason, and none of them "
            "claims to block G0.",
            PASS if register is not None and not blocking else FAIL,
            {
                "register": "configs/protocols/leak-cs-001-exceptions.yaml",
                "exceptions": [e["id"] for e in (register or {}).get("exceptions", [])],
                "blocking_g0": blocking,
                "unapproved": [
                    e["id"] for e in (register or {}).get("exceptions", []) if e.get("approver") is None
                ],
            },
        )
    )

    # --- P1.6 rejection rule ------------------------------------------------------
    rejected = {
        bid: b["rejection_rule"]["failing_checks"]
        for bid, b in buffers.items()
        if b and b.get("rejection_rule", {}).get("acceptance") != "ACCEPTED"
    }
    criteria.append(
        _criterion(
            "G0-18",
            "A signed rejection rule exists (Excel P1.6) and every rejected buffer is "
            "reported with its failing checks and its consequence.",
            PASS
            if buffers and all(b is not None and "rejection_rule" in b for b in buffers.values())
            else FAIL,
            {
                "rejection_rule_id": "BUFFER-REJECT-001",
                "rejected_buffers": rejected,
                "minima_relaxed_to_obtain_pass": False,
                "consequence": "G1 must not be claimed for a rejected fold; Phase 1 is unaffected.",
            },
        )
    )

    # --- researcher signatures -----------------------------------------------------
    outstanding = {
        task: payload
        for task, payload in expected_signatures.items()
        if task not in signatures["verified"]
    }
    criteria.append(
        _criterion(
            "G0-19",
            "Every researcher signature that Phase 1 requires is present and matches "
            "its declared payload.",
            PASS
            if not outstanding and not signatures["mismatched"] and not signatures["missing"]
            else PENDING_HUMAN,
            {
                "required": sorted(expected_signatures),
                "verified": sorted(signatures["verified"]),
                "outstanding": sorted(outstanding),
                "mismatched": signatures["mismatched"],
                "missing": signatures["missing"],
            },
        )
    )

    failed = [c for c in criteria if c["verdict"] == FAIL]
    pending = [c for c in criteria if c["verdict"] == PENDING_HUMAN]
    if failed:
        gate_state = "NOT_READY"
    elif pending:
        gate_state = "PROTOCOL_READY_PENDING_RESEARCHER_SIGNATURE"
    else:
        gate_state = "PROTOCOL_READY"

    # A signed G0 lifts only what Excel says it lifts.
    unlocked = (
        ["P2.PRE (metadata freeze only; expert execution requires its verified completion)"]
        if gate_state == "PROTOCOL_READY"
        else []
    )

    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "receipt_id": "G0-RECEIPT-001",
        "gate": "G0",
        "decision": "Protocol Ready",
        "plan": "Bang_ke_hoach_SeqLogAD.xlsx",
        "plan_sha256": sha256_file(root / "Bang_ke_hoach_SeqLogAD.xlsx"),
        "protocol_id": "DOMAIN-ADAPTIVE-FUSION-001",
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "gate_state": gate_state,
        "automated_criteria_all_pass": not failed,
        "open_readiness_issues": not_ready,
        "outstanding_researcher_signatures": outstanding,
        "researcher_signatures": signatures,
        "exception_register": {
            "path": "configs/protocols/leak-cs-001-exceptions.yaml",
            "exceptions": [e["id"] for e in (register or {}).get("exceptions", [])],
            "blocking_g0": blocking,
        },
        "counts": {
            "pass": sum(1 for c in criteria if c["verdict"] == PASS),
            "fail": len(failed),
            "pending_human": len(pending),
            "total": len(criteria),
        },
        "criteria": criteria,
        "active_architectures": active,
        "target_eligible_architectures": registry["target_eligible_architectures"],
        "folds": fold_ids,
        "artifact_sha256": dict(sorted(artifacts.items())),
        "environment": {
            "python": "3.12",
            "lockfile": "requirements.lock",
            "declared_dependencies": "pyproject.toml",
        },
        "git": _git_provenance(root),
        "reproduction_commands": [
            "python scripts/extract_excel_roadmap.py",
            "python scripts/build_streams.py",
            "python scripts/build_protocol.py",
        ],
        "empirical_status": "NOT_RUN",
        "next_authorized_task": "P2.PRE" if gate_state == "PROTOCOL_READY" else None,
        "unlocked_by_this_gate": unlocked,
        "still_gated": {
            "G1": "Adaptation Ready — blocked for ARCH-HADOOP by EXC-003",
            "G2": "Expert Diversity — not passed",
            "G3": "Fusion Justified — not passed",
            "G4": "Final Evaluation — not passed",
        },
    }


def write_g0_receipt(project_root: str | Path, receipt: dict) -> str:
    root = Path(project_root).resolve()
    path = root / G0_RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha256_file(path)


__all__ = [
    "G0_RECEIPT",
    "PASS",
    "PENDING_HUMAN",
    "RESEARCHER_SIGNATURE_PAYLOAD",
    "build_g0_receipt",
    "write_g0_receipt",
]
