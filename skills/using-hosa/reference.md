# Hosa — reference

Read on demand (not loaded at session start): the full list of skills and the phrases that trigger them. Every skill's own description carries the same triggers.

## Skills

Use the `Skill` tool to invoke any of these. The skill loads its full instructions — follow them exactly.

| Skill | What it does |
|---|---|
| `understand` | Brainstorm + grill an idea → write spec → quiz user → commit |
| `build` | Read spec or description → plan → implement task by task → quiz → commit |
| `iterate` | Change or extend existing code → light grill → targeted plan → quiz → commit |
| `dispatch` | Fan out independent tasks to agents in parallel |
| `test` | Run tests, identify gaps, write new tests, commit them |
| `review` | Check implementation against spec → fix gaps → loop until clean |
| `debug` | Systematic root cause analysis → confirm with user → fix → commit |
| `status` | Snapshot of project state — spec, progress, tests, next step |
| `hosa` | Initialize/update the Hosa project's identity and personas in the KB (`.hosa/kb/`) |
| `recette` | Business/functional acceptance testing of a feature or ticket, from a specific persona's point of view |
| `interview` | Gather cahier des charges input from processes, personas, and the user — CDC pipeline stage 1 |
| `redaction` | Turn interview notes into structured `Exigence` concepts in `kb/cdc/` — CDC pipeline stage 2 |
| `relecture` | Check the cahier des charges for precision, completeness, and consistency — CDC pipeline stage 5 |
| `contestation` | Final independent challenge pass on the cahier des charges — CDC pipeline stage 6; won't sign off until `fondamentaux` and `securite` have run |
| `fondamentaux` | Make sure the cahier des charges contains every basic software function personas never ask for (administration, user management, rights, audit/error logs, change history, backup, import/export, settings, notifications) and the core NFRs — `hosa-product-owner` includes every missing one by default, the user strikes out what doesn't apply — CDC pipeline stage 3, mandatory |
| `securite` | Security in three moments, by `hosa-security`: analysis of the cahier des charges (security exigences, constraints, `Security Rule`s — CDC pipeline stage 4, mandatory), threat model right after `architecture` (STRIDE, abuse cases — data-structuring stage 7), Go/No-Go gate inside `livraison`; also a code audit (OWASP, LLM, supply chain, secrets, RGPD) on request |
| `stack` | Propose and record the technical stack of the managed project, based on the stable cahier des charges — data-structuring pipeline stage 1 |
| `infra` | Set up the managed project's Docker environment, install the chosen stack and the quality tooling (test runner, browser tests, linter, formatter, type checker, CI) for real, and document it; also relays agents' installation requests — data-structuring pipeline stage 2 |
| `donnees` | Annotate the origin (générée/fournie/saisie) of data in the cahier des charges — data-structuring pipeline stage 3 |
| `schema-app` | Derive data entities and write application-side data structures + documentation into the managed project — data-structuring pipeline stage 4 |
| `schema-db` | Write database migrations/DDL into the managed project (`hosa-data-engineer`), then `hosa-dba` applies them, proves they reverse and documents the database tooling — data-structuring pipeline stage 5 |
| `architecture` | Design and scaffold the software architecture of the managed project, consistent with the CDC, the stack, and the data structures — data-structuring pipeline stage 6; chains `securite` (Menaces) |
| `interface` | Complete, working interface: screen inventory and navigation per role covering every stable Exigence, UX fundamentals applied, navigable scaffold verified on screenshots and reviewed independently — Interview each persona, choose style, layout and pages on comparison pages (method and tools from oil-ui), then design and scaffold the interface layer (UX/UI) of the managed project, consistent with the CDC and the software architecture — data-structuring pipeline stage 8 |
| `backlog` | Turn every stable Exigence into Product Backlog tickets — split into deliverable slices with `depends_on`, each carrying story, acceptance criteria from the business rules and error cases, technical, architecture, interface and security notes; `nfr` exigences become the definition of done; proposes the foundation commit — data-structuring pipeline stage 9. Its Single-Ticket Mode completes any ticket created elsewhere |
| `sprint` | Compose a sprint from the Product Backlog — dispatch tickets in priority order up to a given capacity, guarding against dispatching one whose technical feasibility, architecture placement, or interface placement was never actually evaluated — follow-on to the data-structuring pipeline |
| `qa-plan` | Add the tests to a sprint before it starts — one `Test Plan` per ticket in `kb/test/` (`hosa-qa-lead`), grounded in the senior dev's recorded stack decisions, with the personas who must validate it, plus the test dataset and its reset command (`hosa-data-engineer`); chained by `sprint`, required by `git` Mode 1 |
| `qa` | Run a sprint's QA — `hosa-tester` runs each ticket's tests on its own (finds its inputs, fixes the test side, records results, cleans up), `hosa-key-user` runs each required recette, failures routed to the right owner |
| `git` | Open a dedicated branch/worktree for a sprint when it starts, or merge it locally back into the managed project once every ticket has a passing QA record — dispatches `hosa-git`. Companion transversal skill, with dedicated hand-off points in `sprint` (start) and `validation` (finish) |
| `develop` | Implement a single sprint ticket — tests first (`hosa-tester`), short sequential tasks (`hosa-tech-lead`, `hosa-developer`), full suite and lint, code review (`hosa-reviewer`), one commit; correction mode fixes a defect found by QA, the demo or the review inside the sprint |
| `validation` | Close a ticket's cycle — `hosa-product-owner` checks it against its acceptance criteria, technical results (security and NFR cases included) and recettes; once the whole sprint is accepted, runs the user demo (`hosa-qa-lead` Mode 3) required before the merge |
| `bilan-sprint` | Sprint Review and retro once a sprint merges — dispatches `hosa-product-owner` to judge whether the objective was met, list delivered/deferred tickets, surface recurring friction, and write follow-up tickets or process Design Rules. Follow-on to `git` Mode 2 |
| `bdd` | Any database operation — migrations (apply, roll back, conflicts), an environment's database, the test database and its reset, backup/restore, a slow query — dispatches `hosa-dba`; also the relay for `## Base de données nécessaire` |
| `retours` | The report standard every agent and every reply follows — answer first, ASD-STE100 sentences adapted to French, questions numbered Q1, Q2… with lettered options — reference, not a pipeline step |
| `qualite` | Audit the managed project's source code — `hosa-senior-dev` for best practices and performance, `hosa-security` for security (conformity to the rules set at design time, plus the unforeseen holes) — classifies findings by severity, routes blocking ones |
| `documentation` | Check whether the managed project's technical and functional documentation is in sync with its sources, and refresh whatever has drifted — dispatches `hosa-documentation` in cold-check mode. Companion check usable anytime, not a pipeline stage |
| `changement` | Handle a change to a `stable` Exigence — impact analysis (tickets/entities/migrations/screens/docs affected), revert to `draft`, a mini relecture/contestation loop, then follow-up tickets. Companion to the CDC pipeline, usable anytime after `contestation` has run once |
| `livraison` | Release the managed project — quality audit (`qualite`) as a gate, release notes and user documentation (`hosa-documentation`), tested tag (`hosa-git`), optional deployment with a database backup first (`hosa-dba`, `hosa-infra`), optional push/PR |
| `kb-commit` | Commit whatever's accumulated under `.hosa/kb/` as a dedicated commit in the managed project's own git history, separate from the rest of that project's commits and from Hosa's own tooling commits. Companion skill, usable anytime |
| `okf` | Rules every file under `.hosa/kb/` must follow (Open Knowledge Format 0.2) and the validator run that closes every KB write. Companion skill, applied by every skill or agent that writes the KB |

