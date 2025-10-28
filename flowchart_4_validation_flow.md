# Validation Flow

```mermaid
flowchart TD
    Start([User Clicks Validate]) --> APICall[GET /api/vlan-intents/{id}/validate/]
    
    APICall --> GetIntent[Fetch VLANIntent<br/>from Database]
    GetIntent --> GetDevices[Get Device List<br/>from devices.json]
    
    GetDevices --> ConnectAll[Connect to All Switches via SSH]
    
    ConnectAll --> CheckCore[Connect to INVIJB1SW1]
    ConnectAll --> CheckAccess1[Connect to INHYDB3SW3]
    ConnectAll --> CheckAccess2[Connect to UKLONB1SW2]
    
    CheckCore --> CoreCmd[Execute:<br/>show vlan brief]
    CheckAccess1 --> Access1Cmd[Execute:<br/>show vlan brief]
    CheckAccess2 --> Access2Cmd[Execute:<br/>show vlan brief]
    
    CoreCmd --> CoreParse{Parse Output}
    Access1Cmd --> Access1Parse{Parse Output}
    Access2Cmd --> Access2Parse{Parse Output}
    
    CoreParse -->|VLAN found<br/>correct name| CoreOK[INVIJB1SW1: ok]
    CoreParse -->|VLAN not found| CoreMissing[INVIJB1SW1: missing]
    CoreParse -->|VLAN found<br/>wrong name| CoreConflict[INVIJB1SW1: conflict]
    
    Access1Parse -->|VLAN found<br/>correct name| Access1OK[INHYDB3SW3: ok]
    Access1Parse -->|VLAN not found| Access1Missing[INHYDB3SW3: missing]
    Access1Parse -->|VLAN found<br/>wrong name| Access1Conflict[INHYDB3SW3: conflict]
    
    Access2Parse -->|VLAN found<br/>correct name| Access2OK[UKLONB1SW2: ok]
    Access2Parse -->|VLAN not found| Access2Missing[UKLONB1SW2: missing]
    Access2Parse -->|VLAN found<br/>wrong name| Access2Conflict[UKLONB1SW2: conflict]
    
    CoreOK --> BuildReport[Build Consistency Report]
    CoreMissing --> BuildReport
    CoreConflict --> BuildReport
    Access1OK --> BuildReport
    Access1Missing --> BuildReport
    Access1Conflict --> BuildReport
    Access2OK --> BuildReport
    Access2Missing --> BuildReport
    Access2Conflict --> BuildReport
    
    BuildReport --> ReturnAPI[Return JSON Response]
    ReturnAPI --> DisplayUI[Display Color-Coded Results in UI]
    
    DisplayUI --> End([END])
    
    style Start fill:#87CEEB
    style CoreOK fill:#90EE90
    style Access1OK fill:#90EE90
    style Access2OK fill:#90EE90
    style CoreMissing fill:#FF6B6B
    style Access1Missing fill:#FF6B6B
    style Access2Missing fill:#FF6B6B
    style CoreConflict fill:#FFA500
    style Access1Conflict fill:#FFA500
    style Access2Conflict fill:#FFA500
    style BuildReport fill:#87CEEB
    style DisplayUI fill:#90EE90
    style End fill:#90EE90
```

**Usage**: Copy this into [Mermaid Live Editor](https://mermaid.live/) to visualize VLAN consistency validation.
