"""Architecture registry and raw-line adapters for the Excel cross-system protocol.

An *architecture* (Excel P1.1) is a distinct log-producing system or domain, not a
subset of one dataset and not an EventID grouping.  Each adapter is a pure function
from exact raw line bytes to the LOG-UNIFY-001 field set.

Hard rule enforced here: an adapter separates any inline ground-truth marker (BGL's
first column) off the record and never returns it.  Labels reach the pipeline only
through :mod:`seqlogad.protocol.labels`, at the evaluation boundary.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path


class TimestampStatus(StrEnum):
    PARSED = "PARSED"
    CONTINUATION = "CONTINUATION"
    UNPARSEABLE = "UNPARSEABLE"


class ParseStatus(StrEnum):
    OK = "OK"
    CONTINUATION = "CONTINUATION"
    MALFORMED = "MALFORMED"


class TargetEligibility(StrEnum):
    """Whether an architecture may be held out as a LOAO target."""

    ELIGIBLE = "ELIGIBLE"
    SOURCE_ONLY = "SOURCE_ONLY"


class AdapterError(ValueError):
    """Raised when a raw line cannot be represented without losing information."""


@dataclass(frozen=True, slots=True)
class RawRecord:
    """Label-free projection of one raw source line."""

    source_file: str
    source_line_number: int
    timestamp_us: int | None
    timestamp_status: TimestampStatus
    level: str | None
    service: str | None
    component: str | None
    node_id: str | None
    session_id: str | None
    trace_id: str | None
    raw_message_bytes: bytes
    parse_status: ParseStatus


@dataclass(frozen=True)
class ArchitectureSpec:
    """Everything the protocol needs to know about one log-producing system."""

    architecture_id: str
    dataset_id: str
    system_name: str
    domain: str
    raw_root: str
    adapter: str
    evaluation_grouping: str
    target_eligibility: TargetEligibility
    target_eligibility_rationale: str
    label_granularity: str
    label_source: str
    source_reference: str
    citation: str
    license_id: str
    file_glob: tuple[str, ...] = ()
    notes: str = ""
    extra: dict = field(default_factory=dict)


_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _to_us(moment: datetime) -> int:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return int((moment - _EPOCH).total_seconds() * 1_000_000)


def _strip_terminator(raw_line: bytes) -> bytes:
    payload = raw_line
    if payload.endswith(b"\n"):
        payload = payload[:-1]
    if payload.endswith(b"\r"):
        payload = payload[:-1]
    return payload


def _decode(payload: bytes) -> str:
    """Lenient decode used only for *field* parsing; message bytes stay exact."""

    return payload.decode("utf-8", errors="replace")


# --------------------------------------------------------------------------- HDFS

_HDFS_LINE = re.compile(
    r"^(?P<date>\d{6})\s+(?P<time>\d{6})\s+(?P<pid>\d+)\s+(?P<level>[A-Za-z]+)\s+"
    r"(?P<component>\S+):\s(?P<content>.*)$",
    re.DOTALL,
)
_HDFS_BLOCK = re.compile(r"blk_-?\d+")


def parse_hdfs(raw_line: bytes, source_file: str, line_number: int) -> RawRecord:
    payload = _strip_terminator(raw_line)
    text = _decode(payload)
    match = _HDFS_LINE.fullmatch(text)
    if match is None:
        return RawRecord(
            source_file, line_number, None, TimestampStatus.UNPARSEABLE,
            None, None, None, None, None, None, payload, ParseStatus.MALFORMED,
        )
    stamp = datetime.strptime(
        f"{match.group('date')} {match.group('time')}", "%y%m%d %H%M%S"
    )
    component = match.group("component")
    content = match.group("content")
    # Message bytes are taken from the exact raw payload, not from the decoded text,
    # so that a replacement character introduced by field parsing never reaches the
    # canonical message.
    message_bytes = payload[len(payload) - len(content.encode("utf-8", "replace")) :]
    if message_bytes.decode("utf-8", "replace") != content:
        message_bytes = content.encode("utf-8")
    blocks = _HDFS_BLOCK.search(content)
    return RawRecord(
        source_file=source_file,
        source_line_number=line_number,
        timestamp_us=_to_us(stamp),
        timestamp_status=TimestampStatus.PARSED,
        level=match.group("level"),
        service=component.split(".", 1)[0] or None,
        component=component,
        node_id=None,
        session_id=blocks.group(0) if blocks else None,
        trace_id=None,
        raw_message_bytes=message_bytes,
        parse_status=ParseStatus.OK,
    )


# ---------------------------------------------------------------------------- BGL

_BGL_TIMESTAMP = "%Y-%m-%d-%H.%M.%S.%f"
BGL_EMPTY_CONTENT_SENTINEL = "SEQLOGAD_EMPTY_CONTENT"


def parse_bgl(raw_line: bytes, source_file: str, line_number: int) -> RawRecord:
    payload = _strip_terminator(raw_line)
    fields = payload.split(maxsplit=9)
    if len(fields) not in {9, 10}:
        return RawRecord(
            source_file, line_number, None, TimestampStatus.UNPARSEABLE,
            None, None, None, None, None, None, payload, ParseStatus.MALFORMED,
        )
    # fields[0] is the ground-truth alert marker. It is dropped here on purpose and
    # is only ever read by seqlogad.protocol.labels at the evaluation boundary.
    message_bytes = fields[9] if len(fields) == 10 else BGL_EMPTY_CONTENT_SENTINEL.encode()
    try:
        stamp = datetime.strptime(_decode(fields[4]), _BGL_TIMESTAMP)
        timestamp_us: int | None = _to_us(stamp)
        status = TimestampStatus.PARSED
    except ValueError:
        timestamp_us, status = None, TimestampStatus.UNPARSEABLE
    return RawRecord(
        source_file=source_file,
        source_line_number=line_number,
        timestamp_us=timestamp_us,
        timestamp_status=status,
        level=_decode(fields[8]) or None,
        service=_decode(fields[6]) or None,
        component=_decode(fields[7]) or None,
        node_id=_decode(fields[3]) or None,
        session_id=None,
        trace_id=None,
        raw_message_bytes=message_bytes,
        parse_status=ParseStatus.OK,
    )


# ------------------------------------------------------------------------- Hadoop

_HADOOP_LINE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) (?P<level>[A-Z]+) "
    r"(?:\[(?P<thread>[^\]]*)\] )?(?P<component>[^:]+): (?P<content>.*)$",
    re.DOTALL,
)
_HADOOP_TIMESTAMP = "%Y-%m-%d %H:%M:%S,%f"


def parse_hadoop(raw_line: bytes, source_file: str, line_number: int) -> RawRecord:
    payload = _strip_terminator(raw_line)
    text = _decode(payload)
    parts = Path(source_file).parts
    session_id = next((p for p in parts if p.startswith("application_")), None)
    trace_id = Path(source_file).stem or None
    match = _HADOOP_LINE.fullmatch(text)
    if match is None:
        # Stack-trace / wrapped continuation. Kept as its own record so that one raw
        # line always yields exactly one canonical record and nothing is dropped.
        return RawRecord(
            source_file=source_file,
            source_line_number=line_number,
            timestamp_us=None,
            timestamp_status=TimestampStatus.CONTINUATION,
            level=None,
            service=None,
            component=None,
            node_id=None,
            session_id=session_id,
            trace_id=trace_id,
            raw_message_bytes=payload,
            parse_status=ParseStatus.CONTINUATION,
        )
    component = match.group("component").strip()
    service = None
    if component.startswith("org.apache.hadoop."):
        service = component[len("org.apache.hadoop.") :].split(".", 1)[0] or None
    stamp = datetime.strptime(match.group("ts"), _HADOOP_TIMESTAMP)
    content = match.group("content")
    return RawRecord(
        source_file=source_file,
        source_line_number=line_number,
        timestamp_us=_to_us(stamp),
        timestamp_status=TimestampStatus.PARSED,
        level=match.group("level"),
        service=service,
        component=component,
        node_id=match.group("thread"),
        session_id=session_id,
        trace_id=trace_id,
        raw_message_bytes=content.encode("utf-8"),
        parse_status=ParseStatus.OK,
    )


# ---------------------------------------------------------------------- OpenStack

_OPENSTACK_LINE = re.compile(
    r"^(?P<logfile>\S+) (?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) "
    r"(?P<pid>\d+) (?P<level>[A-Z]+) (?P<component>\S+) (?P<content>.*)$",
    re.DOTALL,
)
_OPENSTACK_TIMESTAMP = "%Y-%m-%d %H:%M:%S.%f"
_OPENSTACK_INSTANCE = re.compile(r"\[instance: ([0-9a-fA-F-]{36})\]")
_OPENSTACK_REQUEST = re.compile(r"\breq-([0-9a-fA-F-]{36})\b")


def parse_openstack(raw_line: bytes, source_file: str, line_number: int) -> RawRecord:
    payload = _strip_terminator(raw_line)
    text = _decode(payload)
    match = _OPENSTACK_LINE.fullmatch(text)
    if match is None:
        return RawRecord(
            source_file, line_number, None, TimestampStatus.UNPARSEABLE,
            None, None, None, None, None, None, payload, ParseStatus.MALFORMED,
        )
    stamp = datetime.strptime(match.group("ts"), _OPENSTACK_TIMESTAMP)
    content = match.group("content")
    instance = _OPENSTACK_INSTANCE.search(content)
    request = _OPENSTACK_REQUEST.search(content)
    logfile = match.group("logfile")
    return RawRecord(
        source_file=source_file,
        source_line_number=line_number,
        timestamp_us=_to_us(stamp),
        timestamp_status=TimestampStatus.PARSED,
        level=match.group("level"),
        service=logfile.split(".log", 1)[0] or None,
        component=match.group("component"),
        node_id=None,
        session_id=instance.group(1) if instance else None,
        trace_id=request.group(1) if request else None,
        raw_message_bytes=content.encode("utf-8"),
        parse_status=ParseStatus.OK,
    )


ADAPTERS = {
    "hdfs": parse_hdfs,
    "bgl": parse_bgl,
    "hadoop": parse_hadoop,
    "openstack": parse_openstack,
}


ARCHITECTURES: dict[str, ArchitectureSpec] = {
    "ARCH-HDFS": ArchitectureSpec(
        architecture_id="ARCH-HDFS",
        dataset_id="HDFS_v1",
        system_name="Hadoop Distributed File System (HDFS) v1",
        domain="distributed_storage",
        raw_root="data/raw/hdfs/HDFS_v1",
        adapter="hdfs",
        evaluation_grouping="block_id",
        target_eligibility=TargetEligibility.ELIGIBLE,
        target_eligibility_rationale=(
            "Single append-ordered capture; normal and anomalous block traces are "
            "interleaved throughout the stream, so a label-blind chronological "
            "burn-in/evaluation cut yields an evaluation window that can contain "
            "anomalies."
        ),
        label_granularity="block_trace",
        label_source="preprocessed/anomaly_label.csv",
        source_reference="https://github.com/logpai/loghub/tree/master/HDFS",
        citation="S1",
        license_id="CC-BY-4.0",
        file_glob=("HDFS.log",),
    ),
    "ARCH-BGL": ArchitectureSpec(
        architecture_id="ARCH-BGL",
        dataset_id="BGL",
        system_name="IBM Blue Gene/L supercomputer RAS log",
        domain="hpc_supercomputer",
        raw_root="data/raw/bgl/BGL",
        adapter="bgl",
        evaluation_grouping="record",
        target_eligibility=TargetEligibility.ELIGIBLE,
        target_eligibility_rationale=(
            "Single append-ordered capture with inline per-record alert markers that "
            "are interleaved with non-alert records across the whole time range."
        ),
        label_granularity="log_line",
        label_source="BGL.log:field_0_alert_marker",
        source_reference="https://github.com/logpai/loghub/tree/master/BGL",
        citation="S1",
        license_id="CC-BY-4.0",
        file_glob=("BGL.log",),
    ),
    "ARCH-HADOOP": ArchitectureSpec(
        architecture_id="ARCH-HADOOP",
        dataset_id="Hadoop",
        system_name="Hadoop YARN / MapReduce application and container logs",
        domain="batch_compute_framework",
        raw_root="data/raw/hadoop",
        adapter="hadoop",
        evaluation_grouping="application_id",
        target_eligibility=TargetEligibility.ELIGIBLE,
        target_eligibility_rationale=(
            "Normal and failure-injected applications were run interleaved on the "
            "same cluster, so applications of both classes occur throughout the "
            "wall-clock range and a label-blind chronological cut is informative."
        ),
        label_granularity="application",
        label_source="abnormal_label.txt",
        source_reference="https://github.com/logpai/loghub/tree/master/Hadoop",
        citation="S1",
        license_id="CC-BY-4.0",
        file_glob=("application_*/*.log",),
        notes=(
            "Container logs contain wrapped stack traces; continuation lines are "
            "retained as CONTINUATION records so one raw line always maps to one "
            "canonical record."
        ),
    ),
    "ARCH-OPENSTACK": ArchitectureSpec(
        architecture_id="ARCH-OPENSTACK",
        dataset_id="OpenStack",
        system_name="OpenStack Nova cloud control-plane services",
        domain="cloud_iaas_control_plane",
        raw_root="data/raw/openstack",
        adapter="openstack",
        evaluation_grouping="instance_uuid",
        target_eligibility=TargetEligibility.SOURCE_ONLY,
        target_eligibility_rationale=(
            "The raw data is delivered as three separate capture sessions. The only "
            "label-blind ordering of those sessions is wall-clock, and wall-clock "
            "places the entire anomaly-bearing capture (2017-05-14) strictly before "
            "both normal captures (2017-05-16/17). A label-blind chronological "
            "burn-in then consumes every anomaly and leaves an evaluation window "
            "with no positives. Ordering the sessions any other way would use the "
            "source-provided normal/abnormal file identity, which is ground truth. "
            "The architecture is therefore an ACTIVE source domain and is not a "
            "LOAO target fold."
        ),
        label_granularity="instance_uuid",
        label_source="anomaly_labels.txt",
        source_reference="https://github.com/logpai/loghub/tree/master/OpenStack",
        citation="S1",
        license_id="CC-BY-4.0",
        file_glob=("openstack_normal1.log", "openstack_normal2.log", "openstack_abnormal.log"),
    ),
}


def target_eligible_architectures() -> tuple[str, ...]:
    return tuple(
        key
        for key, spec in ARCHITECTURES.items()
        if spec.target_eligibility is TargetEligibility.ELIGIBLE
    )


def resolve_files(project_root: str | Path, spec: ArchitectureSpec) -> list[Path]:
    """Return the architecture's raw files in a deterministic, declared order."""

    root = Path(project_root).resolve() / spec.raw_root
    files: list[Path] = []
    for pattern in spec.file_glob:
        if any(ch in pattern for ch in "*?["):
            files.extend(sorted(root.glob(pattern)))
        else:
            candidate = root / pattern
            if candidate.is_file():
                files.append(candidate)
    if not files:
        raise AdapterError(f"no raw files resolved for {spec.architecture_id}")
    return files


def iter_raw_records(
    project_root: str | Path, spec: ArchitectureSpec, *, max_records: int | None = None
) -> Iterator[RawRecord]:
    """Stream label-free records in declared file order, then line order."""

    adapter = ADAPTERS[spec.adapter]
    root = Path(project_root).resolve()
    emitted = 0
    for path in resolve_files(root, spec):
        relative = path.relative_to(root).as_posix()
        with path.open("rb") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                yield adapter(raw_line, relative, line_number)
                emitted += 1
                if max_records is not None and emitted >= max_records:
                    return


__all__ = [
    "ADAPTERS",
    "ARCHITECTURES",
    "AdapterError",
    "ArchitectureSpec",
    "ParseStatus",
    "RawRecord",
    "TargetEligibility",
    "TimestampStatus",
    "iter_raw_records",
    "resolve_files",
    "target_eligible_architectures",
]
