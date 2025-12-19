# app/data/analytics.py

import pandas as pd


def get_incidents_by_type_count(conn):
    """
    Count incidents by incident type.
    """
    query = """
        SELECT incident_type, COUNT(*) AS count
        FROM cyber_incidents
        GROUP BY incident_type
        ORDER BY count DESC
    """
    return pd.read_sql_query(query, conn)


def get_high_severity_by_status(conn):
    """
    Count HIGH / CRITICAL severity incidents by status.
    """
    query = """
        SELECT status, COUNT(*) AS count
        FROM cyber_incidents
        WHERE severity IN ('High', 'Critical')
        GROUP BY status
        ORDER BY count DESC
    """
    return pd.read_sql_query(query, conn)