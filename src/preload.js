const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // Clients
  getClients: (query) => ipcRenderer.invoke('db:getClients', { query }),
  addClient: (client) => ipcRenderer.invoke('db:addClient', client),
  updateClient: (client) => ipcRenderer.invoke('db:updateClient', client),
  deleteClient: (id) => ipcRenderer.invoke('db:deleteClient', id),

  // Products
  getProducts: () => ipcRenderer.invoke('db:getProducts'),
  addProduct: (product) => ipcRenderer.invoke('db:addProduct', product),
  updateProduct: (product) => ipcRenderer.invoke('db:updateProduct', product),
  deleteProduct: (id) => ipcRenderer.invoke('db:deleteProduct', id),

  // MKL Orders
  getMklOrders: (filter) => ipcRenderer.invoke('db:getMklOrders', filter),
  addMklOrder: (order) => ipcRenderer.invoke('db:addMklOrder', order),
  updateMklOrder: (order) => ipcRenderer.invoke('db:updateMklOrder', order),
  deleteMklOrder: (id) => ipcRenderer.invoke('db:deleteMklOrder', id),
  setMklStatus: (id, status) => ipcRenderer.invoke('db:setMklStatus', { id, status }),
  getMklOrderItems: (orderId) => ipcRenderer.invoke('db:getMklOrderItems', orderId),
  setMklOrderItems: (orderId, items) => ipcRenderer.invoke('db:setMklOrderItems', { orderId, items }),

  // Meridian Orders
  getMeridianOrders: (filter) => ipcRenderer.invoke('db:getMeridianOrders', filter),
  addMeridianOrder: () => ipcRenderer.invoke('db:addMeridianOrder'),
  updateMeridianOrder: (order) => ipcRenderer.invoke('db:updateMeridianOrder', order),
  deleteMeridianOrder: (id) => ipcRenderer.invoke('db:deleteMeridianOrder', id),
  setMeridianStatus: (id, status) => ipcRenderer.invoke('db:setMeridianStatus', { id, status }),
  getMeridianOrderItems: (orderId) => ipcRenderer.invoke('db:getMeridianOrderItems', orderId),
  setMeridianOrderItems: (orderId, items) => ipcRenderer.invoke('db:setMeridianOrderItems', { orderId, items }),

  // Export
  exportMkl: (status) => ipcRenderer.invoke('db:exportMkl', { status }),
  exportMeridian: (status) => ipcRenderer.invoke('db:exportMeridian', { status })
});