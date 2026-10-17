---
type: Module
title: hosa/app
description: 'Graphe du projet géré : code (tree-sitter) + liens vers la KB, incrémental, requêtes compactes pour les agents.'
resource: hosa/app
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-17T07:14:44Z'}
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

- `GraphError` — `hosa/app/graph.py:28`
- `Index` — `hosa/app/graph.py:452` — Vue indexée d'un graphe pour les requêtes.
- `budgeted` — `hosa/app/graph.py:548`
- `build` — `hosa/app/graph.py:161` — Graphe complet dérivé des faits par fichier et de la KB. Pur : aucun accès disque.
- `build.edge` — `hosa/app/graph.py:165`
- `build.family` — `hosa/app/graph.py:192`
- `build.resolve` — `hosa/app/graph.py:203` — Même fichier -> fichiers importés -> tout le dépôt (même langage). Retourne (ids, conf).
- `checkout_root` — `hosa/app/graph.py:34` — Racine git du checkout qui contient `start` ; à défaut, le dossier qui porte `.hosa/`, sinon `start`.
- `fmt` — `hosa/app/graph.py:542`
- `graph_dir` — `hosa/app/graph.py:48`
- `kb_items` — `hosa/app/graph.py:252` — Tickets et exigences de la KB du checkout, avec leurs liens vers les exigences et les chemins cités.
- `main` — `hosa/app/graph.py:638`
- `node_id` — `hosa/app/graph.py:52` — Unique point de construction des identifiants : `chemin` ou `chemin::Qual.nom`.
- `refresh` — `hosa/app/graph.py:388` — Met le graphe à jour et le retourne. `paths` = fichiers à revérifier (défaut : tout le dépôt).
- `run` — `hosa/app/graph.py:607` — Exécute une commande de requête et retourne le texte à afficher.
- `status` — `hosa/app/graph.py:570` — État de l'index, sans le reconstruire : taille, fraîcheur, fichiers à réindexer ou exclus.
- `ticket_touches` — `hosa/app/graph.py:274` — {slug: [fichiers]} lus dans les commits portant le trailer `Hosa-Ticket: <slug>`.
- `tracked_files` — `hosa/app/graph.py:63` — Fichiers de code suivis ou non ignorés par git (respecte .gitignore), hors `SKIP_PREFIXES`.
- `write_code_map` — `hosa/app/graph.py:332` — Écrit kb/code/ (concepts Module + index.md). Ne réécrit que ce qui a changé ; déprécie les modules disparus.
- `extract` — `hosa/app/graph_extract.py:101` — Faits d'un fichier : {'lang', 'doc', 'defs': [...], 'calls': [...], 'imports': [...]}.
- `lang_of` — `hosa/app/graph_extract.py:22`
- `KbError` — `hosa/app/kb.py:30`
- `activity` — `hosa/app/kb.py:246`
- `append_log` — `hosa/app/kb.py:128` — Entrée OKF §9 dans le log.md du bundle : groupée par date, plus récente en tête.
- `create` — `hosa/app/kb.py:171`
- `dump_frontmatter` — `hosa/app/kb.py:57`
- `get` — `hosa/app/kb.py:109`
- `overview` — `hosa/app/kb.py:296`
- `parse` — `hosa/app/kb.py:42` — Retourne (frontmatter, body). Lève KbError si le YAML est invalide.
- `plan` — `hosa/app/kb.py:272` — Le plan d'avancement tenu par les skills (`project/avancement.md`), ou None s'il n'existe pas encore.
- `render` — `hosa/app/kb.py:65`
- `resolve_kb_root` — `hosa/app/kb.py:34`
- `serialize` — `hosa/app/kb.py:61`
- `trust_tier` — `hosa/app/kb.py:69`
- `update` — `hosa/app/kb.py:144` — Met à jour un concept. merge=True fusionne le frontmatter (PATCH), sinon le remplace (édition complète).
- `walk` — `hosa/app/kb.py:91`
- `make_handler` — `hosa/app/server.py:17`
- `make_handler.Handler` — `hosa/app/server.py:20`
- `serve` — `hosa/app/server.py:153`
- `AppTest` — `hosa/app/test_app.py:32`
- `GraphApiTest` — `hosa/app/test_app.py:137` — KB servie à l'intérieur d'un dépôt git : le graphe est celui de la racine du dépôt.
- `Check` — `hosa/app/test_avancement.py:34`
- `Done` — `hosa/app/test_avancement.py:56`
- `Next` — `hosa/app/test_avancement.py:65`
- `kb` — `hosa/app/test_avancement.py:15`
- `run` — `hosa/app/test_avancement.py:23`
- `GraphTest` — `hosa/app/test_graph.py:38`
- `git` — `hosa/app/test_graph.py:34`
- `ExtractTest` — `hosa/app/test_graph_extract.py:17`
- `calls` — `hosa/app/test_graph_extract.py:13`
- `defs` — `hosa/app/test_graph_extract.py:9`
- `KbIndex` — `hosa/app/test_kb_index.py:13`
- `PluginFrontmatter` — `hosa/app/test_plugin_frontmatter.py:11`
- `KbRoot` — `hosa/app/test_run.py:13`
- `Setup` — `hosa/app/test_run.py:24`
- `UsageOnce` — `hosa/app/test_usage_report.py:19`
- `line` — `hosa/app/test_usage_report.py:14`

## Tickets et exigences

Aucun.
