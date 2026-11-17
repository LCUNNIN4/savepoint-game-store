"""Read-only summary numbers for the dashboard:  /api/stats"""
from flask import Blueprint, jsonify

import db

bp = Blueprint("stats", __name__, url_prefix="/api/stats")

LOW_STOCK_LIMIT = 5


@bp.get("")
def get_stats():
    counts = db.query_one(
        """
        SELECT (SELECT COUNT(*) FROM games)     AS games,
               (SELECT COUNT(*) FROM customers) AS customers,
               (SELECT COUNT(*) FROM orders)    AS orders,
               (SELECT COALESCE(SUM(t.total), 0)
                  FROM orders o
                  JOIN order_totals t ON t.order_id = o.order_id
                 WHERE o.status = 'COMPLETED')  AS revenue
        """
    )
    low_stock = db.query(
        "SELECT game_id, title, platform, stock FROM games "
        "WHERE stock <= %s ORDER BY stock, title",
        (LOW_STOCK_LIMIT,),
    )
    top_sellers = db.query(
        """
        SELECT g.title, g.platform, CAST(SUM(oi.quantity) AS SIGNED) AS units_sold,
               SUM(oi.quantity * oi.unit_price) AS revenue
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN games g  ON g.game_id = oi.game_id
        WHERE o.status = 'COMPLETED'
        GROUP BY g.game_id
        ORDER BY units_sold DESC, revenue DESC
        LIMIT 5
        """
    )
    return jsonify(
        {
            "counts": counts,
            "low_stock_limit": LOW_STOCK_LIMIT,
            "low_stock": low_stock,
            "top_sellers": top_sellers,
        }
    )
