import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # -> multi_domain_platform/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

from app.data.db import connect_database
from openai import OpenAI


st.set_page_config(page_title="IT Operations", page_icon="🧰", layout="wide")
st.title("🧰 IT Operations Dashboard")
st.caption("Ticket monitoring + AI-assisted triage (SQLite + Streamlit)")

# ----------------------------
# Auth guard
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.error("You must be logged in to view this page.")
    if st.button("Go to login page"):
        st.switch_page("Home.py")
    st.stop()


# ----------------------------
# Helpers
# ----------------------------
def pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find a column in df matching one of candidates (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for name in candidates:
        key = name.lower()
        if key in cols_lower:
            return cols_lower[key]
    return None

def safe_value_counts(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Return dataframe: col, count"""
    vc = df[col].fillna("Unknown").astype(str).value_counts()
    out = vc.reset_index()
    out.columns = [col, "count"]  # ensure predictable column names
    return out

def safe_metric_count(df: pd.DataFrame, col: str | None, value: str) -> int:
    if not col or col not in df.columns:
        return 0
    return int((df[col].fillna("").astype(str) == value).sum())

def get_openai_key() -> str | None:
    
    try:
        return st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        return None


# ----------------------------
# Load tickets from DB
# ----------------------------
conn = connect_database()
tickets = pd.read_sql_query("SELECT * FROM it_tickets", conn)
conn.close()

tickets.columns = [c.strip() for c in tickets.columns]  # clean whitespace

# Auto-detect common columns (works even if your CSV uses different headers)
status_col   = pick_column(tickets, ["status", "ticket_status", "state"])
priority_col = pick_column(tickets, ["priority", "ticket_priority"])
category_col = pick_column(tickets, ["category", "ticket_category", "type"])
subject_col  = pick_column(tickets, ["subject", "title", "summary"])
desc_col     = pick_column(tickets, ["description", "details", "body"])
ticketid_col = pick_column(tickets, ["ticket_id", "id", "ticket"])
created_col  = pick_column(tickets, ["created_at", "created_date", "date_created"])
resolved_col = pick_column(tickets, ["resolved_date", "closed_date", "date_resolved"])
assigned_col = pick_column(tickets, ["assigned_to", "assignee", "owner"])


# ----------------------------
# Sidebar filters
# ----------------------------
with st.sidebar:
    st.header("Filters")

    status_filter = "All"
    priority_filter = "All"
    category_filter = "All"

    if status_col:
        status_options = ["All"] + sorted(tickets[status_col].dropna().astype(str).unique().tolist())
        status_filter = st.selectbox("Status", status_options, index=0)
    else:
        st.warning("No status-like column found.")

    if priority_col:
        priority_options = ["All"] + sorted(tickets[priority_col].dropna().astype(str).unique().tolist())
        priority_filter = st.selectbox("Priority", priority_options, index=0)
    else:
        st.warning("No priority-like column found.")

    if category_col:
        category_options = ["All"] + sorted(tickets[category_col].dropna().astype(str).unique().tolist())
        category_filter = st.selectbox("Category", category_options, index=0)
    else:
        st.info("No category-like column found (optional).")

    st.divider()
    st.write("Logged in as:", st.session_state.username)

    with st.expander("Debug: detected columns"):
        st.write({
            "status_col": status_col,
            "priority_col": priority_col,
            "category_col": category_col,
            "subject_col": subject_col,
            "desc_col": desc_col,
            "ticketid_col": ticketid_col,
            "created_col": created_col,
            "resolved_col": resolved_col,
            "assigned_col": assigned_col,
        })


# Apply filters
filtered = tickets.copy()

if status_col and status_filter != "All":
    filtered = filtered[filtered[status_col].astype(str) == status_filter]
if priority_col and priority_filter != "All":
    filtered = filtered[filtered[priority_col].astype(str) == priority_filter]
if category_col and category_filter != "All":
    filtered = filtered[filtered[category_col].astype(str) == category_filter]


# ----------------------------
# KPI row
# ----------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Tickets (filtered)", len(filtered))

# common statuses 
open_n = safe_metric_count(filtered, status_col, "Open")
inprog_n = safe_metric_count(filtered, status_col, "In Progress")
resolved_n = safe_metric_count(filtered, status_col, "Resolved")
closed_n = safe_metric_count(filtered, status_col, "Closed")

c2.metric("Open", open_n)
c3.metric("In Progress", inprog_n)
c4.metric("Resolved/Closed", resolved_n + closed_n)

st.divider()


# ----------------------------
# Charts
# ----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Tickets by Status")
    if status_col:
        by_status_df = safe_value_counts(filtered, status_col)
        series = by_status_df.set_index(status_col)["count"]
        st.bar_chart(series)
    else:
        st.info("Status chart unavailable (no status column detected).")

with right:
    st.subheader("Tickets by Priority")
    if priority_col:
        by_priority_df = safe_value_counts(filtered, priority_col)
        series = by_priority_df.set_index(priority_col)["count"]
        st.bar_chart(series)
    else:
        st.info("Priority chart unavailable (no priority column detected).")

st.divider()

if category_col:
    st.subheader("Tickets by Category")
    by_cat_df = safe_value_counts(filtered, category_col)
    st.bar_chart(by_cat_df.set_index(category_col)["count"])
    st.divider()


# ----------------------------
# Table
# ----------------------------
st.subheader("Ticket List (Filtered)")
st.dataframe(filtered, use_container_width=True, hide_index=True)


# ----------------------------
# AI integration
# ----------------------------
st.divider()
st.subheader("🤖 AI-assisted Ticket Triage")

st.write("The AI receives a sample of the filtered tickets and returns a summary + recommended actions.")

default_question = (
    "Summarise the main issues in these tickets and recommend the top 5 actions. "
    "Prioritise urgent/high priority items. Use bullet points."
)

question = st.text_area("Question", value=default_question, height=90)

colA, colB = st.columns([1, 1])
with colA:
    max_rows = st.slider("Tickets sent to AI (context)", 5, 50, 25, step=5)
with colB:
    model_name = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)

if st.button("Analyze with AI", type="primary"):
    api_key = get_openai_key()
    if not api_key:
        st.error("Missing OPENAI_API_KEY. Add it to `.streamlit/secrets.toml` and restart Streamlit.")
        st.stop()

    sample = filtered.head(max_rows).copy()

    # Build a compact context table with useful columns (only those detected)
    keep_cols = [c for c in [
        ticketid_col, priority_col, status_col, category_col,
        subject_col, desc_col, created_col, resolved_col, assigned_col
    ] if c and c in sample.columns]

    if keep_cols:
        sample = sample[keep_cols]

    context_csv = sample.to_csv(index=False)

    system_prompt = (
        "You are an IT Operations assistant.\n"
        "You help triage tickets, identify patterns, and recommend practical actions.\n"
        "Be concise and actionable. Use bullet points.\n"
        "If data is missing, say what’s missing.\n"
    )

    user_prompt = f"""
Filtered tickets (CSV):
{context_csv}

User question:
{question}

Return:
1) Summary of common issues
2) Top priorities + why
3) Recommended actions (step-by-step)
4) Missing data that would help
"""

    client = OpenAI(api_key=api_key)

    with st.spinner("Thinking..."):
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )

    st.markdown(resp.choices[0].message.content)


# ----------------------------
# Logout
# ----------------------------
st.divider()
if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.switch_page("Home.py")