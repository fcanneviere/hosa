# Rédaction des exigences

What `redaction` writes in `kb/cdc/`, for the agent that writes it: `hosa-product-owner` (Responsibility 9). The orchestration — the notes to read, the questions to the user, the numbering, the assembled document — is the skill's: never read `redaction`'s `SKILL.md`.

**Questions.** Every « ask » below is, for you, an item of your report's `## Open Questions` (`retours` §3: numbered, the proposed answer as option `a)`), which the skill asks the user before redispatching you with the answers. Never a guess, never a placeholder. A question left unanswered is a `**Qn**` line of `decisions.md` (Step 2d).

**Writing pass.** From the comptes rendus paths given: for each `### <Processus>` with no exigence yet, Step 2; then Steps 2b, 2c and 2d; then one entry in `kb/cdc/log.md` (OKF §9) per file written. Return the paths written, one line each: `` `<path>` — <titre> `` (`retours` §4: paths, not content).

**Fixing pass** (anomalies of `kb/cdc/relecture.md` routed `→ redaction`, given by number). Each anomaly names its exigence and section: Read that exigence only (no other file, no search) and Edit that section in place — never rewrite the file, and skip Steps 2 and 2b unless the fix adds a business term (then one Edit of the glossary). Group the anomalies by file: one Read and one Edit per file, however many anomalies it carries (a cross-cutting fix — a renamed term, a repeated rule — is one `replace_all`, not one edit per exigence). Mark the anomalies `corrigée` in `kb/cdc/relecture.md` with one Edit per 5 files fixed, not one per anomaly — a cut pass restarts at the first one not marked. An anomaly that went through `interview` (its Complément mode) has its answer in `kb/cdc/interviews/*-complement.md` § `### A<n>`: read that section only, write the answer into the exigence. A fix that changes a value (threshold, list, message) changes it in its owner fiche, and replaces any copy with a link (« One source per fact », Step 2) — a copy left behind is the next pass's anomaly.

## Step 2: Write One `Exigence` Per Process

```
mkdir -p "<root>/.hosa/kb/cdc/"
```

For each process, `.hosa/kb/cdc/<slug-processus>.md` (slug = kebab-case of the process name):

```markdown
---
type: Exigence
title: <nom du processus>
description: "<une ligne : ce que ce processus accomplit>"
tags: []
espace: [front-office]   # [back-office], [front-office, back-office], ou [hors-application]
domaine: "<domaine métier>"   # ex. « Listes et courses », « Foyer et comptes », « Exploitation du service »
priorite: indispensable   # important | souhaitable
lot: 1
objectifs: [O1]   # les objectifs de kb/project/identity.md que ce processus sert, ou [obligation]
status: draft
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Objectif du processus
<une à deux phrases concrètes>

## Déclencheur
<l'événement ou la situation qui lance le processus ; le processus qui le précède, en lien : [<titre>](<slug>.md)>

## Données en entrée
- <donnée nécessaire>

## Données en sortie
- <donnée produite>

## Qui fait quoi
- <rôle/persona> : <action concrète>

## Règles de gestion
- **RG1** — <règle précise : calcul, condition, seuil, statut et transition — avec un exemple chiffré>

## Cas d'erreur
- **CE1** — <ce qui peut mal se passer> → <ce que le logiciel fait, ce que voit l'utilisateur>

## Responsable
<rôle ou persona responsable>

## Besoin(s) persona répondu(s)
- [<persona>](../personnas/<slug>.md) : <besoin précis>
```

`espace` says where the process lives: **front-office** (the application's end users — clients, citizens, members…), **back-office** (the people who run it — administrators, staff, operators, moderators), or both when a process has a user-facing side and a management side — or **hors-application**, alone, for a process with no screen (a scheduled job, an operator's script, a procedure): `interface` draws no page for it. Every front-office process implies back-office work (who creates, validates, moderates, corrects or deletes what end users see or submit): if the notes don't say who does it, ask — never leave the back-office side implicit.

