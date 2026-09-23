const express = require('express');
const { listConcepts, getConcept, listTicketsByState } = require('./okf');

function createRouter(kbRoot) {
  const router = express.Router();

  router.get('/concepts', (req, res) => {
    res.json(listConcepts(kbRoot, req.query.type));
  });

  router.get('/tickets', (req, res) => {
    res.json(listTicketsByState(kbRoot));
  });

  router.get('/concepts/*', (req, res) => {
    const relPath = req.params[0];
    const concept = getConcept(kbRoot, relPath);
    if (!concept) {
      res.status(404).json({ error: 'not found' });
      return;
    }
    res.json(concept);
  });

  return router;
}

module.exports = { createRouter };
