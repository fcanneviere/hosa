---
name: pilotage
description: "Use when the user wants to see the project in the browser — the Hosa dashboard: progress plan, board, sprints, KB, graph, journal. Triggers: \"ouvre le tableau de bord\", \"lance l'app\", \"montre-moi l'avancement dans le navigateur\", \"/pilotage\"."
---

# Pilotage

Opens the Hosa dashboard on the managed project's `.hosa/kb/`. It only reads and edits the KB files: it never calls Claude.

From the managed project's root, run in the background (`run_in_background: true`), never in the foreground — the server keeps running:

```bash
python "${CLAUDE_PLUGIN_ROOT}/run.py"
```

(`python3` where `python` doesn't exist.) It builds the dependencies on first launch (`hosa/app/.venv`, a minute), then opens http://localhost:3000. `PORT=<n>` changes the port when 3000 is busy.

Then answer in two lines: the link, and what to look at first — **Steering** shows the progress plan (stage in progress, missing proofs, next skill to run).

Fails with "Pas de .hosa/kb" → the project isn't initialised: propose `hosa`.
