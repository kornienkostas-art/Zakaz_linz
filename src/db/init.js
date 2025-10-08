const db = require('./index');

(async () => {
  try {
    await db.ensureInitialized();
    console.log('Database initialized.');
    process.exit(0);
  } catch (e) {
    console.error('Failed to initialize database', e);
    process.exit(1);
  }
})();