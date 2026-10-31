---
name: redaction
description: "Use to turn interview notes into structured exigences in `kb/cdc/`. CDC stage 2. Triggers: \"rédige les exigences\" with notes, after `interview`."
---

# Redaction

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start redaction`; refused → name the missing stage to the user and stop. Stopped on a user question: `block redaction --detail "<question>"`. Once the stage's output is written and committed: `done redaction`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

Writes one `Exigence` concept per business process into `.hosa/kb/cdc/`, with a structured body: Objectif du processus / Déclencheur / Données en entrée / Données en sortie / Qui fait quoi / Règles de gestion / Cas d'erreur / Responsable / Besoin(s) persona répondu(s) — and the domain, priority, lot and objectives it serves in its frontmatter. Keeps the business model (`modele-metier.md`) and the decision log (`decisions.md`) beside them, then assembles the readable cahier des charges (`kb/project/cahier-des-charges.md`): the fiches are the source, the document is what a sponsor reads.

## Flow

```
Source des notes : sortie de `interview` (même session) ou
notes inline de l'utilisateur
        ↓
Pour chaque processus : écrit une Exigence structurée
(status: draft) dans kb/cdc/
        ↓
Modèle métier (objets, cycles de vie, droits, notifications)
et journal des décisions (questions ouvertes, décisions)
        ↓
Log kb/cdc/log.md → `cdc assemble` → document lisible
        ↓
Enchaîne sur `fondamentaux`
```

## Trigger

Manual: `/redaction`. Auto: immediately after `interview` finishes, or "rédige les exigences" / "écris le cahier des charges" with notes provided inline.

---

## Step 1: Get the Notes

**Fixing a relecture** (anomalies `ouverte` in `kb/cdc/relecture.md` routed `→ redaction`): those anomalies are the notes. Each anomaly names its exigence and section: Read that exigence only (no other file, no search) and Edit that section in place — never rewrite the file, and skip Steps 2 and 2b unless the fix adds a business term (then one Edit of the glossary). Group the anomalies by file: one Read and one Edit per file, however many anomalies it carries (a cross-cutting fix — a renamed term, a repeated rule — is one `replace_all`, not one edit per exigence). Mark the anomalies `corrigée` in `kb/cdc/relecture.md` with one Edit per 5 files fixed, not one per anomaly — a cut session restarts at the first one not marked. Over 15 anomalies, dispatch one pass per theme instead of one long pass: a pass is cut at 150 tool calls. Then chain on `relecture`, not `fondamentaux`.

If `interview` just ran in this session, use its notes directly. Otherwise ask: "Quelles sont les notes à rédiger ?" — accept whatever structure the user provides; you don't require `interview`'s exact format.

## Step 2: Write One `Exigence` Per Process

```
mkdir -p .hosa/kb/cdc/
```

For each process, `.hosa/kb/cdc/<slug-processus>.md` (slug = kebab-case of the process name):

```markdown
---
type: Exigence
title: <nom du processus>
description: "<une ligne : ce que ce processus accomplit>"
tags: []
espace: [front-office]   # [back-office], ou [front-office, back-office]
domaine: "<domaine métier>"   # ex. « Listes et courses », « Foyer et comptes », « Exploitation du service »
priorite: indispensable   # important | souhaitable
lot: 1
objectifs: [O1]   # les objectifs de kb/project/identity.md que ce processus sert
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
- <règle précise : calcul, condition, seuil, statut et transition — avec un exemple chiffré>

## Cas d'erreur
- <ce qui peut mal se passer> → <ce que le logiciel fait, ce que voit l'utilisateur>

## Responsable
<rôle ou persona responsable>

