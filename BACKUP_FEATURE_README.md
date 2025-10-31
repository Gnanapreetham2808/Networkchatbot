# Device Backup & Management Features

This branch (`feature/device-backup-and-config`) adds comprehensive device backup and management capabilities to the Network Chatbot.

## ✨ New Features

### 1. **Device Configuration Backup**
- Automated backup of device configurations
- Supports multiple vendors (Cisco, Aruba, Juniper, HPE)
- Dual format output: JSON (structured) and TXT (human-readable)
- Backup history tracking
- Download backups directly from UI

### 2. **Device Management**
- Add new devices via UI
- Configure device details (IP, credentials, vendor, model)
- Visual device inventory
- Support for multiple device types and roles

## 📁 Files Added/Modified

### Backend
- **New:** `Backend/netops_backend/chatbot/device_backup_manager.py`
  - Core backup logic
  - Netmiko connection handling
  - Vendor-specific command mapping
  - JSON and TXT file generation

- **Modified:** `Backend/netops_backend/chatbot/views.py`
  - `DeviceBackupAPIView` - Create and list backups
  - `BackupDetailsAPIView` - Get specific backup data
  - `DeviceManagementAPIView` - Add/list devices

- **Modified:** `Backend/netops_backend/chatbot/urls.py`
  - `/api/nlp/backup/` - Backup endpoints
  - `/api/nlp/device-management/` - Device CRUD

### Frontend
- **New:** `Frontend/src/app/backup/page.tsx`
  - Device backup interface
  - Backup history list
  - Download JSON/TXT files
  - Filter by device

- **New:** `Frontend/src/app/device-management/page.tsx`
  - Add device form
  - Device inventory cards
  - Vendor/model configuration

- **Modified:** `Frontend/src/components/SiteHeader.tsx`
  - Added "Backups" and "Devices" nav links

### Configuration
- **Modified:** `.gitignore`
  - Excludes backup directories from version control

## 🚀 Getting Started

### 1. **Start Django Server**
```powershell
cd C:\Networkchatbot\Backend\netops_backend
python manage.py runserver
```

### 2. **Start Frontend**
```powershell
cd C:\Networkchatbot\Frontend
npm run dev
```

### 3. **Access Features**
- Backups: http://localhost:3000/backup
- Device Management: http://localhost:3000/device-management

## 📡 API Endpoints

### Device Backup
```http
# List all backups
GET /api/nlp/backup/

# List backups for specific device
GET /api/nlp/backup/?device=INVIJB1C01

# Create backup for single device
POST /api/nlp/backup/
Content-Type: application/json
{
  "device": "INVIJB1C01"
}

# Create backup for all devices
POST /api/nlp/backup/
Content-Type: application/json
{
  "backup_all": true
}

# Get backup details
GET /api/nlp/backup/<filename>/
```

### Device Management
```http
# List all devices
GET /api/nlp/device-management/

# Add new device
POST /api/nlp/device-management/
Content-Type: application/json
{
  "alias": "NEW-SW-01",
  "host": "192.168.1.100",
  "username": "admin",
  "password": "password123",
  "device_type": "cisco_ios",
  "vendor": "cisco",
  "model": "WS-C3650-24TS",
  "location": "London DC",
  "role": "access"
}
```

## 🧪 Testing

### Backend Tests
```powershell
# Test device listing
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/nlp/device-management/"

# Test backup creation
$body = @{device="INVIJB1C01"} | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/nlp/backup/" `
  -ContentType "application/json" -Body $body

# Test backup listing
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/nlp/backup/"
```

### Frontend Tests
1. Navigate to http://localhost:3000/backup
2. Select a device from dropdown
3. Click "Create Backup"
4. Verify backup appears in history
5. Click "Download JSON" or "Download TXT"

## 📂 Backup File Locations

```
Backend/backups/
├── json/           # Structured JSON backups
│   └── DEVICE_20250101_120000.json
└── txt/            # Human-readable text reports
    └── DEVICE_20250101_120000.txt
