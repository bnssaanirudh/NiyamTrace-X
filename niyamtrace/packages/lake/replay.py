import hashlib
from pathlib import Path


class TamperError(Exception):
    """Raised when a trace bundle fails cryptographic validation."""


def verify_trace_bundle(trace_path: Path) -> bool:
    """
    Validates the SHA256 checksum of a JSONL trace bundle.
    Raises TamperError if the signature doesn't match or is missing.
    """
    if not trace_path.exists():
        raise FileNotFoundError(f"Trace file not found: {trace_path}")
        
    sig_path = trace_path.with_suffix(".jsonl.sha256")
    if not sig_path.exists():
        raise TamperError(f"Missing signature file for {trace_path}")
        
    expected_checksum = sig_path.read_text(encoding="utf-8").strip()
    
    with trace_path.open("rb") as f:
        actual_checksum = hashlib.sha256(f.read()).hexdigest()
        
    if actual_checksum != expected_checksum:
        raise TamperError(f"Checksum mismatch for {trace_path}. Trace may have been tampered with.")
        
    return True
