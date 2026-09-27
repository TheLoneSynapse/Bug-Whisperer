"""DEMO: sqlalchemy mistake — using an invalid database URL format.

Run with:
    .\run.bat demos\demo_sqlalchemy.py
"""

from sqlalchemy import create_engine

# WRONG (NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:notavalidurl)
engine = create_engine("notavalidurl://")

# CORRECT (use sqlite:/// for a local SQLite database)
engine = create_engine("sqlite:///demo.db")
print("Engine created:", engine)
