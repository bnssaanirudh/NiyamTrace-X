from typing import Any, Dict
from packages.config import get_settings
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json

class LLMProvider:
    def __init__(self, backend: str):
        self.backend = backend
        settings = get_settings()

        if self.backend == "gemini":
            from google import genai
            self.client = genai.Client(api_key=settings.gemini_api_key)
            self.model_name = "gemini-2.5-flash"
        elif self.backend == "groq":
            from groq import Groq
            self.client = Groq(api_key=settings.groq_api_key)
            self.model_name = "llama3-8b-8192"
        elif self.backend == "local":
            from openai import OpenAI
            self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
            self.model_name = "qwen2.5:7b"
        elif self.backend == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model_name = "gpt-4o-mini"
        else:
            raise ValueError(f"Unknown backend {self.backend}")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=10, max=65),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def generate(self, prompt: Dict[str, Any], schema_class: Any) -> Any:
        if self.backend == "gemini":
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt["user"],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema_class,
                    temperature=0.0
                ),
            )
            return response.parsed
        elif self.backend == "groq":
            schema_str = schema_class.model_json_schema()
            sys_msg = prompt["system"] + f"\nYou must output valid JSON matching the following schema EXACTLY. Do not wrap it in markdown.\n{json.dumps(schema_str)}"
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt["user"]}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return schema_class.model_validate_json(completion.choices[0].message.content)
        else:
            # local or openai
            completion = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                response_format=schema_class,
                temperature=0.0
            )
            return completion.choices[0].message.parsed
