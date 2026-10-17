---
type: Module
title: hosa/app
description: 'Graphe du projet géré : code (tree-sitter) + liens vers la KB, incrémental, requêtes compactes pour les agents.'
resource: hosa/app
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-17T13:02:15Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `hosa/app/graph.py` | Graphe du projet géré : code (tree-sitter) + liens vers la KB, incrémental, requêtes compactes pour les agents. |
| `hosa/app/graph_extract.py` | Extraction d'un fichier source (tree-sitter, sans LLM) : définitions, appels, imports, héritage. |
| `hosa/app/kb.py` | Lecture/écriture de la KB OKF (.hosa/kb/) — la KB de fichiers est la seule source de vérité. |
| `hosa/app/server.py` | App de pilotage Hosa — serveur HTTP local (stdlib) au-dessus de la KB OKF. |
| `hosa/app/test_app.py` |  |
| `hosa/app/test_avancement.py` | avancement.py: `check` finds a stage's missing proofs, `done` refuses them, `next` names the skill. |
| `hosa/app/test_graph.py` |  |
| `hosa/app/test_graph_extract.py` |  |
| `hosa/app/test_kb_index.py` | kb_index.py keeps the KB summary short: long descriptions are cut. |
| `hosa/app/test_plugin_frontmatter.py` | Every skill and agent of the plugin must have valid YAML frontmatter with a name and a description. |
| `hosa/app/test_run.py` | run.py: serves the managed project's KB (not a sprint worktree's stale copy), builds its venv once. |
| `hosa/app/test_usage_report.py` | usage_report.py: a response written over several transcript lines is counted once. |

## Symboles publics

