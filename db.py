"""Pooled MySQL queries and transactions. Pass values as SQL parameters."""
from contextlib import contextmanager

from mysql.connector import pooling

from config import DB_CONFIG

_pool = None


def get_connection():
    """Borrow a connection from the pool (the pool is created on first use)."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="gamestore_pool",
            pool_size=5,
            autocommit=True,  # single statements save immediately
            **DB_CONFIG,
        )
    return _pool.get_connection()


def query(sql, params=()):
    """Run a SELECT and return all rows as a list of dictionaries."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()  # gives the connection back to the pool


def query_one(sql, params=()):
    """Run a SELECT and return the first row (or None if there is no row)."""
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Execute a write and return (lastrowid, rowcount)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.lastrowid, cur.rowcount
    finally:
        conn.close()


@contextmanager
def transaction():
    """Commit the block on success; roll back on any exception."""
    conn = get_connection()
    try:
        conn.start_transaction()
        cur = conn.cursor(dictionary=True)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
