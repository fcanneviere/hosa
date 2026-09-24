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
