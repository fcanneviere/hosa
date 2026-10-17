---
type: Module
title: skills/okf/scripts
description: '!/usr/bin/env python3'
resource: skills/okf/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-11T07:00:52Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/okf/scripts/kb_index.py` | !/usr/bin/env python3 |
| `skills/okf/scripts/kb_query.py` | !/usr/bin/env python3 |
| `skills/okf/scripts/okf_validate.py` | !/usr/bin/env python3 |

## Symboles publics

- `build` — `skills/okf/scripts/kb_index.py:38`
- `frontmatter` — `skills/okf/scripts/kb_index.py:26`
- `main` — `skills/okf/scripts/kb_index.py:70`
- `main` — `skills/okf/scripts/kb_query.py:89`
- `matches` — `skills/okf/scripts/kb_query.py:66`
- `sections` — `skills/okf/scripts/kb_query.py:55`
- `split` — `skills/okf/scripts/kb_query.py:39`
- `Report` — `skills/okf/scripts/okf_validate.py:116`
- `check_actor` — `skills/okf/scripts/okf_validate.py:220` — §7 — the actor convention shared by `generated.by`, `verified[].by` and
- `check_computation` — `skills/okf/scripts/okf_validate.py:157` — §10.2 — the Attested Computation contract, including its path-valued fields.
- `check_concept` — `skills/okf/scripts/okf_validate.py:187`
- `check_index` — `skills/okf/scripts/okf_validate.py:345`
- `check_instant` — `skills/okf/scripts/okf_validate.py:235` — §5.2 — `at` values are RFC 3339; a date-only value is tolerated.
- `check_lifecycle` — `skills/okf/scripts/okf_validate.py:275` — §5.4 / §5.5 — `status` and `stale_after`. A concept is stale when
- `check_links` — `skills/okf/scripts/okf_validate.py:407` — Broken bundle-internal links are warnings only (§6.1).
- `check_log` — `skills/okf/scripts/okf_validate.py:372`
- `check_sources` — `skills/okf/scripts/okf_validate.py:304` — §5.1 — the `sources` provenance family and its footnote join keys.
- `check_trust` — `skills/okf/scripts/okf_validate.py:241` — §5.2 — `generated` / `verified`, with the v0.1 `timestamp` fallback.
- `check_window` — `skills/okf/scripts/okf_validate.py:288` — §5.1 — a `usage_window` is a `{from, to}` pair of ISO 8601 datetimes.
- `citations_to_sources` — `skills/okf/scripts/okf_validate.py:429` — Hoist a v0.1 `# Citations` list into the `sources` family (§5.1, §13.1).
- `collect_link_targets` — `skills/okf/scripts/okf_validate.py:387`
- `main` — `skills/okf/scripts/okf_validate.py:539`
- `migrate` — `skills/okf/scripts/okf_validate.py:480` — Migrate a bundle in place. Returns the relative paths actually rewritten.
- `migrate_text` — `skills/okf/scripts/okf_validate.py:448` — Rewrite one file's v0.1 constructs to v0.2. None when nothing changes.
- `split_frontmatter` — `skills/okf/scripts/okf_validate.py:130` — Return (raw_yaml, body). raw_yaml is None when no frontmatter block.
- `validate` — `skills/okf/scripts/okf_validate.py:506`

## Tickets et exigences

Aucun.
