const path = require('path');
const express = require('express');
const { createRouter } = require('./src/routes');

function createApp(kbRoot) {
  const app = express();
  app.use('/api', createRouter(kbRoot));
  app.use(express.static(path.join(__dirname, 'public')));
  return app;
}

function startServer(kbRoot, port) {
  return createApp(kbRoot).listen(port, '127.0.0.1');
}

if (require.main === module) {
  const kbRoot = process.env.HOSA_KB_ROOT || path.join(__dirname, '..', 'kb');
  const port = process.env.PORT || 3000;
  startServer(kbRoot, port).on('listening', () => {
    console.log(`hosa app listening on http://localhost:${port}`);
  });
}

module.exports = { createApp, startServer };
