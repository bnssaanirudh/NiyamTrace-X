"""
audit_notebook_16.py - Programmatic execution and verification of Notebook 16 rules.
Verifies native security regressions, checks PRODUCTION_FIX_EVIDENCE.json,
and generates 16_PRODUCTION_SECURITY_GATE.json.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_audit():
    root = Path(__file__).resolve().parent.parent.parent
    kit_dir = root / "NiyamTraceX_Paper_Final_Validation_Kit"
    out_dir = kit_dir / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = root / "niyamtrace" / "artifacts" / "PRODUCTION_FIX_EVIDENCE.json"

    # 1. Get current commit
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root), capture_output=True, text=True, check=True)
    current_commit = res.stdout.strip()
    known_vulnerable = "651e87ef452c80008d4f73c8f2de21321e21fa50"

    print(f"Current commit: {current_commit}")
    print(f"Known vulnerable commit: {known_vulnerable}")

    record = {
        "run_attempted": True,
        "source_commit": current_commit,
        "mandatory_native_probe_status": "NOT_RUN",
        "tests": [],
        "status": "PENDING",
        "issues": []
    }

    if current_commit == known_vulnerable:
        record["issues"].append("Unpatched vulnerable commit; do not claim closure. Patch in Antigravity and push branch first.")

    # 2. Check and run tests
    tests = [
        "tests/security/test_native_mediation_regressions.py",
        "tests/security/test_e2e_broker.py",
        "tests/integration/test_simulate_execute_atomicity.py"
    ]
    package_dir = root / "niyamtrace"

    for test in tests:
        test_path = package_dir / test
        if not test_path.is_file():
            record["tests"].append({"path": test, "status": "MISSING", "returncode": None})
            continue

        env = os.environ.copy()
        env["PYTHONPATH"] = str(package_dir) + os.pathsep + env.get("PYTHONPATH", "")
        p = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", test],
            cwd=str(package_dir),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        logname = test.replace("/", "_")
        log_file = out_dir / f"16_{logname}.log"
        log_file.write_text(p.stdout + "\nSTDERR:\n" + p.stderr, encoding="utf-8")
        status = "PASS" if p.returncode == 0 else "FAIL"
        record["tests"].append({
            "path": test,
            "status": status,
            "returncode": p.returncode,
            "log_sha256": sha(log_file)
        })
        print(f"Test {test}: {status}")

    # 3. Verify evidence file
    required = {
        "SEC-01_DIRECT_EXECUTOR_MEDIATION", "SEC-02_CERTIFICATE_ORIGIN_BINDING", "SEC-03_MISSING_YEAR",
        "SEC-04_PAIRED_BROKER_POSITIVE", "SEC-REPLAY", "SEC-STALE_STATE", "SEC-WRONG_TENANT", "SEC-POLICY_REVOKE"
    }

    if not evidence_path.is_file():
        record["issues"].append("No PRODUCTION_FIX_EVIDENCE.json from source-native test runner")
    else:
        j = json.loads(evidence_path.read_text(encoding="utf-8"))
        # If repo_commit is different, check if it matches current_commit
        if j.get("repo_commit") != current_commit:
            record["issues"].append(f"Repo HEAD ({current_commit}) / evidence revision ({j.get('repo_commit')}) mismatch")
        got = {x.get("id"): x for x in j.get("probes", []) if isinstance(x, dict)}
        for key in sorted(required):
            v = got.get(key)
            if v is None:
                record["issues"].append("Missing " + key)
                continue
            if v.get("status") != "PASS" or v.get("actual_native_executor") is not True:
                record["issues"].append("Not verified " + key)
            for d in ("trace_sha256", "before_db_sha256", "after_db_sha256"):
                if not isinstance(v.get(d), str) or len(v[d]) != 64:
                    record["issues"].append(key + " missing " + d)
            if key in {"SEC-01_DIRECT_EXECUTOR_MEDIATION", "SEC-02_CERTIFICATE_ORIGIN_BINDING", "SEC-03_MISSING_YEAR"} and v.get("rows_mutated") != 0:
                record["issues"].append(key + " still mutated rows")
            if key == "SEC-04_PAIRED_BROKER_POSITIVE" and not (isinstance(v.get("rows_mutated"), int) and v["rows_mutated"] > 0):
                record["issues"].append("Positive authorized commit did not succeed")

    if record["tests"] and any(x["status"] != "PASS" for x in record["tests"]):
        record["issues"].append("Regression tests missing/failed")

    if not record["issues"]:
        record["mandatory_native_probe_status"] = "CANDIDATE_PASS_REQUIRES_INDEPENDENT_REVIEW"
        record["status"] = "CANDIDATE_REVIEW"
    else:
        record["mandatory_native_probe_status"] = "BLOCKED"
        record["status"] = "PENDING_OR_FAIL"

    gate_out = out_dir / "16_PRODUCTION_SECURITY_GATE.json"
    gate_out.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"\nWritten {gate_out}:\nStatus: {record['status']}, Mandatory probe status: {record['mandatory_native_probe_status']}")
    if record["issues"]:
        print(f"Issues: {record['issues']}")
    return record

if __name__ == "__main__":
    run_audit()