```

## 🔧 Vendor-Specific Commands

### Cisco IOS/IOS-XE
- `show running-config`
- `show startup-config`
- `show version`
- `show ip interface brief`
- `show vlan brief`
- `show inventory`

### Aruba AOS-CX
- `show running-config`
- `show startup-config`
- `show version`
- `show interface brief`
- `show vlan`

### Aruba ProVision (AOS)
- `show running-config`
- `show version`
- `show ip interface brief`
- `show vlan`

### Juniper JunOS
- `show configuration`
- `show version`
- `show interfaces terse`
- `show vlans`

### HPE Comware
- `display current-configuration`
- `display saved-configuration`
- `display version`
- `display ip interface brief`
- `display vlan`

## 🛠️ Configuration Options

### Add Device via UI
1. Go to Device Management page
2. Click "Add Device"
3. Fill in required fields:
   - **Alias:** Unique identifier (e.g., CORE-SW-01)
   - **IP Address:** Management IP
   - **Username:** SSH username
   - **Password:** SSH password
4. Select optional fields:
   - **Vendor:** Cisco, Aruba, Juniper, HPE
   - **Device Type:** Specific OS version
   - **Model:** Hardware model
   - **Location:** Physical location
   - **Role:** Core, Distribution, Access
5. Click "Add Device"

### Add Device via API
```bash
curl -X POST http://127.0.0.1:8000/api/nlp/device-management/ \
  -H "Content-Type: application/json" \
  -d '{
    "alias": "ACCESS-SW-01",
    "host": "192.168.1.10",
    "username": "admin",
    "password": "cisco123",
    "device_type": "cisco_ios",
    "vendor": "cisco",
    "model": "WS-C2960X-24TS",
    "location": "Building A",
    "role": "access"
  }'
```

## 📊 Backup Output Formats

### JSON Format
```json
{
  "snapshot_info": {
    "hostname": "INVIJB1C01",
    "ip_address": "192.168.10.1",
    "platform": "cisco_ios",
    "timestamp": "2025-10-31T12:00:00",
    "collector": "Device Backup Manager"
  },
  "configs": {
    "running_config": "...",
    "startup_config": "...",
    "version": "...",
    "interfaces": "...",
    "vlans": "...",
    "inventory": "..."
  },
  "status": "success",
  "files": [
    "/path/to/backup.json",
    "/path/to/backup.txt"
  ]
}
```

### TXT Format
```
================================================================================
NETWORK DEVICE CONFIGURATION BACKUP
================================================================================

Device:          INVIJB1C01
IP Address:      192.168.10.1
Device Type:     cisco_ios
Backup Time:     2025-10-31T12:00:00
Status:          SUCCESS

================================================================================
SECTION: RUNNING CONFIGURATION
================================================================================

Building configuration...

Current configuration : 12345 bytes
!
! Last configuration change at 12:00:00 UTC Thu Oct 31 2025
...

================================================================================
SECTION: VERSION
================================================================================

Cisco IOS Software, C3650 Software (C3650-UNIVERSALK9-M), Version 15.2(4)E8
...

================================================================================
END OF BACKUP
================================================================================
```

## 🔒 Security Notes

1. **Backup files are excluded from Git** via `.gitignore`
2. **Credentials are stored in `Devices/devices.json`** (ensure this is also in `.gitignore`)
3. **Use environment variables** for sensitive data in production
4. **Implement access control** for backup endpoints
5. **Consider encrypting backup files** for sensitive environments

## 🐛 Troubleshooting

### "Connection timeout" error
- Verify device IP is reachable: `ping <device_ip>`
- Check firewall rules
- Verify SSH (port 22) is enabled on device

### "Authentication failed" error
- Verify username/password in `Devices/devices.json`
- Check if enable password is required
- Verify SSH key authentication if used

### "Template not found" error
- Install ntc-templates: `pip install ntc-templates`
- Update textfsm templates if vendor support missing

### Backup files not appearing
- Check `Backend/backups/json/` and `Backend/backups/txt/` directories exist
- Verify write permissions on backup directories
- Check Django logs for errors

## 📝 Next Steps

### Phase 1 (Current)
- ✅ Basic backup functionality
- ✅ Device management UI
- ✅ JSON and TXT formats

### Phase 2 (Future)
- ⏳ Scheduled automated backups
- ⏳ Backup comparison/diff view
- ⏳ Configuration restore functionality
- ⏳ Backup retention policies
- ⏳ Email notifications for backup status

### Phase 3 (Future)
- ⏳ Multi-site backup management
- ⏳ Backup encryption
- ⏳ Compliance reporting
- ⏳ Change detection and alerts
- ⏳ Integration with version control (GitOps)

## 🤝 Contributing

When adding new vendor support:
1. Add vendor-specific commands to `BACKUP_COMMANDS` dict in `device_backup_manager.py`
2. Test with real device or mock data
3. Update this README with new vendor documentation

## 📄 License

Same as parent project

---

**Branch:** `feature/device-backup-and-config`  
**Created:** October 31, 2025  
**Status:** ✅ Ready for testing
