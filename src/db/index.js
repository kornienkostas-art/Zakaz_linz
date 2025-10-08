const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');
const { format } = require('date-fns');

const appDataDir = path.join(process.cwd(), 'data');
const dbPath = path.join(appDataDir, 'ussurochki.db');
const exportDir = path.join(process.cwd(), 'exports');

let db;

function initDb() {
  if (!fs.existsSync(appDataDir)) fs.mkdirSync(appDataDir, { recursive: true });
  if (!fs.existsSync(exportDir)) fs.mkdirSync(exportDir, { recursive: true });

  db = new Database(dbPath);
  db.pragma('journal_mode = WAL');

  const schemaSql = fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf-8');
  db.exec(schemaSql);
}

async function ensureInitialized() {
  if (!db) initDb();
}

// Clients
function getClients(query) {
  const sql = query
    ? `SELECT * FROM clients WHERE name LIKE ? OR phone LIKE ? ORDER BY name`
    : `SELECT * FROM clients ORDER BY name`;
  const args = query ? [`%${query}%`, `%${query}%`] : [];
  return db.prepare(sql).all(...args);
}

function addClient({ name, phone }) {
  const info = db.prepare(`INSERT INTO clients (name, phone) VALUES (?, ?)`).run(name, phone || '');
  return { id: info.lastInsertRowid, name, phone: phone || '' };
}

function updateClient({ id, name, phone }) {
  db.prepare(`UPDATE clients SET name = ?, phone = ? WHERE id = ?`).run(name, phone || '', id);
  return { id, name, phone: phone || '' };
}

function deleteClient(id) {
  // also detach orders?
  db.prepare(`DELETE FROM orders_mkl WHERE client_id = ?`).run(id);
  db.prepare(`DELETE FROM clients WHERE id = ?`).run(id);
  return true;
}

// Products (for MKL)
function getProducts() {
  return db.prepare(`SELECT * FROM products ORDER BY name`).all();
}

function addProduct({ name, description, price }) {
  const info = db.prepare(`INSERT INTO products (name, description, price) VALUES (?, ?, ?)`).run(
    name,
    description || '',
    price || 0
  );
  return { id: info.lastInsertRowid, name, description: description || '', price: price || 0 };
}

function updateProduct({ id, name, description, price }) {
  db.prepare(`UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?`).run(
    name,
    description || '',
    price || 0,
    id
  );
  return { id, name, description: description || '', price: price || 0 };
}

function deleteProduct(id) {
  db.prepare(`DELETE FROM order_items_mkl WHERE product_id = ?`).run(id);
  db.prepare(`DELETE FROM products WHERE id = ?`).run(id);
  return true;
}

// MKL Orders
function getMklOrders({ status } = {}) {
  const base = `
    SELECT o.id, o.client_id, o.status, o.date, c.name as client_name, c.phone
    FROM orders_mkl o
    LEFT JOIN clients c ON c.id = o.client_id
  `;
  const where = status ? ` WHERE o.status = ?` : '';
  const order = ` ORDER BY o.date DESC, o.id DESC`;
  const stmt = db.prepare(base + where + order);
  return status ? stmt.all(status) : stmt.all();
}

function addMklOrder({ client_id, status = 'не заказан', date = format(new Date(), 'yyyy-MM-dd'), notes = '' }) {
  const info = db.prepare(`INSERT INTO orders_mkl (client_id, status, date, notes) VALUES (?, ?, ?, ?)`).run(
    client_id,
    status,
    date,
    notes
  );
  return { id: info.lastInsertRowid, client_id, status, date, notes };
}

function updateMklOrder({ id, client_id, status, date, notes }) {
  db.prepare(`UPDATE orders_mkl SET client_id = ?, status = ?, date = ?, notes = ? WHERE id = ?`).run(
    client_id,
    status,
    date,
    notes || '',
    id
  );
  return { id, client_id, status, date, notes: notes || '' };
}

function deleteMklOrder(id) {
  db.prepare(`DELETE FROM order_items_mkl WHERE order_id = ?`).run(id);
  db.prepare(`DELETE FROM orders_mkl WHERE id = ?`).run(id);
  return true;
}

function setMklStatus(id, status) {
  db.prepare(`UPDATE orders_mkl SET status = ? WHERE id = ?`).run(status, id);
  return { id, status };
}

function getMklOrderItems(orderId) {
  return db
    .prepare(
      `SELECT i.id, i.order_id, i.product_id, i.qty, p.name as product_name
       FROM order_items_mkl i LEFT JOIN products p ON p.id = i.product_id
       WHERE i.order_id = ? ORDER BY i.id`
    )
    .all(orderId);
}

