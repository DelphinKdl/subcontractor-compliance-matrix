"""Draft alert email text for a lapsed or soon-to-lapse document.

This only builds text for display in the UI. Nothing here sends email.
"""

from datetime import date

from status import RED, compute_status, days_remaining


def build_alert_draft(sub_name: str, pm_email: str, doc_type: str, expiration_date: date, today: date | None = None) -> dict:
    """Return a dict with to/subject/body for a draft alert email."""
    today = today or date.today()
    status = compute_status(expiration_date, today)
    days = days_remaining(expiration_date, today)
    exp_str = expiration_date.strftime("%B %d, %Y")

    if status == RED:
        timing = f"expired on {exp_str}" if days < 0 else f"expired today, {exp_str}"
    else:
        timing = f"expires on {exp_str}, in {days} day{'s' if days != 1 else ''}"

    subject = f"Action needed: {doc_type} for {sub_name}"
    body = (
        f"Hello,\n\n"
        f"Our records show that the {doc_type} on file for {sub_name} {timing}. "
        f"Per site compliance policy, updated documentation is required before "
        f"{sub_name} can continue work on site.\n\n"
        f"Please send an updated {doc_type} certificate at your earliest convenience.\n\n"
        f"Thank you,\nSite Compliance Team"
    )
    return {"to": pm_email, "subject": subject, "body": body}
