"""End-to-end verification using Streamlit's AppTest framework.

Covers the full demo flow: load the app, filter to red/yellow, select a
subcontractor, generate a draft alert, and assert zero exceptions.
"""

import sys
from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_connection  # noqa: E402
from status import RED, YELLOW, compute_status  # noqa: E402

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def _name_with_attention_needed() -> str:
    """Look up a seeded subcontractor with a red or yellow document."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT s.name AS name, d.expiration_date AS expiration_date "
        "FROM documents d JOIN subcontractors s ON s.id = d.subcontractor_id"
    ).fetchall()
    conn.close()
    today = date.today()
    for row in rows:
        exp = date.fromisoformat(row["expiration_date"])
        if compute_status(exp, today) in (RED, YELLOW):
            return row["name"]
    raise AssertionError("expected at least one seeded document in Red or Yellow status")


def test_app_loads_without_exceptions():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    assert not at.exception


def test_filter_to_needs_attention():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.radio[0].set_value("Needs attention (Red and Yellow)")
    at.run(timeout=30)
    assert not at.exception


def test_select_subcontractor_and_generate_alert_draft():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    at.radio[0].set_value("Needs attention (Red and Yellow)")
    at.run(timeout=30)
    assert not at.exception

    # Select a subcontractor known (from the fixed seed) to have a red or
    # yellow document, so a "Generate Alert Draft" button is present.
    name = _name_with_attention_needed()
    sub_selectbox = next(sb for sb in at.selectbox if sb.label == "Select a subcontractor")
    sub_selectbox.set_value(name)
    at.run(timeout=30)
    assert not at.exception
    assert at.button, "expected a Generate Alert Draft button for this subcontractor"

    at.button[0].click()
    at.run(timeout=30)
    assert not at.exception
    assert any("DRAFT, not sent" in w.value for w in at.warning)
