import json
import logging
import re
from typing import Any, Type, TypeVar
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class StructuredOutputError(Exception):
    """Raised when structured JSON cannot be extracted or validated."""
    def __init__(self, message: str, raw_content: str = "", details: str = ""):
        super().__init__(message)
        self.raw_content = raw_content
        self.details = details

def extract_raw_text(response: Any) -> str:
    """Extract string content from LangChain AIMessage, dict, or str."""
    if response is None:
        return ""
    if hasattr(response, "content"):
        c = response.content
        if isinstance(c, list):
            parts = [str(p.get("text", p)) if isinstance(p, dict) else str(p) for p in c]
            return " ".join(parts)
        return str(c)
    if isinstance(response, dict):
        return json.dumps(response)
    return str(response)

def clean_and_extract_json(raw_text: str) -> str:
    """
    Safely cleans and extracts the JSON substring:
    1. Removes DeepSeek R1 <think>...</think> reasoning blocks.
    2. Strips Markdown code fences (```json ... ``` or ``` ... ```).
    3. Handles introductory and concluding conversational text.
    4. Balances braces to find the exact top-level JSON object { ... } or array [ ... ].
    """
    text = raw_text.strip()

    # 1. Strip DeepSeek R1 reasoning tags (<think>...</think>)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    if "<think>" in text:
        parts = text.split("<think>")
        text = parts[0].strip()
        if not text and len(parts) > 1 and "{" in parts[1]:
            text = parts[1][parts[1].find("{"):]

    text = text.strip()

    # 2. Check for markdown code fences: ```json ... ``` or ``` ... ```
    fence_pattern = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", text, re.DOTALL)
    if fence_pattern:
        candidate = fence_pattern.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass  # Fall through to brace extraction

    # Also handle unclosed opening/closing fences
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    # 3. Locate first opening brace
    start_obj = text.find("{")
    start_arr = text.find("[")

    if start_obj == -1 and start_arr == -1:
        return text

    if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
        open_char, close_char = "{", "}"
        start_idx = start_obj
    else:
        open_char, close_char = "[", "]"
        start_idx = start_arr

    # 4. Balanced brace matching (respecting string literals and escapes)
    depth = 0
    in_string = False
    escape = False
    end_idx = -1

    for i in range(start_idx, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == open_char:
                depth += 1
            elif ch == close_char:
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break

    if end_idx != -1:
        return text[start_idx:end_idx + 1].strip()

    # 5. Fallback: slice from first open to last close
    last_idx = text.rfind(close_char)
    if last_idx > start_idx:
        return text[start_idx:last_idx + 1].strip()

    return text

def parse_structured_response(response: Any, schema: Type[T]) -> T:
    """
    Centralized structured-output parsing function:
    1. Extracts raw text safely.
    2. Cleans fences, removes <think> reasoning, and isolates JSON.
    3. Parses JSON with json.loads.
    4. Validates and returns the Pydantic model instance.
    """
    if isinstance(response, schema):
        return response
    if isinstance(response, dict):
        return schema.model_validate(response)

    raw_text = extract_raw_text(response)
    if not raw_text.strip():
        raise StructuredOutputError(
            f"Empty response received from LLM for schema {schema.__name__}",
            raw_content=raw_text
        )

    cleaned_json = clean_and_extract_json(raw_text)

    # Pass 1: Standard json.loads
    parsed_dict = None
    try:
        parsed_dict = json.loads(cleaned_json)
    except Exception as e1:
        # Pass 2: Secondary repair (smart quotes, trailing commas)
        repaired = cleaned_json.replace("“", '"').replace("”", '"').replace("’", "'")
        repaired = re.sub(r",\s*([\}\]])", r"\1", repaired)
        try:
            parsed_dict = json.loads(repaired)
        except Exception as e2:
            logger.warning(
                f"Failed to parse JSON for schema {schema.__name__}: {e1}. Cleaned text was:\n{cleaned_json}"
            )
            raise StructuredOutputError(
                f"Invalid JSON for schema {schema.__name__}: {e1}",
                raw_content=raw_text,
                details=str(e1)
            )

    # Pydantic validation
    try:
        if isinstance(parsed_dict, dict):
            return schema.model_validate(parsed_dict)
        elif isinstance(parsed_dict, list) and hasattr(schema, "__root__"):
            return schema.model_validate(parsed_dict)
        else:
            return schema.model_validate(parsed_dict)
    except ValidationError as ve:
        logger.warning(f"Validation error for {schema.__name__}: {ve}")
        raise StructuredOutputError(
            f"Validation error for {schema.__name__}: {ve}",
            raw_content=raw_text,
            details=str(ve)
        )
