---
type: Module
title: skills/interface/scripts
description: '!/usr/bin/env python3'
resource: skills/interface/scripts
tags: [code]
generated: {by: 'process:hosa-graph', at: '2026-11-13T07:48:56Z'}
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

- `Maquette` — `skills/interface/scripts/atelier.py:795` — Réécrit une maquette en un document autonome, balise par balise : chaque ressource locale intégrée en data:,
- `Refus` — `skills/interface/scripts/atelier.py:57` — Une entrée refusée : le message dit exactement quoi corriger.
- `Source` — `skills/interface/scripts/atelier.py:636` — Un fichier de maquette et les règles d'intégration de ses ressources locales.
- `acteur` — `skills/interface/scripts/atelier.py:1192`
- `adresse_locale` — `skills/interface/scripts/atelier.py:990` — Une option en direct ne vise qu'un serveur de cette machine, sans identifiants, avec un port valide.
- `axes` — `skills/interface/scripts/atelier.py:307` — L'identité d'une carte sur des axes fermés : deux cartes qui ne diffèrent que d'une nuance n'en font qu'une.
- `bloc_css` — `skills/interface/scripts/atelier.py:1239` — Le bloc des jetons. Sans variante, le bloc d'avant les modes, au caractère près : `ecart` le compare.
- `bordure` — `skills/interface/scripts/atelier.py:340` — Le trait des cadres. Une ombre ne se voit pas sur un fond sombre : en mode sombre, la variante
- `canaux` — `skills/interface/scripts/atelier.py:122`
- `carte_html` — `skills/interface/scripts/atelier.py:433`
- `cartes` — `skills/interface/scripts/atelier.py:544`
- `cartes_proches` — `skills/interface/scripts/atelier.py:320`
- `chaine` — `skills/interface/scripts/atelier.py:76`
- `chaines` — `skills/interface/scripts/atelier.py:83`
- `charge_cartes` — `skills/interface/scripts/atelier.py:213`
- `charge_manifest` — `skills/interface/scripts/atelier.py:1013`
- `choisir` — `skills/interface/scripts/atelier.py:1199`
- `comparer` — `skills/interface/scripts/atelier.py:1080`
- `contraste` — `skills/interface/scripts/atelier.py:139`
- `controle_grille` — `skills/interface/scripts/atelier.py:1500` — Ce que `revue` écrit et ce que `avancement.py task done interface revue` relit : la même fonction.
- `controle_revue` — `skills/interface/scripts/atelier.py:1401` — Le contrôle de la tâche interface/revue, déclaré dans pipeline.json (la seule définition).
- `controles` — `skills/interface/scripts/atelier.py:174` — (une ligne par paire avec son rapport, un manque par paire sous son minimum avec une couleur proposée).
- `courbe` — `skills/interface/scripts/atelier.py:382` — L'évolution d'un indicateur en une ligne SVG, à la couleur d'accent ; rien sans série.
- `css` — `skills/interface/scripts/atelier.py:1257`
- `data_url` — `skills/interface/scripts/atelier.py:632`
- `dtcg` — `skills/interface/scripts/atelier.py:1376` — Les jetons de `kb/interface/choix.md` au format DTCG 2025.10 : un fichier dérivé, refait à la demande,
- `dtcg_couleur` — `skills/interface/scripts/atelier.py:1322`
- `dtcg_fichier` — `skills/interface/scripts/atelier.py:1361`
- `dtcg_px` — `skills/interface/scripts/atelier.py:1332`
- `dtcg_valeur` — `skills/interface/scripts/atelier.py:1337` — La valeur DTCG d'un jeton CSS, pour les seules formes que `jetons()` écrit ; toute autre forme est refusée.
- `ecarts` — `skills/interface/scripts/atelier.py:1282` — Les jetons de la KB sont-ils ceux du CSS du projet ? Rien à contrôler sans jetons (identité conservée).
- `ecran_html` — `skills/interface/scripts/atelier.py:395` — Le premier écran dans cette identité, avec le vrai menu, les vraies colonnes et les vraies lignes.
- `ecrit_atomique` — `skills/interface/scripts/atelier.py:532`
- `ecrit_choix` — `skills/interface/scripts/atelier.py:1151`
- `entier` — `skills/interface/scripts/atelier.py:106`
- `famille` — `skills/interface/scripts/atelier.py:332`
- `grille` — `skills/interface/scripts/atelier.py:1419` — Le modèle que `hosa-ux-designer` remplit en revue : une réponse par question, avec sa preuve.
- `jetons` — `skills/interface/scripts/atelier.py:364` — Les jetons de l'identité, nommés comme dans le CSS du projet : la seule définition, de la carte au code.
- `jetons_couleurs` — `skills/interface/scripts/atelier.py:349`
- `jetons_variante` — `skills/interface/scripts/atelier.py:355` — Les jetons qui changent dans le mode opposé : les couleurs, et ce qui les porte (trait, focus).
- `journal` — `skills/interface/scripts/atelier.py:1177` — Une ligne dans `kb/interface/log.md`, sous la date du jour (OKF §9).
- `lit_choix` — `skills/interface/scripts/atelier.py:1134` — {manches: {manche: (option, nom, demande, date)}, jetons: {nom: valeur}, css: chemin\|None} — la dernière
- `lit_json` — `skills/interface/scripts/atelier.py:61`
- `lit_srcset` — `skills/interface/scripts/atelier.py:773` — Les candidats d'un srcset : (adresse, descripteur). Une adresse data: garde ses virgules.
- `luminance` — `skills/interface/scripts/atelier.py:134`
- `main` — `skills/interface/scripts/atelier.py:1536`
- `maintenant` — `skills/interface/scripts/atelier.py:1125`
- `mix` — `skills/interface/scripts/atelier.py:129` — Le mélange sRGB que le navigateur calcule pour `color-mix(in srgb, a part_a, b)`.
- `mode` — `skills/interface/scripts/atelier.py:336`
- `note_grille` — `skills/interface/scripts/atelier.py:1451` — {note, oui, comptes, non, manques} — la note se calcule, l'agent ne la donne pas : plancher de
- `objet` — `skills/interface/scripts/atelier.py:92`
- `ordonne` — `skills/interface/scripts/atelier.py:1003` — L'écran actuel d'abord, sans lettre ; puis la recommandée en a), les autres dans l'ordre du fichier.
- `paires` — `skills/interface/scripts/atelier.py:155` — Chaque paire de couleurs que la carte et l'interface montrent, avec son minimum WCAG AA :
- `parmi` — `skills/interface/scripts/atelier.py:99`
- `plafond` — `skills/interface/scripts/atelier.py:1415`
- `police` — `skills/interface/scripts/atelier.py:204` — Des familles installées, séparées par des virgules : rien qui charge une police par le réseau.
- `prepare_html` — `skills/interface/scripts/atelier.py:966`
- `prepare_image` — `skills/interface/scripts/atelier.py:977`
- `preuve_valide` — `skills/interface/scripts/atelier.py:1436` — Chaque capture citée : un chemin depuis la racine du projet vers une image qui existe, dans le projet.
- `proposition` — `skills/interface/scripts/atelier.py:144` — La couleur la plus proche de `avant`, même teinte, qui tient `mini` sur `arriere` : poussée vers le noir
- `questions_grille` — `skills/interface/scripts/atelier.py:1410` — Les questions fermées de la revue.
- `racine_de` — `skills/interface/scripts/atelier.py:1253`
- `reecrit_css` — `skills/interface/scripts/atelier.py:711` — Une passe sur le CSS : chaque `url()` et chaque chaîne d'`image-set()`/`src()` est un fichier local intégré,
- `revue` — `skills/interface/scripts/atelier.py:1509` — Calcule la note de la grille remplie et ajoute sa ligne sous `## Revue visuelle` de `navigation.md`.
- `section` — `skills/interface/scripts/atelier.py:1129`
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
