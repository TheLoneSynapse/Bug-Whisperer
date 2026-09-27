"""TEST: sqlalchemy — NoSuchModuleError from invalid database URL."""

from sqlalchemy import create_engine

# WRONG (NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:notavalidurl)
engine = create_engine("notavalidurl://")

# CORRECT
# engine = create_engine("sqlite:///demo.db")
