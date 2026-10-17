---
type: Module
title: skills/interface/vendor/oil-ui/scripts
description: '!/usr/bin/env python3'
resource: skills/interface/vendor/oil-ui/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-10-11T07:00:52Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/interface/vendor/oil-ui/scripts/build_explorer.py` | !/usr/bin/env python3 |
| `skills/interface/vendor/oil-ui/scripts/build_style_cards.py` | !/usr/bin/env python3 |
| `skills/interface/vendor/oil-ui/scripts/shoot.mjs` |  |

## Symboles publics

- `AssetCheck` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:45` — Reject resource dependencies; the browser sandbox disables behavior.
- `build` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:356`
- `check_css` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:102`
- `check_css.check_resource` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:106`
- `css_unescape` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:93`
- `css_unescape.replacement` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:94`
- `embed_local_files` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:160` — Inline images, fonts and videos referenced relative to the candidate, as long as they stay inside the manifest folder.
- `embed_local_files.attr` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:173`
- `embed_local_files.css` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:177`
- `embed_local_files.data_url` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:163`
- `inline_local_code` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:196` — Inline stylesheets and, for interactive candidates, scripts that live in the manifest folder.
- `inline_local_code.link` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:199`
- `inline_local_code.script` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:210`
- `load_manifest` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:281`
- `local_file` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:189`
- `local_url` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:269` — Live candidates only point at a dev server on this machine.
- `main` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:402`
- `prepare_html` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:234`
- `prepare_image` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:253`
- `preview_csp` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:144`
- `text_field` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:29`
- `text_list` — `skills/interface/vendor/oil-ui/scripts/build_explorer.py:36`
- `ConfigError` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:57`
- `build` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:250`
- `card_html` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:174`
- `first_font` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:150`
- `load` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:77`
- `main` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:303`
- `need` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:61`
- `sketch` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:154` — Esquisse de mise en page : des aplats seulement, disposés selon le gabarit choisi.
- `text_list` — `skills/interface/vendor/oil-ui/scripts/build_style_cards.py:71`
- `cdp` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:214`
- `center` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:344`
- `check` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:265`
- `cleanup` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:159`
- `evaluate` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:241`
- `fail` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:74`
- `findChrome` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:128` — ---------- Navigateur temporaire isolé, sans toucher aux données du navigateur de l'utilisateur ----------
- `mark` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:303`
- `mask` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:296`
- `mouse` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:349`
- `onerror` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:194`
- `onmessage` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:198`
- `open` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:253`
- `open.fn` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:255`
- `privatePath` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:91`
- `probeMotion` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:514`
- `probeMotion.brief` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:560`
- `probeMotion.weak` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:544`
- `record` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:393` — ---------- Enregistrement vidéo ----------
- `record.onFrame` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:397`
- `resolveTarget` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:94`
- `runSteps` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:350`
- `screenshot` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:282`
- `send` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:206`
- `setViewport` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:248`
- `sheet` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:376` — ---------- Planche : le même navigateur assemble les captures en une image ----------
- `sheet.escapeHtml` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:378`
- `sleep` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:246`
- `tokenize` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:340` — ---------- Actions ----------
- `unmark` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:337`
- `withState` — `skills/interface/vendor/oil-ui/scripts/shoot.mjs:567`

## Tickets et exigences

Aucun.
