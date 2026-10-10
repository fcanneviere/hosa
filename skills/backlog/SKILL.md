---
name: backlog
description: "Use to turn every stable Exigence into Product Backlog tickets — vertical slices with `depends_on`, story and acceptance criteria (PO), and grounded technical, architecture, interface and security notes citing real paths; `nfr` exigences become the definition of done; also refines vague `todo` tickets. Structuration stage 9. Triggers: \"crée le product backlog\", after `interface`."
---

# Backlog

Turns "what the application must do" (the stable cahier des charges) into Product Backlog tickets — each one carrying the business story, its technical feasibility, where it lands in the architecture, and where it lands in the interface, so nothing enters `kb/tickets/` disconnected from the technical reality already decided by `stack`, `architecture`, and `interface`.

## Flow

```
Exigences non fonctionnelles [nfr] → définition de terminé
(kb/rules/design/definition-de-termine.md), vérifiée sur chaque ticket
        ↓
Pour chaque autre Exigence stable de kb/cdc/ sans Ticket lié :
découpe en tickets livrables (une tranche utilisable chacun),
dépendances notées (depends_on)
        ↓
Écrit la story et les critères d'acceptation Given/When/
Then (rôle PO) dans un nouveau Ticket, state: todo
        ↓
Ajoute une note technique (rôle senior dev), ou une ligne
"pas encore évalué" si aucune Stack Decision n'existe
        ↓
Ajoute un placement architecture (rôle architecte), ou une
ligne "pas encore déterminé" si aucune doc d'architecture
n'existe
        ↓
Ajoute un placement interface (rôle UX/UI designer), ou une
ligne "pas encore déterminé" si aucune doc d'interface n'existe
        ↓
Ajoute une note sécurité (rôle expert cybersécurité), ou une
ligne "pas encore faite" si aucune analyse de sécurité n'existe
        ↓
Log kb/tickets/log.md
        ↓
Checkpoint hosa-git : socle encore non commité, puis KB
        ↓
Propose de lancer sprint
```

## Trigger

Manual: `/backlog`. Auto: immediately after `interface`, or "crée le product backlog", "génère les tickets à partir du cahier des charges".

Single-ticket mode: `/backlog <slug-ticket>`, or chained by any skill that just created a `Ticket` — see **Single-Ticket Mode** below. A ticket is born complete: no skill reports a new ticket before this mode has run on it.

## Ticket complet

A ticket is ready to be planned (`sprint`) and executed (`develop`, `qa-plan`) when it has all of:
- a story (`En tant que … je veux … afin de …`) and a `Lié à :` line — to its `Exigence`, or, for a ticket born outside the cahier des charges (bug, recette gap, audit finding, change impact, sprint follow-up), to the concept that surfaced it;
- `## Critères d'acceptation` with at least one Given/When/Then scenario;
- real `## Note technique (senior dev)`, `## Placement architecture (architecte)`, `## Placement interface (UX/UI)` and `## Note sécurité (expert cybersécurité)` notes — not the fallback lines below;
- a `priority`, unless the user explicitly answered "pas encore";
- a `depends_on` (when present) naming existing tickets, with no cycle.

