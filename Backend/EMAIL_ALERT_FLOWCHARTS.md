# Email Alert System - Flowcharts

This document contains visual flowcharts showing how the email alert system works in the Network Chatbot.

---

## 🔄 **Overall Email Alert System Architecture**

```mermaid
graph TB
    Start([Health Monitor Starts]) --> Init[Load Configuration<br/>- CPU Threshold<br/>- Polling Interval<br/>- Email Recipients]
    Init --> LoadDevices[Load Devices from<br/>devices.json]
    LoadDevices --> Loop{Start Monitoring<br/>Loop}
    
    Loop --> Parallel[Poll All Devices<br/>in Parallel<br/>ThreadPoolExecutor]
    
    Parallel --> CPU[CPU Monitoring]
    Parallel --> Topology[Topology Analysis]
    
    CPU --> CPUCheck{CPU > Threshold?}
    CPUCheck -->|Yes| CPUAlert[Raise CPU Alert]
    CPUCheck -->|No| CPUClear[Clear CPU Alert<br/>if exists]
    
    CPUAlert --> EmailCPU[Send Email Alert]
    CPUClear --> Sleep
    
    Topology --> NeighborData[Collect CDP/LLDP<br/>Neighbor Data]
    NeighborData --> LoopDetect{Loops Detected?}
    LoopDetect -->|Yes| LoopAlert[Raise Loop Alert]
    LoopDetect -->|No| LoopClear[Clear Loop Alerts<br/>if exist]
    
    LoopAlert --> EmailLoop[Send Email Alert]
    LoopClear --> Sleep
    
    EmailCPU --> Sleep[Sleep for Interval]
    EmailLoop --> Sleep
    Sleep --> Loop
    
    style Start fill:#90EE90
    style EmailCPU fill:#FFB6C1
    style EmailLoop fill:#FFB6C1
    style CPUAlert fill:#FFA07A
    style LoopAlert fill:#FFA07A
```

---

## 📊 **CPU Alert Flow - Detailed**

```mermaid
flowchart TD
    Start([Monitor Health Running]) --> Poll[Poll Device via SSH]
    Poll --> Execute[Execute Command:<br/>show processes cpu]
    
    Execute --> Success{Command<br/>Success?}
    Success -->|No| LogError[Log Connection Error]
    Success -->|Yes| Parse[Parse CPU Output]
    
    LogError --> Skip[Skip this device]
    Skip --> NextDevice
    
    Parse --> Extract[Extract CPU %:<br/>- 5 sec avg<br/>- 1 min avg<br/>- 5 min avg]
    Extract --> Store[Update DeviceHealth<br/>in Database]
    
    Store --> Compare{CPU ><br/>Threshold?}
    
    Compare -->|No| CheckExisting{Existing<br/>Alert Active?}
    CheckExisting -->|Yes| ClearAlert[Clear Alert<br/>Set cleared_at timestamp]
    CheckExisting -->|No| NextDevice
    ClearAlert --> LogClear[Log: Alert Cleared]
    LogClear --> NextDevice
    
    Compare -->|Yes| CheckCooldown{Alert in<br/>Cooldown?}
    
    CheckCooldown -->|Yes| SkipAlert[Skip Alert<br/>Already notified recently]
    CheckCooldown -->|No| CreateAlert[Create HealthAlert<br/>- Device alias<br/>- CPU percentage<br/>- Timestamp<br/>- Severity: critical]
    
    SkipAlert --> NextDevice
    
    CreateAlert --> SaveDB[Save to Database]
    SaveDB --> LogAlert[Log Alert Details:<br/>- Alias<br/>- CPU %<br/>- Threshold]
    
    LogAlert --> CheckEmail{Email<br/>Recipients<br/>Configured?}
    
    CheckEmail -->|No| NextDevice
    CheckEmail -->|Yes| SendEmail[Send Email via SMTP:<br/>Subject: High CPU Alert<br/>Body: Device details + CPU %]
    
    SendEmail --> EmailSuccess{Email<br/>Sent?}
    
    EmailSuccess -->|Yes| LogSuccess[Log: Email sent successfully]
    EmailSuccess -->|No| LogFail[Log: Email failed<br/>fail_silently=True]
    
    LogSuccess --> UpdateCooldown[Update Last Alert Time<br/>Start 15-min cooldown]
    LogFail --> UpdateCooldown
    
    UpdateCooldown --> NextDevice([Next Device])
    
    style Start fill:#90EE90
    style SendEmail fill:#FFB6C1
    style CreateAlert fill:#FFA07A
    style LogAlert fill:#87CEEB
```

