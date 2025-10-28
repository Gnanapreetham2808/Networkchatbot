# Special Cases Flow

## Case 1: VLAN Already Exists
```mermaid
flowchart LR
    Start([Check VLAN]) --> Execute[show vlan brief]
    Execute --> Parse{VLAN Found?}
    Parse -->|Yes| Skip[Result: skipped<br/>already exists]
    Parse -->|No| Configure[Create VLAN<br/>Configuration]
    Skip --> Continue[Continue Normal Flow]
    Configure --> Continue
    
    style Skip fill:#FFFF99
    style Configure fill:#90EE90
```

## Case 2: SSH Connection Failure
```mermaid
flowchart TD
    Start([SSH Connect Attempt]) --> Connect{Connection<br/>Success?}
    
    Connect -->|No| Exception[Netmiko Exception:<br/>AuthenticationException or<br/>NetmikoTimeoutException]
    
    Exception --> Log[Log Error:<br/>connection error]
    Log --> Failed[Result: failed<br/>connection error]
    
    Failed --> WhichDevice{Device Type?}
    
    WhichDevice -->|Core Switch| AbortAll[ABORT Deployment<br/>Mark Access: skipped core failed<br/>Status = FAILED]
    WhichDevice -->|Access Switch| ContinueOthers[Continue with<br/>Other Access Switches]
    
    AbortAll --> End1([END - ABORT])
    ContinueOthers --> End2([Continue])
    
    Connect -->|Yes| Success[Proceed with<br/>VLAN Configuration]
    Success --> End3([Continue])
    
    style Exception fill:#FF6B6B
    style Failed fill:#FF6B6B
    style AbortAll fill:#FF6B6B
    style Success fill:#90EE90
```

## Case 3: Configuration Error
```mermaid
flowchart TD
    Start([Execute Config Commands]) --> Conf[conf t]
    Conf --> Vlan[vlan 300]
    Vlan --> Name[name Switches]
    Name --> Exit[exit]
    
    Exit --> Check{Command<br/>Success?}
    
    Check -->|No| Error[Configuration Error]
    Error --> LogError[Log Full Error Details]
    LogError --> FailResult[Result: failed<br/>config error]
    FailResult --> UpdateDB[Update Status<br/>Consider as Failure]
    
    Check -->|Yes| Success[Result: created]
    Success --> UpdateSuccess[Status = APPLIED<br/>if all devices ok]
    
    UpdateDB --> End1([END])
    UpdateSuccess --> End2([END])
    
    style Error fill:#FF6B6B
    style FailResult fill:#FF6B6B
    style Success fill:#90EE90
```

## Case 4: Batch Apply from Manager UI
```mermaid
flowchart TD
    Start([User Clicks Apply Pending]) --> API[POST /api/vlan-intents/apply-intents/]
    
    API --> Query[Query Database:<br/>status=PENDING]
    Query --> Found{Found<br/>Pending Intents?}
    
    Found -->|No| NoIntents[Return:<br/>No pending intents]
    NoIntents --> End1([END])
    
    Found -->|Yes| GetList[Get List of<br/>Pending VLANIntents]
    GetList --> Loop[Process Each Intent<br/>SEQUENTIALLY not parallel]
    
    Loop --> Intent1[Deploy Intent 1]
    Intent1 --> Intent2[Deploy Intent 2]
    Intent2 --> IntentN[Deploy Intent N...]
    
    IntentN --> UpdateUI[Show Progress in UI:<br/>Real-time status updates]
    UpdateUI --> Complete[All Intents Processed]
    
    Complete --> Summary[Return Summary:<br/>Success count<br/>Failed count<br/>Device details]
    
    Summary --> Display[Display Results in<br/>VLAN Manager UI]
    Display --> End2([END])
    
    style Start fill:#87CEEB
    style Loop fill:#87CEEB
    style Complete fill:#90EE90
    style Display fill:#90EE90
```

**Usage**: Copy each section into [Mermaid Live Editor](https://mermaid.live/) separately to visualize different special cases.
