# Audit Hosa — agents et skills

**Date :** 2026-09-27
**Périmètre :** `agents/` (19 fichiers + README), `skills/` (31 skills), specs `docs/specs/`, KB `hosa/kb/`, app `hosa/app/`.
**Référence :** commit `5e59439` (branche `master`).
**Objectif évalué :** fournir tous les éléments pour **définir les objectifs d'un projet, le développer et le suivre**, dans un workflow piloté par l'IA.

**Méthode :** j'ai lu intégralement chaque fichier d'agent et de skill, j'ai relevé les références croisées (quel skill appelle quel agent, quel fichier produit quel concept de la KB) et j'ai vérifié l'installation (manifest, hooks). J'ai aussi exécuté les tests de l'app. Chaque constat renvoie à son fichier et, si possible, à sa ligne.

---

## 1. Synthèse

| Question | Réponse courte |
|---|---|
| L'objectif est-il atteint ? | **En grande partie sur le papier, pas encore en pratique.** Le chemin de bout en bout est décrit, de l'identité du projet jusqu'au merge du sprint. Mais rien n'est installable en l'état, 7 agents ne sont appelés par aucun skill, et le **suivi** du projet (troisième pilier) est le plus faible. |
| Les skills et agents nécessaires sont-ils tous là ? | **Non.** Il manque : un suivi et un reporting branchés sur la KB, la validation PO et la clôture des tickets, la revue et la rétrospective de sprint, la gestion des changements du CDC, la livraison et le déploiement (CI/CD), les critères d'acceptation, les objectifs mesurables et la traçabilité (« qui a demandé X ? »). |
| Peut-il être amélioré ? | **Oui, nettement.** Les principaux leviers : rendre Hosa installable, supprimer la duplication skill/agent, corriger les incohérences (voir §4), tenir compte des limites des subagents (pas de dialogue avec l'utilisateur) et ajouter les briques de suivi. |

**Répartition de la maturité**, estimée à partir du contenu des fichiers :

| Pilier | Couverture | Commentaire |
|---|---|---|
| Définir les objectifs | ●●●○○ | Identité, personas et un pipeline CDC en 4 étapes solide. Il manque les objectifs mesurables, le périmètre et les non-objectifs, les exigences non fonctionnelles, les critères d'acceptation et la roadmap. |
| Développer | ●●●●○ | Le pipeline le plus abouti : stack → infra → données → architecture → interface → backlog → sprint → develop → QA → merge. Des garde-fous de qualité réels. |
| Suivre | ●○○○○ | `status` ignore la KB. Aucun skill ne passe un ticket en `done`. Pas de revue de sprint, pas de rétro, pas d'indicateurs. L'app n'affiche pas les sprints. |

---

## 2. Inventaire

### 2.1 Agents (19)

| Agent | Modèle | Appelé par (skills) | Constat |
|---|---|---|---|
| `hosa-planner` | opus-4-8 | `build`, `iterate` | OK |
| `hosa-implementer` | sonnet-5 | `build`, `iterate`, `dispatch` | OK |
| `hosa-tester` | sonnet-5 | `test`, `qa`, `dispatch` | OK |
| `hosa-reviewer` | opus-4-8 | `review`, `dispatch` | OK |
| `hosa-debugger` | sonnet-5 | `debug`, `dispatch` | OK |
| `hosa-key-user` | opus-4-8 | `hosa`, `recette`, `interview`, `contestation`, `donnees`, `interface`, `qa` | Très sollicité ; 4 modes d'entrée |
| `hosa-challenger` | opus-4-8 | `contestation` | OK |
| `hosa-senior-dev` | opus-4-8 | `qualite` seulement | **`stack` ne l'appelle pas**, il refait le travail lui-même |
| `hosa-documentation` | opus-4-8 | `stack`, `infra`, `schema-app`, `architecture`, `contestation`, `documentation` | OK (mais `interface` le contourne, voir §4) |
| `hosa-git` | opus-4-8 | `git` | OK |
| `hosa-tech-lead` | opus-4-8 | `develop` | OK |
| `hosa-developer` | sonnet-5 | `develop` | OK |
| `hosa-product-owner` | opus-4-8 | **aucun** | Rôle joué « en ligne » par `redaction`, `backlog` et `contestation` |
| `hosa-infra` | opus-4-8 | **aucun** | Le skill `infra` refait tout son Mode 1 lui-même |
| `hosa-data-engineer` | opus-4-8 | **aucun** | `donnees`, `schema-app` et `schema-db` font le travail eux-mêmes |
| `hosa-architect` | opus-4-8 | **aucun** | `architecture` fait le travail lui-même |
| `hosa-ux-designer` | opus-4-8 | **aucun** | `interface` fait le travail lui-même |
| `hosa-sprint-planner` | opus-4-8 | **aucun** | `sprint` reprend son texte presque mot pour mot |
| `hosa-qa-lead` | opus-4-8 | **aucun** | `qa-plan` et `qa` reprennent ses modes 1, 2 et 3 |

→ **7 agents sur 19 ne sont appelés par aucun skill.** Ils ne servent qu'en invocation directe, et leur logique est **dupliquée** dans le skill correspondant (voir §4.2).

### 2.2 Skills (31)

| Groupe | Skills | Écrit dans |
|---|---|---|
| Amorçage | `using-hosa` | — |
| Cycle générique | `understand`, `build`, `iterate`, `dispatch`, `test`, `review`, `debug`, `status` | `docs/specs/`, code, commits |
| Cadrage | `hosa` | `kb/project/`, `kb/personnas/` |
| Pipeline CDC | `interview` → `redaction` → `relecture` → `contestation` (+ `fondamentaux`) | `kb/cdc/` |
| Pipeline de structuration | `stack` → `infra` → `donnees` → `schema-app` → `schema-db` → `architecture` → `interface` → `backlog` | `kb/stack`, `kb/infra`, `kb/cdc`, `kb/rules/design`, `kb/tickets`, projet géré |
| Livraison | `sprint` → `git` (Mode 1) → `develop` → `qa-plan` → `qa` → `git` (Mode 2) | `kb/sprints`, `kb/test`, projet géré |
| Transverses | `recette`, `qualite`, `documentation` | `kb/test`, `kb/qualite`, `kb/documentation` |

### 2.3 Workflow tel qu'il est implémenté

```
hosa ─► interview ─► redaction ─► relecture ─► contestation ─► stack ─► infra ─► donnees
                          ▲  fondamentaux (à tout moment)                               │
                          └──────── boucle d'anomalies ◄──────┘                         ▼
backlog ◄─ interface ◄─ architecture ◄─ schema-db ◄─ schema-app ◄────────────────────────┘
   │
   ▼
sprint ─► git (Mode 1) ─► develop (×N tickets) ─► qa-plan ─► qa ─► git (Mode 2: merge)
                                                              │
                                    ┌── ? (aucun skill) ──────┘
                                    ▼
                    validation PO / ticket done / revue / rétro / release  ← MANQUANT
```

Chaque étape propose l'étape suivante (« Je lance X maintenant ? »). L'enchaînement est donc guidé, sans être automatique.

---

## 3. Points forts (factuels)

1. **Chaîne d'amont très complète.** On part de l'identité du projet et des personas, on passe par une interview persona par persona, puis par des exigences structurées en 6 sections, une relecture de précision et une contestation indépendante (`hosa-challenger`, qui n'a jamais écrit le CDC). La validation finale est humaine (`verified: human:`).
2. **Traçabilité OKF.** Frontmatter `generated` et `verified`, `log.md` par bundle, convention d'acteur `human:` / `agent/version`. Elle est appliquée de façon homogène dans tous les agents et skills.
3. **Garde-fous explicites et non contournables :**
   - `sprint` refuse un ticket dont la faisabilité, le placement architecture ou le placement interface n'ont jamais été évalués ([sprint/SKILL.md:54](../skills/sprint/SKILL.md#L54)) ;
   - `hosa-tech-lead` et `hosa-developer` s'arrêtent sur toute « déviation structurelle » au lieu d'improviser ([tech-lead.md:32](../agents/tech-lead.md#L32)) ;
   - le merge est bloqué tant qu'un ticket n'a pas de QA verte ([git.md:57](../agents/git.md#L57)).
4. **Séparation des responsabilités :** un seul installateur (`hosa-infra`), un seul rédacteur de documentation (`hosa-documentation`), un seul agent qui opère le git du projet géré (`hosa-git`).
5. **Honnêteté imposée :** ne jamais annoncer une version épinglée sans la vérifier ([infra.md:38](../agents/infra.md#L38)), ne jamais inventer une métrique de performance ([senior-dev.md:66](../agents/senior-dev.md#L66)), ne jamais déclarer un service « en place » sans l'avoir démarré.
6. **Idempotence pensée :** les relances de `backlog`, `sprint`, `qa-plan`, `interface` et `documentation` ne comblent que les manques et ne dupliquent rien.
7. **App de pilotage fonctionnelle :** 18 tests sur 18 passent (`node --test`, exécuté le 2026-09-27).

---

## 4. Défauts et incohérences constatés

### 4.1 Bloquants (Hosa ne peut pas fonctionner comme décrit)

| # | Constat | Preuve |
|---|---|---|
| B1 | **Hosa n'est pas installable.** Il n'y a ni `.claude-plugin/plugin.json`, ni manifest de marketplace. Le dossier `hooks/` est vide. Hosa n'apparaît pas dans `~/.claude/plugins/installed_plugins.json`, et aucun agent n'est présent dans `~/.claude/agents`. | `git ls-files`, `ls hooks` |
| B2 | **`using-hosa` n'est pas « chargé au démarrage de session »**, contrairement à ce qu'annonce sa description. Aucun hook `SessionStart` ne l'injecte, donc les règles d'auto-déclenchement et les Core Rules ne s'appliquent pas. | [using-hosa/SKILL.md:3](../skills/using-hosa/SKILL.md#L3), `hooks/` vide |
| B3 | **Des subagents supposés dialoguer avec l'utilisateur.** Un subagent s'exécute jusqu'au bout et ne renvoie qu'un seul message final : il ne peut pas mener un échange de questions-réponses. Plusieurs agents reposent pourtant sur ce dialogue. `hosa` envoie `hosa-key-user` « interroger l'utilisateur directement » ([hosa/SKILL.md:93-97](../skills/hosa/SKILL.md#L93-L97)). `hosa-senior-dev` attend « once the user picks » ([senior-dev.md:39](../agents/senior-dev.md#L39)). `hosa-infra` demande à l'utilisateur ([infra.md:34](../agents/infra.md#L34)). `hosa-ux-designer` demande une validation ([ux-designer.md:39-40](../agents/ux-designer.md#L39-L40)). | fichiers cités |
| B4 | **Des dispatchs d'agent à agent.** `hosa-infra`, `hosa-architect` et `hosa-data-engineer` appellent `hosa-documentation`. `hosa-data-engineer` et `hosa-ux-designer` appellent `hosa-key-user`. `hosa-qa-lead` appelle `hosa-tester` et `hosa-key-user`. La Core Rule exige que tout agent appelle `hosa-infra`. Or la documentation Claude Code indique qu'un subagent ne peut pas lancer d'autres subagents : **à vérifier sur la version utilisée**. Si c'est confirmé, ces chaînes ne fonctionnent que lorsque le travail est fait par le skill (session principale), pas par l'agent. | [infra.md:61](../agents/infra.md#L61), [qa-lead.md:59-61](../agents/qa-lead.md#L59-L61), [using-hosa/SKILL.md:99](../skills/using-hosa/SKILL.md#L99) |
| B5 | **La porte de merge compare deux vocabulaires différents.** `hosa-git` exige un « verdict `Réussi` » pour la recette. Mais le verdict de `hosa-key-user` vaut `Accepté / Accepté avec réserves / Refusé`, `Réussi / Échoué / Partiel` ne qualifiant que les scénarios. Selon la lecture, la porte bloque tout, ou bien laisse passer un « Accepté avec réserves ». | [git.md:57](../agents/git.md#L57) vs [key-user.md:122](../agents/key-user.md#L122) |

### 4.2 Duplication entre skill et agent (source de dérive)

7 paires contiennent la même procédure, écrite deux fois : `sprint` / `hosa-sprint-planner`, `qa-plan` + `qa` / `hosa-qa-lead`, `infra` / `hosa-infra`, `architecture` / `hosa-architect`, `interface` / `hosa-ux-designer`, `stack` / `hosa-senior-dev`, `donnees` + `schema-*` / `hosa-data-engineer`. **La dérive est déjà visible :**

| # | Dérive | Preuve |
|---|---|---|
| D1 | L'agent architecte définit une base d'observabilité (correlation-id, logs structurés, symptômes alertables). Le skill `architecture`, qui fait réellement le travail, **ne la mentionne pas**. `hosa-developer` doit pourtant la réutiliser. | [architect.md:36-37](../agents/architect.md#L36-L37) vs [architecture/SKILL.md:48-54](../skills/architecture/SKILL.md#L48-L54), [developer.md:21](../agents/developer.md#L21) |
| D2 | Étape suivante après le choix de stack : `donnees` selon l'agent **et selon le diagramme du skill lui-même**, `infra` selon la sortie du skill. | [senior-dev.md:84](../agents/senior-dev.md#L84), [stack/SKILL.md:32](../skills/stack/SKILL.md#L32) vs [stack/SKILL.md:122](../skills/stack/SKILL.md#L122) |
| D3 | Les descriptions de `stack`, `infra`, `donnees`, `schema-app` et `schema-db` annoncent un pipeline qui **s'arrête à `architecture`**. Celles d'`architecture`, `interface` et `backlog` le prolongent jusqu'à `backlog`. | lignes 3 de chaque SKILL.md |

### 4.3 Incohérences de règles

| # | Constat | Preuve |
|---|---|---|
| I1 | **Documentation « propriété exclusive » contournée.** `hosa-documentation` se dit seul rédacteur de la documentation du projet géré, mais `interface` et `hosa-ux-designer` écrivent eux-mêmes la documentation d'interface. De plus, la section interface ne figure pas dans l'arborescence de `hosa-documentation`. | [documentation.md:8,38-40](../agents/documentation.md#L8) vs [interface/SKILL.md:89-91](../skills/interface/SKILL.md#L89-L91), [ux-designer.md:43](../agents/ux-designer.md#L43) |
| I2 | **« Trust the user, don't add gates »** contredit les **HARD-GATE de quiz** (2 QCM obligatoires, qui ne se lèvent même pas sur demande explicite) de `understand`, `build` et `iterate`. `develop` n'a pas de quiz, sans justification commune. Dans un workflow IA, ces portes bloquent l'automatisation. | [using-hosa/SKILL.md:98](../skills/using-hosa/SKILL.md#L98) vs [build/SKILL.md:90-104](../skills/build/SKILL.md#L90-L104), [develop/SKILL.md:60](../skills/develop/SKILL.md#L60) |
| I3 | **Le correctif appliqué avant confirmation.** `debug` exige la confirmation de l'utilisateur avant d'appliquer un correctif, alors que `hosa-debugger` « applies the fix directly » pendant son enquête. | [debug/SKILL.md:68-73](../skills/debug/SKILL.md#L68-L73) vs [debugger.md:3,39-42](../agents/debugger.md#L39-L42) |
| I4 | **Textes périmés** : `hosa-product-owner` parle du skill `hosa` comme « not yet built » et « future », alors qu'il existe depuis le 2026-09-24. | [product-owner.md:3,35](../agents/product-owner.md#L35) |
| I5 | **Confusion outil / projet géré** : « Product Owner for Hosa », « Hosa project's identity ». Les agents techniques excluent `hosa/app` et `hosa/kb`, mais le PO et le skill `hosa` décrivent le projet comme « Hosa ». | [product-owner.md:8](../agents/product-owner.md#L8), [hosa/SKILL.md:3](../skills/hosa/SKILL.md#L3) |
| I6 | **La KB est dans le dépôt de l'outil** (`hosa/kb/`, chemin codé en dur partout), alors que le code géré est externe (racine `Infra`). Conséquence : une seule KB par installation, donc **impossible de piloter plusieurs projets**, et une KB non versionnée avec le projet qu'elle décrit. | tous les agents et skills Hosa |
| I7 | **Deux mondes non reliés.** `understand`, `build`, `review`, `test` et `status` travaillent sur `docs/specs/` ; le pipeline Hosa travaille sur `kb/`. `review` ne sait pas contrôler un ticket contre son `Exigence`, et `status` ne lit ni les tickets, ni les sprints, ni les résultats de QA. | [status/SKILL.md](../skills/status/SKILL.md), [review/SKILL.md:36](../skills/review/SKILL.md#L36) |
| I8 | **Déclencheurs en collision** : « Fais une recette de… » (`recette`) et « Fais la recette du sprint » (`qa`) ; « Implement this » (`build`) et « Implémente le ticket X » (`develop`) ; « Test this » (`test`) et « Teste le sprint » (`qa`). | [using-hosa/SKILL.md:54-83](../skills/using-hosa/SKILL.md#L54-L83) |
| I9 | **Aucune modification de la KB n'est jamais committée.** Tous les skills du pipeline disent « No Commits » ; seuls les commits dans le projet géré existent. L'historique de la KB repose donc sur un commit manuel. | toutes les sections « No Commits » |
| I10 | **Aucune restriction d'outils (`tools:`) sur les agents**, y compris ceux qui ne doivent « jamais écrire » (`hosa-challenger`, `hosa-reviewer`, `hosa-tech-lead`). La règle n'est que déclarative. | 0 occurrence de `tools:` dans `agents/` |
| I11 | **Modèles épinglés en ID complet** (`claude-opus-4-8` × 15, `claude-sonnet-5` × 4). Opus 4.8 n'est plus le modèle Opus le plus récent (Opus 5.5 est disponible). Un alias (`opus` / `sonnet` / `inherit`) éviterait l'obsolescence. | frontmatter `model:` |
| I12 | Le README des agents indique une invocation via `select:<name>`, qui est la syntaxe de ToolSearch et non celle de l'outil Agent. | [agents/README.md:3](../agents/README.md#L3) |

---

## 5. Couverture fonctionnelle : ce qui manque

### 5.1 Pour « définir les objectifs »

| Manque | Pourquoi c'est nécessaire | Où ça devrait vivre |
|---|---|---|
| **Objectifs mesurables** (KPI/OKR, critères de succès) | `kb/project/identity.md` n'a qu'un « objectif en une phrase ». Sans métrique, impossible de dire si le projet réussit. `understand` le demande (« Success criteria »), mais pas `hosa`. | `hosa` (Init flow) + section `## Objectifs mesurables` |
| **Périmètre et non-objectifs, contraintes** (délai, budget, réglementaire) | Aucun concept ne les porte. `contestation` ne peut pas détecter une dérive de périmètre. | `kb/project/` |
| **Exigences non fonctionnelles** (performance, disponibilité, RGPD, accessibilité) | Le gabarit `Exigence` est centré sur les processus métier. `fondamentaux` couvre le socle applicatif (admin, login…) mais aucune NFR chiffrée. `hosa-infra` cherche pourtant des « non-functional needs » dans le CDC. | nouvelle checklist NFR dans `fondamentaux` ou type `Exigence` taggé `nfr` |
| **Critères d'acceptation** | Ni `Exigence` ni `Ticket` n'ont de section d'acceptation (Given/When/Then). `qa-plan` déduit les tests de la note technique, et la recette juge « du point de vue du persona ». Il n'y a donc aucun contrat vérifiable commun à la QA et au PO. | `backlog` : section `## Critères d'acceptation` |
| **Règles de sécurité** | Le bundle `kb/rules/security/` (`Security Rule`) est défini dans la spec, mais **aucun skill ne l'alimente**. La checklist sécurité est codée en dur dans `hosa-senior-dev`. | `fondamentaux` ou `qualite` |
| **Priorisation et roadmap** | `sprint` demande l'ordre de priorité à l'utilisateur, faute de champ `priority`. Il n'y a ni méthode (MoSCoW, WSJF), ni jalons, ni releases. | `backlog` + champ `priority` / `milestone` |
| **Estimation** | La capacité d'un sprint se compte en nombre de tickets (ce qui est reconnu dans le texte). La vélocité est impossible à calculer. | champ `estimate` sur `Ticket` |

### 5.2 Pour « développer »

| Manque | Détail |
|---|---|
| **CI/CD et déploiement** | La stack enregistre un choix d'hébergement, mais aucun skill ne construit un pipeline CI, un environnement de staging ou de production, ni un déploiement. Le travail s'arrête au merge **local** (le push et les PR sont explicitement hors périmètre, [git.md:8](../agents/git.md#L8)). |
| **Gestion des secrets et de la configuration par environnement** | Seul l'audit `qualite` vérifie l'absence de secrets en dur ; rien ne les met en place. |
| **Création de tickets depuis `debug`, `qa` ou `qualite`** | Une anomalie `Bloquant` ou un bug de QA propose `debug`, mais ne crée jamais de `Ticket`. La spec de pilotage l'exigeait pourtant (« créer un Ticket au lieu de dévier la tâche », [pilotage-design.md:131-133](specs/2026-09-23-hosa-pilotage-design.md#L131-L133)). |
| **Évolution du CDC après `stable`** | Aucun skill ne fait l'analyse d'impact « une exigence stable change → quels tickets, entités, migrations et écrans sont touchés ». `iterate` est générique et ignore la KB. |
| **Revue de code des changements d'un ticket** | `develop` committe après une simple confirmation. `review` ne sait comparer qu'à un fichier `docs/specs/`, pas au ticket et à son exigence. |

### 5.3 Pour « suivre le projet » (le pilier le plus faible)

| Manque | Détail |
|---|---|
| **Validation PO et passage en `done`** | `develop` propose « validation par hosa-product-owner (state: done) », mais **aucun skill ne l'orchestre** et l'agent PO n'est appelé nulle part. Aucun ticket ne peut donc atteindre `done` par le workflow. |
| **Statut projet branché sur la KB** | `status` lit `docs/specs/` et `git log`, mais ni `kb/tickets`, ni `kb/sprints`, ni `kb/test`, ni `kb/qualite`. Il ne peut pas répondre à « où en est le sprint ? ». |
| **Revue et rétrospective de sprint** | Rien entre le merge (`git` Mode 2, `state: done`) et le sprint suivant : pas de bilan, pas d'objectif atteint ou non, pas d'actions d'amélioration. |
| **Indicateurs** | Pas de burndown, de vélocité, de taux de réussite QA, ni de dette `qualite` ouverte. |
| **Traçabilité interrogeable** | Répondre à « Qui a demandé X ? D'où vient cette règle ? » est une responsabilité prévue du skill `hosa`, qui n'est implémentée qu'en tranche 1 ([hosa/SKILL.md:8](../skills/hosa/SKILL.md#L8)). |
| **App de pilotage** | L'app affiche les concepts et un kanban de tickets, mais **ni les sprints, ni les résultats de QA, ni les audits** (aucune occurrence de `Sprint` dans `hosa/app/`). Elle est en lecture seule. |
| **Gestion des risques** | `hosa-challenger` repère des risques dans le CDC, mais ils ne sont conservés nulle part (pas de registre des risques). |

---

## 6. Recommandations

### P0 : rendre Hosa exécutable (sans cela, rien ne fonctionne)

1. **Packager Hosa en plugin Claude Code** : `.claude-plugin/plugin.json` avec `agents/`, `skills/` et `hooks/`, plus une marketplace locale pour l'installation.
2. **Ajouter un hook `SessionStart`** qui injecte `using-hosa` (corrige B2).
3. **Redéfinir la frontière skill/agent** (corrige B3, B4 et §4.2), selon une règle simple :
   - **Skill (session principale)** : tout ce qui dialogue avec l'utilisateur (choix, validation, interview) et tout ce qui orchestre d'autres agents.
   - **Agent (subagent)** : un travail autonome, avec une entrée complète, un seul rapport en sortie et aucun dispatch.
   - Conséquences concrètes :
     - les skills appellent réellement `hosa-architect`, `hosa-data-engineer`, `hosa-ux-designer`, `hosa-sprint-planner`, `hosa-qa-lead` et `hosa-infra` pour la partie « produire », et **le texte dupliqué est retiré du skill** ;
     - les agents interactifs sont découpés en deux modes, *proposer* puis *enregistrer* : l'agent propose, le skill fait valider, puis l'agent (ou le skill) écrit ;
     - les « dispatchs » d'agent à agent deviennent des **retours au skill** : l'agent renvoie `Documentation à produire: …` et c'est le skill qui appelle `hosa-documentation`.
4. **Harmoniser le vocabulaire de la porte QA** (B5) : la porte doit exiger un verdict `Accepté` et décider explicitement du sort de « Accepté avec réserves ».

### P1 : cohérence et suivi

5. **Corriger les incohérences** I1 à I12. En particulier :
   - faire passer `interface` par `hosa-documentation` (`docs/technique/interface.md`) ;
   - reporter l'observabilité dans le skill `architecture` ;
   - aligner les descriptions du pipeline ;
   - trancher la politique de quiz (option possible : désactivable par l'utilisateur, ce qui respecte « Trust the user ») ;
   - faire proposer (et non appliquer) le correctif par `hosa-debugger` ;
   - nettoyer les textes périmés de `hosa-product-owner` ;
   - passer les modèles en alias ;
   - ajouter `tools:` aux agents en lecture seule.
6. **Nouveau skill `validation`** (ou `accept`) : appelle `hosa-product-owner` en mode *fin de cycle* sur un ticket ou un sprint, s'appuie sur les critères d'acceptation, les résultats `kb/test/` et le verdict de recette, puis passe le ticket en `done` + `verified` ou le renvoie. Il ferme la boucle ouverte par `develop`.
7. **Réécrire `status`** pour lire la KB : identité et objectifs, état du CDC (draft / stable), backlog par `state`, sprint actif (tickets, QA), anomalies `qualite` ouvertes, dérive documentaire, puis l'étape suivante du pipeline.
8. **Nouveau skill `bilan-sprint`** (revue + rétro) : objectif atteint ou non, tickets livrés ou reportés, résultats QA, points de friction remontés par les recettes. Il produit un concept `Sprint Review` et des actions (tickets ou `Design Rule` de processus). Il se déclenche après `git` Mode 2.
9. **Critères d'acceptation** : `backlog` ajoute une section `## Critères d'acceptation` (Given/When/Then) dérivée de l'exigence. `qa-plan` en tire ses cas de test, et `recette` et `validation` s'y réfèrent.
10. **Objectifs mesurables et périmètre** dans `hosa` : KPI, non-objectifs, contraintes. `contestation` vérifie ensuite que chaque exigence sert au moins un objectif.

### P2 : compléter le cycle

11. **`changement`** (gestion des évolutions) : une modification d'une `Exigence` stable déclenche une analyse d'impact (tickets, entités, migrations, écrans, documentation), le repassage en `draft` puis une mini-boucle relecture/contestation, et enfin des tickets de changement.
12. **`livraison`** (release/deploy) : pipeline CI, environnements, versionnage, notes de version tirées des tickets `done`, et push/PR optionnels. C'est l'étape qui transforme « merge local » en « livré ».
13. **Tickets automatiques** : `debug`, `qa`, `qualite` et `recette` (pour les quick wins) créent des `Ticket` `todo` liés au lieu de simples suggestions. Cela implémente l'intention de la spec de pilotage.
14. **Tranche 2 du skill `hosa`** : création libre de concepts en langage naturel et réponses de traçabilité.
15. **Bundle `kb/rules/security/`** alimenté (checklist sécurité externalisée hors de `hosa-senior-dev`) et **checklist NFR** dans `fondamentaux`.
16. **Champs `priority`, `estimate` et `milestone`** sur `Ticket` pour une vraie planification (vélocité, roadmap).
17. **App** : vues Sprint, QA et Qualité, puis écriture (la spec prévoit déjà les routes `PATCH`/`POST`).
18. **KB par projet géré** : faire résoudre le chemin de la KB (par exemple `<projet-géré>/.hosa/kb/` ou un chemin configurable) au lieu de `hosa/kb/` codé en dur. La KB est alors versionnée avec le projet et plusieurs projets deviennent possibles.
19. **Politique de commit de la KB** : un commit KB en fin de chaque skill du pipeline (identité de l'utilisateur), ou un skill `kb-commit`, pour que la traçabilité OKF ait un historique fiable.
20. **Lever les collisions de déclencheurs** (I8) : `using-hosa` vérifie le contexte (KB présente ? sprint actif ?) avant de choisir entre la variante générique et la variante Hosa.

### Workflow cible proposé

```
CADRER      hosa (+ objectifs mesurables, périmètre) → personas
SPÉCIFIER   interview → redaction → relecture → contestation (+ fondamentaux, NFR, sécurité)
CONCEVOIR   stack → infra → donnees → schema-app → schema-db → architecture → interface
PLANIFIER   backlog (+ critères d'acceptation, priorité, estimation) → sprint → qa-plan
RÉALISER    git M1 → develop (×N) [→ tickets auto sur bug/qualité]
VÉRIFIER    qa → validation (PO: done/renvoyé) → git M2
LIVRER      livraison (CI/CD, release notes)                         ← nouveau
SUIVRE      status (KB) · bilan-sprint · app (sprints/QA)            ← refondu / nouveau
ÉVOLUER     changement (analyse d'impact CDC → tickets)              ← nouveau
```

---

## 7. Conclusion

Hosa dispose d'une **conception d'amont et de réalisation remarquablement rigoureuse** : spécification contestée, garde-fous structurels, traçabilité OKF et porte QA avant le merge. En revanche, **l'objectif n'est pas encore atteint** pour trois raisons factuelles :

1. **Rien n'est exécutable en l'état** : pas de plugin, pas de hook, et un modèle d'agents qui suppose du dialogue et des dispatchs imbriqués qu'un subagent ne permet pas.
2. **La moitié des agents « métier » est court-circuitée** par des skills qui dupliquent leur logique, et cette duplication dérive déjà.
3. **Le suivi du projet est quasi absent** : aucun ticket ne peut passer en `done` via le workflow, `status` ignore la KB, et il n'y a ni revue de sprint, ni indicateurs, ni livraison.

Les recommandations P0 (packaging, frontière skill/agent, porte QA) suivies de trois nouveaux skills (`validation`, `bilan-sprint` et un `status` refondu) suffiraient à couvrir les trois piliers « définir, développer, suivre » de bout en bout.
