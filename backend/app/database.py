"""
database.py

WHAT THIS FILE DOES (small why):
Sets up the actual connection to the database, and provides a `get_db()`
function that FastAPI uses to hand each request a database session (a
"conversation" with the database that opens, does its work, then closes).

WHY THIS MATTERS (big why):
This is "dependency injection" -- a FastAPI concept where instead of every
route manually opening/closing a database connection (easy to mess up and
forget to close), we define get_db() ONCE, and FastAPI automatically runs
it before every route that needs it, and cleans up after, even if the route
raises an error. You'll see `db: Session = Depends(get_db)` in main.py --
that's this function being plugged in automatically.

For local development we default to SQLite (a database that's just a single
file, zero setup). For production, swap DATABASE_URL to a PostgreSQL
connection string (the PDF's preferred database) -- no code changes needed
elsewhere, just this one line. This is documented as an assumption/setup
note in the README.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tea_packaging.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Yields a database session, then always closes it afterward (the `finally`
    block runs no matter what, even if the route code crashes) -- prevents
    connection leaks under load.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
