#!/usr/8/env python
"""
scripts/load_test.py — API Load Tester

A simple script using httpx and asyncio to blast the gateway API
with concurrent requests to verify throughput and Uvicorn worker stability.
"""

import asyncio
import time
from typing import Any

try:
    import httpx
except ImportError:
    print("Please install httpx: pip install httpx")
    exit(1)

API_URL = "http://localhost:8000/api/v1/trace"
CONCURRENCY = 50
TOTAL_REQUESTS = 200

# Sample payloads representing real intents
PAYLOADS = [
    {
        "actor_role": "finance_admin",
        "actor_id": "U-1234",
        "text": "archive all invoices for vendor 1234 from last month",
    },
    {
        "actor_role": "it_admin",
        "actor_id": "U-9999",
        "text": "block user 5678 for 7 days",
    },
    {
        "actor_role": "finance_director",
        "actor_id": "U-5555",
        "text": "suspend vendor 1234 because of fraud",
    }
]

async def send_request(client: httpx.AsyncClient, i: int) -> dict[str, Any]:
    payload = PAYLOADS[i % len(PAYLOADS)]
    try:
        start_time = time.perf_counter()
        response = await client.post(API_URL, json=payload, timeout=10.0)
        elapsed = time.perf_counter() - start_time
        return {
            "status": response.status_code,
            "latency": elapsed,
            "ok": response.is_success,
            "error": None
        }
    except Exception as e:
        return {
            "status": 0,
            "latency": 0.0,
            "ok": False,
            "error": str(e)
        }

async def worker(queue: asyncio.Queue, client: httpx.AsyncClient, results: list):
    while True:
        try:
            req_index = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        
        res = await send_request(client, req_index)
        results.append(res)
        queue.task_done()

async def run_load_test():
    print(f"Starting load test: {TOTAL_REQUESTS} requests, {CONCURRENCY} concurrency.")
    
    queue = asyncio.Queue()
    for i in range(TOTAL_REQUESTS):
        queue.put_nowait(i)
        
    results = []
    
    start_time = time.perf_counter()
    
    limits = httpx.Limits(max_connections=CONCURRENCY, max_keepalive_connections=CONCURRENCY)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = []
        for _ in range(CONCURRENCY):
            tasks.append(asyncio.create_task(worker(queue, client, results)))
            
        await asyncio.gather(*tasks)
        
    total_time = time.perf_counter() - start_time
    
    # Calculate stats
    success_count = sum(1 for r in results if r["ok"])
    error_count = len(results) - success_count
    latencies = [r["latency"] for r in results if r["ok"]]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    throughput = TOTAL_REQUESTS / total_time
    
    print("\nLoad Test Results:")
    print("-" * 30)
    print(f"Total time:       {total_time:.2f}s")
    print(f"Throughput:       {throughput:.2f} req/s")
    print(f"Success count:    {success_count}")
    print(f"Error count:      {error_count}")
    print(f"Average latency:  {avg_latency*1000:.2f}ms")

if __name__ == "__main__":
    asyncio.run(run_load_test())
