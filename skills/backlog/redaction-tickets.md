# Rédaction des tickets

What `backlog` Steps 2-5c write in each ticket, for the agents that write them: `hosa-product-owner` (Steps 2-5, one `stories-<k>` pass of 8 tickets at most), `hosa-security` (Step 5b, Mode 5) and `hosa-legal` (Step 5c, Mode 3). The orchestration — batches, judge, tasks — is `backlog`'s (`SKILL.md`), not yours: read this file, not that one.

**Read by part.** The documents the notes cite (data dictionary, architecture, interface, threat model) are read by the section the ticket touches — `Grep -n "^## "` for the headings, then `Read` with `offset`/`limit`, or `graph find`/`explain` — never whole, once per pass: each line read stays in the context for every later turn (rieki: 25 KB of `donnees.md` read whole, then carried over 60 turns).

## Step 2: Write the Story (PO role)

**8 tickets per pass.** A pass writes 8 tickets at most, whatever the number of exigences it was given: each ticket written stays in your context for every later turn (rieki: 39 tickets in one pass, 273 k tokens). An exigence that splits into more: decide its whole split first, write the first 8, and list the others under `## Reprise` — `<slug> — <ce qu'il couvre> — depends_on: […]`, one line each — so the next pass writes them without splitting again.

For each `Exigence` left after Step 1, **split it into tickets** first. A ticket is a **vertical slice**: something a persona can exercise end to end, through every layer it needs (data, logic, interface) — never one layer of many features ("toutes les tables", "toute l'API"). Built, tested and demonstrated alone inside one sprint: one screen with its action and the rules that screen applies, one import, one command. Cut by screen, role or variant — not by rule: the rules a screen applies stay in its ticket while they fit in 8 criteria (**Too big** below). You write about 7 criteria per ticket whatever it covers, so each extra ticket adds criteria, tests and points (rieki: 0.65 ticket per bullet of the cahier des charges against 0.12 for pilot2, 4.5 criteria per bullet against 0.9, and 14 % of the criteria repeated in another ticket). The first ticket of an exigence is its main path, end to end; the next ones add a screen, a role or a variant. An exigence that is already that small stays one ticket. When a ticket can't work before another (it needs its data, its screen or its endpoint: authentication, a reference table, a creation before its edition), give it `depends_on: [<slug>]` — a real dependency only, never "plus logique après". A cycle means the split is wrong: re-slice. Unsure where to cut, or which comes first → ask the user.

**Too big.** More than 10 criteria — the checker's limit, counting those `hosa-security` and `hosa-legal` add after you: write 8 at most, so their abuse cases and legal constraints still fit (rieki: 21 tickets over 10 once the security notes were in) — two variants of one flow (two kinds of token, two triggers, two populations), or a ticket that adds a migration, a scheduled command and a screen → split, one variant or one rule per ticket (pilot2: « Ce n'était pas moi », 16 criteria over two variants, estimated "simple"; « Changer son adresse e-mail », 15 criteria with a migration and a daily purge, estimate 2). A catch-all ticket ("corrections de l'interface", eleven unrelated retouches plus a new action) is split by screen, and a new action goes to the ticket of its feature. A split never moves the abuse cases or legal constraints into a ticket of their own (« protéger X contre… », « sécuriser X ») : each one stays in the ticket of the criterion it protects, and every part keeps the abuse cases of its own flow. Too many criteria once they are in → split the flow itself, by variant, screen or rule (rieki: 14 tickets held only criteria moved out of their feature, mostly security, and became features of their own in the backlog).

**Security and compliance mechanisms first.** A mechanism several tickets use — the security event log, the security headers and production configuration, the rate-limit store, the legal pages and the CGU version, consent, the purge of expired data — is its own ticket, the first of its exigence, and every ticket that uses it lists it in `depends_on`: a criterion « … est journalisé » needs the log's ticket. Pilot2 ranked the security log at 43, the legal pages at 49 and the security headers at 51, while 14 tickets ranked 7 to 39 wrote to the log and the signup asked to accept CGU no page showed: security and compliance were left to the end, where they cost a redevelopment.

**Say it once.** A behaviour several tickets share — « Annuler » n'enregistre rien, a value shown as text and never as a link, the same abuse case on every style sheet — is a criterion of one ticket only: its mechanism's ticket, or the definition of done (Step 1b) when every screen must hold it. A ticket that uses it lists that ticket in `depends_on` and keeps at most one criterion that checks its screen calls it. `ticket_check --repetes` finds the criteria two tickets of one exigence both state (rieki: 56 pairs, pilot2: 8).

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

