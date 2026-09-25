"""Subcontractor document and insurance compliance matrix.

Streamlit demo app backed by a local SQLite file. Flags upcoming or
expired insurance/certification documents with a red/yellow/green
status computed live from expiration_date vs. today.
"""

from datetime import date

import pandas as pd
import streamlit as st

from alert import build_alert_draft
from db import get_connection
from status import GREEN, RED, STATUS_ORDER, YELLOW, compute_status, days_remaining

DOC_COLUMNS = ["General Liability Insurance", "Workers' Compensation", "Safety Certification"]

STATUS_COLORS = {
    RED: "#f8d7da",
    YELLOW: "#fff3cd",
    GREEN: "#d4edda",
}

GLOSSARY = {
    "General Liability Insurance": "Covers third-party injury or property damage claims tied to a subcontractor's work on site.",
    "Workers' Compensation": "Covers medical costs and lost wages if one of the subcontractor's own workers is injured on the job.",
    "Safety Certification": "A credential or training record (for example OSHA) showing the subcontractor meets site safety requirements.",
    "Compliant": "Document is valid with more than 15 days left before it expires.",
    "Expires soon": "Document expires within the next 15 days and needs renewal attention.",
    "Expired": "Document has already lapsed. Subcontractor should not be on site with this status.",
}


@st.cache_data
def load_data():
    conn = get_connection()
    subs = pd.read_sql_query("SELECT * FROM subcontractors", conn)
    docs = pd.read_sql_query("SELECT * FROM documents", conn)
    conn.close()
    docs["expiration_date"] = pd.to_datetime(docs["expiration_date"]).dt.date
    return subs, docs


def build_matrix(subs: pd.DataFrame, docs: pd.DataFrame, today: date) -> pd.DataFrame:
    """One row per subcontractor with a status cell per document type and
    an overall status equal to the worst status across their documents."""
    docs = docs.copy()
    docs["status"] = docs["expiration_date"].apply(lambda d: compute_status(d, today))
    docs["days"] = docs["expiration_date"].apply(lambda d: days_remaining(d, today))

    rows = []
    for _, sub in subs.iterrows():
        sub_docs = docs[docs["subcontractor_id"] == sub["id"]]
        row = {"id": sub["id"], "Subcontractor": sub["name"], "Trade": sub["trade"]}
        statuses = []
        for doc_type in DOC_COLUMNS:
            match = sub_docs[sub_docs["doc_type"] == doc_type]
            if match.empty:
                row[doc_type] = "N/A"
            else:
                d = match.iloc[0]
                statuses.append(d["status"])
                if d["status"] == RED:
                    detail = "expired" if d["days"] == 0 else f"expired {abs(d['days'])}d ago"
                else:
                    detail = f"{d['days']}d left"
                row[doc_type] = f"{d['status']} ({detail})"
        overall = min(statuses, key=lambda s: STATUS_ORDER[s]) if statuses else GREEN
        row["Overall status"] = overall
        rows.append(row)
    return pd.DataFrame(rows)


def cell_color(value: str) -> str:
    for status, color in STATUS_COLORS.items():
        if value.startswith(status):
            return color
    return "#ffffff"


