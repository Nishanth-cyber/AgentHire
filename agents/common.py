import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from services.llm import get_current_llm
from services.structured_output import parse_structured_response, StructuredOutputError

logger = logging.getLogger(__name__)

def get_schema_template(schema) -> str:
    """Generate a clean, unambiguous JSON template showing the exact expected keys."""
    fields = {}
    for name, field in schema.model_fields.items():
        if "score" in name:
            fields[name] = 85
        elif any(k in name for k in [
            "skills", "requirements", "strengths", "weaknesses", "suggestions",
            "keywords", "experience", "education", "projects", "certifications",
            "achievements", "gaps", "responsibilities", "partial_matches"
        ]):
            fields[name] = [f"extracted {name.replace('_', ' ')} item"]
        else:
            fields[name] = f"extracted {name.replace('_', ' ')}"
    return json.dumps(fields, indent=2)

def invoke_structured(system: str, payload: dict, schema, max_retries: int = 1):
    """
    Centralized structured invocation pipeline:
    LLM -> parse_structured_response -> JSON -> Pydantic validation.
    Provides the exact JSON schema template to the model in the prompt.
    """
    llm = get_current_llm()
    template_str = get_schema_template(schema)

    system_prompt = f"""{system}

CRITICAL OUTPUT INSTRUCTIONS:
1. You MUST extract all available information. Do NOT return empty fields or empty lists if information exists in the provided text.
2. Return ONLY a valid JSON object matching this EXACT key structure:
{template_str}
3. Use the EXACT top-level keys shown above.
4. Do NOT use Markdown code fences (do NOT output ```json ... ```).
5. Do NOT include explanations, thinking tags, or prose outside the JSON object."""

    if len(payload) == 1 and ("resume_text" in payload or "job_description" in payload):
        key = list(payload.keys())[0]
        label = "RESUME TEXT" if key == "resume_text" else "JOB DESCRIPTION TEXT"
        human_content = f"{label}:\n{payload[key]}\n\nExtract all information from the {label.lower()} into the requested JSON schema now."
    else:
        human_content = "INPUT DATA:\n" + json.dumps(payload, indent=2, ensure_ascii=False) + "\n\nAnalyze the input data and return the requested JSON object now."

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_content)]
    raw_response = llm.invoke(messages)

    try:
        return parse_structured_response(raw_response, schema)
    except StructuredOutputError as first_err:
        if max_retries > 0:
            logger.warning(f"First pass failed for {schema.__name__}: {first_err}. Retrying once with strict schema correction...")
            retry_system = f"You are a strict JSON extractor. Return ONLY valid JSON with keys: {list(schema.model_fields.keys())}. No markdown fences, no explanations."
            retry_human = f"Extract all details from this input into the JSON schema:\n{human_content}"
            retry_response = llm.invoke([SystemMessage(content=retry_system), HumanMessage(content=retry_human)])
            try:
                return parse_structured_response(retry_response, schema)
            except StructuredOutputError as retry_err:
                logger.error(f"Retry failed for {schema.__name__}: {retry_err}")
                raise RuntimeError(
                    f"{schema.__name__} could not produce valid structured output. Please try again."
                ) from retry_err
        raise RuntimeError(
            f"{schema.__name__} parsing failed: {first_err}"
        ) from first_err