Then append acceptance criteria derived from the `Exigence`'s own text — its `## Règles de gestion` and `## Cas d'erreur` above all — at least one scenario per rule and per error case this ticket covers. The criteria of its `## Contraintes juridiques` are `hosa-legal`'s (Step 5c), those of its abuse cases `hosa-security`'s (Step 5b): each criterion has one writer, and the judge asks each writer for its own (`pipeline.json`, `juge-*`). A value the exigence gives by `voir [..](..) § ..` is the one of the fiche it cites:

```markdown
## Critères d'acceptation
- CA1 [RG2] — Étant donné [contexte], quand [action], alors [résultat attendu]
- CA2 [RG3, CE1] — Étant donné [contexte], quand [action], alors [résultat attendu]
```

**Cite the rule.** A criterion names, in brackets after its number, the rule(s) (`RGn`) and error case(s) (`CEn`) of the linked exigence it proves — the ids as the fiche writes them, never one you make up. When the exigence is split into several tickets, each rule and each error case goes to one ticket at least: decide it with the split, and list in `## Reprise` the ids the later tickets take. The checker refuses an id the exigence doesn't have, and `ticket_check --regles` refuses the backlog while an id of the exigence is cited by none of its tickets. A criterion that comes from no rule (the nominal path of the objective) has no brackets. An indicator (`INn`, a dashboard's `## Indicateurs`) is cited the same way, and its criterion gives the value it shows on the test dataset, with the records that produce it: `- CA2 [IN1] — Étant donné 38 places vendues sur 48 cette semaine dans le jeu de test, quand le gérant ouvre le tableau de bord, alors la tuile affiche « 38 / 48 » et mène à la liste de ces 38 réservations` — the checker refuses an indicator criterion with no number. A back-office ticket follows `back-office-et-tableaux-de-bord.md` of `interface`: list, record, history, the actions of the life cycle. An exigence whose rules have no id yet: no brackets — never number them yourself, report it under `## Retour Hosa`.

Number the criteria `CA1`, `CA2`… in order and never renumber one: test plans, recettes and validation cite them by number. A criterion is checkable by a test or a named person: « corrigée sous un mois », « notée hors application » or « une capture est jointe » are procedures, not criteria — they go to the procedure document the ticket writes, and the criterion checks that document exists and says it. If the `Exigence` doesn't say enough to derive a concrete scenario, ask the user rather than inventing one. These criteria are what `qa-plan` grounds its technical test cases in, and what `recette`/`validation` check the delivered ticket against — never leave a ticket without at least one.

## Grounding Rule (Steps 3-5c)

These notes are what a developer builds from, not a summary for a manager. Write them from the real project:
- First find, in the data dictionary (its path is in the `Infra` entry), the architecture and interface documentation, the sections the lot's tickets touch — read those, by part (above) — and query the project graph: `map` once per pass, then `find`/`explain` on every module, entity, route or component the ticket touches.
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

A component never hides what a criterion asks to see: when a `CAn` demands a refusal message (a wrong file type, a value out of range), the placement keeps the server-side refusal and its message reachable — no client-side filter or disabled control that makes the refused case impossible to enter (rieki: `type=` on the upload field hid the French refusal CA2 required). Reread each `CAn` naming a message against **Composants** and **États** before writing the note.

If no interface documentation path is recorded yet (this skill invoked standalone, before `interface` ran), append instead:

```markdown
## Placement interface (UX/UI)
Interface pas encore scaffoldée — placement non déterminé.
```

Never block ticket creation on a missing interface doc.

## Step 5b: Add the Security Note (`hosa-security`)

`hosa-security` (Mode 5 — Notes de tickets), on one lot of 8 tickets at most, once its stories are written; `hosa-juge` judges the lot after the security and legal notes. A note only listing rule names is not a note: pilot2's said « Règles X et Y : compteurs atomiques… », and its sprint 1 then had 2 reviews FAIL on a rule, 14 audit findings and 13 follow-up tickets. The agent reads `kb/cdc/securite.md`, `kb/securite/modele-menaces.md`, the `Security Rule`s and the linked `Exigence`'s `## Contraintes de sécurité`, then for each ticket:
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

`hosa-legal` (Mode 3 — Notes de tickets), same lot. Pilot2's tickets had no legal note: legal constraints sat in the security note as « Contrainte juridique : RGPD art. 12 à 20 », and the legal gate at release was the first to check them. The agent reads `kb/cdc/juridique.md` (registre, contraintes retenues, documents hors logiciel) and the linked `Exigence`'s `## Contraintes juridiques`, then for each ticket:
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

A `securite` or `juridique` stage the progress plan marks `non applicable` gets neither a note from you nor a criterion: `backlog` writes its line (`Non applicable — étape … écartée : …`) with `ticket_check --ecartees`. Leave that line as it is.

Never block ticket creation on a missing analysis.
