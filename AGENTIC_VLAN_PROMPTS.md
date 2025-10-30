# Agentic VLAN Creation with Vendor-Specific Prompts

## 🎯 Overview

Traditional VLAN automation uses **hardcoded commands** that work for simple cases but don't scale across different vendors. **Agentic VLAN Creation** uses AI/LLM with **vendor-specific prompts** to generate complete, multi-command configuration sequences that handle the nuances of each network vendor's syntax.

---

## 🤔 Why Vendor-Specific Prompts?

### The Problem with Generic Prompts

**Generic Prompt (Current Default):**
```python
"You are a precise network CLI assistant. Given a natural language request, 
output exactly one Cisco IOS show command that best answers it. 
Return ONLY the command text, with no quotes or explanations."
```

**Issues:**
1. ❌ Only generates **single commands** (not multi-command workflows)
2. ❌ Optimized for **Cisco IOS** only
3. ❌ Doesn't handle **configuration mode transitions**
4. ❌ Ignores vendor-specific **command syntax differences**
5. ❌ Can't generate **proper command sequences** (configure → create → save → exit)

### Example: Creating VLAN 100 Named "Engineering"

#### ❌ Generic Prompt Output (Incorrect):
```cisco
vlan 100 name Engineering
```
**Problem:** Missing configuration mode, missing save, incomplete workflow

#### ✅ Cisco IOS-Specific Prompt Output (Correct):
```cisco
configure terminal
vlan 100
name Engineering
exit
write memory
end
```
**Result:** Complete workflow with mode transitions and config save

#### ✅ Aruba AOS-CX-Specific Prompt Output (Correct):
```cisco
configure terminal
vlan 100
name Engineering
exit
write memory
end
```
**Result:** Aruba-specific syntax with proper commands

#### ✅ Juniper JunOS-Specific Prompt Output (Correct):
```junos
configure
set vlans Engineering vlan-id 100
commit
exit
```
**Result:** JunOS hierarchical configuration style

---

## 📊 Comparison: Hardcoded vs Agentic

| Aspect | Hardcoded Commands | Agentic (LLM + Vendor Prompts) |
|--------|-------------------|--------------------------------|
| **Vendor Support** | Limited to pre-coded vendors | Supports any vendor with prompt |
| **Command Sequences** | Single or simple sequences | Complete multi-command workflows |
| **Configuration Modes** | Must manually code | LLM handles mode transitions |
| **Flexibility** | Rigid, requires code changes | Adapts to natural language |
| **Maintenance** | High (update code for each vendor) | Low (update prompts as text) |
| **New Features** | Requires code changes | Add to prompt description |
| **Error Handling** | Limited to coded scenarios | LLM can adapt to variations |
| **Scalability** | Poor (N vendors = N code blocks) | Excellent (N vendors = N prompts) |

---

## 🏗️ Architecture

### System Components

```
User Query: "Create VLAN 100 named Engineering in Aruba switch"
    ↓
[Intent Recognizer]
    ↓ Intent: vlan_create, Params: {vlan_id: 100, name: "Engineering"}
    ↓
[Device Resolver]
    ↓ Device: INVIJB10A01 (Aruba AOS-CX)
    ↓
[Vendor Prompt Selector]
    ↓ Select: ARUBA_AOSCX_VLAN_SYSTEM_PROMPT
    ↓
[LLM Provider (Gemini/OpenAI/Local)]
    ↓ Generate: Multi-command sequence
    ↓
configure terminal
vlan 100
name Engineering
exit
write memory
end
    ↓
[Netmiko Executor]
    ↓ Execute commands on device
    ↓
[Validation]
    ↓ Verify: "show vlan 100"
    ↓
✅ Success: VLAN 100 created
```

---

## 📝 Vendor-Specific Prompt Examples

### 1. Cisco IOS/IOS-XE

**Prompt Characteristics:**
- Uses `configure terminal` to enter config mode
- Creates VLAN with `vlan <id>` then `name <name>`
- Saves with `write memory`
- Exits with `end`

**Example Prompt Excerpt:**
```python
CISCO_IOS_VLAN_SYSTEM_PROMPT = """You are an expert Cisco IOS/IOS-XE network engineer.

VLAN CONFIGURATION SYNTAX:
- Enter config mode: configure terminal
- Create VLAN: vlan <vlan-id>
- Name VLAN: name <vlan-name>
- Exit VLAN config: exit
- Save configuration: write memory
- Exit config mode: end

EXAMPLE:
Input: "Create VLAN 100 named Engineering"
Output:
configure terminal
vlan 100
name Engineering
exit
write memory
end

IMPORTANT: Return ONLY executable commands, no explanations."""
```

