-- Clients
CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  phone TEXT
);

-- Products (for MKL)
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  price REAL DEFAULT 0
);

-- MKL Orders
CREATE TABLE IF NOT EXISTS orders_mkl (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('не заказан', 'заказан', 'прозвонен', 'вручен')),
  date TEXT NOT NULL,
  notes TEXT,
  FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items_mkl (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  qty INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (order_id) REFERENCES orders_mkl(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Meridian Orders
CREATE TABLE IF NOT EXISTS orders_meridian (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  status TEXT NOT NULL CHECK (status IN ('не заказан', 'заказан')),
  date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items_meridian (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  product_name TEXT NOT NULL,
  qty INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (order_id) REFERENCES orders_meridian(id) ON DELETE CASCADE
);