- `GraphError` — `hosa/app/graph.py:30`
- `Index` — `hosa/app/graph.py:454` — Vue indexée d'un graphe pour les requêtes.
- `budgeted` — `hosa/app/graph.py:550`
- `build` — `hosa/app/graph.py:163` — Graphe complet dérivé des faits par fichier et de la KB. Pur : aucun accès disque.
- `build.edge` — `hosa/app/graph.py:167`
- `build.family` — `hosa/app/graph.py:194`
- `build.resolve` — `hosa/app/graph.py:205` — Même fichier -> fichiers importés -> tout le dépôt (même langage). Retourne (ids, conf).
- `checkout_root` — `hosa/app/graph.py:36` — Racine git du checkout qui contient `start` ; à défaut, le dossier qui porte `.hosa/`, sinon `start`.
- `fmt` — `hosa/app/graph.py:544`
- `graph_dir` — `hosa/app/graph.py:50`
- `kb_items` — `hosa/app/graph.py:254` — Tickets et exigences de la KB du checkout, avec leurs liens vers les exigences et les chemins cités.
- `main` — `hosa/app/graph.py:640`
- `node_id` — `hosa/app/graph.py:54` — Unique point de construction des identifiants : `chemin` ou `chemin::Qual.nom`.
- `refresh` — `hosa/app/graph.py:390` — Met le graphe à jour et le retourne. `paths` = fichiers à revérifier (défaut : tout le dépôt).
- `run` — `hosa/app/graph.py:609` — Exécute une commande de requête et retourne le texte à afficher.
- `status` — `hosa/app/graph.py:572` — État de l'index, sans le reconstruire : taille, fraîcheur, fichiers à réindexer ou exclus.
- `ticket_touches` — `hosa/app/graph.py:276` — {slug: [fichiers]} lus dans les commits portant le trailer `Hosa-Ticket: <slug>`.
- `tracked_files` — `hosa/app/graph.py:65` — Fichiers de code suivis ou non ignorés par git (respecte .gitignore), hors `SKIP_PREFIXES`.
- `write_code_map` — `hosa/app/graph.py:334` — Écrit kb/code/ (concepts Module + index.md). Ne réécrit que ce qui a changé ; déprécie les modules disparus.
- `extract` — `hosa/app/graph_extract.py:101` — Faits d'un fichier : {'lang', 'doc', 'defs': [...], 'calls': [...], 'imports': [...]}.
- `lang_of` — `hosa/app/graph_extract.py:22`
- `ConflictError` — `hosa/app/kb.py:43`
- `GitError` — `hosa/app/kb.py:39`
- `KbError` — `hosa/app/kb.py:35`
- `UsageError` — `hosa/app/kb.py:47`
- `UsageFailed` — `hosa/app/kb.py:51`
- `activity` — `hosa/app/kb.py:359` — Entrées des `log.md` : jour, dossier, texte, acteur (humain|processus|agent), et `lien` vers le
- `append_log` — `hosa/app/kb.py:221` — Entrée OKF §9 dans le log.md du bundle : groupée par date, plus récente en tête.
- `board` — `hosa/app/kb.py:478` — Tickets à plat, triés par priorité (sans priorité en dernier) puis titre.
- `coverage` — `hosa/app/kb.py:437` — Couverture des critères de chaque ticket, par chemin de concept.
- `coverage_of` — `hosa/app/kb.py:429` — Couverture des critères d'un ticket de `tickets/` (`av.coverage`).
- `create` — `hosa/app/kb.py:278`
- `dump_frontmatter` — `hosa/app/kb.py:88`
- `get` — `hosa/app/kb.py:175`
- `kb_status` — `hosa/app/kb.py:611` — État git de la KB (lecture seule) : dépôt ou non, fichiers de `git status --short`. Le dossier `code/`
- `load_frontmatter` — `hosa/app/kb.py:63` — Le frontmatter en dict, ou KbError avec une cause lisible : jamais le message de PyYAML, qui cite le contenu.
- `overview` — `hosa/app/kb.py:533`
- `parse` — `hosa/app/kb.py:76` — Retourne (frontmatter, body). Lève KbError « Le fichier est illisible : <cause> » si le YAML est invalide.
- `plan` — `hosa/app/kb.py:446` — Le plan d'avancement tenu par les skills (`project/avancement.md`), ou None s'il n'existe pas encore.
- `points` — `hosa/app/kb.py:470`
- `recettes` — `hosa/app/kb.py:500` — Concepts de `test/` hors `*-technique.md`, FAIL d'abord puis du plus récent au plus ancien.
- `render` — `hosa/app/kb.py:117`
- `resolve_kb_root` — `hosa/app/kb.py:55`
- `serialize` — `hosa/app/kb.py:92`
- `trust_tier` — `hosa/app/kb.py:121`
- `update` — `hosa/app/kb.py:237` — Met à jour un concept. merge=True fusionne le frontmatter (PATCH), sinon le remplace (édition complète).
- `usage` — `hosa/app/kb.py:405` — Consommation par agent et par modèle sur les `days` derniers jours, via `usage_report.scan`.
- `usage.rows` — `hosa/app/kb.py:421`
- `version` — `hosa/app/kb.py:204` — Empreinte du fichier sur disque : un PUT qui la renvoie n'écrase pas l'écriture d'un agent.
- `walk` — `hosa/app/kb.py:150` — Concepts de la KB. Un fichier illisible est sauté (la liste n'échoue jamais) et,
- `Server` — `hosa/app/server.py:181`
- `make_handler` — `hosa/app/server.py:27`
- `make_handler.Handler` — `hosa/app/server.py:30`
- `serve` — `hosa/app/server.py:186`
- `AppTest` — `hosa/app/test_app.py:35`
- `BacklogApiTest` — `hosa/app/test_app.py:907` — Tickets du backlog après le sprint 1 : un test par critère vérifiable côté serveur.
- `BoardTest` — `hosa/app/test_app.py:624` — GET /api/overview -> board et kb.points (ticket tickets-tableau-colonnes).
- `CouvertureTest` — `hosa/app/test_app.py:563` — GET /api/couverture et kb.coverage_of (ticket qualite-couverture-criteres-api).
- `GraphApiTest` — `hosa/app/test_app.py:204` — KB servie à l'intérieur d'un dépôt git : le graphe est celui de la racine du dépôt.
- `KbStatusTest` — `hosa/app/test_app.py:315`
- `RecettesTest` — `hosa/app/test_app.py:768` — `recettes` de GET /api/overview (ticket qualite-recettes-api). Cas navigateur : recette (T1-T4).
- `RecettesTest.test_read_only_and_relative_paths.snap` — `hosa/app/test_app.py:894`
- `UsageApiTest` — `hosa/app/test_app.py:437` — GET /api/usage : lit les transcripts factices via kb.ur.project_dir patché (jamais ~/.claude).
- `ValidationProvenanceTest` — `hosa/app/test_app.py:719` — Ticket validation-provenance-liste : couche serveur (le reste est en recette).
- `Check` — `hosa/app/test_avancement.py:34`
- `Coverage` — `hosa/app/test_avancement.py:72`
- `Done` — `hosa/app/test_avancement.py:137`
- `Next` — `hosa/app/test_avancement.py:146`
- `cov` — `hosa/app/test_avancement.py:63` — `av.coverage`, or a clean test failure while it does not exist yet.
- `kb` — `hosa/app/test_avancement.py:15`
- `run` — `hosa/app/test_avancement.py:23`
- `tk` — `hosa/app/test_avancement.py:69`
- `GraphTest` — `hosa/app/test_graph.py:38`
- `git` — `hosa/app/test_graph.py:34`
- `ExtractTest` — `hosa/app/test_graph_extract.py:17`
- `calls` — `hosa/app/test_graph_extract.py:13`
- `defs` — `hosa/app/test_graph_extract.py:9`
- `KbIndex` — `hosa/app/test_kb_index.py:13`
- `PluginFrontmatter` — `hosa/app/test_plugin_frontmatter.py:11`
- `KbRoot` — `hosa/app/test_run.py:13`
- `Setup` — `hosa/app/test_run.py:24`
- `SprintMeasures` — `hosa/app/test_usage_report.py:45`
- `UsageOnce` — `hosa/app/test_usage_report.py:19`
- `line` — `hosa/app/test_usage_report.py:14`

## Tickets et exigences

Aucun.
