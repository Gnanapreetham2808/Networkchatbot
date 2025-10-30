"""Provider-agnostic CLI prediction router.

Selects between the local finetuned T5 (nlp_model.predict_cli) and external LLMs
(OpenAI, Google Gemini, or a generic HTTP endpoint) based on environment variables.

Environment:
    CLI_LLM_PROVIDER   = local | openai | gemini | http
    CLI_LLM_MODEL      = provider-specific model name (e.g., gpt-4o-mini, gemini-pro)
    CLI_LLM_BASE_URL   = base URL for generic HTTP provider
  CLI_LLM_TIMEOUT    = request timeout in seconds (default 15)
  CLI_LLM_SYSTEM_PROMPT = optional custom system prompt
  OPENAI_API_KEY     = required if provider=openai
  GEMINI_API_KEY     = required if provider=gemini

Behavior:
  - Returns a single line CLI command as string, or an error string prefixed with [Error]
  - Strips code fences/backticks and extra commentary if present
"""
from __future__ import annotations

import os
import json
import logging
from typing import Optional

from .nlp_model import predict_cli as _local_predict

logger = logging.getLogger(__name__)

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # fallback to urllib if requests missing

def _http_post(url: str, headers: dict, payload: dict, timeout: float) -> tuple[int, str]:
    """POST JSON and return (status_code, text). Uses requests if available, else urllib."""
    if requests is not None:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)  # type: ignore
        return resp.status_code, resp.text
    # Fallback: urllib
    import urllib.request
    import urllib.error
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # type: ignore
            return getattr(r, "status", 200), r.read().decode("utf-8")
    except urllib.error.HTTPError as e:  # type: ignore
        return e.code, e.read().decode("utf-8")
    except Exception as e:  # type: ignore
        return 599, str(e)


def _sanitize_cli(text: str) -> str:
    """Normalize LLM text to a single line CLI command without backticks or commentary."""
    if not text:
        return ""
    t = text.strip()
    # remove surrounding code fences/backticks
    if t.startswith("```") and t.endswith("```"):
        t = t.strip("`")
    t = t.strip().strip("`")
    # take the first non-empty line
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    if not lines:
        return ""
    cmd = lines[0]
    # remove leading common prefixes
    for prefix in ("Command:", "CLI:", "Answer:", "Output:"):
        if cmd.lower().startswith(prefix.lower()):
            cmd = cmd[len(prefix):].strip()
    # Remove surrounding quotes
    if (cmd.startswith("\"") and cmd.endswith("\"")) or (cmd.startswith("'") and cmd.endswith("'")):
        cmd = cmd[1:-1].strip()
    return cmd


def _system_prompt() -> str:
    default = (
        "You are a precise network CLI assistant. Given a natural language request, "
        "output exactly one Cisco IOS show command that best answers it. "
        "Return ONLY the command text, with no quotes or explanations."
    )
    return os.getenv("CLI_LLM_SYSTEM_PROMPT", default)


def _predict_via_openai(query: str, model: Optional[str] = None, system: Optional[str] = None) -> str:
    import time
    start_time = time.time()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key missing")
        return "[Error] OPENAI_API_KEY not set"
    model = model or os.getenv("CLI_LLM_MODEL", "gpt-4o-mini")
    url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
    timeout = float(os.getenv("CLI_LLM_TIMEOUT", "15"))
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": (system or _system_prompt())},
            {"role": "user", "content": f"Request: {query}\nReturn only one CLI command."},
        ],
        "temperature": 0.0,
        "n": 1,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    status_code, text = _http_post(url, headers, payload, timeout)
    duration_ms = (time.time() - start_time) * 1000
    
    if status_code >= 400:
        logger.error("OpenAI API request failed", extra={
            'status_code': status_code,
            'query': query[:100],
            'duration_ms': duration_ms,
            'error': text[:500]
        })
        return f"[Error] OpenAI HTTP {status_code}: {text[:2000]}"
    try:
        data = json.loads(text)
        content = data["choices"][0]["message"]["content"]
        result = _sanitize_cli(content)
        logger.info("OpenAI prediction completed", extra={
            'query': query[:100],
            'predicted_cli': result,
            'model': model,
            'duration_ms': duration_ms
        })
        return result
    except Exception as e:
        logger.error("OpenAI response parse failed", extra={
            'query': query[:100],
            'error': str(e),
            'response_preview': text[:500]
        }, exc_info=True)
        return f"[Error] OpenAI parse failure: {e} | raw={text[:1000]}"