**Frontmatter of the cahier des charges.** `cdc check` (`relecture`) counts a hole for each missing one:
- `domaine` groups the processes of one business area in the map of the document; reuse an existing domain before creating one.
- `priorite` and `lot` are the user's choices, gathered by `interview`: `indispensable` (without it the product fails its objectives), `important` (expected, can wait for a later lot), `souhaitable` (a plus). What the project will not do is a `## Non-objectifs` line, not a priority. Lot 1 is the first release that reaches the objectives. Missing in the notes → ask (one numbered question for all the exigences, a proposed table), never guess.
- `objectifs` lists the `O1`… of `kb/project/identity.md` § Objectifs mesurables this process serves. A process that answers a persona need and serves none → ask: an objective is missing, or the process is out of scope. A process the law, security or the basics impose (`juridique`, `securite`, `rgpd`, `fondamentaux` tags) writes `objectifs: [obligation]` when it serves no business objective — never a question to the user; `cdc check` refuses `obligation` without one of those tags. Transverse exigences leave it out.
- `nature` (`processus` | `nfr` | `contrainte`) only when the default is wrong: `tags: [nfr]` → nfr; `Aucun — exigence transverse.` with a `juridique`/`securite` tag → contrainte; otherwise processus. Ex. : a confirmation e-mail written by `securite` is still a process → `nature: processus`.

`## Déclencheur` makes the chain of processes readable: the document orders each domain by these links. A process with no trigger has no place in the chain — ask what starts it.

**One source per fact.** A value — a threshold, a duration, a limit, a closed list, the text of a message — is written once, in the fiche that owns it (the exigence whose rule it is; a limit shared by several processes, in the constraint that sets it). Every other place links to it: `voir [<titre>](<slug>.md) § <section>`. That holds for the other exigences, and for `glossaire.md`, `modele-metier.md`, `securite.md`, `juridique.md` and `identity.md`: a glossary entry defines the word, not its values; a notification line names the event, not its limit. A copy is fixed in one place and forgotten in the others — each `relecture` pass then finds the next one.

Use `generated: { by: human:<user>, at: <ISO8601> }` instead if the user dictated the content verbatim rather than you synthesizing it from interview notes.

A process with no rule of its own (pure data entry, say) writes `Aucune règle propre — saisie et consultation.` under `## Règles de gestion`; every process has error cases. These two sections are what `backlog` turns into acceptance criteria: a vague rule here becomes a guessed test later.

**Each rule and each error case has its id** — `RG1`, `RG2`… and `CE1`, `CE2`…, numbered per exigence, one top-level bullet each (its details as sub-bullets). A ticket's criterion cites it (`- CA1 [RG2] — …`), and `ticket_check --regles` refuses the backlog while a rule is cited by no criterion. So an id never moves: never renumber one, never reuse one; a rule that changes keeps its id; a rule dropped keeps its line, `- **RG2** — retirée : <raison>`. `cdc numerote` (Step 3) gives the missing ids — don't count by hand in a fiche you edit — and `cdc check` counts a hole (`règles`) for a rule without one.

If a process serves no specific persona (purely transverse — e.g. a compliance step), write `Aucun — exigence transverse.` under `## Besoin(s) persona répondu(s)` instead of a persona link. Every other section is still required — "transverse" doesn't excuse vagueness.

Each `<besoin précis>` must be found in the linked persona's `Besoins` (`kb_query.py .hosa/kb --type Persona --slug <slug> --sections "Besoins"`). A need the persona doesn't state is either the persona's real need, left unwritten → ask the user, then add it through `hosa` (persona update); or an invented one → remove the line. Never cite a need the persona doesn't hold: `contestation` re-checks exigences against personas.

Every section must be filled with the specific content gathered — a section with no matching information from the notes means you're missing input, not that you should write a placeholder. If information is missing, ask the user rather than writing something generic.

**Held or deduced.** A line the notes mark `[à confirmer]` (`interview`: the persona agent deduced it, the user did not confirm it) keeps its mark in the exigence, at the end of the line, and gets its `**Qn**` in `decisions.md` with the deduction as the proposed answer. Never drop the mark on your own: only the user's answer removes it. `cdc check` counts each marked line as a hole (`recueil`), so the cahier des charges is not signed on a guess. The same holds for what you add yourself to connect two notes: it is a deduction, marked, with its question.

The frequency and volumes of the notes go in `## Déclencheur` (« chaque soir, environ 30 listes »): `fondamentaux` sets the performance targets from them.

A `### Besoins écartés` line of the compte rendu becomes a decision in `decisions.md` (Step 2d): `relecture` reads it to fill the coverage table (`Écarté : <raison>`) instead of raising the need again.

### Non-functional and constraint exigences

