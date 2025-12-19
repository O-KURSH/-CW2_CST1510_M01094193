import pandas as pd
from pathlib import Path
from app.data.db import connect_database


# ============================================================
# STEP 7.1 — INSERT INCIDENT (CREATE)
# ============================================================

def insert_incident(conn, date, incident_type, severity, status, description, reported_by=None):
    """
    Insert a new cyber incident into the database.

    Returns:
        int: ID of the inserted incident
    """
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cyber_incidents
        (date, incident_type, severity, status, description, reported_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, incident_type, severity, status, description, reported_by))

    conn.commit()
    return cursor.lastrowid


# ============================================================
# STEP 7.2 — READ INCIDENTS
# ============================================================

def get_all_incidents(conn):
    """
    Retrieve all incidents from the database.

    Returns:
        pandas.DataFrame
    """
    df = pd.read_sql_query(
        "SELECT * FROM cyber_incidents ORDER BY id DESC",
        conn
    )
    return df


# ============================================================
# STEP 7.3 — UPDATE INCIDENT
# ============================================================

def update_incident_status(conn, incident_id, new_status):
    """
    Update the status of an incident.

    Returns:
        int: number of rows updated (0 or 1)
    """
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE cyber_incidents SET status = ? WHERE id = ?",
        (new_status, incident_id)
    )

    conn.commit()
    return cursor.rowcount


# ============================================================
# STEP 7.4 — DELETE INCIDENT
# ============================================================

def delete_incident(conn, incident_id):
    """
    Delete an incident from the database.

    Returns:
        int: number of rows deleted (0 or 1)
    """
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM cyber_incidents WHERE id = ?",
        (incident_id,)
    )

    conn.commit()
    return cursor.rowcount


# ============================================================
# CSV LOADING (USED IN MAIN)
# ============================================================

def load_csv_to_table(conn, csv_path, table_name):
    """
    Load a CSV file into a database table using pandas.
    Handles column mismatches for all three CSVs.
    """
    csv_path = Path(csv_path)

    # 1 — Check file exists
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return 0

    # 2 — Load CSV
    df = pd.read_csv(csv_path)

    # 2.1 — Normalise headers: lowercase + underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # =======================================================
    # Table-specific fixes
    # =======================================================

    # ----- cyber_incidents -----
    if table_name == "cyber_incidents":
        rename_map = {}
        if "incident_id" in df.columns:
            rename_map["incident_id"] = "id"
        if "timestamp" in df.columns:
            rename_map["timestamp"] = "created_at"
        if rename_map:
            df = df.rename(columns=rename_map)

    # ----- datasets_metadata -----
    # CSV header: dataset_id,name,rows,columns,uploaded_by,upload_date
    if table_name == "datasets_metadata":
        rename_map = {
            "dataset_id": "id",
            "name": "dataset_name",
            "rows": "record_count",
            "columns": "file_size_mb",     # using column count as "size"
            "uploaded_by": "source",
            "upload_date": "last_updated",
        }
        df = df.rename(columns=rename_map)

        # add missing required columns
        if "category" not in df.columns:
            df["category"] = "Unknown"
        if "file_size_mb" in df.columns:
            df["file_size_mb"] = df["file_size_mb"].astype(float)

    # ----- it_tickets -----
    if table_name == "it_tickets":
        # subject is NOT NULL in schema
        if "subject" not in df.columns:
            df["subject"] = "Unknown"
        else:
            df["subject"] = df["subject"].fillna("Unknown")
            df["subject"] = df["subject"].astype(str).str.strip()
            df.loc[df["subject"] == "", "subject"] = "Unknown"

    # =======================================================
    # 3 — Keep only columns that exist in the DB table
    # =======================================================
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    table_cols = [row[1] for row in cursor.fetchall()]  # column names

    cols_to_use = [col for col in df.columns if col in table_cols]

    if not cols_to_use:
        print(f"❌ No matching columns between {csv_path.name} and table '{table_name}'")
        return 0

    df = df[cols_to_use]

    # Extra columns like 'resolution_time_hours' will be dropped here,
    # because they are not in table_cols.

    # 4 — Insert into DB
    df.to_sql(
        table_name,
        conn,
        if_exists="append",
        index=False
    )

    print(f"✅ Loaded {len(df)} rows into '{table_name}' from {csv_path.name}")
    return len(df)
