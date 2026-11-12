---
name: relecture
description: "Use to check every exigence for precision, completeness and consistency, routing gaps to `redaction` or `interview`. CDC stage 6. Triggers: \"relis le cahier des charges\", after `securite`."
---

# Relecture

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start relecture`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block relecture --detail "<question>"`. Once the stage's output is written and committed: `done relecture`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

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
Chaque anomalie : passe, gravité (bloquante / mineure), origine
        ↓
Bloquantes → route vers redaction (à corriger), interview (info
manquante) ou l'utilisateur (question ouverte) : un tour de boucle
Mineures seules → redaction les corrige en une fois, sans boucle
        ↓
`cdc assemble` régénère le document lisible
        ↓
Propre → enchaîne sur `contestation`
```

## Trigger

Manual: `/relecture`. Auto: immediately after `securite`, or "relis le cahier des charges".

---

## Step 1: Scope

**`kb/cdc/relecture.md` exists** (an earlier pass, maybe a cut session) → read it first and never redo that pass. This pass is `p<n+1>`, `n` the highest `p` of its tags. Re-check only its anomalies still `ouverte` and what the fixes changed: the files of `kb/cdc/` modified after its `generated.at` (file time — `redaction` doesn't commit, so a fix it just made is not in `git log` yet) plus those committed on `hosa-kb` since. In those files, read the sections a fix touched, and the places that link to a value it changed — not the whole file again: the first pass read the rest. A new anomaly in a passage no fix touched is recorded only if it is `bloquante` (`cdc revue` refuses a `mineure` of origin `texte` on a re-pass). An open anomaly with no tag (written before the tags existed) gets its tag on this pass. Otherwise, this pass is `p1`: in the pipeline, `relecture` runs after `securite`: check every `Exigence` written or changed in this session by `redaction`, `fondamentaux`, `juridique` and `securite`. Invoked alone, read every `Exigence` in `.hosa/kb/cdc/`.

**Exigences tagged `socle-comptes`.** Their standard text was reviewed once, in `${CLAUDE_PLUGIN_ROOT}/skills/fondamentaux/socle-comptes.md`: don't re-check it. Check only what the project filled in — no `{paramètre}` left, values matching `kb/cdc/fondamentaux.md` § Socle comptes, generic roles replaced by the project's, the matrice des rôles complete (every role of the project, its espace, what it sees and does) — and every rule or error case the project added. A socle rule missing or weakened → **Anomalie** (→ `redaction`).

**Who reads.** Steps 2-3 and the persona coverage of Step 3b are dispatched to `hosa-challenger` in **Relecture** mode, with `model: sonnet`, the pass (`p1`, `p2`…), the scope (file paths — on a re-pass, the sections the fixes touched) and the open anomalies of `kb/cdc/relecture.md` — never to a `general-purpose` agent, which runs on the session's model without Hosa's rules. It returns the anomalies and the coverage table; you run `cdc check`, route everything and write Step 5.

## Step 2: Precision and Completeness Check

Each exigence follows the template of its nature (`redaction`, Step 2): **processus** (the default), **non fonctionnelle** (`tags: [nfr]`), **contrainte** (`juridique`/`securite`, `Aucun — exigence transverse.`) — or the `nature` field when set. For each exigence, check every section of its template against these standards — mark **OK** or **Anomalie** with the exact problem:
- Frontmatter: `domaine`, `priorite` (`indispensable` | `important` | `souhaitable`), `lot`, `espace` and `objectifs` of a processus — `cdc check` lists the missing ones, Step 3b. `objectifs: [obligation]` is right for an exigence the law, security or the basics impose (`juridique`, `securite`, `rgpd`, `fondamentaux` tags): never an anomaly, never a question to the user. A `nfr` or a `contrainte` has no `objectifs`, no `espace` and no `Déclencheur` to check
- `Déclencheur` (processus): the event or the actor's situation that starts it, linking the process it follows when there is one — not "quand l'utilisateur le souhaite"
- `Exigence` (non fonctionnelle): a figure and its unit, never "rapide" or "sécurisé"; `Mesure`: how it is verified (test, measure, tool) — `backlog` copies both into the definition of done
- `Objectif du processus`: concrete and specific, not a restatement of the title
- `Données en entrée` / `Données en sortie`: named data, not "les infos nécessaires" or other placeholders
- `Qui fait quoi`: names an actual persona/rôle for every action listed, not "l'utilisateur" generically when a specific persona applies
- `Règles de gestion`: each rule testable — a condition, a threshold, a calculation or a status change with an example; not "selon les règles en vigueur". "Aucune règle propre" only for pure entry or consultation. One rule per `RGn` bullet: two rules under one id → **Anomalie** (a criterion that cites the id would prove only one of them)
- `Cas d'erreur`: at least one, each with the expected reaction; not "gérer les erreurs". One case per `CEn` bullet
- `Contraintes de sécurité` / `Contraintes juridiques` (added by `securite` and `juridique`): each bullet testable like a rule — what the product does or refuses, with its value; not « sécuriser l'accès » or « respecter le RGPD ». `backlog` turns each one into a criterion and the judge checks that the ticket's note holds it: a vague one becomes a guessed criterion
- `Responsable`: exactly one clear owner, not "l'équipe" or left implicit
- `espace` (frontmatter, processus only): `front-office`, `back-office` or both, consistent with the roles in `Qui fait quoi`; `hors-application` for a process with no screen (a scheduled job, an operator's script, a procedure)
- `Besoin(s) persona répondu(s)`: a real link to a `kb/personnas/` file, or an explicit "Aucun — exigence transverse"

- **One source per fact:** a value (threshold, duration, limit, closed list, message text) is written in one fiche, its owner (`redaction`, Step 2); the others link to it. The same value restated in a second file → **Anomalie**: `bloquante` when the copies disagree (a contradiction), `mineure` when they agree (keep the owner's, replace the copy with a link). One anomaly per value, listing every copy — not one per file.
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

Each hole is an empty cell of a matrix — objectives × exigences, exigences × priority and lot, processes × trigger and espace, objects × states and rights, events × recipients — and becomes one `bloquante` anomaly (the sign-off waits for it), `§` = the matrix:
- `cadrage`, `objectifs`, `priorités`, `périmètre`: a product choice → `interview` (transverse questions, asked to the user);
- `cartographie`, `chaîne des processus`, `espaces`, `traçabilité`, `exigences non fonctionnelles`: the information is in the notes or the exigences → `redaction`; otherwise → `interview`;
- `objets métier`, `cycles de vie`, `droits (CRUD)`, `notifications`: `redaction` writes `kb/cdc/modele-metier.md` from the exigences; a state with no way out or a right nobody decided is a missing rule → `interview`;
- `questions ouvertes`: each one goes to the user in your report, numbered Q1…, with its proposed answer; `redaction` records the answer in `kb/cdc/decisions.md`;
- `recueil`: a line still `[à confirmer]` — the persona agent deduced it, the user never confirmed it → the user, as a question with the deduction as option `a)`; `redaction` removes the mark with the answer. One anomaly per exigence, listing its marked lines. Never judge a marked line as if it were a rule: it is not one yet;
- `règles`: a rule or an error case without its `RGn`/`CEn`, or an id used twice. No anomaly for a missing id: run `<hosa> cdc numerote "<root>/.hosa/kb"` yourself, then `cdc check` again — it is mechanical, no fiche changes meaning. An id used twice → `redaction` (one of the two rules takes the next free id; the tickets that cite it are checked by `ticket_check`).

**Persona coverage.** `hosa-challenger` (Relecture mode) also returns the table `## Couverture des personas`: every `Besoins` and `Pain points` entry of every persona, one row each, and the exigence that answers it — or `Écarté : <raison>` pointing to `kb/cdc/decisions.md`, or `Hors CDC : <ticket ou défaut>` for an implementation defect found in a recette, or `Non couvert`. A `Non couvert` row is an anomaly → `interview`. On a scoped pass, it updates only the rows of the personas linked to the scope — and adds the row of any entry a persona gained since the last pass (`hosa-key-user` appends irritants during interviews and recettes). `cdc check` counts: a persona with fewer rows than entries, or with no `## Besoins`, is a hole.

## Step 4: Report and Route

For each anomaly: which exigence and which section (`redaction` fixes it without searching), the exact problem, and whether it needs a **rewrite** (route to `redaction`), is missing **information that was never gathered** (route to `interview`), or waits for **a decision of the user** (an open question).

**Gravity.** Ask: would a developer or a tester, reading this, build or test the wrong thing, or have to stop and ask?
- **`bloquante`** — yes: two exigences that contradict each other, a rule or a target that can't be tested, a missing error case of a rule, a decision nobody took, data that comes from nowhere, a persona need no exigence covers, a legal or security gap.
- **`mineure`** — no: a synonym the glossary forbids, a `description` that lags, a model or glossary line behind an exigence that says it right, a copy of a value that agrees with its owner. A `mineure` always routes `→ redaction`: if it needs information or a decision, it is `bloquante`.

**Origin.** `texte` — the defect was there when the first pass read the passage; `correction` — a fix of an earlier anomaly made it (a copy left behind, a new contradiction); `regle-hosa` — the project is right and a Hosa rule or template doesn't fit it. A `regle-hosa` anomaly also gets its line in `kb/retours-hosa/journal.md` (`using-hosa`, auto-audit): Hosa is fixed, not each project.

If no anomalies: report "Propre" and chain on `contestation` without asking.

## Step 5: Record the Report

Before reporting, write `kb/cdc/relecture.md` — the anomalies survive a cut session, and `redaction` works from this list:

```markdown
---
type: Revue Relecture
title: Relecture du cahier des charges
description: "Anomalies de précision, de complétude et de cohérence, et leur suite"
tags: [relecture]
generated: { by: process:relecture, at: <ISO8601> }
---
## Anomalies
- A1 [p1, bloquante | mineure, texte | correction | regle-hosa] — [exigence](<slug>.md) § <section> — <problème précis> — → redaction | → interview | → utilisateur — ouverte
## Couverture des personas
| Persona | Besoin ou irritant | Couvert par |
|---|---|---|
| <persona> | <besoin, ou « Irritant : » + l'irritant> | [<exigence>](<slug>.md) / Écarté : <raison> / Hors CDC : <défaut> / Non couvert |
## Verdict
<Propre / N anomalie(s) ouverte(s)>
```

Number anomalies A1…An, stable across passes. A re-run updates the file in place: a fixed anomaly becomes `corrigée`, a new one takes the next number and this pass's tag. Then check the report:

```bash
<hosa> cdc revue "<root>/.hosa/kb"
```

Exit 1 on a tag missing or wrong, a `mineure` not routed `→ redaction`, or a re-pass `mineure` of origin `texte` → fix those lines (drop the anomaly, or raise it to `bloquante` if it is one) and run it again. Then regenerate the readable document — `<hosa> cdc assemble "<root>/.hosa/kb"` writes `kb/project/cahier-des-charges.md`, holes included in its § 12 — then the git checkpoint (`using-hosa`). Then route, by gravity — only a `bloquante` makes a loop:
- `bloquante` anomalies `→ interview` open → `back relecture interview --detail "<A-numbers> : <one line>"` (it reopens `interview`, then `redaction`, then `relecture`);
- otherwise, `bloquante` anomalies `→ redaction` open → `back relecture redaction --detail "<A-numbers> : <one line>"`; `redaction` fixes the open `mineure` ones in the same pass;
- only `→ utilisateur` bloquantes left → `block relecture --detail "<the questions in full>"`;
- only `mineure` anomalies left → no `back`: run `redaction` in its « Fixing a relecture » mode on them, without its `avancement.py` calls (the stage is not reopened). It marks them `corrigée`; no pass re-reads them. Then `done relecture`.

`back` refused (exit 1: two rounds already) → stop the loop: show the user the anomalies still open and what each round changed, and ask whether to run one more round (`back … --force`) or to scope the exigences down. `done relecture` refuses while `cdc revue` fails: a `bloquante` still `ouverte`, or a line badly tagged.

This skill never edits an exigence: fixes happen in `redaction`, which marks each anomaly it closes `corrigée` in `kb/cdc/relecture.md`. `interview` (its Complément mode) closes nothing: it gathers the answer of each `→ interview` anomaly, writes it in `kb/cdc/interviews/<date>-complement.md` and re-routes the anomaly `→ redaction`; `done interview` refuses while a `bloquante` still routes `→ interview`.

## Output

```
## Anomalies
- [A-number] [passe, gravité, origine] [Exigence] — [problème précis] — [→ redaction | → interview | → utilisateur]
- [If none: "Aucune"]

## Verdict
[Propre / N bloquante(s) et N mineure(s) à corriger]

## Complétude
`cdc check` : [N trou(s) par matrice / complet] — couverture des personas : [N besoins et irritants, N non couverts]
Document : `kb/project/cahier-des-charges.md`

## Mesure
[the table of `<hosa> cdc mesure "<root>/.hosa/kb"`: anomalies by pass, gravity and origin. A pass whose `correction` count grows means fixes create defects: say it in one sentence.]

## Suite
[Propre :]
Suite : `contestation`, lancé sans attendre.
[Sinon :] liste des exigences à renvoyer et vers quel skill.
```
