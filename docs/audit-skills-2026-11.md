# Audit des skills Hosa — novembre 2026

**Date :** 2026-11-12
**Référence :** commit `2b67566` (release 0.1.91, branche `master`).
**Périmètre :** les 43 skills de `skills/*/SKILL.md`, lus en entier. Contrôles croisés dans `skills/status/scripts/pipeline.json`, `skills/using-hosa/regles.md`, `skills/status/scripts/avancement.py`, `hooks/budget.js`, `hooks/gate.js`. Les agents (`agents/*.md`) sont lus seulement pour vérifier un constat précis.
**Deux regards :** spécialiste IA et Claude (construction du skill, contexte, coût en tokens, déclenchement, boucles), et spécialiste du métier de chaque skill (analyse fonctionnelle, sécurité, droit, QA, gestion de sprint, livraison).
**Grille :** les règles de `CLAUDE.md` (graphe et boucles), de `using-hosa` et de `regles.md`.

---

## 1. Verdict

**Hosa est solide sur le fond : le pipeline couvre le métier de bout en bout, et les garde-fous clés sont appliqués par du code.** Les meilleurs exemples : les ids `RGn`/`CEn` et `ticket_check --regles`, le juge `hosa-juge`, les preuves de `done`, la borne des revues FAIL dans `gate.js`, la démo humaine avant la fusion, les portes de livraison test/production.

**Les défauts viennent surtout de la dérive entre copies de texte.** Les skills ont été corrigés un par un. Les règles générales ont changé (checkpoints automatiques, tâches, enchaînement sans question). Plusieurs skills gardent l'ancienne version. Les défauts les plus graves :

1. **Une boucle hors du graphe** : l'audit de sprint renvoie à `develop` sans arête ni borne (X10).
2. **Un trou métier dans `changement`** : les tickets `todo` d'une exigence modifiée ne sont jamais réécrits (§ 6, `changement`).
3. **Des dispatches sans tâche** : 16 skills dispatchent des agents sans `task add`, et aucun hook ne le refuse (X1).
4. **Des étapes jamais fermées** : `qa`, `validation` et `bilan-sprint` n'appellent pas `done` (X2).
5. **Du travail d'agent dans la session principale, signé par un agent** : `interview`, `redaction`, `contestation` et `backlog` écrivent au nom de `hosa-product-owner` sans le dispatcher (X6).
6. **De l'état lu dans la mémoire de session** : 7 skills définissent leur périmètre par « dans cette session » (X5).

**Côté métier, quatre manques reviennent** : la capacité du sprint ignore la vitesse mesurée des sprints précédents, l'estimation a trois unités différentes, la reprise des données existantes n'est pas dans les fondamentaux, et une exigence modifiée laisse ses tickets `todo` dans l'ancienne version.

| Pipeline | Skills | Maturité | Défaut principal |
|---|---|---|---|
| Cahier des charges | 8 | ●●●●● | Session principale qui rédige au nom du PO (X6) |
| Structuration | 8 | ●●●●○ | Tâches absentes (X1), fins contradictoires (X3, X4) |
| Sprint | 9 | ●●●●○ | Boucle audit hors graphe (X10), étapes non fermées (X2) |
| Transverses | 11 | ●●●●○ | Trou métier de `changement`, références périmées (X7) |
| Génériques | 7 | ●●●○○ | Quiz « HARD-GATE » contraire à « Trust the user », textes en anglais |

**Vérifications.** Chaque constat cite son fichier et sa ligne. Un constat qui dépend d'un fichier non lu porte la mention « Non vérifié » ou « À vérifier ».

---

## 2. Constats transverses

Chaque constat a un id. Les fiches par skill (§ 4 à § 8) y renvoient.

### X1 — Dispatches sans `task add` / `task done`, et aucun code ne l'impose (grave)

**Règle :** `regles.md` § Plan : « A stage that dispatches agents lists each dispatch after its `start`: `task add` … `task done` ». `CLAUDE.md` : « Appliquées par du code, pas seulement écrites ».

**Constat :** 16 skills de pipeline dispatchent des agents sans nommer `task add` : `stack`, `infra`, `donnees`, `schema-app`, `schema-db`, `architecture`, `sprint`, `qa-plan`, `git`, `qualite` (audit), `validation`, `bilan-sprint`, `livraison`, `contestation`, `relecture` (le challenger), `changement`. Aucun hook ne refuse un dispatch sans tâche. `budget.js` l. 321-334 note chaque dispatch `hosa-*` en cours : la fiche montre alors « Agent encore actif », ce qui évite déjà un second dispatch du même travail.

**Effet :** un dispatch terminé ne laisse aucune tâche `fait` dans le plan. Ses sorties ne passent pas les contrôles de `task done` (`--sortie` existante, OKF, contrôles de `pipeline.json`). Après un `/clear`, la fiche ne sait pas quelles sous-étapes sont faites : la reprise relit les fichiers ou refait le travail.

**Correction :**
- Ajouter à chaque skill sa ligne **Tâches** (ids, agent, `--sortie`), sur le modèle de `juridique` l. 10.
- Ensuite seulement, ajouter dans `budget.js` un refus : un dispatch `hosa-*` pendant une étape `en cours`, sans tâche `à faire` de cet agent, est refusé une fois avec la commande `task add` à lancer. Exempter les checkpoints `hosa-git` Mode 3 et les relais (`hosa-infra` Mode 2, `hosa-documentation`, `hosa-dba` via `bdd`), ou leur donner des tâches. Fail-open, interrupteur `HOSA_TASKS=0`, test dans `budget.test.js`.

### X2 — Étapes de sprint jamais fermées (moyen)

**Constat :** `qa`, `validation` et `bilan-sprint` appellent `start` mais jamais `done <étape>` (vérifié : aucune occurrence dans les skills ni dans `hooks/*.js`). `avancement.py` ne ferme pas une étape tout seul. La fiche de reprise propose `done` seulement quand toutes les tâches et les preuves sont là (`avancement.py` l. 883-885), donc seulement après un `/clear`.

**Effet :** dans une session continue, l'étape reste `en cours`. Le `start` suivant est refusé. Le modèle improvise la fermeture.

**Correction :** donner à ces 3 skills le bloc **Plan d'avancement** standard, avec `done <étape> --sprint <slug>` à la fin.

