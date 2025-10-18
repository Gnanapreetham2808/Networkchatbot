# Email Configuration Guide for Network Chatbot

This guide explains how to configure email notifications for the Network Chatbot health monitoring system.

## 📧 Overview

The health monitoring system (`monitor_health.py`) can send email alerts for:
- **CPU Threshold Alerts**: When device CPU exceeds configured threshold (default: 80%)
- **Loop Detection Alerts**: When network loops are detected via CDP/LLDP

## 🚀 Quick Setup

### Step 1: Choose Your Email Provider

The system supports any SMTP server. Common options:

| Provider | SMTP Server | Port | TLS/SSL |
|----------|-------------|------|---------|
| **Gmail** | smtp.gmail.com | 587 | TLS |
| **Outlook/Office 365** | smtp.office365.com | 587 | TLS |
| **Yahoo Mail** | smtp.mail.yahoo.com | 587 | TLS |
| **SendGrid** | smtp.sendgrid.net | 587 | TLS |
| **AWS SES** | email-smtp.us-east-1.amazonaws.com | 587 | TLS |
| **Custom SMTP** | your-smtp-server | 587/465 | TLS/SSL |

---

## 📝 Configuration Methods

### Method 1: Gmail (Recommended for Testing)

#### 1.1 Enable App Password in Gmail

**Important:** Regular Gmail passwords won't work due to 2FA. You need an **App Password**.

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** and **Other (Custom name)** → Name it "Network Chatbot"
5. Click **Generate** → Copy the 16-character password

#### 1.2 Update Your `.env` File

```bash
# Backend/.env

# Email Backend (use smtp for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Gmail SMTP Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx  # 16-char App Password
EMAIL_TIMEOUT=10

# From Address
DEFAULT_FROM_EMAIL=your-email@gmail.com
ALERT_EMAIL_FROM=your-email@gmail.com

# Recipients (comma-separated)
ALERT_EMAIL_RECIPIENTS=admin@example.com,ops-team@example.com
```

---

### Method 2: Outlook/Office 365

```bash
# Backend/.env

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Outlook SMTP Configuration
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password-here
EMAIL_TIMEOUT=10

DEFAULT_FROM_EMAIL=your-email@outlook.com
ALERT_EMAIL_FROM=your-email@outlook.com
ALERT_EMAIL_RECIPIENTS=admin@example.com,ops@example.com
```

