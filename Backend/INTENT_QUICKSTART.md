# Intent Recognition Quick Start

## Test Intent Recognition (Python Shell)

### 1. Open Django Shell

```bash
cd C:\Networkchatbot\Backend\netops_backend
python manage.py shell
```

### 2. Test Basic Recognition

```python
from chatbot.intent_recognizer import recognize_intent

# Test VLAN creation
intent = recognize_intent("create vlan 100 named engineering")
print(f"Intent: {intent.name}")
print(f"Category: {intent.category}")
print(f"Confidence: {intent.confidence:.2f}")
print(f"Parameters: {intent.params}")
print(f"Requires Approval: {intent.requires_approval}")

# Output:
# Intent: vlan_create
# Category: vlan
# Confidence: 0.92
# Parameters: {'vlan_id': '100', 'vlan_name': 'engineering'}
# Requires Approval: True
```

### 3. Test Different Queries

```python
# VLAN Management
queries = [
    "create vlan 200",
    "delete vlan 50",
    "modify vlan 100 name sales",
    "add vlan 300 called marketing"
]

for query in queries:
    intent = recognize_intent(query)
    if intent:
        print(f"\n'{query}'")
        print(f"  → {intent.name} (confidence: {intent.confidence:.2f})")
        print(f"  → params: {intent.params}")
    else:
        print(f"\n'{query}' → No intent recognized")

# Output:
# 'create vlan 200'
#   → vlan_create (confidence: 0.85)
#   → params: {'vlan_id': '200'}
#
# 'delete vlan 50'
#   → vlan_delete (confidence: 0.88)
#   → params: {'vlan_id': '50'}
#
# 'modify vlan 100 name sales'
#   → vlan_modify (confidence: 0.90)
#   → params: {'vlan_id': '100', 'new_name': 'sales'}
```

### 4. Test Interface Configuration

```python
# Interface intents
queries = [
    "configure interface GigabitEthernet0/1",
    "set up port GigabitEthernet0/2 description Uplink",
    "assign interface GigabitEthernet0/1 to vlan 100",
    "enable interface GigabitEthernet0/3"
]

for query in queries:
    intent = recognize_intent(query)
    if intent:
        print(f"\n'{query}'")
        print(f"  → {intent.name}")
        print(f"  → {intent.params}")

# Output:
# 'configure interface GigabitEthernet0/1'
#   → interface_configure
#   → {'interface_name': 'GigabitEthernet0/1'}
#
# 'assign interface GigabitEthernet0/1 to vlan 100'
#   → interface_assign_vlan
#   → {'interface_name': 'GigabitEthernet0/1', 'vlan_id': '100'}
```

### 5. Test Routing

```python
# Routing intents
queries = [
    "add route to 10.0.0.0/8 via 192.168.1.1",
    "create static route 172.16.0.0/12 next-hop 10.0.0.1",
    "delete route 192.168.0.0/16"
]

for query in queries:
    intent = recognize_intent(query)
    if intent:
        print(f"\n'{query}'")
        print(f"  → {intent.name}")
        print(f"  → {intent.params}")

# Output:
# 'add route to 10.0.0.0/8 via 192.168.1.1'
#   → route_add
#   → {'destination': '10.0.0.0/8', 'next_hop': '192.168.1.1'}
#
# 'delete route 192.168.0.0/16'
#   → route_delete
#   → {'destination': '192.168.0.0/16'}
```

### 6. Browse Available Intents

```python
from chatbot.intent_recognizer import get_intent_recognizer

recognizer = get_intent_recognizer()

# Get all categories
print("\nCategories:")
print(recognizer.get_categories())
# Output: ['acl', 'interface', 'management', 'routing', 'vlan']

# Get intents by category
print("\nVLAN Intents:")
for intent_name in recognizer.get_intents_by_category('vlan'):
    intent_config = recognizer._intent_patterns[intent_name]
    print(f"  - {intent_name}: {intent_config['description']}")

# Output:
# VLAN Intents:
#   - vlan_create: Create or configure VLANs
#   - vlan_delete: Delete VLAN
#   - vlan_modify: Modify VLAN configuration

print("\nInterface Intents:")
for intent_name in recognizer.get_intents_by_category('interface'):
    intent_config = recognizer._intent_patterns[intent_name]
    print(f"  - {intent_name}: {intent_config['description']}")

# Output:
# Interface Intents:
#   - interface_configure: Configure network interface
#   - interface_assign_vlan: Assign interface to VLAN
```