**Generated Output:**
```cisco
configure terminal
vlan 100
name Engineering
exit
write memory
end
```

---

### 2. Aruba AOS-CX

**Prompt Characteristics:**
- Similar to Cisco but with Aruba-specific features
- Supports descriptions within VLAN context
- Uses same mode transitions
- Different validation commands

**Example Prompt Excerpt:**
```python
ARUBA_AOSCX_VLAN_SYSTEM_PROMPT = """You are an expert Aruba AOS-CX network engineer.

ARUBA AOS-CX VLAN SYNTAX:
- Enter config mode: configure terminal
- Create VLAN: vlan <vlan-id>
- Name VLAN: name <vlan-name>
- Optional description: description <text>
- Exit VLAN config: exit
- Save configuration: write memory

EXAMPLE:
Input: "Add VLAN 200 with description 'Sales Department'"
Output:
configure terminal
vlan 200
name Sales
description Sales Department
exit
write memory
end
"""
```

**Generated Output:**
```cisco
configure terminal
vlan 200
name Sales
description Sales Department
exit
write memory
end
```

---

### 3. Juniper JunOS

**Prompt Characteristics:**
- Uses `configure` (not `configure terminal`)
- Hierarchical `set` command syntax
- VLAN name comes **before** vlan-id
- Requires `commit` (not `write memory`)

**Example Prompt Excerpt:**
```python
JUNIPER_JUNOS_VLAN_PROMPT = """You are an expert Juniper JunOS network engineer.

JUNOS VLAN SYNTAX:
- Enter config mode: configure
- Create VLAN: set vlans <vlan-name> vlan-id <id>
- Commit changes: commit
- Exit config: exit

EXAMPLE:
Input: "Create VLAN 100 named Engineering"
Output:
configure
set vlans Engineering vlan-id 100
commit
exit
"""
```

**Generated Output:**
```junos
configure
set vlans Engineering vlan-id 100
commit
exit
```

**Key Differences:**
- ✅ Name before ID: `set vlans Engineering vlan-id 100`
- ✅ Uses `commit` instead of `write memory`
- ✅ No separate VLAN config mode

---

### 4. Aruba ProVision (AOS-Switch)

**Prompt Characteristics:**
- **No** `configure terminal` needed (always in config mode)
- VLAN names use **QUOTES**
- Can assign ports in same context
- Simpler syntax than Cisco

**Example Prompt Excerpt:**
```python
ARUBA_AOS_SWITCH_VLAN_PROMPT = """You are an expert Aruba ProVision switch engineer.

ARUBA PROVISION VLAN SYNTAX:
- Create VLAN: vlan <vlan-id>
- Name VLAN: name "<vlan-name>"  ← QUOTES REQUIRED
- Exit VLAN config: exit
- Save: write memory

EXAMPLE:
Input: "Create VLAN 100 named Engineering"
Output:
vlan 100
name "Engineering"
exit
write memory
"""
```

**Generated Output:**
```cisco
vlan 100
name "Engineering"
exit
write memory
```

**Key Differences:**
- ❌ No `configure terminal` command
- ✅ VLAN names **must be quoted**
- ✅ Simpler command structure

---

### 5. HPE Comware

**Prompt Characteristics:**
- Uses `system-view` instead of `configure terminal`
- Uses `quit` instead of `exit`
- Uses `save` instead of `write memory`

**Example Prompt Excerpt:**
```python
HPE_COMWARE_VLAN_PROMPT = """You are an expert HPE/H3C Comware network engineer.

COMWARE VLAN SYNTAX:
- Enter system view: system-view
- Create VLAN: vlan <vlan-id>
- Name VLAN: name <vlan-name>
- Exit VLAN view: quit
- Save: save

EXAMPLE:
Input: "Create VLAN 100 named Engineering"
Output:
system-view
vlan 100
name Engineering
quit
save
quit
"""
```

**Generated Output:**
```comware
system-view
vlan 100
name Engineering
quit
save
quit
```

**Key Differences:**
- ✅ `system-view` not `configure terminal`
- ✅ `quit` not `exit`
- ✅ `save` not `write memory`

---

## 🔧 Implementation Details

### File Structure

```
Backend/netops_backend/netops_backend/vlan_agent/
├── prompts.py                  ← NEW: Vendor-specific prompts
├── nornir_driver.py           ← UPDATED: Uses prompts
├── models.py                   ← VLANIntent model
├── utils.py                    ← Helper functions
└── views.py                    ← API endpoints
```

### Key Functions

#### 1. `get_vlan_creation_prompt(device_type: str) -> str`

Maps device type to appropriate vendor prompt.

```python
device_type = "aruba_aoscx"
prompt = get_vlan_creation_prompt(device_type)
# Returns: ARUBA_AOSCX_VLAN_SYSTEM_PROMPT
```

