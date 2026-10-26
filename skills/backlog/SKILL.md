---
name: backlog
description: "Use to turn every stable Exigence into Product Backlog tickets — vertical slices with `depends_on`, story and criteria (PO), grounded technical, architecture and interface notes, security and legal notes whose abuse cases and legal constraints are criteria; `nfr` exigences become the definition of done; also refines vague `todo` tickets. Structuration stage 9. Triggers: \"crée le product backlog\", after `interface`."
---

# Backlog

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start backlog`; refused → name the missing stage to the user and stop. Stopped on a user question: `block backlog --detail "<question>"`. Once the stage's output is written and committed: `done backlog`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

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
hosa-security : note sécurité, chaque cas d'abus devient
un critère d'acceptation — ou "pas encore faite" sans analyse
        ↓
hosa-legal : note juridique, chaque contrainte juridique
devient un critère d'acceptation — ou "pas encore faite"
        ↓
Priorités : mécanismes de sécurité et de conformité d'abord
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
- real `## Note technique (senior dev)`, `## Placement architecture (architecte)`, `## Placement interface (UX/UI)`, `## Note sécurité (expert cybersécurité)` and `## Note juridique (expert conformité)` notes — not the fallback lines below;
- each abuse case of the security note and each legal constraint of the legal note tied to its acceptance criterion (`→ CAn`): security and compliance are built and tested with the ticket, not found at the audit, the recette or the release gate;
- a `priority`, unless the user explicitly answered "pas encore";
- a `depends_on` (when present) naming existing tickets, with no cycle, none ranked after this ticket.

The checker is the source of truth — run it from the managed project's root, with any Python 3.9+:

```bash
<hosa> ticket_check .hosa/kb [.hosa/kb/tickets/<slug>.md ...]
```

No ticket given → every `state: todo` ticket. Exit `0` = all complete, `1` = gaps listed per ticket.

---

## Step 1: Scope

List every `stable` `Exigence` (`kb_query.py .hosa/kb --type Exigence --where status=stable`), except those tagged `nfr` (Step 1b). For each one, `kb_query.py .hosa/kb --type Ticket --grep "cdc/<slug>.md"` lists the tickets that link to it — check every existing `Ticket` in `kb/tickets/` for a markdown link pointing back to that `Exigence`'s file — if one already links to it, skip it; a re-run of `backlog` only fills gaps, it never recreates or overwrites a ticket. Also collect every `state: todo` ticket with no `sprint` whose notes miss the Grounding Rule below — free prose instead of the bullets (a security note that only lists rule names), a bullet without a real reference, an abuse case or legal constraint with no `→ CAn`, a missing legal note, or a fallback line whose stage now exists: it is **refined** (those sections rewritten, the criteria they need appended, nothing else). The checker lists them all. Nothing left to create or refine → say so and stop.

## Step 1b: Definition of Done

An `Exigence` tagged `nfr` (performance, availability, data protection, accessibility, compatibility) is a constraint on every ticket, not a feature: it gets no ticket of its own. Write or update `kb/rules/design/definition-de-termine.md` — what every ticket must meet before `validation` accepts it, each item with **how it is checked**:

```markdown
---
type: Design Rule
title: Définition de terminé
description: "Ce que chaque ticket doit respecter avant d'être accepté"
tags: [process, nfr]
status: stable
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Pour chaque ticket
- Les tests du plan passent ; la suite complète reste verte — vérifié par `hosa-tester`
- Lint, format et types sans erreur — commandes de `## Outillage qualité`
- Revue de code PASS — `hosa-reviewer`
- Cas d'abus de la note sécurité et contraintes de la note juridique prouvés par leur critère — `hosa-tester`, `hosa-reviewer`
- Textes conformes au lexique — `<hosa> lexique_check .hosa/kb <checkout>` (script de Hosa, pas du projet : rien à installer)
- Documentation utilisateur à jour quand le ticket change ce qu'un utilisateur voit

