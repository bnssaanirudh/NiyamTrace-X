# Multilingual Agent Safety Dataset

This dataset contains 10000 synthetic user requests for evaluating a database-modifying AI agent safety gate.

## Tools covered

1. `invoice.archive`
   - Required slots: `VENDOR_ID`, `MONTH`, `YEAR`
2. `vendor.suspend`
   - Required slots: `VENDOR_ID`, `REASON`
3. `system.grant`
   - Prohibited for normal users

## Languages

- `eng_Latn`: Pure English
- `hin_Latn`: Hinglish / Romanized Hindi mixed with English
- `tel_Telu`: Telugu script
- `tel_Latn`: Romanized Telugu mixed with English

## Files

- `multilingual_agent_safety_dataset_10000.jsonl`: main training/evaluation file
- `multilingual_agent_safety_dataset_10000.json`: same rows as JSON list
- `multilingual_agent_safety_dataset_10000.csv`: spreadsheet-friendly CSV
- `sample_200.json`: small inspection sample
- `dataset_stats.json`: distribution counts

## Distribution

```json
{
  "total_rows": 10000,
  "by_language": {
    "tel_Telu": 2500,
    "hin_Latn": 2500,
    "eng_Latn": 2500,
    "tel_Latn": 2500
  },
  "by_intent": {
    "invoice.archive": 5362,
    "system.grant": 1213,
    "vendor.suspend": 3425
  },
  "by_verdict": {
    "ALLOW": 5265,
    "BLOCK": 4735
  },
  "by_reason_code": {
    "OK": 5265,
    "PROHIBITED_ACTION": 1213,
    "MISSING_TARGET": 2168,
    "TOOL_ARGS_MISSING_TEMPORAL_SCOPE": 1354
  },
  "by_language_and_verdict": {
    "eng_Latn": {
      "ALLOW": 1299,
      "BLOCK": 1201
    },
    "hin_Latn": {
      "BLOCK": 1179,
      "ALLOW": 1321
    },
    "tel_Telu": {
      "ALLOW": 1316,
      "BLOCK": 1184
    },
    "tel_Latn": {
      "ALLOW": 1329,
      "BLOCK": 1171
    }
  },
  "schema": {
    "id": "stable row identifier",
    "raw_text": "user request text",
    "primary_lang": "eng_Latn | hin_Latn | tel_Telu | tel_Latn",
    "expected_intent": "invoice.archive | vendor.suspend | system.grant",
    "expected_slots": "gold slots as JSON object",
    "expected_gate_verdict": "ALLOW | BLOCK",
    "expected_reason_code": "OK | TOOL_ARGS_MISSING_TEMPORAL_SCOPE | MISSING_TARGET | PROHIBITED_ACTION"
  }
}
```

## Notes

This is a synthetic benchmark dataset generated from controlled templates with randomized vendor IDs, months, years, reasons, tones, typos, slang, and code-mixed phrasing. It is suitable for prototyping safety-gate classifiers, slot extraction models, rule-based validators, and LLM-agent guardrail evaluation. For publication-grade use, manually audit a sample and report synthetic-data limitations.
