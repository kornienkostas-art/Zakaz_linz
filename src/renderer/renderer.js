/**
 * Простая логика интерфейса
 */
const api = window.api;

const state = {
  theme: 'dark',
  // MKL
  mklOrders: [],
  mklSelectedOrderId: null,
  mklOrderItemsBuffer: [], // временный буфер для позиций товара
  clients: [],
  selectedClientId: null,
  products: [],
  // Meridian
  meridianOrders: [],
  meridianSelectedOrderId: null,
  meridianItemsBuffer: []
};

// Навигация между представлениями
function goView(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if (id === 'mklView') {
    refreshMKL();
  } else if (id === 'meridianView') {
    refreshMeridian();
  }
}
window.goView = goView;

// Тема
const themeSwitch = document.getElementById('themeSwitch');
function applyTheme(theme) {
  const html = document.documentElement;
  html.setAttribute('data-theme', theme);
  const link = document.querySelector('link[href*="shoelace"][rel="stylesheet"]');
  if (link) {
    link.href = theme === 'dark'
      ? 'https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.6.0/cdn/themes/dark.css'
      : 'https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.6.0/cdn/themes/light.css';
  }
}
themeSwitch.addEventListener('sl-change', () => {
  state.theme = themeSwitch.checked ? 'dark' : 'light';
  themeSwitch.textContent = themeSwitch.checked ? 'Тёмная' : 'Светлая';
  applyTheme(state.theme);
});
applyTheme(state.theme);

// ======================= MKL =======================

const mklFilter = document.getElementById('mklFilter');
const mklOrdersList = document.getElementById('mklOrdersList');
const mklAddOrderBtn = document.getElementById('mklAddOrderBtn');
const mklExportBtn = document.getElementById('mklExportBtn');
const mklOrderItemsEl = document.getElementById('mklOrderItems');
const mklSaveItemsBtn = document.getElementById('mklSaveItemsBtn');

const clientsListEl = document.getElementById('clientsList');
const clientAddBtn = document.getElementById('clientAddBtn');
const clientNameEl = document.getElementById('clientName');
const clientPhoneEl = document.getElementById('clientPhone');

const productsListEl = document.getElementById('productsList');
const productAddBtn = document.getElementById('productAddBtn');
const productNameEl = document.getElementById('productName');
const productDescEl = document.getElementById('productDesc');
const productPriceEl = document.getElementById('productPrice');

function statusColor(status) {
  switch (status) {
    case 'не заказан': return 'danger';
    case 'заказан': return 'success';
    case 'прозвонен': return 'primary';
    case 'вручен': return 'success';
    default: return 'neutral';
  }
}

async function refreshMKL() {
  const filter = mklFilter.value || '';
  state.mklOrders = await api.getMklOrders(filter ? { status: filter } : {});
  state.clients = await api.getClients();
  state.products = await api.getProducts();

  renderClients();
  renderProducts();
  renderMklOrders();
  renderMklItems();
}

mklFilter.addEventListener('sl-change', refreshMKL);

