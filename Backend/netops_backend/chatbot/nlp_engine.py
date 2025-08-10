from transformers import pipeline
import difflib

# Load zero-shot classification model
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Predefined intents
INTENTS = ["show", "configure", "reset", "ping"]

# Expanded CLI commands
COMMAND_MAPPER = {
    # System info
    "show version": "show version",
    "show running-config": "show running-config",
    "show startup-config": "show startup-config",
    "show clock": "show clock",
    "show inventory": "show inventory",
    "show environment": "show environment",
    "show users": "show users",

    # Interfaces
    "show ip interface brief": "show ip interface brief",
    "show ipv6 interface brief": "show ipv6 interface brief",
    "show interfaces": "show interfaces",
    "show interfaces status": "show interfaces status",
    "show mac address-table": "show mac address-table",

    # Routing
    "show ip route": "show ip route",
    "show ipv6 route": "show ipv6 route",
    "show ip protocols": "show ip protocols",
    "show arp": "show arp",

    # Performance & Logs
    "show logging": "show logging",
    "show processes cpu": "show processes cpu",
    "show processes memory": "show processes memory",

    # Config / Actions
    "configure vlan": "vlan {vlan_id}",
    "ping": "ping {ip}",
}

# Natural language synonyms → CLI mapping
NATURAL_TO_CLI = {
    "current version": "show version",
    "device version": "show version",
    "running configuration": "show running-config",
    "startup configuration": "show startup-config",
    "current time": "show clock",
    "hardware inventory": "show inventory",
    "environment status": "show environment",
    "logged in users": "show users",
    "ip interfaces": "show ip interface brief",
    "ipv6 interfaces": "show ipv6 interface brief",
    "all interfaces": "show interfaces",
    "interface status": "show interfaces status",
    "mac table": "show mac address-table",
    "ip routes": "show ip route",
    "ipv6 routes": "show ipv6 route",
    "routing protocols": "show ip protocols",
    "arp table": "show arp",
    "system logs": "show logging",
    "cpu usage": "show processes cpu",
    "memory usage": "show processes memory",
}


def extract_intent_and_entities(query):
    """Identify intent and extract entities from user query"""
    result = classifier(query, INTENTS)
    intent = result['labels'][0]  # highest ranked intent

    entities = {}
    query_lower = query.lower()

    # VLAN extraction
    if "vlan" in query_lower:
        for word in query_lower.split():
            if word.isdigit():
                entities['vlan_id'] = word
                break

    # IP extraction
    if "." in query_lower:
        for word in query_lower.split():
            if '.' in word and word.count('.') == 3:
                entities['ip'] = word
                break

    return intent, entities


def map_to_cli_command(intent, query, entities):
    """Map detected intent & entities to a CLI command"""
    query_lower = query.lower()

    # 1️⃣ Check natural language synonyms
    for phrase, cli_cmd in NATURAL_TO_CLI.items():
        if phrase in query_lower:
            return cli_cmd

    # 2️⃣ Exact CLI match
    if query_lower in COMMAND_MAPPER:
        if '{vlan_id}' in COMMAND_MAPPER[query_lower] and 'vlan_id' in entities:
            return COMMAND_MAPPER[query_lower].format(vlan_id=entities['vlan_id'])
        if '{ip}' in COMMAND_MAPPER[query_lower] and 'ip' in entities:
            return COMMAND_MAPPER[query_lower].format(ip=entities['ip'])
        return COMMAND_MAPPER[query_lower]

    # 3️⃣ Fuzzy match to closest CLI command
    close_matches = difflib.get_close_matches(query_lower, COMMAND_MAPPER.keys(), n=1, cutoff=0.6)
    if close_matches:
        return COMMAND_MAPPER[close_matches[0]]

    # 4️⃣ Intent-based mapping
    if intent == "configure" and "vlan" in query_lower and 'vlan_id' in entities:
        return f"vlan {entities['vlan_id']}"
    if intent == "ping" and 'ip' in entities:
        return f"ping {entities['ip']}"

    # 5️⃣ Default fallback
    return "show version"
