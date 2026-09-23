const state = { view: 'tickets' };

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

function renderConceptList(concepts) {
  const list = document.getElementById('concept-list');
  list.replaceChildren();
  for (const concept of concepts) {
    const item = document.createElement('li');
    const title = concept.frontmatter.title || concept.path;
    const description = concept.frontmatter.description || '';
    item.textContent = `[${concept.frontmatter.type}] ${title} — ${description}`;
    list.appendChild(item);
  }
}

async function loadTickets() {
  const grouped = await fetchJson('/api/tickets');
  renderTickets(grouped);
}

async function loadKb(type) {
  const url = type ? `/api/concepts?type=${encodeURIComponent(type)}` : '/api/concepts';
  const concepts = await fetchJson(url);
  renderConceptList(concepts);
  return concepts;
}

function populateTypeFilter(concepts) {
  const select = document.getElementById('type-filter');
  const types = [...new Set(concepts.map((c) => c.frontmatter.type))].sort();
  for (const type of types) {
    const option = document.createElement('option');
    option.value = type;
    option.textContent = type;
    select.appendChild(option);
  }
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
      const typeFilter = document.getElementById('type-filter').value;
      await loadKb(typeFilter);
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

document.getElementById('type-filter').addEventListener('change', refresh);
document.getElementById('refresh').addEventListener('click', refresh);

(async function init() {
  try {
    const allConcepts = await loadKb();
    populateTypeFilter(allConcepts);
    await loadTickets();
  } catch (err) {
    showError(`Erreur de chargement : ${err.message}`);
  }
})();
