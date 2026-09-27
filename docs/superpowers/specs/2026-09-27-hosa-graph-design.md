# Hosa — graphe du projet géré (`hosa-graph`) — design

Date : 2026-09-27

## Objectif

Réduire la consommation de tokens des agents Hosa (`hosa-tech-lead`, `hosa-developer`, `hosa-debugger`, `hosa-senior-dev`, `hosa-reviewer`, skill `changement`) en leur donnant un graphe **du projet géré**, tenu à jour automatiquement, qui répond directement à « quel fichier / quelle fonction toucher, et qu'est-ce que ça impacte » — au lieu de Grep/Glob/Read exploratoires. Le graphe relie le code (fichiers, symboles, imports, appels) aux concepts de la KB (exigences du CDC, tickets). Il est consultable dans une section dédiée de l'app web.

**Critère de succès :** un agent qui reçoit un ticket localise les fichiers et symboles à modifier par une requête au graphe, sans balayage du code.

## Contexte et sources

Analyse préalable de trois références :

- **graphify** (Graphify-Labs, v0.9.53, lu dans le code source et exécuté sur `hosa/app`). À reprendre : extraction de code 100 % déterministe par tree-sitter, identifiants stables dérivés du chemin, incrémental par hash de fichier, trois primitives de requête (`explain`, `affected`, `query` bornée), hook `PreToolUse` qui oriente l'agent vers le graphe. À écarter : liens doc↔code produits uniquement par LLM (IDs qui dérivent, doublons fantômes), communautés/god nodes/surprising connections, exports multiples, « benchmark » de tokens synthétique. Point faible majeur : fraîcheur (aucune vérification au moment de la requête).
- **OKF 0.2** (spec GoogleCloudPlatform/open-knowledge-format). Les relations OKF sont des liens markdown **non typés** (§6.1) ; la spec vise la connaissance curée et se dégrade au-delà de ~1 000–5 000 concepts. Conséquence : graphe machine en JSON + couche OKF résumée (un concept par module).
- **okf-skills** (scaccogatto, MIT). `okf_validate.py` (un fichier, PyYAML seul) valide la KB actuelle sans erreur ; réutilisé tel quel.

Avantage propre à Hosa : les liens métier sont **déterministes** — `develop` fait un commit par ticket, et chaque ticket porte déjà `Lié à : [exigence](../cdc/xxx.md)`. D'où la chaîne exigence → ticket → fichiers → symboles sans aucune inférence LLM.

## Décisions

| # | Question | Décision |
|---|---|---|
| 1 | Moteur d'extraction | Indexeur propre (~300 lignes) sur `tree-sitter-language-pack` + requêtes `tags.scm` embarquées — pas de dépendance à graphify |
| 2 | Fraîcheur | Hook plugin `PostToolUse` (Edit/Write) + rattrapage `SessionStart` + **vérification mtime au moment de chaque requête**. Pas de hook git |
| 3 | Adoption par les agents | Consignes dans les agents + hook `PreToolUse` Grep/Glob, **un seul rappel par session**, fail-open, jamais bloquant |
| 4 | Interface | Explorateur centré sur un élément + mini-schéma SVG du voisinage + vue traçabilité. Pas de carte globale |
| 5 | Couche OKF | Concepts `kb/code/` générés de façon déterministe (un `Module` par dossier) + `kb/code/index.md` comme carte du dépôt. Pas de résumé LLM |

## 1. Stockage et format

Emplacement : `<checkout>/.hosa/graph/graph.json` et `<checkout>/.hosa/graph/manifest.json`, **ignorés par git** (dérivés, régénérables). `<checkout>` est la racine git du dépôt indexé (`git rev-parse --show-toplevel`) : le worktree d'un sprint a son propre graphe, la branche de base le sien.

`graph.json` :

```json
{
  "version": 1,
  "root": "C:/dev/projet",
  "built_at": "2026-09-27T10:00:00Z",
  "nodes": [
    {"id": "src/kb.py", "kind": "file", "label": "kb.py", "file": "src/kb.py", "lang": "python", "doc": "Lecture/écriture de la KB OKF"},
    {"id": "src/kb.py::update", "kind": "function", "label": "update", "file": "src/kb.py", "line": 143, "end": 167, "lang": "python", "doc": "Met à jour un concept."},
    {"id": "ticket:export-csv", "kind": "ticket", "label": "Export CSV des factures", "file": ".hosa/kb/tickets/export-csv.md", "state": "doing"},
    {"id": "exigence:facturation", "kind": "exigence", "label": "Facturation", "file": ".hosa/kb/cdc/facturation.md", "status": "stable"}
  ],
  "edges": [
    {"src": "src/kb.py", "dst": "src/kb.py::update", "rel": "contains", "conf": "exact"},
    {"src": "src/kb.py::update", "dst": "src/kb.py::_safe_target", "rel": "calls", "conf": "exact", "line": 146},
    {"src": "ticket:export-csv", "dst": "src/kb.py", "rel": "touches", "conf": "exact"},
    {"src": "ticket:export-csv", "dst": "exigence:facturation", "rel": "implements", "conf": "exact"}
  ]
}
```

