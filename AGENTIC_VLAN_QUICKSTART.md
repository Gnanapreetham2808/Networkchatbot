# Agentic VLAN Creation - Quick Reference

## 🎯 What Changed?

### Before (Hardcoded):
```python
# Single command per vendor
if "cisco" in device_type:
    cfg = [f"vlan {vlan_id}", f"name {name}"]
```
- ❌ Limited to hardcoded vendors
- ❌ Single commands only
- ❌ No configuration mode handling
- ❌ Hard to add new vendors

### After (Agentic):
```python
# LLM generates complete workflows
prompt = get_vlan_creation_prompt(device_type)
commands = predict_cli_provider(query, system_prompt=prompt)
```
- ✅ Multi-vendor support (Cisco, Aruba, Juniper, HPE, etc.)
- ✅ Complete command sequences with mode transitions
- ✅ Easy to add vendors (just add prompt)
- ✅ Scalable to any operation

---

## 📁 New Files

### `Backend/netops_backend/netops_backend/vlan_agent/prompts.py` (NEW)
- **520 lines** of vendor-specific prompts
- **5 vendors supported:** Cisco IOS, Aruba AOS-CX, Aruba ProVision, Juniper JunOS, HPE Comware
- **Helper functions:** `get_vlan_creation_prompt()`, `format_vlan_query()`, etc.

### `Backend/netops_backend/netops_backend/vlan_agent/nornir_driver.py` (UPDATED)
- **Added:** `_configure_vlan_agentic()` function (120+ lines)
- **Updated:** `_deploy_to_single_device()` to use agentic mode
- **Imports:** prompts module functions

### `Backend/.env` (UPDATED)
- **Added:** `ENABLE_AGENTIC_VLAN_CREATION=1`
- **Added:** Configuration section for VLAN automation

---

## ⚙️ Configuration

### Enable Agentic Mode

Edit `Backend/.env`:
```bash
# Enable VLAN automation
ENABLE_VLAN_AUTOMATION=1

# Enable agentic mode (LLM with vendor-specific prompts)
ENABLE_AGENTIC_VLAN_CREATION=1

# Require approval before execution
REQUIRE_VLAN_APPROVAL=1
```

### Restart Server
```bash
cd Backend/netops_backend
python manage.py runserver
```

---

## 🚀 Usage Examples

### Cisco IOS Switch
```
User: "Create VLAN 100 named Engineering on Cisco switch"

Generated Commands:
configure terminal
vlan 100
name Engineering
exit
write memory
end
```

### Aruba AOS-CX Switch
```
User: "Add VLAN 200 called Sales on Aruba switch"

Generated Commands:
configure terminal
vlan 200
name Sales
exit
write memory
end
```

### Juniper JunOS
```
User: "Create VLAN 100 named Engineering on Juniper"

Generated Commands:
configure
set vlans Engineering vlan-id 100
commit
exit
```

### Multiple VLANs
```
User: "Create VLANs 10, 20, 30 named Data, Voice, Video"

Generated Commands:
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

---

## 📊 Vendor Command Comparison

| Vendor | Enter Config | Create VLAN | Name | Save | Exit |
|--------|-------------|-------------|------|------|------|
| **Cisco IOS** | `configure terminal` | `vlan 100` | `name Eng` | `write memory` | `end` |
| **Aruba AOS-CX** | `configure terminal` | `vlan 100` | `name Eng` | `write memory` | `end` |
| **Aruba ProVision** | *(none)* | `vlan 100` | `name "Eng"` | `write memory` | *(none)* |
| **Juniper JunOS** | `configure` | `set vlans Eng vlan-id 100` | *(combined)* | `commit` | `exit` |
| **HPE Comware** | `system-view` | `vlan 100` | `name Eng` | `save` | `quit` |

---

## 🧪 Testing

### Test in Python Shell

```python
python manage.py shell

# Import functions
from netops_backend.vlan_agent.prompts import (
    get_vlan_creation_prompt,
    format_vlan_query,
    get_supported_vendors
)
from netops_backend.nlp_router import predict_cli_provider

# View supported vendors
print(get_supported_vendors())
# ['Cisco IOS/IOS-XE', 'Aruba AOS-CX', 'Aruba AOS (ProVision)', 'Juniper JunOS', 'HPE Comware']

# Test Cisco prompt
cisco_prompt = get_vlan_creation_prompt('cisco_ios')
query = format_vlan_query(100, "Engineering", "create")
commands = predict_cli_provider(query, provider='local', system_prompt=cisco_prompt)
print(commands)

# Test Aruba prompt
aruba_prompt = get_vlan_creation_prompt('aruba_aoscx')
query = format_vlan_query(200, "Sales", "create")
commands = predict_cli_provider(query, provider='gemini', system_prompt=aruba_prompt)
print(commands)
```

### Test via API

```powershell
# PowerShell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/nlp/network-command/" `
  -ContentType "application/json" `
  -Body '{"query": "create vlan 100 named test on aruba", "session_id": "test"}'
```

