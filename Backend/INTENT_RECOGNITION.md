# Intent Recognition & Configuration Management

## Overview

The chatbot now uses an **Intent Recognition System** to detect configuration requests and route them to appropriate automation workflows. This replaces hardcoded regex patterns with a scalable, extensible architecture.

## Architecture

```
User Query
    ↓
Intent Recognizer (intent_recognizer.py)
    ↓
[Pattern Matching + Parameter Extraction]
    ↓
Intent Object {name, category, confidence, params}
    ↓
Backend Validation (views.py)
    ↓
[Check if feature enabled + requires approval]
    ↓
Execute or Request Approval
```

## Supported Intent Categories

### 1. VLAN Management (`vlan`)
- **`vlan_create`**: Create or configure VLANs
  - Patterns: "create vlan", "add vlan", "configure vlan"
  - Params: vlan_id, vlan_name
  - Status: ⚠️ Currently disabled

- **`vlan_delete`**: Delete VLAN
  - Patterns: "delete vlan", "remove vlan", "no vlan"
  - Params: vlan_id
  - Status: ⚠️ Currently disabled

- **`vlan_modify`**: Modify VLAN configuration
  - Patterns: "modify vlan", "change vlan", "update vlan"
  - Params: vlan_id, new_name
  - Status: ⚠️ Currently disabled

### 2. Interface Configuration (`interface`)
- **`interface_configure`**: Configure network interface
  - Patterns: "configure interface", "set up port", "enable interface"
  - Params: interface_name, action, description
  - Status: 🔜 Coming soon

- **`interface_assign_vlan`**: Assign interface to VLAN
  - Patterns: "assign interface to vlan", "access vlan", "trunk vlan"
  - Params: interface_name, vlan_id, mode
  - Status: 🔜 Coming soon

### 3. Routing Configuration (`routing`)
- **`route_add`**: Add static route
  - Patterns: "add route", "create route", "ip route"
  - Params: destination, next_hop
  - Status: 🔜 Coming soon

- **`route_delete`**: Delete static route
  - Patterns: "remove route", "delete route", "no ip route"
  - Params: destination
  - Status: 🔜 Coming soon

### 4. ACL Management (`acl`)
- **`acl_create`**: Create access control list
  - Patterns: "create acl", "add access list", "access-list"
  - Params: acl_number, acl_name
  - Status: 🔜 Coming soon

- **`acl_apply`**: Apply ACL to interface
  - Patterns: "apply acl", "attach acl to interface"
  - Params: acl_name, interface, direction
  - Status: 🔜 Coming soon

### 5. Device Management (`management`)
- **`device_backup`**: Backup device configuration
  - Patterns: "backup config", "save configuration", "copy running-config"
  - Params: none
  - Status: 🔜 Coming soon

- **`device_reboot`**: Reboot network device
  - Patterns: "reboot device", "restart switch", "reload"
  - Params: confirm
  - Status: 🔜 Coming soon

## How It Works

### Intent Recognition Flow

1. **User Query**: "create vlan 100 named engineering"

2. **Pattern Matching**:
   ```python
   recognizer = get_intent_recognizer()
   intent = recognizer.recognize(query)
   ```

3. **Intent Object**:
   ```python
   Intent(
       name='vlan_create',
       category='vlan',
       confidence=0.92,
       params={'vlan_id': '100', 'vlan_name': 'engineering'},
       requires_approval=True,
       description='Create or configure VLANs'
   )
   ```

4. **Backend Validation**:
   - Check if feature enabled (e.g., VLAN automation)
   - Check if approval required
   - Validate parameters
   - Execute or request approval

### Command Safety

Commands are categorized into three types:

#### 1. Read-Only (Always Allowed) ✅
```python
SAFE_READ_PREFIXES = (
    'show ', 'dir', 'display ', 'get ', 'list '
)
```
Examples:
- ✅ "show interfaces"
- ✅ "display vlan"
- ✅ "get running-config"

