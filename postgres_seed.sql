-- Demo schema + seed data for local Postgres tests.
-- Run with: psql -U <user> -d <db> -f test-data/postgres_seed.sql

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  country TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE subscriptions (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id),
  plan TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE categories (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  category_id INT NOT NULL REFERENCES categories(id),
  name TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id),
  status TEXT NOT NULL,
  total_amount NUMERIC(10, 2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id INT NOT NULL REFERENCES orders(id),
  product_id INT NOT NULL REFERENCES products(id),
  price NUMERIC(10, 2) NOT NULL,
  quantity INT NOT NULL
);

INSERT INTO users (email, country, created_at) VALUES
('ava@example.com', 'US', NOW() - INTERVAL '400 days'),
('liam@example.com', 'CA', NOW() - INTERVAL '350 days'),
('noah@example.com', 'IN', NOW() - INTERVAL '300 days'),
('mia@example.com', 'US', NOW() - INTERVAL '280 days'),
('emma@example.com', 'DE', NOW() - INTERVAL '250 days'),
('olivia@example.com', 'FR', NOW() - INTERVAL '200 days'),
('lucas@example.com', 'AU', NOW() - INTERVAL '180 days'),
('sophia@example.com', 'IN', NOW() - INTERVAL '170 days');

INSERT INTO subscriptions (user_id, plan, status, started_at) VALUES
(1, 'pro', 'active', NOW() - INTERVAL '200 days'),
(2, 'basic', 'active', NOW() - INTERVAL '190 days'),
(3, 'pro', 'active', NOW() - INTERVAL '180 days'),
(4, 'enterprise', 'active', NOW() - INTERVAL '160 days'),
(5, 'basic', 'paused', NOW() - INTERVAL '140 days'),
(6, 'pro', 'active', NOW() - INTERVAL '120 days'),
(7, 'basic', 'active', NOW() - INTERVAL '100 days'),
(8, 'enterprise', 'active', NOW() - INTERVAL '80 days');

INSERT INTO categories (name) VALUES
('Books'),
('Electronics'),
('Home'),
('Office');

INSERT INTO products (category_id, name, is_active) VALUES
(1, 'SQL Mastery', TRUE),
(1, 'Async Python', TRUE),
(2, 'Mechanical Keyboard', TRUE),
(2, '27in Monitor', TRUE),
(3, 'Ergo Chair', TRUE),
(4, 'Notebook Pack', TRUE),
(4, 'Marker Set', TRUE),
(3, 'Desk Lamp', TRUE);

INSERT INTO orders (user_id, status, total_amount, created_at) VALUES
(1, 'completed', 109.99, NOW() - INTERVAL '30 days'),
(1, 'completed', 249.00, NOW() - INTERVAL '14 days'),
(2, 'pending', 59.90, NOW() - INTERVAL '8 days'),
(3, 'completed', 420.00, NOW() - INTERVAL '60 days'),
(3, 'completed', 89.50, NOW() - INTERVAL '22 days'),
(4, 'completed', 999.99, NOW() - INTERVAL '10 days'),
(5, 'cancelled', 70.00, NOW() - INTERVAL '120 days'),
(6, 'completed', 155.75, NOW() - INTERVAL '4 days'),
(7, 'pending', 45.25, NOW() - INTERVAL '1 days'),
(8, 'completed', 310.10, NOW() - INTERVAL '3 days');

INSERT INTO order_items (order_id, product_id, price, quantity) VALUES
(1, 1, 39.99, 1),
(1, 6, 35.00, 2),
(2, 3, 99.00, 1),
(2, 2, 75.00, 2),
(3, 8, 59.90, 1),
(4, 4, 210.00, 2),
(5, 1, 39.99, 1),
(5, 7, 24.75, 2),
(6, 5, 499.99, 2),
(7, 6, 35.00, 2),
(8, 3, 155.75, 1),
(9, 7, 15.08, 3),
(10, 2, 155.05, 2);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
