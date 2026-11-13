---
type: Module
title: skills/interface/scripts
description: '!/usr/bin/env python3'
resource: skills/interface/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-12T23:52:08Z'}
---

## Fichiers

| Fichier | Rôle |
|---|---|
| `skills/interface/scripts/atelier.py` | !/usr/bin/env python3 |
| `skills/interface/scripts/capture.mjs` |  |
| `skills/interface/scripts/capture.py` | !/usr/bin/env python3 |
| `skills/interface/scripts/interface_check.py` | !/usr/bin/env python3 |
| `skills/interface/scripts/lexique_check.py` | !/usr/bin/env python3 |

## Symboles publics

- `Maquette` — `skills/interface/scripts/atelier.py:692` — Réécrit une maquette en un document autonome, balise par balise : chaque ressource locale intégrée en data:,
- `Refus` — `skills/interface/scripts/atelier.py:45` — Une entrée refusée : le message dit exactement quoi corriger.
- `Source` — `skills/interface/scripts/atelier.py:533` — Un fichier de maquette et les règles d'intégration de ses ressources locales.
- `acteur` — `skills/interface/scripts/atelier.py:1058`
- `adresse_locale` — `skills/interface/scripts/atelier.py:866` — Une option en direct ne vise qu'un serveur de cette machine, sans identifiants, avec un port valide.
- `bloc_css` — `skills/interface/scripts/atelier.py:1102`
- `canaux` — `skills/interface/scripts/atelier.py:110`
- `carte_html` — `skills/interface/scripts/atelier.py:356`
- `cartes` — `skills/interface/scripts/atelier.py:457`
- `chaine` — `skills/interface/scripts/atelier.py:64`
- `chaines` — `skills/interface/scripts/atelier.py:71`
- `charge_cartes` — `skills/interface/scripts/atelier.py:201`
- `charge_manifest` — `skills/interface/scripts/atelier.py:889`
- `choisir` — `skills/interface/scripts/atelier.py:1065`
- `comparer` — `skills/interface/scripts/atelier.py:956`
- `contraste` — `skills/interface/scripts/atelier.py:127`
- `controles` — `skills/interface/scripts/atelier.py:162` — (une ligne par paire avec son rapport, un manque par paire sous son minimum avec une couleur proposée).
- `courbe` — `skills/interface/scripts/atelier.py:305` — L'évolution d'un indicateur en une ligne SVG, à la couleur d'accent ; rien sans série.
- `css` — `skills/interface/scripts/atelier.py:1110`
- `data_url` — `skills/interface/scripts/atelier.py:529`
- `ecarts` — `skills/interface/scripts/atelier.py:1134` — Les jetons de la KB sont-ils ceux du CSS du projet ? Rien à contrôler sans jetons (identité conservée).
- `ecran_html` — `skills/interface/scripts/atelier.py:318` — Le premier écran dans cette identité, avec le vrai menu, les vraies colonnes et les vraies lignes.
- `ecrit_atomique` — `skills/interface/scripts/atelier.py:445`
- `ecrit_choix` — `skills/interface/scripts/atelier.py:1023`
- `entier` — `skills/interface/scripts/atelier.py:94`
- `famille` — `skills/interface/scripts/atelier.py:279`
- `jetons` — `skills/interface/scripts/atelier.py:283` — Les jetons de l'identité, nommés comme dans le CSS du projet : la seule définition, de la carte au code.
- `journal` — `skills/interface/scripts/atelier.py:1043` — Une ligne dans `kb/interface/log.md`, sous la date du jour (OKF §9).
- `lit_choix` — `skills/interface/scripts/atelier.py:1008` — {manches: {manche: (option, nom, demande, date)}, jetons: {nom: valeur}, css: chemin\|None} — la dernière
- `lit_json` — `skills/interface/scripts/atelier.py:49`
- `lit_srcset` — `skills/interface/scripts/atelier.py:670` — Les candidats d'un srcset : (adresse, descripteur). Une adresse data: garde ses virgules.
- `luminance` — `skills/interface/scripts/atelier.py:122`
- `main` — `skills/interface/scripts/atelier.py:1154`
- `maintenant` — `skills/interface/scripts/atelier.py:999`
- `mix` — `skills/interface/scripts/atelier.py:117` — Le mélange sRGB que le navigateur calcule pour `color-mix(in srgb, a part_a, b)`.
- `objet` — `skills/interface/scripts/atelier.py:80`
- `ordonne` — `skills/interface/scripts/atelier.py:879` — L'écran actuel d'abord, sans lettre ; puis la recommandée en a), les autres dans l'ordre du fichier.
- `paires` — `skills/interface/scripts/atelier.py:143` — Chaque paire de couleurs que la carte et l'interface montrent, avec son minimum WCAG AA :
- `parmi` — `skills/interface/scripts/atelier.py:87`
- `police` — `skills/interface/scripts/atelier.py:192` — Des familles installées, séparées par des virgules : rien qui charge une police par le réseau.
- `prepare_html` — `skills/interface/scripts/atelier.py:842`
- `prepare_image` — `skills/interface/scripts/atelier.py:853`
- `proposition` — `skills/interface/scripts/atelier.py:132` — La couleur la plus proche de `avant`, même teinte, qui tient `mini` sur `arriere` : poussée vers le noir
- `racine_de` — `skills/interface/scripts/atelier.py:1106`
- `reecrit_css` — `skills/interface/scripts/atelier.py:608` — Une passe sur le CSS : chaque `url()` et chaque chaîne d'`image-set()`/`src()` est un fichier local intégré,
- `section` — `skills/interface/scripts/atelier.py:1003`
- `ErreurDePage` — `skills/interface/scripts/capture.mjs:296`
- `Tube` — `skills/interface/scripts/capture.mjs:177`
- `Tube.attend.fin` — `skills/interface/scripts/capture.mjs:230`
- `adresse` — `skills/interface/scripts/capture.mjs:612`
- `adresseDeBase` — `skills/interface/scripts/capture.mjs:120`
- `adresseDeBase.absent` — `skills/interface/scripts/capture.mjs:128`
- `arret` — `skills/interface/scripts/capture.mjs:46`
- `centre` — `skills/interface/scripts/capture.mjs:546`
- `chargee` — `skills/interface/scripts/capture.mjs:316`
- `clique` — `skills/interface/scripts/capture.mjs:559`
- `controlesDeLaPage` — `skills/interface/scripts/capture.mjs:348` — Chaque problème nomme l'élément par un sélecteur court, et son texte quand il en a un.
- `controlesDeLaPage.cite` — `skills/interface/scripts/capture.mjs:355`
- `controlesDeLaPage.couleur` — `skills/interface/scripts/capture.mjs:373`
- `controlesDeLaPage.fondDe` — `skills/interface/scripts/capture.mjs:383`
- `controlesDeLaPage.hexa` — `skills/interface/scripts/capture.mjs:399`
- `controlesDeLaPage.lum` — `skills/interface/scripts/capture.mjs:394`
- `controlesDeLaPage.nom` — `skills/interface/scripts/capture.mjs:351`
- `controlesDeLaPage.nomme` — `skills/interface/scripts/capture.mjs:422`
- `controlesDeLaPage.rapport` — `skills/interface/scripts/capture.mjs:398`
- `controlesDeLaPage.sur` — `skills/interface/scripts/capture.mjs:381`
- `controlesDeLaPage.visible` — `skills/interface/scripts/capture.mjs:359`
- `dansLaPage` — `skills/interface/scripts/capture.mjs:299` — (page d'erreur du navigateur) perd son contexte un instant : on réessaie.
- `dePage` — `skills/interface/scripts/capture.mjs:275`
- `empreinte` — `skills/interface/scripts/capture.mjs:97`
- `fenetre` — `skills/interface/scripts/capture.mjs:328`
- `joue` — `skills/interface/scripts/capture.mjs:580`
- `joue.tour` — `skills/interface/scripts/capture.mjs:590`
- `joue.unSeul` — `skills/interface/scripts/capture.mjs:583`
- `liste` — `skills/interface/scripts/capture.mjs:76`
- `mots` — `skills/interface/scripts/capture.mjs:537` — ---------- Actions : se connecter, ouvrir un menu, remplir un champ… ----------
- `nettoie` — `skills/interface/scripts/capture.mjs:250`
- `nomRoute` — `skills/interface/scripts/capture.mjs:99`
- `nomSur` — `skills/interface/scripts/capture.mjs:98`
- `ouvre` — `skills/interface/scripts/capture.mjs:318`
- `page` — `skills/interface/scripts/capture.mjs:274`
- `pause` — `skills/interface/scripts/capture.mjs:103`
- `photo` — `skills/interface/scripts/capture.mjs:334`
- `planche` — `skills/interface/scripts/capture.mjs:518` — ---------- Planche : les captures d'une taille, quatre par ligne ----------
- `planche.echappe` — `skills/interface/scripts/capture.mjs:521`
- `poseMasque` — `skills/interface/scripts/capture.mjs:474`
- `poseReperes` — `skills/interface/scripts/capture.mjs:440` — ---------- Repères, masque : un calque SVG posé sur la page, retiré après la capture ----------
- `poseReperes.forme` — `skills/interface/scripts/capture.mjs:448`
- `prive` — `skills/interface/scripts/capture.mjs:116`
- `retireCalques` — `skills/interface/scripts/capture.mjs:512`
- `sansBarre` — `skills/interface/scripts/capture.mjs:648`
- `souris` — `skills/interface/scripts/capture.mjs:557`
- `touche` — `skills/interface/scripts/capture.mjs:571`
- `trouveNavigateur` — `skills/interface/scripts/capture.mjs:152` — ---------- Navigateur : invisible, profil jetable, piloté sur un tube ----------
- `lignes_ecrans` — `skills/interface/scripts/capture.py:39`
- `main` — `skills/interface/scripts/capture.py:82`
- `node` — `skills/interface/scripts/capture.py:70`
- `remplit` — `skills/interface/scripts/capture.py:58`
- `roles_du_plan` — `skills/interface/scripts/capture.py:29` — Les rôles de la colonne `Rôles`, dans l'ordre : un passage de capture chacun.
- `routes_du_plan` — `skills/interface/scripts/capture.py:47` — Les routes de la colonne `Route` de `## Écrans`, dans l'ordre, sans doublon ; avec `role`, celles de ce rôle.
- `back_office_gaps` — `skills/interface/scripts/interface_check.py:97`
- `checklist` — `skills/interface/scripts/interface_check.py:67`
- `dashboard_gaps` — `skills/interface/scripts/interface_check.py:125`
- `field` — `skills/interface/scripts/interface_check.py:42`
- `gaps` — `skills/interface/scripts/interface_check.py:155`
- `indicators` — `skills/interface/scripts/interface_check.py:91` — The `INn` in force under `## Indicateurs` (a retired one keeps its line: `- **IN2** — retiré : …`).
- `main` — `skills/interface/scripts/interface_check.py:227`
- `objects` — `skills/interface/scripts/interface_check.py:82` — The business objects of `kb/cdc/modele-metier.md`: each `## <Objet>` but the notifications.
- `plain` — `skills/interface/scripts/interface_check.py:62` — A cell without its markdown: `Commandes` → Commandes, `` `/admin` `` → /admin.
- `section` — `skills/interface/scripts/interface_check.py:47`
- `split` — `skills/interface/scripts/interface_check.py:37`
- `stable_exigences` — `skills/interface/scripts/interface_check.py:72` — (slug, frontmatter, body) of each `stable` Exigence.
- `table` — `skills/interface/scripts/interface_check.py:52` — The rows of the first markdown table in `text`, header dropped, each padded to `width` cells.
- `cells` — `skills/interface/scripts/lexique_check.py:34`
- `files` — `skills/interface/scripts/lexique_check.py:65`
- `lexicon` — `skills/interface/scripts/lexique_check.py:38` — {term: [forbidden synonyms]}, folders to scan, problems.
- `main` — `skills/interface/scripts/lexique_check.py:92`
- `scan` — `skills/interface/scripts/lexique_check.py:76`
- `screens` — `skills/interface/scripts/lexique_check.py:56`
- `section` — `skills/interface/scripts/lexique_check.py:29`

## Tickets et exigences

Aucun.
