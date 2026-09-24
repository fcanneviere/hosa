---
name: donnees
description: Use to annotate the origin (générée/fournie/saisie) of each donnée listed under `Données en entrée`/`Données en sortie` in stable `kb/cdc/` Exigences. First stage of the data-structuring pipeline (donnees → schema-app → schema-db), runs after `contestation` has made the CDC stable.
---

# Données

Qualifies where each piece of data in the cahier des charges actually comes from — a prerequisite before any real data structure can be derived from it.

## Flow

```
Pour chaque Exigence stable de kb/cdc/ (ou celles touchées
dans cette session si enchaîné depuis contestation) :
        ↓
Pour chaque item de Données en entrée/sortie déjà annoté : passe
        ↓
Pour chaque item non annoté ou ambigu :
  dépend d'un persona ? → hosa-key-user (mode interview processus)
  purement technique ?  → demande à l'utilisateur
        ↓
Écrit l'annotation en place, préserve le reste du contenu
        ↓
Log kb/cdc/log.md
        ↓
Propose d'enchaîner sur `schema-app`
```

## Trigger

Manual: `/donnees`. Auto: immediately after a clean `contestation` sign-off, or "précise les données du cahier des charges", "qualifie l'origine des données".

---

## Step 1: Scope

If invoked right after `contestation`, work on the `Exigence`s that just moved to `stable` in this session. Otherwise, read every `stable` `Exigence` in `kb/cdc/`. Skip anything still `draft` — data qualification works from a settled cahier des charges, not one still being contested. If there are no `stable` Exigences at all, say so and stop.

## Step 2: Per Item — Qualify Origin

For each item under `Données en entrée`/`Données en sortie`:
- Already annotated (`— origine : ...`) → skip.
- Origin depends on a persona's point of view (who enters it, who hands it off) → dispatch `hosa-key-user` in process-interview mode (`agents/key-user.md`) with the exigence's process and the specific item: does this persona enter it (saisie), receive it from elsewhere (fournie), or does the process generate it (générée)?
- Purely technical, no persona involved (e.g. a system timestamp, a computed total) → ask the user directly, never force a `hosa-key-user` dispatch for data no persona owns.

One item at a time — don't batch multiple ambiguous items into a single question.

## Step 3: Write the Annotation

In place, preserving every other line of the `Exigence`:

```markdown
- <donnée> — origine : générée | fournie | saisie (par <persona ou système>)
```

`générée` and `fournie` name the system/process or the external source in the parenthesis; `saisie` names the persona.

## Step 4: Log

Append to `kb/cdc/log.md` (create if missing) — OKF §9: chronological, most recent date first, grouped by date.

## No Commits

You don't commit. Report what changed in the KB and let the user or the orchestrating flow decide when to commit.

## Output

```
## Exigences qualifiées
- `kb/cdc/<slug>.md` — <n> items annotés

## Suite
Je lance `schema-app` maintenant ?
```
