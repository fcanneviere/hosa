---
name: adoption
description: "Use when a project's code exists before Hosa: read what it does, judge what is good or wrong, before the cahier des charges. Triggers: \"projet existant\", \"analyse le code existant\", \"adopte ce code\"."
---

# Adoption

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Stage `adoption`, between `hosa` and `interview`. Before anything: `avancement.py start adoption`; refused → name the missing stage to the user and stop; refused as already done or `non applicable` → a run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block adoption --detail "<question>"`. Once the output is written and committed: `done adoption`.

**Tâches.** Before each dispatch, `avancement.py task add adoption <id> --agent <agent>`; on its return, `task done adoption <id> --sortie <the paths it wrote>`: `inventaire` (`hosa-analyst`, `kb/existant/inventaire.md`), `documentation` (`hosa-documentation` on `model: sonnet`, the rebuilt documents and their `kb/documentation/` entries), `audit-qualite` (`hosa-senior-dev`, `kb/qualite/adoption.md`), `audit-securite` (`hosa-security`, `kb/securite/audit-<date>-adoption.md`), `audit-bdd` (`hosa-dba`, `kb/qualite/adoption-bdd.md`), `diagnostic` (`hosa-analyst`, `kb/existant/diagnostic.md`). `inventaire`, `documentation` and `diagnostic` are controlled (`<hosa> existant_check .hosa/kb inventaire|documentation|diagnostic`): a gap refuses `task done`; `documentation` refuses `task add` before `inventaire` is done, `diagnostic` while `inventaire`, `documentation` or an audit is still open. Stopped on an Open Question → `task block adoption <id> --detail "<la question>"`, and `task add` the same id again once answered.

The code existed before Hosa. This stage says what it does and what in it is sound or wrong, each fact with its file and line. Then the cahier des charges starts from it: `interview` asks about each process the code does, the exigences keep them, the backlog fixes what the user chose to fix. `hosa-analyst` reads; the audits keep their owners; this skill talks to the user and dispatches.

## Flow

```
## Point de départ = Neuf → skip, enchaîne `interview`
        ↓ Existant
Un message : inventaire (hosa-analyst) + audit qualité (hosa-senior-dev)
+ audit sécurité (hosa-security), en parallèle
        ↓
Rôles sans persona → l'utilisateur crée les personas manquants
Une base de données constatée → audit base (hosa-dba)
Documentation constatée → reconstruite au standard Hosa (hosa-documentation)
        ↓
Diagnostic (hosa-analyst) : points forts, problèmes D1…, propositions
        ↓
L'utilisateur tranche chaque problème : corriger, accepter, plus tard
        ↓
done adoption → checkpoint hosa-git → enchaîne `interview`
```

## Trigger

Chained by `hosa` when `## Point de départ` says `Existant`. Manual: `/adoption`. Auto: "projet existant", "analyse le code existant", "adopte ce code", "il y a déjà du code". Reopened by `interview` (`back interview adoption`) → Step 6.

---

## Step 0: New or existing

Read `## Point de départ` of `kb/project/identity.md`.
- **Neuf** → `skip adoption --detail "projet neuf"`, say it in one line, chain `interview`.
- **Existant** → go on. `skip adoption` is refused while it says `Existant`.
- No source file in the project's root (only `.hosa/`, a README) → say so, and ask once: correct `## Point de départ` to `Neuf` (`hosa`, update flow), or name the folder of the code.

## Step 1: Read the code and audit it, in one message

Three dispatches in one message — they are independent:
- `inventaire`: `hosa-analyst` Mode 1, with the project's root and the `## Point de départ` list (what the user keeps as it is).
- `audit-qualite`: `hosa-senior-dev`, the audit of `qualite` (its fixed checklist), on the **whole codebase**, written to `kb/qualite/adoption.md`.
- `audit-securite`: `hosa-security` Mode 2, the whole codebase, the secrets in the git history and the dependencies, written to `kb/securite/audit-<date>-adoption.md`. `kb/rules/security/` is empty before `securite`: the baseline rules apply.

Each brief says: static reading only, no Docker environment exists before `infra`, nothing is installed or started. A finding with no input to show it stays `À corriger`, never `Bloquant` — a readable secret is its own proof.

## Step 2: Roles and database

