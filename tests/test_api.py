"""API tests.  Run with:  python -m pytest tests -v

WARNING: these tests reset the database to the sample data first
(they call init_db), so do not run them if you want to keep your data.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import init_db  # noqa: E402
from app import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    init_db.main()
    return app.test_client()


def stock_of(client, game_id):
    return client.get(f"/api/games/{game_id}").get_json()["stock"]


def test_read_lists(client):
    for table in ("games", "publishers", "genres", "customers", "orders"):
        response = client.get(f"/api/{table}")
        assert response.status_code == 200
        assert len(response.get_json()) > 0


def test_game_crud(client):
    # Create
    new = {"title": "Test Game", "publisher_id": 1, "platform": "PC",
           "price": 19.99, "stock": 5, "release_date": "2026-01-15",
           "genre_ids": [1, 3]}
    response = client.post("/api/games", json=new)
    assert response.status_code == 201
    game = response.get_json()
    assert game["genres"] == "Action, RPG"
    game_id = game["game_id"]

    # Read
    assert client.get(f"/api/games/{game_id}").get_json()["title"] == "Test Game"

    # Update (also replaces the genres)
    new.update(title="Test Game 2", price=9.5, genre_ids=[6])
    response = client.put(f"/api/games/{game_id}", json=new)
    assert response.status_code == 200
    updated = response.get_json()
    assert (updated["title"], updated["price"], updated["genres"]) == ("Test Game 2", 9.5, "Roguelike")

    # Delete
    assert client.delete(f"/api/games/{game_id}").status_code == 200
    assert client.get(f"/api/games/{game_id}").status_code == 404


def test_game_search_and_filter(client):
    titles = [g["title"] for g in client.get("/api/games?search=mario").get_json()]
    assert titles == ["Mario Kart 8 Deluxe", "Super Mario Odyssey"]
    racing = client.get("/api/games?genre_id=5").get_json()
    assert {g["title"] for g in racing} == {"Mario Kart 8 Deluxe", "Forza Horizon 5"}


def test_validation_errors(client):
    bad = {"title": "", "publisher_id": 1, "platform": "PC", "price": 1, "stock": 1}
    assert client.post("/api/games", json=bad).status_code == 400
    bad.update(title="X", price=-5)
    assert client.post("/api/games", json=bad).status_code == 400
    bad.update(price=5, platform="Dreamcast")
    assert client.post("/api/games", json=bad).status_code == 400
    bad.update(platform="PC", publisher_id=9999)  # foreign key does not exist
    assert client.post("/api/games", json=bad).status_code == 400
    assert client.post("/api/customers", json={"first_name": "A"}).status_code == 400


def test_duplicates_rejected(client):
    assert client.post("/api/genres", json={"name": "Action"}).status_code == 409
    dup = {"first_name": "A", "last_name": "B", "email": "alex.rivera@example.com"}
    assert client.post("/api/customers", json=dup).status_code == 409


def test_simple_crud_tables(client):
    cases = [
        ("publishers", "publisher_id", {"name": "Test Pub", "country": "Canada"}, {"name": "Test Pub 2"}),
        ("genres", "genre_id", {"name": "Puzzle"}, {"name": "Puzzle 2"}),
        ("customers", "customer_id",
         {"first_name": "T", "last_name": "User", "email": "t@example.com"},
         {"first_name": "T", "last_name": "Changed", "email": "t@example.com"}),
    ]
    for table, key, create, update in cases:
        response = client.post(f"/api/{table}", json=create)
        assert response.status_code == 201, table
        row_id = response.get_json()[key]
        response = client.put(f"/api/{table}/{row_id}", json=update)
        assert response.status_code == 200, table
        for field, value in update.items():
            assert response.get_json()[field] == value
        assert client.delete(f"/api/{table}/{row_id}").status_code == 200
        assert client.get(f"/api/{table}/{row_id}").status_code == 404
        assert client.delete(f"/api/{table}/{row_id}").status_code == 404


def test_delete_blocked_by_foreign_keys(client):
    assert client.delete("/api/publishers/1").status_code == 409  # has games
    assert client.delete("/api/customers/1").status_code == 409   # has orders
    assert client.delete("/api/games/1").status_code == 409       # is in an order


def test_order_takes_and_restores_stock(client):
    before = stock_of(client, 2)
    response = client.post("/api/orders", json={
        "customer_id": 2, "items": [{"game_id": 2, "quantity": 3}]})
    assert response.status_code == 201
    order = response.get_json()
    assert order["status"] == "PENDING"
    assert order["total"] == pytest.approx(3 * 59.99)
    assert stock_of(client, 2) == before - 3

    # Cancelling puts the stock back, and the status is then final.
    response = client.put(f"/api/orders/{order['order_id']}", json={"status": "CANCELLED"})
    assert response.status_code == 200
    assert stock_of(client, 2) == before
    response = client.put(f"/api/orders/{order['order_id']}", json={"status": "COMPLETED"})
    assert response.status_code == 409
    assert client.delete(f"/api/orders/{order['order_id']}").status_code == 200
    assert stock_of(client, 2) == before  # not restored twice


def test_order_is_all_or_nothing(client):
    """If one item is out of stock the whole order is rolled back."""
    orders_before = len(client.get("/api/orders").get_json())
    stock_before = stock_of(client, 2)
    response = client.post("/api/orders", json={
        "customer_id": 2,
        "items": [{"game_id": 2, "quantity": 1}, {"game_id": 12, "quantity": 1}]})
    assert response.status_code == 409  # game 12 has 0 stock
    assert len(client.get("/api/orders").get_json()) == orders_before
    assert stock_of(client, 2) == stock_before


def test_complete_and_delete_pending_order(client):
    before = stock_of(client, 3)
    first = client.post("/api/orders", json={
        "customer_id": 3, "items": [{"game_id": 3, "quantity": 2}]}).get_json()
    second = client.post("/api/orders", json={
        "customer_id": 3, "items": [{"game_id": 3, "quantity": 1}]}).get_json()
    assert stock_of(client, 3) == before - 3

    # Completed orders keep their stock taken, even when deleted later.
    assert client.put(f"/api/orders/{first['order_id']}", json={"status": "COMPLETED"}).status_code == 200
    assert client.delete(f"/api/orders/{first['order_id']}").status_code == 200
    assert stock_of(client, 3) == before - 3

    # Deleting a PENDING order puts its stock back.
    assert client.delete(f"/api/orders/{second['order_id']}").status_code == 200
    assert stock_of(client, 3) == before - 2


def test_price_is_frozen_in_order(client):
    """Changing a game's price later must not change old orders."""
    game = client.get("/api/games/11").get_json()
    order = client.post("/api/orders", json={
        "customer_id": 4, "items": [{"game_id": 11, "quantity": 1}]}).get_json()
    game.update(price=99.0, stock=game["stock"] - 1)
    assert client.put("/api/games/11", json=game).status_code == 200
    again = client.get(f"/api/orders/{order['order_id']}").get_json()
    assert again["total"] == pytest.approx(24.99)


def test_stats(client):
    stats = client.get("/api/stats").get_json()
    assert stats["counts"]["games"] == 12
    assert any(g["title"] == "Hades" and g["stock"] == 0 for g in stats["low_stock"])