---

## 🔁 **Loop Detection Alert Flow - Detailed**

```mermaid
flowchart TD
    Start([Topology Analysis]) --> CheckDevices{Enough<br/>Devices?<br/>>= 3}
    
    CheckDevices -->|No| Skip[Skip Loop Detection]
    CheckDevices -->|Yes| CollectNeighbors[Collect Neighbor Data<br/>for all devices]
    
    Skip --> End([End])
    
    CollectNeighbors --> PollAll[For Each Device:<br/>Execute CDP/LLDP command]
    
    PollAll --> ParseNeighbors[Parse Neighbor Info:<br/>- Device name<br/>- Interface<br/>- Platform]
    
    ParseNeighbors --> MapAliases[Map Neighbor Names<br/>to Known Aliases<br/>fuzzy matching]
    
    MapAliases --> BuildGraph[Build Network<br/>Topology Graph]
    
    BuildGraph --> DetectCycles[Detect Cycles<br/>using Graph Algorithm:<br/>DFS traversal]
    
    DetectCycles --> CyclesFound{Loops<br/>Detected?}
    
    CyclesFound -->|No| CheckActive{Active Loop<br/>Alerts Exist?}
    
    CheckActive -->|Yes| ClearAll[Clear All Loop Alerts<br/>Set cleared_at timestamp]
    CheckActive -->|No| End
    
    ClearAll --> LogClearAll[Log: All loop alerts cleared]
    LogClearAll --> End
    
    CyclesFound -->|Yes| ProcessLoops[For Each Loop<br/>Max 5 loops]
    
    ProcessLoops --> CreateSig[Create Loop Signature<br/>Canonical sorted path]
    
    CreateSig --> CheckLoopCooldown{Loop Signature<br/>in Cooldown?}
    
    CheckLoopCooldown -->|Yes| SkipLoop[Skip This Loop<br/>Already notified]
    CheckLoopCooldown -->|No| CreateLoopAlert[Create HealthAlert:<br/>- Category: loop<br/>- Severity: warn<br/>- Path: A → B → C → A<br/>- Meta: JSON path]
    
    SkipLoop --> NextLoop{More<br/>Loops?}
    
    CreateLoopAlert --> SaveLoopDB[Save to Database]
    SaveLoopDB --> LogLoop[Log Loop Alert:<br/>- Path<br/>- Signature]
    
    LogLoop --> CheckLoopEmail{Email<br/>Recipients?}
    
    CheckLoopEmail -->|No| UpdateLoopCooldown
    CheckLoopEmail -->|Yes| SendLoopEmail[Send Email:<br/>Subject: Loop Detected<br/>Body: Loop path + devices]
    
    SendLoopEmail --> LoopEmailSuccess{Email<br/>Sent?}
    
    LoopEmailSuccess -->|Yes| LogLoopSuccess[Log: Loop email sent]
    LoopEmailSuccess -->|No| LogLoopFail[Log: Loop email failed<br/>fail_silently=True]
    
    LogLoopSuccess --> UpdateLoopCooldown[Update Loop Cooldown<br/>Store signature + timestamp]
    LogLoopFail --> UpdateLoopCooldown
    
    UpdateLoopCooldown --> NextLoop
    NextLoop -->|Yes| ProcessLoops
    NextLoop -->|No| End
    
    style Start fill:#90EE90
    style SendLoopEmail fill:#FFB6C1
    style CreateLoopAlert fill:#FFA07A
    style DetectCycles fill:#87CEEB
```

---

## 📧 **Email Sending Process - Detailed**

