# Email Configuration Summary

## 📧 What Was Added

I've configured email notification support for your Network Chatbot health monitoring system.

---

## ✅ Files Modified/Created

### 1. **Django Settings** (`Backend/netops_backend/netops_backend/settings.py`)
   - Added email configuration section
   - SMTP backend support (Gmail, Outlook, SendGrid, AWS SES, etc.)
   - Configurable via environment variables

### 2. **Environment Files**
   - **`.env`** - Updated with email configuration (empty credentials - ready for you to fill)
   - **`.env.example`** - Updated with email configuration template and examples

### 3. **Documentation** (`Backend/EMAIL_SETUP_GUIDE.md`)
   - Comprehensive 500+ line guide
   - Step-by-step setup for Gmail, Outlook, SendGrid, AWS SES
   - Troubleshooting section
   - Security best practices
   - Production deployment examples

### 4. **Test Script** (`Backend/netops_backend/test_email.py`)
   - Interactive email testing tool
   - Tests both console and SMTP backends
   - Validates configuration

---

## 🚀 Quick Start Guide

### Step 1: Choose Email Provider

**For Testing (Easiest):** Gmail with App Password

**For Production:** SendGrid or AWS SES

### Step 2: Configure `.env` File

```bash
# Backend/.env

# Switch to SMTP backend
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Gmail Configuration (example)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App Password (16 chars)

# Alert Settings
DEFAULT_FROM_EMAIL=your-email@gmail.com
ALERT_EMAIL_FROM=your-email@gmail.com
ALERT_EMAIL_RECIPIENTS=admin@example.com,ops-team@example.com
```

### Step 3: Get Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate password for "Mail" → "Other (Network Chatbot)"
5. Copy the 16-character password to `.env`

### Step 4: Test Configuration

```powershell
cd Backend\netops_backend
python test_email.py
```

This interactive script will:
- Show your current email configuration
- Test sending an email
- Provide troubleshooting tips

### Step 5: Start Health Monitoring with Alerts

```powershell
cd Backend\netops_backend
python manage.py monitor_health --interval 60 --cpu-threshold 80 --email admin@example.com
```

---

## 📧 What Alerts Will Be Sent

### 1. **CPU Threshold Alerts**
When device CPU exceeds configured threshold (default: 80%)

**Example Email:**
```
Subject: [NetOps] High CPU Alert - INVIJB1SW1

Device: INVIJB1SW1 (10.1.5.20)
Alert: CPU at 85%
Threshold: 80%
Time: 2025-10-18 11:30:45 UTC

This alert will auto-clear when CPU drops below threshold.
```

**Features:**
- Cooldown period: Won't spam (15-minute default)
- Auto-clears when CPU normalizes
- Includes device details and timestamp

### 2. **Network Loop Detection Alerts**
When CDP/LLDP topology analysis detects potential loops

**Example Email:**
```
Subject: [NetOps] Possible Network Loop Detected

Potential loop detected:

Loop Path: INVIJB1SW1 -> INVIJB1SW2 -> INVIJB1SW3 -> INVIJB1SW1

Recommended Actions:
1. Check STP configuration
2. Verify port states
3. Check for duplicate bridge IDs
```

**Features:**
- Topology-aware detection
- Path visualization
- Auto-clears when loop resolves

---

## 🔧 Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EMAIL_BACKEND` | `console` | Backend type: `console` or `smtp` |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server hostname |
| `EMAIL_PORT` | `587` | SMTP port (587 for TLS, 465 for SSL) |
| `EMAIL_USE_TLS` | `1` | Enable TLS (1=yes, 0=no) |
| `EMAIL_USE_SSL` | `0` | Enable SSL (1=yes, 0=no) |
| `EMAIL_HOST_USER` | - | SMTP username (email address) |
| `EMAIL_HOST_PASSWORD` | - | SMTP password or App Password |
| `EMAIL_TIMEOUT` | `10` | Connection timeout in seconds |
| `DEFAULT_FROM_EMAIL` | `netops-alerts@example.com` | Default sender email |
| `ALERT_EMAIL_FROM` | `netops-alerts@example.com` | Alert sender email |
| `ALERT_EMAIL_RECIPIENTS` | - | Comma-separated recipient list |

### Health Monitoring Command Options

```bash
python manage.py monitor_health [OPTIONS]

Options:
  --interval SECONDS       Polling interval (default: 60)
  --cpu-threshold PERCENT  CPU alert threshold (default: 80)
  --email EMAIL           Alert recipient (can use multiple times)
  --loop-cooldown SECONDS Loop alert cooldown (default: 900)
  --cpu-cooldown SECONDS  CPU alert cooldown (default: 900)
```

**Examples:**

