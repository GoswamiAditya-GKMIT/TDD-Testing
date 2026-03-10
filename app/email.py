import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME")
SMTP_TLS = os.getenv("SMTP_TLS", "True") == "True"


def send_verification_email(email: str, token: str):  # pragma: no cover
    print(f"DEBUG: Preparing to send verification email to {email}")

    # Create message
    message = MIMEMultipart()
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    message["To"] = email
    message["Subject"] = "Verify Your Email - TrackUs"

    body = f"""
    Hello,

    Thank you for registering with TrackUs. 
    Please verify your email using the following token:

    {token}

    Regards,
    The TrackUs Team
    """
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to server
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        if SMTP_TLS:
            server.starttls()

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)
        server.quit()
        print(f"SUCCESS: Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to send email to {email}: {e}")
        return False
