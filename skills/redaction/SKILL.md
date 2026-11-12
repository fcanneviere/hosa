---
name: redaction
description: "Use to turn interview notes into structured exigences in `kb/cdc/`. CDC stage 2. Triggers: \"rédige les exigences\" with notes, after `interview`."
---

# Redaction

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start redaction`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block redaction --detail "<question>"`. Once the stage's output is written and committed: `done redaction`. Never skip these calls: without them a cut session can't resume (« reprends »), and `budget.js` can't apply the stage's `dispatch` rules (each agent's model, the agents at once) — they hold only while the stage is `en cours`.

**Tâches.** Before each dispatch, `avancement.py task add redaction <id> --agent hosa-product-owner --objet "<processus ou anomalies>"`; on its return, `task done redaction <id> --sortie <the paths it wrote>`: `ecriture` (Step 2), or `correction-<k>` (a fixing pass). Stopped on an Open Question → `task block redaction <id> --detail "<les questions>"`, and `task add` the same id again once answered. Called for `mineure` anomalies only (below): no task.

Turns the comptes rendus of `interview` into one `Exigence` concept per business process in `.hosa/kb/cdc/` — Objectif du processus / Déclencheur / Données en entrée / Données en sortie / Qui fait quoi / Règles de gestion / Cas d'erreur / Responsable / Besoin(s) persona répondu(s), and the domain, priority, lot and objectives in the frontmatter — with the glossary, the business model (`modele-metier.md`) and the decision log (`decisions.md`) beside them, then assembles the readable cahier des charges (`kb/project/cahier-des-charges.md`): the fiches are the source, the document is what a sponsor reads. **`hosa-product-owner` writes them** (Responsibility 9), by `${CLAUDE_PLUGIN_ROOT}/skills/redaction/redaction-exigences.md`; this skill finds the notes, asks the user, numbers and assembles. The session never writes an exigence itself: it is the heaviest writing of the cahier des charges, and its provenance says who wrote it.

## Flow

```
Notes : comptes rendus de kb/cdc/interviews/ (stable),
ou notes inline de l'utilisateur
        ↓
Dispatch hosa-product-owner (rédaction) avec leurs chemins
        ↓ Open Questions → Q1, Q2… à l'utilisateur, redispatch
Exigences (draft), glossaire, modèle métier, décisions,
log kb/cdc/log.md
        ↓
`cdc numerote` → `cdc assemble` → document lisible
        ↓
Checkpoint hosa-git → enchaîne sur `fondamentaux`
```

## Trigger

Manual: `/redaction`. Auto: immediately after `interview` finishes, or "rédige les exigences" / "écris le cahier des charges" with notes provided inline.

---

## Step 1: Get the Notes

**Fixing a relecture** (anomalies `ouverte` in `kb/cdc/relecture.md` routed `→ redaction`): those anomalies are the notes. List them (`<hosa> cdc revue "<root>/.hosa/kb" --route redaction`) and dispatch `hosa-product-owner` in a fixing pass with their numbers and `redaction-exigences.md` § Fixing pass — never the anomalies rewritten. Over 15 anomalies, one pass per theme (they go together when their files differ): a pass is cut at 150 tool calls. Then Step 3 and chain on `relecture`, not `fondamentaux`. Called by `relecture` or `contestation` for `mineure` anomalies only → skip this skill's `avancement.py` calls (the stage is not reopened) and return to the caller, not to `relecture`.

The notes are the comptes rendus of `kb/cdc/interviews/` — read from the KB, never from a session's memory (a `/clear` separates the stages): each `### <Processus>` with no exigence yet in `kb/cdc/`, plus `### Objets métier`, `### Besoins écartés` and `### Questions restées ouvertes`. A compte rendu still `status: draft` → `interview` is not finished: say so and stop. No compte rendu and no inline notes → ask: "Quelles sont les notes à rédiger ?" — accept whatever structure the user provides, and write it to `kb/cdc/interviews/<ISO-date>-notes.md` (`type: Compte Rendu`, `generated: { by: human:<user> }`) so the agent reads a path.

## Step 2: Dispatch the Writing

Dispatch `hosa-product-owner` (Responsibility 9) with the comptes rendus paths, `kb/project/identity.md`, `kb/personnas/`, the existing `kb/cdc/glossaire.md`, `modele-metier.md` and `decisions.md` if any, and the path of `redaction-exigences.md`. Its `## Open Questions` (a missing priority or lot, a back-office actor, a state with no way out, a need no persona holds) → the user, numbered (`retours` §3), all in one message; redispatch it with the answers. Its answers not given now stay `**Qn**` lines of `decisions.md` — the agent writes them. Never write or edit an exigence yourself, even for one line: redispatch.

## Step 3: Number and Assemble

The agent logged its writes in `kb/cdc/log.md`. Number the rules and error cases still without an id, and regenerate the readable document:

```bash
<hosa> cdc numerote "<root>/.hosa/kb"
<hosa> cdc assemble "<root>/.hosa/kb"
```

It writes `kb/project/cahier-des-charges.md` (`type: Cahier des charges`, `generated: process:hosa-cdc`) in the plan a project manager expects: 0 fiche du document, 1 contexte et enjeux, 2 objectifs et indicateurs, 3 périmètre et lots, 4 acteurs, 5 cartographie puis fiches des processus par domaine, 6 objets métier et glossaire, 7 exigences non fonctionnelles, 8 synthèse des contraintes juridiques et de sécurité, 9 hypothèses et risques, 10 critères de recette globaux, 11 décisions et questions ouvertes, 12 contrôle de complétude, annexes. The technical sections of the fiches (`## Contraintes de sécurité`, `## Contraintes juridiques`) stay in the fiches, linked. Never edit the document: fix the fiche, then regenerate.

## Commits

None here: the skill ends with the `hosa-git` checkpoint (`using-hosa`, Git checkpoints), then `done redaction`.

## Output

```
## Exigences écrites
- `kb/cdc/<slug>.md` — <titre> (status: draft)

## Cahier des charges
- Document : `kb/project/cahier-des-charges.md` — <N> trou(s) au contrôle de complétude, dont <N> ligne(s) `[à confirmer]`
- Questions ouvertes : <Q1… reprises en fin de rapport, ou « aucune »>

## Suite
Suite : `fondamentaux`, lancé sans attendre.
```