function setMklOrderItems(orderId, items) {
  const del = db.prepare(`DELETE FROM order_items_mkl WHERE order_id = ?`);
  const ins = db.prepare(`INSERT INTO order_items_mkl (order_id, product_id, qty) VALUES (?, ?, ?)`);
  const trx = db.transaction(() => {
    del.run(orderId);
    for (const it of items) {
      ins.run(orderId, it.product_id, it.qty || 1);
    }
  });
  trx();
  return getMklOrderItems(orderId);
}

// Meridian Orders
function getMeridianOrders({ status } = {}) {
  const base = `SELECT id, status, date FROM orders_meridian`;
  const where = status ? ` WHERE status = ?` : '';
  const order = ` ORDER BY date DESC, id DESC`;
  const stmt = db.prepare(base + where + order);
  return status ? stmt.all(status) : stmt.all();
}

function addMeridianOrder() {
  const date = format(new Date(), 'yyyy-MM-dd');
  const info = db.prepare(`INSERT INTO orders_meridian (status, date) VALUES (?, ?)`).run('не заказан', date);
  return { id: info.lastInsertRowid, status: 'не заказан', date };
}

function updateMeridianOrder({ id, status, date }) {
  db.prepare(`UPDATE orders_meridian SET status = ?, date = ? WHERE id = ?`).run(status, date, id);
  return { id, status, date };
}

function deleteMeridianOrder(id) {
  db.prepare(`DELETE FROM order_items_meridian WHERE order_id = ?`).run(id);
  db.prepare(`DELETE FROM orders_meridian WHERE id = ?`).run(id);
  return true;
}

function setMeridianStatus(id, status) {
  db.prepare(`UPDATE orders_meridian SET status = ? WHERE id = ?`).run(status, id);
  return { id, status };
}

function getMeridianOrderItems(orderId) {
  return db
    .prepare(`SELECT id, order_id, product_name, qty FROM order_items_meridian WHERE order_id = ? ORDER BY id`)
    .all(orderId);
}

function setMeridianOrderItems(orderId, items) {
  const del = db.prepare(`DELETE FROM order_items_meridian WHERE order_id = ?`);
  const ins = db.prepare(`INSERT INTO order_items_meridian (order_id, product_name, qty) VALUES (?, ?, ?)`);
  const trx = db.transaction(() => {
    del.run(orderId);
    for (const it of items) {
      ins.run(orderId, it.product_name, it.qty || 1);
    }
  });
  trx();
  return getMeridianOrderItems(orderId);
}

// Export to TXT
function exportMkl(status) {
  const orders = getMklOrders({ status });
  const lines = [];
  lines.push(`УссурОЧки.рф — Заказы МКЛ — экспорт (${status || 'все'})`);
  lines.push(`Дата выгрузки: ${format(new Date(), 'yyyy-MM-dd HH:mm')}`);
  lines.push(``);
  for (const o of orders) {
    const items = getMklOrderItems(o.id);
    const itemsStr = items.map((i) => `${i.product_name} x${i.qty}`).join(', ');
    lines.push(
      `#${o.id} | ${o.date} | ${o.client_name} (${o.phone}) | ${o.status} | Товары: ${itemsStr || '—'}`
    );
  }
  const file = path.join(exportDir, `mkl_${status || 'all'}_${Date.now()}.txt`);
  fs.writeFileSync(file, lines.join('\n'), 'utf-8');
  return file;
}

function exportMeridian(status) {
  const orders = getMeridianOrders({ status });
  const lines = [];
  lines.push(`УссурОЧки.рф — Заказы Меридиан — экспорт (${status || 'все'})`);
  lines.push(`Дата выгрузки: ${format(new Date(), 'yyyy-MM-dd HH:mm')}`);
  lines.push(``);
  for (const o of orders) {
    const items = getMeridianOrderItems(o.id);
    const itemsStr = items.map((i) => `${i.product_name} x${i.qty}`).join(', ');
    lines.push(`#${o.id} | ${o.date} | ${o.status} | Товары: ${itemsStr || '—'}`);
  }
  const file = path.join(exportDir, `meridian_${status || 'all'}_${Date.now()}.txt`);
  fs.writeFileSync(file, lines.join('\n'), 'utf-8');
  return file;
}

module.exports = {
  ensureInitialized,
  // clients
  getClients,
  addClient,
  updateClient,
  deleteClient,
  // products
  getProducts,
  addProduct,
  updateProduct,
  deleteProduct,
  // MKL
  getMklOrders,
  addMklOrder,
  updateMklOrder,
  deleteMklOrder,
  setMklStatus,
  getMklOrderItems,
  setMklOrderItems,
  // Meridian
  getMeridianOrders,
  addMeridianOrder,
  updateMeridianOrder,
  deleteMeridianOrder,
  setMeridianStatus,
  getMeridianOrderItems,
  setMeridianOrderItems,
  // Export
  exportMkl,
  exportMeridian
};