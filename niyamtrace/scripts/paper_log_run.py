"""Run a real command, capture its console log, and hash its output artifacts."""

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def current_commit() -> str | None:
    try:
        process = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return process.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--kind",
        choices=["test", "smoke", "benchmark", "inference", "replay", "training"],
        required=True,
    )
    parser.add_argument("--source-run")
    parser.add_argument("--output-dir", type=Path, default=Path("paper_runs"))
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Pass an executable after --")
    if args.kind == "replay" and not args.source_run:
        parser.error("--kind replay requires --source-run")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id += "-" + uuid.uuid4().hex[:10]
    folder = args.output_dir / run_id
    folder.mkdir(parents=True, exist_ok=False)
    started_at, started_clock = utc_now(), time.monotonic()
    status, exit_code, error_message = "START_ERROR", 127, None
    with (folder / "run.log").open("w", encoding="utf-8", errors="replace") as log:
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                bufsize=1,
            )
            if process.stdout is not None:
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    sys.stdout.write(line)
            exit_code = process.wait()
            status = "PROCESS_EXIT_ZERO" if exit_code == 0 else "PROCESS_NONZERO"
        except (OSError, ValueError) as error:
            error_message = str(error)
            log.write(error_message + "\n")

    artifacts = []
    for item in args.artifact:
        path = Path(item)
        if path.is_file():
            artifacts.append(
                {
                    "path": str(path.resolve()),
                    "status": "PRESENT",
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )
        else:
            artifacts.append({"path": item, "status": "MISSING", "sha256": "", "bytes": ""})
    with (folder / "artifacts_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "status", "sha256", "bytes"])
        writer.writeheader()
        writer.writerows(artifacts)

    record = {
        "run_id": run_id,
        "name": args.name,
        "kind": args.kind,
        "source_run_id": args.source_run,
        "started_utc": started_at,
        "ended_utc": utc_now(),
        "duration_seconds": round(time.monotonic() - started_clock, 3),
        "git_commit": current_commit(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "command": command,
        "exit_code": exit_code,
        "process_status": status,
        "error": error_message,
        "note": "Exit code does not establish research validity. Check logs for secrets.",
    }
    (folder / "metadata.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Run evidence written to {folder} (exit={exit_code})")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