function renderMklOrders() {
  mklOrdersList.innerHTML = '';
  state.mklOrders.forEach(o => {
    const card = document.createElement('sl-card');
    card.className = 'list-item order';
    const header = document.createElement('div');
    header.slot = 'header';
    header.innerHTML = `#${o.id} • ${o.date} • ${o.client_name || 'Без клиента'}`;
    card.appendChild(header);

    const badge = document.createElement('sl-badge');
    badge.variant = statusColor(o.status);
    badge.pill = true;
    badge.textContent = o.status;
    card.appendChild(badge);

    const actions = document.createElement('div');
    actions.className = 'row';
    const statusSelect = document.createElement('sl-select');
    statusSelect.size = 'small';
    statusSelect.value = o.status;
    ['не заказан', 'заказан', 'прозвонен', 'вручен'].forEach(s => {
      const opt = document.createElement('sl-option');
      opt.value = s;
      opt.textContent = s;
      statusSelect.appendChild(opt);
    });
    statusSelect.addEventListener('sl-change', async () => {
      await api.setMklStatus(o.id, statusSelect.value);
      refreshMKL();
    });

    const selectBtn = document.createElement('sl-button');
    selectBtn.size = 'small';
    selectBtn.variant = 'primary';
    selectBtn.innerHTML = '<sl-icon name="cursor"></sl-icon> Выбрать';
    selectBtn.addEventListener('click', async () => {
      state.mklSelectedOrderId = o.id;
      state.mklOrderItemsBuffer = await api.getMklOrderItems(o.id);
      renderMklItems();
    });

    const editBtn = document.createElement('sl-button');
    editBtn.size = 'small';
    editBtn.variant = 'neutral';
    editBtn.innerHTML = '<sl-icon name="pencil"></sl-icon> Редактировать';
    editBtn.addEventListener('click', async () => {
      const newDate = prompt('Дата (YYYY-MM-DD):', o.date);
      const newNotes = prompt('Примечание:', o.notes || '');
      if (newDate) {
        await api.updateMklOrder({ id: o.id, client_id: o.client_id, status: o.status, date: newDate, notes: newNotes || '' });
        refreshMKL();
      }
    });

    const delBtn = document.createElement('sl-button');
    delBtn.size = 'small';
    delBtn.variant = 'danger';
    delBtn.innerHTML = '<sl-icon name="trash"></sl-icon> Удалить';
    delBtn.addEventListener('click', async () => {
      if (confirm('Удалить заказ?')) {
        await api.deleteMklOrder(o.id);
        if (state.mklSelectedOrderId === o.id) {
          state.mklSelectedOrderId = null;
          state.mklOrderItemsBuffer = [];
        }
        refreshMKL();
      }
    });

    actions.appendChild(statusSelect);
    actions.appendChild(selectBtn);
    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    card.appendChild(actions);

    mklOrdersList.appendChild(card);
  });
}

function renderMklItems() {
  mklOrderItemsEl.innerHTML = '';
  if (!state.mklSelectedOrderId) {
    mklOrderItemsEl.innerHTML = '<small>Выберите заказ для редактирования позиций.</small>';
    return;
  }
  state.mklOrderItemsBuffer.forEach((it, idx) => {
    const row = document.createElement('div');
    row.className = 'list-item';
    row.innerHTML = `${it.product_name} • x${it.qty}`;
    const right = document.createElement('div');
    right.className = 'row';
    const qtyInput = document.createElement('sl-input');
    qtyInput.type = 'number';
    qtyInput.size = 'small';
    qtyInput.value = String(it.qty);
    qtyInput.style.width = '90px';
    qtyInput.addEventListener('sl-change', () => {
      state.mklOrderItemsBuffer[idx].qty = Number(qtyInput.value || 1);
    });
    const removeBtn = document.createElement('sl-button');
    removeBtn.size = 'small';
    removeBtn.variant = 'danger';
    removeBtn.innerHTML = '<sl-icon name="x"></sl-icon>';
    removeBtn.addEventListener('click', () => {
      state.mklOrderItemsBuffer.splice(idx, 1);
      renderMklItems();
    });
    right.appendChild(qtyInput);
    right.appendChild(removeBtn);
    row.appendChild(right);
    mklOrderItemsEl.appendChild(row);
  });

  // панель добавления позиции из списка товаров
  const addPanel = document.createElement('div');
  addPanel.className = 'row';
  const productSelect = document.createElement('sl-select');
  productSelect.placeholder = 'Выберите товар';
  state.products.forEach(p => {
    const opt = document.createElement('sl-option');
    opt.value = String(p.id);
    opt.textContent = p.name;
    productSelect.appendChild(opt);
  });

  const qtyInput = document.createElement('sl-input');
  qtyInput.type = 'number';
  qtyInput.placeholder = 'Кол-во';
  qtyInput.value = '1';
  qtyInput.style.width = '120px';

  const addBtn = document.createElement('sl-button');
  addBtn.variant = 'primary';
  addBtn.size = 'small';
  addBtn.innerHTML = '<sl-icon name="plus"></sl-icon> Добавить';
  addBtn.addEventListener('click', () => {
    const pid = Number(productSelect.value);
    if (!pid) return;
    const prod = state.products.find(p => p.id === pid);
    state.mklOrderItemsBuffer.push({ product_id: pid, product_name: prod.name, qty: Number(qtyInput.value || 1) });
    renderMklItems();
  });

  addPanel.appendChild(productSelect);
  addPanel.appendChild(qtyInput);
  addPanel.appendChild(addBtn);
  mklOrderItemsEl.appendChild(addPanel);
}

