---
name: pilotage
description: "Use when the user wants to see the project in the browser — the Hosa dashboard: progress plan, board, sprints, KB, graph, journal. Triggers: \"ouvre le tableau de bord\", \"lance l'app\", \"montre-moi l'avancement dans le navigateur\", \"/pilotage\"."
---

# Pilotage

Opens the Hosa dashboard on the managed project's `.hosa/kb/`: follow the project, read and edit the KB, validate, write remarks for Claude. It only reads and edits the KB files: it never calls Claude.

From the managed project's root, run in the background (`run_in_background: true`), never in the foreground — the server keeps running:

```bash
CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" python "${CLAUDE_PLUGIN_ROOT}/run.py"
```

(`python3` where `python` doesn't exist.) It builds the dependencies on first launch if the session start hasn't yet (`${CLAUDE_PLUGIN_DATA}/venv`, a minute), then serves on port 3000, or on a free port when 3000 is taken (another project's dashboard may be there), and opens the browser on its own address. Never set `PORT` unless the user asks for a port.

The link is the address of the server's `Hosa — http://127.0.0.1:<port>` line: read the background output once for that line before answering. Never give an address you didn't read there — 3000 may be another project's KB. No such line, or `[exited …]` → give the error line instead.

Then answer in two lines: the link read there, and what to look at first — the **Vue d'ensemble** shows the next step and its command, and the button « Remarque pour Claude » sends feedback on any screen. Remarks are files of `kb/remarques/`: the resume card lists the open ones; close each with `<hosa> avancement "<kb>" remarque <chemin> --detail "<réponse>"`.

The Hosa pane (`/hosa-panneau`) has the same thing as a button, « Ouvrir le tableau de bord »: suggest it when the pane is open.

Fails with "Pas de .hosa/kb" → the project isn't initialised: propose `hosa`.
