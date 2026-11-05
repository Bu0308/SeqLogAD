"""Build a Colab operator package around the frozen Sequence V13R1 trainer."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
READY_DIR = ROOT / "outputs/runpod/P2.2-S42-A40-V13R1-READY"
READY_ZIP = ROOT / "outputs/runpod/P2.2-S42-A40-V13R1-READY.zip"
DELIVERY = ROOT / "outputs/colab/P2.2-S42-A40-V13R1-COLAB-READY"
NOTEBOOK = "P2.2_run_all_sequence_lora_s42_v13r1_colab.ipynb"
COLLECTOR = "collect_v13r1_colab.py"
ARCHIVE_HELPER = "collection_archive_v13r1.py"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def src(cell: dict) -> str:
    return "".join(cell["source"])


def put(cell: dict, value: str) -> None:
    cell["source"] = value.splitlines(keepends=True)


def build_collector() -> Path:
    text = (READY_DIR / "collect_v13r1.py").read_text(encoding="utf-8")
    text = text.replace("TRAIN_NAME = 'P2.2 Sequence V13R1 RunPod attempt'",
                        "TRAIN_NAME = 'P2.2 Sequence V13R1 Colab attempt'")
    text = text.replace("'recorded_before_training': True, 'attempt_id': attempt}",
                        "'recorded_before_training': True, 'attempt_id': attempt,\n"
                        "        'execution_platform': 'Google Colab'}")
    path = DELIVERY / COLLECTOR
    path.write_text(text, encoding="utf-8")
    return path


def config_cell() -> str:
    return '''# HUMAN CONFIG — upload the V13R1 READY ZIP to Drive and configure HF_TOKEN Secret.
+from pathlib import Path
+from google.colab import drive
+import os, uuid
+
+TASK_ID = "P2.2"
+NOTEBOOK_STATUS = "READY"
+BLOCKERS = []
+RUN_MODE = "development"
+SEED = 42
+TARGETS = ["BGL", "HDFS", "HADOOP"]
+READY_ZIP_NAME = "P2.2-S42-A40-V13R1-READY.zip"
+NOTEBOOK_NAME = "P2.2_run_all_sequence_lora_s42_v13r1_colab.ipynb"
+DRIVE_ROOT = Path("/content/drive/MyDrive/SeqLogAD_V13R1_COLAB")
+READY_ARCHIVE = DRIVE_ROOT / "input" / READY_ZIP_NAME
+NOTEBOOK_PATH = DRIVE_ROOT / NOTEBOOK_NAME
+WORK_ROOT = Path("/content/seqlogad_v13r1_colab") / uuid.uuid4().hex
+UPLOAD_ROOT = WORK_ROOT / "uploads"
+STATE_ROOT = Path("/content/SeqLogAD")
+PERSISTENT_ROOT = DRIVE_ROOT / "sequence-v13r1"
+HF_HOME = WORK_ROOT / "hf-cache"
+VENV = WORK_ROOT / "venv-py312"
+RUNTIME_ROOT = WORK_ROOT / "runtime" / "ad0f313b1b2e-4ed76b92e4b0-c765eb88a4fe"
+REPO_ROOT = str(RUNTIME_ROOT / "seqlogad_code_all_experts_s42")
+DATA_ROOT = str(RUNTIME_ROOT / "phase2_sequence")
+SOURCE_DEVELOPMENT_ROOT = str(RUNTIME_ROOT / "phase2_source_development_v13r1")
+EXPECTED_READY_ZIP_SHA256 = "a17a0949bd7743a263267460d35ff9182fccc9b601420f6edb923b465076c14c"
+EXPECTED_SOURCE_DEVELOPMENT_ZIP_SHA256 = "c765eb88a4feebc8ceb157110e5a6bd28dec942a7fb9343d7f6b969b3e79b295"
+EXPECTED_SOURCE_DEVELOPMENT_MANIFEST_SHA256 = "885b53821671e7f60e6df5270a78a23535900bf4ba6d339e69b29f93eb2c6399"
+EXPECTED_CODE_ZIP_SHA256 = "ad0f313b1b2e482f75eb2f5d10800fe59c451a2d1adc0c9e85aa0f1b0d01efb3"
+EXPECTED_DATA_ZIP_SHA256 = "4ed76b92e4b001138b28b4b3d3017d6ff7f30dd31e8cca0649bfdf34ede781"
+EXPECTED_PMEM_WHEEL_SHA256 = "637964eed3af38c6170c5571bbc02338268cf31bddb15eaf3cc6d883c6b3ce4f"
+EXPECTED_BUNDLE_SHA256 = "1268b669a8b1b474658cfa7daa6556c987b0f31f07e0101ed30af250a8d7f129"
+EXPECTED_COLLECTOR_SHA256 = "__COLLECTOR_SHA__"
+MIN_VRAM_GIB = 40
+SUPPORTED_GPU_FAMILIES = ("NVIDIA A100", "NVIDIA H100")
+COLLECTOR = "collect_v13r1_colab.py"
+SESSION_ROOT = WORK_ROOT / "attempts" / uuid.uuid4().hex
+OUTPUT_ROOT = str(WORK_ROOT / "seqlogad_outputs")
+EXPORT_ROOT = DRIVE_ROOT / "exports"
+
+assert RUN_MODE == "development" and SEED == 42
+assert TARGETS == ["BGL", "HDFS", "HADOOP"]
+assert NOTEBOOK_STATUS == "READY", "Notebook is fail-closed: " + ", ".join(BLOCKERS)
+drive.mount("/content/drive")
+assert READY_ARCHIVE.is_file(), f"Upload {READY_ZIP_NAME} to MyDrive/SeqLogAD_V13R1_COLAB/input"
+assert NOTEBOOK_PATH.is_file(), f"Upload {NOTEBOOK_NAME} to MyDrive/SeqLogAD_V13R1_COLAB"
+for directory in (WORK_ROOT, STATE_ROOT, PERSISTENT_ROOT, HF_HOME, SESSION_ROOT, EXPORT_ROOT):
+    directory.mkdir(parents=True, exist_ok=True)
+os.environ["HF_HOME"] = str(HF_HOME)
+print({"ready_zip": str(READY_ARCHIVE), "persistent_drive_root": str(PERSISTENT_ROOT),
+       "ephemeral_work_root": str(WORK_ROOT)})
+
+# Journal is written to Drive before setup and before Projmem is installed.
+import json, datetime, traceback
+ATTEMPT_ROOT = PERSISTENT_ROOT / "attempts" / SESSION_ROOT.name
+ATTEMPT_ROOT.mkdir(parents=True, exist_ok=False)
+JOURNAL_PATH = ATTEMPT_ROOT / "lifecycle.jsonl"
+
+def journal(event, detail=""):
+    token = os.environ.get("HF_TOKEN")
+    if token:
+        detail = detail.replace(token, "[TOKEN_HIDDEN]")
+    with JOURNAL_PATH.open("a") as handle:
+        handle.write(json.dumps({"event": event, "detail": detail,
+            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}) + "\\n")
+        handle.flush()
+        os.fsync(handle.fileno())
+
+journal("STARTED")
+'''.replace("\n+", "\n")


def modify_setup(text: str, collector_hash: str, collector_source: str) -> str:
    needle = "    code_zip = locate(EXPECTED_CODE_ZIP_SHA256)"
    assert text.count(needle) == 1
    text = text.replace(needle, '''    assert digest(READY_ARCHIVE) == EXPECTED_READY_ZIP_SHA256, "READY package checksum mismatch"
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=False)
    safe_extract(READY_ARCHIVE, UPLOAD_ROOT)
    assert (UPLOAD_ROOT / "RUNPOD_UPLOAD_MANIFEST.json").is_file(), "READY package layout mismatch"
    import base64
    colab_collector = UPLOAD_ROOT / COLLECTOR
    colab_collector.write_bytes(base64.b64decode("COLLECTOR_B64"))
    assert digest(colab_collector) == EXPECTED_COLLECTOR_SHA256, "Colab collector source hash mismatch"
    code_zip = locate(EXPECTED_CODE_ZIP_SHA256)'''.replace("\n+", "\n"))
    old = '''    assert {REQUIRED_GPU!r} in name, f"Expected {REQUIRED_GPU}, got {{name}}"
    assert total >= {MIN_VRAM_GIB} * 1024**3, f"Expected at least {MIN_VRAM_GIB} GiB VRAM"
    assert native_bf16, "Native BF16 is required"'''.replace("\n+", "\n")
    new = '''    assert any(family in name for family in {SUPPORTED_GPU_FAMILIES!r}), (
        f"Colab requires A100/H100, found {{name}}"
    )
    assert total >= {MIN_VRAM_GIB} * 1024**3, f"Expected at least {MIN_VRAM_GIB} GiB VRAM"
    assert native_bf16, "Native BF16 is required"'''.replace("\n+", "\n")
    assert text.count(old) == 1
    text = text.replace(old, new)
    text = text.replace('UPLOAD_ROOT / "collect_v13r1.py"', 'UPLOAD_ROOT / COLLECTOR')
    text = text.replace("'a708df30484dcbdc0f23594cb1292681bcd1200a1a2d67d721b40ab086a66db5'", f"'{collector_hash}'")
    text = text.replace('"--exports", "/workspace/exports"', '"--exports", str(EXPORT_ROOT)')
    hardware_call = 'run_live([PYTHON, "-c", hardware_check])'
    assert text.count(hardware_call) == 1
    text = text.replace(hardware_call,
                        'import textwrap\n    run_live([PYTHON, "-c", textwrap.dedent(hardware_check)])')
    init_marker = '    journal("PROJMEM_INITIALIZED")'
    assert text.count(init_marker) == 1
    text = text.replace(init_marker, '    journal("PROJMEM_INITIALIZED")\n    provenance_dir = PERSISTENT_ROOT / "handoff_inputs"\n    provenance_dir.mkdir(parents=True, exist_ok=True)\n    for source_path in (UPLOAD_ROOT / COLLECTOR, NOTEBOOK_PATH):\n        target_path = provenance_dir / source_path.name\n        shutil.copy2(source_path, target_path)\n        run_live([pmem_cli, "track", str(target_path.relative_to(PERSISTENT_ROOT)), "--update"],\n                 cwd=str(PERSISTENT_ROOT))\n    run_live([pmem_cli, "note", "Colab operator sources captured before training: " + SESSION_ROOT.name,\n              "--tag", "method", "--tag", "V13R1"], cwd=str(PERSISTENT_ROOT))')
    return text


def replace_auth(text: str) -> str:
    old = '''    token = os.environ.get("HF_TOKEN")
    assert token, "Set HF_TOKEN as a RunPod environment secret; never paste it into the notebook"'''
    new = '''    from google.colab import userdata
    token = userdata.get("HF_TOKEN")
    assert token, "Add HF_TOKEN in Colab Secrets and grant this notebook access"
    os.environ["HF_TOKEN"] = token'''
    assert text.count(old) == 1
    return text.replace(old, new)


def replace_finalize(text: str) -> str:
    old = '''    run_live([PYTHON, str(COLLECT_HELPER), "finalize", "--root", str(PERSISTENT_ROOT),
              "--exports", "/workspace/exports"], cwd=str(PERSISTENT_ROOT))'''.replace("\n+", "\n")
    new = '''    before = set(EXPORT_ROOT.glob("SeqLogAD_sequence-v13r1_FULL_*.tar.gz"))
    finalize_exit, finalize_output = run_live(
        [PYTHON, str(COLLECT_HELPER), "finalize", "--root", str(PERSISTENT_ROOT),
         "--exports", str(EXPORT_ROOT)],
        cwd=str(PERSISTENT_ROOT), check=False, capture=True,
    )
    assert finalize_exit == 0 and "COLLECT_READY=YES" in finalize_output, (
        "Evidence finalize failed; preserve the Drive folder and inspect logs"
    )
    after = set(EXPORT_ROOT.glob("SeqLogAD_sequence-v13r1_FULL_*.tar.gz"))
    created = sorted(after - before)
    assert len(created) == 1, f"Expected one new FULL archive, got {{created}}"
    final_archive = created[0]
    checksum = Path(str(final_archive) + ".sha256")
    assert checksum.is_file()
    expected_hash, expected_name = checksum.read_text().strip().split("  ", 1)
    assert expected_name == final_archive.name and digest(final_archive) == expected_hash
    print("FULL_ARCHIVE_SAVED_TO_DRIVE=" + str(final_archive))
    print("FULL_ARCHIVE_SHA256=" + expected_hash)
    print("COLLECT_READY=YES")
    print("DOWNLOAD_REQUESTED=YES")
    from google.colab import files
    files.download(str(final_archive))
    files.download(str(checksum))'''.replace("\n+", "\n")
    assert text.count(old) == 1
    text = text.replace(old, new)
    text = text.replace('print("DOWNLOAD_FULL_ARCHIVE_FROM=/workspace/exports")\nprint("COLLECT_READY=YES")', '')
    return text


def make_notebook(collector_hash: str, collector_source: str) -> Path:
    nb = json.loads((READY_DIR / "P2.2_run_all_sequence_lora_s42_v13r1_collect.ipynb").read_text())
    put(nb["cells"][0], '''# V13R1 — Google Colab TRAIN + COLLECT (seed 42)

Open from Google Drive, select an A100/H100 GPU runtime, and run all cells once.
The V13R1 trainer, data, seed, metrics and early stopping are unchanged. Colab
needs at least 40 GiB VRAM and native BF16. Training state and FULL evidence are
saved to Google Drive; the final cell also starts browser downloads for the FULL archive and its checksum.

The Colab runtime cannot close its own browser tab. The browser-controlling AI
should verify the FULL archive download finished, then close this Colab tab.
''')
    config = config_cell().replace("__COLLECTOR_SHA__", collector_hash)
    put(nb["cells"][1], config)
    import base64
    setup = modify_setup(src(nb["cells"][5]), collector_hash, collector_source)
    setup = setup.replace("COLLECTOR_B64", base64.b64encode(collector_source.encode()).decode())
    put(nb["cells"][5], setup)
    put(nb["cells"][6], '''## Hugging Face authentication

Add a Colab Secret named `HF_TOKEN` and grant this notebook access. The account
must be approved for gated `meta-llama/Llama-3.1-8B`. The token is never placed
in notebook source or the collected archive.
''')
    put(nb["cells"][7], replace_auth(src(nb["cells"][7])))
    cell8 = src(nb["cells"][8]).replace('UPLOAD_ROOT / "collect_v13r1.py"', 'UPLOAD_ROOT / COLLECTOR')
    cell8 = cell8.replace("a708df30484dcbdc0f23594cb1292681bcd1200a1a2d67d721b40ab086a66db5", collector_hash)
    put(nb["cells"][8], cell8)
    train = src(nb["cells"][10]).replace('"P2.2 Sequence V13R1 RunPod attempt"',
                                           '"P2.2 Sequence V13R1 Colab attempt"')
    put(nb["cells"][10], train)
    final_cell = replace_finalize(src(nb["cells"][14])).replace(
        "a708df30484dcbdc0f23594cb1292681bcd1200a1a2d67d721b40ab086a66db5",
        collector_hash,
    )
    put(nb["cells"][14], final_cell)
    path = DELIVERY / NOTEBOOK
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def guide_text() -> str:
    return f'''# Google Colab V13R1 — hướng dẫn Windows và macOS

## Phạm vi

Notebook này dùng nguyên trainer, seed 42, dữ liệu, adapter, source-development labels và metric contract của V13R1-READY. Wrapper riêng ghi persistence/Projmem vào Google Drive và hỗ trợ Colab A100/H100 có ít nhất 40 GiB VRAM cùng BF16 native. Không tự hạ cấu hình nếu Colab cấp T4/L4 hoặc GPU yếu hơn. Target metrics vẫn NOT_EVALUATED.

Colab chạy Linux ở cloud. Máy Windows/macOS chỉ cần trình duyệt; không cần cài CUDA, Python hay thư viện train.

## Chuẩn bị một lần

1. Trên Chrome/Edge ở Windows hoặc macOS, tạo Google Drive folder `My Drive/SeqLogAD_V13R1_COLAB/input`.
2. Giải nén `P2.2-S42-A40-V13R1-COLAB-READY.zip`. Upload notebook `{NOTEBOOK}` vào `SeqLogAD_V13R1_COLAB/`; upload `P2.2-S42-A40-V13R1-READY.zip` vào `SeqLogAD_V13R1_COLAB/input/`.
3. Đối chiếu SHA-256 của READY ZIP: `{sha(READY_ZIP)}`. Notebook sẽ xác minh ZIP cùng từng payload trước khi train.
4. Tạo Colab Secret `HF_TOKEN`, bật quyền cho notebook; HF account cần quyền gated model. Không dán token vào cell.
5. Chọn GPU A100/H100, tối thiểu 40 GiB và BF16 native. Colab không bảo đảm cung cấp GPU này. Cần đủ quota/compute và dung lượng Drive; checkpoint recovery ghi Drive trong lúc train.

## Chạy và lấy archive

1. Drive: mở notebook bằng **Open with → Google Colaboratory**.
2. Chọn **Runtime → Change runtime type → GPU** (A100/H100 nếu có).
3. Bấm **Runtime → Run all**. Lần đầu cấp quyền Drive mount và quyền notebook đọc `HF_TOKEN` Secret.
4. Giữ tab mở đến khi cell cuối báo `COLLECT_READY=YES`, đường dẫn `FULL_ARCHIVE_SAVED_TO_DRIVE`, checksum và `DOWNLOAD_REQUESTED=YES`. Notebook lưu FULL archive và `.sha256` vào Drive trước rồi mới yêu cầu browser tải cả hai file về máy.
5. AI điều khiển browser cần chờ cả hai file ở Downloads hiển thị hoàn tất, kiểm tra tên và kích thước, rồi mới đóng tab Colab. Nếu Chrome/Edge hỏi quyền tải nhiều file từ Colab, cho phép hai file archive/checksum theo tác vụ này. Notebook không thể tự đóng tab vì giới hạn bảo mật của browser. Không tắt runtime trước khi archive đã lưu và download hoàn tất.
6. Giữ cả `.tar.gz` và `.sha256`. Nếu browser chặn download thì file vẫn còn trong Drive; tải lại từ `exports/`.

## Runbook ngắn cho AI browser operator

Dùng local files `{NOTEBOOK}` và `P2.2-S42-A40-V13R1-READY.zip`. Upload chúng tới hai vị trí trên trong Google Drive, mở notebook với Colab, chọn GPU được hỗ trợ, chạy Run all, theo dõi đến final marker, đợi download hoàn thành rồi đóng riêng tab Colab. Không mở nhãn target, không sửa notebook/config, không chạy nhiều session song song. Nếu cần login/2FA/CAPTCHA, quyền Drive/HF, mua compute hoặc giải quyết quota, dừng ở màn hình đó để người dùng xử lý.

## Đường dẫn dữ liệu

- Persistent Projmem: `My Drive/SeqLogAD_V13R1_COLAB/sequence-v13r1/.pmem/pmem.db`
- Logs, attempts, checkpoints/recovery và fold ZIPs: `.../sequence-v13r1/`
- FULL archive + checksum: `My Drive/SeqLogAD_V13R1_COLAB/exports/`
- Local download sau khi hoàn tất: thư mục Downloads của Windows/macOS (theo cấu hình browser).

Không xóa hoặc ghi đè DB/attempt cũ. Gói FULL chứa dữ liệu nguồn restricted; không đưa lên repo public. DB Colab là bản riêng, cần audit trước khi merge vào collection Mac.

## Nếu bị ngắt

Giữ thư mục Drive nguyên vẹn. Sau khi chắc không có training process còn chạy, mở lại cùng notebook/Drive root; runner kiểm tra trạng thái và checkpoint recovery đã lưu. Không chạy Pod/Colab khác cùng lúc. Nếu không xuất hiện `COLLECT_READY=YES`, chưa coi là hoàn tất; giữ `.pmem`, attempt logs và archive lỗi để audit.
'''


def package(notebook: Path, guide: Path, collector: Path) -> tuple[Path, Path]:
    helper = READY_DIR / ARCHIVE_HELPER
    manifest_path = DELIVERY / "COLAB_UPLOAD_MANIFEST.json"
    files = {notebook.name: notebook, guide.name: guide, COLLECTOR: collector,
             ARCHIVE_HELPER: helper, READY_ZIP.name: READY_ZIP,
             READY_ZIP.name + ".sha256": Path(str(READY_ZIP) + ".sha256")}
    manifest = {
        "schema": "SEQLOGAD-COLAB-OPERATOR-KIT-1",
        "variant": "LORA-SEQ-003-R1-v1.3.1", "seed": 42,
        "notebook": NOTEBOOK, "input_ready_zip": READY_ZIP.name,
        "input_ready_zip_sha256": sha(READY_ZIP),
        "runtime": "Google Colab Linux; local browser supported on Windows/macOS",
        "gpu_requirement": "NVIDIA A100/H100, >=40 GiB VRAM, native BF16",
        "persistent_storage": "Google Drive MyDrive/SeqLogAD_V13R1_COLAB",
        "trainer_payload_unchanged": True, "target_metrics": "NOT_EVALUATED",
        "files": {name: {"sha256": sha(path), "size": path.stat().st_size}
                  for name, path in files.items()}}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    files[manifest_path.name] = manifest_path
    archive = ROOT / "outputs/colab/P2.2-S42-A40-V13R1-COLAB-READY.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name, path in files.items():
            zf.write(path, name)
    checksum = Path(str(archive) + ".sha256")
    checksum.write_text(f"{sha(archive)}  {archive.name}\n")
    return archive, checksum


def main() -> None:
    if not READY_ZIP.is_file():
        raise FileNotFoundError(READY_ZIP)
    DELIVERY.mkdir(parents=True, exist_ok=True)
    collector = build_collector()
    notebook = make_notebook(sha(collector), collector.read_text(encoding="utf-8"))
    guide = DELIVERY / "HUONG_DAN_COLAB_V13R1_VI.md"
    guide.write_text(guide_text(), encoding="utf-8")
    archive, _ = package(notebook, guide, collector)
    print(json.dumps({"delivery": str(DELIVERY), "package": str(archive),
                      "package_sha256": sha(archive), "package_size": archive.stat().st_size,
                      "notebook": str(notebook), "guide": str(guide),
                      "manifest": str(DELIVERY / "COLAB_UPLOAD_MANIFEST.json"),
                      "collector_sha256": sha(collector), "input_ready_zip_sha256": sha(READY_ZIP)},
                     indent=2))


if __name__ == "__main__":
    main()
