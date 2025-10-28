# Flowchart Prompt for VLAN Automation System

Copy and paste this prompt into your flowchart maker AI (like Mermaid Live Editor, Lucidchart AI, or similar):

---

## Prompt for Flowchart AI:

Create a comprehensive flowchart diagram for a **VLAN Automation System** with the following components and flows:

### 1. SYSTEM ARCHITECTURE DIAGRAM
Show these components and their connections:
- **Frontend Layer**: Next.js React App with two interfaces:
  - Chat Interface (/chat)
  - VLAN Manager Interface (/vlan-manager)
- **API Layer**: Django REST Framework with endpoints:
  - POST /api/vlan-intents/nlp/ (NLP parser)
  - POST /api/vlan-intents/apply-intents/ (Batch deploy)
  - GET /api/vlan-intents/{id}/validate/ (Validation)
  - Standard CRUD endpoints
- **Business Logic Layer**:
  - NLP Parser (Regex-based text extraction)
  - VLAN Intent Manager
  - Network Driver (Netmiko SSH automation)
- **Data Layer**:
  - PostgreSQL/SQLite Database (VLANIntent model)
  - Device Inventory (devices.json)
- **Network Layer**: Three physical switches:
  - INVIJB1SW1 (Cisco Core Switch) - PRIMARY
  - INHYDB3SW3 (Aruba Access Switch) - SECONDARY
  - UKLONB1SW2 (Cisco Access Switch) - SECONDARY

### 2. END-TO-END USER FLOW
Create a sequential flow showing:

**Step 1: User Input**
- User types in chat: "Create VLAN 300 named Switches on access"
- Frontend detects VLAN keywords with regex

**Step 2: NLP Processing**
- POST request to /api/vlan-intents/nlp/?apply=1
- NLP Parser extracts:
  - vlan_id: 300
  - name: "Switches"
  - scope: "access"

**Step 3: Intent Creation**
- Django creates VLANIntent record in database
- Initial status: "PENDING"
- Validates: vlan_id between 1-4094, unique (vlan_id, scope)

**Step 4: Hierarchical Deployment** (Show as subprocess)
- **Phase A: Core Switch Deployment**
  - Connect to INVIJB1SW1 via SSH (Netmiko)
  - Check if VLAN exists: "show vlan brief"
  - Decision: If exists → Skip, If not → Configure
  - Configure: "conf t", "vlan 300", "name Switches", "exit"
  - Result: "created" or "skipped" or "failed"
  
- **Phase B: Decision Point**
  - If Core = "failed" → ABORT deployment
  - Mark all access switches as "skipped (core failed)"
  - Update intent status to "FAILED"
  - If Core = "created" or "skipped" → Continue to Phase C

- **Phase C: Access Switches Deployment**
  - Deploy to INHYDB3SW3 (same process as Core)
  - Deploy to UKLONB1SW2 (same process as Core)
  - Both run in parallel after core success

**Step 5: Status Update**
- Aggregate results from all devices
- Update database status:
  - All success/skip → status = "APPLIED"
  - Any failure → status = "FAILED"
- Return results to frontend

**Step 6: User Response**
- Display formatted message:
  - "VLAN 300 (Switches) deployment completed"
  - Show per-device status table:
    - INVIJB1SW1: ✓ created
    - INHYDB3SW3: ✓ created
    - UKLONB1SW2: ⊘ skipped (already exists)

### 3. HIERARCHICAL DEPLOYMENT LOGIC
Create a flowchart showing the decision tree:

