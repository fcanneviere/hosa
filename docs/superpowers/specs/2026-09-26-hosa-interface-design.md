# Hosa — couche interface (UX/UI)

**Date:** 2026-09-26
**Statut:** approuvé pour implémentation

## Contexte

Le pipeline de structuration des données (`docs/superpowers/specs/2026-09-25-hosa-backlog-design.md`)
va aujourd'hui de `stack` à `backlog` : la stack est choisie, les données
sont structurées, l'architecture logicielle est scaffoldée, et chaque
`Exigence` `stable` devient un `Ticket` enrichi d'une note technique et d'un
placement architecture. Rien, dans ce pipeline, ne s'occupe de ce que
l'utilisateur final voit et manipule — aucun agent ne porte l'identité
visuelle du projet, ses règles de design, ni la façon dont l'interface
traduit le besoin de chaque persona en écrans concrets.

Cette itération ajoute un agent — `hosa-ux-designer` — et une sixième
étape du pipeline, `interface`, insérée entre `architecture` et `backlog`.
Elle interviewe chaque persona (comme `interview` le fait déjà pour le CDC,
via `hosa-key-user`), propose une identité visuelle et des règles de
design, conçoit et scaffold la couche interface dans le projet géré, puis
enrichit chaque ticket créé par `backlog` d'un troisième point de vue :
l'emplacement dans l'interface.

## Portée : le projet géré, pas Hosa lui-même

Même règle que le reste du pipeline : `hosa/kb/` reste la source de
spécification, `hosa/app/` et `hosa/kb/` ne sont jamais la cible d'écriture.
`interface` scaffold dans le projet *externe* que Hosa pilote — chemin lu
depuis l'entrée `Infra`, jamais supposé être `hosa/app`.

## Pipeline mis à jour

```
stack → donnees → schema-app → schema-db → architecture → interface → backlog → sprint
```

`interface` devient la sixième étape du pipeline de structuration des
données ; `backlog` (septième) et `sprint` restent après elle. Invocable
seule ; `architecture` la propose sans l'imposer, même logique que le reste
du pipeline.

## 1. Agent `hosa-ux-designer`

`agents/ux-designer.md`, frontmatter :
```yaml
name: hosa-ux-designer
model: claude-opus-4-8
memory: project
```

Rôle : garant de la couche interface du projet géré par Hosa. Intervient
une fois le CDC stable et l'architecture logicielle scaffoldée. Interviewe
chaque persona pour savoir ce qu'il a besoin de voir, propose une identité
visuelle et des règles de design pour le projet, conçoit une couche
interface (écrans, composants, navigation) cohérente avec l'architecture
existante, puis la scaffold réellement dans le projet cible.

### Input

Une demande de conception de l'interface. Si le CDC n'a pas encore
d'`Exigence` `stable`, ou si l'architecture n'est pas encore scaffoldée, le
dit et propose de lancer `contestation`/`architecture` d'abord plutôt que
de deviner.

### Process

