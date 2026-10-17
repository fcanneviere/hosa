# Architecture du tableau de bord Hosa

## Vue d'ensemble
Application locale en deux couches, sans base de données : la KB (fichiers Markdown avec frontmatter YAML, dans `.hosa/kb/`) est la seule source de vérité.

```
navigateur ── HTTP JSON ──► hosa/app/server.py ──► kb.py ──► .hosa/kb/*.md
   public/index.html            (routes /api/*)       │
   public/app.js                                       ├──► skills/status/scripts/avancement.py (règles de la méthode)
   public/style.css                                    └──► graph.py ──► .hosa/graph/graph.json
```

## Modules
- `hosa/app/server.py` — serveur HTTP (stdlib), garde-fous : hôte local seulement (rebinding DNS), écritures en `application/json` seulement (CSRF), chemins confinés à la KB. Sert `public/` (page unique, routage côté client par le hash).
- `hosa/app/kb.py` — lecture, écriture et journalisation des concepts ; `overview()` agrège le tableau de bord ; `plan()` lit le plan d'avancement via `avancement.py`.
- `hosa/app/graph.py`, `graph_extract.py` — graphe du code (tree-sitter) et liens vers la KB.
- `skills/status/scripts/avancement.py` — règles de la méthode (étapes, preuves). Dépendance en lecture seule : l'app l'importe, ne la modifie pas. Exception : `coverage` y est ajoutée, l'app et `check` partagent la même règle.
- `hosa/app/public/` — interface : `index.html` (coquille), `app.js` (vues, état, appels API), `style.css`.

## API
- `GET /api/overview` — projet, plan d'avancement, sections estimées, compteurs de tickets et d'exigences, sprints, dernier audit, activité récente, `recettes` (`path, ticket, titre, persona, at, verdict`).
- `GET /api/activity` — entrées des `log.md`.
- `GET /api/couverture` — couverture des critères de chaque ticket (`criteres`, `couverts`, `total`, `plan`), calculée par `avancement.py coverage`.
- `GET /api/concepts[?type=]`, `GET /api/concepts/<chemin>` — concepts.
- `POST /api/concepts` — création ; `PATCH` (fusion du frontmatter) et `PUT` (remplacement) sur `/api/concepts/<chemin>`.
- `POST /api/render` — rendu Markdown assaini.
- `GET /api/graph/find?q=`, `/api/graph/node?id=`, `/api/graph/trace` — graphe.

## Règles
- Toute règle de la méthode vient d'`avancement.py` ; l'app n'en recalcule aucune.
- Toute écriture passe par `kb.update`/`kb.create` et ajoute une ligne de log.
- Nouvelle donnée affichée → nouvelle clé d'API côté serveur, jamais une lecture de fichier côté navigateur.
- Interface : pas de framework, pas de build, pas de ressource réseau.
