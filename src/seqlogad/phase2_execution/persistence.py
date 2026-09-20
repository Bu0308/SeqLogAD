"""Bounded atomic Google Drive persistence with end-to-end digest checks."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from seqlogad.common.checksum import sha256_file

from .archive import verify_zip


def _write_sidecar_atomic(path, digest):
    sidecar = Path(str(path) + ".sha256")
    temporary = Path(str(sidecar) + ".partial")
    temporary.write_text(f"{digest}  {Path(path).name}\n")
    os.replace(temporary, sidecar)


def verify_persisted_zip(path):
    path = Path(path)
    result = verify_zip(path)
    sidecar = Path(str(path) + ".sha256")
    if not sidecar.is_file():
        raise ValueError("persistent ZIP checksum sidecar missing")
    digest, name = sidecar.read_text().strip().split("  ", 1)
    if name != path.name or digest != result["sha256"]:
        raise ValueError("persistent ZIP checksum sidecar mismatch")
    return result


def publish_atomic(local_zip, destination):
    local_zip, destination = Path(local_zip), Path(destination)
    source = verify_zip(local_zip)
    destination.parent.mkdir(parents=True, exist_ok=True)
    incoming = Path(str(destination) + ".incoming")
    previous = Path(str(destination) + ".previous")
    for path in (incoming, Path(str(incoming) + ".sha256")):
        if path.exists():
            path.unlink()
    shutil.copy2(local_zip, incoming)
    if sha256_file(incoming) != source["sha256"]:
        incoming.unlink(missing_ok=True)
        raise ValueError("Drive copy SHA-256 mismatch before replacement")
    _write_sidecar_atomic(incoming, source["sha256"])
    verify_persisted_zip(incoming)
    if destination.exists():
        previous.unlink(missing_ok=True)
        os.replace(destination, previous)
        old_sidecar = Path(str(destination) + ".sha256")
        if old_sidecar.exists():
            os.replace(old_sidecar, Path(str(previous) + ".sha256"))
    try:
        os.replace(incoming, destination)
        Path(str(incoming) + ".sha256").unlink(missing_ok=True)
        _write_sidecar_atomic(destination, source["sha256"])
        final = verify_persisted_zip(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        Path(str(destination) + ".sha256").unlink(missing_ok=True)
        if previous.exists():
            os.replace(previous, destination)
            previous_sidecar = Path(str(previous) + ".sha256")
            if previous_sidecar.exists():
                os.replace(previous_sidecar, Path(str(destination) + ".sha256"))
        raise
    previous.unlink(missing_ok=True)
    Path(str(previous) + ".sha256").unlink(missing_ok=True)
    return final
