---
name: okf
description: Use whenever a skill or agent writes, edits, renames or deprecates a file under `.hosa/kb/` — the rules every KB file must follow (Open Knowledge Format 0.2) and the validator run that closes every KB write. Also usable directly — "vérifie la KB", "valide le format OKF".
---

# OKF — writing the Hosa knowledge base

The KB (`.hosa/kb/`) is an [Open Knowledge Format 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format) bundle. Every file in it is read by other agents, by the web app and by the project graph — a malformed file silently drops out of all three. Follow these rules on every write, then run the validator.

## Concepts

One markdown file = one concept. YAML frontmatter, then a markdown body.

```markdown
---
type: Ticket
title: Export CSV des factures
description: Export des factures du mois au format CSV.
tags: [facturation]
status: draft
generated: { by: hosa-product-owner/1.0, at: 2026-09-27T10:00:00Z }
---
Lié à : [exigence](../cdc/facturation.md)
```

- **`type` is the only required field** — without it the concept is invisible (the app and the graph skip it). Use the type the owning bundle already uses (`Ticket`, `Exigence`, `Persona`, `Sprint`, `Module`…); never invent a variant spelling.
- `title`, `description`, `tags`, `resource` are optional but expected when known. `description` is one sentence — it is what `index.md` shows.
- **Filename = slug**: lowercase, digits, single hyphens (`export-csv.md`). The slug is the concept's identity — tickets, the graph and links use it. Never rename a concept others link to; deprecate it and create a new one.
- **`status`** ∈ `draft` | `stable` | `deprecated`. Never delete a concept others may reference: set `status: deprecated` and say in the body what replaces it.
- Dates are ISO 8601 strings (`2026-09-27T10:00:00Z`), quoted if a YAML parser could read them as a date.

## Trust tier — `generated` / `verified`

- `generated: { by: <actor>, at: <ISO8601> }` — who wrote the current content. Actor shapes: `human:<name>` (a person), `<agent>/<version>` (an agent, e.g. `hosa-architect/1.0`), `process:<tool>` (a deterministic tool, e.g. `process:hosa-graph`). Exact lowercase prefixes — trust tiers are keyed off them.
- `verified: { by: <actor>, at: <ISO8601> }` — who checked it. **Never write `verified: { by: human:… }` unless a human actually reviewed this exact content in this session.** An agent may only write `verified` with its own `<agent>/<version>` actor.
- Rewriting a concept's content resets trust: update `generated`, drop a `verified` that no longer covers the new content.

## Links

Relations are plain relative markdown links in the body (OKF §6.1): `[exigence](../cdc/facturation.md)`. Relative to the current file, always ending in `.md` (or `/` for a bundle). No wiki-links, no absolute paths, no typed-relation syntax. A link to a concept that does not exist is an error — create the target or drop the link.

## Reserved files

`index.md` and `log.md` are reserved names — never a concept.

- **`index.md`** (§8) lists a bundle's concepts and sub-bundles, one line each: `* [Title](slug.md) - description` or `* [folder](folder/) - what it holds`. The root `index.md` also carries `okf_version: "0.2"`. Add the line when you create a concept or bundle.
- **`log.md`** (§9) records every write in the bundle, newest day first:

  ```markdown
  # Log — kb/tickets

  ## 2026-09-27
  - hosa-product-owner/1.0 a créé `export-csv`
  ```

  One line per write: actor, verb, slug in backticks. Append under today's heading (create it at the top if missing). Never rewrite past entries.

## Generated bundles

`kb/code/` is written by `process:hosa-graph` from the source code — never edit it by hand, your change is overwritten at the next index. To correct it, fix the code (docstrings, file layout) and let the graph regenerate it.

## Final step — validate (required)

After any KB write, run the validator on the KB root and fix every error before reporting done:

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/okf/scripts/okf_validate.py" <project>/.hosa/kb
```

Then refresh the KB summary — one line per concept, the file every agent reads before opening anything else:

```bash
<python> "${CLAUDE_PLUGIN_ROOT}/skills/okf/scripts/kb_index.py" <project>/.hosa/kb
```

The hooks also refresh it after each Edit/Write in the KB and at session start; running it here covers writes made by scripts.

`<python>` is the Hosa app's venv interpreter (`hosa/app/.venv/Scripts/python.exe` on Windows, `hosa/app/.venv/bin/python` elsewhere) or any Python with PyYAML. Exit code `0` = conformant; `1` = errors listed (fix them, rerun); `2` = bad invocation. Warnings are not blocking but mention them in your report. `--json` gives machine-readable output.