## Test via REST API

### 1. Test Read-Only Commands (Should Work ✅)

```bash
# PowerShell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/nlp/network-command/" `
  -ContentType "application/json" `
  -Body '{"query": "show interfaces", "session_id": "test-123"}'
```

**Expected Result:**
- Status: 200 OK
- Command executed successfully

### 2. Test VLAN Creation (Should Return 503 ⚠️)

```bash
# PowerShell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/nlp/network-command/" `
  -ContentType "application/json" `
  -Body '{"query": "create vlan 100 named test", "session_id": "test-123"}'
```

**Expected Result:**
```json
{
  "error": "VLAN automation is currently disabled",
  "intent": "vlan_create",
  "description": "Create or configure VLANs",
  "session_id": "test-123"
}
```
- Status: 503 Service Unavailable
- Intent recognized but automation disabled

### 3. Test Interface Configuration (Should Return 403 🔜)

```bash
# PowerShell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/nlp/network-command/" `
  -ContentType "application/json" `
  -Body '{"query": "configure interface GigabitEthernet0/1", "session_id": "test-123"}'
```

**Expected Result:**
```json
{
  "error": "Configuration approval required",
  "intent": "interface_configure",
  "description": "Configure network interface",
  "params": {
    "interface_name": "GigabitEthernet0/1"
  },
  "session_id": "test-123"
}
```
- Status: 403 Forbidden
- Intent recognized but approval required

### 4. Test Dangerous Command (Should Return 403 ❌)

```bash
# PowerShell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/nlp/network-command/" `
  -ContentType "application/json" `
  -Body '{"query": "erase startup-config", "session_id": "test-123"}'
```

**Expected Result:**
```json
{
  "error": "This command contains potentially dangerous operations",
  "session_id": "test-123"
}
```
- Status: 403 Forbidden
- Dangerous operation blocked

## Check Current Status

### 1. View Intent Recognition Status

```python
from chatbot.intent_recognizer import get_intent_recognizer
import os

recognizer = get_intent_recognizer()

print("Intent Recognition Status")
print("=" * 50)
print(f"Total Intents: {len(recognizer._intent_patterns)}")
print(f"Categories: {', '.join(recognizer.get_categories())}")
print()

# Feature flags
features = {
    'VLAN Automation': os.getenv('ENABLE_VLAN_AUTOMATION', '0') == '1',
    'Interface Automation': os.getenv('ENABLE_INTERFACE_AUTOMATION', '0') == '1',
    'Routing Automation': os.getenv('ENABLE_ROUTING_AUTOMATION', '0') == '1',
    'ACL Automation': os.getenv('ENABLE_ACL_AUTOMATION', '0') == '1'
}

print("Feature Status:")
for feature, enabled in features.items():
    status = "✅ Enabled" if enabled else "⚠️ Disabled"
    print(f"  {feature}: {status}")
```

**Example Output:**
```
Intent Recognition Status
==================================================
Total Intents: 11
Categories: acl, interface, management, routing, vlan

Feature Status:
  VLAN Automation: ⚠️ Disabled
  Interface Automation: ⚠️ Disabled
  Routing Automation: ⚠️ Disabled
  ACL Automation: ⚠️ Disabled
```

## Next Steps

### 1. Install LangChain (For Memory Management)

```powershell
cd C:\Networkchatbot\Backend
.\install_memory.ps1
```

Or manually:
```powershell
cd C:\Networkchatbot\Backend
pip install langchain==0.3.7 langchain-huggingface==0.1.2 langchain-community==0.3.7 sentence-transformers==3.3.1
```