- **`kind`** : `file`, `class`, `function`, `method`, `ticket`, `exigence`.
- **`id`** : `<chemin relatif posix>` pour un fichier, `<chemin>::<Symbole>` pour un symbole de premier niveau, `<chemin>::<Classe>.<méthode>` pour une méthode, `ticket:<slug>`, `exigence:<slug>`. Lisibles et tapables par un agent. Un seul point de construction (`node_id()`).
- **`rel`** : `contains`, `imports`, `calls`, `inherits` (code) ; `touches` (ticket → fichier), `implements` (ticket → exigence), `mentions` (concept KB → fichier cité).
- **`conf`** : `exact` si la cible est unique ; `ambiguous` si plusieurs définitions portent le nom référencé (une arête par candidat). Jamais de devinette silencieuse.

`manifest.json` : `{ "<chemin relatif>": {"mtime": <float>, "sha256": "<hex>"} }`.

## 2. Extraction — `hosa/app/graph.py`

### Code

- **Parsing** : `tree-sitter-language-pack` (ajouté à `hosa/app/requirements.txt`). Détection du langage par extension.
- **Requêtes** : `hosa/app/queries/<lang>-tags.scm` (définitions `@definition.*` / références `@reference.*`, format des tags tree-sitter) et une capture `@import` par langage. Langages initiaux : Python, JavaScript, TypeScript, PHP, Go, Java, C#, Ruby. Ajouter un langage = déposer son `.scm`.
- **Fichiers parcourus** : fichiers suivis par git (`git ls-files`) — respecte `.gitignore` sans code dédié. `.hosa/` exclu du parsing de code. Fichier d'un langage sans requête : nœud `file` seul.
- **Résolution** d'une référence `nom` dans le fichier F, dans l'ordre : définition du même nom dans F → dans les fichiers que F importe → dans tout le dépôt. Un seul candidat : `exact`. Plusieurs au dernier niveau : une arête `ambiguous` par candidat. Aucun : pas d'arête (appel vers une bibliothèque externe).
- **Imports** : chemin d'import résolu vers un fichier du dépôt quand il correspond (relatif ou module → chemin) ; sinon ignoré.
- **`doc`** : première ligne non vide de la docstring / du commentaire qui précède la définition, tronquée à 120 caractères.

### Liens KB (déterministes)

- **ticket → fichiers (`touches`)** : `git log --format=%H%x00%(trailers:key=Hosa-Ticket,valueonly)` puis fichiers de chaque commit portant le trailer. Seuls les fichiers encore présents dans le graphe sont liés. Modification requise du skill `develop` (Step 6) : ajouter `-m "Hosa-Ticket: <slug-ticket>"` au commit.
- **ticket → exigence (`implements`)** : liens markdown vers `../cdc/*.md` (ou `/cdc/*.md`) dans le corps des concepts `type: Ticket`.
- **concept → fichier (`mentions`)** : chemins entre backticks, dans n'importe quel concept de la KB, qui correspondent à un fichier indexé.
- La KB lue est celle résolue par `kb.resolve_kb_root(<checkout>)`, réutilise `kb.walk()`.

### Incrémental

- `index` sans argument : compare `manifest` (mtime puis sha256 si mtime diffère) aux fichiers suivis ; ne reparse que les fichiers modifiés/nouveaux ; supprime les nœuds des fichiers disparus.
- Réindexer un fichier F : retirer tous les nœuds dont `file == F` et toutes les arêtes dont `src` est un de ces nœuds ; reparser F ; puis re-résoudre les références **de F** et les références des autres fichiers qui pointaient vers des symboles de F (arêtes orphelines supprimées, nouvelles cibles résolues).
- Liens KB recalculés à chaque `index` (peu coûteux : `git log` + `walk`).
- Écriture atomique de `graph.json` (fichier temporaire + `os.replace`) ; verrou fichier `.hosa/graph/lock` pour que le hook et une requête concurrente ne s'écrasent pas.

