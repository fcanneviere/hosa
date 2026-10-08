---
name: donnees
description: "Use to qualify each data item's origin (générée/fournie/saisie) in stable exigences. Structuration stage 3. Triggers: \"qualifie l'origine des données\", after `infra`."
---

# Données

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
Propose d'enchaîner sur `schema-app`
```

## Trigger

Manual: `/donnees`. Auto: immediately after `infra`, or "précise les données du cahier des charges", "qualifie l'origine des données".

---

## Step 1: Dispatch to Scope and Surface

Dispatch `hosa-data-engineer` with `model: sonnet` — qualifying origins is classification, not design (Responsibility 1 Phase 1, `agents/data-engineer.md`). If `contestation` validated one or more `Exigence`s to `stable` earlier in this same session (whether or not `stack` ran in between), tell it to scope to those; otherwise it scopes to every `stable` `Exigence` in `kb/cdc/`.

If it returns an Open Question (no `stable` Exigence at all) — relay it to the user and stop.

## Step 2: Resolve Ambiguous Items

For each item under `## Personas à interviewer` — dispatch `hosa-key-user` in process-interview mode (`agents/key-user.md`) with the exigence's process and the specific item: does this persona enter it (saisie), receive it from elsewhere (fournie), or does the process generate it (générée)? One item at a time — don't batch multiple ambiguous items into a single dispatch.

For each item under `## Open Questions` (purely technical, no persona involved) — ask the user directly, one item at a time.

## Step 3: Dispatch to Record

Redispatch `hosa-data-engineer` with `model: sonnet` (Responsibility 1 Phase 2) with every answer collected in Step 2. It writes each annotation in place and logs to `kb/cdc/log.md`.

## No Commits

You don't commit. Report what changed in the KB and let the user or the orchestrating flow decide when to commit.

## Output

```
## Exigences qualifiées
- `kb/cdc/<slug>.md` — <n> items annotés

## Suite
**Q1 — Je lance `schema-app` maintenant ?**
  a) Oui, maintenant. (recommandé)
  b) Non, on s'arrête là.
```
