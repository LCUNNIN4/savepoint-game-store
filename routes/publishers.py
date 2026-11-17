"""CRUD API for publishers:  /api/publishers"""
from flask import Blueprint, jsonify

import db
from utils import ApiError, get_json, optional_text, require_text

bp = Blueprint("publishers", __name__, url_prefix="/api/publishers")


def read_fields(data):
    return (
        require_text(data, "name", 100),
        optional_text(data, "country", 60),
        optional_text(data, "website", 200),
    )


@bp.get("")
def list_publishers():
    """READ all publishers, with how many games each one has."""
    rows = db.query(
        """
        SELECT p.publisher_id, p.name, p.country, p.website,
               COUNT(g.game_id) AS game_count
        FROM publishers p
        LEFT JOIN games g ON g.publisher_id = p.publisher_id
        GROUP BY p.publisher_id
        ORDER BY p.name
        """
    )
    return jsonify(rows)


@bp.get("/<int:publisher_id>")
def get_publisher(publisher_id):
    """READ one publisher."""
    row = db.query_one(
        "SELECT * FROM publishers WHERE publisher_id = %s", (publisher_id,)
    )
    if row is None:
        raise ApiError("Publisher not found", 404)
    return jsonify(row)


@bp.post("")
def create_publisher():
    """CREATE a publisher."""
    name, country, website = read_fields(get_json())
    new_id, _ = db.execute(
        "INSERT INTO publishers (name, country, website) VALUES (%s, %s, %s)",
        (name, country, website),
    )
    return get_publisher(new_id), 201


@bp.put("/<int:publisher_id>")
def update_publisher(publisher_id):
    """UPDATE a publisher."""
    name, country, website = read_fields(get_json())
    get_publisher(publisher_id)  # sends 404 if it does not exist
    db.execute(
        "UPDATE publishers SET name = %s, country = %s, website = %s "
        "WHERE publisher_id = %s",
        (name, country, website, publisher_id),
    )
    return get_publisher(publisher_id)


@bp.delete("/<int:publisher_id>")
def delete_publisher(publisher_id):
    """DELETE a publisher. MySQL blocks this (ON DELETE RESTRICT) if the
    publisher still has games; app.py turns that into a 409 error."""
    _, deleted = db.execute(
        "DELETE FROM publishers WHERE publisher_id = %s", (publisher_id,)
    )
    if deleted == 0:
        raise ApiError("Publisher not found", 404)
    return jsonify({"message": "Publisher deleted"})