The checker is the source of truth — run it from the managed project's root, with any Python 3.9+:

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/backlog/scripts/ticket_check.py" .hosa/kb [.hosa/kb/tickets/<slug>.md ...]
```

No ticket given → every `state: todo` ticket. Exit `0` = all complete, `1` = gaps listed per ticket.

---

## Step 1: Scope

List every `stable` `Exigence` (`kb_query.py .hosa/kb --type Exigence --where status=stable`), except those tagged `nfr` (Step 1b). For each one, `kb_query.py .hosa/kb --type Ticket --grep "cdc/<slug>.md"` lists the tickets that link to it — check every existing `Ticket` in `kb/tickets/` for a markdown link pointing back to that `Exigence`'s file — if one already links to it, skip it; a re-run of `backlog` only fills gaps, it never recreates or overwrites a ticket. Also collect every `state: todo` ticket with no `sprint` whose technical, architecture or interface note misses the Grounding Rule below — free prose instead of the bullets, a bullet without a real reference, or a fallback line whose stage now exists: it is **refined** (those sections rewritten, nothing else). Nothing left to create or refine → say so and stop.

## Step 1b: Definition of Done

An `Exigence` tagged `nfr` (performance, availability, data protection, accessibility, compatibility) is a constraint on every ticket, not a feature: it gets no ticket of its own. Write or update `kb/rules/design/definition-de-termine.md` — what every ticket must meet before `validation` accepts it, each item with **how it is checked**:

```markdown
---
type: Design Rule
title: Définition de terminé
description: Ce que chaque ticket doit respecter avant d'être accepté
tags: [process, nfr]
status: stable
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Pour chaque ticket
- Les tests du plan passent ; la suite complète reste verte — vérifié par `hosa-tester`
- Lint, format et types sans erreur — commandes de `## Outillage qualité`
- Revue de code PASS — `hosa-reviewer`
- Contraintes de la note sécurité respectées et testées
- Textes conformes au lexique — `lexique_check.py`
- Documentation utilisateur à jour quand le ticket change ce qu'un utilisateur voit

## Exigences non fonctionnelles
- [<exigence nfr>](../../cdc/<slug>.md) — <cible chiffrée> — vérifié par : <test automatisé, mesure, outil> — s'applique à : <tous les tickets / ceux qui touchent X>
```

A target still "pas encore de chiffre" → the item says so; `qa-plan` then tests nothing for it, and the report says it. An `nfr` exigence that also needs something built (a data export for the right of access, a backup job) → its feature part gets a ticket, like any other exigence. Update this file in place on a re-run; log it to `kb/rules/design/log.md`.

## Step 2: Write the Story (PO role)

For each `Exigence` left after Step 1, **split it into tickets** first. A ticket is a **vertical slice**: something a persona can exercise end to end, through every layer it needs (data, logic, interface) — never one layer of many features ("toutes les tables", "toute l'API"). Built, tested and demonstrated alone inside one sprint: one screen with its action, one rule, one import. The first ticket of an exigence is the thinnest path that works; the next ones widen it. A process with several screens, roles or rules gives several tickets. An exigence that is already that small stays one ticket. When a ticket can't work before another (it needs its data, its screen or its endpoint: authentication, a reference table, a creation before its edition), give it `depends_on: [<slug>]` — a real dependency only, never "plus logique après". A cycle means the split is wrong: re-slice. Unsure where to cut, or which comes first → ask the user.

Then write each ticket to `kb/tickets/<slug>.md`, `state: todo`:

```markdown
---
type: Ticket
title: <titre>
description: <description courte>
tags: []
state: todo
depends_on: []          # tickets à livrer avant celui-ci — retiré si vide
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
En tant que [persona],
je veux [besoin],
afin de [valeur].

Lié à : [persona](../personnas/xxx.md), [exigence](../cdc/xxx.md)
```

If the `Exigence` names no clear persona, ask the user which persona it serves before writing the story — same "no guessing" discipline as every other Hosa skill.

Then append acceptance criteria derived from the `Exigence`'s own text — its `## Règles de gestion` and `## Cas d'erreur` above all — at least one scenario per rule and per error case this ticket covers, plus the nominal path:

```markdown
## Critères d'acceptation
- CA1 — Étant donné [contexte], quand [action], alors [résultat attendu]
```

Number the criteria `CA1`, `CA2`… and never renumber one: test plans, recettes and validation cite them by number. If the `Exigence` doesn't say enough to derive a concrete scenario, ask the user rather than inventing one. These criteria are what `qa-plan` grounds its technical test cases in, and what `recette`/`validation` check the delivered ticket against — never leave a ticket without at least one.

## Grounding Rule (Steps 3-5)

