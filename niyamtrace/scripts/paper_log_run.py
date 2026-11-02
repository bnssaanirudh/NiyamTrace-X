#!/usr/bin/env python3
"""Capture a real experiment/test invocation with UTC metadata and artifact hashes."""
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

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def utc():
    return datetime.now(timezone.utc).isoformat()

def git_sha():
    try:
        p = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, timeout=10, check=True)
        return p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--kind", choices=["test", "smoke", "benchmark", "inference",
                                       "replay", "training"], required=True)
    ap.add_argument("--source-run")
    ap.add_argument("--output-dir", type=Path, default=Path("paper_runs"))
    ap.add_argument("--artifact", action="append", default=[])
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    cmd = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not cmd:
        ap.error("Pass an executable after --")
    if args.kind == "replay" and not args.source_run:
        ap.error("--kind replay requires --source-run")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    folder = args.output_dir / run_id
    folder.mkdir(parents=True, exist_ok=False)
    started, start_clock = utc(), time.monotonic()
    status, code = "ERROR", 127
    error = None
    with (folder / "run.log").open("w", encoding="utf-8", errors="replace") as log:
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, errors="replace", bufsize=1)
            for line in proc.stdout:
                log.write(line)
                log.flush()
                sys.stdout.write(line)
            code = proc.wait()
            status = "PROCESS_EXIT_ZERO" if code == 0 else "PROCESS_NONZERO"
        except (OSError, ValueError) as exc:
            error = str(exc)
            log.write(error + "\n")
    rows = []
    for filename in args.artifact:
        path = Path(filename)
        if path.is_file():
            rows.append({"path": str(path.resolve()), "status": "PRESENT",
                         "sha256": sha256(path), "bytes": path.stat().st_size})
        else:
            rows.append({"path": filename, "status": "MISSING", "sha256": "", "bytes": ""})
    with (folder / "artifacts_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "status", "sha256", "bytes"])
        writer.writeheader()
        writer.writerows(rows)
    metadata = {"run_id": run_id, "name": args.name, "kind": args.kind,
                "source_run_id": args.source_run, "started_utc": started,
                "ended_utc": utc(), "duration_seconds": round(time.monotonic() - start_clock, 3),
                "git_commit": git_sha(), "python_version": sys.version,
                "platform": platform.platform(), "command": cmd, "exit_code": code,
                "process_status": status, "error": error,
                "note": "Process exit code is not a benchmark validity verdict. Review logs for secrets."}
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Run evidence written to {folder} (exit={code})")
    return code

if __name__ == "__main__":
    raise SystemExit(main())
