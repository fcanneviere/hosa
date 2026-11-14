---
type: Module
title: hosa/app
description: 'Graphe du projet géré : code (tree-sitter) + liens vers la KB, incrémental, requêtes compactes pour les agents.'
resource: hosa/app
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-14T17:43:10Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `hosa/app/graph.py` | Graphe du projet géré : code (tree-sitter) + liens vers la KB, incrémental, requêtes compactes pour les agents. |
| `hosa/app/graph_extract.py` | Extraction d'un fichier source (tree-sitter, sans LLM) : définitions, appels, imports, héritage. |
| `hosa/app/kb.py` | Lecture/écriture de la KB OKF (.hosa/kb/) — la KB de fichiers est la seule source de vérité. |
| `hosa/app/server.py` | App de pilotage Hosa — serveur HTTP local (stdlib) au-dessus de la KB OKF. |
| `hosa/app/test_app.py` |  |
| `hosa/app/test_atelier.py` | atelier.py: style cards held to WCAG AA, an offline comparison page, the user's choice and the tokens in the KB. |
| `hosa/app/test_avancement.py` | avancement.py: `check` finds a stage's missing proofs, `done` refuses them, `next` names the skill. |
| `hosa/app/test_capture.py` | capture.py / capture.mjs: screenshots whose verdict a machine reads — rendering, accessibility, routes rendered. |
| `hosa/app/test_cdc.py` | cdc.py assembles the cahier des charges and finds every empty cell of its completeness matrices. |
| `hosa/app/test_docker_check.py` | docker_check.py: a sprint project is checked against its worktree, with that worktree's compose files only. |
| `hosa/app/test_graph.py` |  |
| `hosa/app/test_graph_extract.py` |  |
| `hosa/app/test_interface_check.py` | interface_check.py: every functional exigence has its screens — except a process with no screen. |
| `hosa/app/test_kb_index.py` | kb_index.py keeps the KB summary short: long descriptions are cut. |
| `hosa/app/test_kb_query.py` | kb_query.py reads the KB's frontmatter as YAML would: lists, quoted values, hidden folders, output cap. |
| `hosa/app/test_lexique_check.py` | lexique_check.py: a folder line keeps only its path; skipped folders and minified files are never scanned. |
| `hosa/app/test_okf_validate.py` | okf_validate.py: hidden folders are no concepts, a link out of the KB is checked on disk, old warnings are grouped. |
| `hosa/app/test_plugin_frontmatter.py` | Every skill and agent of the plugin must have valid YAML frontmatter with a name and a description. |
| `hosa/app/test_run.py` | run.py: serves the managed project's KB (not a sprint worktree's stale copy), builds its venv once. |
| `hosa/app/test_ticket_check.py` | ticket_check.py: a file cited as existing but created by another ticket needs a `depends_on` on it; |
| `hosa/app/test_usage_report.py` | usage_report.py: a response written over several transcript lines is counted once. |

## Symboles publics