## Exigences non fonctionnelles
- [<exigence nfr>](../../cdc/<slug>.md) — <cible chiffrée> — vérifié par : <test automatisé, mesure, outil> — s'applique à : <tous les tickets / ceux qui touchent X>
```

A target still "pas encore de chiffre" → the item says so; `qa-plan` then tests nothing for it, and the report says it. An `nfr` exigence that also needs something built (a data export for the right of access, a backup job) → its feature part gets a ticket, like any other exigence. Update this file in place on a re-run; log it to `kb/rules/design/log.md`.

## Step 2: Write the Story (PO role)

**By batches.** Dispatch `hosa-product-owner` for this step on at most 8 exigences at a time, a fresh dispatch per batch, each given its exigence paths and the slugs already written (for `depends_on`) — one pass over a whole cahier des charges (51 tickets on the pilot) hits its tool-call cap six times. A report with `## Reprise` → a fresh dispatch on what it lists.

For each `Exigence` left after Step 1, **split it into tickets** first. A ticket is a **vertical slice**: something a persona can exercise end to end, through every layer it needs (data, logic, interface) — never one layer of many features ("toutes les tables", "toute l'API"). Built, tested and demonstrated alone inside one sprint: one screen with its action, one rule, one import. The first ticket of an exigence is the thinnest path that works; the next ones widen it. A process with several screens, roles or rules gives several tickets. An exigence that is already that small stays one ticket. When a ticket can't work before another (it needs its data, its screen or its endpoint: authentication, a reference table, a creation before its edition), give it `depends_on: [<slug>]` — a real dependency only, never "plus logique après". A cycle means the split is wrong: re-slice. Unsure where to cut, or which comes first → ask the user.