```mermaid
flowchart TD
    Start([Trigger Email Alert]) --> CheckBackend{Email Backend<br/>Type?}
    
    CheckBackend -->|console| PrintConsole[Print Email to Console:<br/>- Subject<br/>- From<br/>- To<br/>- Body]
    CheckBackend -->|smtp| CheckConfig{SMTP Config<br/>Valid?}
    
    PrintConsole --> LogConsole[Log: Email printed to console]
    LogConsole --> End([End])
    
    CheckConfig -->|No| LogNoConfig[Log: Email not configured<br/>Missing HOST_USER or PASSWORD]
    LogNoConfig --> End
    
    CheckConfig -->|Yes| BuildEmail[Build Email Message:<br/>- Subject line<br/>- From address<br/>- To recipients<br/>- Message body<br/>- Timestamp]
    
    BuildEmail --> ConnectSMTP[Connect to SMTP Server:<br/>- Host: smtp.gmail.com<br/>- Port: 587<br/>- TLS: enabled]
    
    ConnectSMTP --> AuthSuccess{Authentication<br/>Success?}
    
    AuthSuccess -->|No| AuthError[SMTPAuthenticationError:<br/>- Wrong username/password<br/>- 2FA blocking<br/>- Need App Password]
    
    AuthError --> LogAuthError[Log: SMTP auth failed]
    LogAuthError --> Retry{Retry<br/>Available?}
    
    Retry -->|Yes| ConnectSMTP
    Retry -->|No| End
    
    AuthSuccess -->|Yes| SendMessage[Send Email Message<br/>via SMTP]
    
    SendMessage --> SendSuccess{Message<br/>Accepted?}
    
    SendSuccess -->|No| SendError[SMTPSenderRefused:<br/>- FROM address not verified<br/>- Relay denied<br/>- Rate limit hit]
    
    SendError --> LogSendError[Log: Email send failed]
    LogSendError --> End
    
    SendSuccess -->|Yes| CloseConnection[Close SMTP Connection]
    CloseConnection --> LogSuccess[Log: Email sent successfully<br/>- Recipients<br/>- Subject<br/>- Timestamp]
    
    LogSuccess --> UpdateMetrics[Update Metrics:<br/>- Email counter<br/>- Success rate<br/>- Last send time]
    
    UpdateMetrics --> End
    
    style Start fill:#90EE90
    style SendMessage fill:#FFB6C1
    style LogSuccess fill:#98FB98
    style AuthError fill:#FF6B6B
    style SendError fill:#FF6B6B
```

---

## 🔄 **Alert Cooldown & Deduplication Logic**

```mermaid
flowchart TD
    Start([Alert Triggered]) --> GetTimestamp[Get Current Timestamp]
    
    GetTimestamp --> CheckType{Alert Type?}
    
    CheckType -->|CPU| GetDeviceAlias[Get Device Alias]
    CheckType -->|Loop| GetLoopSignature[Get Loop Signature<br/>Sorted path string]
    
    GetDeviceAlias --> CheckLastCPU{Last CPU Alert<br/>for this Device?}
    GetLoopSignature --> CheckLastLoop{Last Loop Alert<br/>for this Signature?}
    
    CheckLastCPU -->|None| AllowCPU[Allow Alert:<br/>First alert for this device]
    CheckLastLoop -->|None| AllowLoop[Allow Alert:<br/>First alert for this loop]
    
    CheckLastCPU -->|Exists| CalcTimeDiffCPU[Calculate Time Difference:<br/>Now - Last Alert Time]
    CheckLastLoop -->|Exists| CalcTimeDiffLoop[Calculate Time Difference:<br/>Now - Last Alert Time]
    
    CalcTimeDiffCPU --> WithinCooldownCPU{Time Diff <<br/>Cooldown Period?<br/>Default: 15 min}
    CalcTimeDiffLoop --> WithinCooldownLoop{Time Diff <<br/>Cooldown Period?<br/>Default: 15 min}
    
    WithinCooldownCPU -->|Yes| BlockCPU[Block Alert:<br/>Still in cooldown<br/>Don't spam]
    WithinCooldownCPU -->|No| AllowCPU
    
    WithinCooldownLoop -->|Yes| BlockLoop[Block Alert:<br/>Still in cooldown<br/>Don't spam]
    WithinCooldownLoop -->|No| AllowLoop
    
    BlockCPU --> LogSkip[Log: Alert skipped<br/>Cooldown active]
    BlockLoop --> LogSkip
    LogSkip --> End([End - No Email Sent])
    
    AllowCPU --> SendCPUEmail[Send CPU Alert Email]
    AllowLoop --> SendLoopEmail[Send Loop Alert Email]
    
    SendCPUEmail --> UpdateCPUTime[Update Last Alert Time<br/>for this Device]
    SendLoopEmail --> UpdateLoopTime[Update Last Alert Time<br/>for this Signature]
    
    UpdateCPUTime --> Success([Alert Sent Successfully])
    UpdateLoopTime --> Success
    
    style Start fill:#90EE90
    style BlockCPU fill:#FFB6C1
    style BlockLoop fill:#FFB6C1
    style Success fill:#98FB98
    style LogSkip fill:#FFA07A
```

