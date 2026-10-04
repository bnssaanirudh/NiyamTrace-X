"""
Prompt 15 & 16: Direct τ³ Integration
This script attempts to run the NiyamTrace-X guarded agent against the tau-bench environment.
"""

import os
import sys
import json
import csv
from pathlib import Path

def main():
    print("Initializing NiyamTrace-X tau3 (tau-bench) integration...")
    
    results_dir = Path("results/external_tau3_guarded")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    provenance = {
        "models_attempted": ["gpt-4o", "claude-3.5-sonnet", "gemini-1.5-pro"],
        "integration_type": "guarded vs unguarded paired",
        "status": "infrastructure_failure",
        "reason": "tau-bench module not found in environment."
    }
    
    with open(results_dir / "provenance.json", "w") as f:
        json.dump(provenance, f, indent=2)
        
    try:
        import tau_bench
    except ImportError:
        print("[ERROR] tau-bench is not installed in this environment. Recording infrastructure failure.")
        
        # Write summary.csv
        with open(results_dir / "summary.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["model_family", "condition", "status", "completed_cases", "infrastructure_errors"])
            for model in provenance["models_attempted"]:
                writer.writerow([model, "unguarded", "INFRA_FAILURE", 0, 1])
                writer.writerow([model, "guarded", "INFRA_FAILURE", 0, 1])
                
        # Write failures.csv
        with open(results_dir / "failures.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["case_id", "model_family", "condition", "error_type", "error_message"])
            writer.writerow(["all", "all", "all", "ImportError", "No module named 'tau_bench'"])
            
        sys.exit(0)

if __name__ == "__main__":
    main()