1. Lit `kb/cdc/` (`Exigence` `stable`), `kb/personnas/`, `kb/stack/`
   (`Stack Decision`), et la documentation d'architecture déjà écrite par
   `hosa-architect` dans le projet cible (chemin dans l'entrée `Infra`).
2. Pour chaque persona de `kb/personnas/`, dispatch `hosa-key-user` en mode
   UI-interview : ce que ce persona a besoin de voir, dans quel ordre,
   quelles informations sont prioritaires, quelles contraintes d'usage
   (mobile, accessibilité, autonomie...). Un persona à la fois.
3. Propose une identité visuelle (palette de couleurs, typographie, ton) ;
   l'utilisateur valide ou ajuste. Écrit le résultat dans `kb/project/`
   (nouvelle section `## Identité visuelle` sur le concept `Project`
   existant). Si `kb/project/` n'a pas encore de concept `Project` réel
   (seulement l'exemple), le dit et propose de lancer `hosa` d'abord.
4. Propose des règles de design (ex: densité d'information, composants
   réutilisables, conventions d'interaction) ; l'utilisateur valide ou
   ajuste. Écrit chaque règle retenue comme concept `Design Rule` dans
   `kb/rules/design/<slug>.md` :

```markdown
---
type: Design Rule
title: <titre court>
description: <résumé une ligne>
tags: []
status: stable
generated: { by: human:<user>, at: <ISO8601> }
---
## Règle
<contenu>

## Justification
<pourquoi>
```

   Log dans `kb/rules/design/log.md` (créé si absent) — OKF §9.
5. Conçoit la couche interface (écrans, composants, navigation) cohérente
   avec l'architecture logicielle déjà en place ; dit ce qu'il choisit et
   pourquoi.
6. Scaffold l'interface dans le projet cible : dossiers, composants de
   base, thème/tokens de style correspondant à la stack retenue et à
   l'identité visuelle définie en étape 3. Si des éléments d'interface
   existent déjà, les étend plutôt que de les dupliquer.
7. Rédige la documentation d'interface dans le projet cible (jamais dans
   `hosa/kb`) — ex. `docs/interface.md`, ou l'emplacement de doc déjà en
   place dans le projet.
8. Met à jour l'entrée `Infra` avec le chemin du document d'interface, sous
   un en-tête dédié `## Documentation d'interface`.

### Output

```
## Interviews personas
- <persona> — [besoins UI surfacés]

## Identité visuelle
[Palette, typographie, ton retenus, et où c'est écrit]

## Règles de design
- `kb/rules/design/<slug>.md` — [règle]

## Couche interface conçue
[Écrans/composants retenus et pourquoi]

## Structures créées
- `<path>` — [dossier/composant scaffoldé]

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]
```

### No Commits

Ne commit jamais — même règle que tous les agents Hosa.

### Project Memory

Sauvegarde : l'identité visuelle déjà validée par l'utilisateur pour ce
projet (pour ne pas la reproposer de zéro à chaque session) ; les
conventions d'interface récurrentes du projet cible déjà en place. Ne
sauvegarde pas : le contenu d'une interface déjà scaffoldée — relisible
depuis le code, ni les réponses individuelles d'une UI-interview — déjà
restituées dans le corps de la session.

## 2. Skill `skills/interface/SKILL.md`

**Trigger manuel :** `/interface`. **Auto :** immédiatement après
`architecture`, ou "conçois l'interface", "crée l'identité visuelle",
"définis l'UX/UI du projet".

**Flow :**
```
Lit kb/cdc stable, kb/personnas, kb/stack, et la doc
d'architecture (Infra → ## Documentation d'architecture)
        ↓
Si CDC ou architecture manque, le dit et propose de lancer
l'étape manquante d'abord
        ↓
Pour chaque persona : dispatch hosa-key-user (UI-interview) —
un persona à la fois
        ↓
Propose une identité visuelle → kb/project/ (## Identité
visuelle)
        ↓
Propose des règles de design → Design Rule dans kb/rules/design/
        ↓
Conçoit la couche interface, cohérente avec l'architecture
        ↓
Scaffold l'interface dans le projet cible
        ↓
Rédige la documentation d'interface dans le projet cible
        ↓
Met à jour l'Infra (## Documentation d'interface)
        ↓
Propose de lancer backlog
```

**Étapes** : reprend le process de l'agent ci-dessus, 1 pour 1 (même
principe que `stack`/`architecture` : le skill porte les responsabilités de
l'agent en ligne).

**No Commits** : ne commit jamais.

**Sortie :** voir format agent ci-dessus, plus :
```
## Suite
Je lance `backlog` maintenant ?
```

## 3. Modification à `hosa-key-user`

Ajoute un troisième mode d'entrée, à côté de l'identification, de la
recette, et du process-interview déjà présents :

> **Une UI-interview request** — de `hosa-ux-designer` (via `interface`),
> des questions ciblées sur ce que ce persona a besoin de voir : quelles
> informations prioritaires, dans quel ordre, quelles contraintes d'usage.
> Répond en restant dans le personnage.

Nouvelle section `## Step 2 (alternate 2): Answer a UI-interview request` —
même mécanique que le "process-interview request" déjà documenté : répond
en caractère, peut ajouter un nouveau Pain point/Quick win à
`kb/personnas/<slug>.md` si l'échange en révèle un non déjà listé (même
convention que pendant une recette ou un process-interview), sans toucher à
`Besoins`/`Attentes`. Dit explicitement s'il ne peut pas déduire une
réponse plutôt que d'inventer un détail d'écran sans base.

## 4. Modification à `architecture`

Le `## Suite` actuel ("Je lance `backlog` maintenant ?") devient : "Je
lance `interface` maintenant ?"

## 5. Modification à `backlog`

### Nouveau Step (entre l'actuel Step 4 et Step 5) : Placement interface (rôle UX/UI designer)

Lit la documentation d'interface référencée par l'entrée `Infra` dans
`kb/infra/` (en-tête `## Documentation d'interface`, distinct de la doc
d'architecture). Si absente (`interface` n'a pas encore tourné), ajoute une
ligne "Interface pas encore scaffoldée — placement non déterminé." au lieu
de bloquer la création du ticket. Sinon, ajoute au ticket :

```markdown
## Placement interface (UX/UI)
[Écran/composant concerné et pourquoi]
```

Steps renumérotés en conséquence (l'ancien Step 5 "Log" devient Step 6).

## 6. Modification à `sprint`

Le guard technique de l'étape "Dispatch Up to Capacity" (Step 4) vérifie
désormais trois sections au lieu de deux : `## Note technique`,
`## Placement architecture`, et `## Placement interface`. Un ticket dont
l'une des trois est absente ou tient encore la ligne de repli
correspondante ("Stack pas encore choisie...", "Architecture pas encore
scaffoldée...", "Interface pas encore scaffoldée...") déclenche le même
traitement que déjà défini : le dire, proposer de combler le manque, et
laisser le ticket dans le backlog si le manque reste non comblé.

## 7. Registre dans `using-simflow`

`interface` est ajouté à la table des skills (stage 6 du pipeline de
structuration des données) et à la table de triggers auto de
`skills/using-simflow/SKILL.md`, même format que les entrées existantes.
Les descriptions de `backlog` et `sprint` sont mises à jour pour refléter
la nouvelle position (`backlog` devient stage 7). `hosa-ux-designer` est
ajouté à `agents/README.md`.

## Hors scope (v1)

- Nouveau type OKF pour l'identité visuelle — elle vit comme section du
  concept `Project` déjà existant, même principe que le reste du pipeline
  qui réutilise les bundles OKF en place plutôt que d'en créer sans besoin.
- Wireframes ou maquettes graphiques (images) — l'agent conçoit et scaffold
  l'interface en texte/code, pas de génération d'images.
- Régénération d'une interface déjà scaffoldée si le CDC, la stack ou
  l'architecture changent après coup (pas de détection de drift, même
  principe que le reste du pipeline).
- Tests d'accessibilité ou d'utilisabilité automatisés — restent portés par
  `recette` (validation métier par persona), pas par cette étape.
