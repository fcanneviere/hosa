---
name: relecture
description: "Use to check every exigence for precision, completeness and consistency, routing gaps to `redaction` or `interview`. CDC stage 6. Triggers: \"relis le cahier des charges\", after `securite`."
---

# Relecture

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start relecture`; refused → name the missing stage to the user and stop. Stopped on a user question: `block relecture --detail "<question>"`. Once the stage's output is written and committed: `done relecture`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

Reads the cahier des charges as written and checks it holds up — not a rewrite, a precision check.

## Flow

```
Scope : exigences écrites ou modifiées dans cette session
(redaction, fondamentaux, securite), ou l'ensemble de kb/cdc/
si appelé seul
        ↓
Pour chaque exigence : les sections de son modèle (processus,
non fonctionnelle, contrainte) sont-elles remplies, précises ?
        ↓
Cohérence entre exigences : sorties/entrées qui s'enchaînent,
responsables non contradictoires
        ↓
Complétude : `cdc check` (matrices) + couverture des personas
        ↓
Anomalies trouvées → route vers redaction (à corriger),
interview (info manquante) ou l'utilisateur (question ouverte)
        ↓
`cdc assemble` régénère le document lisible
        ↓
Propre → propose d'enchaîner sur `contestation`
```

## Trigger

Manual: `/relecture`. Auto: immediately after `securite`, or "relis le cahier des charges".

---

## Step 1: Scope

**`kb/cdc/relecture.md` exists** (an earlier pass, maybe a cut session) → read it first and never redo that pass: re-check only its anomalies still `ouverte` and the exigences changed since its `generated.at`: files of `kb/cdc/` modified after that date (file time — `redaction` doesn't commit, so a fix it just made is not in `git log` yet) plus those committed on `hosa-kb` since. Otherwise: in the pipeline, `relecture` runs after `securite`: check every `Exigence` written or changed in this session by `redaction`, `fondamentaux`, `juridique` and `securite`. Invoked alone, read every `Exigence` in `.hosa/kb/cdc/`.

**Exigences tagged `socle-comptes`.** Their standard text was reviewed once, in `${CLAUDE_PLUGIN_ROOT}/skills/fondamentaux/socle-comptes.md`: don't re-check it. Check only what the project filled in — no `{paramètre}` left, values matching `kb/cdc/fondamentaux.md` § Socle comptes, generic roles replaced by the project's, the matrice des rôles complete (every role of the project, its espace, what it sees and does) — and every rule or error case the project added. A socle rule missing or weakened → **Anomalie** (→ `redaction`).

**Who reads.** Steps 2-3 and the persona coverage of Step 3b are dispatched to `hosa-challenger` in **Relecture** mode, with `model: sonnet`, the scope (file paths) and the open anomalies of `kb/cdc/relecture.md` — never to a `general-purpose` agent, which runs on the session's model without Hosa's rules. It returns the anomalies and the coverage table; you run `cdc check`, route everything and write Step 5.

## Step 2: Precision and Completeness Check

Each exigence follows the template of its nature (`redaction`, Step 2): **processus** (the default), **non fonctionnelle** (`tags: [nfr]`), **contrainte** (`juridique`/`securite`, `Aucun — exigence transverse.`) — or the `nature` field when set. For each exigence, check every section of its template against these standards — mark **OK** or **Anomalie** with the exact problem:
- Frontmatter: `domaine`, `priorite` (`indispensable` | `important` | `souhaitable`), `lot`; `objectifs` on a processus that answers a persona need — `cdc check` lists the missing ones, Step 3b
- `Déclencheur` (processus): the event or the actor's situation that starts it, linking the process it follows when there is one — not "quand l'utilisateur le souhaite"
- `Exigence` (non fonctionnelle): a figure and its unit, never "rapide" or "sécurisé"; `Mesure`: how it is verified (test, measure, tool) — `backlog` copies both into the definition of done
- `Objectif du processus`: concrete and specific, not a restatement of the title
- `Données en entrée` / `Données en sortie`: named data, not "les infos nécessaires" or other placeholders
- `Qui fait quoi`: names an actual persona/rôle for every action listed, not "l'utilisateur" generically when a specific persona applies
- `Règles de gestion`: each rule testable — a condition, a threshold, a calculation or a status change with an example; not "selon les règles en vigueur". "Aucune règle propre" only for pure entry or consultation
- `Cas d'erreur`: at least one, each with the expected reaction; not "gérer les erreurs"
- `Responsable`: exactly one clear owner, not "l'équipe" or left implicit
- `espace` (frontmatter, functional exigences — not `nfr`): `front-office`, `back-office` or both, consistent with the roles in `Qui fait quoi`
- `Besoin(s) persona répondu(s)`: a real link to a `kb/personnas/` file, or an explicit "Aucun — exigence transverse"