#### 2. Configuration (Requires Intent Recognition) ⚠️
```python
CONFIG_PREFIXES = (
    'configure ', 'config ', 'vlan ', 'interface ',
    'ip route', 'access-list ', 'no ', 'shutdown',
    'switchport ', 'name ', 'description '
)
```
Examples:
- ⚠️ "configure terminal" (requires intent)
- ⚠️ "vlan 100" (requires intent)
- ⚠️ "interface GigabitEthernet0/1" (requires intent)

#### 3. Dangerous (Always Blocked) ❌
```python
BLOCKED_SUBSTRINGS = (
    ' delete', ' erase', ' write ', ' format',
    ' reload', 'copy ', ' tftp', ' ftp ', 'scp '
)
```
Examples:
- ❌ "delete vlan.dat"
- ❌ "erase startup-config"
- ❌ "reload" (without proper intent)

## Adding New Automation Features

### Step 1: Define Intent Pattern

Edit `intent_recognizer.py`:

```python
'ospf_configure': {
    'category': 'routing',
    'patterns': [
        r'\b(configure|enable|setup)\s+ospf\b',
        r'\brouter\s+ospf\b',
    ],
    'requires_approval': True,
    'description': 'Configure OSPF routing protocol',
    'param_extractors': {
        'process_id': r'ospf\s+(\d+)',
        'router_id': r'router-id\s+([\d\.]+)',
        'network': r'network\s+([\d\.\/]+)',
        'area': r'area\s+(\d+)',
    }
}
```

### Step 2: Update Backend Handler

In `views.py`, add handler for the new intent:

```python
if intent.category == 'routing' and intent.name == 'ospf_configure':
    # Check if OSPF automation is enabled
    if not os.getenv("ENABLE_OSPF_AUTOMATION", "0") == "1":
        return Response({
            "error": "OSPF automation is not enabled",
            "intent": intent.name
        }, status=503)
    
    # Route to OSPF automation handler
    from netops_backend.ospf_agent import configure_ospf
    result = configure_ospf(
        device=resolved_device_dict,
        process_id=intent.params.get('process_id'),
        router_id=intent.params.get('router_id'),
        networks=intent.params.get('network')
    )
    return Response(result, status=200)
```

### Step 3: Enable Feature

In `.env`:
```bash
ENABLE_OSPF_AUTOMATION=1
```

### Step 4: Test

```bash
# Test intent recognition
python manage.py shell
>>> from chatbot.intent_recognizer import recognize_intent
>>> intent = recognize_intent("configure ospf 1 with router-id 1.1.1.1")
>>> print(intent.name, intent.params)
```

## Usage Examples

### Python API

```python
from chatbot.intent_recognizer import recognize_intent

# Recognize VLAN creation
intent = recognize_intent("create vlan 100 named engineering")
print(f"Intent: {intent.name}")  # vlan_create
print(f"Params: {intent.params}")  # {'vlan_id': '100', 'vlan_name': 'engineering'}

# Recognize interface configuration
intent = recognize_intent("configure interface GigabitEthernet0/1 description Uplink")
print(f"Intent: {intent.name}")  # interface_configure
print(f"Params: {intent.params}")  # {'interface_name': 'GigabitEthernet0/1', 'description': 'Uplink'}

# Recognize routing
intent = recognize_intent("add route to 10.0.0.0/8 via 192.168.1.1")
print(f"Intent: {intent.name}")  # route_add
print(f"Params: {intent.params}")  # {'destination': '10.0.0.0/8', 'next_hop': '192.168.1.1'}
```

### Management Command

```bash
# Test intent recognition
python manage.py shell
>>> from chatbot.intent_recognizer import get_intent_recognizer
>>> recognizer = get_intent_recognizer()

# View all categories
>>> print(recognizer.get_categories())
['acl', 'interface', 'management', 'routing', 'vlan']

# View intents by category
>>> print(recognizer.get_intents_by_category('vlan'))
['vlan_create', 'vlan_delete', 'vlan_modify']

# Test recognition
>>> intent = recognizer.recognize("delete vlan 50")
>>> print(f"{intent.name}: {intent.description}")
vlan_delete: Delete VLAN
```