---

## 📨 **Email Content Generation**

```mermaid
flowchart TD
    Start([Generate Email]) --> GetAlertType{Alert Type?}
    
    GetAlertType -->|CPU| BuildCPUSubject[Subject:<br/>[NetOps] High CPU Alert - DEVICE_ALIAS]
    GetAlertType -->|Loop| BuildLoopSubject[Subject:<br/>[NetOps] Possible Loop Detected]
    
    BuildCPUSubject --> BuildCPUBody[Body:<br/>Device: ALIAS HOST<br/>Location: LOCATION<br/>CPU: XX%<br/>Threshold: XX%<br/>Time: TIMESTAMP<br/><br/>Action Required:<br/>1. Check processes<br/>2. Investigate tasks<br/>3. Consider upgrade]
    
    BuildLoopSubject --> BuildLoopBody[Body:<br/>Potential loop via:<br/>DEVICE1 → DEVICE2 → DEVICE3 → DEVICE1<br/><br/>Affected Devices:<br/>- DEVICE1 IP1<br/>- DEVICE2 IP2<br/>- DEVICE3 IP3<br/><br/>Recommended Actions:<br/>1. Check STP config<br/>2. Verify port states<br/>3. Check bridge IDs]
    
    BuildCPUBody --> SetFrom[Set FROM Address:<br/>ALERT_EMAIL_FROM env var<br/>Default: alerts@netops.local]
    BuildLoopBody --> SetFrom
    
    SetFrom --> SetRecipients[Set TO Recipients:<br/>1. Command line --email args<br/>2. ALERT_EMAIL_RECIPIENTS env<br/>3. Email passed to monitor_health]
    
    SetRecipients --> ValidateRecipients{Recipients<br/>Valid?}
    
    ValidateRecipients -->|No| LogNoRecipients[Log: No recipients configured<br/>Skip email]
    ValidateRecipients -->|Yes| FormatMessage[Format Email Message:<br/>- Plain text<br/>- UTF-8 encoding<br/>- Standard MIME headers]
    
    LogNoRecipients --> End([End])
    
    FormatMessage --> AddMetadata[Add Metadata:<br/>- Message-ID<br/>- Date header<br/>- X-Priority: High for critical]
    
    AddMetadata --> SendToSMTP[Pass to Django<br/>send_mail Function]
    
    SendToSMTP --> End([Return Email Object])
    
    style Start fill:#90EE90
    style SendToSMTP fill:#87CEEB
    style LogNoRecipients fill:#FFA07A
```

---

## 🔧 **Configuration Flow**

```mermaid
flowchart TD
    Start([Application Start]) --> LoadEnv[Load .env File<br/>dotenv library]
    
    LoadEnv --> ReadEmailBackend[Read EMAIL_BACKEND:<br/>- console Development<br/>- smtp Production]
    
    ReadEmailBackend --> BackendType{Backend?}
    
    BackendType -->|console| ConfigConsole[Configure Console Backend:<br/>Print to stdout<br/>No SMTP needed]
    BackendType -->|smtp| ReadSMTPConfig[Read SMTP Configuration:<br/>- EMAIL_HOST<br/>- EMAIL_PORT<br/>- EMAIL_HOST_USER<br/>- EMAIL_HOST_PASSWORD<br/>- EMAIL_USE_TLS]
    
    ConfigConsole --> ReadRecipients
    
    ReadSMTPConfig --> ValidateConfig{All Required<br/>Fields Set?}
    
    ValidateConfig -->|No| WarnMissing[Warn: Incomplete config<br/>Emails will fail<br/>Check logs]
    ValidateConfig -->|Yes| TestConnection[Optional: Test Connection<br/>on startup<br/>Not blocking]
    
    WarnMissing --> ReadRecipients
    TestConnection --> ReadRecipients[Read Alert Recipients:<br/>ALERT_EMAIL_RECIPIENTS]
    
    ReadRecipients --> ParseRecipients[Parse Comma-Separated<br/>Email List]
    
    ParseRecipients --> ValidateEmails{Valid Email<br/>Addresses?}
    
    ValidateEmails -->|No| WarnInvalid[Warn: Invalid email format<br/>Skip invalid entries]
    ValidateEmails -->|Yes| StoreConfig[Store Configuration<br/>in Django settings]
    
    WarnInvalid --> StoreConfig
    
    StoreConfig --> ReadThresholds[Read Alert Thresholds:<br/>- CPU threshold<br/>- Cooldown periods]
    
    ReadThresholds --> Ready([Configuration Ready])
    
    style Start fill:#90EE90
    style Ready fill:#98FB98
    style WarnMissing fill:#FFA07A
    style WarnInvalid fill:#FFA07A
```

