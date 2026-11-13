---
type: Module
title: skills/interface/scripts
description: '!/usr/bin/env python3'
resource: skills/interface/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-13T07:17:11Z'}
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

- `Maquette` — `skills/interface/scripts/atelier.py:738` — Réécrit une maquette en un document autonome, balise par balise : chaque ressource locale intégrée en data:,
- `Refus` — `skills/interface/scripts/atelier.py:52` — Une entrée refusée : le message dit exactement quoi corriger.
- `Source` — `skills/interface/scripts/atelier.py:579` — Un fichier de maquette et les règles d'intégration de ses ressources locales.
- `acteur` — `skills/interface/scripts/atelier.py:1125`
- `adresse_locale` — `skills/interface/scripts/atelier.py:933` — Une option en direct ne vise qu'un serveur de cette machine, sans identifiants, avec un port valide.
- `axes` — `skills/interface/scripts/atelier.py:292` — L'identité d'une carte sur des axes fermés : deux cartes qui ne diffèrent que d'une nuance n'en font qu'une.
- `bloc_css` — `skills/interface/scripts/atelier.py:1169`
- `canaux` — `skills/interface/scripts/atelier.py:117`
- `carte_html` — `skills/interface/scripts/atelier.py:394`
- `cartes` — `skills/interface/scripts/atelier.py:495`
- `cartes_proches` — `skills/interface/scripts/atelier.py:305`
- `chaine` — `skills/interface/scripts/atelier.py:71`
- `chaines` — `skills/interface/scripts/atelier.py:78`
- `charge_cartes` — `skills/interface/scripts/atelier.py:208`
- `charge_manifest` — `skills/interface/scripts/atelier.py:956`
- `choisir` — `skills/interface/scripts/atelier.py:1132`
- `comparer` — `skills/interface/scripts/atelier.py:1023`
- `contraste` — `skills/interface/scripts/atelier.py:134`
- `controle_grille` — `skills/interface/scripts/atelier.py:1315` — Ce que `revue` écrit et ce que `avancement.py task done interface revue` relit : la même fonction.
- `controles` — `skills/interface/scripts/atelier.py:169` — (une ligne par paire avec son rapport, un manque par paire sous son minimum avec une couleur proposée).
- `courbe` — `skills/interface/scripts/atelier.py:343` — L'évolution d'un indicateur en une ligne SVG, à la couleur d'accent ; rien sans série.
- `css` — `skills/interface/scripts/atelier.py:1177`
- `data_url` — `skills/interface/scripts/atelier.py:575`
- `ecarts` — `skills/interface/scripts/atelier.py:1201` — Les jetons de la KB sont-ils ceux du CSS du projet ? Rien à contrôler sans jetons (identité conservée).
- `ecran_html` — `skills/interface/scripts/atelier.py:356` — Le premier écran dans cette identité, avec le vrai menu, les vraies colonnes et les vraies lignes.
- `ecrit_atomique` — `skills/interface/scripts/atelier.py:483`
- `ecrit_choix` — `skills/interface/scripts/atelier.py:1090`
- `entier` — `skills/interface/scripts/atelier.py:101`
- `famille` — `skills/interface/scripts/atelier.py:317`
- `grille` — `skills/interface/scripts/atelier.py:1239` — Le modèle que `hosa-ux-designer` remplit en revue : une réponse par question, avec sa preuve.
- `jetons` — `skills/interface/scripts/atelier.py:321` — Les jetons de l'identité, nommés comme dans le CSS du projet : la seule définition, de la carte au code.
- `journal` — `skills/interface/scripts/atelier.py:1110` — Une ligne dans `kb/interface/log.md`, sous la date du jour (OKF §9).
- `lit_choix` — `skills/interface/scripts/atelier.py:1075` — {manches: {manche: (option, nom, demande, date)}, jetons: {nom: valeur}, css: chemin\|None} — la dernière
- `lit_json` — `skills/interface/scripts/atelier.py:56`
- `lit_srcset` — `skills/interface/scripts/atelier.py:716` — Les candidats d'un srcset : (adresse, descripteur). Une adresse data: garde ses virgules.
- `luminance` — `skills/interface/scripts/atelier.py:129`
- `main` — `skills/interface/scripts/atelier.py:1351`
- `maintenant` — `skills/interface/scripts/atelier.py:1066`
- `mix` — `skills/interface/scripts/atelier.py:124` — Le mélange sRGB que le navigateur calcule pour `color-mix(in srgb, a part_a, b)`.
- `note_grille` — `skills/interface/scripts/atelier.py:1271` — {note, oui, comptes, non, manques} — la note se calcule, l'agent ne la donne pas : plancher de
- `objet` — `skills/interface/scripts/atelier.py:87`
- `ordonne` — `skills/interface/scripts/atelier.py:946` — L'écran actuel d'abord, sans lettre ; puis la recommandée en a), les autres dans l'ordre du fichier.
- `paires` — `skills/interface/scripts/atelier.py:150` — Chaque paire de couleurs que la carte et l'interface montrent, avec son minimum WCAG AA :
- `parmi` — `skills/interface/scripts/atelier.py:94`
- `plafond` — `skills/interface/scripts/atelier.py:1235`
- `police` — `skills/interface/scripts/atelier.py:199` — Des familles installées, séparées par des virgules : rien qui charge une police par le réseau.
- `prepare_html` — `skills/interface/scripts/atelier.py:909`
- `prepare_image` — `skills/interface/scripts/atelier.py:920`
- `preuve_valide` — `skills/interface/scripts/atelier.py:1256` — Chaque capture citée : un chemin depuis la racine du projet vers une image qui existe, dans le projet.
- `proposition` — `skills/interface/scripts/atelier.py:139` — La couleur la plus proche de `avant`, même teinte, qui tient `mini` sur `arriere` : poussée vers le noir
- `questions_grille` — `skills/interface/scripts/atelier.py:1226` — Les questions fermées de la revue, déclarées dans pipeline.json (la seule définition).
- `racine_de` — `skills/interface/scripts/atelier.py:1173`
- `reecrit_css` — `skills/interface/scripts/atelier.py:654` — Une passe sur le CSS : chaque `url()` et chaque chaîne d'`image-set()`/`src()` est un fichier local intégré,
- `revue` — `skills/interface/scripts/atelier.py:1324` — Calcule la note de la grille remplie et ajoute sa ligne sous `## Revue visuelle` de `navigation.md`.
- `section` — `skills/interface/scripts/atelier.py:1070`
- `ErreurDePage` — `skills/interface/scripts/capture.mjs:297`
- `Tube` — `skills/interface/scripts/capture.mjs:178`
- `Tube.attend.fin` — `skills/interface/scripts/capture.mjs:231`
- `adresse` — `skills/interface/scripts/capture.mjs:639`
- `adresseDeBase` — `skills/interface/scripts/capture.mjs:120`
- `adresseDeBase.absent` — `skills/interface/scripts/capture.mjs:128`
- `arret` — `skills/interface/scripts/capture.mjs:46`
- `centre` — `skills/interface/scripts/capture.mjs:573`
- `chargee` — `skills/interface/scripts/capture.mjs:317`
- `clique` — `skills/interface/scripts/capture.mjs:586`
- `controlesDeLaPage` — `skills/interface/scripts/capture.mjs:349` — Chaque problème nomme l'élément par un sélecteur court, et son texte quand il en a un.
- `controlesDeLaPage.cite` — `skills/interface/scripts/capture.mjs:356`
- `controlesDeLaPage.couleur` — `skills/interface/scripts/capture.mjs:400`
- `controlesDeLaPage.fondDe` — `skills/interface/scripts/capture.mjs:410`
- `controlesDeLaPage.hexa` — `skills/interface/scripts/capture.mjs:426`
- `controlesDeLaPage.lum` — `skills/interface/scripts/capture.mjs:421`
- `controlesDeLaPage.nom` — `skills/interface/scripts/capture.mjs:352`
- `controlesDeLaPage.nomme` — `skills/interface/scripts/capture.mjs:449`
- `controlesDeLaPage.rapport` — `skills/interface/scripts/capture.mjs:425`
- `controlesDeLaPage.sur` — `skills/interface/scripts/capture.mjs:408`
- `controlesDeLaPage.visible` — `skills/interface/scripts/capture.mjs:360`
- `dansLaPage` — `skills/interface/scripts/capture.mjs:300` — (page d'erreur du navigateur) perd son contexte un instant : on réessaie.
- `dePage` — `skills/interface/scripts/capture.mjs:276`
- `empreinte` — `skills/interface/scripts/capture.mjs:97`
- `fenetre` — `skills/interface/scripts/capture.mjs:329`
- `joue` — `skills/interface/scripts/capture.mjs:607`
- `joue.tour` — `skills/interface/scripts/capture.mjs:617`
- `joue.unSeul` — `skills/interface/scripts/capture.mjs:610`
- `liste` — `skills/interface/scripts/capture.mjs:76`
- `mots` — `skills/interface/scripts/capture.mjs:564` — ---------- Actions : se connecter, ouvrir un menu, remplir un champ… ----------
- `nettoie` — `skills/interface/scripts/capture.mjs:251`
- `nomRoute` — `skills/interface/scripts/capture.mjs:99`
- `nomSur` — `skills/interface/scripts/capture.mjs:98`
- `ouvre` — `skills/interface/scripts/capture.mjs:319`
- `page` — `skills/interface/scripts/capture.mjs:275`
- `pause` — `skills/interface/scripts/capture.mjs:103`
- `photo` — `skills/interface/scripts/capture.mjs:335`
- `planche` — `skills/interface/scripts/capture.mjs:545` — ---------- Planche : les captures d'une taille, quatre par ligne ----------
- `planche.echappe` — `skills/interface/scripts/capture.mjs:548`
- `poseMasque` — `skills/interface/scripts/capture.mjs:501`
- `poseReperes` — `skills/interface/scripts/capture.mjs:467` — ---------- Repères, masque : un calque SVG posé sur la page, retiré après la capture ----------
- `poseReperes.forme` — `skills/interface/scripts/capture.mjs:475`
- `prive` — `skills/interface/scripts/capture.mjs:116`
- `retireCalques` — `skills/interface/scripts/capture.mjs:539`
- `sansBarre` — `skills/interface/scripts/capture.mjs:675`
- `souris` — `skills/interface/scripts/capture.mjs:584`
- `touche` — `skills/interface/scripts/capture.mjs:598`
- `trouveNavigateur` — `skills/interface/scripts/capture.mjs:153` — ---------- Navigateur : invisible, profil jetable, piloté sur un tube ----------
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