### 2. Test Memory Management

```bash
cd netops_backend
python manage.py memory_test
```

### 3. Enable VLAN Automation (When Ready)

Edit `Backend/.env`:
```bash
ENABLE_VLAN_AUTOMATION=1
```

Restart server:
```bash
cd netops_backend
python manage.py runserver
```

### 4. Build Approval UI (Frontend)

To enable configuration commands:
1. Create approval modal component
2. Display intent details (name, params, confidence)
3. Allow user to approve/reject
4. Send approval token with request
5. Backend validates approval token before execution

## Command Reference

### Intent Recognition Shell Commands

```python
# Import
from chatbot.intent_recognizer import recognize_intent, get_intent_recognizer

# Recognize single query
intent = recognize_intent("your query here")

# Get recognizer instance
recognizer = get_intent_recognizer()

# Browse categories
recognizer.get_categories()

# Browse intents by category
recognizer.get_intents_by_category('vlan')

# Recognize with recognizer instance
recognizer.recognize("your query here")
```

### Useful Management Commands

```bash
# Test memory management
python manage.py memory_test

# Clear memory caches
python manage.py memory_test --clear-all

# View memory stats
python manage.py memory_test --stats

# Django shell
python manage.py shell

# Run server
python manage.py runserver
```

## Troubleshooting

### Issue: "No intent recognized"

**Possible Causes:**
- Query doesn't match any patterns
- Confidence too low (< threshold)

**Solution:**
```python
# Test with lower threshold
intent = recognize_intent("your query", min_confidence=0.5)

# Or check raw pattern matches
recognizer = get_intent_recognizer()
import re
for name, config in recognizer._intent_patterns.items():
    for pattern in config['compiled_patterns']:
        if pattern.search("your query"):
            print(f"Matches: {name}")
```

### Issue: "Intent recognized but params empty"

**Possible Causes:**
- Query doesn't contain extractable parameters
- Parameter patterns don't match

**Solution:**
```python
# Check what params are expected
recognizer = get_intent_recognizer()
intent_config = recognizer._intent_patterns['vlan_create']
print("Expected params:", list(intent_config['param_extractors'].keys()))

# Test parameter extraction
import re
query = "create vlan 100 named test"
for param_name, pattern in intent_config['param_extractors'].items():
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        print(f"{param_name}: {match.group(1) if match.lastindex >= 1 else match.group(0)}")
```

### Issue: API returns 403 for all config commands

**Expected Behavior:**
- This is intentional! All configuration commands require approval
- VLAN automation returns 503 (disabled)
- Other config intents return 403 (approval required)

**To Enable:**
1. Build approval workflow in frontend
2. Update backend to accept approval tokens
3. Enable feature flags in `.env`

## Summary

**Current Capabilities:**
- ✅ Intent recognition: 11 intents across 5 categories
- ✅ Pattern matching: Flexible regex-based detection
- ✅ Parameter extraction: Automatic extraction from natural language
- ✅ Command safety: Read-only, configuration, dangerous classification
- ✅ Backend validation: Intent-based request handling

**Current Limitations:**
- ⚠️ VLAN automation disabled (intentional)
- ⚠️ Other config features require approval (coming soon)
- ⚠️ No frontend approval UI yet

**Testing Status:**
- ✅ Read-only commands work
- ⚠️ Config commands recognized but blocked
- ❌ Dangerous commands blocked

**Quick Test Commands:**
```python
# Python shell
from chatbot.intent_recognizer import recognize_intent
recognize_intent("create vlan 100 named test")  # VLAN
recognize_intent("configure interface GigabitEthernet0/1")  # Interface
recognize_intent("add route to 10.0.0.0/8 via 192.168.1.1")  # Routing
```

For full documentation, see:
- [INTENT_RECOGNITION.md](./INTENT_RECOGNITION.md) - Complete guide
- [MEMORY_MANAGEMENT.md](./MEMORY_MANAGEMENT.md) - Memory system
- [MEMORY_QUICKSTART.md](./MEMORY_QUICKSTART.md) - Memory commands
