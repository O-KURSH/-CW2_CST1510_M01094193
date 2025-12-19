import streamlit as st
import pandas as pd

from app.data.db import connect_database


# -----------------------------
# Auth guard (same pattern as before)
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.error("You must be logged in to view the dashboard.")
    if st.button("Go to login page"):
        st.switch_page("Home.py")
    st.stop()


st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard")
st.caption("Overview of incidents, datasets, and IT tickets from the SQLite database.")


# -----------------------------
# Helpers (robust to schema changes)
# -----------------------------
def table_exists(conn, table_name: str) -> bool:
    q = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    return pd.read_sql_query(q, conn, params=(table_name,)).shape[0] > 0

def get_columns(conn, table_name: str) -> list[str]:
    try:
        df = pd.read_sql_query(f"PRAGMA table_info({table_name})", conn)
        return df["name"].tolist()
    except Exception:
        return []

def row_count(conn, table_name: str) -> int:
    try:
        df = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {table_name}", conn)
        return int(df.loc[0, "n"])
    except Exception:
        return 0

def value_counts(conn, table_name: str, col: str) -> pd.DataFrame:
    # returns DataFrame with columns: col, count
    q = f"""
        SELECT {col} AS value, COUNT(*) AS count
        FROM {table_name}
        GROUP BY {col}
        ORDER BY count DESC
    """
    return pd.read_sql_query(q, conn)


# -----------------------------
# Load data / compute KPIs
# -----------------------------
conn = connect_database()

# Table names you already use
tables = {
    "users": "users",
    "incidents": "cyber_incidents",
    "datasets": "datasets_metadata",
    "tickets": "it_tickets"
}

# Counts (safe even if table missing)
users_n = row_count(conn, tables["users"]) if table_exists(conn, tables["users"]) else 0
incidents_n = row_count(conn, tables["incidents"]) if table_exists(conn, tables["incidents"]) else 0
datasets_n = row_count(conn, tables["datasets"]) if table_exists(conn, tables["datasets"]) else 0
tickets_n = row_count(conn, tables["tickets"]) if table_exists(conn, tables["tickets"]) else 0

# Incident-specific metrics (only if columns exist)
inc_cols = get_columns(conn, tables["incidents"])
has_status = "status" in inc_cols
has_severity = "severity" in inc_cols

open_incidents = 0
high_crit_incidents = 0

if table_exists(conn, tables["incidents"]) and has_status:
    try:
        df_open = pd.read_sql_query(
            f"SELECT COUNT(*) AS n FROM {tables['incidents']} WHERE status = ?",
            conn,
            params=("Open",)
        )
        open_incidents = int(df_open.loc[0, "n"])
    except Exception:
        open_incidents = 0

if table_exists(conn, tables["incidents"]) and has_severity:
    try:
        df_hc = pd.read_sql_query(
            f"""
            SELECT COUNT(*) AS n
            FROM {tables['incidents']}
            WHERE severity IN ('High', 'Critical')
            """,
            conn
        )
        high_crit_incidents = int(df_hc.loc[0, "n"])
    except Exception:
        high_crit_incidents = 0


# -----------------------------
# KPI row
# -----------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Users", users_n)
c2.metric("Incidents", incidents_n)
c3.metric("Open Incidents", open_incidents)
c4.metric("High/Critical", high_crit_incidents)
c5.metric("IT Tickets", tickets_n)

st.divider()

left, right = st.columns([1, 1])

# -----------------------------
# Charts (Incidents by severity/status)
# -----------------------------
with left:
    st.subheader("Incidents by Severity")
    if table_exists(conn, tables["incidents"]) and has_severity:
        try:
            sev_df = value_counts(conn, tables["incidents"], "severity")
            sev_df = sev_df.set_index("value")
            st.bar_chart(sev_df["count"])
            with st.expander("View severity counts"):
                st.dataframe(sev_df.reset_index(), use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load severity chart: {e}")
    else:
        st.info("Severity data not available (missing table or column).")

with right:
    st.subheader("Incidents by Status")
    if table_exists(conn, tables["incidents"]) and has_status:
        try:
            status_df = value_counts(conn, tables["incidents"], "status")
            status_df = status_df.set_index("value")
            st.bar_chart(status_df["count"])
            with st.expander("View status counts"):
                st.dataframe(status_df.reset_index(), use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load status chart: {e}")
    else:
        st.info("Status data not available (missing table or column).")

st.divider()

# -----------------------------
# Recent incidents table
# -----------------------------
st.subheader("Recent Incidents")

if table_exists(conn, tables["incidents"]):
    # Prefer created_at, fallback to id desc
    order_col = "created_at" if "created_at" in inc_cols else "id"
    try:
        recent = pd.read_sql_query(
            f"""
            SELECT *
            FROM {tables['incidents']}
            ORDER BY {order_col} DESC
            LIMIT 10
            """,
            conn
        )
        st.dataframe(recent, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Could not load recent incidents: {e}")
else:
    st.info("No incidents table found.")

st.divider()

# -----------------------------
# Datasets + Tickets quick preview
# -----------------------------
colA, colB = st.columns(2)

with colA:
    st.subheader("Datasets (preview)")
    if table_exists(conn, tables["datasets"]):
        ds_cols = get_columns(conn, tables["datasets"])
        order_col = "upload_date" if "upload_date" in ds_cols else ("created_at" if "created_at" in ds_cols else "id")
        try:
            ds = pd.read_sql_query(
                f"SELECT * FROM {tables['datasets']} ORDER BY {order_col} DESC LIMIT 5",
                conn
            )
            st.dataframe(ds, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"Could not load datasets preview: {e}")
    else:
        st.info("No datasets_metadata table found.")

with colB:
    st.subheader("IT Tickets (preview)")
    if table_exists(conn, tables["tickets"]):
        t_cols = get_columns(conn, tables["tickets"])
        order_col = "created_at" if "created_at" in t_cols else ("created_date" if "created_date" in t_cols else "id")
        try:
            t = pd.read_sql_query(
                f"SELECT * FROM {tables['tickets']} ORDER BY {order_col} DESC LIMIT 5",
                conn
            )
            st.dataframe(t, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"Could not load tickets preview: {e}")
    else:
        st.info("No it_tickets table found.")

conn.close()

# -----------------------------
# Logout button
# -----------------------------
st.divider()
if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Logged out.")
    st.switch_page("Home.py")