import os
import shutil
import zipfile
from pathlib import Path


def main():
    base_dir = Path("submission_evidence")
    base_dir.mkdir(exist_ok=True)
    
    # Copy files
    shutil.copy("provenance/FINAL_REPRODUCIBILITY_MANIFEST.json", base_dir / "provenance_manifest.json")
    shutil.copy("provenance/CLAIM_EVIDENCE_MATRIX_FINAL.csv", base_dir / "claim_evidence_matrix.csv")
    
    # Copy directories if they exist
    dirs_to_copy = {
        "reports/benchmark_final_v3": "internal_results",
        "results/external_tau3_guarded": "external_tau3",
        "results/external_agentdojo_guarded": "external_agentdojo",
        "results/external_bfcl": "bfcl",
        "results/final_statistics": "statistical_analysis",
    }
    
    for src, dst_name in dirs_to_copy.items():
        src_path = Path(src)
        dst_path = base_dir / dst_name
        if src_path.exists():
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
            
    # Zip it up
    with zipfile.ZipFile("submission_evidence.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(base_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(base_dir)
                zf.write(file_path, arcname)
                
    print("Created submission_evidence.zip")

if __name__ == "__main__":
    main()
