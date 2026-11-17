"""Creates the database, tables and sample data.

Usage:  python init_db.py

It runs database/schema.sql and then database/seed.sql using the login
from your .env file. WARNING: it drops and re-creates the tables, so any
data you added is reset to the sample data.
"""
from pathlib import Path

import mysql.connector

from config import DB_CONFIG

BASE = Path(__file__).parent / "database"


def run_sql_file(cursor, path):
    """Run every statement in a .sql file.

    Simple splitter: removes '--' comment lines and splits on ';'.
    (Good enough for our two files, which have no ';' inside strings.)
    """
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("--")
    ]
    for statement in "\n".join(lines).split(";"):
        if statement.strip():
            cursor.execute(statement)


def main():
    settings = dict(DB_CONFIG)
    settings.pop("database")  # the database may not exist yet
    conn = mysql.connector.connect(**settings)
    cur = conn.cursor()
    for name in ("schema.sql", "seed.sql"):
        print(f"Running {name} ...")
        run_sql_file(cur, BASE / name)
    conn.commit()
    conn.close()
    print("Done. Database 'gamestore' is ready.")


if __name__ == "__main__":
    main()