mklSaveItemsBtn.addEventListener('click', async () => {
  if (!state.mklSelectedOrderId) return;
  const items = state.mklOrderItemsBuffer.map(it => ({ product_id: it.product_id, qty: it.qty }));
  await api.setMklOrderItems(state.mklSelectedOrderId, items);
  alert('Позиции сохранены');
  refreshMKL();
});

mklAddOrderBtn.addEventListener('click', async () => {
  if (!state.selectedClientId) {
    alert('Выберите клиента слева, затем добавьте заказ.');
    return;
  }
  const date = prompt('Дата (YYYY-MM-DD):', new Date().toISOString().slice(0, 10));
  const notes = prompt('Примечание:', '');
  const order = await api.addMklOrder({ client_id: state.selectedClientId, date: date || new Date().toISOString().slice(0, 10), notes: notes || '' });
  state.mklSelectedOrderId = order.id;
  state.mklOrderItemsBuffer = [];
  refreshMKL();
});

mklExportBtn.addEventListener('click', async () => {
  const filter = mklFilter.value || '';
  const file = await api.exportMkl(filter || null);
  if (file) alert('Экспорт выполнен: ' + file);
});

// ---- Клиенты
function renderClients() {
  clientsListEl.innerHTML = '';
  state.clients.forEach(c => {
    const row = document.createElement('sl-card');
    row.className = 'list-item';
    const header = document.createElement('div');
    header.slot = 'header';
    header.textContent = `${c.name} • ${c.phone || '—'}`;
    row.appendChild(header);

    const actions = document.createElement('div');
    actions.className = 'row';
    const selectBtn = document.createElement('sl-button');
    selectBtn.size = 'small';
    selectBtn.variant = state.selectedClientId === c.id ? 'success' : 'neutral';
    selectBtn.textContent = state.selectedClientId === c.id ? 'Выбран' : 'Выбрать';
    selectBtn.addEventListener('click', () => {
      state.selectedClientId = c.id;
      renderClients();
    });

    const editBtn = document.createElement('sl-button');
    editBtn.size = 'small';
    editBtn.innerHTML = '<sl-icon name="pencil"></sl-icon>';
    editBtn.addEventListener('click', async () => {
      const name = prompt('ФИО:', c.name) || c.name;
      const phone = prompt('Телефон:', c.phone || '') || (c.phone || '');
      await api.updateClient({ id: c.id, name, phone });
      refreshMKL();
    });

    const delBtn = document.createElement('sl-button');
    delBtn.size = 'small';
    delBtn.variant = 'danger';
    delBtn.innerHTML = '<sl-icon name="trash"></sl-icon>';
    delBtn.addEventListener('click', async () => {
      if (confirm('Удалить клиента (его заказы МКЛ также будут удалены)?')) {
        await api.deleteClient(c.id);
        if (state.selectedClientId === c.id) state.selectedClientId = null;
        refreshMKL();
      }
    });

    actions.appendChild(selectBtn);
    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    row.appendChild(actions);
    clientsListEl.appendChild(row);
  });
}

clientAddBtn.addEventListener('click', async () => {
  const name = clientNameEl.value.trim();
  if (!name) return alert('Введите ФИО');
  const phone = clientPhoneEl.value.trim();
  await api.addClient({ name, phone });
  clientNameEl.value = '';
  clientPhoneEl.value = '';
  refreshMKL();
});