These notes are what a developer builds from, not a summary for a manager. Write them from the real project:
- First read the data dictionary (its path is in the `Infra` entry), the architecture and interface documentation, and query the project graph: `map` once per run, then `find`/`explain` on every module, entity, route or component the ticket touches.
- **Every bullet names something real** — a path, an entity with its exact fields and types, a route, a function or component — as the dictionary, the documentation or the graph give it. Something that doesn't exist yet is `à créer`: a new file in an existing module is plain `à créer`; a missing module, layer, entity, field or screen is `à créer — owner: <hosa-architect | hosa-data-engineer | hosa-ux-designer>`, a structural gap `sprint` won't plan until its owner fills it.
- No bullet without a reference: "faisable avec la stack", "couche service", "écran principal" are not answers. Can't name it → `inconnu — <ce qu'il faudrait lire ou décider>`, a visible gap.
- A bullet that doesn't apply says `aucun`; never leave a bullet out.

## Step 3: Add the Technical Note (senior dev role)

Read `kb/stack/` for `Stack Decision` concepts. If at least one exists, append to the ticket just written:

```markdown
## Note technique (senior dev)
- **Contrat** : <méthode + route, ou signature> — entrée <champs et types>, sortie <champs et types>, erreurs <code ou exception → cas>
- **Règles et validations** : <règle précise> → critère « <Étant donné… du Step 2> » (une ligne par règle)
- **Tests à écrire** : <chemin du fichier de test> — <cas : nominal, erreur, limite>
- **Hors périmètre** : <ce que ce ticket ne fait pas, et le ticket qui le fera>
- **Complexité** : <1|2|3> — <la partie qui coûte, et pourquoi au regard de la stack>
```

If `kb/stack/` has no `Stack Decision` yet (this skill invoked standalone, before `stack` ran), append instead:

```markdown
## Note technique (senior dev)
Stack pas encore choisie — faisabilité non évaluée.
```

Never block ticket creation on a missing `Stack Decision`.

## Step 4: Add the Architecture Placement (architect role)

Read `kb/infra/` for the `Infra` entry's `## Documentation d'architecture` heading (written by `architecture`) — that heading, specifically, not the data dictionary or migrations paths `schema-app`/`schema-db` also record in the same `Infra` entry. If it's there, read the documentation it points to and append to the ticket:

```markdown
## Placement architecture (architecte)
- **Module/couche** : <module> (<chemin>) — <pourquoi ici>
- **Fichiers touchés** : `<chemin>` — <ce qui y change> (un par ligne ; `à créer` si absent)
- **Données** : <Entité>.<champ> (<type>) lu/écrit — ou `aucun`
- **Migration** : <ce qu'elle ajoute ou modifie> — ou `aucune`
- **Points d'appel** : <symbole existant qui appellera ce code, d'après `graph.py affected`>
```

If no architecture documentation path is recorded yet (this skill invoked standalone, before `architecture` ran), append instead:

```markdown
## Placement architecture (architecte)
Architecture pas encore scaffoldée — placement non déterminé.
```

Never block ticket creation on a missing architecture doc.

## Step 5: Add the Interface Placement (UX/UI designer role)

Read `kb/infra/` for the `Infra` entry's `## Documentation d'interface` heading (written by `interface`) — that heading, specifically, not the architecture doc, the data dictionary, or the migrations paths the same `Infra` entry may also record. If it's there, read the documentation it points to and `kb/interface/navigation.md`, and append to the ticket:

```markdown
## Placement interface (UX/UI)
- **Écran / route** : <écran du plan de navigation> (`<route>`, `<chemin>`)
- **Composants** : `<chemin du composant>` — <rôle dans ce ticket> (`à créer` si absent) — ou `aucun`
- **États** : chargement, vide, erreur, succès — <ce que l'utilisateur voit dans chacun>
- **Libellés** : « <texte exact> » pour chaque bouton, message et titre ajouté
[Tout est nommé avec les termes de `kb/interface/lexique.md` ; un écran ou un terme absent est ajouté via `interface`, jamais inventé ici]
```

If no interface documentation path is recorded yet (this skill invoked standalone, before `interface` ran), append instead:

```markdown
## Placement interface (UX/UI)
Interface pas encore scaffoldée — placement non déterminé.
```

Never block ticket creation on a missing interface doc.

## Step 5b: Add the Security Note (cybersecurity expert role)

Read `kb/cdc/securite.md`, the `Security Rule`s in `kb/rules/security/`, and the linked `Exigence`'s `## Contraintes de sécurité` and security exigences. If the analysis exists, append the constraints this ticket must meet — so they're built in, not retrofitted:

