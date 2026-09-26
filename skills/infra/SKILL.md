---
name: infra
description: Use to set up and configure the managed project's Docker environment and install the chosen stack into it, for real, with a version-pinned, documented result. Second stage of the data-structuring pipeline (stack → infra → donnees → schema-app → schema-db → architecture), runs after `stack` has recorded the technical choices.
---

# Infra

Turns a chosen stack into a real, running, documented Docker environment for the managed project — the environment every later stage (and every day-to-day command against the managed project) runs inside.

## Flow

```
Lit kb/infra/ (chemin racine) et kb/stack/ (Stack Decision)
        ↓
Stack Decision absente → propose de lancer `stack` d'abord
        ↓
Lit le code existant du projet cible (Docker déjà présent ?)
et kb/cdc/ (besoins non-fonctionnels impliquant un service
supplémentaire)
        ↓
Détermine la composition Docker, épingle une version récente
et maintenue par service
        ↓
Écrit Dockerfile(s) + docker-compose.yml, démarre réellement
l'environnement, vérifie chaque service
        ↓
Écrit/complète kb/infra/environnement-docker.md, log
kb/infra/log.md
        ↓
Dispatch hosa-documentation (Mode 1) pour la documentation
d'installation
        ↓
Propose d'enchaîner sur `donnees`
```

## Trigger

Manual: `/infra`. Auto: immediately after `stack`, or "mets en place l'environnement Docker", "installe la stack".

---

## Step 1: Find the Managed Project

Read `kb/infra/` for an existing `Infra` entry giving the project's root path. If none exists, ask the user for it and write one — never accept `hosa/app` or `hosa/kb` as the path.

## Step 2: Check the Stack Decision

Read `kb/stack/` for the recorded `Stack Decision`s. If none exists, say so and propose running `stack` first — don't guess what to install.

## Step 3: Read Existing Infrastructure and Non-Functional Needs

Read the managed project's existing code for a Docker setup already in place — extend it, never duplicate it. Read `kb/cdc/`'s `stable` `Exigence`s for any non-functional need implying an extra service (a cache, a queue).

## Step 4: Determine the Composition and Pin Versions

Determine one service per stack component that has to run (application runtime, database, any extra service from Step 3). For each, pick a current, maintained, stable version — never `latest`, always pinned explicitly. If a web-search tool is available, use it to confirm the version currently maintained. If none is available, state the assumption and today's date explicitly, and say the user should correct it if a newer maintained version exists.

## Step 5: Write and Start the Environment

Write the `Dockerfile`(s) and `docker-compose.yml` in the managed project, matching its existing conventions if any. Actually start it (`docker compose up -d` or the project's existing equivalent) and verify each service responds. If Docker isn't available in the current execution environment, say so explicitly — never report a service as "in place" without having actually started and checked it.

## Step 6: Update the `Infra` Entry

Write or update `hosa/kb/infra/environnement-docker.md`:

```markdown
---
type: Infra
title: Environnement Docker — <projet>
description: Services Docker du projet géré, versions épinglées
tags: []
status: stable
generated: { by: hosa-infra/1.0, at: <ISO8601> }
---
## Services
- <service> — <image>:<version épinglée>

## Fichiers
- `<Dockerfile(s)>`
- `<docker-compose.yml>`
```

If the file already exists (a re-run), update it in place rather than duplicating it. Log to `kb/infra/log.md` (create if missing) — OKF §9.

## Step 7: Dispatch `hosa-documentation` (Mode 1)

Dispatch `hosa-documentation` (Mode 1) with what was installed and the paths concerned (Dockerfile(s), compose file, services/versions) — it writes the installation documentation into the managed project. Wait for its confirmation before continuing.

## No Commits

You don't commit. Report what changed and let the user decide when to commit.

## Output

```
## Environnement Docker
- Services : <service> (<image>:<version épinglée>)
- Fichiers : `<Dockerfile(s)>`, `<docker-compose.yml>`
- Statut : démarré et vérifié / non vérifié — <raison>

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]

## Suite
Je lance `donnees` maintenant ?
```
