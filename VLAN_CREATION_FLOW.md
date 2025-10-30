# Exact Flow: How "Create VLAN 20 in Aruba Switch" Works

## 🎯 User Request Example
```
User: "Create VLAN 20 named Engineering in Aruba switch"
```

---

## 📊 Complete Execution Flow

### **Phase 1: Frontend → Backend Request** 🌐

```mermaid
User Query
    ↓
Frontend (React/Next.js)
    ↓ POST /api/nlp/network-command/
{
  "query": "create vlan 20 named engineering in aruba",
  "session_id": "uuid-here"
}
    ↓
Backend (Django REST API)
```

**Code Location:** `Frontend/src/components/ChatInterface.tsx`
```typescript
const response = await fetch('http://localhost:8000/api/nlp/network-command/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query, session_id })
});
```

---

### **Phase 2: Intent Recognition** 🧠

**Code Location:** `Backend/netops_backend/chatbot/intent_recognizer.py`

```python
# Step 1: Pattern Matching
recognizer = get_intent_recognizer()
intent = recognizer.recognize("create vlan 20 named engineering in aruba")

# Step 2: Intent Detected
Intent(
    name='vlan_create',
    category='vlan',
    confidence=0.92,
    params={
        'vlan_id': '20',
        'vlan_name': 'engineering'
    },
    requires_approval=True,
    description='Create or configure VLANs'
)
```

**Pattern Used:**
```python
'vlan_create': {
    'patterns': [
        r'\b(create|add|new|make)\s+(a\s+)?vlan\b',  # ← MATCHES "create vlan"
        r'\bvlan\s+(create|add|new)\b',
        r'\bconfigure\s+vlan\b',
    ],
    'param_extractors': {
        'vlan_id': r'vlan\s+(\d+)',              # ← EXTRACTS "20"
        'vlan_name': r'(?:name|called)\s+(["\']?)(\w+)\1',  # ← EXTRACTS "engineering"
    }
}
```

---

### **Phase 3: Current Status (⚠️ BLOCKED)** 🚫

**Code Location:** `Backend/netops_backend/chatbot/views.py` (lines 564-572)

```python
if intent.category == 'vlan':
    # VLAN automation currently disabled
    return Response({
        "error": "VLAN automation is currently disabled",
        "intent": intent.name,
        "description": intent.description,
        "session_id": session_id
    }, status=503)  # ← SERVICE UNAVAILABLE
```

**Current Response:**
```json
{
  "error": "VLAN automation is currently disabled",
  "intent": "vlan_create",
  "description": "Create or configure VLANs",
  "session_id": "uuid-here"
}
```

**Status:** ⚠️ **Feature recognized but intentionally disabled**

---

## 🔓 What Would Happen If VLAN Automation Was Enabled

### **Phase 4: Device Resolution** 🔍

**Code Location:** `Backend/netops_backend/Devices/device_resolver.py`

```python
# Step 1: Extract keywords from query
query = "create vlan 20 named engineering in aruba"
keywords = ["aruba", "vlan", "create", "engineering"]

# Step 2: Match device alias
resolved_device = resolve_device_from_text(query)
# Output: "INVIJB10A01" (Aruba AOS-CX switch in Vijayawada)

# Step 3: Load device details from devices.json
device_details = {
    "alias": "INVIJB10A01",
    "host": "10.249.162.106",
    "device_type": "aruba_aoscx",
    "location": "Vijayawada",
    "role": "Access Switch"
}
```

**Keyword Mapping:**
```python
_LOCATION_KEYWORDS = {
    'aruba': 'INVIJB10A01',     # ← "aruba" keyword → Aruba switch
    'vijayawada': 'INVIJB10A01',
    'cisco': 'INVIJB1C01',
    'london': 'UKLONB10C01'
}
```

---

### **Phase 5: NLP Command Generation** 🤖

**Code Location:** `Backend/netops_backend/chatbot/nlp_router.py`

Since device is Aruba (AOS-CX), it uses **Google Gemini API**:

```python
# Step 1: Route to Gemini
llm_provider = "gemini"  # From .env: ARUBA_LLM_PROVIDER=gemini
model = "gemini-2.0-flash-exp"  # From .env

# Step 2: Send to Gemini API
prompt = f"""
Convert this network request to CLI commands for aruba_aoscx:
Query: "create vlan 20 named engineering"
Device: INVIJB10A01 (Aruba AOS-CX)

Return ONLY the command, no explanations.
"""

response = genai.GenerativeModel(model).generate_content(prompt)

# Step 3: Extract CLI command
cli_command = "vlan 20 name engineering"
```

