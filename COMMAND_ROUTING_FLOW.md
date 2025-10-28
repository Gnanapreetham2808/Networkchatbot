# 🔄 Command Routing Flow: Read-Only vs Agentic Mode

## Overview

Your network chatbot has **two distinct modes** with different routing logic:

1. **Read-Only Mode** (Default) - Show commands only, device-vendor-aware NLP
2. **Agentic Mode** - VLAN creation and deployment only

---

## 📊 Read-Only Mode Flow

### **Step 1: Device Resolution**
**File:** `Backend/netops_backend/chatbot/views.py` (Lines 166-330)

```
User Query: "Show me the interfaces Brief"
           ↓
Device Resolver (Automatic Detection):
  • Extract device hints from query (keywords like "vijayawada", "london", "uk")
  • Check conversation history for last used device
  • Fallback to default device (UKLONB10C01)
           ↓
Device Identified: INVIJB1C01 (Cisco) or INVIJB10A01 (Aruba) or UKLONB10C01 (Cisco)
```

**Resolution Priority:**
1. Explicit alias in query/parameter
2. Location keywords in query
3. Conversation history
4. Default device from env/config

---

### **Step 2: Vendor-Aware NLP Routing**
**File:** `Backend/netops_backend/chatbot/views.py` (Lines 430-503)

```python
# After device is resolved, check vendor type
vendor = resolved_device_dict.get("vendor")  # "cisco" or "aruba"

if vendor == "aruba":
    # ✅ ARUBA → OpenAI API (GPT-4o-mini/GPT-4)
    cli_command = predict_cli_provider(
        query=sanitized_query,
        provider="openai",
        model="gpt-4o-mini",
        system_prompt="You are a precise network CLI assistant. Given a natural language request, output exactly one Aruba AOS-CX show command that best answers it. Ignore any location words (like city or site). Return ONLY the command text."
    )
    
elif vendor == "cisco":
    # ✅ CISCO → Local T5 Model (Default)
    cli_command = predict_cli_provider(
        query=query,
        provider="local",  # Uses T5/LoRA model
        model=None,
        system_prompt=None
    )
```

**Vendor Detection Logic:**
```python
vendor_l = str(vendor).lower()

if "aruba" in vendor_l or "hp" in vendor_l or "hewlett" in vendor_l:
    # Route to OpenAI
else:
    # Route to Local T5 (Cisco default)
```

---

### **Step 3: CLI Command Generation**

#### **For Cisco Devices (T5 Model)**
**File:** `Backend/netops_backend/nlp_router.py`

```python
def predict_cli_provider(query, provider="local", model=None, system_prompt=None):
    if provider == "local":
        # Use fine-tuned T5 model
        input_text = f"translate to cli: {query}"
        input_ids = tokenizer.encode(input_text, return_tensors='pt')
        
        outputs = t5_model.generate(
            input_ids,
            max_length=50,
            num_beams=4,
            early_stopping=True
        )
        
        cli_command = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Returns: "show ip interface brief"
```

**Cisco T5 Processing:**
- Input: `"translate to cli: Show me the interfaces Brief"`
- Model: Local T5-base fine-tuned on cisco_nl2cli.json
- Output: `"show ip interface brief"`
- Speed: ~300-500ms
- Cost: Free

---

#### **For Aruba Devices (OpenAI API)**
**File:** `Backend/netops_backend/nlp_router.py`

```python
def predict_cli_provider(query, provider="openai", model="gpt-4o-mini", system_prompt=None):
    if provider == "openai":
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=model,  # "gpt-4o-mini"
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise network CLI assistant. Given a natural language request, output exactly one Aruba AOS-CX show command that best answers it. Ignore any location words (like city or site). Return ONLY the command text."
                },
                {
                    "role": "user",
                    "content": "Show me the interfaces Brief"
                }
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        cli_command = response.choices[0].message.content.strip()
        # Returns: "show interface brief"
```

**Aruba OpenAI Processing:**
- Input: `"Show me the interfaces Brief"` (sanitized, location keywords removed)
- Model: GPT-4o-mini (configurable to GPT-4)
- Output: `"show interface brief"` (Aruba syntax)
- Speed: ~800-1200ms
- Cost: ~$0.03 per 1000 tokens

---

### **Step 4: Command Execution via Netmiko**
**File:** `Backend/netops_backend/chatbot/views.py` (Lines 520-700)

```python
# Connect to device via SSH
connection = ConnectHandler(
    device_type=resolved_device_dict['device_type'],  # 'cisco_ios' or 'aruba_aoscx'
    host=device_ip,                                   # '192.168.10.1'
    username=resolved_device_dict['username'],        # 'admin'
    password=resolved_device_dict['password'],        # 'cisco' or 'Aruba'
    port=22
)

# Execute command
output = connection.send_command(cli_command)

# Disconnect
connection.disconnect()
```

