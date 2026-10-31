---
name: interview
description: "Use to gather the cahier des charges: business processes, who does what, what each means for each persona; writes a Compte Rendu. CDC stage 1. Triggers: \"rédige le cahier des charges\", \"interview les personas\"."
---

# Interview

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Before anything: `avancement.py start interview`; refused → name the missing stage to the user and stop. Stopped on a user question: `block interview --detail "<question>"`. Once the stage's output is written and committed: `done interview`. Never skip these calls: without them a cut session can't resume (« reprends ») and the session stays on the wrong model.

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
- Ask: comment ça se passe aujourd'hui (outil, contournement, ce qui rate), ce qui déclenche le processus pour lui (un événement, une situation, la fin d'un autre processus), objectif du persona dans ce processus, données en entrée (ce dont il a besoin pour commencer), données en sortie (ce qu'il produit/transmet), ce qu'il fait concrètement, les **règles de gestion** qu'il applique (calculs, conditions, seuils, statuts et qui fait passer de l'un à l'autre), et les **cas d'erreur** (donnée manquante ou fausse, doublon, retard, refus) avec ce qui doit se passer alors — avec des exemples chiffrés réels

One persona at a time — don't batch multiple personas into a single dispatch.

## Step 4: Transverse Questions — Ask the User Directly

Anything that doesn't belong to one persona's point of view — who's responsible at the process level, cross-cutting constraints, priority relative to other processes — ask the user directly. `hosa-key-user` speaks only for its persona, never for the project.

Once every process is covered, ask the user, each as one numbered question with a proposed answer:
- **Objectives.** `kb/project/identity.md` § Objectifs mesurables has no row `| O1 | … |` with an indicator, a target and a measure → propose them from the personas' `Objectifs` (ex. : « zéro article oublié sur une liste »), to confirm or correct through `hosa`. Then which objectives each process serves.
- **Priority and lot.** One table for all processes: `indispensable` / `important` / `souhaitable`, and the lot (1 = the first release that reaches the objectives). Recommend: lot 1 = the shortest chain of processes from start to objective, everything else after.
- **Business objects.** For each object the processes create or change (a list, an order, an account): its states and what makes it change state, who may create, read, change and delete it, and who is told of each change (channel, moment). A state with no way out (« et après, que devient-il ? ») or a right nobody owns is the question to ask — this is where the forgotten processes are found.

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
description: "<une ligne : processus couverts>"
tags: [interview]
status: stable
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
### <Processus>
- Personas impliqués : <liste>
- Situation actuelle : <comment ça se passe aujourd'hui, ce qui rate>
- Déclencheur : <ce qui lance le processus>
- Priorité et lot : <indispensable | important | souhaitable>, lot <n> ; objectifs servis : <O1…>
- Objectif : <par persona, si ça diffère>
- Données en entrée : <liste>
- Données en sortie : <liste>
- Qui fait quoi : <par persona/rôle>
- Règles de gestion : <calculs, conditions, statuts, avec exemples>
- Cas d'erreur : <ce qui peut mal se passer, et la réaction attendue>
- Responsable : <si obtenu>

### Objets métier
- <Objet> — états : <a → b : qui ou quoi> ; droits : <rôle : créer / consulter / modifier / supprimer> ; prévenus : <événement → qui, canal, moment>

### Questions restées ouvertes
- <question> — proposé : <réponse>
```

One `### <Processus>` section per process covered this session. An open question goes to `redaction`, which records it in `kb/cdc/decisions.md`. Use `generated: { by: human:<user>, at: <ISO8601> }` instead if the user dictated the content verbatim rather than you synthesizing it from the exchange. This is the raw record — write it as gathered, don't retroactively clean it up to match what `redaction` later produces. Append an entry to `kb/cdc/interviews/log.md` (create if missing) — OKF §9: chronological, most recent date first, grouped by date.

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