On `inventaire`'s return:
- A role with `persona : aucun` → ask the user, one question for them all: create a persona for each (recommended when a person really plays it), or merge it into an existing persona. Create them with `hosa` (« Writing personas », then « Enriching personas »), then fix each role's `persona :` line.
- `## Données constatées` names a database or migrations → `audit-bdd`: `hosa-dba` Mode 4 (audit), static reading of the migrations, models and queries, written to `kb/qualite/adoption-bdd.md`. No database → no `audit-bdd` task.

## Step 2b: Rebuild the existing documentation

`## Documentation constatée` lists each documentation file of the project with its target in Hosa's layout (the checker refuses a file it misses). A target other than `aucune` → `documentation`: `hosa-documentation` Mode 4, on `model: sonnet` (`pipeline.json` `dispatch`), in the same message as `audit-bdd`. It rebuilds each target to Hosa's standard (layout, templates, ASD-STE100 in the project's language), keeps only what the code confirms, and returns the gaps between the old documents and the code. No target → no task.

Its report lists the sources kept beside their new target. One question for them all:

**Q.** Les anciens fichiers de documentation (`<liste>`) sont repris dans `docs/`. Que fait-on des originaux ?
- a) Chacun devient un renvoi d'une ligne vers son nouveau fichier : une seule source, rien ne dérive.
- b) On les supprime : git garde leur historique.
- c) On les garde tels quels.

a) or b) → `task add adoption documentation-originaux --agent hosa-documentation` with the answer and the list; never in the main session. Give its `## Écarts` to Step 3: each one becomes a problem `source : inventaire`.

## Step 3: Diagnostic

`diagnostic`: `hosa-analyst` Mode 2, with the inventory and the audits' paths. It merges the audits, adds what the inventory shows (a process `partiel` or `cassé`, untested rules, dead code), and proposes a decision for each problem.

## Step 4: The user decides

Show the points forts (one line each), then the problems in one table: `Dn`, gravité, ce qui se passe, code, proposition. Then one question per kind, the recommended answer `a)`:

**Q1.** Je propose de corriger D1, D3 ; plus tard D2 ; accepter D4. Tu valides ?
- a) Oui, comme proposé.
- b) Je change : « D3 accepter », « D2 corriger »…

A `Bloquant` the user accepts → ask its reason: it goes after the decision. Write each answer under its problem, `  - Décision : corriger | accepter | plus tard — <raison, dite par l'utilisateur>`, a line under `## Révisions`, then `reponse adoption --detail "Q1 a"`. What the user says to keep (a module, a convention, the stack) goes to `## Point de départ` of `identity.md`: `stack` and `architecture` read it as a fixed decision.

## Step 5: Close

`done adoption` refuses while a problem has no decision, a path is wrong, a document is not rebuilt or the identity is not `Existant` (`<hosa> existant_check .hosa/kb adoption`). Checkpoint (`hosa-git` Mode 3: `kb/existant/`, the audits, the personas, the rebuilt documentation and `kb/documentation/`), then chain `interview` in one line: « Code existant lu : <n> processus, <b> problèmes à corriger. Je lance l'interview. »

Downstream, each `EXn` must be cited by a compte rendu (`done interview`) and by an exigence's `existant: [EXn]` unless a compte rendu says it `abandonné` (`done redaction`); in the backlog, what the code does is a `state: done` ticket (`existant: [EXn]`, each criterion proved under `## Preuve`), what is missing a `todo` ticket with its `## Écart à l'existant`, and each `Dn` decided `corriger` a ticket with `diagnostic: [Dn]` (`done backlog`).

## Step 6: A loop from `interview`

`interview` found a process or a fact the inventory missed (`back interview adoption --cause <EXn ou sujet> --detail "<the gap>"`): `task add adoption complement-<n> --agent hosa-analyst`, Mode 3 with the exact gaps. A new problem → Step 4 for it alone. Then `done adoption` (it needs a `## Révisions` line dated after the loop) and back to `interview`.

## Output

```
## Adoption
- <n> processus, dont <p> partiels et <c> cassés — `kb/existant/inventaire.md`
- <f> points forts ; <b> problèmes : <x> à corriger, <y> plus tard, <z> acceptés — `kb/existant/diagnostic.md`
- Documentation : <n> fichiers repris dans <cibles> ; <e> écarts au code
- Audits : <chemins>

## Suite
`interview`, lancé sans attendre.
```