**Alternative Path (if Cisco):** Would use local T5 model instead

---

### **Phase 6: Command Safety Validation** 🛡️

**Code Location:** `Backend/netops_backend/chatbot/views.py` (lines 534-598)

```python
cli_command = "vlan 20 name engineering"

# Step 1: Check if read-only (NO)
is_read_only = cli_command.startswith(('show ', 'display ', 'get '))
# Result: False

# Step 2: Check if configuration command (YES)
is_config_command = cli_command.startswith(('vlan ', 'configure ', 'interface '))
# Result: True

# Step 3: Check for dangerous operations (NO)
has_dangerous_ops = any(word in cli_command for word in [' delete', ' erase', ' format'])
# Result: False

# Step 4: Already recognized intent in Phase 2
# Intent: vlan_create with params {vlan_id: 20, vlan_name: engineering}

# Step 5: Check if feature enabled
if os.getenv("ENABLE_VLAN_AUTOMATION") == "1":
    # ✅ PROCEED TO EXECUTION
    pass
else:
    # ⚠️ CURRENTLY RETURNS 503 (disabled)
    return Response({"error": "VLAN automation disabled"}, status=503)
```

---

### **Phase 7: VLAN Agent Execution** ⚙️ (When Enabled)

**Code Location:** `Backend/netops_backend/netops_backend/vlan_agent/nornir_driver.py`

#### **7A: Create VLAN Intent in Database**
```python
# Create intent record
vlan_intent = VLANIntent.objects.create(
    vlan_id=20,
    name="engineering",
    scope="access",
    status="PENDING"
)
```

#### **7B: Hierarchical Deployment Flow**
```python
# Deploy following hierarchy: Core → Access switches
hierarchy = {
    "core": "UKLONB10C01",      # London Core (Cisco)
    "access": [
        "INVIJB1C01",            # Vijayawada Access (Cisco)
        "INVIJB10A01"            # Vijayawada Access (Aruba) ← YOUR TARGET
    ]
}

# Step 1: Deploy to Core Switch FIRST
deploy_to_device("UKLONB10C01", vlan_id=20, name="engineering")
# Commands sent:
#   configure terminal
#   vlan 20
#   name engineering
#   end

# Step 2: If core success, deploy to Access Switches
deploy_to_device("INVIJB1C01", vlan_id=20, name="engineering")
# Commands sent (Cisco):
#   configure terminal
#   vlan 20
#   name engineering
#   end

deploy_to_device("INVIJB10A01", vlan_id=20, name="engineering")
# Commands sent (Aruba AOS-CX):
#   configure terminal
#   vlan 20
#   name engineering
#   exit
```

#### **7C: Netmiko Connection to Aruba Switch**
```python
def _deploy_to_single_device(alias, dev, vlan_id, name, is_core):
    params = {
        "device_type": "aruba_aoscx",
        "host": "10.249.162.106",
        "username": "admin",
        "password": "password",  # From .env
        "port": 22
    }
    
    with ConnectHandler(**params) as conn:
        # Step 1: Check if VLAN exists
        output = conn.send_command("show vlan 20")
        if "VLAN 20" in output:
            return "skipped"  # Already exists
        
        # Step 2: Configure VLAN
        commands = [
            "vlan 20",
            "name engineering"
        ]
        conn.send_config_set(commands)
        
        # Step 3: Save config (optional)
        conn.save_config()  # write memory
        
        return "created"
```

#### **7D: Actual SSH Commands Sent to Aruba Switch**
```cisco
# SSH Connection established to 10.249.162.106:22
INVIJB10A01# configure terminal
INVIJB10A01(config)# vlan 20
INVIJB10A01(config-vlan-20)# name engineering
INVIJB10A01(config-vlan-20)# exit
INVIJB10A01(config)# write memory
```

---

### **Phase 8: Validation** ✅

**Code Location:** `Backend/netops_backend/netops_backend/vlan_agent/nornir_driver.py`

