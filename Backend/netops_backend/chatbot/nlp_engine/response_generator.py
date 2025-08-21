"""Natural language response generator using flan-t5 summarization.

We summarize longer CLI output to a user-friendly explanation. For short
outputs we echo them with a compact template. If the model cannot be loaded
we fall back to rule / template based condensation.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List

_GEN_MODEL = None  # (tokenizer, model) or False

def _load_model():
    """Lazy-load Hugging Face summarizer (default: flan-t5-base)."""
    global _GEN_MODEL
    if _GEN_MODEL is not None:
        return _GEN_MODEL if _GEN_MODEL is not False else None
    if os.getenv("NLP_DISABLE_SUMMARY", "0") == "1":
        _GEN_MODEL = False
        return None
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        model_name = os.getenv("NLP_SUMMARY_MODEL", "google/flan-t5-base")
        tok = AutoTokenizer.from_pretrained(model_name)
        mdl = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        _GEN_MODEL = (tok, mdl)
        print(f"[response_generator] Loaded summarizer {model_name}")
    except Exception as e:
        print("[response_generator] load failed:", e)
        _GEN_MODEL = False
        return None
    return _GEN_MODEL


def _simple_condense(text: str, max_words: int = 60) -> str:
    """Fallback: trim long output to first N words."""
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]) + " …"


def _clean_cli_text(text: str) -> str:
    """Remove CLI artifacts (ANSI, multiple spaces, control chars)."""
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)  # strip ANSI
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _chunk_text(words: List[str], chunk_size: int = 400) -> List[str]:
    """Split word list into chunks (to avoid >512 token errors)."""
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]


TEMPLATES = {
    "show": "Here is the summarized result for '{command}': {summary}",
    "configure": "Configuration command '{command}' applied. Summary: {summary} NOTE: Review changes before committing to production.",
    "reset": "Reset-related command '{command}' executed. Result: {summary}",
    "ping": "Ping result for '{command}': {summary}",
    "troubleshoot": "Diagnostic output for '{command}': {summary}",
}


def _template_wrap(label: str, command: str, summary: str) -> str:
    tpl = TEMPLATES.get(label)
    if not tpl:
        return f"Result for intent '{label}' (command '{command}'): {summary}" if label else summary
    return tpl.format(command=command, summary=summary)


def _looks_bad(text: str) -> bool:
    """Detect hallucinated or useless summaries.

    Added detection for imperative / instructional openings like 'Specify the ...'
    which indicate the model described the task instead of summarizing content.
    """
    lower = text.strip().lower()
    if len(lower.split()) < 3:
        return True
    bad_phrases = [
        "a computer is a computer",
        "some information",
        "connected to a network",
        "this is output",
        "specify the",
        "provide the",
        "give the",
        "list the interfaces",
    ]
    if re.match(r"^(specify|provide|give|list|show|display)\b", lower):
        return True
    return any(bp in lower for bp in bad_phrases)


def _parse_interface_table(lines: List[str]) -> str | None:
    """Summarize interface status style tables deterministically.

    Heuristics:
      - Find header containing 'interface' AND one of 'status', 'protocol', 'vlan'.
      - Parse following lines until prompt or blank separator.
      - Count up/up, admin-down, down/down, others.
      - Provide small sample (up to 3 entries).
    """
    header_i = None
    for i, l in enumerate(lines[:25]):
        low = l.lower()
        if 'interface' in low and (('status' in low) or ('protocol' in low) or ('vlan' in low)):
            header_i = i
            break
    if header_i is None:
        return None
    entries = []
    for raw in lines[header_i+1:]:
        if not raw.strip():
            # allow sparse; continue scanning
            continue
        if re.match(r"^[=-]{3,}$", raw.strip()):
            continue
        if raw.strip().startswith(('Device#','Router#','Switch#')):
            break
        parts = raw.split()
        if len(parts) < 2:
            continue
        name = parts[0]
        tail = [p.lower() for p in parts[1:6]]
        status_label = None
        status_join = " ".join(tail)
        if 'administratively' in status_join and 'down' in status_join:
            status_label = 'admin-down'
        elif tail.count('up') >= 2:
            status_label = 'up/up'
        elif tail.count('down') >= 2:
            status_label = 'down/down'
        elif 'up' in tail and 'down' in tail:
            status_label = 'up/down'
        else:
            # pick first status-like token
            status_label = next((t for t in tail if t in {'up','down','err-disabled','disabled'}), 'unknown')
        entries.append((name, status_label))
        if len(entries) >= 1024:
            break
    if not entries:
        return None
    total = len(entries)
    counts = {}
    for _, st in entries:
        counts[st] = counts.get(st, 0) + 1
    # Build ordered summary
    order = ['up/up','up/down','down/down','admin-down','err-disabled','unknown']
    parts = [f"{k}:{counts[k]}" for k in order if k in counts]
    # Add any other statuses
    for k,v in counts.items():
        if k not in order:
            parts.append(f"{k}:{v}")
    sample = ", ".join([f"{n} {s}" for n,s in entries[:3]])
    return f"{total} interfaces ({', '.join(parts)}). Sample: {sample}."


def _summarize_with_model(cli_command: str, cleaned: str) -> str | None:
    """Run summarization model with chunking support."""
    try:
        model_ctx = _load_model()
        if not model_ctx:
            return None
        tok, mdl = model_ctx

        words = cleaned.split()
        if len(words) > 480:
            # Split into chunks and summarize each
            chunks = _chunk_text(words, 380)
            summaries = []
            for ch in chunks:
                prompt = (
                    f"Summarize this CLI output (focus on key status, up/down, errors, counts) in <=50 words.\n"
                    f"Command: {cli_command}\nOutput: {ch}\nSummary:"
                )
                x = tok(prompt, return_tensors="pt", truncation=True)
                y = mdl.generate(**x, max_new_tokens=80)
                summaries.append(tok.decode(y[0], skip_special_tokens=True).strip())
            # Summarize the summaries
            combined = " ".join(summaries)
            prompt_final = f"Combine and refine these summaries into <=90 words, clear and concise:\n{combined}\nFinal Summary:"
            x = tok(prompt_final, return_tensors="pt", truncation=True)
            y = mdl.generate(**x, max_new_tokens=100)
            return tok.decode(y[0], skip_special_tokens=True).strip()
        else:
            prompt = (
                f"Summarize this network device CLI output in <=90 words. "
                f"Highlight interface status, errors, routes, or anomalies.\n"
                f"Command: {cli_command}\nOutput: {cleaned}\nSummary:"
            )
            x = tok(prompt, return_tensors="pt", truncation=True)
            y = mdl.generate(**x, max_new_tokens=110)
            return tok.decode(y[0], skip_special_tokens=True).strip()
    except Exception as e:
        print("[response_generator] generation failed, fallback:", e)
        return None


def generate_natural_response(intent: Dict[str, Any], entities: Dict[str, Any], cli_command: str, cli_output: str) -> str:
    """Convert raw CLI output into a user-friendly natural language message."""
    if not cli_output:
        return f"The command '{cli_command}' executed but returned no output."

    cleaned = _clean_cli_text(cli_output)
    word_count = len(cleaned.split())

    # Short outputs → echo back
    if word_count < 5:
        return f"Command '{cli_command}' succeeded. Output: {cleaned}"

    # Deterministic interface table summary first (if applicable)
    natural_text = None
    if cli_command.lower().startswith('show'):
        table_sum = _parse_interface_table(cli_output.splitlines())
        if table_sum:
            natural_text = table_sum

    # Model summarization if still needed
    if natural_text is None:
        natural_text = _summarize_with_model(cli_command, cleaned)

    # Fallback to truncation if summary is bad/empty
    if not natural_text or _looks_bad(natural_text):
        natural_text = _simple_condense(cleaned)

    label = (intent or {}).get("label", "")
    return _template_wrap(label, cli_command, natural_text)