- **Vocabulary:** an exigence uses a word `kb/cdc/glossaire.md` lists under "Pas", or a business term with no glossary entry that two exigences use with different meanings → **Anomalie** (→ `redaction`). No glossary yet → one anomaly asking `redaction` to start it, not one per term.

## Step 3: Cross-Exigence Consistency

Check pairs of exigences that plausibly connect (one's output feeds another's input, or they share a responsable):
- Does a claimed `Données en entrée` actually get produced somewhere as `Données en sortie`, or is it assumed from nowhere?
- Do two exigences assign the same responsibility to different responsables?

## Step 3b: Completeness Matrices

Steps 2-3 check what is written; this step finds what is missing. Run, on the whole KB whatever the scope:

```bash
<hosa> cdc check "<root>/.hosa/kb" --json
```

Each hole is an empty cell of a matrix — objectives × exigences, exigences × priority and lot, processes × trigger, objects × states and rights, events × recipients — and becomes one anomaly, `§` = the matrix:
- `cadrage`, `objectifs`, `priorités`, `périmètre`: a product choice → `interview` (transverse questions, asked to the user);
- `cartographie`, `chaîne des processus`, `traçabilité`, `exigences non fonctionnelles`: the information is in the notes or the exigences → `redaction`; otherwise → `interview`;
- `objets métier`, `cycles de vie`, `droits (CRUD)`, `notifications`: `redaction` writes `kb/cdc/modele-metier.md` from the exigences; a state with no way out or a right nobody decided is a missing rule → `interview`;
- `questions ouvertes`: each one goes to the user in your report, numbered Q1…, with its proposed answer; `redaction` records the answer in `kb/cdc/decisions.md`.

**Persona coverage.** `hosa-challenger` (Relecture mode) also returns the table `## Couverture des personas`: every `Besoins` and `Pain points` entry of every persona, and the exigence that answers it — or `Écarté : <raison>` pointing to `kb/cdc/decisions.md`, or `Hors CDC : <ticket ou défaut>` for an implementation defect found in a recette, or `Non couvert`. A `Non couvert` row is an anomaly → `interview`. On a scoped pass, it updates only the rows of the personas linked to the scope.

## Step 4: Report and Route

For each anomaly: which exigence and which section (`redaction` fixes it without searching), the exact problem, and whether it needs a **rewrite** (route to `redaction`), is missing **information that was never gathered** (route to `interview`), or waits for **a decision of the user** (an open question).

If no anomalies: report "Propre" and propose `contestation` as the next step.

## Step 5: Record the Report

Before reporting, write `kb/cdc/relecture.md` — the anomalies survive a cut session, and `redaction` works from this list:

```markdown
---
type: Revue Relecture
title: Relecture du cahier des charges
description: "Anomalies de précision, de complétude et de cohérence, et leur suite"
tags: [relecture]
generated: { by: relecture, at: <ISO8601> }
---
## Anomalies
- A1 — [exigence](<slug>.md) § <section> — <problème précis> — → redaction | → interview | → utilisateur — ouverte
## Couverture des personas
| Persona | Besoin ou irritant | Couvert par |
|---|---|---|
| <persona> | <besoin, ou « Irritant : » + l'irritant> | [<exigence>](<slug>.md) / Écarté : <raison> / Hors CDC : <défaut> / Non couvert |
## Verdict
<Propre / N anomalie(s) ouverte(s)>
```

Number anomalies A1…An, stable across passes. A re-run updates the file in place: a fixed anomaly becomes `corrigée`, a new one takes the next number. Then regenerate the readable document — `<hosa> cdc assemble "<root>/.hosa/kb"` writes `kb/project/cahier-des-charges.md`, holes included in its § 12 — then the git checkpoint (`using-hosa`), and `block relecture --detail "N anomalies ouvertes, voir kb/cdc/relecture.md"` while any stays `ouverte`.

This skill never edits an exigence: fixes happen in `redaction` (or `interview`), which marks each anomaly it closes `corrigée` in `kb/cdc/relecture.md`.

## Output

```
## Anomalies
- [Exigence] — [OK / Anomalie: <problème précis>] — [si anomalie: → redaction | → interview]
- [If none: "Aucune"]

## Verdict
[Propre / N anomalie(s) à corriger]

## Complétude
`cdc check` : [N trou(s) par matrice / complet] — couverture des personas : [N besoins et irritants, N non couverts]
Document : `kb/project/cahier-des-charges.md`

## Suite
[Propre :]
Suite : `contestation`, lancé sans attendre.
[Sinon :] liste des exigences à renvoyer et vers quel skill.
```
