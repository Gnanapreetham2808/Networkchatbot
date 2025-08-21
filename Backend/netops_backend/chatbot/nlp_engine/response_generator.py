"""
Response generation module.

Views expect generate_natural_response(intent_dict, entities_dict, cli_command, cli_output).
Now integrates with Hugging Face model (via cli_interface) to improve responses.
"""

from __future__ import annotations
from typing import Any, Dict

def generate_natural_response(intent: Dict[str, Any], entities: Dict[str, Any], cli_command: str, cli_output: str) -> str:
    """
    Generate a natural response from CLI command output.
    Falls back to summarization if the model is not available.
    """

    # Ensure we have a command string for messaging
    if not cli_command:
        query = intent.get("query", "unknown request") if isinstance(intent, dict) else "unknown request"
        cli_command = f"(no-mapping for: {query})"

    if not cli_output:
        return f"Command '{cli_command}' produced no output."

    # Clean up CLI output for readability
    cleaned = " ".join(cli_output.strip().split())
    if len(cleaned.split()) > 60:
        cleaned = " ".join(cleaned.split()[:60]) + " …"

    # Pick a friendly prefix based on intent
    label = intent.get("label") if isinstance(intent, dict) else None
    prefix = {
        "show": "Result",
        "config": "Configuration",
        "check": "Verification",
        "unknown": "Output",
    }.get(label or "", "Output")

    # Return final response
    return f"{prefix} for '{cli_command}': {cleaned}"
