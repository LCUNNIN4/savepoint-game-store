"""CRUD API for genres:  /api/genres"""
from flask import Blueprint, jsonify

import db
from utils import ApiError, get_json, require_text

bp = Blueprint("genres", __name__, url_prefix="/api/genres")


@bp.get("")
def list_genres():
    """READ all genres, with how many games are tagged with each."""
    rows = db.query(
        """
        SELECT ge.genre_id, ge.name, COUNT(gg.game_id) AS game_count
        FROM genres ge
        LEFT JOIN game_genres gg ON gg.genre_id = ge.genre_id
        GROUP BY ge.genre_id
        ORDER BY ge.name
        """
    )
    return jsonify(rows)


@bp.get("/<int:genre_id>")
def get_genre(genre_id):
    """READ one genre."""
    row = db.query_one("SELECT * FROM genres WHERE genre_id = %s", (genre_id,))
    if row is None:
        raise ApiError("Genre not found", 404)
    return jsonify(row)


@bp.post("")
def create_genre():
    """CREATE a genre."""
    name = require_text(get_json(), "name", 50)
    new_id, _ = db.execute("INSERT INTO genres (name) VALUES (%s)", (name,))
    return get_genre(new_id), 201


@bp.put("/<int:genre_id>")
def update_genre(genre_id):
    """UPDATE (rename) a genre."""
    name = require_text(get_json(), "name", 50)
    get_genre(genre_id)  # sends 404 if it does not exist
    db.execute("UPDATE genres SET name = %s WHERE genre_id = %s", (name, genre_id))
    return get_genre(genre_id)


@bp.delete("/<int:genre_id>")
def delete_genre(genre_id):
    """DELETE a genre. Its rows in game_genres are removed automatically
    (ON DELETE CASCADE); the games themselves are kept."""
    _, deleted = db.execute("DELETE FROM genres WHERE genre_id = %s", (genre_id,))
    if deleted == 0:
        raise ApiError("Genre not found", 404)
    return jsonify({"message": "Genre deleted"})
