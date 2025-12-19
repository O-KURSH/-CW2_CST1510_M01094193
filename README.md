# Project for module CST1510

# Multi-Domain Data Platform (Streamlit + SQLite + AI)

A coursework project demonstrating a multi-domain data platform using:
- **SQLite** database with multiple domains (IT tickets, cyber incidents, datasets)
- **Authentication** with **bcrypt** password hashing
- **Streamlit** multi-page UI (Dashboard + IT Operations)
- **AI assistant** (OpenAI) for ticket triage / analysis

## Project Structure (key folders)

- `multi_domain_platform/app/data/`  
  Database connection + schema + data access modules (SQLite).
- `multi_domain_platform/app/services/`  
  Business logic (e.g., authentication / user services).
- `multi_domain_platform/app/ui/`  
  Streamlit UI entrypoint (`Home.py`) and pages (`pages/`).
- `DATA/`  
  CSV input files used to populate the database (coursework datasets).