### Couche OKF — `kb/code/`

- Un concept par dossier contenant au moins un fichier indexé : `kb/code/<chemin-du-dossier-avec-tirets>.md`, `type: Module`, `title` = chemin du dossier, `description` = `doc` du fichier principal (`__init__.py`, `index.*`, `mod.rs`…) ou du premier fichier, `resource` = chemin, `generated: {by: process:hosa-graph, at}`.
- Corps : table des fichiers (une ligne : fichier — doc), symboles publics (non préfixés `_`) avec `fichier:ligne`, liens vers les tickets et exigences liés (liens markdown OKF §6.1).
- `kb/code/index.md` (OKF §8) : une ligne par module `* [dossier](dossier.md) - description` — la carte du dépôt en une page.
- Un concept n'est réécrit que si son contenu (hors `generated.at`) change ; chaque écriture ajoute une entrée au `kb/code/log.md` (OKF §9, via `kb.append_log`). Module disparu : `status: deprecated` + entrée de log (règle OKF : déprécier plutôt que supprimer).

## 3. Interface agents — CLI

`<python du venv> <plugin>/hosa/app/graph.py <cmd> [--root <checkout>]` (défaut : racine git du répertoire courant).

| Commande | Sortie |
|---|---|
| `map` | Contenu de `kb/code/index.md` |
| `find <texte> [--limit 20]` | Nœuds dont id/label/doc correspondent (score : correspondance exacte du label > préfixe > sous-chaîne ; tokens pondérés) |
| `explain <id\|nom>` | Le nœud, puis ses arêtes entrantes et sortantes groupées par `rel` |
| `affected <id\|nom> [--depth 2]` | Parcours inverse sur `calls`/`imports`/`inherits`/`contains`, + tickets qui touchent les fichiers atteints |
| `ticket <slug>` | Exigences, fichiers et symboles liés au ticket |
| `index [fichier…]` | Réindexation (incrémentale ou ciblée) |

- Format de sortie : une ligne par élément, `kind  label  fichier:ligne  [conf]`, sans JSON — le moins de tokens possible. Plafond `--budget` (défaut 2 000 tokens, estimés à 4 caractères/token) ; au-delà, la sortie est tronquée avec une ligne `… N éléments de plus (affiner la requête)`.
- Un `<nom>` qui correspond à plusieurs nœuds : liste des candidats avec leur `id`, sans choisir.
- **Fraîcheur à la requête** : avant de répondre, `stat()` des fichiers des nœuds retournés ; tout fichier dont le mtime diffère du manifeste est réindexé, puis la requête est rejouée. Aucun graphe → construction complète avant la première réponse.
- Horodatage de la dernière requête : `.hosa/graph/last_query` (utilisé par le hook de rappel).
- Le hook `SessionStart` injecte dans le contexte la ligne de commande exacte (interpréteur du venv + chemin absolu de `graph.py`) pour que les agents n'aient pas à la reconstruire.

## 4. Hooks du plugin (`hooks/hooks.json`)

Scripts Node (comme les hooks existants) qui appellent le Python du venv de `hosa/app`. Tous fail-open : toute erreur → `exit 0` sans sortie.

- **`PostToolUse` `Edit|Write|MultiEdit`** — `hooks/graph-update.js` : lit `tool_input.file_path` ; si un `.hosa/graph/` existe dans un ancêtre, lance `graph.py index <fichier>` (synchrone, timeout 10 s).
- **`SessionStart`** — ajout à `hooks/session-start.js` : si le cwd appartient à un projet ayant `.hosa/kb/`, lance `graph.py index` **détaché** (la première construction complète peut dépasser le timeout de 5 s) et ajoute la ligne de commande du graphe au contexte injecté.
- **`PreToolUse` `Grep|Glob`** — `hooks/graph-nudge.js` : si `.hosa/graph/graph.json` existe et que `last_query` est absent ou antérieur au début de session (fichier-marqueur `.hosa/graph/session` écrit par `SessionStart`), émet une seule fois `additionalContext` : « Le graphe du projet est disponible : `graph.py explain|affected|ticket|find` avant de grepper. » puis écrit un marqueur pour ne plus le répéter dans la session. Jamais de refus.

## 5. Interface web — vue « Graphe »

Serveur (`server.py`), lecture seule, via les fonctions de `graph.py` (fraîcheur appliquée comme pour la CLI) :