**Command Execution:**
```
Cisco (INVIJB1C01):
  INVIJB1C01# show ip interface brief
  
Aruba (INVIJB10A01):
  INVIJB10A01# show interface brief
```

---

### **Step 5: Response Formatting**

```python
response_data = {
    'output': output,                    # CLI output from device
    'device_alias': hostname,            # 'INVIJB1C01'
    'device_host': device_ip,            # '192.168.10.1'
    'cli_command': cli_command,          # 'show ip interface brief'
    'session_id': session_id,
    'vendor': vendor,                    # 'cisco' or 'aruba'
    'nlp_method': 'T5' if vendor == 'cisco' else 'OpenAI',
    'status': 'success'
}
```

---

## ⚡ Agentic Mode Flow (VLAN Only)

### **Step 1: Frontend Detection**
**File:** `Frontend/src/app/chat/page.tsx`

```typescript
const handleSend = async () => {
  const userMessage = input.trim()
  
  // Check if Agentic Mode is enabled
  if (agenticMode) {
    // Check if message is a VLAN command
    const vlanMatch = userMessage.match(/create vlan|add vlan|new vlan|configure vlan/i)
    
    if (vlanMatch) {
      // ✅ Route to VLAN Agent (Bypass NLP)
      const vlanUrl = BACKEND_URL + '/api/vlan-intents/nlp/?apply=1'
      
      const response = await fetch(vlanUrl, {
        method: 'POST',
        body: JSON.stringify({ command: userMessage })
      })
      
      // VLAN creation uses REGEX parsing, NOT OpenAI/T5
    } else {
      // ❌ Not a VLAN command in Agentic Mode
      // Show error: "Agentic mode only supports VLAN creation"
    }
  } else {
    // ✅ Read-Only Mode - Route to normal chatbot (device-aware NLP)
    // Uses T5 for Cisco, OpenAI for Aruba
  }
}
```

---

### **Step 2: VLAN Regex Parsing**
**File:** `Backend/netops_backend/netops_backend/vlan_agent/nlp_parser.py`

```python
def parse_vlan_intent(command: str) -> dict:
    """Parse VLAN creation intent using REGEX (NO OpenAI/T5)"""
    
    # Pattern: "create vlan 100 named Engineering"
    pattern = r'(?:create|add|new|configure)\s+vlan\s+(\d+)(?:\s+named?\s+(\w+))?'
    
    match = re.search(pattern, command, re.IGNORECASE)
    
    if match:
        vlan_id = int(match.group(1))
        vlan_name = match.group(2) or f"VLAN{vlan_id}"
        
        return {
            'vlan_id': vlan_id,
            'name': vlan_name,
            'scope': 'access'  # default
        }
```

**VLAN Parsing:**
- Input: `"create vlan 100 named Engineering"`
- Method: Pure Regex (NO AI)
- Output: `{'vlan_id': 100, 'name': 'Engineering', 'scope': 'access'}`
- Speed: <1ms
- Cost: Free

---

### **Step 3: Hierarchical VLAN Deployment**
**File:** `Backend/netops_backend/netops_backend/vlan_agent/nornir_driver.py`

```python
def deploy_vlan_to_switches(vlan_plan: dict) -> dict:
    """Deploy VLAN to Core → Access switches"""
    
    CORE_SWITCH = "UKLONB10C01"  # London (Cisco)
    ACCESS_SWITCHES = ["INVIJB1C01", "INVIJB10A01"]  # Vijayawada (Cisco, Aruba)
    
    # Step 1: Deploy to Core first
    core_result = _deploy_to_single_device(CORE_SWITCH, vlan_plan)
    
    # Step 2: If Core succeeds, deploy to Access switches
    if core_result == "created":
        for access_switch in ACCESS_SWITCHES:
            _deploy_to_single_device(access_switch, vlan_plan)
    
    return {
        "UKLONB10C01": "created",    # Core
        "INVIJB1C01": "created",     # Access (Cisco)
        "INVIJB10A01": "created"     # Access (Aruba)
    }
```

**VLAN Deployment:**
- Core: UKLONB10C01 (London, Cisco) → Deployed first
- Access: INVIJB1C01 (Vijayawada, Cisco) → Deployed after core
- Access: INVIJB10A01 (Vijayawada, Aruba) → Deployed after core

---

## 📊 Comparison Table

| Feature | Read-Only Mode | Agentic Mode |
|---------|----------------|--------------|
| **Purpose** | Show commands only | VLAN creation only |
| **Device Resolution** | Automatic (query-based) | Not applicable |
| **Cisco NLP** | T5 Model (local) | N/A - Regex only |
| **Aruba NLP** | OpenAI GPT-4o-mini | N/A - Regex only |
| **Command Types** | `show *` only | `create vlan *` only |
| **Execution** | Single device | Hierarchical (Core→Access) |
| **Safety** | Read-only enforced | Requires explicit toggle |
| **Speed** | 500-1200ms | 300-500ms |
| **Cost** | $0 (Cisco), $0.03/1k tokens (Aruba) | $0 (Regex only) |

