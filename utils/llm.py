import os
import time
from typing import Type, TypeVar
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

load_dotenv(override=True)

T = TypeVar("T", bound=BaseModel)


def get_gemini_client() -> genai.Client:
    load_dotenv(override=True)
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables (.env).")
    return genai.Client(api_key=api_key)


def get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()


def generate_structured(
    prompt: str,
    response_schema: Type[T],
    system_instruction: str = "You are a precise, realistic travel planning specialist.",
    max_retries: int = 3
) -> T:
    client = get_gemini_client()
    primary_model = get_model_name()
    models_to_try = list(dict.fromkeys([primary_model, "gemini-3.5-flash-lite", "gemini-3.5-flash"]))
    last_error = None

    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.4,
                    ),
                )
                if response.parsed is not None:
                    return response.parsed
                return response_schema.model_validate_json(response.text)
            except errors.APIError as e:
                last_error = e
                if e.code == 404:
                    break
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))

    raise RuntimeError(f"Gemini structured generation failed after retries: {last_error}")