```powershell
# Basic monitoring with email alerts
python manage.py monitor_health --email admin@example.com

# Custom thresholds and intervals
python manage.py monitor_health --interval 30 --cpu-threshold 70 --email ops@example.com

# Multiple recipients
python manage.py monitor_health --email admin1@example.com --email admin2@example.com --email ops-team@example.com
```

---

## 🎯 Supported Email Providers

### 1. **Gmail** (Best for Testing)
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App Password
```
✅ Free, reliable, easy setup  
⚠️ Requires App Password (2FA)

### 2. **Outlook/Office 365**
```bash
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```
✅ Business-friendly, good deliverability  
⚠️ May need to enable SMTP AUTH

### 3. **SendGrid** (Best for Production)
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=apikey  # Literally "apikey"
EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxx  # API Key
```
✅ Free tier: 100 emails/day  
✅ High deliverability, analytics  
✅ No ISP blocking

### 4. **AWS SES** (Enterprise)
```bash
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=AKIAIOSFODNN7EXAMPLE
EMAIL_HOST_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```
✅ Scalable, cheap ($0.10 per 1000 emails)  
✅ AWS integration  
⚠️ Requires verified domain

---

## 🧪 Testing Checklist

- [ ] `.env` file updated with email credentials
- [ ] Email provider credentials verified (App Password for Gmail)
- [ ] Test script executed: `python test_email.py`
- [ ] Test email received in inbox (check spam folder)
- [ ] Recipients configured in `ALERT_EMAIL_RECIPIENTS`
- [ ] Health monitoring started with `--email` flag
- [ ] CPU alert tested (manually create alert or wait for real alert)
- [ ] Loop detection tested (if applicable)
- [ ] Email backend set to `smtp` (not `console`) for production

---

## 🔐 Security Notes

### ⚠️ IMPORTANT: Never Commit Credentials

Your `.env` file is already in `.gitignore`, but double-check:

```bash
# Verify .env is ignored
git status

# Should NOT show .env file
```

### Use App Passwords (Gmail)

**Never use your regular Gmail password!**

- Regular password won't work with 2FA
- App Passwords are 16 characters: `xxxx-xxxx-xxxx-xxxx`
- Generate at: https://myaccount.google.com/apppasswords

### Rotate Credentials Regularly

- Change email passwords every 90 days
- Rotate API keys (SendGrid/AWS) quarterly
- Monitor for suspicious activity

### Consider Secrets Management

For production, use:
- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**

Example:
```python
import boto3
secrets = boto3.client('secretsmanager')
password = secrets.get_secret_value(SecretId='netops/email')['SecretString']
```

---

## 🐛 Common Issues & Solutions

### Issue: "SMTPAuthenticationError: Username and Password not accepted"

**Cause:** Wrong credentials or 2FA blocking

**Solution:**
- Gmail: Use App Password (not regular password)
- Outlook: Enable SMTP AUTH in admin settings
- Verify username is correct (usually your email address)

### Issue: Email goes to spam

**Solution:**
- Use verified domain email (not gmail.com for business)
- Add SPF/DKIM records to your domain
- Use dedicated service (SendGrid/AWS SES)

### Issue: "Connection timed out"

**Solution:**
- Check firewall allows outbound SMTP (port 587)
- Try port 465 with SSL: `EMAIL_USE_SSL=1, EMAIL_USE_TLS=0`
- Test with: `telnet smtp.gmail.com 587`

### Issue: No emails received

**Solution:**
1. Check console output for errors
2. Verify `EMAIL_BACKEND=smtp` (not `console`)
3. Check spam folder
4. Run test script: `python test_email.py`
5. Review logs: `cat Backend/logs/netops.log | grep email`

---

## 📚 Additional Resources

### Documentation
- **Full Setup Guide:** `Backend/EMAIL_SETUP_GUIDE.md` (500+ lines)
- **Django Email Docs:** https://docs.djangoproject.com/en/stable/topics/email/
- **Gmail App Passwords:** https://support.google.com/accounts/answer/185833
- **SendGrid SMTP:** https://docs.sendgrid.com/for-developers/sending-email/integrating-with-the-smtp-api

### Testing Tools
- **Test Script:** `python Backend/netops_backend/test_email.py`
- **Mail Tester:** https://www.mail-tester.com/ (check deliverability)
- **MXToolbox:** https://mxtoolbox.com/ (DNS checker)

---

## 🎉 Next Steps

1. **Set up email credentials** in `.env` (start with Gmail for testing)
2. **Run test script:** `python test_email.py`
3. **Start health monitoring:** `python manage.py monitor_health --email your-email@example.com`
4. **Monitor alerts** in your inbox
5. **Switch to production provider** (SendGrid/AWS SES) when ready

---

## 📞 Support

For detailed setup instructions, troubleshooting, and production deployment:

👉 **See `Backend/EMAIL_SETUP_GUIDE.md`**

**Questions?** Check the troubleshooting section or Django's email documentation.

---

**Status:** ✅ Email configuration complete and ready to use!