---

## 🔍 Debugging

### Check if Agentic Mode is Active

```python
import os
print("Agentic Mode:", os.getenv("ENABLE_AGENTIC_VLAN_CREATION", "0"))
print("VLAN Automation:", os.getenv("ENABLE_VLAN_AUTOMATION", "0"))
```

### View Generated Commands (Logs)

Check Django logs for entries like:
```
[INFO] Generating VLAN commands via gemini LLM with vendor-specific prompt
[INFO] LLM generated 6 commands for VLAN creation
[INFO] Commands: ['configure terminal', 'vlan 100', 'name Engineering', ...]
```

### Test Individual Components

```python
# Test prompt selection
from netops_backend.vlan_agent.prompts import get_vlan_creation_prompt

cisco_prompt = get_vlan_creation_prompt('cisco_ios')
print("Cisco Prompt Length:", len(cisco_prompt))

aruba_prompt = get_vlan_creation_prompt('aruba_aoscx')
print("Aruba Prompt Length:", len(aruba_prompt))

# Test query formatting
from netops_backend.vlan_agent.prompts import format_vlan_query

query = format_vlan_query(100, "Engineering", "create")
print("Formatted Query:", query)
# Output: "Create VLAN 100 named Engineering"
```

---

## 📚 Key Functions Reference

### `get_vlan_creation_prompt(device_type: str) -> str`
Returns vendor-specific prompt for VLAN creation.

```python
prompt = get_vlan_creation_prompt('aruba_aoscx')
# Returns: ARUBA_AOSCX_VLAN_SYSTEM_PROMPT (multi-line string)
```

### `format_vlan_query(vlan_id: int, vlan_name: str, action: str) -> str`
Formats natural language query for LLM.

```python
query = format_vlan_query(100, "Engineering", "create")
# Returns: "Create VLAN 100 named Engineering"
```

### `get_vlan_validation_command(device_type: str, vlan_id: int) -> str`
Returns vendor-specific validation command.

```python
cmd = get_vlan_validation_command('cisco_ios', 100)
# Returns: "show vlan id 100"

cmd = get_vlan_validation_command('juniper', 100)
# Returns: "show vlans"
```

### `_configure_vlan_agentic(connection, vlan_id, name, device_type, use_llm) -> Dict`
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
    "commands": ["configure terminal", "vlan 100", ...],
    "output": "...",
    "method": "agentic",
    "config_saved": True
}
```

---

## 🎯 Supported Vendors

### ✅ Fully Implemented
- **Cisco IOS/IOS-XE** - Complete multi-command workflows
- **Aruba AOS-CX** - Complete with descriptions
- **Aruba ProVision** - Simplified syntax with quotes
- **Juniper JunOS** - Hierarchical set commands
- **HPE Comware** - System-view based

### 🔜 Easy to Add
Any vendor can be added by creating a new prompt in `prompts.py`:
```python
NEW_VENDOR_VLAN_PROMPT = """You are an expert <Vendor> engineer.

SYNTAX:
- Command 1: ...
- Command 2: ...

EXAMPLE:
Input: "Create VLAN 100"
Output:
<vendor-specific-commands>
"""
```

---

## ⚡ Quick Command Reference

### Enable Features
```bash
# Edit Backend/.env
ENABLE_VLAN_AUTOMATION=1
ENABLE_AGENTIC_VLAN_CREATION=1
```

### Test Prompts
```python
python manage.py shell
>>> from netops_backend.vlan_agent.prompts import *
>>> get_supported_vendors()
>>> get_vlan_creation_prompt('cisco_ios')
```

### View Logs
```bash
tail -f Backend/netops_backend/logs/django.log
```

### Restart Server
```bash
cd Backend/netops_backend
python manage.py runserver
```

---

## 💡 Key Benefits

1. **Multi-Vendor Support** - One system, all vendors
2. **Complete Workflows** - Mode transitions + save commands
3. **Easy to Extend** - Add vendors by adding prompts
4. **Natural Language** - Flexible query understanding
5. **Maintainable** - Prompts are text, not code
6. **Scalable** - Same pattern for interfaces, routing, ACLs, etc.

---

## 📖 Documentation Links

- **Full Guide:** `AGENTIC_VLAN_PROMPTS.md` - Complete explanation with examples
- **Implementation:** `Backend/netops_backend/netops_backend/vlan_agent/prompts.py` - Source code
- **Flow Diagram:** `VLAN_CREATION_FLOW.md` - Step-by-step execution flow

---

## 🎉 Summary

**Before:** Hardcoded commands for limited vendors
```python
cfg = [f"vlan {vlan_id}", f"name {name}"]
```

**After:** AI-generated multi-command workflows for any vendor
```python
prompt = get_vlan_creation_prompt(device_type)
commands = llm.generate(query, prompt)
# Returns: ['configure terminal', 'vlan 100', 'name Engineering', 'exit', 'write memory', 'end']
```

**Result:** Scalable, maintainable, multi-vendor VLAN automation! 🚀
