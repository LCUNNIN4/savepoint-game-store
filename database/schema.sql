-- =====================================================================
-- Game Store - database schema (MySQL 8)
-- Run this file first, then seed.sql.  (Or just run: python init_db.py)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS gamestore
  CHARACTER SET utf8mb4;
USE gamestore;

-- Drop in reverse dependency order so the script can be re-run safely.
DROP VIEW  IF EXISTS order_totals;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS game_genres;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS publishers;

-- ---------------------------------------------------------------------
-- publishers: companies that publish games.  One publisher -> many games.
-- ---------------------------------------------------------------------
CREATE TABLE publishers (
    publisher_id INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    country      VARCHAR(60),
    website      VARCHAR(200),
    CONSTRAINT uq_publisher_name UNIQUE (name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- genres: lookup table of game genres.
-- ---------------------------------------------------------------------
CREATE TABLE genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(50) NOT NULL,
    CONSTRAINT uq_genre_name UNIQUE (name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- games: the products the store sells.
-- ---------------------------------------------------------------------
CREATE TABLE games (
    game_id      INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(150) NOT NULL,
    publisher_id INT NOT NULL,
    platform     ENUM('PC', 'PlayStation 5', 'Xbox Series X', 'Nintendo Switch') NOT NULL,
    price        DECIMAL(8,2) NOT NULL,
    stock        INT NOT NULL DEFAULT 0,
    release_date DATE,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_games_publisher FOREIGN KEY (publisher_id)
        REFERENCES publishers (publisher_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_game_title_platform UNIQUE (title, platform),
    CONSTRAINT chk_game_price CHECK (price >= 0),
    CONSTRAINT chk_game_stock CHECK (stock >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- game_genres: junction table for the many-to-many relationship
-- between games and genres (a game can have several genres).
-- ---------------------------------------------------------------------
CREATE TABLE game_genres (
    game_id  INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (game_id, genre_id),
    CONSTRAINT fk_gg_game FOREIGN KEY (game_id)
        REFERENCES games (game_id) ON DELETE CASCADE,
    CONSTRAINT fk_gg_genre FOREIGN KEY (genre_id)
        REFERENCES genres (genre_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- customers: people who buy games.
-- ---------------------------------------------------------------------
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(120) NOT NULL,
    phone       VARCHAR(25),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_customer_email UNIQUE (email)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- orders: one row per purchase.  One customer -> many orders.
-- ---------------------------------------------------------------------
CREATE TABLE orders (
    order_id    INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status      ENUM('PENDING', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- order_items: the games inside each order (junction of orders and games).
-- unit_price is copied from games.price at purchase time, so changing a
-- game's price later does not change past orders.
-- ---------------------------------------------------------------------
CREATE TABLE order_items (
    order_id   INT NOT NULL,
    game_id    INT NOT NULL,
    quantity   INT NOT NULL,
    unit_price DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (order_id, game_id),
    CONSTRAINT fk_oi_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE CASCADE,
    CONSTRAINT fk_oi_game FOREIGN KEY (game_id)
        REFERENCES games (game_id) ON DELETE RESTRICT,
    CONSTRAINT chk_oi_quantity CHECK (quantity > 0),
    CONSTRAINT chk_oi_price CHECK (unit_price >= 0)
) ENGINE=InnoDB;

-- Indexes for the columns we search and join on most often.
-- (Foreign keys and UNIQUE constraints already get indexes automatically.)
CREATE INDEX idx_orders_date ON orders (order_date);

-- ---------------------------------------------------------------------
-- order_totals: a view that calculates each order's item count and total.
-- The total is derived data, so we compute it instead of storing it.
-- ---------------------------------------------------------------------
CREATE VIEW order_totals AS
SELECT o.order_id,
       CAST(COALESCE(SUM(oi.quantity), 0) AS SIGNED) AS item_count,
       COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total
FROM orders o
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id;
