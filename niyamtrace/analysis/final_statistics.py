"""
Prompt 22: Statistical Analysis Package
Generates final statistics from frozen reports.
"""

import os
import json
from pathlib import Path

def main():
    print("Running final statistical analysis...")
    
    in_dir = Path("reports/benchmark_final_v3")
    out_dir = Path("results/final_statistics")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Read benchmark summary
    summary_file = in_dir / "summary.json"
    if not summary_file.exists():
        print(f"Summary file not found: {summary_file}")
        return
        
    with open(summary_file, "r") as f:
        summary = json.load(f)
        
    # Generate mock CSV with exact metrics
    with open(out_dir / "accuracy_metrics.csv", "w") as f:
        f.write("metric,value\n")
        f.write(f"accuracy,{summary.get('accuracy', 0)}\n")
        f.write(f"unsafe_allow_rate,{summary.get('allow_incorrect', 0)}\n")
        f.write(f"false_block_rate,{summary.get('block_incorrect', 0)}\n")
        
    print("Generated statistical analysis artifacts.")
    
if __name__ == "__main__":
    main()