```
START Deployment
    ↓
Deploy to Core Switch (INVIJB1SW1)
    ↓
[Decision] Core Result?
    ├─→ "failed" 
    │       ↓
    │   Mark Access Switches: "skipped (core failed)"
    │       ↓
    │   Status = "FAILED"
    │       ↓
    │   END (ABORT)
    │
    └─→ "created" OR "skipped"
            ↓
        Deploy to Access Switch 1 (INHYDB3SW3)
            ↓
        Deploy to Access Switch 2 (UKLONB1SW2)
            ↓
        Aggregate All Results
            ↓
        [Decision] Any failures?
            ├─→ YES: Status = "FAILED"
            └─→ NO: Status = "APPLIED"
            ↓
        END (SUCCESS)
```

### 4. VALIDATION FLOW
Show the validation process:
- User clicks "Validate" button
- GET /api/vlan-intents/{id}/validate/
- Connect to all 3 switches via SSH
- Execute "show vlan brief" on each
- Parse output for VLAN ID match
- Return consistency report:
  - Device: "ok" (VLAN exists with correct name)
  - Device: "missing" (VLAN not found)
  - Device: "conflict" (VLAN exists with different name)
- Display color-coded results in UI

### 5. SPECIAL CASES TO SHOW
Include these decision branches:

**Case 1: VLAN Already Exists**
- Check returns existing VLAN
- Skip configuration
- Result: "skipped (already exists)"
- Continue normal flow

**Case 2: SSH Connection Failure**
- Netmiko raises AuthenticationException or NetmikoTimeoutException
- Log error
- Result: "failed (connection error)"
- If on Core → Abort all
- If on Access → Continue with other switches

**Case 3: Configuration Error**
- Command execution fails
- Result: "failed (config error)"
- Log full error details
- Update status accordingly

**Case 4: Batch Apply from Manager UI**
- User clicks "Apply Pending" in /vlan-manager
- POST /api/vlan-intents/apply-intents/
- Fetch all intents with status="PENDING"
- Deploy each sequentially (not parallel)
- Show progress in UI

### 6. DATA MODEL
Show the VLANIntent database schema:
- **Fields:**
  - id (AutoField, Primary Key)
  - vlan_id (Integer, 1-4094, required)
  - name (String, max 64 chars, required)
  - scope (String, max 32, default="access")
  - status (String, max 32, default="PENDING")
  - created_at (DateTime, auto_now_add)
  - updated_at (DateTime, auto_now)
- **Constraints:**
  - unique_together = ("vlan_id", "scope")
- **Status Values:**
  - "PENDING" → Not yet deployed
  - "APPLIED" → Successfully deployed
  - "FAILED" → Deployment failed

### 7. COLOR CODING SUGGESTIONS
- **Green**: Success states, "APPLIED", "created", "ok"
- **Blue**: Processing states, "PENDING", in-progress
- **Yellow**: Skip states, "skipped", "already exists"
- **Red**: Error states, "FAILED", "failed", "missing", "conflict"
- **Purple**: Core switch (INVIJB1SW1)
- **Orange**: Access switches (INHYDB3SW3, UKLONB1SW2)

### 8. LAYOUT PREFERENCES
- Use **swimlanes** for Frontend/API/Logic/Network layers in architecture diagram
- Use **decision diamonds** for conditional branches
- Use **subprocesses** for device deployment loops
- Show **parallel processes** for access switch deployment (after core success)
- Include **annotations** for key technology choices (Django, Netmiko, React)
- Add **timing indicators** where relevant (e.g., SSH timeout: 10s)

---

## Additional Context for AI:
This is a network automation chatbot that allows IT operators to create VLANs across multiple switches using natural language. The system enforces a hierarchical deployment pattern where the core switch MUST succeed before attempting access switches. All communication with network devices is via SSH using Netmiko library. The NLP parsing is regex-based (offline, no external LLM). The system includes validation to ensure VLAN consistency across the network infrastructure.

**Key Innovation**: Hierarchical deployment with abort logic prevents inconsistent network state (half-deployed VLANs).

---

## Output Format:
Generate the flowchart in your native format (Mermaid, Lucidchart, etc.) with clear visual hierarchy, appropriate use of colors, and proper labeling of all decision points and processes.