```markdown
## Note sécurité (expert cybersécurité)
[Contraintes applicables à ce ticket — données sensibles touchées, contrôle d'accès attendu, journalisation, règles `kb/rules/security/` concernées — ou "Aucune contrainte propre à ce ticket — règles générales de `kb/rules/security/` applicables." quand c'est le cas]
```

If `kb/cdc/securite.md` doesn't exist yet (`securite` never ran), append instead:

```markdown
## Note sécurité (expert cybersécurité)
Analyse de sécurité pas encore faite — contraintes non déterminées.
```

Never block ticket creation on a missing analysis.

## Step 6: Priority and Estimate

Once every ticket for this run is written, ask the user once: "Dans quel ordre je priorise ces N tickets ? (numéros, ou 'pas encore' pour laisser sans priorité)". If given, write `priority: <rang>` (1 = le plus urgent) into each ticket's frontmatter in that order; tickets left unprioritized keep no `priority` field rather than an invented one — `sprint` treats those as lowest priority, after every explicitly ranked ticket. Then set each ticket's `estimate` yourself, in the senior dev role, from its `Complexité`: `1` (≤ ½ day), `2` (about 1 day) or `3` (2-3 days). Show them in the report; the user can correct any. Bigger than 3 → split it, as in Step 2.

## Step 7: Log and Check

Log each ticket created (and its `priority`/`estimate` once set) to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9. Then run the checker (see **Ticket complet**) on the tickets just written and report any gap it lists.

## Step 8: Checkpoint

Every structuration skill ends with its `hosa-git` checkpoint, so the foundation is already committed. Check anyway `git -C <root> status --porcelain -- . ':(exclude).hosa'`: not empty → dispatch `hosa-git` (Mode 3, checkpoint) with those files — `git` Mode 1 refuses to start a sprint on uncommitted source. Then the KB checkpoint for the tickets.

## Single-Ticket Mode

Run on one existing `Ticket` — created by `hosa-product-owner` from `qa`, `recette`, `debug`, `qualite`, `changement`, `bilan-sprint`, by the `hosa` free-form flow, or by hand. Fills only what's missing; never rewrites a section that already meets the Grounding Rule.

1. Run the checker on the ticket. Already complete → say so and stop.
2. Story, `Lié à :` or `## Critères d'acceptation` missing → dispatch `hosa-product-owner` (Responsibility 4) to add them, with the concept that surfaced the ticket. It returns an Open Question instead of guessing a persona or a scenario — ask the user and redispatch.
3. Each of the four notes missing or still on its fallback line → write it as in Steps 3-5b. If the stage it depends on still hasn't run (no `Stack Decision`, no architecture or interface doc, no security analysis), keep the fallback line and say which stage is missing — that's the only case where a ticket legitimately stays incomplete.
4. No `priority` → ask the user where it goes in the current backlog ("avant/après quel ticket ?", or "pas encore"). Given a rank, write it and shift every other `todo` ticket at that rank or below by one, so ranks stay unique. Then ask for an `estimate`, same rules as Step 6.
5. If the ticket was created during an `active` sprint, ask whether it joins that sprint now or waits for the next one; only write `sprint: <slug>` (and add it to the sprint's `## Tickets`) on an explicit yes — `sprint`'s readiness guard is what this mode just satisfied. Then run `qa-plan` for it: a ticket joins a sprint with its tests, like every other.
6. Log every change to `kb/tickets/log.md` (and `kb/sprints/log.md` if Step 5 added it), then rerun the checker and report its line for this ticket.

## No Commits

You don't commit — neither in the managed project nor in Hosa's own KB. Report what changed and let the user decide when to commit.

## Output

```
## Tickets précisés
- `kb/tickets/<slug>.md` — [titre] (sections réécrites)

## Tickets créés
- `kb/tickets/<slug>.md` — [titre] (state: todo) — [ligne du checker : complet / ce qui manque]

## Suite
Suite : `sprint` (proposition de sprint à valider), lancé sans attendre.
```
