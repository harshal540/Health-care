"""
STEP 2: DATABASE CONNECTION
----------------------------
This file sets up the connection to our database.

We use SQLite because it needs ZERO setup - no separate database
server to install. The whole database lives in one file: clinic.db
That makes it perfect for learning and for a small clinic.

If you ever need a bigger database (PostgreSQL, MySQL, etc.), you
only change the DATABASE_URL below - nothing else in the project
needs to change.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Where the database file will live
DATABASE_URL = "sqlite:///./clinic.db"

# 2. The "engine" is the actual connection to the database
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # only needed for SQLite
)

# 3. SessionLocal is a factory that creates new database "conversations"
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base is the parent class every database table (model) will inherit from
Base = declarative_base()


def get_db():
    """
    A FastAPI 'dependency'. FastAPI calls this for every request that
    needs the database, gives the route a fresh session, and closes it
    automatically afterwards - even if an error happens.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
