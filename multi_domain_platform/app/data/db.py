import sqlite3
from pathlib import Path

def connect_database():
    """
    Connect to the SQLite database using an absolute path.

    Database location (recommended):
    multi_domain_platform/data/intelligence_platform.db
    """
    # This file is: multi_domain_platform/app/data/db.py
    # parents[2] -> multi_domain_platform/
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

    DATA_DIR = PROJECT_ROOT / "data"   
   

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    db_path = DATA_DIR / "intelligence_platform.db"  
    return sqlite3.connect(str(db_path))