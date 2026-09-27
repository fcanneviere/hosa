const express = require('express');
const { listConcepts, getConcept, listTicketsByState, updateConcept, TICKET_STATES } = require('./okf');

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

  router.patch('/concepts/*', express.json(), (req, res) => {
    const relPath = req.params[0];
    const patch = req.body && req.body.frontmatter;
    if (!patch || typeof patch !== 'object' || Array.isArray(patch)) {
      res.status(400).json({ error: 'body must be { frontmatter: {...} }' });
      return;
    }
    if ('state' in patch && !TICKET_STATES.has(patch.state)) {
      res.status(400).json({ error: `state must be one of: ${[...TICKET_STATES].join(', ')}` });
      return;
    }
    const concept = updateConcept(kbRoot, relPath, patch);
    if (!concept) {
      res.status(404).json({ error: 'not found' });
      return;
    }
    res.json(concept);
  });

  return router;
}

module.exports = { createRouter };