## Configuration

### Environment Variables

```bash
# Feature Flags
ENABLE_VLAN_AUTOMATION=0          # VLAN management (currently disabled)
ENABLE_INTERFACE_AUTOMATION=0     # Interface configuration
ENABLE_ROUTING_AUTOMATION=0       # Routing configuration
ENABLE_ACL_AUTOMATION=0           # ACL management

# Approval Requirements
REQUIRE_VLAN_APPROVAL=1           # Require approval for VLAN changes
REQUIRE_INTERFACE_APPROVAL=1      # Require approval for interface changes
REQUIRE_ROUTING_APPROVAL=1        # Require approval for routing changes

# Intent Recognition
INTENT_MIN_CONFIDENCE=0.7         # Minimum confidence threshold
INTENT_STRICT_MODE=1              # Strict mode (block unrecognized intents)
```

## Testing

### Unit Tests

```python
# Test intent recognition
def test_vlan_create_intent():
    from chatbot.intent_recognizer import recognize_intent
    
    queries = [
        "create vlan 100",
        "add vlan 200 named test",
        "configure vlan 300"
    ]
    
    for query in queries:
        intent = recognize_intent(query)
        assert intent is not None
        assert intent.name == 'vlan_create'
        assert intent.category == 'vlan'
        assert 'vlan_id' in intent.params

# Test parameter extraction
def test_param_extraction():
    intent = recognize_intent("create vlan 100 named engineering")
    assert intent.params['vlan_id'] == '100'
    assert intent.params['vlan_name'] == 'engineering'
```

### Integration Tests

```bash
# Test via API
curl -X POST http://localhost:8000/api/nlp/network-command/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "create vlan 100 named test",
    "session_id": "test-123"
  }'

# Expected response (VLAN automation disabled):
{
  "error": "VLAN automation is currently disabled",
  "intent": "vlan_create",
  "description": "Create or configure VLANs",
  "session_id": "test-123"
}
```

## Roadmap

### Phase 1: Foundation ✅ (Current)
- ✅ Intent recognition system
- ✅ Pattern matching engine
- ✅ Parameter extraction
- ✅ Command safety validation
- ✅ Backend integration

### Phase 2: VLAN Automation 🔜 (Next)
- 🔜 Enable VLAN creation
- 🔜 VLAN modification
- 🔜 VLAN deletion
- 🔜 Frontend approval UI

### Phase 3: Interface Management 📅 (Planned)
- 📅 Interface configuration
- 📅 VLAN assignment
- 📅 Port descriptions
- 📅 Shutdown/no shutdown

### Phase 4: Advanced Features 📅 (Future)
- 📅 Routing configuration
- 📅 ACL management
- 📅 QoS policies
- 📅 Device backup/restore

## Benefits

### 1. Scalability
- Easy to add new automation features
- No hardcoded regex in frontend
- Centralized intent management

### 2. Safety
- Intent-based validation
- Approval workflows
- Dangerous operation blocking

### 3. Flexibility
- Pattern-based matching
- Parameter extraction
- Confidence scoring

### 4. Maintainability
- Single source of truth for intents
- Easy to modify patterns
- Clear separation of concerns

## Summary

The Intent Recognition System provides a scalable, extensible foundation for network automation:

- **✅ Replaces hardcoded regex** with configurable patterns
- **✅ Supports multiple categories** (VLAN, Interface, Routing, ACL, Management)
- **✅ Parameter extraction** from natural language
- **✅ Safety validation** (read-only, configuration, dangerous)
- **✅ Easy to extend** for future automation features

**Current Status:**
- Intent Recognition: ✅ Implemented
- VLAN Automation: ⚠️ Disabled (toggle visible but non-functional)
- Other Features: 🔜 Coming soon

**Next Steps:**
1. Enable VLAN automation
2. Implement frontend approval UI
3. Add interface configuration
4. Expand to routing and ACL management
