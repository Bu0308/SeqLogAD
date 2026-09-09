"""The generated Phase 1 artifacts must satisfy the contracts that produced them.

These assertions run against the *materialised* registry, folds, buffers, audits and
G0 receipt, so they fail if a rebuild silently changes the protocol.  They skip when
the artifacts are absent, because building them needs the raw corpora.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_ROOT = PROJECT_ROOT / "data/processed/protocol"

pytestmark = pytest.mark.skipif(
    not (PROTOCOL_ROOT / "G0-receipt.json").is_file(),
    reason="Phase 1 artifacts not built; run scripts/build_streams.py then build_protocol.py",
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def receipt() -> dict:
    return _json(PROTOCOL_ROOT / "G0-receipt.json")


@pytest.fixture(scope="module")
def registry() -> dict:
    return _json(PROJECT_ROOT / "data/registry/dataset_registry.json")


@pytest.fixture(scope="module")
def folds() -> list[dict]:
    return [_json(path) for path in sorted((PROTOCOL_ROOT / "folds").glob("FOLD-TARGET-*.json"))]


@pytest.fixture(scope="module")
def audits() -> list[dict]:
    return [_json(path) for path in sorted((PROTOCOL_ROOT / "audits").glob("LEAK-CS-001-*.json"))]


@pytest.fixture(scope="module")
def buffers() -> list[dict]:
    return [_json(path) for path in sorted((PROTOCOL_ROOT / "buffers").glob("BUFFER-*.json"))]


# --- P1.2 -------------------------------------------------------------------

def test_registry_has_at_least_four_active_architectures(registry: dict) -> None:
    assert len(registry["active_architectures"]) >= 4


def test_every_active_row_records_verified_provenance(registry: dict) -> None:
    for row in registry["rows"]:
        if row["status"] != "ACTIVE":
            continue
        assert row["license_status"].startswith("VERIFIED")
        assert row["record_doi"].startswith("https://doi.org/")
        assert len(row["corpus_sha256"]) == 64
        assert row["raw_files"] > 0
        assert row["record_count"] and row["record_count"] > 0
        assert row["label_available"] == "YES"
        assert row["label_access_policy"] == "EVALUATION_ONLY"


def test_rejected_candidates_carry_a_reason(registry: dict) -> None:
    for row in registry["rows"]:
        if row["status"] in {"REJECTED", "CANDIDATE"}:
            assert row["disposition_reason"].strip()


def test_unverified_label_availability_is_not_claimed(registry: dict) -> None:
    for row in registry["rows"]:
        if row["status"] != "ACTIVE":
            assert row["label_available"] in {"NOT_VERIFIED", "UNKNOWN"}


# --- P1.5 -------------------------------------------------------------------

def test_every_fold_has_at_least_three_source_architectures(folds: list[dict]) -> None:
    assert folds
    for fold in folds:
        assert fold["source_architecture_count"] >= 3


def test_every_split_invariant_holds_on_every_fold(folds: list[dict]) -> None:
    for fold in folds:
        assert fold["invariants_all_hold"], fold["fold_id"]
        for name, holds in fold["invariants"].items():
            assert holds, f"{fold['fold_id']}: {name}"


def test_target_never_appears_among_source_architectures(folds: list[dict]) -> None:
    for fold in folds:
        assert fold["target_architecture"] not in fold["source_architectures"]


def test_burn_in_strictly_precedes_evaluation(folds: list[dict]) -> None:
    for fold in folds:
        burn_in = fold["partitions"]["TARGET_BURN_IN"]["members"][0]
        evaluation = fold["partitions"]["TARGET_EVALUATION"]["members"][0]
        assert burn_in["last_timestamp_utc"] < evaluation["first_timestamp_utc"]
        assert burn_in["last_rank"] < evaluation["first_rank"]


def test_folds_declare_no_label_use_and_no_seed(folds: list[dict]) -> None:
    for fold in folds:
        assert fold["target_labels_read"] is False
        assert fold["seed"] is None
        assert fold["determinism"] == "FLOOR_BOUNDARIES_ON_CHRONOLOGICAL_RANK"


def test_only_target_eligible_architectures_are_held_out(folds: list[dict]) -> None:
    from seqlogad.protocol.architectures import ARCHITECTURES, TargetEligibility

    for fold in folds:
        spec = ARCHITECTURES[fold["target_architecture"]]
        assert spec.target_eligibility is TargetEligibility.ELIGIBLE


def test_source_only_architecture_still_serves_as_a_source(folds: list[dict]) -> None:
    from seqlogad.protocol.architectures import ARCHITECTURES, TargetEligibility

    source_only = [
        key
        for key, spec in ARCHITECTURES.items()
        if spec.target_eligibility is TargetEligibility.SOURCE_ONLY
    ]
    for architecture in source_only:
        assert all(architecture in fold["source_architectures"] for fold in folds)


# --- P1.6 -------------------------------------------------------------------

def test_buffers_are_acquired_label_blind(buffers: list[dict]) -> None:
    assert buffers
    for buffer in buffers:
        assert buffer["acquisition_rule"] == "LABEL_BLIND_CHRONOLOGICAL_PREFIX"
        assert buffer["forbidden_operation"] == "SELECT_RECORDS_WHERE_LABEL_EQUALS_NORMAL"
        assert buffer["target_labels_read"] is False
        assert buffer["label_columns_present"] == []


def test_buffer_contamination_is_an_assumption_not_a_measurement(buffers: list[dict]) -> None:
    for buffer in buffers:
        contamination = buffer["contamination"]
        assert contamination["measured"] is None
        assert contamination["measurement_boundary"] == "FINAL_EVALUATION"
        assert 0 < contamination["declared_bound_fraction"] < 1


def test_buffer_provenance_is_complete(buffers: list[dict]) -> None:
    required = {
        "split_contract_sha256",
        "buffer_contract_sha256",
        "stream_index_sha256",
        "stream_parquet_sha256",
        "normalizer_rule_file_sha256",
    }
    for buffer in buffers:
        assert required <= set(buffer["provenance"])
        assert len(buffer["buffer_membership_sha256"]) == 64


def test_readiness_is_never_silently_upgraded(buffers: list[dict]) -> None:
    for buffer in buffers:
        states = {check["state"] for check in buffer["readiness_checks"]}
        if "NOT_READY" in states:
            assert buffer["readiness"] == "NOT_READY"
        elif "UNKNOWN" in states:
            assert buffer["readiness"] == "UNKNOWN"
        else:
            assert buffer["readiness"] == "READY"


def test_readiness_checks_never_read_labels(buffers: list[dict]) -> None:
    for buffer in buffers:
        for check in buffer["readiness_checks"]:
            assert check["reads_labels"] is False


# --- P1.7 -------------------------------------------------------------------

def test_isolation_audit_passed_on_every_fold(audits: list[dict]) -> None:
    assert audits
    for audit in audits:
        assert audit["verdict"] == "PASS", audit["fold_id"]
        assert audit["counts"]["fail"] == 0
        assert audit["target_labels_read"] is False


def test_audit_covers_every_declared_check(audits: list[dict]) -> None:
    expected = {f"L{index:02d}" for index in range(1, 18)}
    for audit in audits:
        assert {check["check_id"] for check in audit["checks"]} == expected


def test_informational_checks_are_not_counted_as_passes(audits: list[dict]) -> None:
    for audit in audits:
        informational = [c for c in audit["checks"] if c["verdict"] == "INFORMATIONAL"]
        assert audit["counts"]["informational"] == len(informational)
        assert audit["counts"]["pass"] + audit["counts"]["informational"] <= audit["counts"]["total"]


# --- P1.8 / G0 ---------------------------------------------------------------

def test_g0_signature_is_verified_against_the_ledger_not_asserted(receipt: dict) -> None:
    """G0 turns on an exact payload match, so a flag alone can never pass it."""

    criterion = next(c for c in receipt["criteria"] if c["id"] == "G0-15")
    ledger = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/g0-signatures.yaml").read_text(encoding="utf-8")
    )["g0_signatures"]
    received = {e["task"]: e["payload_received"] for e in ledger["signatures"]}
    assert received["P1.8/G0"] == criterion["evidence"]["expected_payload"]
    assert criterion["verdict"] == "PASS"
    assert receipt["gate_state"] == "PROTOCOL_READY"


def test_every_required_signature_matches_its_declared_payload(receipt: dict) -> None:
    ledger = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/g0-signatures.yaml").read_text(encoding="utf-8")
    )["g0_signatures"]
    received = {e["task"]: e["payload_received"] for e in ledger["signatures"]}

    buffer_payload = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/target-buffer-v1.yaml").read_text(encoding="utf-8")
    )["target_buffer"]["researcher_signature"]["payload"]
    register_payload = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/leak-cs-001-exceptions.yaml").read_text(encoding="utf-8")
    )["leak_cs_001_exceptions"]["signature"]["payload"]

    assert received["P1.6"] == buffer_payload
    assert received["P1.7"] == register_payload
    assert received["P1.1"] == "APPROVE P1.1 RESEARCH SCOPE — DOMAIN-ADAPTIVE-FUSION-001"

    criterion = next(c for c in receipt["criteria"] if c["id"] == "G0-19")
    assert criterion["verdict"] == "PASS"
    assert criterion["evidence"]["mismatched"] == []
    assert criterion["evidence"]["missing"] == []
    assert criterion["evidence"]["outstanding"] == []


def test_signing_g0_does_not_silently_unlock_later_gates(receipt: dict) -> None:
    """A signed G0 lifts exactly what Excel says it lifts, and nothing else."""

    assert receipt["unlocked_by_this_gate"] == [
        "P2.1 (representation and target-adaptation work is no longer forbidden)"
    ]
    assert set(receipt["still_gated"]) == {"G1", "G2", "G3", "G4"}
    assert "EXC-003" in receipt["still_gated"]["G1"]
    assert receipt["empirical_status"] == "NOT_RUN"


def test_approved_exceptions_are_acknowledged_not_resolved() -> None:
    spec = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/leak-cs-001-exceptions.yaml").read_text(encoding="utf-8")
    )["leak_cs_001_exceptions"]
    assert spec["signature"]["status"] == "SIGNED"
    for entry in spec["exceptions"]:
        assert entry["approver"], f"{entry['id']} has no approver"
    hadoop = next(e for e in spec["exceptions"] if e["id"] == "EXC-003")
    assert hadoop["blocks_g1"] is True, "approval must not lift the G1 block"


def test_all_automated_criteria_pass(receipt: dict) -> None:
    failures = [c["id"] for c in receipt["criteria"] if c["verdict"] == "FAIL"]
    assert failures == []
    assert receipt["automated_criteria_all_pass"] is True
    assert receipt["counts"]["pending_human"] == 0


def test_receipt_forbids_pre_g0_training(receipt: dict) -> None:
    criterion = next(c for c in receipt["criteria"] if c["id"] == "G0-14")
    assert criterion["evidence"]["representation_training_run"] is False
    assert criterion["evidence"]["target_adaptation_run"] is False
    assert receipt["empirical_status"] == "NOT_RUN"


def test_receipt_binds_every_contract_hash(receipt: dict) -> None:
    artifacts = receipt["artifact_sha256"]
    for required in (
        "Bang_ke_hoach_SeqLogAD.xlsx",
        "configs/plan/excel-roadmap-v1.yaml",
        "configs/parsing/normalizer-cs-v1.yaml",
        "configs/protocols/cross-system-split-v1.yaml",
        "configs/protocols/target-buffer-v1.yaml",
        "data/registry/dataset_registry.json",
    ):
        assert required in artifacts
        assert len(artifacts[required]) == 64


def test_receipt_hashes_match_the_files_on_disk(receipt: dict) -> None:
    from seqlogad.common.checksum import sha256_file

    migration = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/phase2-roadmap-migration-v1.yaml").read_text()
    )["migration"]
    # The unchanged receipt binds its historical roadmap, not the migrated plan.
    assert receipt["plan_sha256"] == migration["from_sha256"]
    for relative, digest in receipt["artifact_sha256"].items():
        path = PROJECT_ROOT / migration["historical_receipt_bindings"].get(relative, relative)
        if path.is_file():
            assert sha256_file(path) == digest, relative


def test_historical_receipt_preserves_its_original_task_namespace(receipt: dict) -> None:
    assert receipt["next_authorized_task"] == "P2.1"


def test_open_readiness_issues_are_surfaced(receipt: dict) -> None:
    criterion = next(c for c in receipt["criteria"] if c["id"] == "G0-16")
    assert criterion["verdict"] == "PASS"
    assert "folds_with_open_readiness_issue" in criterion["evidence"]


# --- contracts ---------------------------------------------------------------

def test_rejection_rule_is_applied_and_never_relaxed(buffers: list[dict]) -> None:
    """Excel P1.6 requires a rejection rule; a rejected buffer must say so."""

    for buffer in buffers:
        rule = buffer["rejection_rule"]
        assert rule["id"] == "BUFFER-REJECT-001"
        assert rule["minima_relaxed_to_obtain_pass"] is False
        assert rule["authority"] == "RESEARCHER_ONLY"
        if buffer["readiness"] == "READY":
            assert rule["acceptance"] == "ACCEPTED"
            assert rule["g1_claimable_for_this_fold"] is True
        else:
            assert rule["acceptance"] in {"REJECTED", "INDETERMINATE"}
            assert rule["adaptation_use_permitted"] is False
            assert rule["g1_claimable_for_this_fold"] is False
            assert rule["failing_checks"]


def test_exception_register_covers_declared_exceptions(receipt: dict) -> None:
    """Excel P1.7 step 3: every exception carries a reason and an approver."""

    spec = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/leak-cs-001-exceptions.yaml").read_text(encoding="utf-8")
    )["leak_cs_001_exceptions"]
    assert spec["exceptions"], "the register must not be empty"
    for entry in spec["exceptions"]:
        assert entry["reason"].strip()
        assert "approver" in entry
        assert entry["blocks_g0"] is False, f"{entry['id']} claims to block G0"
    criterion = next(c for c in receipt["criteria"] if c["id"] == "G0-17")
    assert criterion["verdict"] == "PASS"
    assert criterion["evidence"]["blocking_g0"] == []


def test_all_required_signatures_are_enumerated_and_none_outstanding(receipt: dict) -> None:
    """All four Phase 1 signatures are named, and each is verified rather than assumed."""

    signatures = receipt["researcher_signatures"]
    assert set(signatures["verified"]) == {"P1.1", "P1.6", "P1.7", "P1.8/G0"}
    assert signatures["mismatched"] == []
    assert signatures["missing"] == []
    assert receipt["outstanding_researcher_signatures"] == {}
    assert len(signatures["ledger_sha256"]) == 64


def test_buffer_contract_declares_a_rejection_rule() -> None:
    spec = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/target-buffer-v1.yaml").read_text(encoding="utf-8")
    )["target_buffer"]
    rule = spec["rejection_rule"]
    assert rule["authority"] == "RESEARCHER_ONLY"
    assert "relaxing any value in readiness_minima to obtain a pass" in rule["forbidden_remedies"]
    assert "relax_minima" in rule["ai_may_not"]


def test_split_contract_forbids_label_use_and_random_mixing() -> None:
    spec = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/cross-system-split-v1.yaml").read_text(encoding="utf-8")
    )["cross_system_split"]
    assert spec["target_labels_in_split_construction"] is False
    assert spec["mixed_system_random_split_allowed"] is False
    assert spec["fold_strategy"] == "LEAVE_ONE_ARCHITECTURE_OUT"
    assert spec["minimum_source_architectures_per_fold"] == 3


def test_buffer_contract_forbids_label_exposure() -> None:
    spec = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/target-buffer-v1.yaml").read_text(encoding="utf-8")
    )["target_buffer"]
    assert all(value is False for value in spec["label_exposure"].values())
    assert spec["acquisition"]["forbidden_operation"] == "SELECT_RECORDS_WHERE_LABEL_EQUALS_NORMAL"
    assert "ground_truth_anomaly_label" in spec["acquisition"]["forbidden_selection_signals"]


def test_active_state_mirrors_the_receipt_and_cannot_overstate_it(receipt: dict) -> None:
    """The registry is a mirror. It may never assert a gate the receipt does not."""

    state = yaml.safe_load(
        (PROJECT_ROOT / "configs/active-state.yaml").read_text(encoding="utf-8")
    )["active_state"]

    signed = receipt["gate_state"] == "PROTOCOL_READY"
    assert (state["gates"]["G0"] == "PASSED") == signed
    migration = yaml.safe_load(
        (PROJECT_ROOT / "configs/protocols/phase2-roadmap-migration-v1.yaml").read_text()
    )["migration"]
    assert migration["from_sha256"] == receipt["plan_sha256"]
    assert migration["crosswalk"][receipt["next_authorized_task"]] == [state["next_authorized_task"]]
    assert state["scientific_results_status"] == receipt["empirical_status"] == "NOT_RUN"
    assert state["representation_training_status"] == "NOT_STARTED"
    assert state["target_adaptation_status"] == "NOT_STARTED"

    # Historical P2.1 base freeze now routes P2.PRE; later gates stay closed.
    for gate in ("G1", "G2", "G3", "G4"):
        assert state["gates"][gate] == "NOT_PASSED"
    assert state["next_authorized_task_status"] == "AUTHORIZED_NOT_STARTED_METADATA_ONLY"

    # The open exceptions survive the signature.
    assert "EXC-003" in state["open_items_after_g0"]
    assert set(state["researcher_signatures"]["verified"]) == set(
        receipt["researcher_signatures"]["verified"]
    )


def test_no_phase_2_artifact_exists(receipt: dict) -> None:
    """G0 authorises P2.1; it does not start it."""

    for relative in ("outputs/checkpoints", "outputs/runs", "outputs/results"):
        directory = PROJECT_ROOT / relative
        produced = [
            path
            for path in directory.rglob("*")
            if path.is_file() and path.name not in {"README.md", ".gitkeep"}
        ]
        assert produced == [], f"{relative} contains Phase 2 output: {produced}"
    criterion = next(c for c in receipt["criteria"] if c["id"] == "G0-14")
    assert criterion["evidence"]["representation_training_run"] is False
    assert criterion["evidence"]["target_adaptation_run"] is False
