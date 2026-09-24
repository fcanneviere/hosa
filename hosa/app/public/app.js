const state = { view: 'tickets', allConcepts: [] };

const TRUST_LABELS = {
  'human-reviewed': 'vérifié (humain)',
  'machine-confirmed': 'vérifié (machine)',
  unverified: 'non vérifié',
};

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${url}`);
  return res.json();
}

function renderTickets(grouped) {
  for (const columnState of ['todo', 'doing', 'done', 'blocked']) {
    const column = document.querySelector(`.column[data-state="${columnState}"] .cards`);
    column.replaceChildren();
    for (const ticket of grouped[columnState] || []) {
      const card = document.createElement('div');
      card.className = 'card';
      card.textContent = ticket.frontmatter.title || ticket.path;
      column.appendChild(card);
    }
  }
}

function matchesFilters(concept, { type, tag, query }) {
  if (type && concept.frontmatter.type !== type) return false;
  if (tag && !(concept.frontmatter.tags || []).includes(tag)) return false;
  if (query) {
    const haystack = `${concept.frontmatter.title || ''} ${concept.frontmatter.description || ''}`.toLowerCase();
    if (!haystack.includes(query.toLowerCase())) return false;
  }
  return true;
}

function renderConceptList(concepts) {
  const list = document.getElementById('concept-list');
  list.replaceChildren();
  for (const concept of concepts) {
    const item = document.createElement('li');
    const title = document.createElement('span');
    title.className = 'concept-title';
    title.textContent = concept.frontmatter.title || concept.path;
    const type = document.createElement('span');
    type.className = 'badge badge-type';
    type.textContent = concept.frontmatter.type;
    const description = document.createElement('span');
    description.className = 'concept-description';
    description.textContent = concept.frontmatter.description || '';
    item.append(type, title, description);
    item.addEventListener('click', () => showConceptDetail(concept.path));
    list.appendChild(item);
  }
}

function infoboxRow(table, label, value) {
  if (!value) return;
  const row = table.insertRow();
  const th = document.createElement('th');
  th.textContent = label;
  row.appendChild(th);
  const td = document.createElement('td');
  td.textContent = value;
  row.appendChild(td);
}

function renderConceptDetail(concept) {
  const panel = document.getElementById('concept-detail');
  panel.hidden = false;
  panel.replaceChildren();

  const title = document.createElement('h3');
  title.textContent = concept.frontmatter.title || concept.path;
  panel.appendChild(title);

  const infobox = document.createElement('table');
  infobox.className = 'infobox';
  infoboxRow(infobox, 'Type', concept.frontmatter.type);
  infoboxRow(infobox, 'Statut', concept.frontmatter.status || 'stable');
  infoboxRow(infobox, 'Confiance', TRUST_LABELS[concept.trustTier] || concept.trustTier);
  if (concept.frontmatter.tags && concept.frontmatter.tags.length) {
    infoboxRow(infobox, 'Tags', concept.frontmatter.tags.join(', '));
  }
  if (concept.frontmatter.generated) {
    infoboxRow(infobox, 'Généré par', `${concept.frontmatter.generated.by} (${concept.frontmatter.generated.at || '?'})`);
  }
  if (concept.frontmatter.verified) {
    infoboxRow(infobox, 'Vérifié par', `${concept.frontmatter.verified.by} (${concept.frontmatter.verified.at || '?'})`);
  }
  const trustBadge = document.createElement('span');
  trustBadge.className = `badge badge-trust badge-trust-${concept.trustTier}`;
  trustBadge.textContent = TRUST_LABELS[concept.trustTier] || concept.trustTier;
  panel.append(infobox, trustBadge);

  const body = document.createElement('div');
  body.className = 'concept-body';
  body.innerHTML = concept.bodyHtml; // sanitized server-side (sanitize-html) before it reaches the client
  panel.appendChild(body);
}

async function showConceptDetail(path) {
  try {
    const concept = await fetchJson(`/api/concepts/${path}`);
    renderConceptDetail(concept);
    showError('');
  } catch (err) {
    showError(`Erreur de chargement : ${err.message}`);
  }
}

function renderKbView() {
  const type = document.getElementById('type-filter').value;
  const tag = document.getElementById('tag-filter').value;
  const query = document.getElementById('search-box').value;
  const filtered = state.allConcepts.filter((c) => matchesFilters(c, { type, tag, query }));
  renderConceptList(filtered);
}

async function loadTickets() {
  const grouped = await fetchJson('/api/tickets');
  renderTickets(grouped);
}

async function loadKb() {
  state.allConcepts = await fetchJson('/api/concepts');
  return state.allConcepts;
}

function populateSelectOptions(selectId, values) {
  const select = document.getElementById(selectId);
  const current = select.value;
  select.replaceChildren();
  const defaultOption = document.createElement('option');
  defaultOption.value = '';
  defaultOption.textContent = 'Tous';
  select.appendChild(defaultOption);
  for (const value of values) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
  if (values.includes(current)) select.value = current;
}

function populateTypeFilter(concepts) {
  const types = [...new Set(concepts.map((c) => c.frontmatter.type))].sort();
  populateSelectOptions('type-filter', types);
}

function populateTagFilter(concepts) {
  const tags = [...new Set(concepts.flatMap((c) => c.frontmatter.tags || []))].sort();
  populateSelectOptions('tag-filter', tags);
}

function switchView(view) {
  state.view = view;
  document.getElementById('view-tickets').hidden = view !== 'tickets';
  document.getElementById('view-kb').hidden = view !== 'kb';
  for (const button of document.querySelectorAll('nav button')) {
    button.classList.toggle('active', button.dataset.view === view);
  }
}

function showError(message) {
  const banner = document.getElementById('error-banner');
  banner.textContent = message;
  banner.hidden = !message;
}

async function refresh() {
  try {
    if (state.view === 'tickets') {
      await loadTickets();
    } else {
      const concepts = await loadKb();
      populateTypeFilter(concepts);
      populateTagFilter(concepts);
      renderKbView();
    }
    showError('');
  } catch (err) {
    showError(`Erreur de chargement : ${err.message}`);
  }
}

document.querySelectorAll('nav button').forEach((button) => {
  button.addEventListener('click', () => {
    switchView(button.dataset.view);
    refresh();
  });
});

document.getElementById('type-filter').addEventListener('change', renderKbView);
document.getElementById('tag-filter').addEventListener('change', renderKbView);
document.getElementById('search-box').addEventListener('input', renderKbView);
document.getElementById('refresh').addEventListener('click', refresh);

(async function init() {
  try {
    const concepts = await loadKb();
    populateTypeFilter(concepts);
    populateTagFilter(concepts);
    renderKbView();
    await loadTickets();
  } catch (err) {
    showError(`Erreur de chargement : ${err.message}`);
  }
})();
