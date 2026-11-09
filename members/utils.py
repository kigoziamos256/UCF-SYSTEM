from django.core.mail import send_mail
from django.conf import settings

def send_ucf_email(subject, message, recipient_list):
    """Helper function to safely send emails in the background."""
    if not recipient_list:
        return
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=True,
        )
        print(f"✅ Email sent to {len(recipient_list)} recipients.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
