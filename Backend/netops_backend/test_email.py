"""
Email Configuration Test Script

This script helps you test your email configuration for the Network Chatbot.
It will send a test email and verify that your SMTP settings are correct.

Usage:
    python test_email.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for Django imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netops_backend.settings')

# Setup Django
import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings


def print_config():
    """Print current email configuration (without passwords)."""
    print("\n" + "="*70)
    print("CURRENT EMAIL CONFIGURATION")
    print("="*70)
    print(f"Email Backend:       {settings.EMAIL_BACKEND}")
    print(f"SMTP Host:           {settings.EMAIL_HOST}")
    print(f"SMTP Port:           {settings.EMAIL_PORT}")
    print(f"Use TLS:             {settings.EMAIL_USE_TLS}")
    print(f"Use SSL:             {settings.EMAIL_USE_SSL}")
    print(f"From Email:          {settings.DEFAULT_FROM_EMAIL}")
    print(f"Host User:           {settings.EMAIL_HOST_USER or '(not set)'}")
    print(f"Host Password:       {'***set***' if settings.EMAIL_HOST_PASSWORD else '(not set)'}")
    print(f"Alert Recipients:    {', '.join(settings.ALERT_EMAIL_RECIPIENTS) if settings.ALERT_EMAIL_RECIPIENTS else '(not set)'}")
    print("="*70 + "\n")


def test_console_backend():
    """Test console backend (prints email to console)."""
    print("📧 Testing Console Backend...")
    print("-" * 70)
    
    try:
        send_mail(
            subject='[TEST] Network Chatbot Email Test',
            message='This is a test email from the Network Chatbot.\n\nIf you see this in the console, the console backend is working!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        print("✅ SUCCESS: Console backend is working!")
        print("   Check the output above to see the email content.\n")
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}\n")
        return False


def test_smtp_backend():
    """Test SMTP backend (sends real email)."""
    print("📧 Testing SMTP Backend...")
    print("-" * 70)
    
    # Check if configuration is set
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("❌ ERROR: EMAIL_HOST_USER and EMAIL_HOST_PASSWORD must be set in .env")
        print("   See EMAIL_SETUP_GUIDE.md for instructions.\n")
        return False
    
    if not settings.ALERT_EMAIL_RECIPIENTS:
        print("⚠️  WARNING: No recipients configured in ALERT_EMAIL_RECIPIENTS")
        recipient = input("Enter test email address: ").strip()
        if not recipient:
            print("❌ No recipient provided. Aborting.\n")
            return False
        recipients = [recipient]
    else:
        recipients = settings.ALERT_EMAIL_RECIPIENTS
        print(f"Sending to: {', '.join(recipients)}")
    
    try:
        result = send_mail(
            subject='[TEST] Network Chatbot Email Test',
            message=(
                'This is a test email from the Network Chatbot Health Monitoring System.\n\n'
                'If you receive this email, your SMTP configuration is working correctly!\n\n'
                'Configuration Details:\n'
                f'- SMTP Host: {settings.EMAIL_HOST}\n'
                f'- SMTP Port: {settings.EMAIL_PORT}\n'
                f'- From: {settings.DEFAULT_FROM_EMAIL}\n\n'
                'Next Steps:\n'
                '1. Configure alert recipients in ALERT_EMAIL_RECIPIENTS\n'
                '2. Start health monitoring: python manage.py monitor_health\n'
                '3. Configure CPU thresholds and alert cooldowns\n\n'
                'For more information, see EMAIL_SETUP_GUIDE.md'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        
        if result == 1:
            print(f"✅ SUCCESS: Email sent to {', '.join(recipients)}")
            print("   Check your inbox (and spam folder) for the test email.\n")
            return True
        else:
            print("⚠️  WARNING: send_mail returned 0 (email may not have been sent)\n")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("\nTroubleshooting Tips:")
        print("1. Check your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
        print("2. For Gmail, use an App Password (not your regular password)")
        print("3. Verify firewall allows outbound SMTP (port 587)")
        print("4. See EMAIL_SETUP_GUIDE.md for detailed instructions\n")
        return False


def main():
    """Main test function."""
    print("\n" + "="*70)
    print("NETWORK CHATBOT - EMAIL CONFIGURATION TEST")
    print("="*70 + "\n")
    
    # Print current configuration
    print_config()
    
    # Determine backend type
    backend = settings.EMAIL_BACKEND
    is_console = 'console' in backend.lower()
    
    if is_console:
        print("ℹ️  You are using the CONSOLE backend (development mode)")
        print("   Emails will be printed to the console, not sent via SMTP.\n")
        
        choice = input("Do you want to:\n  1. Test console backend\n  2. Switch to SMTP and test\n  3. Exit\nChoice (1/2/3): ").strip()
        
        if choice == '1':
            test_console_backend()
        elif choice == '2':
            print("\n📝 To enable SMTP backend:")
            print("   1. Update .env: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
            print("   2. Configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
            print("   3. Run this script again")
            print("\n   See EMAIL_SETUP_GUIDE.md for detailed setup instructions.\n")
        else:
            print("Exiting.\n")
    else:
        print("ℹ️  You are using the SMTP backend (production mode)")
        print("   Real emails will be sent via your configured SMTP server.\n")
        
        choice = input("Send test email? (y/n): ").strip().lower()
        if choice == 'y':
            test_smtp_backend()
        else:
            print("Test cancelled.\n")
    
    print("="*70)
    print("For detailed email setup instructions, see:")
    print("  Backend/EMAIL_SETUP_GUIDE.md")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