- `GraphError` — `hosa/app/graph.py:30`
- `Index` — `hosa/app/graph.py:520` — Vue indexée d'un graphe pour les requêtes.
- `budgeted` — `hosa/app/graph.py:617`
- `build` — `hosa/app/graph.py:184` — Graphe complet dérivé des faits par fichier et de la KB. Pur : aucun accès disque.
- `build.edge` — `hosa/app/graph.py:188`
- `build.family` — `hosa/app/graph.py:219`
- `build.resolve` — `hosa/app/graph.py:230` — Même fichier -> fichiers importés -> tout le dépôt (même langage). Retourne (ids, conf).
- `checkout_root` — `hosa/app/graph.py:36` — Racine git du checkout qui contient `start` ; à défaut, le dossier qui porte `.hosa/`, sinon `start`.
- `fmt` — `hosa/app/graph.py:611`
- `graph_dir` — `hosa/app/graph.py:50`
- `kb_checkout` — `hosa/app/graph.py:283` — Checkout dont la KB fait foi. Un worktree de sprint (`.worktrees/…`) n'a pas de KB, ou une copie périmée :
- `kb_items` — `hosa/app/graph.py:291` — Tickets et exigences de la KB du projet, avec leurs liens vers les exigences et les chemins cités.
- `main` — `hosa/app/graph.py:708`
- `node_id` — `hosa/app/graph.py:54` — Unique point de construction des identifiants : `chemin` ou `chemin::Qual.nom`.
- `refresh` — `hosa/app/graph.py:453` — Met le graphe à jour et le retourne. `paths` = fichiers à revérifier (défaut : tout le dépôt).
- `run` — `hosa/app/graph.py:677` — Exécute une commande de requête et retourne le texte à afficher.
- `status` — `hosa/app/graph.py:639` — État de l'index, sans le reconstruire : taille, fraîcheur, fichiers à réindexer ou exclus.
- `ticket_touches` — `hosa/app/graph.py:316` — {slug: [fichiers]} lus dans les commits portant le trailer `Hosa-Ticket: <slug>`.
- `ticket_touches.current` — `hosa/app/graph.py:339`
- `tracked_files` — `hosa/app/graph.py:65` — Fichiers suivis ou non ignorés par git (respecte .gitignore), hors `SKIP_PREFIXES`. Les fichiers hors code
- `write_code_map` — `hosa/app/graph.py:397` — Écrit kb/code/ (concepts Module + index.md). Ne réécrit que ce qui a changé ; déprécie les modules disparus.
- `extract` — `hosa/app/graph_extract.py:109` — Faits d'un fichier : {'lang', 'doc', 'defs': [...], 'calls': [...], 'imports': [...]}.
- `lang_of` — `hosa/app/graph_extract.py:23`
- `ConflictError` — `hosa/app/kb.py:46`
- `GitError` — `hosa/app/kb.py:42`
- `KbError` — `hosa/app/kb.py:38`
- `UsageError` — `hosa/app/kb.py:50`
- `UsageFailed` — `hosa/app/kb.py:54`
- `activity` — `hosa/app/kb.py:381` — Entrées des `log.md` : jour, dossier, texte, acteur (humain\|processus\|agent), et `lien` vers le
- `append_log` — `hosa/app/kb.py:225` — Entrée OKF §9 dans le log.md du bundle : groupée par date, plus récente en tête.
- `board` — `hosa/app/kb.py:511` — Tickets à plat, triés par priorité (sans priorité en dernier) puis titre.
- `coverage` — `hosa/app/kb.py:468` — Couverture des critères de chaque ticket, par chemin de concept.
- `coverage_of` — `hosa/app/kb.py:460` — Couverture des critères d'un ticket de `tickets/` (`av.coverage`).
- `create` — `hosa/app/kb.py:282`
- `dump_frontmatter` — `hosa/app/kb.py:91`
- `get` — `hosa/app/kb.py:179`
- `kb_status` — `hosa/app/kb.py:632` — État git de la KB (lecture seule) : dépôt ou non, fichiers de `git status --short`. Le dossier `code/`
- `load_frontmatter` — `hosa/app/kb.py:66` — Le frontmatter en dict, ou KbError avec une cause lisible : jamais le message de PyYAML, qui cite le contenu.
- `overview` — `hosa/app/kb.py:566`
- `parse` — `hosa/app/kb.py:79` — Retourne (frontmatter, body). Lève KbError « Le fichier est illisible : <cause> » si le YAML est invalide.
- `plan` — `hosa/app/kb.py:477` — Le plan d'avancement tenu par les skills (`project/avancement.md`), ou None s'il n'existe pas encore.
- `points` — `hosa/app/kb.py:503`
- `recettes` — `hosa/app/kb.py:533` — Concepts de `test/` hors `*-technique.md`, FAIL d'abord puis du plus récent au plus ancien.
- `remark` — `hosa/app/kb.py:306` — Remarque de l'utilisateur pour Claude : un fichier de `kb/remarques/`, signé `human:<auteur>`.
- `remarques` — `hosa/app/kb.py:345` — Les remarques de l'utilisateur : ouvertes d'abord, puis de la plus récente à la plus ancienne.
- `render` — `hosa/app/kb.py:120`
- `resolve_kb_root` — `hosa/app/kb.py:58`
- `serialize` — `hosa/app/kb.py:95`
- `trust_tier` — `hosa/app/kb.py:124`
- `update` — `hosa/app/kb.py:241` — Met à jour un concept. merge=True fusionne le frontmatter (PATCH), sinon le remplace (édition complète).
- `usage` — `hosa/app/kb.py:427` — Consommation par agent et par modèle sur les `days` derniers jours, via `usage_report.scan`.
- `usage.rows` — `hosa/app/kb.py:450`
- `version` — `hosa/app/kb.py:208` — Empreinte du fichier sur disque : un PUT qui la renvoie n'écrase pas l'écriture d'un agent.
- `walk` — `hosa/app/kb.py:153` — Concepts de la KB. Un fichier illisible est sauté (la liste n'échoue jamais) et,
- `Server` — `hosa/app/server.py:185`
- `listen` — `hosa/app/server.py:197` — A port asked for (PORT) is that port or an OSError. None asked: 3000, or a free port when 3000 is taken —
- `make_handler` — `hosa/app/server.py:27`
- `make_handler.Handler` — `hosa/app/server.py:30`
- `serve` — `hosa/app/server.py:190`
- `AppTest` — `hosa/app/test_app.py:35`
- `BacklogApiTest` — `hosa/app/test_app.py:965` — Tickets du backlog après le sprint 1 : un test par critère vérifiable côté serveur.
- `BoardTest` — `hosa/app/test_app.py:682` — GET /api/overview -> board et kb.points (ticket tickets-tableau-colonnes).
- `CouvertureTest` — `hosa/app/test_app.py:621` — GET /api/couverture et kb.coverage_of (ticket qualite-couverture-criteres-api).
- `GraphApiTest` — `hosa/app/test_app.py:255` — KB servie à l'intérieur d'un dépôt git : le graphe est celui de la racine du dépôt.
- `KbStatusTest` — `hosa/app/test_app.py:366`
- `RecettesTest` — `hosa/app/test_app.py:826` — `recettes` de GET /api/overview (ticket qualite-recettes-api). Cas navigateur : recette (T1-T4).
- `RecettesTest.test_read_only_and_relative_paths.snap` — `hosa/app/test_app.py:952`
- `UsageApiTest` — `hosa/app/test_app.py:488` — GET /api/usage : lit les transcripts factices via kb.ur.project_dir patché (jamais ~/.claude).
- `ValidationProvenanceTest` — `hosa/app/test_app.py:777` — Ticket validation-provenance-liste : couche serveur (le reste est en recette).
- `Base` — `hosa/app/test_atelier.py:23`
- `Cartes` — `hosa/app/test_atelier.py:69`
- `Choix` — `hosa/app/test_atelier.py:337`
- `Cli` — `hosa/app/test_atelier.py:679`
- `Comparer` — `hosa/app/test_atelier.py:169`
- `Contraste` — `hosa/app/test_atelier.py:53`
- `Diversite` — `hosa/app/test_atelier.py:539`
- `Revue` — `hosa/app/test_atelier.py:584`
- `AuditStage` — `hosa/app/test_avancement.py:771`
- `Block` — `hosa/app/test_avancement.py:238`
- `Bounds` — `hosa/app/test_avancement.py:1237` — The audit of 2026-11-12: each bound and each state below was open, and is now a refusal with its test.
- `Bounds.test_one_writer_of_the_plan_at_a_time.second` — `hosa/app/test_avancement.py:1339`
- `Check` — `hosa/app/test_avancement.py:38`
- `Coverage` — `hosa/app/test_avancement.py:164`
- `Docs` — `hosa/app/test_avancement.py:1207` — The pipelines written in prose (using-hosa, README) follow pipeline.json.
- `Done` — `hosa/app/test_avancement.py:229`
- `Graph` — `hosa/app/test_avancement.py:1023` — pipeline.json is the one stage graph: each stage once, each stage's skill exists, loops go backwards.
- `Init` — `hosa/app/test_avancement.py:1190`
- `Loops` — `hosa/app/test_avancement.py:1073`
- `LoopsClosed` — `hosa/app/test_avancement.py:1401` — The audit's five points left open, 2026-11-12: each one is now a refusal.
- `LoopsClosed.test_the_review_closes_on_a_note_of_8_computed_from_its_grid_or_its_two_exits.done` — `hosa/app/test_avancement.py:1486`
- `LoopsClosed.test_the_review_closes_on_a_note_of_8_computed_from_its_grid_or_its_two_exits.grid` — `hosa/app/test_avancement.py:1477`
- `Next` — `hosa/app/test_avancement.py:794`
- `Reponse` — `hosa/app/test_avancement.py:248` — `reponse`: the user's answers leave a blocked stage, and the journal says whether they took the recommendation.
- `Reprendre` — `hosa/app/test_avancement.py:812` — `reprendre`: the resume card, in one call — the stage, its skill, the sprint, the tasks, the action.
- `Tasks` — `hosa/app/test_avancement.py:339` — `task`: the agents' dispatches of an open stage — a proof of exit like the files its skill writes.
- `batch` — `hosa/app/test_avancement.py:1055` — A backlog batch `n` whose stories, security and legal notes are done on `tickets`, its judge's task added.
- `closed_until` — `hosa/app/test_avancement.py:1064` — Every upstream stage done up to <stage> included (forced: these tests are about the loops).
- `cov` — `hosa/app/test_avancement.py:155` — `av.coverage`, or a clean test failure while it does not exist yet.
- `kb` — `hosa/app/test_avancement.py:19`
- `run` — `hosa/app/test_avancement.py:27`
- `section_rows` — `hosa/app/test_avancement.py:1639`
- `tk` — `hosa/app/test_avancement.py:161`
- `Navigateur` — `hosa/app/test_capture.py:80`
- `Routes` — `hosa/app/test_capture.py:43`
- `chrome` — `hosa/app/test_capture.py:32`
- `Assemble` — `hosa/app/test_cdc.py:291`
- `Completeness` — `hosa/app/test_cdc.py:114`
- `Review` — `hosa/app/test_cdc.py:247`
- `holes` — `hosa/app/test_cdc.py:110`
- `kb` — `hosa/app/test_cdc.py:98`
- `review` — `hosa/app/test_cdc.py:242`
- `DockerCheck` — `hosa/app/test_docker_check.py:20`
- `container` — `hosa/app/test_docker_check.py:15`
- `GraphTest` — `hosa/app/test_graph.py:38`
- `git` — `hosa/app/test_graph.py:34`
- `ExtractTest` — `hosa/app/test_graph_extract.py:17`
- `calls` — `hosa/app/test_graph_extract.py:13`
- `defs` — `hosa/app/test_graph_extract.py:9`
- `BackOfficeAndDashboards` — `hosa/app/test_interface_check.py:76`
- `Screens` — `hosa/app/test_interface_check.py:38`
- `exigence` — `hosa/app/test_interface_check.py:23`
- `kb_gaps` — `hosa/app/test_interface_check.py:64`
- `screen_gaps` — `hosa/app/test_interface_check.py:27`
- `KbIndex` — `hosa/app/test_kb_index.py:13`
- `KbQuery` — `hosa/app/test_kb_query.py:22`
- `run` — `hosa/app/test_kb_query.py:15`
- `LexiqueCheck` — `hosa/app/test_lexique_check.py:23`
- `OkfValidate` — `hosa/app/test_okf_validate.py:13`
- `PluginFrontmatter` — `hosa/app/test_plugin_frontmatter.py:11`
- `KbRoot` — `hosa/app/test_run.py:16`
- `Setup` — `hosa/app/test_run.py:27`
- `PhantomPaths` — `hosa/app/test_ticket_check.py:20`
- `SecurityAndLegalNotes` — `hosa/app/test_ticket_check.py:60`
- `ticket` — `hosa/app/test_ticket_check.py:16`
- `SprintMeasures` — `hosa/app/test_usage_report.py:67`
- `UsageOnce` — `hosa/app/test_usage_report.py:19`
- `line` — `hosa/app/test_usage_report.py:14`

## Tickets et exigences

Aucun.
