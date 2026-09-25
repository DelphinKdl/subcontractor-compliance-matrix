"""Status computation for subcontractor compliance documents.

Status is always computed live from expiration_date vs. today, never stored.
"""

from datetime import date

GREEN = "Green"
YELLOW = "Yellow"
RED = "Red"

STATUS_LABELS = {
    GREEN: "Compliant",
    YELLOW: "Expires soon",
    RED: "Expired",
}

STATUS_ORDER = {RED: 0, YELLOW: 1, GREEN: 2}


def days_remaining(expiration_date: date, today: date | None = None) -> int:
    """Days between today and expiration_date. Negative means already past."""
    today = today or date.today()
    return (expiration_date - today).days


def compute_status(expiration_date: date, today: date | None = None) -> str:
    """Return Green, Yellow, or Red for a document's expiration date.

    Green: more than 15 days out.
    Yellow: 1-15 days out, inclusive.
    Red: today or earlier (expires today counts as already expired).
    """
    days = days_remaining(expiration_date, today)
    if days <= 0:
        return RED
    if days <= 15:
        return YELLOW
    return GREEN