**Supported Device Types:**
- `cisco_ios`, `cisco_xe`, `cisco_nxos` → Cisco prompt
- `aruba_aoscx`, `aoscx` → Aruba AOS-CX prompt
- `aruba_os`, `aruba_procurve` → Aruba ProVision prompt
- `juniper`, `junos` → Juniper JunOS prompt
- `hp_comware`, `hpe_comware`, `h3c` → HPE Comware prompt

#### 2. `format_vlan_query(vlan_id: int, vlan_name: str, action: str) -> str`

Formats natural language query for LLM.

```python
query = format_vlan_query(100, "Engineering", "create")
# Returns: "Create VLAN 100 named Engineering"
```

#### 3. `_configure_vlan_agentic(connection, vlan_id, name, device_type, use_llm)`

Executes VLAN creation using LLM-generated commands.

```python
result = _configure_vlan_agentic(
    connection=netmiko_conn,
    vlan_id=100,
    name="Engineering",
    device_type="aruba_aoscx",
    use_llm=True
)

# Returns:
{
    "status": "success",
    "vlan_id": 100,
    "vlan_name": "Engineering",
    "device_type": "aruba_aoscx",
    "commands": [
        "configure terminal",
        "vlan 100",
        "name Engineering",
        "exit",
        "write memory",
        "end"
    ],
    "output": "...",
    "method": "agentic",
    "config_saved": True
}
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# ==========================================
# VLAN AUTOMATION CONFIGURATION
# ==========================================

# Enable/Disable VLAN Automation
ENABLE_VLAN_AUTOMATION=0  # Set to 1 to enable

# Agentic Mode (Use LLM with vendor prompts)
# 1 = Agentic (LLM-generated multi-command sequences)
# 0 = Traditional (hardcoded commands)
ENABLE_AGENTIC_VLAN_CREATION=1

# Approval Requirement
REQUIRE_VLAN_APPROVAL=1

# ==========================================
# LLM PROVIDER CONFIGURATION
# ==========================================

# Aruba devices use Gemini API
ARUBA_LLM_PROVIDER=gemini
ARUBA_LLM_MODEL=gemini-2.0-flash-exp
GEMINI_API_KEY=your-api-key-here

# Cisco devices use local T5 model (no API key)
CISCO_LLM_PROVIDER=local
```

---

## 🚀 Usage Examples

### Example 1: Create VLAN on Cisco Switch

**User Query:**
```
"Create VLAN 100 named Engineering on Cisco switch"
```

**Flow:**
1. Intent: `vlan_create`, Params: `{vlan_id: 100, name: "Engineering"}`
2. Device: INVIJB1C01 (Cisco IOS)
3. Prompt: `CISCO_IOS_VLAN_SYSTEM_PROMPT`
4. LLM Provider: Local T5 model
5. Generated Commands:
   ```cisco
   configure terminal
   vlan 100
   name Engineering
   exit
   write memory
   end
   ```
6. Execution: Netmiko sends commands via SSH
7. Validation: `show vlan id 100`
8. Result: ✅ VLAN 100 created

---

### Example 2: Create VLAN on Aruba Switch

**User Query:**
```
"Add VLAN 200 called Sales on Aruba switch"
```

**Flow:**
1. Intent: `vlan_create`, Params: `{vlan_id: 200, name: "Sales"}`
2. Device: INVIJB10A01 (Aruba AOS-CX)
3. Prompt: `ARUBA_AOSCX_VLAN_SYSTEM_PROMPT`
4. LLM Provider: Google Gemini API
5. Generated Commands:
   ```cisco
   configure terminal
   vlan 200
   name Sales
   exit
   write memory
   end
   ```
6. Execution: Netmiko sends commands via SSH
7. Validation: `show vlan 200`
8. Result: ✅ VLAN 200 created

---

### Example 3: Create Multiple VLANs

**User Query:**
```
"Create VLANs 10, 20, and 30 named Data, Voice, and Video on Cisco"
```

**Flow:**
1. Intent: `vlan_create` (multiple)
2. Device: INVIJB1C01 (Cisco IOS)
3. Prompt: `CISCO_IOS_VLAN_SYSTEM_PROMPT`
4. Generated Commands:
   ```cisco
   configure terminal
   vlan 10
   name Data
   exit
   vlan 20
   name Voice
   exit
   vlan 30
   name Video
   exit
   write memory
   end
   ```
5. Result: ✅ 3 VLANs created in single workflow

---

## 📊 Comparison Table: Commands by Vendor

