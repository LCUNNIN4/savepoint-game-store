"""CRUD API for orders:  /api/orders

Stock rules:
  * Creating an order takes the games out of stock.
  * Cancelling a PENDING order (or deleting one) puts the stock back.
  * A PENDING order can become COMPLETED or CANCELLED. After that the
    status is final.
"""
from flask import Blueprint, jsonify

import db
from utils import ApiError, get_json, require_int

bp = Blueprint("orders", __name__, url_prefix="/api/orders")

# Joins orders with the customer and with the order_totals VIEW.
ORDER_SELECT = """
    SELECT o.order_id, o.customer_id,
           CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
           o.order_date, o.status, t.item_count, t.total
    FROM orders o
    JOIN customers c    ON c.customer_id = o.customer_id
    JOIN order_totals t ON t.order_id = o.order_id
"""


@bp.get("")
def list_orders():
    """READ all orders, newest first."""
    return jsonify(db.query(ORDER_SELECT + " ORDER BY o.order_date DESC, o.order_id DESC"))


@bp.get("/<int:order_id>")
def get_order(order_id):
    """READ one order together with its line items."""
    order = db.query_one(ORDER_SELECT + " WHERE o.order_id = %s", (order_id,))
    if order is None:
        raise ApiError("Order not found", 404)
    order["items"] = db.query(
        """
        SELECT oi.game_id, g.title, g.platform, oi.quantity, oi.unit_price,
               oi.quantity * oi.unit_price AS line_total
        FROM order_items oi
        JOIN games g ON g.game_id = oi.game_id
        WHERE oi.order_id = %s
        ORDER BY g.title
        """,
        (order_id,),
    )
    return jsonify(order)


@bp.post("")
def create_order():
    """CREATE an order.

    Body: {"customer_id": 1, "items": [{"game_id": 4, "quantity": 2}, ...]}

    Everything happens in ONE transaction: if any game is out of stock,
    nothing is saved at all.
    """
    data = get_json()
    customer_id = require_int(data, "customer_id", 1)
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ApiError("An order needs at least one item")

    # Add up quantities in case the same game was listed twice.
    wanted = {}
    for item in items:
        if not isinstance(item, dict):
            raise ApiError("Each item needs a game_id and a quantity")
        game_id = require_int(item, "game_id", 1)
        wanted[game_id] = wanted.get(game_id, 0) + require_int(item, "quantity", 1)

    with db.transaction() as cur:
        cur.execute(
            "SELECT customer_id FROM customers WHERE customer_id = %s", (customer_id,)
        )
        if cur.fetchone() is None:
            raise ApiError("Customer not found", 404)

        cur.execute("INSERT INTO orders (customer_id) VALUES (%s)", (customer_id,))
        order_id = cur.lastrowid

        for game_id, quantity in sorted(wanted.items()):
            # FOR UPDATE locks the game's row until we commit, so two
            # customers cannot both buy the last copy at the same time.
            cur.execute(
                "SELECT title, price, stock FROM games WHERE game_id = %s FOR UPDATE",
                (game_id,),
            )
            game = cur.fetchone()
            if game is None:
                raise ApiError(f"Game {game_id} not found", 404)
            if game["stock"] < quantity:
                raise ApiError(
                    f"Not enough stock for '{game['title']}' "
                    f"(wanted {quantity}, only {game['stock']} left)",
                    409,
                )
            cur.execute(
                "INSERT INTO order_items (order_id, game_id, quantity, unit_price) "
                "VALUES (%s, %s, %s, %s)",
                (order_id, game_id, quantity, game["price"]),
            )
            cur.execute(
                "UPDATE games SET stock = stock - %s WHERE game_id = %s",
                (quantity, game_id),
            )
    return get_order(order_id), 201


def restore_stock(cur, order_id):
    """Put every game of an order back into stock (one UPDATE with a JOIN)."""
    cur.execute(
        """
        UPDATE games g
        JOIN order_items oi ON oi.game_id = g.game_id
        SET g.stock = g.stock + oi.quantity
        WHERE oi.order_id = %s
        """,
        (order_id,),
    )


@bp.put("/<int:order_id>")
def update_order(order_id):
    """UPDATE an order's status.  Body: {"status": "COMPLETED"}"""
    new_status = get_json().get("status")
    if new_status not in ("COMPLETED", "CANCELLED"):
        raise ApiError("'status' must be COMPLETED or CANCELLED")

    with db.transaction() as cur:
        cur.execute(
            "SELECT status FROM orders WHERE order_id = %s FOR UPDATE", (order_id,)
        )
        order = cur.fetchone()
        if order is None:
            raise ApiError("Order not found", 404)
        if order["status"] != "PENDING":
            raise ApiError(
                f"Order is already {order['status']} and cannot be changed", 409
            )
        if new_status == "CANCELLED":
            restore_stock(cur, order_id)
        cur.execute(
            "UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id)
        )
    return get_order(order_id)


@bp.delete("/<int:order_id>")
def delete_order(order_id):
    """DELETE an order. Its order_items rows go with it (ON DELETE CASCADE).
    If the order was still PENDING, its stock is put back first."""
    with db.transaction() as cur:
        cur.execute(
            "SELECT status FROM orders WHERE order_id = %s FOR UPDATE", (order_id,)
        )
        order = cur.fetchone()
        if order is None:
            raise ApiError("Order not found", 404)
        if order["status"] == "PENDING":
            restore_stock(cur, order_id)
        cur.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
    return jsonify({"message": "Order deleted"})