## Besoin(s) persona répondu(s)
- [<persona>](../personnas/<slug>.md) : <besoin précis>
```

`espace` says where the process lives: **front-office** (the application's end users — clients, citizens, members…), **back-office** (the people who run it — administrators, staff, operators, moderators), or both when a process has a user-facing side and a management side. Every front-office process implies back-office work (who creates, validates, moderates, corrects or deletes what end users see or submit): if the notes don't say who does it, ask — never leave the back-office side implicit.

**Frontmatter of the cahier des charges.** `cdc check` (`relecture`) counts a hole for each missing one:
- `domaine` groups the processes of one business area in the map of the document; reuse an existing domain before creating one.
- `priorite` and `lot` are the user's choices, gathered by `interview`: `indispensable` (without it the product fails its objectives), `important` (expected, can wait for a later lot), `souhaitable` (a plus). What the project will not do is a `## Non-objectifs` line, not a priority. Lot 1 is the first release that reaches the objectives. Missing in the notes → ask (one numbered question for all the exigences, a proposed table), never guess.
- `objectifs` lists the `O1`… of `kb/project/identity.md` § Objectifs mesurables this process serves. A process that answers a persona need and serves none → ask: an objective is missing, or the process is out of scope. Transverse exigences leave it out.
- `nature` (`processus` | `nfr` | `contrainte`) only when the default is wrong: `tags: [nfr]` → nfr; `Aucun — exigence transverse.` with a `juridique`/`securite` tag → contrainte; otherwise processus. Ex. : a confirmation e-mail written by `securite` is still a process → `nature: processus`.

`## Déclencheur` makes the chain of processes readable: the document orders each domain by these links. A process with no trigger has no place in the chain — ask what starts it.

Use `generated: { by: human:<user>, at: <ISO8601> }` instead if the user dictated the content verbatim rather than you synthesizing it from interview notes.

A process with no rule of its own (pure data entry, say) writes `Aucune règle propre — saisie et consultation.` under `## Règles de gestion`; every process has error cases. These two sections are what `backlog` turns into acceptance criteria: a vague rule here becomes a guessed test later.

If a process serves no specific persona (purely transverse — e.g. a compliance step), write `Aucun — exigence transverse.` under `## Besoin(s) persona répondu(s)` instead of a persona link. Every other section is still required — "transverse" doesn't excuse vagueness.

Each `<besoin précis>` must be found in the linked persona's `Besoins` (`kb_query.py .hosa/kb --type Persona --slug <slug> --sections "Besoins"`). A need the persona doesn't state is either the persona's real need, left unwritten → ask the user, then add it through `hosa` (persona update); or an invented one → remove the line. Never cite a need the persona doesn't hold: `contestation` re-checks exigences against personas.

Every section must be filled with the specific content gathered — a section with no matching information from the notes means you're missing input, not that you should write a placeholder. If information is missing, ask the user rather than writing something generic.

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

## Step 3: Log and Assemble

Append to `kb/cdc/log.md` (create if missing) — OKF §9: chronological, most recent date first, grouped by date. Then regenerate the readable document:

```bash
<hosa> cdc assemble "<root>/.hosa/kb"
```

It writes `kb/project/cahier-des-charges.md` (`type: Cahier des charges`, `generated: process:hosa-cdc`) in the plan a project manager expects: 0 fiche du document, 1 contexte et enjeux, 2 objectifs et indicateurs, 3 périmètre et lots, 4 acteurs, 5 cartographie puis fiches des processus par domaine, 6 objets métier et glossaire, 7 exigences non fonctionnelles, 8 synthèse des contraintes juridiques et de sécurité, 9 hypothèses et risques, 10 critères de recette globaux, 11 décisions et questions ouvertes, 12 contrôle de complétude, annexes. The technical sections of the fiches (`## Contraintes de sécurité`, `## Contraintes juridiques`) stay in the fiches, linked. Never edit the document: fix the fiche, then regenerate.

## No Commits

You don't commit. Report what changed in the KB and let the user or the orchestrating flow decide when to commit.

## Output

```
## Exigences écrites
- `kb/cdc/<slug>.md` — <titre> (status: draft)

## Cahier des charges
- Document : `kb/project/cahier-des-charges.md` — <N> trou(s) au contrôle de complétude
- Questions ouvertes : <Q1… reprises en fin de rapport, ou « aucune »>

## Suite
Suite : `fondamentaux`, lancé sans attendre.
```
