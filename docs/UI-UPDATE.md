# Savepoint UI update

Savepoint is the new name and interface for the existing Game Store application.
The Flask routes, MySQL schema and pip requirements remain the same.

## Visual changes

- Charcoal panels, electric-green highlights and a small pixel-cross logo.
- Numbered navigation for overview, games, publishers, genres, customers and orders.
- Dashboard totals, sales bars and a stock-watch panel populated from the API.
- Game initials, platform colours and catalogue references in the inventory table.
- Matching dialogs, visible field labels, keyboard focus outlines and inline save errors.
- On small screens, navigation and wide tables scroll horizontally inside their containers.
- System fonts and local assets allow the interface to work without external font or image services.

## Code walkthrough

`static/index.html` contains the navigation, six sections and edit dialogs.
`static/style.css` groups rules by navigation, overview, tables, forms and screen size.
The colour variables are at the start of that file.

`static/app.js` keeps the existing resource-specific loading functions. The `pages`
object supplies section headings. `showTab` changes the active section, while
`api` sends JSON requests to Flask. `bindSaveForm` handles the repeated save flow
for games, publishers, genres and customers: collect fields, save, refresh, or
display an error in the dialog. Orders retain their own stock-aware workflow.

Game search waits briefly after typing and ignores outdated responses. Placing
an order refreshes whichever section is visible so stock counts stay current.
Connection status reflects API requests instead of showing a fixed online label.

Frontend indentation and spacing are consistent. Python changes only shorten
comments and docstrings; route behaviour and database logic are unchanged.

## Validation

All 12 existing API tests passed with Python 3.12 and MySQL 8.0 on an isolated
test database. Browser checks covered search, publisher/genre/customer/game
creation, duplicate-entry errors, game edits, order totals, stock deductions,
order details and cancellation restoring stock. Desktop and phone layouts were
visually checked. Test records were kept out of the user's running database.

The original report and explanation PDFs are preserved. Their UI screenshots
show the earlier design; use the Savepoint screenshots in the README for the
updated interface. The report's `pip install -r requirements.txt` instruction
still applies inside the virtual environment.