// ---- Товары
function renderProducts() {
  productsListEl.innerHTML = '';
  state.products.forEach(p => {
    const row = document.createElement('sl-card');
    row.className = 'list-item';
    const header = document.createElement('div');
    header.slot = 'header';
    header.textContent = `${p.name} • ${p.description || '—'} • ${p.price} ₽`;
    row.appendChild(header);

    const actions = document.createElement('div');
    actions.className = 'row';

    const editBtn = document.createElement('sl-button');
    editBtn.size = 'small';
    editBtn.innerHTML = '<sl-icon name="pencil"></sl-icon>';
    editBtn.addEventListener('click', async () => {
      const name = prompt('Наименование:', p.name) || p.name;
      const description = prompt('Описание:', p.description || '') || (p.description || '');
      const priceStr = prompt('Цена:', String(p.price)) || String(p.price);
      const price = Number(priceStr || p.price);
      await api.updateProduct({ id: p.id, name, description, price });
      refreshMKL();
    });

    const delBtn = document.createElement('sl-button');
    delBtn.size = 'small';
    delBtn.variant = 'danger';
    delBtn.innerHTML = '<sl-icon name="trash"></sl-icon>';
    delBtn.addEventListener('click', async () => {
      if (confirm('Удалить товар? Позиции в заказах МКЛ с этим товаром будут удалены.')) {
        await api.deleteProduct(p.id);
        refreshMKL();
      }
    });

    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    row.appendChild(actions);
    productsListEl.appendChild(row);
  });
}

productAddBtn.addEventListener('click', async () => {
  const name = productNameEl.value.trim();
  if (!name) return alert('Введите наименование');
  const description = productDescEl.value.trim();
  const price = Number(productPriceEl.value || 0);
  await api.addProduct({ name, description, price });
  productNameEl.value = '';
  productDescEl.value = '';
  productPriceEl.value = '';
  refreshMKL();
});

// ======================= MERIDIAN =======================

const meridianFilter = document.getElementById('meridianFilter');
const meridianOrdersList = document.getElementById('meridianOrdersList');
const meridianAddOrderBtn = document.getElementById('meridianAddOrderBtn');
const meridianExportBtn = document.getElementById('meridianExportBtn');
const meridianOrderItemsEl = document.getElementById('meridianOrderItems');
const meridianItemNameEl = document.getElementById('meridianItemName');
const meridianItemQtyEl = document.getElementById('meridianItemQty');
const meridianAddItemBtn = document.getElementById('meridianAddItemBtn');
const meridianSaveItemsBtn = document.getElementById('meridianSaveItemsBtn');

meridianFilter.addEventListener('sl-change', refreshMeridian);

async function refreshMeridian() {
  const filter = meridianFilter.value || '';
  state.meridianOrders = await api.getMeridianOrders(filter ? { status: filter } : {});
  renderMeridianOrders();
  renderMeridianItems();
}

function meridianStatusColor(status) {
  switch (status) {
    case 'не заказан': return 'danger';
    case 'заказан': return 'success';
    default: return 'neutral';
  }
}

