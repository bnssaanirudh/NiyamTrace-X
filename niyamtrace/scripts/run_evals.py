import asyncio
import json
import uuid
from pathlib import Path

from apps.gateway.main import InvokeRequest
from apps.gateway.pipeline import NiyamPipeline
from packages.config import get_settings
from packages.storage.session import SessionManager


def load_cases(data_path: Path) -> list[dict]:
    cases = []
    with data_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


async def run_evals():
    settings = get_settings()
    session_manager = SessionManager(settings.erp_db_url)
    pipeline = NiyamPipeline(session_manager)
    
    data_path = Path("data/gold/intake_contracts.jsonl")
    if not data_path.exists():
        print(f"Error: {data_path} not found.")
        return
        
    print("--- NiyamTrace Evals ---")
    print(f"Dataset: {data_path}")
    print("=" * 40)
    
    cases = load_cases(data_path)
    total = len(cases)
    passed = 0
    
    for case in cases:
        raw_text = case["raw_text"]
        expected_action = case["expected_action"]
        
        req = InvokeRequest(
            request_id=str(uuid.uuid4()),
            actor_id="eval_user",
            raw_text=raw_text,
            task_id=case["task_id"],
            variant_group_id=case.get("variant_group_id")
        )
        
        try:
            # We skip real tool execution side-effects by using a mock or just evaluating intent
            # For safety, we use simulate=True to not commit changes
            req.simulate = True
            
            result = await pipeline.run(req)
            
            actual_action = result.get("contract", {}).get("action")
            
            if actual_action == expected_action:
                passed += 1
                status = "✅ PASS"
            else:
                status = f"❌ FAIL (Expected: {expected_action}, Got: {actual_action})"
                
            print(f"[{case['language_form']}] {raw_text[:40]}... -> {status}")
        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
            print(f"[{case['language_form']}] {raw_text[:40]}... -> ❌ ERROR: {e}")
                
    print("=" * 40)
    print(f"Eval Results: {passed}/{total} ({(passed/total)*100 if total > 0 else 0:.1f}%) passed.")
    
if __name__ == "__main__":
    asyncio.run(run_evals())
