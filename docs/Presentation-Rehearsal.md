# Savepoint presentation rehearsal

La'Damian Cunningham — November 19, 2026

Repository: https://github.com/LCUNNIN4/savepoint-game-store

## Five-minute speaking plan

1. **0:00–0:25 — Introduction.** “Savepoint is a staff application for a video game store. It manages games, customers and orders using a relational database.”
2. **0:25–0:55 — Architecture.** “The browser sends JSON to Flask. Flask validates it and runs SQL through the MySQL connector. The database stores the records and enforces relationships.”
3. **0:55–1:35 — Database.** Explain one publisher to many games and one customer to many orders. Explain why game_genres and order_items are junction tables. Mention that order_items stores the purchase-time price.
4. **1:35–2:05 — CRUD.** “POST creates, GET reads, PUT updates and DELETE removes records.” Show the game catalogue and its controls.
5. **2:05–2:50 — Transactions.** Explain an order with 8 copies available: buying 2 leaves 6, and cancelling the pending order restores 8. If any requested game has insufficient stock, the transaction rolls back the entire order.
6. **2:50–3:15 — Verification.** “All 12 API tests passed. They cover CRUD, constraints and order behaviour. This is a local demonstration; login and payments are outside its scope.”
7. **3:15–5:00 — Live demo.** Follow the steps below and finish by showing the repository link.

Use these as practice notes, then explain the project in your own words.

## Before class

- Start MySQL and double-click **Start Game Store.cmd** in your project folder.
- Open http://127.0.0.1:5000/ and verify that the dashboard shows “Store connected”.
- Have the presentation, report and GitHub page open.
- Use the supplied sample customers and games for the demonstration.
- Do not run `init_db.py` or the automated tests against data you want to keep. They recreate/reset sample data.

## Live demo sequence

1. Open **Genres** and add `Class Demo` to show creation.
2. Find that entry to show reading, then edit it to `Class Demo Updated`.
3. Delete that unused genre to show deletion. Avoid deleting existing catalogue data.
4. Open **Games**, choose a game with stock, and note its quantity.
5. Select **New order**, choose a sample customer, add that game with quantity 1, and place the order.
6. Verify that stock fell by 1. Open **Orders**, inspect the new order's details, and explain its saved price.
7. Cancel that pending order and verify that stock returned to its starting value.
8. If the server is unavailable, use the report screenshots and explain these same steps.

## Questions you should be able to answer

**Why MySQL?** It stores related records and enforces keys, relationships and constraints. InnoDB supports the transactions used by orders.

**What is a primary key?** A column or combination of columns that uniquely identifies a row, such as game_id or the game_id/genre_id pair.

**What is a foreign key?** A reference to a row in another table. games.publisher_id points to publishers.publisher_id.

**Why have game_genres?** A game may have several genres, and a genre may apply to several games. The junction table stores each association without repeating game details.

**Why save unit_price in order_items?** It is the price charged for that particular purchase. Changing today's catalogue price must not rewrite historical orders.

**What does a transaction do?** It groups several changes so they all succeed together or are all rolled back. This prevents a partial order from deducting only some stock.

**What does FOR UPDATE do?** It locks selected game rows during the transaction so competing orders cannot both treat the same last copy as available.

**Why use SQL parameters?** Values are passed separately from SQL text instead of being concatenated into the query.

**Why can some deletes fail?** Foreign keys protect records that other records still reference. For example, a game in an order cannot be removed.

**What is order_totals?** A database view that calculates item counts and totals from order_items. It avoids storing a second total that could become inconsistent.

**Why does cancellation not add stock twice?** The API only allows a pending order to change status. A cancelled order cannot be cancelled again.

**Does pip install MySQL Server?** No. Pip installs the Python dependencies, including the connector. MySQL Server is installed and started separately.

**What did AI help with?** AI assisted development, UI changes and documentation. Be specific about your own review, changes and understanding; do not claim work or understanding you cannot demonstrate.

## Files to know

- `database/schema.sql`: tables, foreign keys, constraints and the view.
- `routes/games.py`: catalogue CRUD and filtering.
- `routes/orders.py`: order transactions and stock restoration.
- `db.py`: pooled connections, parameterised queries and transaction helper.
- `static/app.js`: API calls, section navigation and form saves.
- `requirements.txt`: pinned Python packages installed by pip.

## Submission checklist

- Submit **Savepoint-Project-Report.pdf** by November 18, 2026.
- Include https://github.com/LCUNNIN4/savepoint-game-store wherever the course asks for the repository URL.
- Check the repository opens while signed out.
- Rehearse the five-minute presentation and the stock example before November 19.
- Follow any additional upload or naming rules in your course portal.