**Too big.** More than 10 criteria, two variants of one flow (two kinds of token, two triggers, two populations), or a ticket that adds a migration, a scheduled command and a screen → split, one variant or one rule per ticket (pilot2: « Ce n'était pas moi », 16 criteria over two variants, estimated "simple"; « Changer son adresse e-mail », 15 criteria with a migration and a daily purge, estimate 2). A catch-all ticket ("corrections de l'interface", eleven unrelated retouches plus a new action) is split by screen, and a new action goes to the ticket of its feature.

**Security and compliance mechanisms first.** A mechanism several tickets use — the security event log, the security headers and production configuration, the rate-limit store, the legal pages and the CGU version, consent, the purge of expired data — is its own ticket, the first of its exigence, and every ticket that uses it lists it in `depends_on`: a criterion « … est journalisé » needs the log's ticket. Pilot2 ranked the security log at 43, the legal pages at 49 and the security headers at 51, while 14 tickets ranked 7 to 39 wrote to the log and the signup asked to accept CGU no page showed: security and compliance were left to the end, where they cost a redevelopment.

**Production setup is a ticket, not a release surprise.** A `## Documents à produire hors logiciel` line or a production prerequisite (least-privilege accounts, encrypted backups with a tested restore, proxy configuration) that needs code or configuration gets its ticket here, not from the audit (pilot2: three database Blocking findings and four production-setup tickets created after sprint 1). The document itself stays the user's.

**Exigences tagged `socle-comptes`** are not re-sliced: take the split of `${CLAUDE_PLUGIN_ROOT}/skills/fondamentaux/socle-comptes.md` § Découpage en tickets, the tickets the variants keep, with its `depends_on`. Rate limiting is in `connexion`'s criteria, never a later ticket (pilot2: login shipped without it). In Step 6, propose these tickets first, in the split's order.

Then write each ticket to `kb/tickets/<slug>.md`, `state: todo`:

```markdown
---
type: Ticket
title: <titre>
description: "<description courte>"
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

Then append acceptance criteria derived from the `Exigence`'s own text — its `## Règles de gestion`, `## Cas d'erreur` and `## Contraintes juridiques` above all — at least one scenario per rule, per error case and per legal constraint this ticket covers, plus the nominal path:

```markdown
## Critères d'acceptation
- CA1 — Étant donné [contexte], quand [action], alors [résultat attendu]
```

Number the criteria `CA1`, `CA2`… in order and never renumber one: test plans, recettes and validation cite them by number. A criterion is checkable by a test or a named person: « corrigée sous un mois », « notée hors application » or « une capture est jointe » are procedures, not criteria — they go to the procedure document the ticket writes, and the criterion checks that document exists and says it. If the `Exigence` doesn't say enough to derive a concrete scenario, ask the user rather than inventing one. These criteria are what `qa-plan` grounds its technical test cases in, and what `recette`/`validation` check the delivered ticket against — never leave a ticket without at least one.

## Grounding Rule (Steps 3-5c)

These notes are what a developer builds from, not a summary for a manager. Write them from the real project:
- First read the data dictionary (its path is in the `Infra` entry), the architecture and interface documentation, and query the project graph: `map` once per run, then `find`/`explain` on every module, entity, route or component the ticket touches.
- **Every bullet names something real** — a path, an entity with its exact fields and types, a route, a function or component — as the dictionary, the documentation or the graph give it. Something that doesn't exist yet is `à créer`: a new file in an existing module is plain `à créer`; a missing module, layer, entity, field or screen is `à créer — owner: <hosa-architect | hosa-data-engineer | hosa-ux-designer>`, a structural gap `sprint` won't plan until its owner fills it.
- A file another ticket marks `à créer` is cited by its path **and** that ticket goes into `depends_on` — never as if it already existed: `sprint` would plan this ticket without its creator (pilot2: `core/limitation.py`). The checker lists every path cited as existing that the project lacks.
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

## Step 5b: Add the Security Note (`hosa-security`)

Dispatch `hosa-security` (Mode 5 — Notes de tickets), by batches of 8 tickets like Step 2, with the ticket paths. A note only listing rule names is not a note: pilot2's said « Règles X et Y : compteurs atomiques… », and its sprint 1 then had 2 reviews FAIL on a rule, 14 audit findings and 13 follow-up tickets. The agent reads `kb/cdc/securite.md`, `kb/securite/modele-menaces.md`, the `Security Rule`s and the linked `Exigence`'s `## Contraintes de sécurité`, then for each ticket:
- **appends an acceptance criterion per abuse case** this ticket must refuse, after the last `CAn`, in the PO's Given/When/Then form — « Étant donné …, quand un attaquant …, alors … » — unless an existing criterion already states it;
- writes the note:

```markdown
## Note sécurité (expert cybersécurité)
- **Règles** : `<slug de règle>` — <ce que la règle exige ici : seuil, clé, champ, mode de panne> (une ligne par règle)
- **Cas d'abus** : (un par ligne, recopié de `kb/cdc/securite.md` ou du modèle de menaces) — ou `aucun`
  - Étant donné …, quand un attaquant …, alors … → CAn
- **Contrôle d'accès** : <rôles permis, rôles refusés et leur réponse, filtre (foyer, propriétaire)> — ou `aucun`
- **Journalisation** : <événement, journal, champs ; ticket qui fournit le journal, dans `depends_on`> — ou `aucun`
- **Données sensibles** : <champ (classification)> — <où il ne doit jamais sortir : journal, réponse, e-mail, cache> — ou `aucun`
```

A ticket with no constraint of its own writes `aucun` on each bullet but **Règles** (the general rules it touches). If `kb/cdc/securite.md` doesn't exist yet (`securite` never ran), append instead:

```markdown
## Note sécurité (expert cybersécurité)
Analyse de sécurité pas encore faite — contraintes non déterminées.
```

Never block ticket creation on a missing analysis.

## Step 5c: Add the Legal Note (`hosa-legal`)

Dispatch `hosa-legal` (Mode 3 — Notes de tickets), same batches. Pilot2's tickets had no legal note: legal constraints sat in the security note as « Contrainte juridique : RGPD art. 12 à 20 », and the legal gate at release was the first to check them. The agent reads `kb/cdc/juridique.md` (registre, contraintes retenues, documents hors logiciel) and the linked `Exigence`'s `## Contraintes juridiques`, then for each ticket:
- **appends an acceptance criterion per legal constraint** the ticket delivers, unless an existing criterion already states it — testable, not « respecter le RGPD »;
- writes the note:

```markdown
## Note juridique (expert conformité)
- **Contraintes** : (une par ligne) — ou `aucun`
  - <contrainte> — <article> → CAn
- **Données personnelles** : <traitement du registre> — <données touchées> — base légale <…> — conservation <durée> — ou `aucun`
- **Hors logiciel** : <document de `## Documents à produire hors logiciel` lié, et qui le produit> — ou `aucun`
```

If `kb/cdc/juridique.md` doesn't exist yet (`juridique` never ran), append instead:

```markdown
## Note juridique (expert conformité)
Analyse juridique pas encore faite — contraintes non déterminées.
```

Never block ticket creation on a missing analysis.

## Step 6: Priority and Estimate

Once every ticket for this run is written, propose an order and ask the user once: "Je propose cet ordre pour ces N tickets ; je l'applique ? (oui, un autre ordre, ou 'pas encore' pour laisser sans priorité)". The proposal puts every ticket after the tickets in its `depends_on`, and the security and compliance mechanisms (Step 2) right after the first slice that makes them usable — never in a block at the end. An order from the user that ranks a ticket before one of its dependencies → say which, once; the checker reports it until it's fixed. Given an order, write `priority: <rang>` (1 = le plus urgent) into each ticket's frontmatter in that order; tickets left unprioritized keep no `priority` field rather than an invented one — `sprint` treats those as lowest priority, after every explicitly ranked ticket. Then set each ticket's `estimate` yourself, in the senior dev role, from its `Complexité`: `1` (≤ ½ day), `2` (about 1 day) or `3` (2-3 days). Show them in the report; the user can correct any. Bigger than 3 → split it, as in Step 2.

## Step 7: Log and Check

Log each ticket created (and its `priority`/`estimate` once set) to `kb/tickets/log.md` (create if missing) — chronological, most recent date first, per OKF §9. Then run the checker (see **Ticket complet**) on the tickets just written and report any gap it lists.

## Step 8: Checkpoint

Every structuration skill ends with its `hosa-git` checkpoint, so the foundation is already committed. Check anyway `git -C <root> status --porcelain -- . ':(exclude).hosa'`: not empty → dispatch `hosa-git` with `model: haiku` (Mode 3, checkpoint) with those files — `git` Mode 1 refuses to start a sprint on uncommitted source. Then the KB checkpoint for the tickets.

## Single-Ticket Mode

Run on one existing `Ticket` — created by `hosa-product-owner` from `qa`, `recette`, `debug`, `qualite`, `changement`, `bilan-sprint`, by the `hosa` free-form flow, or by hand. Fills only what's missing; never rewrites a section that already meets the Grounding Rule.

1. Run the checker on the ticket. Already complete → say so and stop.
2. Story, `Lié à :` or `## Critères d'acceptation` missing → dispatch `hosa-product-owner` (Responsibility 4) to add them, with the concept that surfaced the ticket. It returns an Open Question instead of guessing a persona or a scenario — ask the user and redispatch.
3. Each of the five notes missing, still on its fallback line or failing the checker → write it as in Steps 3-5c (`hosa-security` and `hosa-legal` for theirs, with the criteria they append). A ticket born from an audit finding keeps the finding's `fichier:ligne` in its technical note, and its security note names the rule the finding broke. If the stage a note depends on still hasn't run (no `Stack Decision`, no architecture or interface doc, no security or legal analysis), keep the fallback line and say which stage is missing — that's the only case where a ticket legitimately stays incomplete.
4. No `priority` → propose a rank in the current backlog — after its `depends_on`, and a security or compliance fix before the tickets that build on the flawed code — and ask the user ("je le place en N, avant <ticket> ?", or "pas encore"). Given a rank, write it and shift every other `todo` ticket at that rank or below by one, so ranks stay unique and whole. Then set its `estimate`, same rules as Step 6.
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