**Note:** For Office 365, you may need to enable SMTP AUTH:
1. Go to [Microsoft 365 Admin Center](https://admin.microsoft.com)
2. **Users** → **Active users** → Select user
3. **Mail** tab → **Manage email apps**
4. Enable **Authenticated SMTP**

---

### Method 3: SendGrid (Production-Ready)

**Why SendGrid?**
- Free tier: 100 emails/day
- High deliverability
- No ISP blocking concerns
- Detailed analytics

#### 3.1 Setup SendGrid

1. Sign up at [SendGrid.com](https://sendgrid.com/)
2. Go to **Settings** → **API Keys**
3. Create API Key with **Mail Send** permissions
4. Copy the API key (starts with `SG.`)

#### 3.2 Configure SendGrid

```bash
# Backend/.env

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# SendGrid SMTP Configuration
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_HOST_USER=apikey  # Literally the string "apikey"
EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Your API key
EMAIL_TIMEOUT=10

DEFAULT_FROM_EMAIL=alerts@yourdomain.com
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_RECIPIENTS=admin@example.com,ops@example.com
```

**Important:** Verify your sender email in SendGrid dashboard for production use.

---

### Method 4: AWS SES (Enterprise)

**Best for:** High-volume, production workloads

#### 4.1 Setup AWS SES

1. Go to [AWS SES Console](https://console.aws.amazon.com/ses/)
2. **Verified identities** → Verify your email/domain
3. **SMTP Settings** → Create SMTP credentials
4. Note your SMTP username and password

#### 4.2 Configure AWS SES

```bash
# Backend/.env

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# AWS SES Configuration (us-east-1 example)
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_HOST_USER=AKIAIOSFODNN7EXAMPLE  # SMTP username from SES
EMAIL_HOST_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY  # SMTP password
EMAIL_TIMEOUT=10

DEFAULT_FROM_EMAIL=alerts@yourdomain.com
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_RECIPIENTS=admin@example.com,ops@example.com
```

**Production Tips:**
- Move SES out of sandbox mode (submit AWS support request)
- Use verified domain for better deliverability
- Monitor bounce/complaint rates

---

## 🧪 Testing Email Configuration

### Test 1: Django Shell Test

```powershell
cd Backend\netops_backend
python manage.py shell
```

```python
from django.core.mail import send_mail

# Send test email
send_mail(
    subject='Test Email from Network Chatbot',
    message='This is a test email. If you receive this, email configuration is working!',
    from_email='your-email@gmail.com',
    recipient_list=['recipient@example.com'],
    fail_silently=False,
)

# If successful, you'll see: 1
# If failed, you'll see an error message
```

### Test 2: Health Monitoring Alert Test

```powershell
# Start health monitoring with CPU threshold
cd Backend\netops_backend
python manage.py monitor_health --interval 60 --cpu-threshold 80 --email admin@example.com
```

**Trigger a test alert:**
1. Manually create a high CPU alert in Django shell:
```python
from chatbot.models import HealthAlert
HealthAlert.objects.create(
    alias='TEST_DEVICE',
    category='cpu',
    severity='critical',
    message='TEST: CPU at 95%'
)
```

2. Check your email inbox for the alert

---

## 🔧 Troubleshooting

### Issue 1: "SMTPAuthenticationError"

**Cause:** Wrong username/password or 2FA blocking

**Solutions:**
- **Gmail:** Use App Password, not regular password
- **Outlook:** Enable SMTP AUTH in admin settings
- **SendGrid:** Username must be exactly `apikey`

### Issue 2: "SMTPSenderRefused" / "550 Relay Denied"

**Cause:** FROM address not verified

**Solutions:**
- Verify sender email in your provider dashboard
- Use the same email for `EMAIL_HOST_USER` and `DEFAULT_FROM_EMAIL`

### Issue 3: Connection Timeout

**Cause:** Firewall blocking port 587/465

**Solutions:**
- Check firewall allows outbound SMTP (port 587)
- Try port 465 with `EMAIL_USE_SSL=1` and `EMAIL_USE_TLS=0`
- Test with telnet: `telnet smtp.gmail.com 587`

### Issue 4: Emails Going to Spam

**Solutions:**
- Use verified domain (not gmail.com for business emails)
- Add SPF/DKIM records to your domain DNS
- Use dedicated email service (SendGrid/AWS SES)

### Issue 5: "No module named 'django.core.mail'"

**Cause:** Missing Django installation

**Solution:**
```powershell
pip install django
```

---

## 🎯 Development vs Production

### Development Setup (Console Backend)

For testing without sending real emails:

```bash
# Backend/.env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Emails will be printed to console:

```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Subject: [NetOps] High CPU on INVIJB1SW1
From: alerts@netops.local
To: admin@example.com

CPU at 85% on device INVIJB1SW1
```

### Production Setup (SMTP Backend)

```bash
# Backend/.env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
# ... rest of SMTP config
```

---

## 📊 Monitoring Email Delivery

### Check Django Logs

```powershell
# View email-related logs
cat Backend\logs\netops.log | Select-String "send_mail|email"
```

### Check Email Provider Dashboard

- **Gmail:** Check sent items
- **SendGrid:** Dashboard → Activity → Recent Activity
- **AWS SES:** CloudWatch → SES Metrics

---

## 🔐 Security Best Practices

### 1. Use Environment Variables (Never Hardcode)

✅ **Good:**
```bash
# .env file
EMAIL_HOST_PASSWORD=your-password
```

❌ **Bad:**
```python
# settings.py
EMAIL_HOST_PASSWORD = "my-password-123"  # NEVER DO THIS
```

### 2. Use App Passwords / API Keys

- **Gmail:** App Passwords (16 characters)
- **SendGrid:** API Keys (starts with `SG.`)
- **AWS SES:** IAM user with SES-only permissions

### 3. Rotate Credentials Regularly

- Change email passwords every 90 days
- Rotate API keys quarterly
- Monitor access logs

### 4. Encrypt Sensitive Data

For production, consider using:
- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**

```python
# Example: Load password from Vault
import boto3
secrets = boto3.client('secretsmanager')
email_password = secrets.get_secret_value(SecretId='netops/email')['SecretString']
```

---

## 📧 Email Templates

### CPU Alert Email

```
Subject: [NetOps] High CPU Alert - INVIJB1SW1

Device: INVIJB1SW1 (10.1.5.20)
Location: Vijayawada Building 1
Alert: CPU at 85%
Threshold: 80%
Time: 2025-10-18 11:30:45 UTC

Action Required:
1. Check running processes: show processes cpu sorted
2. Investigate high-CPU tasks
3. Consider device upgrade if sustained

This alert will auto-clear when CPU drops below threshold.
```

### Loop Detection Email

```
Subject: [NetOps] Possible Network Loop Detected

Potential loop detected in network topology:

Loop Path: INVIJB1SW1 -> INVIJB1SW2 -> INVIJB1SW3 -> INVIJB1SW1

Affected Devices:
- INVIJB1SW1 (10.1.5.20)
- INVIJB1SW2 (10.1.5.21)
- INVIJB1SW3 (10.1.5.22)

Recommended Actions:
1. Check STP configuration: show spanning-tree
2. Verify port states and root bridge
3. Check for duplicate bridge IDs

Time Detected: 2025-10-18 11:35:12 UTC
```

---

## 🚀 Production Deployment

### Docker Deployment

Update `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
      - EMAIL_HOST=smtp.sendgrid.net
      - EMAIL_PORT=587
      - EMAIL_USE_TLS=1
      - EMAIL_HOST_USER=apikey
      - EMAIL_HOST_PASSWORD=${EMAIL_PASSWORD}  # From .env file
      - ALERT_EMAIL_RECIPIENTS=admin@example.com,ops@example.com
```

### Kubernetes Deployment

Create secret:

```bash
kubectl create secret generic email-config \
  --from-literal=host=smtp.sendgrid.net \
  --from-literal=user=apikey \
  --from-literal=password=SG.xxxxxxxxxx
```

Update deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: netops-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        - name: EMAIL_HOST
          valueFrom:
            secretKeyRef:
              name: email-config
              key: host
        - name: EMAIL_HOST_PASSWORD
          valueFrom:
            secretKeyRef:
              name: email-config
              key: password
```

---

## 📞 Support & Resources

### Documentation
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [SendGrid SMTP Guide](https://docs.sendgrid.com/for-developers/sending-email/integrating-with-the-smtp-api)
- [AWS SES SMTP Guide](https://docs.aws.amazon.com/ses/latest/dg/send-email-smtp.html)

### Testing Tools
- [Mail-Tester.com](https://www.mail-tester.com/) - Check email deliverability
- [MXToolbox](https://mxtoolbox.com/) - DNS/SPF/DKIM checker

### Alternative Email Services
- **Mailgun** - Developer-friendly, pay-as-you-go
- **Postmark** - High deliverability, transactional focus
- **Brevo (Sendinblue)** - Free tier, marketing + transactional

---

## ✅ Configuration Checklist

Before enabling email alerts in production:

- [ ] Email provider account created
- [ ] SMTP credentials generated (App Password/API Key)
- [ ] `.env` file updated with credentials
- [ ] Test email sent successfully
- [ ] Sender email verified (if required by provider)
- [ ] Recipient emails added to `ALERT_EMAIL_RECIPIENTS`
- [ ] Email backend set to `smtp` (not console)
- [ ] Firewall allows outbound SMTP (port 587)
- [ ] Email credentials stored securely (not committed to Git)
- [ ] Production monitoring dashboard set up

---

**Ready to enable email alerts?** Start with Gmail for testing, then switch to SendGrid/AWS SES for production!

**Questions?** Check the troubleshooting section or review Django's email documentation.