function renderMeridianOrders() {
  meridianOrdersList.innerHTML = '';
  state.meridianOrders.forEach(o => {
    const card = document.createElement('sl-card');
    card.className = 'list-item order';
    const header = document.createElement('div');
    header.slot = 'header';
    header.innerHTML = `#${o.id} • ${o.date}`;
    card.appendChild(header);

    const badge = document.createElement('sl-badge');
    badge.variant = meridianStatusColor(o.status);
    badge.pill = true;
    badge.textContent = o.status;
    card.appendChild(badge);

    const actions = document.createElement('div');
    actions.className = 'row';
    const statusSelect = document.createElement('sl-select');
    statusSelect.size = 'small';
    statusSelect.value = o.status;
    ['не заказан', 'заказан'].forEach(s => {
      const opt = document.createElement('sl-option');
      opt.value = s;
      opt.textContent = s;
      statusSelect.appendChild(opt);
    });
    statusSelect.addEventListener('sl-change', async () => {
      await api.setMeridianStatus(o.id, statusSelect.value);
      refreshMeridian();
    });

    const selectBtn = document.createElement('sl-button');
    selectBtn.size = 'small';
    selectBtn.variant = 'primary';
    selectBtn.innerHTML = '<sl-icon name="cursor"></sl-icon> Выбрать';
    selectBtn.addEventListener('click', async () => {
      state.meridianSelectedOrderId = o.id;
      state.meridianItemsBuffer = await api.getMeridianOrderItems(o.id);
      renderMeridianItems();
    });

    const editBtn = document.createElement('sl-button');
    editBtn.size = 'small';
    editBtn.variant = 'neutral';
    editBtn.innerHTML = '<sl-icon name="pencil"></sl-icon> Редактировать';
    editBtn.addEventListener('click', async () => {
      const newDate = prompt('Дата (YYYY-MM-DD):', o.date);
      if (newDate) {
        await api.updateMeridianOrder({ id: o.id, status: o.status, date: newDate });
        refreshMeridian();
      }
    });

    const delBtn = document.createElement('sl-button');
    delBtn.size = 'small';
    delBtn.variant = 'danger';
    delBtn.innerHTML = '<sl-icon name="trash"></sl-icon> Удалить';
    delBtn.addEventListener('click', async () => {
      if (confirm('Удалить заказ?')) {
        await api.deleteMeridianOrder(o.id);
        if (state.meridianSelectedOrderId === o.id) {
          state.meridianSelectedOrderId = null;
          state.meridianItemsBuffer = [];
        }
        refreshMeridian();
      }
    });

    actions.appendChild(statusSelect);
    actions.appendChild(selectBtn);
    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    card.appendChild(actions);

    meridianOrdersList.appendChild(card);
  });
}

function renderMeridianItems() {
  meridianOrderItemsEl.innerHTML = '';
  if (!state.meridianSelectedOrderId) {
    meridianOrderItemsEl.innerHTML = '<small>Выберите заказ для редактирования позиций.</small>';
    return;
  }
  state.meridianItemsBuffer.forEach((it, idx) => {
    const row = document.createElement('div');
    row.className = 'list-item';
    row.innerHTML = `${it.product_name} • x${it.qty}`;
    const right = document.createElement('div');
    right.className = 'row';
    const qtyInput = document.createElement('sl-input');
    qtyInput.type = 'number';
    qtyInput.size = 'small';
    qtyInput.value = String(it.qty);
    qtyInput.style.width = '90px';
    qtyInput.addEventListener('sl-change', () => {
      state.meridianItemsBuffer[idx].qty = Number(qtyInput.value || 1);
    });
    const removeBtn = document.createElement('sl-button');
    removeBtn.size = 'small';
    removeBtn.variant = 'danger';
    removeBtn.innerHTML = '<sl-icon name="x"></sl-icon>';
    removeBtn.addEventListener('click', () => {
      state.meridianItemsBuffer.splice(idx, 1);
      renderMeridianItems();
    });
    right.appendChild(qtyInput);
    right.appendChild(removeBtn);
    row.appendChild(right);
    meridianOrderItemsEl.appendChild(row);
  });
}

meridianAddOrderBtn.addEventListener('click', async () => {
  const order = await api.addMeridianOrder();
  state.meridianSelectedOrderId = order.id;
  state.meridianItemsBuffer = [];
  refreshMeridian();
});

meridianAddItemBtn.addEventListener('click', () => {
  if (!state.meridianSelectedOrderId) return alert('Сначала выберите заказ.');
  const name = meridianItemNameEl.value.trim();
  const qty = Number(meridianItemQtyEl.value || 1);
  if (!name) return;
  state.meridianItemsBuffer.push({ product_name: name, qty });
  meridianItemNameEl.value = '';
  meridianItemQtyEl.value = '1';
  renderMeridianItems();
});

meridianSaveItemsBtn.addEventListener('click', async () => {
  if (!state.meridianSelectedOrderId) return;
  await api.setMeridianOrderItems(state.meridianSelectedOrderId, state.meridianItemsBuffer.map(i => ({ product_name: i.product_name, qty: i.qty })));
  alert('Позиции сохранены');
  refreshMeridian();
});

meridianExportBtn.addEventListener('click', async () => {
  const filter = meridianFilter.value || '';
  const file = await api.exportMeridian(filter || null);
  if (file) alert('Экспорт выполнен: ' + file);
});

// Старт на домашнем экране
goView('homeView');