An `Exigence` tagged `nfr` (performance, availability, compatibility, accessibility…) is a target, not a process. Same frontmatter (no `objectifs`), this body:

```markdown
## Exigence
- <la cible chiffrée, avec son unité et ses conditions> — ex. : « Cocher un article prend moins de 1 s dans 95 % des cas, avec 100 foyers actifs. »

## Mesure
- <comment on la vérifie : test automatisé, test de charge, outil, recette> — `backlog` la copie dans la définition de terminé

## Périmètre
<les écrans, processus ou données concernés>

## Justification
<le besoin ou la contrainte qui la fonde>

## Responsable
<rôle>

## Besoin(s) persona répondu(s)
- [<persona>](../personnas/<slug>.md) : <besoin précis>
```

A constraint (`juridique`, `securite`) keeps the process template, `## Déclencheur` optional. It states what the product does and what the user sees, with its values (durations, thresholds, limits). The way to build it — algorithm, hash, normalization, order of checks — is a `Security Rule` in `kb/rules/security/`, linked from the exigence: the document's reader is the sponsor, the rule's reader is the developer.

## Step 2b: Glossary

Keep `.hosa/kb/cdc/glossaire.md` — the domain vocabulary, so the CDC, the tickets and the code name each thing one way. `interface` starts its lexicon (`kb/interface/lexique.md`) from it.

```markdown
---
type: Glossaire
title: Glossaire du domaine
description: "Les termes métier du projet et leur sens unique"
tags: [glossaire]
status: draft
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Termes
- **<terme>** : <définition en une phrase, dans les mots du métier>. Pas : <synonymes à éviter>.
```

Add every business term of this run's exigences that a newcomer could misread or that has a synonym in the notes — never technical terms (table, endpoint). One entry per term, updated in place. Two words for one thing → the one the user chose in `interview`, or one numbered question with a recommendation; the other goes under "Pas". Write the exigences with the chosen term only.

## Step 2c: Business Model

Keep `.hosa/kb/cdc/modele-metier.md` — each business object the processes create or change, and what `cdc check` reads to find what nobody decided:

```markdown
---
type: Modèle Métier
title: Modèle métier
description: "Les objets du métier, leurs états, qui a le droit de faire quoi sur chacun, et qui est prévenu de quoi"
tags: [cdc]
status: draft
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## <Objet>
<définition en une phrase, ou « voir le glossaire »>

### Cycle de vie
- (début) → <état> : <qui ou quoi le fait passer> — [<exigence>](<slug>.md)
- <état> → <état> : <…> — [<exigence>](<slug>.md)
- <état> → (fin) : <suppression, effacement, purge> — [<exigence>](<slug>.md)

### Droits
| Rôle | Créer | Consulter | Modifier | Supprimer |
|---|---|---|---|---|
| <rôle> | <oui / non / à quelle condition> | … | … | … |

## Notifications
| Événement | Destinataires | Canal | Moment | Exigence |
|---|---|---|---|---|
| <événement> | <qui> | <push, e-mail, badge, état affiché> | <quand> | [<exigence>](<slug>.md) |
```

One `## <Objet>` per object of the glossary that has states (a list, an order, an account) — not for a plain value (a quantity). Every transition names the exigence that carries it. Write it from the exigences, not from imagination: each hole it shows — a state with no way out, a right no exigence decides (`?`), an event with no recipient or no moment — is a question for the user, recorded in `decisions.md`, never a guess. Every role of the matrix des rôles appears in each `### Droits` table.

## Step 2d: Decision Log

Keep `.hosa/kb/cdc/decisions.md` (`type: Journal des décisions`) — what was decided, when, by whom and why, so a decision never hides inside a rule:

```markdown
## Questions ouvertes
- **Q1** — <date> — [<exigence>](<slug>.md) : <la question> Proposé : <réponse recommandée>.
[Ou « Aucune. »]

## Décisions
- <date> — human:<user> — [<exigence>](<slug>.md) : <la décision>. Raison : <la raison donnée>.
```

A question you ask the user and they don't answer in this run → a `**Qn**` line, numbered after the last one. Once answered: remove the line, add the decision (newest first), and write it into the exigence it changes. A decision recorded in an exigence (« décision de human:… ») gets its line here too. A reason the user didn't give is written « non notée », never invented. The cahier des charges is not signed while a question stays open (`contestation`).
