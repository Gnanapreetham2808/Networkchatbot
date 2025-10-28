# Data Model (VLANIntent)

```mermaid
erDiagram
    VLANIntent {
        int id PK "AutoField, Primary Key"
        int vlan_id "1-4094, Required, Validated"
        string name "Max 64 chars, Required"
        string scope "Max 32, Default=access"
        string status "Max 32, Default=PENDING"
        datetime created_at "Auto timestamp"
        datetime updated_at "Auto update timestamp"
    }
    
    VLANIntent ||--o{ DeploymentLog : "has many"
    VLANIntent ||--o{ ValidationResult : "has many"
    
    DeploymentLog {
        int id PK
        int vlan_intent_id FK
        string device_name
        string result "created/skipped/failed"
        text error_message "Optional"
        datetime timestamp
    }
    
    ValidationResult {
        int id PK
        int vlan_intent_id FK
        string device_name
        string consistency "ok/missing/conflict"
        datetime checked_at
    }
```

## Status State Machine
```mermaid
stateDiagram-v2
    [*] --> PENDING : Intent Created
    
    PENDING --> APPLIED : All Devices Success/Skip
    PENDING --> FAILED : Any Device Failed
    PENDING --> PENDING : Validation Only
    
    APPLIED --> APPLIED : Re-validation (ok)
    APPLIED --> FAILED : Re-deploy Failed
    
    FAILED --> APPLIED : Retry Success
    FAILED --> FAILED : Retry Failed
    
    APPLIED --> [*] : Delete Intent
    FAILED --> [*] : Delete Intent
    
    note right of PENDING
        Initial state when
        VLANIntent is created
        via NLP or manual entry
    end note
    
    note right of APPLIED
        Successfully deployed
        to all devices
        (core + access switches)
    end note
    
    note right of FAILED
        Deployment failed
        on one or more devices
        (or core switch failed)
    end note
```

## Constraints & Validations
```mermaid
graph TD
    subgraph "Field Validations"
        V1[vlan_id: MinValueValidator=1]
        V2[vlan_id: MaxValueValidator=4094]
        V3[name: max_length=64]
        V4[scope: max_length=32]
        V5[status: max_length=32]
    end
    
    subgraph "Model Constraints"
        C1[unique_together:<br/>vlan_id + scope]
        C2[Example:<br/>VLAN 100 access ✓<br/>VLAN 100 core ✓<br/>VLAN 100 access ✗ duplicate]
    end
    
    subgraph "Business Rules"
        R1[Core switch must succeed<br/>before access switches]
        R2[Status transitions:<br/>PENDING → APPLIED/FAILED only]
        R3[Cannot have same<br/>vlan_id+scope combination]
    end
    
    V1 --> C1
    V2 --> C1
    C1 --> R3
    R3 --> R1
    
    style C1 fill:#FF6B6B
    style R1 fill:#9370DB
    style R3 fill:#FFA500
```

**Usage**: Copy sections into [Mermaid Live Editor](https://mermaid.live/) to visualize the database schema and relationships.
