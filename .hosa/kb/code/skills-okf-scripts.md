---
type: Module
title: skills/okf/scripts
description: '!/usr/bin/env python3'
resource: skills/okf/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-12T18:11:46Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/okf/scripts/kb_index.py` | !/usr/bin/env python3 |
| `skills/okf/scripts/kb_query.py` | !/usr/bin/env python3 |
| `skills/okf/scripts/okf_validate.py` | !/usr/bin/env python3 |

## Symboles publics

- `build` — `skills/okf/scripts/kb_index.py:90`
- `frontmatter` — `skills/okf/scripts/kb_index.py:37`
- `main` — `skills/okf/scripts/kb_index.py:121`
- `concept_files` — `skills/okf/scripts/kb_query.py:40` — The KB's concept files: no reserved file, no generated `code/`, nothing under a hidden folder
- `main` — `skills/okf/scripts/kb_query.py:124`
- `matches` — `skills/okf/scripts/kb_query.py:99`
- `scalar` — `skills/okf/scripts/kb_query.py:50`
- `sections` — `skills/okf/scripts/kb_query.py:88`
- `split` — `skills/okf/scripts/kb_query.py:71` — Tolerant frontmatter reader (stdlib only): scalars, flow lists and block lists.
- `text_of` — `skills/okf/scripts/kb_query.py:67`
- `value` — `skills/okf/scripts/kb_query.py:59` — A YAML flow list `[a, "b"]` → ['a', 'b']; a quoted scalar unquoted; else the text.
- `Report` — `skills/okf/scripts/okf_validate.py:127`
- `bundle_files` — `skills/okf/scripts/okf_validate.py:119` — Every `.md` of the bundle, except under a hidden folder: `.claude/agent-memory*` (an agent whose
- `changed_files` — `skills/okf/scripts/okf_validate.py:543` — Bundle-relative paths with uncommitted changes (this session's writes), or None outside git.
- `changed_files.run` — `skills/okf/scripts/okf_validate.py:545`
- `check_actor` — `skills/okf/scripts/okf_validate.py:231` — §7 — the actor convention shared by `generated.by`, `verified[].by` and
- `check_computation` — `skills/okf/scripts/okf_validate.py:168` — §10.2 — the Attested Computation contract, including its path-valued fields.
- `check_concept` — `skills/okf/scripts/okf_validate.py:198`
- `check_index` — `skills/okf/scripts/okf_validate.py:356`
- `check_instant` — `skills/okf/scripts/okf_validate.py:246` — §5.2 — `at` values are RFC 3339; a date-only value is tolerated.
- `check_lifecycle` — `skills/okf/scripts/okf_validate.py:286` — §5.4 / §5.5 — `status` and `stale_after`. A concept is stale when
- `check_links` — `skills/okf/scripts/okf_validate.py:424` — Broken bundle-internal links are warnings only (§6.1).
- `check_log` — `skills/okf/scripts/okf_validate.py:383`
- `check_sources` — `skills/okf/scripts/okf_validate.py:315` — §5.1 — the `sources` provenance family and its footnote join keys.
- `check_trust` — `skills/okf/scripts/okf_validate.py:252` — §5.2 — `generated` / `verified`, with the v0.1 `timestamp` fallback.
- `check_window` — `skills/okf/scripts/okf_validate.py:299` — §5.1 — a `usage_window` is a `{from, to}` pair of ISO 8601 datetimes.
- `citations_to_sources` — `skills/okf/scripts/okf_validate.py:450` — Hoist a v0.1 `# Citations` list into the `sources` family (§5.1, §13.1).
- `collect_link_targets` — `skills/okf/scripts/okf_validate.py:404`
- `main` — `skills/okf/scripts/okf_validate.py:596`
- `migrate` — `skills/okf/scripts/okf_validate.py:501` — Migrate a bundle in place. Returns the relative paths actually rewritten.
- `migrate_text` — `skills/okf/scripts/okf_validate.py:469` — Rewrite one file's v0.1 constructs to v0.2. None when nothing changes.
- `split_frontmatter` — `skills/okf/scripts/okf_validate.py:141` — Return (raw_yaml, body). raw_yaml is None when no frontmatter block.
- `validate` — `skills/okf/scripts/okf_validate.py:527`
- `warning_lines` — `skills/okf/scripts/okf_validate.py:558` — Warnings on changed files in full; the others grouped by kind, with a count and EXAMPLES files.

## Tickets et exigences

Aucun.
