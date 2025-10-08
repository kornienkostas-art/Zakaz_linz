const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

const db = require('./db'); // exposes methods

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 700,
    title: 'УссурОЧки.рф — Управление заказами',
    backgroundColor: '#121212',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });

  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  if (isDev) {
    win.webContents.openDevTools({ mode: 'detach' });
  }
}

// Ensure single instance
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    const win = BrowserWindow.getAllWindows()[0];
    if (win) {
      if (win.isMinimized()) win.restore();
      win.focus();
    }
  });

  app.whenReady().then(async () => {
    // Initialize DB (creates file and tables if needed)
    try {
      await db.ensureInitialized();
    } catch (e) {
      console.error('DB init failed', e);
      dialog.showErrorBox('Ошибка БД', 'Не удалось инициализировать базу данных.');
    }
    createWindow();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// IPC handlers
ipcMain.handle('db:getClients', (_, args) => db.getClients(args?.query));
ipcMain.handle('db:addClient', (_, client) => db.addClient(client));
ipcMain.handle('db:updateClient', (_, client) => db.updateClient(client));
ipcMain.handle('db:deleteClient', (_, id) => db.deleteClient(id));

ipcMain.handle('db:getProducts', () => db.getProducts());
ipcMain.handle('db:addProduct', (_, product) => db.addProduct(product));
ipcMain.handle('db:updateProduct', (_, product) => db.updateProduct(product));
ipcMain.handle('db:deleteProduct', (_, id) => db.deleteProduct(id));

ipcMain.handle('db:getMklOrders', (_, filter) => db.getMklOrders(filter));
ipcMain.handle('db:addMklOrder', (_, order) => db.addMklOrder(order));
ipcMain.handle('db:updateMklOrder', (_, order) => db.updateMklOrder(order));
ipcMain.handle('db:deleteMklOrder', (_, id) => db.deleteMklOrder(id));
ipcMain.handle('db:setMklStatus', (_, { id, status }) => db.setMklStatus(id, status));
ipcMain.handle('db:getMklOrderItems', (_, orderId) => db.getMklOrderItems(orderId));
ipcMain.handle('db:setMklOrderItems', (_, { orderId, items }) => db.setMklOrderItems(orderId, items));

ipcMain.handle('db:getMeridianOrders', (_, filter) => db.getMeridianOrders(filter));
ipcMain.handle('db:addMeridianOrder', () => db.addMeridianOrder());
ipcMain.handle('db:updateMeridianOrder', (_, order) => db.updateMeridianOrder(order));
ipcMain.handle('db:deleteMeridianOrder', (_, id) => db.deleteMeridianOrder(id));
ipcMain.handle('db:setMeridianStatus', (_, { id, status }) => db.setMeridianStatus(id, status));
ipcMain.handle('db:getMeridianOrderItems', (_, orderId) => db.getMeridianOrderItems(orderId));
ipcMain.handle('db:setMeridianOrderItems', (_, { orderId, items }) => db.setMeridianOrderItems(orderId, items));

ipcMain.handle('db:exportMkl', async (_, { status }) => {
  const filePath = await db.exportMkl(status);
  if (filePath) shell.showItemInFolder(filePath);
  return filePath;
});
ipcMain.handle('db:exportMeridian', async (_, { status }) => {
  const filePath = await db.exportMeridian(status);
  if (filePath) shell.showItemInFolder(filePath);
  return filePath;
});