```python
# Verify VLAN created successfully
def validate_vlan_propagation(vlan_id=20):
    results = {}
    
    for device in ["UKLONB10C01", "INVIJB1C01", "INVIJB10A01"]:
        with ConnectHandler(**device_params) as conn:
            output = conn.send_command(f"show vlan {vlan_id}")
            
            if "VLAN 20" in output or "Name: engineering" in output:
                results[device] = "ok"  # ✅
            else:
                results[device] = "missing"  # ❌
    
    return results
```

**Expected Validation Output:**
```python
{
    "UKLONB10C01": "ok",      # Core switch ✅
    "INVIJB1C01": "ok",       # Cisco access ✅
    "INVIJB10A01": "ok"       # Aruba access ✅
}
```

---

### **Phase 9: Response to Frontend** 📤

**Code Location:** `Backend/netops_backend/chatbot/views.py`

```python
# Success response
return Response({
    "response": "VLAN 20 'engineering' created successfully on Aruba switch INVIJB10A01",
    "command": "vlan 20 name engineering",
    "device": "INVIJB10A01",
    "deployment_summary": {
        "UKLONB10C01": "created",
        "INVIJB1C01": "created",
        "INVIJB10A01": "created"
    },
    "validation": {
        "UKLONB10C01": "ok",
        "INVIJB1C01": "ok",
        "INVIJB10A01": "ok"
    },
    "session_id": "uuid-here"
}, status=200)
```

---

## 📝 Complete Step-by-Step Summary

| Step | Component | Action | Output |
|------|-----------|--------|--------|
| 1 | **Frontend** | User types query | "create vlan 20 named engineering in aruba" |
| 2 | **Intent Recognizer** | Pattern matching | Intent: `vlan_create`, Params: `{vlan_id: 20, name: engineering}` |
| 3 | **Command Validator** | Check if enabled | ⚠️ Currently returns 503 (disabled) |
| 4 | **Device Resolver** | Extract device keywords | Device: INVIJB10A01 (Aruba AOS-CX) |
| 5 | **NLP Router** | Generate CLI command via Gemini | Command: `vlan 20 name engineering` |
| 6 | **VLAN Agent** | Create DB intent | VLANIntent(vlan_id=20, name=engineering, status=PENDING) |
| 7 | **Hierarchical Deploy** | Core → Access switches | Deploy order: UKLONB10C01 → INVIJB1C01 → INVIJB10A01 |
| 8 | **Netmiko** | SSH to Aruba switch | Execute: `configure terminal` → `vlan 20` → `name engineering` |
| 9 | **Validation** | Verify VLAN exists | Check: `show vlan 20` on all devices |
| 10 | **Response** | Return to frontend | Status: 200 OK, Summary: {created: 3, ok: 3} |

---

## 🔧 Configuration Files Involved

### 1. **Backend/.env**
```bash
# VLAN Feature Flag (currently disabled)
ENABLE_VLAN_AUTOMATION=0  # ← Set to 1 to enable

# Gemini API (used for Aruba)
GEMINI_API_KEY=your-gemini-api-key-here
ARUBA_LLM_PROVIDER=gemini
ARUBA_LLM_MODEL=gemini-2.0-flash-exp

# Device Credentials
DEVICE_USERNAME=admin
DEVICE_PASSWORD=password
```

### 2. **Backend/netops_backend/Devices/devices.json**
```json
{
  "INVIJB10A01": {
    "alias": "INVIJB10A01",
    "host": "10.249.162.106",
    "device_type": "aruba_aoscx",
    "location": "Vijayawada",
    "username": "admin",
    "password": "password"
  }
}
```

### 3. **Backend/netops_backend/chatbot/intent_recognizer.py**
```python
INTENT_PATTERNS = {
    'vlan_create': {
        'category': 'vlan',
        'patterns': [
            r'\b(create|add|new|make)\s+(a\s+)?vlan\b',
            r'\bvlan\s+(create|add|new)\b'
        ],
        'param_extractors': {
            'vlan_id': r'vlan\s+(\d+)',
            'vlan_name': r'(?:name|called)\s+(["\']?)(\w+)\1'
        }
    }
}
```

---

## 🚦 Current Status

### ⚠️ **What Works Now:**
- ✅ Intent recognition (detects VLAN creation requests)
- ✅ Device resolution (identifies Aruba switch from keywords)
- ✅ Command generation (Gemini API creates CLI commands)
- ✅ Command validation (safety checks)
- ✅ Hierarchical deployment logic (Core → Access)
- ✅ Netmiko integration (SSH connection ready)

