"""CRUD API for customers:  /api/customers"""
from flask import Blueprint, jsonify

import db
from utils import ApiError, get_json, optional_text, require_text

bp = Blueprint("customers", __name__, url_prefix="/api/customers")


def read_fields(data):
    email = require_text(data, "email", 120)
    if "@" not in email:
        raise ApiError("'email' must be a valid email address")
    return (
        require_text(data, "first_name", 50),
        require_text(data, "last_name", 50),
        email,
        optional_text(data, "phone", 25),
    )


@bp.get("")
def list_customers():
    """READ all customers, with how many orders each one has placed."""
    rows = db.query(
        """
        SELECT c.customer_id, c.first_name, c.last_name, c.email, c.phone,
               c.created_at, COUNT(o.order_id) AS order_count
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.customer_id
        GROUP BY c.customer_id
        ORDER BY c.last_name, c.first_name
        """
    )
    return jsonify(rows)


@bp.get("/<int:customer_id>")
def get_customer(customer_id):
    """READ one customer."""
    row = db.query_one(
        "SELECT * FROM customers WHERE customer_id = %s", (customer_id,)
    )
    if row is None:
        raise ApiError("Customer not found", 404)
    return jsonify(row)


@bp.post("")
def create_customer():
    """CREATE a customer."""
    fields = read_fields(get_json())
    new_id, _ = db.execute(
        "INSERT INTO customers (first_name, last_name, email, phone) "
        "VALUES (%s, %s, %s, %s)",
        fields,
    )
    return get_customer(new_id), 201


@bp.put("/<int:customer_id>")
def update_customer(customer_id):
    """UPDATE a customer."""
    fields = read_fields(get_json())
    get_customer(customer_id)  # sends 404 if it does not exist
    db.execute(
        "UPDATE customers SET first_name = %s, last_name = %s, email = %s, "
        "phone = %s WHERE customer_id = %s",
        fields + (customer_id,),
    )
    return get_customer(customer_id)


@bp.delete("/<int:customer_id>")
def delete_customer(customer_id):
    """DELETE a customer. MySQL blocks this (ON DELETE RESTRICT) if the
    customer has orders; app.py turns that into a 409 error."""
    _, deleted = db.execute(
        "DELETE FROM customers WHERE customer_id = %s", (customer_id,)
    )
    if deleted == 0:
        raise ApiError("Customer not found", 404)
    return jsonify({"message": "Customer deleted"})
