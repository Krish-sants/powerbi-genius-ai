"""Unified LLM service — wraps OpenAI and Anthropic, picks whichever key is available."""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger
from dotenv import load_dotenv

# Load .env from project root regardless of working directory or import order
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=True)
    logger.debug(f"[LLMService] Loaded .env from {_env_path}")


def _get_provider() -> str:
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    raise RuntimeError("No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")


def _parse_json_robust(content: str) -> Dict:
    """Parse JSON from LLM response, handling common issues."""
    content = content.strip()

    # Strip markdown fences
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first and last fence lines
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        content = "\n".join(inner).strip()

    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Extract first complete JSON object using brace matching
    try:
        start = content.index("{")
        depth = 0
        end = start
        in_string = False
        escape_next = False
        for i, ch in enumerate(content[start:], start):
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        candidate = content[start:end + 1]
        return json.loads(candidate)
    except (ValueError, json.JSONDecodeError):
        pass

    # Last resort: remove trailing commas before } or ] then retry
    try:
        fixed = re.sub(r",\s*([}\]])", r"\1", content)
        return json.loads(fixed)
    except json.JSONDecodeError as e:
        logger.error(f"[LLMService] JSON parse failed. Content length={len(content)}. Error: {e}")
        raise


async def chat_json(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    model_override: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """Send a chat request and return parsed JSON. Works with OpenAI and Anthropic."""
    provider = _get_provider()
    if provider == "anthropic":
        return await _anthropic_json(messages, system, model_override, temperature, max_tokens)
    else:
        return await _openai_json(messages, system, model_override, temperature, max_tokens)


# Reuse a single async client per provider — creating one per request throws away
# the underlying HTTP connection pool and adds TLS handshake latency to every call.
_anthropic_client = None
_openai_client = None


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic as anthropic_sdk
        _anthropic_client = anthropic_sdk.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _anthropic_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


async def _anthropic_json(messages, system, model_override, temperature, max_tokens) -> Dict:
    model = model_override or "claude-sonnet-4-6"
    client = _get_anthropic_client()

    sys_prompt = system or "You are a world-class business intelligence analyst. Always respond with valid JSON only."
    filtered = [m for m in messages if m.get("role") != "system"] or messages

    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=sys_prompt,
        messages=filtered,
    )

    # Log stop reason so we can detect truncation
    stop_reason = response.stop_reason
    if stop_reason == "max_tokens":
        logger.warning(f"[LLMService] Response truncated at max_tokens={max_tokens}. Consider increasing.")

    content = response.content[0].text.strip()
    return _parse_json_robust(content)


async def _openai_json(messages, system, model_override, temperature, max_tokens) -> Dict:
    model = model_override or "gpt-4o"
    client = _get_openai_client()

    all_messages = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)

    response = await client.chat.completions.create(
        model=model,
        messages=all_messages,
        response_format={"type": "json_object"},
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return json.loads(response.choices[0].message.content)


def get_active_provider() -> str:
    try:
        return _get_provider()
    except RuntimeError:
        return "none"