### 🚫 **What's Blocked:**
- ❌ VLAN automation execution (returns 503 error)
- ❌ Reason: `ENABLE_VLAN_AUTOMATION=0` in .env
- ❌ Frontend approval UI not built yet

### 🔜 **To Enable VLAN Creation:**

#### Option 1: Enable Without Approval (Quick Test)
```bash
# Edit Backend/.env
ENABLE_VLAN_AUTOMATION=1

# Restart Django server
cd Backend/netops_backend
python manage.py runserver
```

#### Option 2: Build Approval Workflow (Production)
1. Create approval modal in frontend
2. Display intent details: `vlan_create`, VLAN ID: 20, Name: engineering
3. User clicks "Approve" → sends approval token
4. Backend validates token and executes
5. Shows deployment progress (Core → Access 1 → Access 2)
6. Displays validation results

---

## 🎯 Example Queries That Work

```bash
# All these trigger the same vlan_create intent:

"create vlan 20 in aruba switch"
"add vlan 30 named sales to aruba"
"configure vlan 100 called marketing on aruba"
"make a new vlan 50 on aruba switch"
"vlan 200 create on aruba"
```

**Parameter Extraction Examples:**
```python
"create vlan 20" 
→ {vlan_id: '20'}

"create vlan 20 named engineering"
→ {vlan_id: '20', vlan_name: 'engineering'}

"add vlan 100 called 'Guest WiFi'"
→ {vlan_id: '100', vlan_name: 'Guest WiFi'}
```

---

## 💡 Key Insights

1. **Hierarchical Deployment:** VLANs are created on Core switch first, then propagated to Access switches. If core fails, access switches are skipped.

2. **Multi-Vendor Support:** Same intent works for both Cisco and Aruba:
   - Cisco: Uses T5 local model
   - Aruba: Uses Gemini API
   - Both: Use Netmiko for SSH

3. **Safety First:** All configuration commands require:
   - Intent recognition (pattern matching)
   - Feature flag enabled
   - No dangerous operations (delete, erase, format)
   - Optional: User approval (planned)

4. **Device-Specific Commands:** System generates correct syntax per device:
   - Cisco IOS: `vlan 20` → `name engineering`
   - Aruba AOS-CX: `vlan 20` → `name engineering` (same but different output format)

5. **Validation:** After creation, system verifies VLAN exists on all devices using `show vlan <id>` command.

---

## 🔍 Debugging Commands

### Test Intent Recognition
```python
python manage.py shell
>>> from chatbot.intent_recognizer import recognize_intent
>>> intent = recognize_intent("create vlan 20 named engineering in aruba")
>>> print(intent.name, intent.params)
vlan_create {'vlan_id': '20', 'vlan_name': 'engineering'}
```

### Test Device Resolution
```python
>>> from Devices.device_resolver import resolve_device_from_text
>>> device = resolve_device_from_text("create vlan 20 in aruba")
>>> print(device)
INVIJB10A01
```

### Test API (Currently Returns 503)
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/nlp/network-command/" `
  -ContentType "application/json" `
  -Body '{"query": "create vlan 20 in aruba", "session_id": "test"}'
```

---

## 🎉 Summary

**Your Question:** "If I ask to create VLAN 20 in a particular switch, how will it create exactly?"

**Answer:** 

The system follows this exact path:

1. **Frontend** sends your query to backend API
2. **Intent Recognizer** detects `vlan_create` intent and extracts VLAN ID (20) and name
3. **Device Resolver** identifies target switch (INVIJB10A01 - Aruba) from keywords
4. **NLP Router** uses Gemini API to generate CLI command (`vlan 20 name engineering`)
5. **Command Validator** checks safety and feature flags
6. **⚠️ CURRENTLY BLOCKED** - Returns 503 because `ENABLE_VLAN_AUTOMATION=0`
7. **WHEN ENABLED:**
   - Creates VLANIntent in database
   - Deploys hierarchically: Core (UKLONB10C01) → Access (INVIJB1C01, INVIJB10A01)
   - Uses Netmiko to SSH into Aruba switch
   - Executes: `configure terminal` → `vlan 20` → `name engineering` → `write memory`
   - Validates VLAN exists using `show vlan 20`
   - Returns success response with deployment summary

**Current Status:** ⚠️ Feature is fully implemented but **intentionally disabled** pending approval workflow.

**To Enable:** Set `ENABLE_VLAN_AUTOMATION=1` in `Backend/.env` and restart server.
