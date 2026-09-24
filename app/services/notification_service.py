import smtplib
from email.message import EmailMessage

from app.config import settings


def send_escalation_notification(
    ticket_id: str,
    issue_title: str,
    priority: str,
) -> bool:

    if not settings.smtp_enabled:
        print(
            f"[NOTIFICATION] Ticket {ticket_id} "
            f"requires {priority} escalation: {issue_title}"
        )
        return True

    message = EmailMessage()

    message["Subject"] = (
        f"[{priority}] IT Support Ticket {ticket_id}"
    )

    message["From"] = settings.smtp_username
    message["To"] = settings.support_email

    message.set_content(
        f"""
IT Support Escalation

Ticket ID: {ticket_id}
Priority: {priority}
Issue: {issue_title}

Please review this ticket immediately.
"""
    )

    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
        ) as server:

            server.starttls()

            server.login(
                settings.smtp_username,
                settings.smtp_password,
            )

            server.send_message(message)

        return True

    except Exception as exc:
        print(f"Notification error: {exc}")
        return False