### X3 — Fins contradictoires sur le commit (moyen, mécanique)

**Règle :** `regles.md` § Checkpoints : « Every skill that wrote files ends … by dispatching `hosa-git` … Never a question. »

**Constat :** ces skills disent encore « Report what changed and let the user decide when to commit » :
- `infra` l. 63, `sprint` l. 62, `qa-plan` l. 64, `qualite` l. 103, `bdd` l. 44 ;
- `backlog` l. 157, qui contredit son propre Step 8 (l. 140-142) ;
- `validation` l. 65 et `bilan-sprint` l. 51 (« You don't commit », sans checkpoint).

`kb-commit` l. 30 dit que les skills de pipeline le proposent et qu'il tourne « only when the user confirms ». Ce n'est plus vrai : les skills dispatchent `hosa-git` Mode 3.

**Correction :** remplacer chaque section « No Commits » par une ligne unique : « Commits : aucun ici. Le skill finit par le checkpoint `hosa-git` (`regles.md` § Checkpoints). » Mettre à jour `kb-commit` l. 30.

### X4 — « Propose d'enchaîner » contre « lancé sans attendre » (faible, mécanique)

**Règle :** « Chain, don't ask. »

**Constat :** le schéma `## Flow` dit « Propose… », la section `## Output` dit « lancé sans attendre » : `stack` l. 30, `infra` l. 23, `donnees` l. 26, `schema-app` l. 23, `schema-db` l. 24, `interface` l. 43, `backlog` l. 57, `qa-plan` l. 27, `relecture` l. 35 et l. 105.

**Effet :** le modèle lit deux consignes contraires. Il choisit parfois de demander, ce qui coûte un tour et un réveil.

**Correction :** aligner les schémas sur « Enchaîne sur `<étape>` ».

### X5 — État lu dans la mémoire de session (grave)

**Règle :** « L'état vit dans la KB. » « Une preuve se lit dans la KB, jamais dans la mémoire d'une session. » « One session per stage. »

**Constat :**
- `relecture` l. 46 : périmètre `p1` = « every Exigence written or changed in this session by `redaction`, `fondamentaux`, `juridique` and `securite` ». Avec une session par étape, cette liste est toujours vide.
- `contestation` l. 43 : « once per session, at the first entry » ; l. 79 : « at least one Exigence validated to stable in this session ».
- `donnees` l. 37 : « If `contestation` validated … earlier in this same session ».
- `changement` l. 87 : renvoie à ce même périmètre « session » de `relecture`.
- `qualite` l. 41 : « default to the files touched this session ».
- `qa` l. 72 : « flaky or slow across at least two of this session's runs ».

**Correction :** lire le périmètre dans la KB. Pour `relecture` p1 : les exigences `draft` de `kb/cdc/`, ou celles modifiées après le dernier `relecture.md` (comme le re-pass le fait déjà). Pour `contestation` : la porte Step 0 se lit sur le plan (`## Boucles` ouverte ou non). Pour `donnees` : les exigences `stable` sans annotation d'origine. Pour `qualite` : `git diff` depuis le dernier audit. Pour `qa` : les lignes `## Résultats techniques` des passes précédentes.

### X6 — Travail d'agent dans la session principale, signé par un agent (grave)

**Règle :** « Never do an agent's work in the main session. » OKF : `generated.by` dit qui a écrit.

**Constat :**
- `interview` écrit le compte rendu dans la session principale, avec `generated: { by: hosa-product-owner/1.0 }` (l. 128). Le schéma dit « PO relance » (l. 31), mais aucun PO n'est dispatché.
- `redaction` écrit les exigences, le glossaire et le modèle métier avec `by: hosa-product-owner/1.0` (l. 61, 158, 177), sans dispatch. `agents/product-owner.md` n'a aucune responsabilité de rédaction (vérifié). `redaction` l. 37 parle de « dispatch one pass per theme » sans agent à dispatcher.
- `contestation` Step 1 : « The PO always does its own quick pass » (l. 49), sans dispatch. Le schéma dit « PO passe les exigences en stable » (l. 31) ; Step 4 le fait dans la session.
- `backlog` Step 6 : « set each ticket's `estimate` yourself, in the senior dev role » (l. 134).

**Effet :**
- **Traçabilité fausse.** « Qui a demandé X ? » (`hosa`) répond « décidé par l'agent hosa-product-owner » pour un texte que la session a écrit.
- **Coût.** `redaction` est l'étape d'écriture la plus lourde. Elle charge tous les comptes rendus dans la session principale, relue à chaque tour.

**Correction (recommandée) :**
- Garder `interview` dans la session (c'est un dialogue). Signer le compte rendu `human:<user>` pour les réponses dictées, et `process:interview` pour la synthèse.
- Créer une responsabilité « Rédaction » dans `hosa-product-owner`. `redaction` la dispatche (Sonnet) avec les chemins des comptes rendus.
- `contestation` Step 1 : dispatcher `hosa-product-owner` pour sa passe, ou retirer le mot « PO » et dire que la session la fait.
- `backlog` Step 6 : l'estimation part dans la passe `stories-<k>`, ou dans une tâche `hosa-senior-dev`.

### X7 — Références mortes ou périmées (faible, mécanique)

- **« Example persona / example files »** (à vérifier) : `interview` l. 50, `recette` l. 38, `interface` l. 62, `build` l. 43, `understand` l. 39, `iterate` l. 36, `review` l. 36, et `agents/ux-designer.md`. `kb_branch.py init` ne crée aucun exemple. Mais `avancement.py check hosa` exclut encore `exemple-persona.md` (`hosa/app/test_avancement.py` l. 85-86) : d'anciens projets en ont peut-être un. Trouver d'abord qui créait ce fichier. S'il n'existe plus nulle part, remplacer « populated beyond its example files » par « `.hosa/kb/` existe ». Ce changement modifie le Step 0 de 4 skills génériques : ce n'est pas une correction de texte seul.
- **« Same as `stack` Step 1 »** : `qualite` l. 39 et `documentation` l. 28. Le Step 1 de `stack` est la question open source / SaaS. Remplacer par « lis le chemin racine dans `kb/infra/` ».
- **`validation` l. 33** : « proposé en Suite de `develop` ». La Suite de `develop` mène à l'audit.
- **`hosa` l. 225-227** (`## App`) : décrit des endpoints de l'app. Inutile au modèle qui exécute le skill. À retirer.
- **`hosa` l. 233** cite `Security Rule` ; le tableau l. 235-240 n'a pas de ligne pour lui.
- **`kb-commit` l. 60** : « the 12 agents that keep a memory ». Nombre écrit en dur, faux dès qu'un agent change.

### X8 — Dispatches en série là où la règle est le parallèle ou le lot (moyen, coût)

**Règle :** `regles.md` § Réveils : « Dispatch a stage's independent agents in one message. » Chaque réveil relit tout le contexte (49-66 % des tokens de la session principale).

**Constat :**
- `interface` l. 66 : « One persona at a time — don't batch multiple personas into a single dispatch ». La phrase se lit comme « en série ». Les personas sont indépendants.
- `donnees` l. 43 : « One item at a time — don't batch multiple ambiguous items into a single dispatch ». Un dispatch par donnée ambiguë. `interview` et `contestation` font l'inverse : un dispatch par persona, toutes ses questions dedans.
- `qa-plan` l. 46 : un `hosa-qa-lead` par ticket.
- `validation` l. 41-43 : un `hosa-product-owner` par ticket. `develop` et `qa` travaillent par lot.

**Correction :** `interface` : un dispatch par persona, tous dans un message. `donnees` : un dispatch par persona avec toutes ses données. `qa-plan` et `validation` : un dispatch par lot (4 tickets au plus), un verdict par ticket. Garder `qa` Step 4 en série : les personas partagent l'environnement.

### X9 — Questions et textes hors du standard `retours` (faible)

- `stack` l. 43-46 : options numérotées 1, 2, 3, sans lettres. `retours` § 3 : lettres, la recommandée en `a)`.
- Les skills génériques donnent des phrases toutes faites en anglais (`understand` l. 126 et 145, `build` l. 90 et 109, `debug` l. 65 et 74, `review` l. 89, `test` l. 56). `retours` impose le français.

### X10 — Boucles hors du graphe ou sans borne (grave)

**Règle :** « Chaque retour en arrière est une arête » déclarée dans `pipeline.json`, avec sa borne appliquée par du code.

**Constat :**
- **Audit de sprint → `develop`.** `qualite` l. 97 : un Bloquant de l'audit part en `develop <ticket> correction`, puis un nouvel audit. `pipeline.json` n'a aucune boucle `from: "audit"` (vérifié). Aucun `back`, donc aucun compte de tours. La borne de `gate.js` compte les revues FAIL, pas les audits Bloquant. `qualite` l. 94 cite lui-même le cas pilot2 : « at that rate a sprint never closes ».
- **`schema-db` Step 1b** (l. 44) : « A migration it can't apply or reverse sends the work back to Step 1 — the stage isn't done until both agree ». Boucle interne sans borne.
- **`schema-db` → `donnees`** (l. 40) : « propose running `donnees` first », sans `back`. `schema-app` le fait bien (l. 38). Il n'y a pas d'arête `schema-db → donnees`.
- **`review`** (générique) : borne de 3 cycles au schéma (l. 28) et à l'en-tête (l. 80), de 2 au Step 4 (l. 88). Le compteur vit dans la session.

**Correction :**
- Ajouter `{"from": "audit", "to": ["develop"], "max": 2}` et faire appeler `back audit develop --sprint <slug> --ticket <t> --cause <Bn>` par `qualite`. `skills/develop/correction.md` point 6 décrit ce même chemin (« Correction d'un Bloquant de l'audit du sprint … → ré-audit seulement ») : le mettre à jour aussi. Ajouter un test à `hosa/app/test_avancement.py`, et vérifier le test qui compare la prose au graphe.
- `schema-db` : compter les allers-retours `hosa-dba` → `hosa-data-engineer` comme tâches (`task add schema-db migrations`, contrôle `max`), et ajouter l'arête `schema-db → donnees`.
- `review` : une seule borne, 2.

### X11 — Le même paragraphe copié 23 fois (faible, entretien)

Le bloc « Plan d'avancement » (≈ 700 caractères, qui finit par « Never skip these calls ») est copié dans 20 skills. Chaque skill ne se charge qu'avec lui-même : le coût en tokens reste faible. Le vrai coût est l'entretien : X3 et X4 viennent de copies que personne n'a mises à jour.

La phrase finale « the session stays on the wrong model » n'est pas expliquée. Un modèle qui ne comprend pas la raison d'une règle la suit moins bien.

**Correction :** une forme courte et identique partout : « **Plan :** étape `<x>` — `start`, `block`, `done` (`regles.md` § Plan). » La raison va une fois dans `regles.md`. Un test (comme celui de la prose du graphe) vérifie que chaque skill d'étape a ce bloc.

### X12 — Langue des consignes (faible)

`develop` mélange un corps français (Steps 1-6, Lot Mode) et des passages anglais (Steps 3a-4c, Reprise). Les autres skills donnent leurs consignes en anglais et leurs modèles en français. Choisir une règle et l'appliquer : consignes en anglais, modèles et textes pour l'utilisateur en français.

### X13 — Contenu au lieu de chemins entre agents (moyen)

**Règle :** « Entre agents, des chemins. » `retours` § 4 : le rapport ne garde que ce que la session utilise.

- `contestation` l. 53 : « Dispatch `hosa-challenger` with the full content of `.hosa/kb/cdc/` ». Sortie l. 93 : « [Its full report] ».
- `git` sortie l. 60 : « [hosa-git's Output Format] », recopié tel quel.
- `review` l. 51 et `build` l. 57 : « The full spec file content ».

**Correction :** passer les chemins, et ne garder dans la sortie que le verdict, les anomalies routées et les questions.

---

## 3. Construction IA : bilan général

**Ce qui est bon :**
- **Descriptions** : forme « Use to … Triggers: … » partout, avec des déclencheurs en français. C'est ce qui fait choisir le bon skill.
- **Divulgation progressive** : `backlog` → `redaction-tickets.md`, `develop` → `correction.md` et `blocages.md`, `fondamentaux` → `socle-comptes.md`, `using-hosa` → `regles.md`. Le modèle ne lit le détail qu'à l'étape qui en a besoin.
- **Sorties vérifiables** : `cdc check`, `cdc revue`, `ticket_check`, `interface_check`, `lexique_check`, le juge, les preuves de `done`.
- **Indépendance des relectures** : challenger sans le document assemblé, revue visuelle sans le raisonnement du designer, revue de correction sur le diff seul.
- **Choix du modèle par tâche** : Sonnet pour la classification et les notes de tickets, Haiku pour les checkpoints, Opus pour le jugement de couverture.

**Ce qui peut progresser :**
- **Taille des plus gros skills.** `redaction` (18 Ko), `backlog` (17,3 Ko), `develop` (16,6 Ko), `hosa` (16,6 Ko), `relecture` (16 Ko), `interview` (15,7 Ko). Leurs modèles de fichiers (identité, exigence, modèle métier, journal des décisions, compte rendu) peuvent partir dans des fichiers de référence lus à l'étape. Non vérifié : je ne cite pas de seuil officiel d'Anthropic, mais le principe de divulgation progressive s'applique.
- **Anecdotes de projets** (rieki, pilot2, hosa-ui) dans 12 skills. Elles donnent la raison d'une règle : c'est utile. Les garder en une proposition courte, sans les chiffres secondaires.
- **Descriptions des skills génériques** sans déclencheurs français (`understand`, `build`, `iterate`, `debug`, `test`, `review`, `dispatch`). Un utilisateur francophone qui dit « j'ai une idée » ou « ça plante » les déclenche moins sûrement.

---

## 4. Pipeline 1 — Cahier des charges

### `hosa`
- **IA.** Bon découpage en flux (init, mise à jour, concept libre, traçabilité). La reprise est bien pensée : `identity.md` écrit dès la question 5, reprise à la première section `À compléter.`.
- **Métier.** Les 15 questions couvrent un cadrage de projet sérieux (contexte, objectifs mesurables, non-objectifs, hypothèses et risques). Deux manques :
  - **Le décideur.** Aucune question sur qui signe le cahier des charges et arbitre le périmètre (sponsor, client). `contestation` fait signer « l'utilisateur » ; dans un projet pour un client, ce n'est pas la même personne.
  - **La taille** n'a que `petit` / `standard`. Un projet multi-équipes ou multi-produits n'a pas de réglage.
- **Cohérence.**
  - Le modèle d'`identity.md` montre `status: stable` (l. 115) ; le texte dit de l'écrire `draft` d'abord (l. 12). Le modèle d'un persona montre `status: stable` avant son enrichissement (l. 182).
  - `mkdir -p .hosa/kb/project/` (l. 106) : chemin relatif. `regles.md` § KB demande des chemins absolus.
  - X7 (`## App`, `Security Rule`).
- **Bilan.** Bon skill d'ouverture. À corriger : statuts des modèles, chemin absolu, question du décideur.

### `interview`
- **IA.** Très bon. La distinction « tenu / déduit » et la marque `[à confirmer]` empêchent l'agent persona d'inventer. Une question à la fois pour les questions ouvertes, groupées pour les confirmations : bon équilibre.
- **Métier.** Les questions par processus sont celles d'un analyste métier expérimenté (déclencheur, fréquence et volumes, règles, cas d'erreur, objets métier et cycles de vie). `hosa` Q12 demande les dépendances, et `interview` demande l'outil actuel de chaque processus. Mais deux trous classiques d'un cahier des charges ne sont pas posés comme tels :
  - **Les intégrations** : quels systèmes l'application remplace, alimente ou lit (ERP, tableur, messagerie, API d'un tiers), avec le sens et la fréquence des échanges.
  - **La reprise des données** de l'outil actuel au démarrage (volume, qualité, qui la valide).
- **Cohérence.** X6 (compte rendu signé PO, « PO relance »). X7 (« other than the example », l. 50).
- **Bilan.** Excellent. Ajouter une question transverse « systèmes existants et reprise des données » au Step 4. Corriger la signature.

### `redaction`
- **IA.** Règles très précises : un fait à une seule place, ids `RGn`/`CEn` stables, marque `[à confirmer]` conservée, mode « Fixing a relecture » économe (une lecture et une édition par fichier). Le skill est le plus long de Hosa (18 Ko) : ses modèles (exigence processus, NFR, glossaire, modèle métier, décisions) peuvent partir dans un fichier de référence.
- **Métier.** Le modèle d'exigence est celui d'une bonne spécification fonctionnelle. Le modèle métier (états, droits CRUD, notifications) trouve les processus oubliés : c'est le meilleur outil du pipeline.
- **Cohérence.** X6 (signé PO sans dispatch ; « dispatch one pass per theme », l. 37, sans agent).
- **Bilan.** Très bon sur le fond. Le défaut est d'architecture : faire la rédaction par un agent.

### `fondamentaux`
- **IA.** Bon : la liste est passée telle quelle, le socle comptes est copié et non réécrit, `## Choix validés` est écrit avant l'écriture finale pour qu'une session coupée reprenne.
- **Métier.**
  - **Chevauchement avec `juridique`.** La ligne NFR « Protection des données (RGPD) : base légale, durée de rétention, droit d'accès » (l. 72) est le cœur du métier de `juridique`. Deux étapes décident la même chose : risque de contradiction entre deux exigences.
  - **Manques dans la liste :** reprise des données de l'existant ; fichiers et pièces jointes (stockage, taille, formats, antivirus) ; langues et fuseaux horaires ; quotas et limites d'usage.
  - **Charge du Step 3.** Un seul tour pose : les manquants, les chiffres NFR, priorités et lots, les variantes et paramètres du socle, la matrice des rôles, et le contexte juridique et sécurité. C'est économe en tokens, mais lourd pour un `débutant`.
- **Cohérence.** Le déclencheur « every time it writes new exigences » (l. 36) contredit le graphe : les boucles `relecture → redaction` ne relancent pas `fondamentaux`.
- **Bilan.** Bon. Retirer la ligne RGPD (renvoyer à `juridique`), compléter la liste, couper le Step 3 en deux tours pour un `débutant`.

### `juridique`
- **IA.** Propre : deux phases, `## Choix validés` avant l'écriture, mode Livraison hors étape et dit tel quel.
- **Métier.** Bon réflexe de juriste : obligations incluses par défaut, retrait seulement avec une raison écrite, avertissement « ne remplace pas un avocat ou un DPO », documents hors logiciel listés, dérogation écrite au nom de l'utilisateur. La porte juridique seulement en production est juste.
- **Cohérence.** No-Go : le ticket est créé avec `priority: 1`, puis le Single-Ticket Mode redemande une priorité (l. 67). Petit doublon.
- **Bilan.** Bon. Rien de grave.

### `securite`
- **IA.** Quatre modes clairs, deux étapes distinctes dans le plan (`securite`, `menaces`), tâches nommées.
- **Métier.** Démarche d'expert : exigences au cahier des charges, STRIDE et cas d'abus sur l'architecture réelle, cas d'abus devenus critères puis tests, audit avec preuve, Go/No-Go à la livraison. La consigne sur un secret poussé (« rotation d'abord ») est la bonne. Suggestion : le modèle de menaces peut demander un chiffrement de colonne ou un cloisonnement de données ; il n'a d'arête que vers `architecture`. Une arête `menaces → schema-db` serait utile.
- **Cohérence.** Mode Audit : un Bloquant donne un ticket via `hosa-product-owner` (bien), sans `task add` (X1, hors étape : acceptable).
- **Bilan.** Très bon.

### `relecture`
- **IA.** Le meilleur skill de boucle de Hosa : gravité (`bloquante` / `mineure`), origine (`texte` / `correction` / `regle-hosa`), passes numérotées, contrôleur `cdc revue`, mesure `cdc mesure` qui montre si les corrections créent des défauts. Le challenger tourne sur Sonnet, avec les chemins.
- **Métier.** Le critère de gravité (« un développeur ou un testeur construirait-il la mauvaise chose ? ») est le bon.
- **Cohérence.** X5 (périmètre `p1` « in this session », l. 46). X4 (« propose », l. 35 et 105).
- **Bilan.** Excellent. Corriger le périmètre `p1`.

### `contestation`
- **IA.** Bonne idée : deux contestations indépendantes, porte `fondamentaux` / `juridique` / `securite` lue sur les dates, signature du document et non d'une liste de fichiers.
- **Métier.** C'est la recette du cahier des charges : la signature fait passer en `stable` avec `verified: human`. Juste.
- **Cohérence.** X5 (l. 43, l. 79). X6 (passe PO et passage en `stable` dans la session). X13 (« full content », « Its full report »). X1 (challenger sans tâche).
- **Bilan.** Bon sur le fond, à remettre en ligne avec les règles d'orchestration.

---

## 5. Pipeline 2 — Structuration

### `stack`
- **IA.** Court et net : la session demande, `hosa-senior-dev` propose et enregistre, `hosa-documentation` écrit l'ADR.
- **Métier.** Bon : `hosa-senior-dev` propose 2-3 options par catégorie, hébergement compris (`agents/senior-dev.md` l. 40), et écarte une option qui viole une contrainte de sécurité (localisation des données réglementées). Suggestion : les cibles concrètes (test, production, accès) ne sont définies qu'à la première livraison (`livraison` Step 6). Une cible de test définie avant le premier sprint permettrait des démos sur un vrai environnement.
- **Cohérence.** X9 (options 1/2/3). X1. X4 (l. 30).
- **Bilan.** Bon.

### `infra`
- **IA.** Bon : l'outillage qualité (tests, lint, types, CI) fait partie de l'étape, et `git` Mode 1 le vérifie avant un sprint.
- **Métier.** Juste : versions épinglées, Docker partout, CI dès le départ.
- **Cohérence.** X3 (l. 63). X4 (l. 23). X1. Modes présentés dans l'ordre 1, 3, 2.
- **Bilan.** Bon. Corrections mécaniques.

### `donnees`
- **IA.** Court. Sonnet pour la classification : bon choix.
- **Métier.** La qualification générée / fournie / saisie est utile. Point de fond : l'agent « writes each annotation in place » (l. 49) dans des exigences **signées** (`stable`, `verified: human`). OKF dit qu'une réécriture du contenu retire `verified`. Soit l'annotation casse la signature, soit `verified` couvre un texte que l'utilisateur n'a pas vu. Mettre l'origine dans un champ de frontmatter hors signature, ou dans `kb/donnees/origines.md`.
- **Cohérence.** X8 (un dispatch par donnée). X5 (l. 37). X1. X4.
- **Bilan.** À revoir : un dispatch par persona, et l'annotation hors du texte signé.

### `schema-app`
- **IA / métier.** Propre. Bonne règle : la documentation reçoit des chemins, jamais les champs réécrits. `back schema-app donnees` est bien appelé.
- **Cohérence.** X1. X4.
- **Bilan.** Bon.

### `schema-db`
- **Métier.** Bonne séparation : `hosa-data-engineer` conçoit, `hosa-dba` applique et prouve l'aller-retour des migrations. Point de fond : si aucune `Stack Decision` ne fixe la base de données, `hosa-data-engineer` l'enregistre lui-même (l. 38). Ce choix revient à `stack` (`hosa-senior-dev`, options et compromis). Renvoyer à `stack`.
- **Cohérence.** X10 (boucle Step 1b ↔ Step 1 sans borne ; renvoi à `donnees` sans `back`). X1. X4.
- **Bilan.** À corriger : arêtes et bornes, choix du moteur rendu à `stack`.

### `architecture`
- **IA / métier.** Bon : socle d'observabilité dès le départ (corrélation, logs structurés, métriques RED, symptômes alertables), titre fixe `## Documentation d'architecture` pour les lecteurs suivants, enchaînement sur le modèle de menaces.
- **Cohérence.** X1.
- **Bilan.** Bon.

### `interface`
- **IA.** Très travaillé : trois manches de choix sur des pages de comparaison, trois passages 3a/3b/3c pour tenir sous le plafond d'appels, contrôleurs `interface_check` et `lexique_check` liés à `task done`, revue visuelle indépendante notée sur 10 avec une borne.
- **Métier.** Démarche d'UX designer solide : interviews des personas, navigation par rôle en arbre, lexique fixé avant les écrans, front et back office.
- **Cohérence.** X8 (l. 66). X4 (l. 43). X7 (« only the example persona », l. 62).
- **Bilan.** Excellent. Paralléliser les interviews.

### `backlog`
- **IA.** Le skill le plus abouti pour tenir le coût : lots de 8 tickets, graphe de 4 tâches, juge en dernier, deux agents à la fois, Sonnet pour les notes, `ticket_check --regles` pour la matrice règles × critères.
- **Métier.**
  - **Notes techniques en jeu de rôle.** La note technique, le placement architecture et le placement interface sont écrits par `hosa-product-owner` « dans le rôle » du senior dev, de l'architecte et du designer. La forme est contrôlée : la Grounding Rule (`redaction-tickets.md` l. 54-62) exige une référence réelle par puce, et `ticket_check` liste les chemins cités qui n'existent pas. Le fond ne l'est pas : le juge n'a aucune question sur ces notes (`pipeline.json`). Une faisabilité mal jugée passe. Suggestion : une question du juge sur la note technique, ou une passe `hosa-senior-dev` sur les tickets d'estimation 3.
  - **Trois unités d'estimation.** `backlog` écrit `estimate` 1, 2 ou 3 (½ jour, 1 jour, 2-3 jours, l. 134). `hosa-sprint-planner` lit S, M, L (`agents/sprint-planner.md` l. 17). `develop` compose ses lots en « points » (l. 80). Choisir une unité et l'écrire aux trois endroits.
- **Cohérence.** Le schéma `## Flow` (l. 24-58) décrit l'ancien déroulé séquentiel, pas le graphe des 4 tâches. X3 (l. 157 contre Step 8). X6 (estimation dans la session).
- **Bilan.** Très bon sur le contrôle, à compléter sur les notes techniques.

---

## 6. Pipeline 3 — Sprint

### `sprint`
- **IA.** Bon : préconditions vérifiées (outillage qualité, modèle de menaces), puis `qa-plan`, `git` et `develop` sans question.
- **Métier.** **La capacité ignore la vitesse mesurée.** Sans capacité donnée, `hosa-sprint-planner` prend la règle `kb/rules/design/cadence-des-sprints.md`, sinon ce que les estimations remplissent en une semaine (`agents/sprint-planner.md` l. 17). Il ne lit pas les sprints précédents. Or `bilan-sprint` mesure chaque sprint (`## Mesures`). Proposer comme capacité la moyenne livrée sur les 2 derniers sprints, et le dire. Voir aussi les trois unités d'estimation (`backlog`).
- **Cohérence.** X1. X3 (l. 62). La sortie dit « `develop lot` » (l. 83) ; le Step 4 dit « the first ticket » (l. 58).
- **Bilan.** Bon. Brancher la vélocité.

### `qa-plan`
- **IA / métier.** Très bon : un plan par ticket avant le sprint, tests `[sécurité]`, `[navigateur]`, `[nfr]`, jeu de données qui couvre chaque `CAn` (ou dit pourquoi il ne peut pas). C'est la pratique d'un responsable QA sérieux.
- **Cohérence.** X1. X3 (l. 64). X4 (l. 27). X8 (un dispatch par ticket).
- **Bilan.** Bon. Dispatcher par lot.

### `git`
- **IA.** Court. Relais bien décrits (`## Installation nécessaire`, `## Base de données nécessaire`, réserves de validation).
- **Métier.** Bon : le démarrage vérifie l'outillage qualité et les plans de test, la fusion vérifie la démo, l'audit (`Bloquant : 0`) et les réserves de validation.
- **Cohérence.** Pas de bloc Plan d'avancement standard (le Step 1b le remplace). X1. X13 (sortie recopiée).
- **Bilan.** Bon.

### `develop`
- **IA.** Le cœur de Hosa, très mûr : tests d'abord par un autre agent, lots de tâches d'un même module, un seul lot à la fois, Sonnet sur une règle de sécurité, revue indépendante, borne des FAIL dans `gate.js`, trailer `Hosa-Ticket:`, une session par lot.
- **Métier.** Bonne discipline d'équipe : le développeur ne modifie pas un test qui lui paraît faux (c'est un `Blocked`), worktree propre avant le ticket suivant.
- **Cohérence.** X12 (français et anglais mélangés). Sinon rien.
- **Bilan.** Excellent.

### `qualite`
- **IA.** Bon : trois audits en parallèle, règle d'honnêteté des métriques, Bloquant avec sa preuve, re-audit limité à la correction.
- **Métier.** La classe « Prérequis de livraison » (ne bloque pas la fusion, bloque la production) est une très bonne idée. La duplication vérifiée sur tout le code, même sur un audit limité, aussi.
- **Cohérence.**
  - **X10 : la boucle audit → `develop` n'est pas une arête.** C'est le défaut le plus grave de l'audit.
  - X5 (l. 41). X7 (l. 39). X3 (l. 103). X1.
  - La sortie propose « Je lance `debug` sur le ticket ? » (l. 125). Dans un projet Hosa, un ticket hors sprint va au prochain `sprint`, et un ticket du sprint va en `develop … correction`. `debug` est le skill générique.
- **Bilan.** Bon, sauf la boucle.

### `qa`
- **IA.** Bon : tâches bien nommées, suite complète une seule fois par passe, `Arbre testé` réutilisé à la fusion, commits de tests propres.
- **Métier.** Bonne séparation : défaut (`Non` sur un `CAn`) corrigé dans le sprint, besoin nouveau mis au backlog, irritant noté sans correction. La recette par un agent persona reste une simulation ; la démo humaine dans `validation` compense. Bien.
- **Cohérence.** X2 (pas de `done qa`). X5 (l. 72). Numérotation : pas de Step 2.
- **Bilan.** Très bon. Ajouter `done`.

### `validation`
- **IA.** Le mode « Reconfirmation » sur Haiku après une correction technique est une bonne économie.
- **Métier.** Bon : acceptation par le PO sur les preuves (un critère prouvé seulement en lisant le code n'est pas prouvé), puis démo par une vraie personne, avec des tests T1… cliquables.
- **Cohérence.** X2 (pas de `done validation`). X1. X8 (un PO par ticket). L'étape est par sprint, mais le skill est écrit par ticket ; rien ne dit comment enchaîner tous les tickets du sprint après `qa`. Ajouter un mode sprint : un dispatch par lot, puis la démo. X3 (l. 65). X7 (l. 33).
- **Bilan.** Bon sur le fond. À réécrire autour du sprint.

### `bilan-sprint`
- **IA.** Bon : mesures objectives (`usage_report`), mesure des questions suivies, propositions jamais appliquées sans l'utilisateur.
- **Métier.** **La rétro ne demande pas l'avis de l'utilisateur** (non vérifié dans la responsabilité 7 de `agents/product-owner.md` ; le skill ne le demande pas). Le PO juge l'objectif et les frictions à partir des fichiers, et ses `## Open Questions` portent sur ses propositions. Une rétrospective demande aussi à l'équipe ce qui l'a gênée ou aidée. Ajouter une question ouverte non bloquante (« Qu'est-ce qui t'a gêné ou aidé ce sprint ? »). La réponse va au bilan et à `kb/retours-hosa/journal.md`. Sortir aussi la vélocité du sprint pour le `sprint` suivant.
- **Cohérence.** X2 (pas de `done bilan-sprint`). X3 (l. 51). X1.
- **Bilan.** Bon. Ajouter la voix de l'utilisateur et la vélocité.

### `livraison`
- **IA.** Long mais clair. Le tableau test / production dit exactement ce qui bloque. La promotion réutilise la version testée sans tout refaire.
- **Métier.** Niveau d'un responsable de mise en production : audits de sprint réutilisés, portes sécurité et juridique, sauvegarde vérifiée avant migration en production, retour arrière écrit avant la livraison, vérification après déploiement, version jamais devinée, push seulement sur demande.
- **Cohérence.** X1 (aucune tâche pour `hosa-documentation`, `hosa-git`, `hosa-dba`, `hosa-infra`).
- **Bilan.** Excellent.

---

## 7. Skills transverses

### `changement`
- **IA.** Bon : graphe du projet pour l'impact, agents en lecture seule pour l'analyse, boucle propre déclarée (`back changement changement --objet`), vérification de faisabilité de la plateforme.
- **Métier.** **Trou de logique.** Step 2 dit des tickets `todo` : « nothing built yet … it'll just be re-derived » (l. 51). Mais `backlog` Step 1 saute toute exigence qui a déjà un ticket lié, et ne réécrit jamais un ticket (« never recreates or overwrites a ticket »). Le mode « refine » ne corrige que les notes, pas la story ni les critères. **Résultat : un ticket `todo` garde l'ancienne version de l'exigence, et un sprint peut le développer.** Correction : au Step 7, dispatcher `hosa-product-owner` pour réécrire story et critères de chaque ticket `todo` lié, puis relancer le juge sur ces tickets.
- **Métier, autre point.** Rien ne dit quoi faire d'un ticket `doing` du sprint actif touché par le changement : le mettre en pause, ou le corriger dans le sprint.
- **Cohérence.** X5 (l. 87). X1.
- **Bilan.** Bon outil, avec un trou qui fait livrer l'ancien besoin. À corriger en priorité.

### `reprendre`
- **IA.** Court et efficace : une seule commande, puis l'action. Le cas « agent encore actif » évite un second dispatch.
- **Métier.** C'est la passation entre deux sessions : la fiche dit l'étape, la tâche et l'action suivante, comme une bonne note de relève.
- **Bilan.** Propre. Raccourcir l'anecdote d'ouverture (l. 8).

### `status`
- **IA.** Bon : `avancement show` d'abord, lecture directe sans agent, mesures (consommation, juge, questions).
- **Cohérence.** **Le mode générique lit la KB.** Les lignes « Sécurité » (`kb/securite/…`) et « Retours Hosa » (`kb/retours-hosa/journal.md`) sont dans `## Mode Générique` (l. 112-114), qui ne s'applique que sans `.hosa/kb/`. Elles doivent aller dans le mode Hosa et sa sortie.
- **Bilan.** Bon. Déplacer ces deux lignes.

### `recette`
- **Métier.** Bon principe (vérifier que le logiciel sert la personne, pas seulement qu'il marche).
- **Cohérence.**
  - **Format.** `qa` l. 62 écrit les recettes « in the exact format `recette` uses », avec un `Oui` / `Non` / `Non observé` par `CAn`. Le modèle de `recette` (l. 65) n'a pas ce format : « corps : scénarios, pain points… ». Une recette lancée seule ne sert donc pas de preuve à `validation`.
  - **Routage.** Un défaut part en ticket et `debug` (l. 78). Dans le sprint actif, `qa` l'envoie en `develop <ticket> correction`. Aligner.
  - L. 46 : « confirm before treating as written » puis « not a blocking gate ». Les deux phrases se contredisent.
  - X7 (« non-example persona »).
- **Bilan.** À aligner sur le format et le routage de `qa`.

### `bdd`
- **Métier.** Un administrateur de bases de données y trouve ses sujets : migrations et conflits entre branches, base de test isolée, sauvegarde et restauration, requête lente, verrou. Le partage des rôles est net (`hosa-data-engineer` conçoit, `hosa-infra` installe, `hosa-dba` opère). La restauration testée est prévue par `schema-db` et `livraison`, pas ici : normal pour un point d'entrée.
- **Bilan.** Propre et court. X3 (l. 44).

### `documentation`
- **Métier.** Un rédacteur technique vérifie que la documentation suit le code. Le contrôle par dates (source plus récente que `generated.at`) trouve la dérive. Il ne trouve pas une doc fausse dès l'écriture : c'est le rôle des producteurs en Mode 1. La règle « source sans date = non vérifiable » est honnête.
- **Bilan.** Propre. X7 (l. 28).

### `kb-commit`
- **Métier.** Bonne pratique de gestion de configuration : la KB vit sur sa propre branche, chaque commit KB cite le commit de code (`Hosa-Code-Commit`), la migration vérifie le contenu octet par octet avant de supprimer quoi que ce soit.
- **Bilan.** Propre. X3 (l. 30), X7 (l. 60).

### `okf`
- **IA.** Règles nettes (type obligatoire, slug, niveau de confiance, log court), validateur obligatoire, `kb_query` pour lire peu.
- **Métier.** Le niveau de confiance (`generated` / `verified`, et la règle « réécrire retire `verified` ») est celui d'un vrai référentiel documentaire. C'est cette règle que `donnees` contredit.
- **Bilan.** Propre.

### `retours`
- **IA.** Standard de rédaction très utile : réponse en première ligne, ASD-STE100, questions `Q1 a)`, tests `T1`. La règle « la recommandée toujours en `a)` » vient d'une mesure réelle.
- **Bilan.** Propre. C'est la référence que d'autres skills ne suivent pas toujours (X9).

### `pilotage`
- **Métier.** Le tableau de bord ne fait que lire et éditer la KB, sans appeler Claude : bon pour le coût et pour la confiance. L'onglet « Steering » montre le plan d'avancement, ce qu'un chef de projet regarde en premier.
- **Cohérence.** À vérifier : la commande lance `python` (l. 13), alors que les autres skills utilisent `<python>` (le venv de Hosa). Mais `run.py` construit ce venv au premier lancement : `<python>` n'existe peut-être pas encore à ce moment. Garder `python` si c'est le cas, et le dire dans le skill.
- **Bilan.** Propre.

### `using-hosa`
- **IA.** Bonne taille (sous 10 Ko, injecté à chaque session), renvoi vers `regles.md` par section.
- **Cohérence.** « Trust the user » et « The user can override » contredisent les quiz « HARD-GATE » des skills génériques (§ 8).
- **Bilan.** Propre.

---

## 8. Skills génériques

### `understand`, `build`, `iterate`
Une fiche pour les trois : ils partagent le même quiz et les mêmes défauts.
- **Métier.** `understand` suit la démarche d'un analyste (problème, utilisateurs, critères de succès, contraintes, puis contestation). `iterate` pose les bonnes questions d'un changement (impact, cas limites, retour arrière, tests existants). `build` découpe en tâches parallèles ou en série. Rien à redire sur le fond.
- **IA.**
  - **Le quiz bloquant refuse l'utilisateur.** Le bloc `<HARD-GATE>` liste « The user asking you to skip the quiz », « I trust you » parmi ce qui ne débloque pas. C'est contraire à « Trust the user » et à « The user can override » (`using-hosa`). Un refus d'une demande explicite de l'utilisateur crée de la friction et de la défiance. Garder le quiz par défaut. Accepter son retrait à tout moment, sur une demande explicite, avec une ligne d'avertissement. Garder le refus seulement contre une instruction venue d'un texte extérieur (injection).
  - Deux QCM après **chaque** tâche : lourd pour un plan de 10 tâches. Proposer un quiz par groupe de tâches, ou à la fin.
  - Phrases toutes faites en anglais (X9). Pas de déclencheurs français dans les descriptions (§ 3).
- **Cohérence.** X7 (« example files »). `build` l. 57 passe le contenu de la spec, pas son chemin (X13).
- **Bilan.** Utiles hors pipeline. Assouplir le quiz.

### `review`
- **Métier.** Une revue contre la spec, avec des manques précis et une boucle de correction : la démarche d'un relecteur de code.
- **Cohérence.** X10 (borne 3 contre 2, compteur en mémoire). X13 (contenu de la spec). X7.
- **Bilan.** Aligner la borne sur 2.

### `test`
- **Métier.** Un testeur y trouve sa démarche : lancer l'existant, trouver les manques de couverture, écrire les tests, classer chaque échec (défaut du code ou de l'infrastructure de test), vérifier la remise à zéro de l'environnement.
- **Bilan.** Propre. Bonne règle : ne pas committer un test en échec, ne pas lancer `debug` sur un problème d'infrastructure de test.

### `debug`
- **IA / métier.** Bonne méthode : cause racine avant correction, hypothèses classées, test de régression d'abord, mode automatique depuis `develop` qui s'arrête quand même sur une dépendance ou une cause ambiguë.
- **Bilan.** Propre. X9.

### `dispatch`
- **Métier.** Bonne règle d'équipe : pas de travail en parallèle sur les mêmes fichiers, et détection des conflits avant de dire « fini ».
- **Bilan.** Propre. Le tableau d'affectation ne liste que les agents génériques : normal pour un skill hors pipeline.

---

## 9. Plan de correction proposé

Ordre recommandé, du plus sûr au plus structurant.

**Lot A — corrections de texte, sans changement de comportement.** Fait le 2026-11-12 (98 tests des hooks et 304 tests de l'app passent). X3, X4, X9 (`stack`), X12, X7 sauf les « example files » (références à `stack` Step 1, `validation` l. 33, `hosa` `## App` et `Security Rule`, `kb-commit` l. 60), `status` (lignes du mode générique), `backlog` (schéma `## Flow`), `review` (borne 2), `hosa` (statuts des modèles, chemin absolu), `qa` (numérotation), `fondamentaux` (déclencheur).

**À vérifier avant de corriger.** X7 « example files » (qui créait `exemple-persona.md` ?), `pilotage` (`python` ou `<python>`).

**Lot B — graphe et boucles (code et tests).**
- X10 : arête `audit → develop`, appel `back` dans `qualite`, arête `schema-db → donnees`, borne de `schema-db` Step 1b.
- X2 : `done` dans `qa`, `validation`, `bilan-sprint`.
- X1 : lignes **Tâches** dans les 16 skills, puis le refus dans `budget.js` avec son interrupteur et son test.
- X5 : périmètres lus dans la KB.

**Lot C — logique métier.**
- `changement` : réécrire les tickets `todo` liés.
- `donnees` : annotation hors du texte signé.
- `sprint` + `bilan-sprint` : vitesse mesurée ; `backlog` + `sprint-planner` + `develop` : une seule unité d'estimation.
- `interview` + `fondamentaux` : systèmes existants, reprise des données, fichiers, langues ; ligne RGPD rendue à `juridique`.
- `bilan-sprint` : question de rétro à l'utilisateur.
- `backlog` : question du juge sur la note technique.
- `recette` : format `CAn` et routage de `qa`.
- `hosa` : question du décideur.

**Lot D — architecture des agents et coût.**
- X6 : responsabilité « Rédaction » de `hosa-product-owner`, signatures exactes.
- X8 : dispatches par persona et par lot.
- X13 : chemins entre agents.
- Quiz des skills génériques.
- Modèles des gros skills sortis dans des fichiers de référence ; bloc Plan court (X11) avec son test.
