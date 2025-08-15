"""Natural language response generator.

Design goals:
 - Do NOT block Django startup with large model downloads. (Lazy load.)
 - Allow disabling summarization via env var NLP_DISABLE_SUMMARY=1.
 - Allow choosing a lighter model via NLP_SUMMARY_MODEL (defaults to distilbart).
 - Gracefully fall back to raw CLI output if model unavailable or errors occur.
 - Provide short deterministic phrasing for very short outputs.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict

_SUMMARIZER = None  # None = not tried yet, False = permanently unavailable


def _get_summarizer():
    global _SUMMARIZER
    if _SUMMARIZER is not None:
        # Either already loaded object or False
        return _SUMMARIZER if _SUMMARIZER is not False else None

    if os.getenv("NLP_DISABLE_SUMMARY", "0") == "1":
        _SUMMARIZER = False
        return None

    try:
        from transformers import pipeline  # Local import to avoid mandatory dependency if unused
        model_name = os.getenv("NLP_SUMMARY_MODEL", "sshleifer/distilbart-cnn-12-6")
        _SUMMARIZER = pipeline("summarization", model=model_name, device=-1)
        print(f"[response_generator] Loaded summarization model: {model_name}")
    except Exception as e:  # Broad by design: any failure disables summarization
        print("[response_generator] Summarizer unavailable:", e)
        _SUMMARIZER = False
        return None
    return _SUMMARIZER


def _simple_condense(text: str, max_words: int = 60) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]) + " …"


def _clean_cli_text(text: str) -> str:
    # Remove excessive spaces / control chars
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)  # ANSI
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_natural_response(intent: Dict[str, Any], entities: Dict[str, Any], cli_command: str, cli_output: str) -> str:
    """Convert raw CLI output into a user-friendly natural language message.

    Heuristics:
      - Short outputs (<5 words) are echoed directly with success phrasing.
      - Attempt model summarization for longer outputs (lazy load on first call).
      - Fall back to rule-based condensation if summarization fails or disabled.
      - Add light intent-aware framing.
    """

    if not cli_output:
        return f"The command '{cli_command}' executed but returned no output."

    cleaned = _clean_cli_text(cli_output)
    word_count = len(cleaned.split())

    if word_count < 5:
        return f"Command '{cli_command}' succeeded. Output: {cleaned}"

    summarizer = _get_summarizer()
    natural_text = None

    if summarizer:
        try:
            # Some models have a max token length; we lightly truncate if huge
            # (rough heuristic: 1 token ≈ 1.3 words; limit ~800 words)
            if word_count > 800:
                truncated = " ".join(cleaned.split()[:800])
            else:
                truncated = cleaned
            summary = summarizer(truncated, max_length=90, min_length=15, do_sample=False)
            natural_text = summary[0].get("summary_text") if summary else None
        except Exception as e:
            print("[response_generator] Summarization failed, using fallback:", e)
            natural_text = None

    if not natural_text:
        natural_text = _simple_condense(cleaned)

    label = (intent or {}).get("label", "")
    if label == "show":
        return f"Here is the summarized result for '{cli_command}': {natural_text}"
    if label == "configure":
        return f"Configuration command '{cli_command}' applied. Summary: {natural_text}"
    if label:
        return f"Result for intent '{label}' (command '{cli_command}'): {natural_text}"
    return natural_text

