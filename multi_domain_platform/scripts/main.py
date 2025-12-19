import time
import pandas as pd

from app.data.db import connect_database
from app.data.schema import create_all_tables
from app.data.users import migrate_users_from_file
from app.data.incidents import (
    load_csv_to_table,
    insert_incident,
    update_incident_status,
    delete_incident
)
from app.services.user_service import register_user, login_user
from app.data.analytics import (
    get_incidents_by_type_count,
    get_high_severity_by_status
)


def run_comprehensive_tests():
    """
    Run comprehensive tests on your database.
    """
    print("\n" + "=" * 60)
    print("🧪 RUNNING COMPREHENSIVE TESTS")
    print("=" * 60)

    # ---------------------------------------------------------
    # SETUP (ensures tables + data exist before tests)
    # ---------------------------------------------------------
    print("\n[SETUP] Creating tables + loading data")
    conn = connect_database()

    # Always ensure schema exists
    create_all_tables(conn)

    # Migrate users (safe to run repeatedly because it uses INSERT OR IGNORE)
    migrate_users_from_file()

    # Load CSVs (will append if you run multiple times)
    # If your lab expects a "clean" run each time, delete the .db first.
    load_csv_to_table(conn, "DATA/cyber_incidents.csv", "cyber_incidents")
    load_csv_to_table(conn, "DATA/datasets_metadata.csv", "datasets_metadata")
    load_csv_to_table(conn, "DATA/it_tickets.csv", "it_tickets")

    # ---------------------------------------------------------
    # TEST 1: Authentication
    # ---------------------------------------------------------
    print("\n[TEST 1] Authentication")

    # Use a unique username each run to avoid UNIQUE constraint issues
    test_username = f"test_user_{int(time.time())}"

    success, msg = register_user(test_username, "TestPass123!", "user")
    print(f"  Register: {'✅' if success else '❌'} {msg}")

    success, msg = login_user(test_username, "TestPass123!")
    print(f"  Login:    {'✅' if success else '❌'} {msg}")

    # ---------------------------------------------------------
    # TEST 2: CRUD Operations
    # ---------------------------------------------------------
    print("\n[TEST 2] CRUD Operations")

    # Create
    test_id = insert_incident(
        conn,
        "2024-11-05",
        "Test Incident",
        "Low",
        "Open",
        "This is a test incident",
        test_username
    )
    print(f"  Create: ✅ Incident #{test_id} created")

    # Read
    df = pd.read_sql_query(
        "SELECT * FROM cyber_incidents WHERE id = ?",
        conn,
        params=(test_id,)
    )
    if len(df) == 1:
        print(f"  Read:    ✅ Found incident #{test_id}")
    else:
        print(f"  Read:    ❌ Could not find incident #{test_id}")

    # Update
    rows_updated = update_incident_status(conn, test_id, "Resolved")
    print(f"  Update:  {'✅' if rows_updated > 0 else '❌'} Status updated")

    # Delete
    rows_deleted = delete_incident(conn, test_id)
    print(f"  Delete:  {'✅' if rows_deleted > 0 else '❌'} Incident deleted")

    # ---------------------------------------------------------
    # TEST 3: Analytical Queries
    # ---------------------------------------------------------
    print("\n[TEST 3] Analytical Queries")

    df_by_type = get_incidents_by_type_count(conn)
    print(f"  By Type:        ✅ Found {len(df_by_type)} incident types")

    df_high = get_high_severity_by_status(conn)
    print(f"  High Severity:  ✅ Found {len(df_high)} status categories")

    conn.close()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    run_comprehensive_tests()