- `GET /api/graph/find?q=` — liste de nœuds.
- `GET /api/graph/node?id=` — nœud + arêtes entrantes/sortantes + `affected` à profondeur 2.
- `GET /api/graph/trace` — pour chaque exigence : tickets (`implements` inverse) puis fichiers/symboles (`touches`).

Le graphe est lu depuis la racine git parente de la KB servie.

Client (`public/app.js`, `style.css`) — nouvelle entrée de navigation `graph` :

- **Recherche** en tête de vue (fichier, fonction, ticket, exigence).
- **Fiche** d'un nœud : emplacement `fichier:ligne`, `doc`, appelants, appelés, imports, tickets/exigences liés, impact ; chaque élément cliquable (navigue vers sa fiche ; tickets/exigences → leur page `#/kb/...`).
- **Mini-schéma SVG** du voisinage (1–2 niveaux, disposition radiale calculée côté client, sans bibliothèque), couleur par `kind`, arêtes `ambiguous` en pointillé.
- **Vue traçabilité** (`#/graph/trace`) : exigence → tickets → fichiers ; exigences `stable` sans aucun fichier lié mises en évidence.
- Pas de graphe (`graph.json` absent) : message indiquant comment le construire (`graph.py index`).

## 6. Skill `okf` et intégration

- **`skills/okf/SKILL.md`** : règles d'écriture et de maintenance OKF 0.2 (frontmatter, `type` requis, noms réservés `index.md`/`log.md`, `generated`/`verified` et tiers de confiance, `status` ∈ draft|stable|deprecated, liens §6.1, index §8, log §9, déprécier plutôt que supprimer, ne jamais marquer `verified: human:` sans revue humaine) et étape finale obligatoire : lancer le validateur, corriger toute erreur.
- **`skills/okf/scripts/okf_validate.py`** : copie d'okf-skills avec en-tête de licence MIT et provenance (URL + commit).
- **`using-hosa`** : nouvelle Core Rule — toute écriture dans la KB suit `okf` et se termine par le validateur ; ligne `okf` ajoutée à la table des skills ; mention du graphe (commande injectée à la session).
- **Agents** — `tech-lead`, `developer`, `debugger`, `senior-dev`, `reviewer` : étape d'orientation « `graph.py ticket <slug>` / `explain` / `affected` d'abord ; Read ciblé ensuite ; Grep seulement si le graphe ne répond pas ». `changement` : `affected` pour l'analyse d'impact.
- **`develop`** Step 6 : trailer `Hosa-Ticket: <slug>` dans le commit.
- **`.gitignore`** du projet géré : `graph.py index` y ajoute `.hosa/graph/` si la ligne est absente (une seule fois, avec une entrée de log dans `kb/code/log.md`).

## 7. Tests — `hosa/app/test_graph.py`

Fixture : mini-projet temporaire (dépôt git initialisé) avec deux fichiers Python et un fichier JS qui s'importent et s'appellent, deux fonctions homonymes dans deux fichiers, une KB avec une exigence et un ticket lié, un commit portant `Hosa-Ticket:`.

Vérifie :

1. Nœuds `file`/`function`/`class`/`method` avec lignes correctes.
2. Arêtes `contains`, `imports`, `calls` (`exact`), `inherits`.
3. Appel vers un nom défini deux fois → deux arêtes `ambiguous`.
4. `touches` (via trailer) et `implements` (via lien markdown), `mentions`.
5. Incrémental : modifier un fichier → ses anciens nœuds disparaissent, les nouveaux apparaissent, les arêtes entrantes vers un symbole supprimé disparaissent ; fichier supprimé → ses nœuds disparaissent.
6. Fraîcheur : modifier un fichier sans `index` → `explain` renvoie l'état nouveau.
7. `kb/code/` : concepts `Module` valides (passent `okf_validate.py`), non réécrits si rien n'a changé.
8. API : `/api/graph/find`, `/api/graph/node`, `/api/graph/trace` (dans `test_app.py`, style existant).

## Hors périmètre

- Communautés, god nodes, surprising connections, exports (HTML/Obsidian/Neo4j) — inutiles pour « quel fichier toucher ».
- Liens inférés par LLM (doc↔code, résumés de modules) — fragiles ; les liens déterministes couvrent le besoin.
- Hook git post-commit — la vérification à la requête couvre le cas.
- Carte globale force-directed — illisible au-delà de quelques centaines de nœuds.
- Serveur MCP — la CLI suffit ; à ajouter si un client non-Claude-Code doit interroger le graphe.