def render_matrix_html(df: pd.DataFrame) -> str:
    """Render the matrix as a plain HTML table with a large, fixed font
    size so it stays legible from a few feet away, which a canvas-based
    grid widget can't guarantee."""
    display_cols = ["Subcontractor", "Trade"] + DOC_COLUMNS + ["Overall status"]

    header_html = "".join(f"<th>{col}</th>" for col in display_cols)
    rows_html = []
    for _, row in df.iterrows():
        cells = [f"<td>{row['Subcontractor']}</td>", f"<td>{row['Trade']}</td>"]
        for col in DOC_COLUMNS + ["Overall status"]:
            color = cell_color(row[col])
            cells.append(f"<td style='background-color:{color}'>{row[col]}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    return f"""
    <div style="overflow-x:auto">
    <table class="compliance-matrix">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
    </table>
    </div>
    """


MATRIX_CSS = """
<style>
table.compliance-matrix {
    border-collapse: collapse;
    width: 100%;
    font-size: 1.05rem;
}
table.compliance-matrix th, table.compliance-matrix td {
    border: 1px solid #ccc;
    padding: 10px 14px;
    text-align: left;
    white-space: nowrap;
    color: #111111;
}
table.compliance-matrix th {
    background-color: #262730;
    color: white !important;
}
</style>
"""


def main():
    st.set_page_config(page_title="Subcontractor Compliance Matrix", layout="wide")
    st.title("Subcontractor Document and Insurance Compliance Matrix")
    st.caption(
        "Tracks General Liability, Workers' Comp, and Safety Certification "
        "expirations across subcontractors and flags anything expiring soon "
        "or already expired."
    )
    with st.expander("What do these terms mean?"):
        for term, definition in GLOSSARY.items():
            st.markdown(f"**{term}**: {definition}")

    today = date.today()
    subs, docs = load_data()
    matrix = build_matrix(subs, docs, today)

    compliant = (matrix["Overall status"] == GREEN).sum()
    expiring = (matrix["Overall status"] == YELLOW).sum()
    expired = (matrix["Overall status"] == RED).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Compliant", compliant)
    col2.metric("Expiring soon", expiring)
    col3.metric("Expired", expired)

    st.subheader("Compliance matrix")
    filter_choice = st.radio(
        "Show",
        ["All", "Needs attention (Red and Yellow)", "Red only", "Yellow only", "Green only"],
        horizontal=True,
    )
    if filter_choice == "Needs attention (Red and Yellow)":
        filtered = matrix[matrix["Overall status"].isin([RED, YELLOW])]
    elif filter_choice == "Red only":
        filtered = matrix[matrix["Overall status"] == RED]
    elif filter_choice == "Yellow only":
        filtered = matrix[matrix["Overall status"] == YELLOW]
    elif filter_choice == "Green only":
        filtered = matrix[matrix["Overall status"] == GREEN]
    else:
        filtered = matrix

    sort_col = st.selectbox("Sort by", ["Overall status", "Subcontractor", "Trade"])
    if sort_col == "Overall status":
        filtered = filtered.sort_values(
            by="Overall status", key=lambda s: s.map(STATUS_ORDER)
        )
    else:
        filtered = filtered.sort_values(by=sort_col)

    st.markdown(MATRIX_CSS, unsafe_allow_html=True)
    st.markdown(render_matrix_html(filtered), unsafe_allow_html=True)
    st.caption(f"Showing {len(filtered)} of {len(matrix)} subcontractors.")

    st.subheader("Subcontractor detail")
    names = sorted(subs["name"].tolist())
    selected_name = st.selectbox("Select a subcontractor", names)
    show_detail(subs, docs, selected_name, today)

    with st.expander("About this project"):
        st.markdown(
            "This applies compliance-audit and validation-gate logic from data "
            "analytics work to a construction-specific problem: subcontractor "
            "insurance and safety certifications lapsing without anyone noticing "
            "until it becomes a liability on site. It's a prototype built to "
            "demonstrate the pattern, not a production tool.\n\n"
            "Next steps I'd want to explore with a field engineer: how insurance "
            "certificates actually get collected and verified today, what other "
            "documents or credentials matter beyond the three tracked here, and "
            "whether flags like these would fit into an existing project "
            "management tool or need to stand alone."
        )


def show_detail(subs: pd.DataFrame, docs: pd.DataFrame, selected_name: str, today: date):
    sub = subs[subs["name"] == selected_name].iloc[0]
    sub_docs = docs[docs["subcontractor_id"] == sub["id"]].copy()
    sub_docs["status"] = sub_docs["expiration_date"].apply(lambda d: compute_status(d, today))
    sub_docs["days"] = sub_docs["expiration_date"].apply(lambda d: days_remaining(d, today))

    st.markdown(f"**{sub['name']}**  \nTrade: {sub['trade']}  \nScope: {sub['scope_of_work']}")

    for _, doc in sub_docs.iterrows():
        status = doc["status"]
        days = doc["days"]
        if status == RED:
            days_text = "expired today" if days == 0 else f"expired {abs(days)} days ago"
        else:
            days_text = f"{days} days remaining"

        with st.container(border=True):
            cols = st.columns([3, 2, 2, 2])
            cols[0].write(doc["doc_type"])
            cols[1].write(doc["expiration_date"].strftime("%B %d, %Y"))
            cols[2].write(days_text)
            cols[3].markdown(
                f"<span style='background-color:{STATUS_COLORS[status]};padding:2px 8px;border-radius:4px'>{status}</span>",
                unsafe_allow_html=True,
            )

            if status in (RED, YELLOW):
                if st.button("Generate Alert Draft", key=f"alert_{doc['id']}"):
                    st.session_state[f"draft_{doc['id']}"] = build_alert_draft(
                        sub["name"], sub["pm_email"], doc["doc_type"], doc["expiration_date"], today
                    )

                draft = st.session_state.get(f"draft_{doc['id']}")
                if draft:
                    st.warning("DRAFT, not sent. No email has been sent by this app.")
                    st.text_input("To", value=draft["to"], key=f"to_{doc['id']}", disabled=True)
                    st.text_input("Subject", value=draft["subject"], key=f"subject_{doc['id']}", disabled=True)
                    st.text_area("Body", value=draft["body"], key=f"body_{doc['id']}", height=160, disabled=True)


if __name__ == "__main__":
    main()