---

## 🎯 **Complete Alert Lifecycle**

```mermaid
sequenceDiagram
    participant Mon as Health Monitor
    participant SSH as SSH/Netmiko
    participant Dev as Network Device
    participant DB as Database
    participant Email as Email System
    participant SMTP as SMTP Server
    participant Admin as Admin Inbox
    
    Note over Mon: Start monitoring loop
    Mon->>SSH: Connect to device
    SSH->>Dev: show processes cpu
    Dev-->>SSH: CPU output: 85%
    SSH-->>Mon: Parsed: 85%
    
    Mon->>DB: Update DeviceHealth<br/>cpu_utilization=85
    
    Note over Mon: Check threshold (80%)
    Mon->>Mon: 85% > 80% = Alert!
    
    Mon->>DB: Check last alert time
    DB-->>Mon: Last alert: 20 min ago
    
    Note over Mon: Outside cooldown (15 min)
    
    Mon->>DB: Create HealthAlert<br/>category=cpu<br/>severity=critical
    DB-->>Mon: Alert ID created
    
    Mon->>Email: send_mail()<br/>Subject: High CPU Alert<br/>To: admin@example.com
    
    Email->>SMTP: Connect smtp.gmail.com:587
    SMTP-->>Email: 220 Ready
    
    Email->>SMTP: STARTTLS
    SMTP-->>Email: 220 Go ahead
    
    Email->>SMTP: AUTH LOGIN
    SMTP-->>Email: 235 Authenticated
    
    Email->>SMTP: MAIL FROM: alerts@netops.local
    Email->>SMTP: RCPT TO: admin@example.com
    Email->>SMTP: DATA (email body)
    SMTP-->>Email: 250 Message accepted
    
    Email->>SMTP: QUIT
    SMTP-->>Email: 221 Bye
    
    Email-->>Mon: Email sent successfully
    
    Mon->>DB: Update last_alert_time
    
    Note over SMTP,Admin: Email delivered
    SMTP->>Admin: [NetOps] High CPU Alert
    
    Note over Admin: Admin receives alert
    
    Note over Mon: Wait for interval (60s)
    
    Mon->>SSH: Connect to device again
    SSH->>Dev: show processes cpu
    Dev-->>SSH: CPU output: 75%
    SSH-->>Mon: Parsed: 75%
    
    Mon->>DB: Update DeviceHealth<br/>cpu_utilization=75
    
    Note over Mon: 75% < 80% = Clear!
    
    Mon->>DB: Find active alert
    DB-->>Mon: Alert ID found
    
    Mon->>DB: Set cleared_at = NOW
    DB-->>Mon: Alert cleared
    
    Mon->>Email: send_mail()<br/>Subject: CPU Normal<br/>To: admin@example.com
    
    Email->>SMTP: Send cleared notification
    SMTP->>Admin: [NetOps] CPU Normal
    
    Note over Admin: Alert resolved!
```

---

## 🚨 **Error Handling Flow**

