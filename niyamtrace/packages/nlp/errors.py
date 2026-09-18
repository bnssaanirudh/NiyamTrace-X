class NLPExtractionError(Exception):
    def __init__(self, message: str, stage: str, detail: str = None):
        self.message = message
        self.stage = stage
        self.detail = detail
        super().__init__(self.message)

class ConfidenceTooLowError(NLPExtractionError):
    def __init__(self, confidence: float, threshold: float):
        super().__init__(
            message=f"Extraction confidence {confidence} is below threshold {threshold}",
            stage="LLMExtractor",
            detail="User clarification required"
        )
