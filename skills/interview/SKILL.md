---
name: interview
description: "Use to gather the cahier des charges: business processes, who does what, what each means for each persona; writes a Compte Rendu. CDC stage 1. Triggers: \"rédige le cahier des charges\", \"interview les personas\"."
---

# Interview

Gathers raw material for the cahier des charges: which business processes exist, who's involved, and — persona by persona, via `hosa-key-user` — what each process means for them. Writes no `Exigence` itself; that's `redaction`'s job. It does write a `Compte Rendu` of the session itself — the raw notes, before `redaction` turns them into structured `Exigence` concepts — so "qui a demandé X, et quand" stays answerable even after an `Exigence` is edited later. `hosa-key-user` may still append newly surfaced Pain points/Quick wins to a persona's own KB entry during the process-interview dispatch (same convention as during a recette) — report any such change and its log entry, don't treat it as silent.

## Flow

```
Propose les processus métier déduits de l'identité + personas
→ l'utilisateur confirme/ajuste (rien à déduire → demande un à un)
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
Écrit le compte-rendu dans kb/cdc/interviews/
        ↓
Restitue les notes structurées, processus par processus
        ↓
Propose d'enchaîner sur `redaction`
```

## Trigger

Manual: `/interview`. Auto: "rédige le cahier des charges", "interview les personas", "démarre le cahier des charges", or accepting the proposal `hosa` makes once personas are ready.

---

## Step 0: Personas First

A cahier des charges is told from its personas' point of view. No persona in `kb/personnas/` other than the example → stop, say so, and propose `hosa` to create at least one (numbered question).

## How Questions Are Asked

- **Look it up before asking.** What the KB already answers (identity, personas, an earlier compte rendu, a brief) is read, not asked.
- **One question at a time, numbered, with a recommended answer** — "Q1. <question> — je propose : <réponse> (recommandé), parce que <raison>". A recommendation turns an open question into a quick check.
- **Walk the decision tree.** Settle a decision before the ones that depend on it (who validates an order comes before what happens when they refuse it).
- **Pin the vocabulary.** When the user and a persona name the same thing differently ("commande" / "panier"), or a word is ambiguous, ask once which term the project uses and what it means — it goes to the glossary `redaction` keeps.

## Step 1: List the Processes

Read `kb/project/identity.md` and `kb/personnas/`, and derive candidate processes — each a concrete activity a persona carries out end to end ("préparer la liste", "faire les courses"), not a feature. Propose them: "Voici les processus métier que je déduis du projet et des personas : [liste]. Tu confirmes, tu en retires, ou tu en ajoutes ?" Adjust until the user confirms. Nothing to derive from → ask: "Quels sont les grands processus métier à couvrir ? (un par un, dis 'terminé' quand c'est bon)", one at a time. Zero is not a valid end state here — unlike personas, a cahier des charges needs at least one process; if the user says "terminé" immediately, ask once more before accepting it.

## Step 2: Per Process — Identify Personas

For each process, check `.hosa/kb/personnas/` and ask the user which persona(s) are involved in this specific process (skip asking only if exactly one persona exists and it's an obvious fit — confirm with the user rather than assume for anything less clear-cut).

## Step 3: Per Persona — Dispatch `hosa-key-user`

For each persona involved, dispatch `hosa-key-user` as a process-interview request (see `agents/key-user.md`):
- Which process, and this persona's role in it
- Ask: objectif du persona dans ce processus, données en entrée (ce dont il a besoin pour commencer), données en sortie (ce qu'il produit/transmet), ce qu'il fait concrètement, les **règles de gestion** qu'il applique (calculs, conditions, seuils, statuts et qui fait passer de l'un à l'autre), et les **cas d'erreur** (donnée manquante ou fausse, doublon, retard, refus) avec ce qui doit se passer alors — avec des exemples chiffrés réels

One persona at a time — don't batch multiple personas into a single dispatch.

## Step 4: Transverse Questions — Ask the User Directly

Anything that doesn't belong to one persona's point of view — who's responsible at the process level, cross-cutting constraints, priority relative to other processes — ask the user directly. `hosa-key-user` speaks only for its persona, never for the project.

## Step 5: Live Challenge

If a persona's or the user's answer is vague ("on verra", "un peu de tout") or a stated need seems unjustified, push back once — ask for the concrete version. Don't loop more than once per answer here; a deeper audit happens later in `contestation`.

## Step 6: Write the Compte Rendu

```
mkdir -p .hosa/kb/cdc/interviews/
```

Write `.hosa/kb/cdc/interviews/<ISO-date>-interview.md` (one file per interview session, even if it covers several processes):

```markdown
---
type: Compte Rendu
title: Interview cahier des charges — <date>
description: <une ligne : processus couverts>
tags: [interview]
status: stable
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
### <Processus>
- Personas impliqués : <liste>
- Objectif : <par persona, si ça diffère>
- Données en entrée : <liste>
- Données en sortie : <liste>
- Qui fait quoi : <par persona/rôle>
- Règles de gestion : <calculs, conditions, statuts, avec exemples>
- Cas d'erreur : <ce qui peut mal se passer, et la réaction attendue>
- Responsable : <si obtenu>
```

One `### <Processus>` section per process covered this session. Use `generated: { by: human:<user>, at: <ISO8601> }` instead if the user dictated the content verbatim rather than you synthesizing it from the exchange. This is the raw record — write it as gathered, don't retroactively clean it up to match what `redaction` later produces. Append an entry to `kb/cdc/interviews/log.md` (create if missing) — OKF §9: chronological, most recent date first, grouped by date.

## Step 7: Hand Off

Restitute the same notes to the user, grouped by process (same structure as the compte rendu above), then propose: "Notes prêtes pour [N] processus.

Suite : `redaction`, lancé sans attendre."

## No Commits

This skill writes the `Compte Rendu` but never commits it — same as every other pipeline skill, the user or `kb-commit` decides when. It never writes `Exigence` concepts; that's `redaction`'s job. Any persona Pain points/Quick wins that `hosa-key-user` appended during a process-interview dispatch are already written to `kb/personnas/<slug>.md` and logged to `kb/personnas/log.md` by that agent — report them in the handoff, but they aren't this skill's commit to make either.

## Output

```
## Compte rendu écrit
- `kb/cdc/interviews/<date>-interview.md` — [N] processus

## Notes
[Structured notes from Step 7]

## Suite
Notes prêtes pour [N] processus. Je lance `redaction` maintenant ?
```