```mermaid
flowchart TD
    Start([Email Send Attempt]) --> Try[Try: send_mail]
    
    Try --> Errors{Error Type?}
    
    Errors -->|SMTPAuthenticationError| AuthFail[Authentication Failed:<br/>- Wrong credentials<br/>- Need App Password<br/>- 2FA blocking]
    
    Errors -->|SMTPSenderRefused| SenderFail[Sender Refused:<br/>- FROM not verified<br/>- Relay denied<br/>- Domain issues]
    
    Errors -->|SMTPRecipientsRefused| RecipientFail[Recipients Refused:<br/>- Invalid email address<br/>- Mailbox full<br/>- Blocked by provider]
    
    Errors -->|Timeout| TimeoutFail[Connection Timeout:<br/>- Firewall blocking<br/>- SMTP server down<br/>- Network issues]
    
    Errors -->|ConnectionRefused| ConnRefused[Connection Refused:<br/>- Wrong port<br/>- SMTP disabled<br/>- TLS/SSL mismatch]
    
    Errors -->|No Error| Success[Email Sent Successfully]
    
    AuthFail --> LogError[Log Error with Details:<br/>- Error type<br/>- Error message<br/>- Configuration used]
    SenderFail --> LogError
    RecipientFail --> LogError
    TimeoutFail --> LogError
    ConnRefused --> LogError
    
    LogError --> CheckFailSilently{fail_silently<br/>= True?}
    
    CheckFailSilently -->|Yes| Continue[Continue Execution<br/>Don't crash monitor]
    CheckFailSilently -->|No| Raise[Raise Exception<br/>Stop execution]
    
    Success --> LogSuccess[Log: Email sent<br/>- Recipients<br/>- Timestamp]
    
    Continue --> NotifyOps[Optional: Notify Ops<br/>via alternative channel<br/>SMS, Slack, PagerDuty]
    
    LogSuccess --> UpdateMetrics[Update Success Metrics]
    NotifyOps --> UpdateMetrics[Update Failure Metrics]
    
    UpdateMetrics --> End([End])
    Raise --> End
    
    style Start fill:#90EE90
    style Success fill:#98FB98
    style AuthFail fill:#FF6B6B
    style SenderFail fill:#FF6B6B
    style TimeoutFail fill:#FF6B6B
    style LogSuccess fill:#87CEEB
```

---

## 📊 **Alert Metrics & Monitoring**

```mermaid
flowchart TD
    Start([Alert Event]) --> RecordMetric[Record Metric:<br/>- Alert type<br/>- Device<br/>- Timestamp<br/>- Success/Failure]
    
    RecordMetric --> UpdateCounters[Update Counters:<br/>- Total alerts<br/>- Email sent<br/>- Email failed]
    
    UpdateCounters --> CalculateRates[Calculate Rates:<br/>- Alerts per hour<br/>- Email success rate<br/>- Average response time]
    
    CalculateRates --> CheckThresholds{Metrics Exceed<br/>Thresholds?}
    
    CheckThresholds -->|Too Many Alerts| AlertFlood[Alert Flood Detected:<br/>- >10 alerts/min<br/>- Possible alert storm<br/>- Throttle alerts]
    
    CheckThresholds -->|High Failure Rate| EmailIssue[Email System Issue:<br/>- >50% failures<br/>- Check SMTP config<br/>- Switch to fallback]
    
    CheckThresholds -->|Normal| Continue[Continue Normal<br/>Operation]
    
    AlertFlood --> ThrottleAlerts[Enable Throttling:<br/>- Max 5 alerts/device/hour<br/>- Batch similar alerts<br/>- Notify admin]
    
    EmailIssue --> SwitchBackup[Switch to Backup:<br/>- Use console logging<br/>- Try alternative SMTP<br/>- Notify admin]
    
    ThrottleAlerts --> LogAction[Log Action Taken]
    SwitchBackup --> LogAction
    Continue --> LogMetrics[Log Metrics to:<br/>- Database<br/>- Time-series DB<br/>- Log file]
    
    LogAction --> LogMetrics
    
    LogMetrics --> ExportMetrics[Export to:<br/>- Prometheus<br/>- Grafana<br/>- CloudWatch]
    
    ExportMetrics --> End([End])
    
    style Start fill:#90EE90
    style AlertFlood fill:#FFA07A
    style EmailIssue fill:#FFA07A
    style ExportMetrics fill:#87CEEB
```

---

## 🔐 **Security & Privacy Flow**

