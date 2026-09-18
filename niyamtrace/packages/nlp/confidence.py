class ConfidenceCalibrator:
    @staticmethod
    def is_confident(raw_confidence: float, intent: str) -> bool:
        """
        Calibrate raw LLM confidence based on intent sensitivity.
        Security-sensitive intents require higher confidence.
        """
        thresholds = {
            "access.grant": 0.8,
            "vendor.suspend": 0.85,
            "invoice.archive": 0.5,
            "limit.update": 0.75,
            "unknown": 0.9,
        }
        threshold = thresholds.get(intent, 0.6)
        return raw_confidence >= threshold
