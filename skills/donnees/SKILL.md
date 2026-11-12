---
name: donnees
description: "Use to qualify each data item's origin (générée/fournie/saisie) in stable exigences. Structuration stage 3. Triggers: \"qualifie l'origine des données\", after `infra`."
---

# Données

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start donnees`; refused → name the missing stage to the user and stop; refused as already done → a re-run only on the user's request: the same `start` with `--rouvre "<their request>"`. Stopped on a user question: `block donnees --detail "<question>"`. Once the stage's output is written and committed: `done donnees`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

**Tâches.** Before Step 3, `avancement.py task add donnees annotations --agent hosa-data-engineer`; on its return, `task done donnees annotations --sortie <the exigences it annotated>`. Phase 1 and the persona questions write nothing: no task. Stopped on an Open Question → `task block donnees annotations --detail "<la question>"`, and `task add` it again once answered.

Qualifies where each piece of data in the cahier des charges actually comes from — a prerequisite before any real data structure can be derived from it. This skill is the only one that talks to the user or dispatches other agents — the actual scoping and annotation is `hosa-data-engineer`'s.

## Flow

```
Dispatch hosa-data-engineer (Responsibility 1, Phase 1: scope +
surface ambiguous items)
        ↓ Open Questions (no stable Exigence) → relay to user, stop
        ↓ Personas à interviewer / Open Questions (ambiguous items)
Dispatch hosa-key-user (process-interview) pour chaque item
persona-dépendant ; demande à l'utilisateur pour chaque item
purement technique
        ↓
Redispatch hosa-data-engineer (Phase 2) avec toutes les
réponses → écrit les annotations
        ↓
Enchaîne sur `schema-app`
```

## Trigger

Manual: `/donnees`. Auto: immediately after `infra`, or "précise les données du cahier des charges", "qualifie l'origine des données".

---

## Step 1: Dispatch to Scope and Surface

Dispatch `hosa-data-engineer` with `model: sonnet` — qualifying origins is classification, not design (Responsibility 1 Phase 1, `agents/data-engineer.md`). It scopes to every `stable` `Exigence` in `kb/cdc/` whose data items carry no origin annotation yet — read from the KB, never from a session's memory: a re-run only fills the gaps.

If it returns an Open Question (no `stable` Exigence at all) — relay it to the user and stop.

## Step 2: Resolve Ambiguous Items

Items under `## Personas à interviewer` — one `hosa-key-user` dispatch per persona, in process-interview mode (`agents/key-user.md`), with all of that persona's items, each with its exigence's process: does this persona enter it (saisie), receive it from elsewhere (fournie), or does the process generate it (générée)? All the dispatches in one message: the personas are independent. An answer the agent marks `[à confirmer]` is its deduction: it goes to the user with the others below.

Items under `## Open Questions` (purely technical, no persona involved), and the personas' `[à confirmer]` answers — ask the user in one message, numbered, the proposed origin as option `a)`.

## Step 3: Dispatch to Record

Redispatch `hosa-data-engineer` with `model: sonnet` (Responsibility 1 Phase 2) with every answer collected in Step 2. It writes each annotation in place and logs to `kb/cdc/log.md`.

## No Commits

You don't commit. Report what changed. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa`, "Git checkpoints".

## Output

```
## Exigences qualifiées
- `kb/cdc/<slug>.md` — <n> items annotés : <donnée — origine>, une par item (les exigences sont signées : l'utilisateur voit ce qui leur est ajouté)

## Suite
Suite : `schema-app`, lancé sans attendre.
```
