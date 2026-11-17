"""CRUD API for games:  /api/games"""
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

import db
from utils import ApiError, get_json, require_int, require_text

bp = Blueprint("games", __name__, url_prefix="/api/games")

PLATFORMS = ["PC", "PlayStation 5", "Xbox Series X", "Nintendo Switch"]

# One query used by both "list" and "get one". It joins four tables:
# games -> publishers (many-to-one) and games -> game_genres -> genres
# (many-to-many). GROUP_CONCAT squeezes a game's genres into one row.
GAME_SELECT = """
    SELECT g.game_id, g.title, g.publisher_id, p.name AS publisher_name,
           g.platform, g.price, g.stock, g.release_date,
           GROUP_CONCAT(ge.name ORDER BY ge.name SEPARATOR ', ') AS genres,
           GROUP_CONCAT(ge.genre_id) AS genre_ids
    FROM games g
    JOIN publishers p        ON p.publisher_id = g.publisher_id
    LEFT JOIN game_genres gg ON gg.game_id = g.game_id
    LEFT JOIN genres ge      ON ge.genre_id = gg.genre_id
"""


def tidy(row):
    """Turn the genre_ids text '1,3' into a real list [1, 3]."""
    ids = row["genre_ids"]
    row["genre_ids"] = sorted(int(i) for i in ids.split(",")) if ids else []
    row["genres"] = row["genres"] or ""
    return row


def read_fields(data):
    """Validate the game fields sent by the client."""
    title = require_text(data, "title", 150)
    publisher_id = require_int(data, "publisher_id", 1)
    stock = require_int(data, "stock", 0)

    platform = data.get("platform")
    if platform not in PLATFORMS:
        raise ApiError(f"'platform' must be one of: {', '.join(PLATFORMS)}")

    try:
        price = Decimal(str(data.get("price")))
    except InvalidOperation:
        raise ApiError("'price' must be a number")
    if not price.is_finite() or price < 0 or price > Decimal("999999.99"):
        raise ApiError("'price' must be between 0 and 999999.99")

    release_date = data.get("release_date") or None
    if release_date:
        try:
            date.fromisoformat(release_date)
        except (TypeError, ValueError):
            raise ApiError("'release_date' must look like YYYY-MM-DD")

    genre_ids = data.get("genre_ids") or []
    if not isinstance(genre_ids, list) or not all(
        isinstance(i, int) and not isinstance(i, bool) for i in genre_ids
    ):
        raise ApiError("'genre_ids' must be a list of genre ids")

    fields = (title, publisher_id, platform, price, stock, release_date)
    return fields, sorted(set(genre_ids))


@bp.get("")
def list_games():
    """READ all games. Optional filters: ?search=  ?genre_id=  ?publisher_id="""
    where, params = [], []

    search = request.args.get("search", "").strip()
    if search:
        where.append("g.title LIKE %s")
        params.append(f"%{search}%")

    publisher_id = request.args.get("publisher_id", type=int)
    if publisher_id:
        where.append("g.publisher_id = %s")
        params.append(publisher_id)

    genre_id = request.args.get("genre_id", type=int)
    if genre_id:
        where.append(
            "g.game_id IN (SELECT game_id FROM game_genres WHERE genre_id = %s)"
        )
        params.append(genre_id)

    sql = GAME_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY g.game_id ORDER BY g.title, g.platform"
    return jsonify([tidy(r) for r in db.query(sql, params)])


@bp.get("/<int:game_id>")
def get_game(game_id):
    """READ one game."""
    row = db.query_one(
        GAME_SELECT + " WHERE g.game_id = %s GROUP BY g.game_id", (game_id,)
    )
    if row is None:
        raise ApiError("Game not found", 404)
    return jsonify(tidy(row))


@bp.post("")
def create_game():
    """CREATE a game and its genre links, in one transaction."""
    fields, genre_ids = read_fields(get_json())
    with db.transaction() as cur:
        cur.execute(
            "INSERT INTO games (title, publisher_id, platform, price, stock, "
            "release_date) VALUES (%s, %s, %s, %s, %s, %s)",
            fields,
        )
        game_id = cur.lastrowid
        for genre_id in genre_ids:
            cur.execute(
                "INSERT INTO game_genres (game_id, genre_id) VALUES (%s, %s)",
                (game_id, genre_id),
            )
    return get_game(game_id), 201


@bp.put("/<int:game_id>")
def update_game(game_id):
    """UPDATE a game. Its genre links are replaced with the new list."""
    fields, genre_ids = read_fields(get_json())
    get_game(game_id)  # sends 404 if it does not exist
    with db.transaction() as cur:
        cur.execute(
            "UPDATE games SET title = %s, publisher_id = %s, platform = %s, "
            "price = %s, stock = %s, release_date = %s WHERE game_id = %s",
            fields + (game_id,),
        )
        cur.execute("DELETE FROM game_genres WHERE game_id = %s", (game_id,))
        for genre_id in genre_ids:
            cur.execute(
                "INSERT INTO game_genres (game_id, genre_id) VALUES (%s, %s)",
                (game_id, genre_id),
            )
    return get_game(game_id)


@bp.delete("/<int:game_id>")
def delete_game(game_id):
    """DELETE a game. Blocked by MySQL (ON DELETE RESTRICT) if the game
    appears in any order, so order history is never broken."""
    _, deleted = db.execute("DELETE FROM games WHERE game_id = %s", (game_id,))
    if deleted == 0:
        raise ApiError("Game not found", 404)
    return jsonify({"message": "Game deleted"})
