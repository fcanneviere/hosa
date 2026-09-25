# Hosa — product backlog collaboratif (PO + senior dev + architecte)

**Date:** 2026-09-25
**Statut:** approuvé pour implémentation

## Contexte

Le pipeline de structuration des données (`docs/superpowers/specs/2026-09-24-hosa-stack-architecture-design.md`)
se termine aujourd'hui à `architecture` : la stack est choisie, les
structures de données sont écrites, l'architecture logicielle est
scaffoldée. Rien ne relie encore tout ça au Product Backlog
(`hosa/kb/tickets/`), que `hosa-product-owner` peut déjà créer seul mais
sans aucun ancrage technique — un ticket écrit avant que la stack ou
l'architecture existent ne peut pas dire où ni comment le construire.

Cette itération ajoute une sixième étape, `backlog`, qui transforme chaque
`Exigence` `stable` sans ticket en un `Ticket` enrichi par trois points de
vue : la valeur métier (PO), la faisabilité technique (senior dev),
l'emplacement dans l'architecture (architecte). Aucun nouvel agent n'est
créé — `hosa-product-owner`, `hosa-senior-dev`, `hosa-architect` existent
déjà ; le skill reprend leurs responsabilités en ligne, même principe que
`stack`/`architecture`.

## Pipeline mis à jour

```
interview → redaction → relecture → contestation →
stack → donnees → schema-app → schema-db → architecture → backlog
```

`backlog` devient la sixième et dernière étape du pipeline de
structuration des données. Invocable seule ; `architecture` la propose sans
l'imposer, même logique que le reste du pipeline.

## Le Product Backlog reste `kb/tickets/`

Pas de nouveau concept OKF. `kb/tickets/` est déjà "le Product Backlog"
(cf. `agents/product-owner.md`), et `Ticket.state` (`todo | doing | done |
blocked`) est déjà "le statut". `backlog` écrit dans ce bundle existant,
avec un corps de ticket enrichi de deux nouvelles sections.

## Skill `skills/backlog/SKILL.md`

**Trigger manuel :** `/backlog`. **Auto :** immédiatement après
`architecture`, ou "crée le product backlog", "génère les tickets à partir
du cahier des charges".

### Step 1 : Périmètre

Lit chaque `Exigence` `stable` de `kb/cdc/`. Pour chacune, cherche dans
`kb/tickets/` un `Ticket` existant dont le corps contient un lien markdown
vers cette exigence. Si un tel ticket existe déjà, passe à la suivante —
un rerun de `backlog` n'écrase jamais un ticket déjà créé. Si aucune
`Exigence` `stable` n'a de ticket manquant, le dit et s'arrête (rien à
faire).

### Step 2 : Story (rôle PO)

Pour chaque `Exigence` sans ticket, écrit un nouveau `Ticket` dans
`kb/tickets/<slug>.md`, `state: todo`, avec la story au format déjà utilisé
par `hosa-product-owner` :

```markdown
---
type: Ticket
title: <titre>
description: <description courte>
tags: []
state: todo
generated: { by: hosa-product-owner/1.0, at: <ISO8601> }
---
En tant que [persona],
je veux [besoin],
afin de [valeur].

Lié à : [persona](../personnas/xxx.md), [exigence](../cdc/xxx.md)
```

### Step 3 : Note technique (rôle senior dev)

Lit `kb/stack/` pour les `Stack Decision` déjà enregistrées. Si absentes
(`backlog` invoqué seul, avant que `stack` ait tourné), ajoute une ligne
"Stack pas encore choisie — faisabilité non évaluée" au lieu de bloquer la
création du ticket. Sinon, ajoute au ticket :

```markdown
## Note technique (senior dev)
[Faisabilité/complexité au regard de la stack retenue]
```

### Step 4 : Placement architecture (rôle architecte)

Lit la documentation d'architecture référencée par l'entrée `Infra` dans
`kb/infra/`. Si absente (`architecture` n'a pas encore tourné), ajoute une
ligne "Architecture pas encore scaffoldée — placement non déterminé" au
lieu de bloquer. Sinon, ajoute au ticket :

```markdown
## Placement architecture (architecte)
[Module/couche concerné et pourquoi]
```

### Step 5 : Log

Log dans `kb/tickets/log.md` (créé si absent) — OKF §9, un ticket créé par
ligne.

### No Commits

Ne commit jamais — même règle que tous les skills Hosa.

### Output

```
## Tickets créés
- `kb/tickets/<slug>.md` — [titre] (state: todo)

## Suite
Pipeline de structuration des données terminé.
```

## Modification à `architecture`

Le `## Suite` actuel ("Pipeline de structuration des données terminé.")
est retiré — cette étape n'est plus la dernière. À la place :
"Je lance `backlog` maintenant ?"

## Registre dans `using-simflow`

`backlog` est ajouté à la table des skills (stage 6) et à la table de
triggers auto de `skills/using-simflow/SKILL.md`, même format que les
entrées existantes.

## Hors scope (v1)

- Régénération d'un ticket déjà créé si l'`Exigence`, la stack ou
  l'architecture changent après coup (pas de détection de drift, même
  principe que le reste du pipeline).
- Découpage automatique d'une `Exigence` en plusieurs tickets — une
  `Exigence` `stable` sans ticket produit exactement un `Ticket` ; le
  découpage manuel reste une action ultérieure de `hosa-product-owner`
  (déjà couvert par son rôle "Backlog" existant).
- Priorisation du backlog par `backlog` — le skill crée les tickets en
  `state: todo`, la priorisation reste la responsabilité continue de
  `hosa-product-owner` (déjà couverte, hors scope de cette itération).
