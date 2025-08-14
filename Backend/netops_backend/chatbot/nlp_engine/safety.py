# chatbot/nlp_engine/safety.py

def gate_command(cmd):
    # Allow-list prefixes (match exact or followed by space)
    BASE_PREFIXES = ["show", "ping", "traceroute"]
    SENSITIVE_KEYWORDS = ["delete", "erase", "format", "reload", "shutdown", "write erase"]
    c = cmd.strip().lower()

    def is_allowed_prefix(text):
        for p in BASE_PREFIXES:
            if text == p or text.startswith(p + " "):
                return True
        return False

    allowed = is_allowed_prefix(c)
    sensitive = any(k in c for k in SENSITIVE_KEYWORDS)
    return {
        "allowed": allowed and not sensitive,
        "needs_confirmation": allowed and sensitive,
        "reason": "allowed prefix" if allowed else "not in allow-list"
    }