def _predict_via_gemini(query: str, model: Optional[str] = None, system: Optional[str] = None) -> str:
    """Predict CLI via Google Gemini API."""
    import time
    start_time = time.time()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("Gemini API key missing")
        return "[Error] GEMINI_API_KEY not set"
    
    model = model or os.getenv("CLI_LLM_MODEL", "gemini-1.5-flash")
    # Gemini REST API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    timeout = float(os.getenv("CLI_LLM_TIMEOUT", "15"))
    
    # Combine system prompt and user query for Gemini
    system_content = system or _system_prompt()
    # Don't add "Return only one CLI command" if custom system prompt is provided (e.g., VLAN creation needs multiple lines)
    if system:
        full_prompt = f"{system_content}\n\nRequest: {query}"
    else:
        full_prompt = f"{system_content}\n\nRequest: {query}\nReturn only one CLI command."
    
    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 300,  # Increased for multi-line VLAN commands
        }
    }
    
    headers = {"Content-Type": "application/json"}
    status_code, text = _http_post(url, headers, payload, timeout)
    duration_ms = (time.time() - start_time) * 1000
    
    if status_code >= 400:
        print(f"[GEMINI ERROR] Status: {status_code}, Response: {text[:1000]}")
        logger.error("Gemini API request failed", extra={
            'status_code': status_code,
            'query': query[:100],
            'duration_ms': duration_ms,
            'error': text[:500]
        })
        return f"[Error] Gemini HTTP {status_code}: {text[:2000]}"
    
    try:
        data = json.loads(text)
        # Gemini response structure: candidates[0].content.parts[0].text
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        result = _sanitize_cli(content)
        logger.info("Gemini prediction completed", extra={
            'query': query[:100],
            'predicted_cli': result,
            'model': model,
            'duration_ms': duration_ms
        })
        return result
    except Exception as e:
        logger.error("Gemini response parse failed", extra={
            'query': query[:100],
            'error': str(e),
            'response_preview': text[:500]
        }, exc_info=True)
        return f"[Error] Gemini parse failure: {e} | raw={text[:1000]}"



def _predict_via_generic_http(query: str, model: Optional[str] = None, system: Optional[str] = None) -> str:
    base = os.getenv("CLI_LLM_BASE_URL")
    if not base:
        return "[Error] CLI_LLM_BASE_URL not set for http provider"
    timeout = float(os.getenv("CLI_LLM_TIMEOUT", "15"))
    url = base.rstrip("/")
    payload = {
        "query": query,
        "system": (system or _system_prompt()),
        "mode": "cli_command",
        "model": model or os.getenv("CLI_LLM_MODEL"),
    }
    headers = {"Content-Type": "application/json"}
    status_code, text = _http_post(url, headers, payload, timeout)
    if status_code >= 400:
        return f"[Error] HTTP {status_code}: {text[:2000]}"
    try:
        data = json.loads(text)
        content = data.get("text") or data.get("content") or data.get("answer")
        if not content:
            return f"[Error] Generic HTTP response missing 'text' | raw={text[:1000]}"
        return _sanitize_cli(content)
    except Exception as e:
        return f"[Error] HTTP parse failure: {e} | raw={text[:1000]}"


def predict_cli(query: str) -> str:
    """Predict a CLI command via configured provider.

    Falls back to local finetuned model if provider unset or set to 'local'.
    """
    provider = (os.getenv("CLI_LLM_PROVIDER", "local") or "local").lower()
    if provider in ("", "local"):
        return _local_predict(query)
    if not query or not query.strip():
        return "[Error] Empty query"
    if provider == "openai":
        return _predict_via_openai(query)
    if provider == "gemini":
        return _predict_via_gemini(query)
    if provider == "http":
        return _predict_via_generic_http(query)
    return f"[Error] Unknown CLI_LLM_PROVIDER={provider}"


def predict_cli_provider(query: str, provider: Optional[str] = None, model: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
    """Predict a CLI command with an explicit provider/model override.

    provider: local | openai | gemini | http
    model: optional provider-specific model name (e.g., gpt-4o-mini, gemini-pro)
    system_prompt: optional custom system prompt
    """
    prov = (provider or os.getenv("CLI_LLM_PROVIDER", "local") or "local").lower()
    if prov in ("", "local"):
        return _local_predict(query)
    if not query or not query.strip():
        return "[Error] Empty query"
    if prov == "openai":
        return _predict_via_openai(query, model=model, system=system_prompt)
    if prov == "gemini":
        return _predict_via_gemini(query, model=model, system=system_prompt)
    if prov == "http":
        return _predict_via_generic_http(query, model=model, system=system_prompt)
    return f"[Error] Unknown CLI_LLM_PROVIDER={prov}"