| Operation | Cisco IOS | Aruba AOS-CX | Aruba ProVision | Juniper JunOS | HPE Comware |
|-----------|-----------|--------------|-----------------|---------------|-------------|
| **Enter Config** | `configure terminal` | `configure terminal` | *(none)* | `configure` | `system-view` |
| **Create VLAN** | `vlan 100` | `vlan 100` | `vlan 100` | `set vlans Eng vlan-id 100` | `vlan 100` |
| **Name VLAN** | `name Engineering` | `name Engineering` | `name "Engineering"` | *(in create command)* | `name Engineering` |
| **Description** | *(in interface vlan)* | `description <text>` | *(not supported)* | `set vlans Eng description <text>` | `description <text>` |
| **Exit Context** | `exit` | `exit` | `exit` | *(none)* | `quit` |
| **Save Config** | `write memory` | `write memory` | `write memory` | `commit` | `save` |
| **Exit Config** | `end` | `end` | *(none)* | `exit` | `quit` |

---

## ✅ Benefits of Agentic Approach

### 1. **Multi-Vendor Support**
- ✅ One system handles Cisco, Aruba, Juniper, HPE, etc.
- ✅ Easy to add new vendors (just add prompt)
- ✅ No code changes needed for new vendors

### 2. **Complete Workflows**
- ✅ Handles configuration mode transitions
- ✅ Includes save commands automatically
- ✅ Proper exit sequences

### 3. **Natural Language Flexibility**
- ✅ "Create VLAN 100" → works
- ✅ "Add VLAN 100 named Eng" → works
- ✅ "Configure VLAN 100 called Engineering with description" → works

### 4. **Maintainability**
- ✅ Prompts are text (easy to edit)
- ✅ No code recompilation needed
- ✅ Version control for prompts

### 5. **Scalability**
- ✅ Adding new operations = adding new prompts
- ✅ Same architecture for interfaces, routing, ACLs, etc.
- ✅ Extensible to any network operation

---

## 🧪 Testing

### Test Agentic Mode

```bash
# Enable agentic mode
# Edit Backend/.env:
ENABLE_AGENTIC_VLAN_CREATION=1
ENABLE_VLAN_AUTOMATION=1

# Restart server
cd Backend/netops_backend
python manage.py runserver
```

### Test API Request

```powershell
# Test VLAN creation
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/nlp/network-command/" `
  -ContentType "application/json" `
  -Body '{"query": "create vlan 100 named test on aruba", "session_id": "test"}'
```

### Expected Response (Agentic Mode)

```json
{
  "response": "VLAN 100 'test' created successfully",
  "device": "INVIJB10A01",
  "deployment_summary": {
    "UKLONB10C01": "created",
    "INVIJB1C01": "created",
    "INVIJB10A01": "created"
  },
  "agentic_details": {
    "method": "agentic",
    "llm_provider": "gemini",
    "commands_generated": [
      "configure terminal",
      "vlan 100",
      "name test",
      "exit",
      "write memory",
      "end"
    ]
  },
  "session_id": "test"
}
```

---

## 🔍 Debugging

### View Generated Commands

```python
# Python shell
python manage.py shell

>>> from netops_backend.vlan_agent.prompts import get_vlan_creation_prompt, format_vlan_query
>>> from netops_backend.nlp_router import predict_cli_provider

# Get Cisco prompt
>>> cisco_prompt = get_vlan_creation_prompt('cisco_ios')
>>> query = format_vlan_query(100, "Engineering", "create")
>>> print(query)
Create VLAN 100 named Engineering

# Generate commands
>>> commands = predict_cli_provider(query, provider='local', system_prompt=cisco_prompt)
>>> print(commands)
configure terminal
vlan 100
name Engineering
exit
write memory
end
```

---

## 📚 Summary

### Traditional (Hardcoded)
```python
# Code: Hard to maintain, limited vendors
if "cisco" in device_type:
    cfg = [f"vlan {vlan_id}", f"name {name}"]
elif "aruba_aoscx" in device_type:
    cfg = [f"vlan {vlan_id}", f"name {name}"]
# ... repeat for each vendor
```

### Agentic (LLM + Vendor Prompts)
```python
# Flexible, scalable, vendor-agnostic
prompt = get_vlan_creation_prompt(device_type)  # Auto-selects vendor prompt
query = format_vlan_query(vlan_id, name, "create")
commands = predict_cli_provider(query, system_prompt=prompt)
# LLM generates complete multi-command workflow
```

**Key Advantages:**
- ✅ **Multi-vendor support** without vendor-specific code
- ✅ **Complete command sequences** with mode transitions
- ✅ **Easy to maintain** (edit prompts, not code)
- ✅ **Scalable** to any network operation
- ✅ **Natural language** interface

**Result:** One system that works for Cisco, Aruba, Juniper, HPE, and any future vendors!
