-- =====================================================================
-- Game Store - sample data.  Run after schema.sql.
-- Prices and stock numbers are made up for demonstration.
-- =====================================================================
USE gamestore;

INSERT INTO publishers (publisher_id, name, country, website) VALUES
  (1, 'Nintendo',        'Japan',         'https://www.nintendo.com'),
  (2, 'Sony Interactive Entertainment', 'United States', 'https://www.playstation.com'),
  (3, 'Xbox Game Studios', 'United States', 'https://www.xbox.com'),
  (4, 'Capcom',          'Japan',         'https://www.capcom.com'),
  (5, 'Bandai Namco',    'Japan',         'https://www.bandainamcoent.com'),
  (6, 'Supergiant Games', 'United States', 'https://www.supergiantgames.com');

INSERT INTO genres (genre_id, name) VALUES
  (1, 'Action'), (2, 'Adventure'), (3, 'RPG'), (4, 'Shooter'),
  (5, 'Racing'), (6, 'Roguelike'), (7, 'Platformer'), (8, 'Horror');

INSERT INTO games (game_id, title, publisher_id, platform, price, stock, release_date) VALUES
  (1,  'The Legend of Zelda: Tears of the Kingdom', 1, 'Nintendo Switch', 69.99, 25, '2023-05-12'),
  (2,  'Super Mario Odyssey',      1, 'Nintendo Switch', 59.99, 18, '2017-10-27'),
  (3,  'Mario Kart 8 Deluxe',      1, 'Nintendo Switch', 59.99, 30, '2017-04-28'),
  (4,  'God of War Ragnarok',      2, 'PlayStation 5',   69.99, 12, '2022-11-09'),
  (5,  'Marvel''s Spider-Man 2',   2, 'PlayStation 5',   69.99,  9, '2023-10-20'),
  (6,  'Halo Infinite',            3, 'Xbox Series X',   59.99, 14, '2021-12-08'),
  (7,  'Forza Horizon 5',          3, 'Xbox Series X',   59.99,  4, '2021-11-09'),
  (8,  'Resident Evil 4',          4, 'PlayStation 5',   39.99, 20, '2023-03-24'),
  (9,  'Monster Hunter Rise',      4, 'PC',              39.99,  3, '2022-01-12'),
  (10, 'Elden Ring',               5, 'PC',              59.99, 22, '2022-02-25'),
  (11, 'Hades',                    6, 'PC',              24.99, 40, '2020-09-17'),
  (12, 'Hades',                    6, 'Nintendo Switch', 24.99,  0, '2020-09-17');

INSERT INTO game_genres (game_id, genre_id) VALUES
  (1, 1), (1, 2), (2, 7), (2, 2), (3, 5),
  (4, 1), (4, 2), (5, 1), (5, 2), (6, 4),
  (7, 5), (8, 8), (8, 4), (9, 1), (9, 3),
  (10, 1), (10, 3), (11, 6), (11, 1), (12, 6), (12, 1);

INSERT INTO customers (customer_id, first_name, last_name, email, phone) VALUES
  (1, 'Alex',   'Rivera',  'alex.rivera@example.com',  '555-0101'),
  (2, 'Jordan', 'Kim',     'jordan.kim@example.com',   '555-0102'),
  (3, 'Sam',    'Patel',   'sam.patel@example.com',    '555-0103'),
  (4, 'Taylor', 'Nguyen',  'taylor.nguyen@example.com', NULL);

INSERT INTO orders (order_id, customer_id, order_date, status) VALUES
  (1, 1, '2026-11-01 10:15:00', 'COMPLETED'),
  (2, 2, '2026-11-03 14:40:00', 'COMPLETED'),
  (3, 1, '2026-11-08 09:05:00', 'PENDING'),
  (4, 3, '2026-11-10 17:30:00', 'CANCELLED');

INSERT INTO order_items (order_id, game_id, quantity, unit_price) VALUES
  (1, 1, 1, 69.99), (1, 3, 1, 59.99),
  (2, 10, 1, 59.99), (2, 11, 2, 24.99),
  (3, 4, 1, 69.99),
  (4, 6, 1, 59.99);