```mermaid
flowchart TD
    Start([Email Alert Process]) --> CheckSensitive[Check for Sensitive Data:<br/>- Passwords<br/>- API keys<br/>- Credentials]
    
    CheckSensitive --> MaskData[Mask Sensitive Data:<br/>- Hash values<br/>- Truncate strings<br/>- Remove secrets]
    
    MaskData --> Encrypt{Encryption<br/>Enabled?}
    
    Encrypt -->|Yes| EncryptBody[Encrypt Email Body:<br/>- PGP/GPG<br/>- S/MIME<br/>- TLS in transit]
    Encrypt -->|No| PlainText[Send as Plain Text<br/>over TLS]
    
    EncryptBody --> CheckRecipients[Validate Recipients:<br/>- Authorized users only<br/>- Check whitelist<br/>- Verify domains]
    PlainText --> CheckRecipients
    
    CheckRecipients --> AuthCheck{Recipients<br/>Authorized?}
    
    AuthCheck -->|No| BlockEmail[Block Email:<br/>Log security violation<br/>Alert security team]
    AuthCheck -->|Yes| LogAccess[Log Access:<br/>- Who received alert<br/>- When<br/>- What data]
    
    BlockEmail --> SecurityAlert[Send Security Alert:<br/>Unauthorized access attempt]
    
    LogAccess --> CheckCompliance{Compliance<br/>Requirements?}
    
    CheckCompliance -->|Yes| AuditLog[Store in Audit Log:<br/>- Immutable log<br/>- Tamper-proof<br/>- Long-term retention]
    CheckCompliance -->|No| StandardLog[Store in Standard Log]
    
    AuditLog --> SendEmail[Send Email via<br/>Secure Channel]
    StandardLog --> SendEmail
    
    SendEmail --> VerifyDelivery[Verify Delivery:<br/>- Check SMTP response<br/>- Track message ID<br/>- Confirm receipt]
    
    VerifyDelivery --> CleanupMemory[Cleanup Memory:<br/>- Clear sensitive data<br/>- Destroy temp files<br/>- Zero out buffers]
    
    SecurityAlert --> End([End])
    CleanupMemory --> End
    
    style Start fill:#90EE90
    style BlockEmail fill:#FF6B6B
    style SecurityAlert fill:#FF6B6B
    style EncryptBody fill:#87CEEB
    style AuditLog fill:#87CEEB
```

---

## 📝 **Summary of Alert Types**

| Alert Type | Trigger | Cooldown | Auto-Clear | Email Subject |
|------------|---------|----------|------------|---------------|
| **CPU High** | CPU > 80% (configurable) | 15 minutes | Yes, when CPU < threshold | `[NetOps] High CPU Alert - DEVICE` |
| **Network Loop** | Loop detected in topology | 15 minutes | Yes, when loop resolves | `[NetOps] Possible Loop Detected` |
| **Device Down** | Connection timeout | 10 minutes | Yes, when device responds | `[NetOps] Device Unreachable - DEVICE` |
| **Health Check Fail** | Monitor process error | 5 minutes | No (manual) | `[NetOps] Health Monitor Error` |

---

## 🎯 **Key Decision Points in Flowcharts**

1. **Alert Cooldown Check**: Prevents alert spam by enforcing minimum time between alerts
2. **Email Backend Selection**: Determines console (dev) vs SMTP (prod) delivery
3. **Configuration Validation**: Ensures all required settings before attempting send
4. **Loop Deduplication**: Uses canonical signature to prevent duplicate loop alerts
5. **Error Handling**: Graceful degradation with fail_silently=True
6. **Auto-Clear Logic**: Automatically clears alerts when conditions normalize

---

## 💡 **How to Read These Flowcharts**

- **Green boxes**: Start/success states
- **Red/Pink boxes**: Alert conditions or email actions
- **Blue boxes**: Data processing or logging
- **Orange boxes**: Warning/error conditions
- **Diamond shapes**: Decision points
- **Rounded boxes**: External systems (SMTP, database)

---

## 🔗 **Related Documentation**

- **Email Setup**: `Backend/EMAIL_SETUP_GUIDE.md`
- **Configuration**: `Backend/EMAIL_CONFIGURATION_SUMMARY.md`
- **Testing**: Run `python Backend/netops_backend/test_email.py`
- **Monitor Command**: `python manage.py monitor_health --help`

---

**Generated:** October 18, 2025  
**Version:** 1.0  
**Status:** Complete and ready for implementation
