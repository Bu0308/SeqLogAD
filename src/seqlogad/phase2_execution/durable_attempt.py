"""Stream a training attempt durably and expose structured metrics to Projmem."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile


def collect_metrics(persistent_root):
    result = {}
    for target in ("BGL", "HDFS", "HADOOP"):
        archive = Path(persistent_root) / "P2.2/targets" / f"P2.2_{target}_S42.zip"
        if not archive.exists():
            continue
        with zipfile.ZipFile(archive) as handle:
            names = [name for name in handle.namelist() if name.count("/") == 1
                     and name.endswith("/metrics.json")]
            if len(names) != 1:
                raise ValueError("target archive must contain one run metrics file")
            metrics = json.loads(handle.read(names[0]))
        development = metrics.get("source_development_best", {})
        for name, value in development.items():
            if name.startswith("macro_") and isinstance(value, (int, float)):
                result[f"{target}_source_development_{name}"] = value
        for name in ("runtime_seconds", "peak_vram_allocated", "peak_vram_reserved", "step",
                     "source_validation_next_log_nll", "train_next_log_nll"):
            if name in metrics:
                result[f"{target}_{name}"] = metrics[name]
    f1s = [result.get(f"{target}_source_development_macro_f1")
           for target in ("BGL", "HDFS", "HADOOP")]
    if all(value is not None for value in f1s):
        result["source_development_macro_f1"] = sum(f1s) / len(f1s)
    return result


def write_state(path, state):
    temporary = path.with_suffix(".partial")
    with temporary.open("w") as handle:
        json.dump(state, handle, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def execute(command, attempt, persistent_root):
    attempt = Path(attempt)
    attempt.mkdir(parents=True, exist_ok=True)
    state_path = attempt / "training-state.json"
    write_state(state_path, {"status": "RUNNING", "pid": os.getpid()})
    token = os.environ.get("HF_TOKEN")
    with (attempt / "training.log").open("a", buffering=1) as log:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, bufsize=1) as process:
            for line in process.stdout:
                if token:
                    line = line.replace(token, "[TOKEN_HIDDEN]")
                log.write(line)
                log.flush()
                os.fsync(log.fileno())
                print(line, end="", flush=True)
            code = process.wait()
    metrics = collect_metrics(persistent_root)
    write_state(attempt / "metrics.json", metrics)
    write_state(state_path, {"status": "SUCCEEDED" if code == 0 else "FAILED", "exit_code": code})
    return code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--persistent-root", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("training command is required")
    sys.exit(execute(command, args.attempt, args.persistent_root))


if __name__ == "__main__":
    main()
