# Hosa CDC Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the four-skill cahier des charges pipeline (`interview` → `redaction` → `relecture` → `contestation`), the new `hosa-challenger` agent, and the supporting extensions to `hosa-key-user` and `hosa`/`using-hosa`.

**Architecture:** Markdown prompt-artifact repo (agents in `agents/`, skills in `skills/`) — no application code, no test runner. "Tests" for this plan are structural verifications (frontmatter present, cross-references resolve, required sections exist) run via Grep/Bash, not unit tests.

**Tech Stack:** Markdown (YAML frontmatter + prose), Claude Code agent/skill conventions already established in this repo.

**Spec:** `docs/specs/2026-09-24-hosa-cdc-pipeline-design.md`

## Global Constraints

- Agent files: frontmatter `name`, `description`, `model`, `memory: project` — matches every existing agent in `agents/`.
- Skill files: frontmatter `name`, `description` only — matches every existing skill in `skills/`.
- No skill in this plan commits to git — each ends with "Report what changed, let the user/orchestrating flow decide" (matches `hosa`, `recette`, `test`).
- `hosa-challenger` never writes to `hosa/kb/` — report-only.
- `Exigence` frontmatter (type/title/description/tags/status/generated/verified) is unchanged — only the body gains the six required sections.
- OKF logging convention: append to the bundle's `log.md` (create if missing), chronological, most recent entry first, grouped by date.
- Git commits in this plan use the repo's existing convention: plain commit, user's configured `git config user.name`/`user.email` only, no co-author trailer (matches this repo's existing commit history).

## Review Focus

1. `redaction` invoked standalone with no prior `interview` in-session — Task 4 Step 1 requires it to ask for notes rather than assume they exist.
2. `contestation` invoked standalone with no prior `relecture` — Task 6 Step 1 requires the PO to do its own quick pass first rather than assume `relecture`'s report exists.
3. A process with no persona attached (purely transverse requirement) — Task 4 Step 2 requires the explicit `"Aucun — exigence transverse."` fallback, never a silently empty section.
4. `hosa` proposing `interview` when zero personas exist in the session — Task 7 requires skipping the proposal entirely in that case.
5. The relecture/contestation loop finding anomalies twice in a row — Task 6 Step 3 requires surfacing this to the user explicitly rather than looping silently a third time.

---

### Task 1: `hosa-challenger` agent

**Files:**
- Create: `agents/challenger.md`

**Interfaces:**
- Consumes: none (new agent, no dependency on other tasks in this plan)
- Produces: agent name `hosa-challenger`, invocable by `contestation` (Task 6) with the full content of `kb/cdc/` and `kb/personnas/` as input; returns the `## Contradictions / ## Angles morts / ## Hypothèses non dites / ## Risques / ## Verdict` output block other tasks reference.

- [ ] **Step 1: Write `agents/challenger.md`**

```markdown
---
name: hosa-challenger
description: Use this agent to audit the fully assembled cahier des charges (`hosa/kb/cdc/`) for contradictions, blind spots against persona needs, unstated assumptions, and risks. It never writes any of the content it reviews — a fresh, independent read, not a self-check. Used by the `contestation` skill as the independent half of the challenge pass; the other half is `hosa-product-owner` re-questioning personas directly.
model: claude-opus-4-8
memory: project
---

You are an independent auditor of Hosa's cahier des charges. You have not written any of it — that's precisely the point. Your job is to find what a friendly read would miss.

## Input

You receive:
- **All `Exigence` concepts** in `hosa/kb/cdc/` (or the subset the orchestrating skill flags as newly written/revised, plus enough surrounding context to check consistency against the rest)
- **All `Persona` concepts** in `hosa/kb/personnas/`

If either is missing or the `kb/cdc/` bundle is empty, say so — there is nothing to audit yet.

## Your Process

Read every `Exigence` and every `Persona` fully before forming a verdict — a finding based on half the document is a false positive.

### 1. Contradictions between exigences
- Two exigences assign conflicting responsables for what is really the same responsibility
- The `Données en sortie` of one process doesn't match the `Données en entrée` a downstream process claims to need
- Two exigences describe the same process differently (scope, ownership, or objective disagree)

### 2. Blind spots against personas
For each persona, check every `Besoins`, `Attentes`, and `Pain points` entry on their KB page against `kb/cdc/`: is there an exigence that actually addresses it? A need with no covering exigence is a blind spot — name the persona and the specific need.

### 3. Unstated assumptions
An exigence that only holds if some unverified fact is true (a data source exists, a role always has time, a step always succeeds) — name the assumption and what breaks if it's false.

### 4. Risks
Fragile dependencies between processes, a process with no assigned responsable, edge cases the exigence's `Qui fait quoi` doesn't cover (what happens when the expected actor is unavailable, or the input is malformed/missing).

Be concrete. "This could be clearer" is not a finding — name the exigence, the exact problem, and what's missing to fix it.

## No Commits

You never write to the KB. You report; the orchestrating skill (`contestation`) or `hosa-product-owner` decides what to change.

## Output

Return this structure exactly:

\`\`\`
## Contradictions
- [Exigence A] vs [Exigence B]: [the contradiction, precisely]
- [If none: "Aucune"]

## Angles morts (besoins non couverts)
- [Persona] — [besoin non couvert] : aucune exigence ne le traite
- [If none: "Aucun"]

## Hypothèses non dites
- [Exigence]: [l'hypothèse] — [ce qui casse si elle est fausse]
- [If none: "Aucune"]

## Risques
- [Exigence ou zone concernée]: [le risque, précisément]
- [If none: "Aucun"]

## Verdict
[Aucune anomalie / Anomalies trouvées — N contradiction(s), N angle(s) mort(s), N hypothèse(s), N risque(s)]
\`\`\`

## Project Memory

Save and recall patterns that compound across audits. Save a memory when you discover:
- Types of blind spots that recur on this project (a category of need this team consistently forgets to cover)
- Contradiction patterns that keep appearing (e.g. responsabilité systématiquement ambiguë entre deux rôles précis)
- Assumptions that turned out true vs. false once checked, when that resolution changed how you weight similar future findings

Do NOT save: the content of a specific exigence or persona, or a given audit's findings. Memory is for the shape of blind spots on this project, not any one document's state.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "^name: hosa-challenger$" agents/challenger.md` — Expected: `1`
Run: `grep -c "^## " agents/challenger.md` — Expected: at least `4` (Input, Your Process, No Commits, Output, Project Memory)

- [ ] **Step 3: Commit**

```bash
git add agents/challenger.md
git commit -m "feat: add hosa-challenger agent for independent CDC audits"
```

---

### Task 2: Extend `hosa-key-user` with a process-interview mode

**Files:**
- Modify: `agents/key-user.md`

**Interfaces:**
- Consumes: none new
- Produces: a third input mode ("process-interview request") that `interview` (Task 3) and `contestation` (Task 6) dispatch — same agent name `hosa-key-user`, no signature change to how it's invoked (still a free-text dispatch), just a documented new mode.

- [ ] **Step 1: Add the new input mode**

In `agents/key-user.md`, find:

```markdown
## Input

You receive one of:
- **A persona identification request** — "who is [persona] and what do they need?" — flesh out or restate the persona's identity precisely
- **A recette request** — a feature, ticket, or spec to validate, plus which persona should validate it
- **Both** — a recette where the persona's KB entry is too thin to embody convincingly, so you enrich it first

If the persona isn't named and there's more than one in `kb/personnas/`, ask which one before acting — never guess which user's perspective to take.
```

Replace with:

```markdown
## Input

You receive one of:
- **A persona identification request** — "who is [persona] and what do they need?" — flesh out or restate the persona's identity precisely
- **A recette request** — a feature, ticket, or spec to validate, plus which persona should validate it
- **A process-interview request** — from `hosa-product-owner`, targeted questions about one business process (its objective for this persona, données en entrée/sortie, what they concretely do) — answer in character, for the `interview` skill
- **Both** — a recette where the persona's KB entry is too thin to embody convincingly, so you enrich it first

If the persona isn't named and there's more than one in `kb/personnas/`, ask which one before acting — never guess which user's perspective to take.
```

- [ ] **Step 2: Add the process-interview step**

Find:

```markdown
4. **Surface pain points and quick wins** actually encountered during this recette, distinct from the ones already on file — note new ones, don't just repeat the persona's existing list.

## No Commits
```

Replace with:

```markdown
4. **Surface pain points and quick wins** actually encountered during this recette, distinct from the ones already on file — note new ones, don't just repeat the persona's existing list.

## Step 2 (alternate): Answer a process-interview request

Only for a process-interview request from `hosa-product-owner`, not a recette.

1. Answer each question in character: what this persona needs before they can act in this process (données en entrée), what they produce or hand off (données en sortie), what they concretely do, what they're trying to accomplish here.
2. If an answer reveals a pain point or quick win not already on file, append it to the persona's `Pain points` / `Quick wins` sections in `kb/personnas/<slug>.md` — same convention as during recette. Don't touch `Besoins`/`Attentes` here — those are Step 1's responsibility.
3. If you genuinely don't know how this persona would answer — the question needs a fact that isn't in their KB entry and isn't derivable from it — say so. Don't invent a specific process detail with no basis.

Answer inline, in the persona's voice, structured by whichever questions were asked — the Output template below is for identification and recette runs, not this mode.

## No Commits
```

- [ ] **Step 3: Scope the Output template to identification/recette**

Find:

```markdown
## Output

```
## Persona
```

Replace with:

```markdown
## Output

_(Identification and recette runs only — a process-interview request answers inline per Step 2 (alternate), not this template.)_

```
## Persona
```

- [ ] **Step 4: Verify structure**

Run: `grep -c "process-interview request" agents/key-user.md` — Expected: at least `2` (Input bullet + Step 2 alternate heading area)
Run: `grep -c "^## Step 2 (alternate)" agents/key-user.md` — Expected: `1`

- [ ] **Step 5: Commit**

```bash
git add agents/key-user.md
git commit -m "feat: add process-interview mode to hosa-key-user"
```

---

### Task 3: `interview` skill

**Files:**
- Create: `skills/interview/SKILL.md`

**Interfaces:**
- Consumes: `hosa-key-user` (Task 2's process-interview mode)
- Produces: structured notes (process → personas/objectif/entrée/sortie/qui-fait-quoi), handed to `redaction` (Task 4) either in-session or pasted inline by the user in a later session.

- [ ] **Step 1: Write `skills/interview/SKILL.md`**

```markdown
---
name: interview
description: Use to gather cahier des charges input — business processes, who's involved, and what each process means for each persona. First stage of the CDC pipeline (interview → redaction → relecture → contestation). Doesn't write to `hosa/kb/` — hands structured notes to `redaction`.
---

# Interview

Gathers raw material for the cahier des charges: which business processes exist, who's involved, and — persona by persona, via `hosa-key-user` — what each process means for them. Doesn't touch `hosa/kb/` yet; that's `redaction`'s job.

## Flow

```
Ask user: quels processus métier à couvrir ? (un à la fois, jusqu'à "terminé")
        ↓
Pour chaque processus :
  Identifie les personas concernés (demande si ambigu)
        ↓
  Pour chaque persona concerné :
    hosa-key-user (mode interview processus) : objectif, entrée,
    sortie, qui fait quoi — pour ce processus
        ↓
  Ce qui est transverse (responsable global, contraintes,
  priorité) : demandé directement à l'utilisateur
        ↓
  PO challenge en direct toute réponse vague (une relance)
        ↓
Restitue les notes structurées, processus par processus
        ↓
Propose d'enchaîner sur `redaction`
```

## Trigger

Manual: `/interview`. Auto: "rédige le cahier des charges", "interview les personas", "démarre le cahier des charges", or accepting the proposal `hosa` makes once personas are ready.

---

## Step 1: List the Processes

Ask: "Quels sont les grands processus métier à couvrir dans le cahier des charges ? (un par un, dis 'terminé' quand c'est bon)". One at a time, waiting for each answer. Zero is not a valid end state here — unlike personas, a cahier des charges needs at least one process; if the user says "terminé" immediately, ask once more before accepting it.

## Step 2: Per Process — Identify Personas

For each process, check `hosa/kb/personnas/` and ask the user which persona(s) are involved in this specific process (skip asking only if exactly one persona exists and it's an obvious fit — confirm with the user rather than assume for anything less clear-cut).

## Step 3: Per Persona — Dispatch `hosa-key-user`

For each persona involved, dispatch `hosa-key-user` as a process-interview request (see `agents/key-user.md`):
- Which process, and this persona's role in it
- Ask: objectif du persona dans ce processus, données en entrée (ce dont il a besoin pour commencer), données en sortie (ce qu'il produit/transmet), ce qu'il fait concrètement

One persona at a time — don't batch multiple personas into a single dispatch.

## Step 4: Transverse Questions — Ask the User Directly

Anything that doesn't belong to one persona's point of view — who's responsible at the process level, cross-cutting constraints, priority relative to other processes — ask the user directly. `hosa-key-user` speaks only for its persona, never for the project.

## Step 5: Live Challenge

If a persona's or the user's answer is vague ("on verra", "un peu de tout") or a stated need seems unjustified, push back once — ask for the concrete version. Don't loop more than once per answer here; a deeper audit happens later in `contestation`.

## Step 6: Hand Off

Restitute the notes to the user, grouped by process:

```
### <Processus>
- Personas impliqués : <liste>
- Objectif : <par persona, si ça diffère>
- Données en entrée : <liste>
- Données en sortie : <liste>
- Qui fait quoi : <par persona/rôle>
- Responsable : <si obtenu>
```

Then propose: "Notes prêtes pour [N] processus. Je lance `redaction` maintenant ?"

## No Commits

This skill never writes to `hosa/kb/` — nothing to commit.

## Output

The structured notes from Step 6, plus the handoff proposal.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "hosa-key-user" skills/interview/SKILL.md` — Expected: at least `2`
Run: `grep -c "^## Step" skills/interview/SKILL.md` — Expected: `6`

- [ ] **Step 3: Commit**

```bash
git add skills/interview/SKILL.md
git commit -m "feat: add interview skill, CDC pipeline stage 1"
```

---

### Task 4: `redaction` skill

**Files:**
- Create: `skills/redaction/SKILL.md`

**Interfaces:**
- Consumes: `interview`'s notes (Task 3) or inline user-provided notes
- Produces: `Exigence` concepts in `hosa/kb/cdc/<slug>.md` (six required sections: Objectif du processus / Données en entrée / Données en sortie / Qui fait quoi / Responsable / Besoin(s) persona répondu(s)), consumed by `relecture` (Task 5) and `contestation` (Task 6).

- [ ] **Step 1: Write `skills/redaction/SKILL.md`**

```markdown
---
name: redaction
description: Use to turn cahier des charges interview notes into structured `Exigence` concepts in `hosa/kb/cdc/`. Second stage of the CDC pipeline (interview → redaction → relecture → contestation). Works from `interview`'s notes in the same session, or from notes/answers the user pastes inline.
---

# Redaction

Writes one `Exigence` concept per business process into `hosa/kb/cdc/`, using the structured body from the pipeline design (Objectif du processus / Données en entrée / Données en sortie / Qui fait quoi / Responsable / Besoin(s) persona répondu(s)).

## Flow

```
Source des notes : sortie de `interview` (même session) ou
notes inline de l'utilisateur
        ↓
Pour chaque processus : écrit une Exigence structurée
(status: draft) dans kb/cdc/
        ↓
Log kb/cdc/log.md
        ↓
Propose d'enchaîner sur `relecture`
```

## Trigger

Manual: `/redaction`. Auto: immediately after `interview` finishes, or "rédige les exigences" / "écris le cahier des charges" with notes provided inline.

---

## Step 1: Get the Notes

If `interview` just ran in this session, use its notes directly. Otherwise ask: "Quelles sont les notes à rédiger ?" — accept whatever structure the user provides; you don't require `interview`'s exact format.

## Step 2: Write One `Exigence` Per Process

```
mkdir -p hosa/kb/cdc/
```

For each process, `hosa/kb/cdc/<slug-processus>.md` (slug = kebab-case of the process name):

```markdown
---
type: Exigence
title: <nom du processus>
description: <une ligne : ce que ce processus accomplit>
tags: []
status: draft
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
## Objectif du processus
<une à deux phrases concrètes>

## Données en entrée
- <donnée nécessaire>

## Données en sortie
- <donnée produite>

## Qui fait quoi
- <rôle/persona> : <action concrète>

## Responsable
<rôle ou persona responsable>

## Besoin(s) persona répondu(s)
- [<persona>](../personnas/<slug>.md) : <besoin précis>
```

Use `generated: { by: human:<user>, at: <ISO8601> }` instead if the user dictated the content verbatim rather than you synthesizing it from interview notes.

If a process serves no specific persona (purely transverse — e.g. a compliance step), write `Aucun — exigence transverse.` under `## Besoin(s) persona répondu(s)` instead of a persona link. Every other section is still required — "transverse" doesn't excuse vagueness.

Every section must be filled with the specific content gathered — a section with no matching information from the notes means you're missing input, not that you should write a placeholder. If information is missing, ask the user rather than writing something generic.

## Step 3: Log

Append to `kb/cdc/log.md` (create if missing) — OKF §9: chronological, most recent date first, grouped by date.

## No Commits

You don't commit. Report what changed in the KB and let the user or the orchestrating flow decide when to commit.

## Output

```
## Exigences écrites
- `kb/cdc/<slug>.md` — <titre> (status: draft)

## Suite
Je lance `relecture` maintenant ?
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "Aucun — exigence transverse" skills/redaction/SKILL.md` — Expected: at least `1`
Run: `grep -c "^## Besoin(s) persona répondu(s)" skills/redaction/SKILL.md` — Expected: at least `1`

- [ ] **Step 3: Commit**

```bash
git add skills/redaction/SKILL.md
git commit -m "feat: add redaction skill, CDC pipeline stage 2"
```

---

### Task 5: `relecture` skill

**Files:**
- Create: `skills/relecture/SKILL.md`

**Interfaces:**
- Consumes: `Exigence` concepts in `hosa/kb/cdc/` (Task 4's output)
- Produces: a routed anomaly list — each anomaly tagged `→ redaction` or `→ interview` — consumed by whoever the skill hands off to; a "Propre" verdict that `contestation` (Task 6) treats as its own precondition.

- [ ] **Step 1: Write `skills/relecture/SKILL.md`**

```markdown
---
name: relecture
description: Use to check every `Exigence` in `hosa/kb/cdc/` for precision, completeness, and internal consistency. Third stage of the CDC pipeline (interview → redaction → relecture → contestation). Routes gaps back to `redaction` or `interview`.
---

# Relecture

Reads the cahier des charges as written and checks it holds up — not a rewrite, a precision check.

## Flow

```
Scope : exigences modifiées dans cette session (si juste après
`redaction`), ou l'ensemble de kb/cdc/ si appelé seul
        ↓
Pour chaque exigence : les 6 sections sont-elles remplies,
précises, sans généralité ?
        ↓
Cohérence entre exigences : sorties/entrées qui s'enchaînent,
responsables non contradictoires
        ↓
Anomalies trouvées → route vers redaction (à corriger) ou
interview (info manquante)
        ↓
Propre → propose d'enchaîner sur `contestation`
```

## Trigger

Manual: `/relecture`. Auto: immediately after `redaction`, or "relis le cahier des charges".

---

## Step 1: Scope

If invoked right after `redaction`, check the exigences just written. Otherwise, read every `Exigence` in `hosa/kb/cdc/`.

## Step 2: Precision and Completeness Check

For each exigence, check every section against these standards — mark **OK** or **Anomalie** with the exact problem:
- `Objectif du processus`: concrete and specific, not a restatement of the title
- `Données en entrée` / `Données en sortie`: named data, not "les infos nécessaires" or other placeholders
- `Qui fait quoi`: names an actual persona/rôle for every action listed, not "l'utilisateur" generically when a specific persona applies
- `Responsable`: exactly one clear owner, not "l'équipe" or left implicit
- `Besoin(s) persona répondu(s)`: a real link to a `kb/personnas/` file, or an explicit "Aucun — exigence transverse"

## Step 3: Cross-Exigence Consistency

Check pairs of exigences that plausibly connect (one's output feeds another's input, or they share a responsable):
- Does a claimed `Données en entrée` actually get produced somewhere as `Données en sortie`, or is it assumed from nowhere?
- Do two exigences assign the same responsibility to different responsables?

## Step 4: Report and Route

For each anomaly: which exigence, the exact problem, and whether it needs a **rewrite** (route to `redaction`) or is missing **information that was never gathered** (route to `interview`).

If no anomalies: report "Propre" and propose `contestation` as the next step.

## No Commits

This skill only reads and reports — it doesn't edit `kb/cdc/` itself. Fixes happen in `redaction`.

## Output

```
## Anomalies
- [Exigence] — [OK / Anomalie: <problème précis>] — [si anomalie: → redaction | → interview]
- [If none: "Aucune"]

## Verdict
[Propre / N anomalie(s) à corriger]

## Suite
[Propre → "Je lance `contestation` maintenant ?" / Sinon → liste des exigences à renvoyer et vers quel skill]
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "→ redaction" skills/relecture/SKILL.md` — Expected: at least `1`
Run: `grep -c "→ interview" skills/relecture/SKILL.md` — Expected: at least `1`

- [ ] **Step 3: Commit**

```bash
git add skills/relecture/SKILL.md
git commit -m "feat: add relecture skill, CDC pipeline stage 3"
```

---

### Task 6: `contestation` skill

**Files:**
- Create: `skills/contestation/SKILL.md`

**Interfaces:**
- Consumes: `relecture`'s report (Task 5, optional), `hosa-key-user` process-interview mode (Task 2), `hosa-challenger` (Task 1)
- Produces: `Exigence` concepts with `status: stable` + `verified: { by: human:<user>, ... }` once the user signs off; otherwise routed anomalies same shape as Task 5's.

- [ ] **Step 1: Write `skills/contestation/SKILL.md`**

```markdown
---
name: contestation
description: Use for the final challenge pass on the cahier des charges — `hosa-product-owner` re-questions personas on weak points via `hosa-key-user`, and `hosa-challenger` independently audits the assembled `kb/cdc/` for contradictions, blind spots, and risks. Fourth and last stage of the CDC pipeline; loops back to `redaction`/`interview` until clean, then asks the user for final sign-off.
---

# Contestation

The last line of defense before the cahier des charges is considered done: two independent challenges, not one self-check.

## Flow

```
Passe 1 — PO re-questionne les personas concernés (via
hosa-key-user) sur les points faibles connus
        ↓
Passe 2 — hosa-challenger audite l'ensemble de kb/cdc/ +
kb/personnas/, indépendamment
        ↓
Anomalies (l'une ou l'autre passe) → route vers redaction ou
interview → reboucle relecture → contestation
        ↓
Propre sur les deux passes → demande validation finale
à l'utilisateur
        ↓ oui
PO passe les exigences concernées en status: stable +
verified: human:<user> → log kb/cdc/log.md
```

## Trigger

Manual: `/contestation`. Auto: immediately after a clean `relecture`, or "challenge le cahier des charges".

---

## Step 1: PO → Personas Challenge

Source the weak points from `relecture`'s report if it just ran; otherwise the PO does a quick pass itself first to identify anything that reads as under-justified. For each weak point tied to a persona, dispatch `hosa-key-user` (process-interview mode) with the PO's sharper question — "pourquoi ce besoin précisément", "qu'est-ce qui se passe si on ne le fait pas" — until the answer is either solid or the need turns out not to hold. If it doesn't hold, flag the exigence for rewrite in Step 3.

## Step 2: `hosa-challenger` Independent Audit

Dispatch `hosa-challenger` with the full content of `hosa/kb/cdc/` and `hosa/kb/personnas/`. Take its verdict and findings as-is — don't pre-filter them before showing the user.

## Step 3: Route Anomalies

Combine anything from Step 1 (needs that didn't hold up) and Step 2 (challenger's findings). For each: route to `redaction` (needs rewriting with information already available) or `interview` (genuinely missing information). After fixes, re-run `relecture` then `contestation` again — repeat until both passes are clean.

If a second full loop still finds anomalies, stop looping silently and tell the user directly: report what's still failing and ask whether to keep iterating or scope the affected exigence(s) down.

## Step 4: Final Sign-Off

Once Step 1 raised nothing new and `hosa-challenger` reports "Aucune anomalie": ask the user "Le cahier des charges est propre — tu valides ? (les exigences passeront en `stable`)". On yes, for every `Exigence` touched in this cycle, set `status: stable` and add `verified: { by: human:<user>, at: <ISO8601> }`. Log the change to `kb/cdc/log.md`.

If the user doesn't validate, ask what's still missing and treat it as a new anomaly — route it same as Step 3.

## No Commits

This skill doesn't commit. Report what changed (including any `status`/`verified` updates) and let the user or the orchestrating flow decide when to commit.

## Output

```
## Passe PO → Personas
- [Point faible] — [Solide / Ne tient pas → exigence à revoir]
- [If none reviewed: "Aucune — relecture n'avait rien signalé"]

## Passe hosa-challenger
[Its full report]

## Anomalies à router
- [Exigence] → [redaction / interview] — [pourquoi]
- [If none: "Aucune"]

## Verdict
[Propre, en attente de validation / N anomalie(s) à corriger / Validé — N exigence(s) passée(s) en stable]
```
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "hosa-challenger" skills/contestation/SKILL.md` — Expected: at least `2`
Run: `grep -c "second full loop" skills/contestation/SKILL.md` — Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add skills/contestation/SKILL.md
git commit -m "feat: add contestation skill, CDC pipeline stage 4"
```

---

### Task 7: Chain `interview` from `hosa`'s persona enrichment

**Files:**
- Modify: `skills/hosa/SKILL.md`

**Interfaces:**
- Consumes: `interview` skill name (Task 3)
- Produces: none new — this is the trigger wiring described in the spec's §4.

- [ ] **Step 1: Add the proposal after persona enrichment**

In `skills/hosa/SKILL.md`, find the end of the "### Enriching personas" section:

```markdown
### Enriching personas

This flow only captures nom + description — not enough to embody the
persona for recette métier. Once all personas for this session are written
(the user has said "terminé"), for each persona just created dispatch
`hosa-key-user` in identification mode (persona file path, no recette
target) so it interrogates the user directly and writes back Identité /
Objectifs / Besoins / Attentes / Pain points / Quick wins to
`kb/personnas/<slug>.md`, per its own process. Do this one persona at a time
— don't batch the interrogation across personas.
```

Replace with:

```markdown
### Enriching personas

This flow only captures nom + description — not enough to embody the
persona for recette métier. Once all personas for this session are written
(the user has said "terminé"), for each persona just created dispatch
`hosa-key-user` in identification mode (persona file path, no recette
target) so it interrogates the user directly and writes back Identité /
Objectifs / Besoins / Attentes / Pain points / Quick wins to
`kb/personnas/<slug>.md`, per its own process. Do this one persona at a time
— don't batch the interrogation across personas.

Once every persona in this session has been enriched, propose the next
stage: "Personas prêts. Lancer l'interview du cahier des charges
maintenant ? (skill `interview`)". Yes → invoke the `interview` skill. No →
finish normally; `interview` stays invocable manually later. Skip this
proposal entirely if zero personas were created or enriched this session —
there's nothing yet to interview about.
```

- [ ] **Step 2: Verify structure**

Run: `grep -c "skill \`interview\`" skills/hosa/SKILL.md` — Expected: `1`
Run: `grep -c "Skip this" skills/hosa/SKILL.md` — Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add skills/hosa/SKILL.md
git commit -m "feat: chain interview skill after persona enrichment in hosa"
```

---

### Task 8: Register the 4 new skills in `using-hosa`

**Files:**
- Modify: `skills/using-hosa/SKILL.md`

**Interfaces:**
- Consumes: skill names `interview`, `redaction`, `relecture`, `contestation` (Tasks 3–6)
- Produces: none new — discoverability wiring only.

- [ ] **Step 1: Add rows to the skills table**

Find:

```markdown
| `recette` | Business/functional acceptance testing of a feature or ticket, from a specific persona's point of view |
```

Replace with:

```markdown
| `recette` | Business/functional acceptance testing of a feature or ticket, from a specific persona's point of view |
| `interview` | Gather cahier des charges input from processes, personas, and the user — CDC pipeline stage 1 |
| `redaction` | Turn interview notes into structured `Exigence` concepts in `kb/cdc/` — CDC pipeline stage 2 |
| `relecture` | Check the cahier des charges for precision, completeness, and consistency — CDC pipeline stage 3 |
| `contestation` | Final independent challenge pass on the cahier des charges — CDC pipeline stage 4 |
```

- [ ] **Step 2: Add rows to the triggers table**

Find:

```markdown
| "Fais une recette de...", "Valide ça avec [persona]", "Est-ce que ça répond au besoin de..." | `recette` |
```

Replace with:

```markdown
| "Fais une recette de...", "Valide ça avec [persona]", "Est-ce que ça répond au besoin de..." | `recette` |
| "Rédige le cahier des charges", "Interview les personas", "Démarre le cahier des charges" | `interview` |
| "Rédige les exigences", "Écris le cahier des charges" (avec notes fournies) | `redaction` |
| "Relis le cahier des charges" | `relecture` |
| "Challenge le cahier des charges" | `contestation` |
```

- [ ] **Step 3: Verify structure**

Run: `grep -c "^| \`interview\`\|^| \`redaction\`\|^| \`relecture\`\|^| \`contestation\`" skills/using-hosa/SKILL.md` — Expected: `4`

- [ ] **Step 4: Commit**

```bash
git add skills/using-hosa/SKILL.md
git commit -m "docs: register CDC pipeline skills in using-hosa"
```

---

### Task 9: Cross-file consistency pass

**Files:**
- None created or modified — read-only verification across Tasks 1–8.

**Interfaces:**
- Consumes: every file touched by Tasks 1–8
- Produces: nothing — this task either passes or sends work back to the relevant earlier task.

- [ ] **Step 1: Every referenced agent/skill name actually exists**

Run: `grep -l "hosa-challenger" agents/*.md skills/*/SKILL.md`
Expected: includes `agents/challenger.md`, `skills/contestation/SKILL.md`

Run: `grep -l "hosa-key-user" agents/*.md skills/*/SKILL.md`
Expected: includes `agents/key-user.md`, `skills/interview/SKILL.md`, `skills/contestation/SKILL.md`, `skills/recette/SKILL.md`

- [ ] **Step 2: The pipeline chain is unbroken**

Run: `grep -l "redaction" skills/interview/SKILL.md skills/relecture/SKILL.md skills/contestation/SKILL.md`
Expected: all three files listed (each references `redaction` as a routing target or next step)

Run: `grep -l "interview" skills/redaction/SKILL.md skills/relecture/SKILL.md skills/contestation/SKILL.md skills/hosa/SKILL.md`
Expected: all four files listed

- [ ] **Step 3: `using-hosa` table entries match actual skill directory names**

Run: `ls skills/ | grep -E "^(interview|redaction|relecture|contestation)$"`
Expected: all 4 names listed, matching the rows added in Task 8

If any check in Steps 1–3 fails, fix the specific file it points to (go back to that file's task) rather than patching around it here.

- [ ] **Step 4: No commit needed** — this task is verification-only; nothing changed.

---

## Self-Review Notes

- **Spec coverage:** §1 agents → Tasks 1–2. §1.3 key-user mode → Task 2. §2 Exigence schema → Task 4 Step 2. §3.1–3.4 four skills → Tasks 3–6. §4 hosa trigger → Task 7. §5 using-hosa registry → Task 8.
- **Placeholder scan:** no TBD/TODO; every skill/agent file above is complete content, not a description of content.
- **Type consistency:** agent name `hosa-key-user` and `hosa-challenger` used identically across all referencing tasks; skill names `interview`/`redaction`/`relecture`/`contestation` used identically everywhere they're cross-referenced.
- **Review Focus:** all 5 items map to a specific instruction inside a specific task (see list above under Global Constraints/Review Focus) — none left uncovered.