## Triggering Rules

**Auto-trigger** the matching skill immediately via the `Skill` tool — without asking for permission — when the user's message clearly matches a skill's purpose:

| User says something like... | Trigger |
|---|---|
| "I have an idea for...", "I want to build...", "Let's plan..." | `understand` |
| "Implement this", "Build it", "Add this feature", "Write the code" | `build` |
| "Change how X works", "Refactor this", "Update this", "Add X to existing Y" | `iterate` |
| "Run these in parallel", "Fan out", "Do these simultaneously" | `dispatch` |
| "Test this", "Run tests", "Check if it works" | `test` |
| "Does this match the spec?", "Check requirements", "Is everything implemented?" | `review` |
| "It's broken", "This isn't working", "I'm getting an error", "There's a bug" | `debug` |
| "Where are we?", "What's done?", "Catch me up", "What's left?" | `status` |
| "Initialise le projet", "Configure hosa", "Crée un persona pour..." | `hosa` |
| "Fais une recette de...", "Valide ça avec [persona]", "Est-ce que ça répond au besoin de..." | `recette` |
| "Rédige le cahier des charges", "Interview les personas", "Démarre le cahier des charges" | `interview` |
| "Rédige les exigences", "Écris le cahier des charges" (avec notes fournies) | `redaction` |
| "Relis le cahier des charges" | `relecture` |
| "Challenge le cahier des charges" | `contestation` |
| "Vérifie les fondamentaux du cahier des charges", "Le cahier des charges couvre-t-il les basiques (admin, utilisateurs, logs, sauvegarde, import/export...)" | `fondamentaux` |
| "Analyse la sécurité du cahier des charges", "Quelles contraintes de sécurité ?", "Sécurité dès la conception" | `securite` |
| "Applique les migrations", "Conflit de migrations", "Réinitialise la base de test", "Sauvegarde/restaure la base", "La requête est lente" | `bdd` |
| "Choisis la stack technique", "Quelle stack pour le projet" | `stack` |
| "Mets en place l'environnement Docker", "Installe la stack" | `infra` |
| "Précise les données du cahier des charges", "Qualifie l'origine des données" | `donnees` |
| "Génère la structure de données de l'application" | `schema-app` |
| "Génère la structure de base de données" | `schema-db` |
| "Crée l'architecture logicielle", "Génère l'architecture de l'application" | `architecture` |
| "Conçois l'interface", "Crée l'identité visuelle", "Définis l'UX/UI du projet" | `interface` |
| "Crée le product backlog", "Génère les tickets à partir du cahier des charges" | `backlog` |
| "Complète le ticket X", "Ce ticket n'est pas prêt" | `backlog` (Single-Ticket Mode) |
| "Planifie un sprint", "Compose le prochain sprint" | `sprint` |
| "Prépare les tests du sprint", "Planifie les tests techniques du sprint" | `qa-plan` |
| "Exécute la QA du sprint", "Teste le sprint", "Fais la recette du sprint" | `qa` |
| "Démarre le sprint X", "Commence le sprint X" | `git` (Mode 1) |
| "Termine le sprint X", "Fusionne le sprint X", "Merge le sprint X" | `git` (Mode 2) |
| "Développe le ticket X", "Implémente le ticket X" | `develop` |
| "Valide le ticket X", "Accepte le ticket X" | `validation` |
| "Fais le bilan du sprint X", "Rétro du sprint X" | `bilan-sprint` |
| "Audite la qualité du code", "Vérifie les bonnes pratiques" | `qualite` |
| "Fais une revue de sécurité", "Audite la sécurité du code", "Modèle de menaces", "Est-ce que c'est sécurisé ?" | `securite` |
| "Vérifie que la documentation est à jour" | `documentation` |
| "Cette exigence a changé", "Modifie le cahier des charges sur X (déjà stable)" | `changement` |
| "Livre le projet", "Déploie", "Prépare la release" | `livraison` |
| "Committe la KB", "Sauvegarde les changements de la KB" | `kb-commit` |
