"""Email sender for daily match reports."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional


def send_report_email(
    subject: str,
    body_markdown: str,
    body_html: Optional[str] = None,
    recipients: Optional[List[str]] = None,
) -> bool:
    """Send the daily report via email.

    Uses SMTP credentials from environment variables:
    - SMTP_HOST (default: smtp.gmail.com)
    - SMTP_PORT (default: 587)
    - SMTP_USER
    - SMTP_PASSWORD
    - EMAIL_FROM
    - EMAIL_TO (comma-separated, used if recipients not provided)
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM", smtp_user)

    if recipients is None:
        recipients_str = os.getenv("EMAIL_TO", "")
        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

    if not smtp_user or not smtp_password:
        print("⚠️  SMTP credentials not configured. Skipping email send.")
        print("   Set SMTP_USER and SMTP_PASSWORD in .env")
        return False

    if not recipients:
        print("⚠️  No recipients configured. Skipping email send.")
        print("   Set EMAIL_TO in .env or pass recipients explicitly.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = ", ".join(recipients)

        # Plain text version
        msg.attach(MIMEText(body_markdown, "plain", "utf-8"))

        # HTML version if provided
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(email_from, recipients, msg.as_string())

        print(f"✅ Email sent to: {', '.join(recipients)}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP authentication failed. Check your credentials.")
        print("   For Gmail, use an App Password: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