---

## 🔑 Key Points

### **Read-Only Mode (Default)**

1. ✅ **Device is resolved FIRST** (from query, conversation, or default)
2. ✅ **Vendor determines NLP method:**
   - **Cisco** → Local T5 Model (free, fast)
   - **Aruba** → OpenAI API (paid, accurate)
3. ✅ **Command executed on single device** via Netmiko SSH
4. ✅ **Only `show` commands allowed** (enforced by safety checks)

### **Agentic Mode (Opt-In)**

1. ✅ **VLAN commands ONLY** (`create vlan`, `add vlan`, etc.)
2. ✅ **Regex parsing** (NO OpenAI, NO T5)
3. ✅ **Hierarchical deployment:**
   - Core (UKLONB10C01) first
   - Then Access switches (INVIJB1C01, INVIJB10A01)
4. ✅ **Requires explicit user toggle** (purple mode indicator)

---

## 🎯 Configuration

### **Environment Variables**

```bash
# Aruba always uses OpenAI (per requirement)
ARUBA_LLM_MODEL=gpt-4o-mini
ARUBA_SYSTEM_PROMPT="You are a precise network CLI assistant..."

# Cisco uses local T5 by default
CISCO_LLM_PROVIDER=local
CISCO_LLM_MODEL=  # Leave empty for local T5

# Fallback settings
ARUBA_FALLBACK_PROVIDER=openai
ARUBA_FALLBACK_MODEL=gpt-4o-mini
CISCO_FALLBACK_PROVIDER=openai
CISCO_FALLBACK_MODEL=gpt-4o-mini

# Default device (if no device resolved)
DEFAULT_DEVICE_ALIAS=UKLONB10C01
```

---

## 🚀 Example Flows

### **Example 1: Show Command on Cisco Device**

```
User: "Show me the interfaces Brief"
      ↓
Device Resolver: Detects default device → INVIJB1C01 (Cisco)
      ↓
NLP Router: Vendor = "cisco" → Use T5 Model
      ↓
T5 Model: "Show me the interfaces Brief" → "show ip interface brief"
      ↓
Netmiko: SSH to 192.168.10.1 (INVIJB1C01)
      ↓
Execute: INVIJB1C01# show ip interface brief
      ↓
Output: Interface table returned to frontend
```

### **Example 2: Show Command on Aruba Device**

```
User: "Show interfaces on vijayawada aruba switch"
      ↓
Device Resolver: Keywords "vijayawada" + "aruba" → INVIJB10A01 (Aruba)
      ↓
NLP Router: Vendor = "aruba" → Use OpenAI API
      ↓
OpenAI GPT-4o-mini: "Show interfaces" → "show interface brief"
      ↓
Netmiko: SSH to 192.168.50.3 (INVIJB10A01)
      ↓
Execute: INVIJB10A01# show interface brief
      ↓
Output: Interface table returned to frontend
```

### **Example 3: VLAN Creation (Agentic Mode)**

```
User: *Toggles Agentic Mode ON*
User: "Create VLAN 100 named Engineering"
      ↓
Frontend: Detects "create vlan" → Route to VLAN Agent
      ↓
Regex Parser: Extract vlan_id=100, name="Engineering"
      ↓
Nornir Driver: Deploy to Core → Access
      ↓
UKLONB10C01 (Core): vlan 100; name Engineering; end
INVIJB1C01 (Access): vlan 100; name Engineering; end
INVIJB10A01 (Access): vlan 100; name Engineering; end
      ↓
Output: "✅ VLAN 100 created on all switches"
```

---

## ✅ System Status

Your current implementation:

✅ Device resolver works correctly  
✅ Vendor-aware NLP routing implemented  
✅ Cisco → T5 Model (local)  
✅ Aruba → OpenAI API (GPT-4o-mini)  
✅ Agentic Mode uses REGEX (no AI for VLANs)  
✅ Safety enforced (read-only by default)  
✅ Hierarchical VLAN deployment (Core → Access)

---

## 📝 Notes

- **VLAN commands NEVER use OpenAI/T5** - they use pure regex parsing for speed and reliability
- **Show commands always use device-aware NLP** - T5 for Cisco, OpenAI for Aruba
- **Device resolution happens BEFORE NLP routing** - this ensures correct vendor-specific command generation
- **Agentic Mode is limited to VLAN operations only** - enforced by frontend regex check

Your system is correctly implemented according to the specification! 🎉
