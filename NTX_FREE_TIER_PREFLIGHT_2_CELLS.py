# %% CELL 1
# ============================================================
# CELL 1 — FREE-TIER PREFLIGHT
# Gemini retry/fallback + confirmed Groq Qwen/GPT-OSS
# ============================================================

from pathlib import Path
from openai import OpenAI
import pandas as pd
import time
import os

# ------------------------------------------------------------
# Fix standalone execution
# ------------------------------------------------------------

RESULTS = Path("/content/NTX_FREE_TIER_RESULTS")
RESULTS.mkdir(parents=True, exist_ok=True)

print("Results folder:", RESULTS)


# ------------------------------------------------------------
# API KEYS
#
# Assumes these were already entered earlier:
#
# GEMINI_API_KEY
# GROQ_API_KEY
# ------------------------------------------------------------

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing.")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing.")


# ------------------------------------------------------------
# TEST FUNCTION
# ------------------------------------------------------------

TEST_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order using its order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string"
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False
            }
        }
    }
]


# ------------------------------------------------------------
# ONLY MODELS WE ACTUALLY NEED
# ------------------------------------------------------------

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
]

GROQ_MODELS = [
    {
        "provider": "groq",
        "family": "Qwen",
        "model": "qwen/qwen3.8-27b",
    },
    {
        "provider": "groq",
        "family": "GPT-OSS",
        "model": "openai/gpt-oss-20b",
    },
]


def test_model(provider, family, model, api_key, base_url, retries=3):
    result = {
        "provider": provider,
        "family": family,
        "model": model,
        "chat_ok": False,
        "tool_ok": False,
        "chat_error": "",
        "tool_error": "",
        "status": "FAILED",
    }

    client = OpenAI(api_key=api_key, base_url=base_url)

    for attempt in range(1, retries + 1):
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Reply exactly OK"}],
                temperature=0,
                max_tokens=16,
            )
            result["chat_ok"] = bool(r.choices)
            result["chat_error"] = ""
            break
        except Exception as e:
            result["chat_error"] = repr(e)
            print(f"  Chat attempt {attempt}/{retries} failed:", str(e)[:180])
            if attempt < retries:
                time.sleep(2 ** attempt)

    if result["chat_ok"]:
        for attempt in range(1, retries + 1):
            try:
                r = client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": "Call lookup_order for order A123."
                    }],
                    tools=TEST_TOOL,
                    tool_choice={
                        "type": "function",
                        "function": {"name": "lookup_order"}
                    },
                    temperature=0,
                    max_tokens=128,
                )

                msg = r.choices[0].message
                calls = getattr(msg, "tool_calls", None)

                if calls:
                    called_name = (
                        calls[0].function.name
                        if calls[0].function
                        else None
                    )
                    result["tool_ok"] = (called_name == "lookup_order")

                if result["tool_ok"]:
                    result["tool_error"] = ""
                    break

            except Exception as e:
                result["tool_error"] = repr(e)
                print(f"  Tool attempt {attempt}/{retries} failed:", str(e)[:180])
                if attempt < retries:
                    time.sleep(2 ** attempt)

    if result["chat_ok"] and result["tool_ok"]:
        result["status"] = "OK"

    return result


rows = []
working_gemini = None

print("\n" + "=" * 80)
print("SEARCHING FOR FREE GEMINI MODEL")
print("=" * 80)

for model in GEMINI_MODELS:
    print(f"\nTesting Gemini: {model}")

    result = test_model(
        provider="gemini",
        family="Gemini",
        model=model,
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        retries=4,
    )

    rows.append(result)

    print(" Chat:", "✅" if result["chat_ok"] else "❌")
    print(" Tool:", "✅" if result["tool_ok"] else "❌")

    if result["status"] == "OK":
        working_gemini = model
        print("\n✅ Working Gemini model found:", model)
        break


print("\n" + "=" * 80)
print("VERIFYING GROQ MODELS")
print("=" * 80)

for item in GROQ_MODELS:
    print(f"\nTesting {item['family']}:", item["model"])

    result = test_model(
        provider="groq",
        family=item["family"],
        model=item["model"],
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        retries=2,
    )

    rows.append(result)

    print(" Chat:", "✅" if result["chat_ok"] else "❌")
    print(" Tool:", "✅" if result["tool_ok"] else "❌")


preflight = pd.DataFrame(rows)

print("\n" + "=" * 90)
print("FREE-TIER PREFLIGHT RESULT")
print("=" * 90)

display(
    preflight[
        [
            "provider",
            "family",
            "model",
            "chat_ok",
            "tool_ok",
            "status",
            "chat_error",
            "tool_error",
        ]
    ]
)

preflight.to_csv(
    RESULTS / "00_free_tier_provider_preflight.csv",
    index=False
)

print("\nSaved:", RESULTS / "00_free_tier_provider_preflight.csv")

# %% CELL 2
# ============================================================
# CELL 2 — BUILD FINAL 3-FAMILY FREE-TIER MATRIX
# ============================================================

import pandas as pd

selected = []

for family in ["Gemini", "Qwen", "GPT-OSS"]:

    hits = preflight[
        (preflight["family"] == family)
        &
        (preflight["status"] == "OK")
    ]

    if len(hits) == 0:
        print(f"❌ {family}: no successful model")
        continue

    row = hits.iloc[0]

    if row["provider"] == "gemini":
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    else:
        base_url = "https://api.groq.com/openai/v1"

    selected.append(
        {
            "provider": row["provider"],
            "family": row["family"],
            "model": row["model"],
            "base_url": base_url,
        }
    )


selected_df = pd.DataFrame(selected)

print("\n" + "=" * 90)
print("FINAL FREE-TIER PAPER EXPERIMENT MATRIX")
print("=" * 90)

display(selected_df)

required = {"Gemini", "Qwen", "GPT-OSS"}

found = set(selected_df["family"]) if len(selected_df) else set()
missing = required - found

if missing:

    print("\n❌ STILL MISSING:", sorted(missing))

    if "Gemini" in missing:
        print("""
Gemini is the likely blocker.

If every Gemini fallback returned 503:
- do NOT rerun Groq separately
- rerun CELL 1 later
- it will retry Gemini first and then verify Groq
""")

    raise RuntimeError(
        "Three-family free-tier matrix is not complete yet."
    )


print("""
============================================================
✅ FREE-TIER THREE-FAMILY MATRIX READY
============================================================

Gemini   → Gemini free API
Qwen     → Groq free tier
GPT-OSS  → Groq free tier

You can now proceed to BFCL + AgentDojo + τ³.
============================================================
""")


selected_df.to_csv(
    RESULTS / "01_selected_free_tier_models.csv",
    index=False
)

selected_df.to_json(
    RESULTS / "01_selected_free_tier_models.json",
    orient="records",
    indent=2,
)

print("Saved:", RESULTS / "01_selected_free_tier_models.json")
