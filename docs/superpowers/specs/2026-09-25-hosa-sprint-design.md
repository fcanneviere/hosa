# Hosa — planification de sprints (PO + planificateur, avec garde-fou technique)

**Date:** 2026-09-25
**Statut:** approuvé pour implémentation

## Contexte

`backlog` (`docs/superpowers/specs/2026-09-25-hosa-backlog-design.md`) transforme
chaque `Exigence` `stable` sans ticket en `Ticket` enrichi d'une story, d'une
note technique et d'un placement architecture. Rien n'organise encore ces
tickets en cycles de travail : `hosa-product-owner` priorise le backlog en
continu, mais aucun mécanisme ne découpe le backlog en sprints ni ne
vérifie, avant d'y engager un ticket, que tout ce qu'il faut pour le
réaliser est réellement disponible.

Cette itération ajoute un septième stage, `sprint`, porté par un nouvel
agent `hosa-sprint-planner` qui travaille avec `hosa-product-owner` pour
composer chaque sprint, et consulte les notes déjà écrites par
`hosa-senior-dev`/`hosa-architect` (via `backlog`) comme garde-fou : un
ticket dont la faisabilité technique ou le placement architecture n'ont
jamais été réellement évalués n'entre pas dans un sprint sans qu'on
propose d'abord de combler ce manque.

## Pipeline mis à jour

```
interview → redaction → relecture → contestation →
stack → donnees → schema-app → schema-db → architecture → backlog → sprint
```

`sprint` devient la septième étape, chaînée après `backlog`. Elle sort du
périmètre strict de la "structuration des données" — c'est une étape de
planification de la livraison — donc sa description ne se présente pas
comme faisant partie du "data-structuring pipeline", mais comme la suite
qui l'exploite. Invocable seule ; `backlog` la propose sans l'imposer.

## Nouveau concept OKF : `Sprint`

Nouveau bundle `kb/sprints/`. Un `Sprint` :

```markdown
---
type: Sprint
title: <nom du sprint>
description: <objectif ou période>
tags: []
state: planned
generated: { by: hosa-sprint-planner/1.0, at: <ISO8601> }
---
## Tickets
- [<titre>](../tickets/<slug>.md)
- [<titre>](../tickets/<slug>.md)
```

`state` suit le même cycle que les autres concepts pilotés dans le temps :
`planned | active | done`.

## Modification au concept `Ticket`

`hosa-product-owner` (`agents/product-owner.md`) et `backlog` gagnent un
champ de frontmatter optionnel sur `Ticket` : `sprint: <slug>` — rempli
uniquement quand un ticket est effectivement dispatché dans un sprint.
Absent tant qu'un ticket reste dans le backlog non planifié.

## Agent `hosa-sprint-planner`

`agents/sprint-planner.md`, frontmatter :
```yaml
name: hosa-sprint-planner
model: claude-opus-4-8
memory: project
```

Rôle : compose chaque sprint à partir du Product Backlog (`kb/tickets/`).
Ne priorise pas lui-même — reprend l'ordre de priorité déjà tenu par
`hosa-product-owner` — mais est garant que rien n'entre dans un sprint
sans que sa faisabilité technique et son placement architecture aient été
réellement évalués (pas seulement la ligne de repli laissée par
`backlog` quand `stack`/`architecture` n'avaient pas encore tourné).

### Input

Une demande de planification de sprint, avec une capacité (nombre de
tickets) — si absente, la demande à l'utilisateur ; pas d'estimation
automatique de complexité, aucun champ de ce type n'existe sur `Ticket`
aujourd'hui.

### Process

1. Lit `kb/tickets/` pour les `Ticket` `state: todo` sans champ `sprint`
   déjà rempli.
2. Reprend l'ordre de priorité tel que tenu par `hosa-product-owner` (relit
   le backlog dans son état courant ; si l'ordre n'est pas explicite,
   demande à l'utilisateur ou à `hosa-product-owner` plutôt que de
   deviner).
3. Pour chaque ticket dans cet ordre, jusqu'à capacité atteinte :
   - Lit ses sections `Note technique (senior dev)` et
     `Placement architecture (architecte)` (écrites par `backlog`).
   - Si l'une des deux est encore la ligne de repli ("Stack pas encore
     choisie…" / "Architecture pas encore scaffoldée…"), le dit et propose
     de combler le manque maintenant (lancer `stack`/`architecture`, ou
     obtenir un avis réel de `hosa-senior-dev`/`hosa-architect`) plutôt que
     d'engager le ticket sans savoir si c'est réalisable.
   - Si l'utilisateur comble le manque, relit la note mise à jour et
     réévalue ce ticket. Si le manque reste non comblé, ce ticket n'entre
     pas dans ce sprint — il reste dans le backlog, capacité inchangée.
   - Sinon (les deux notes sont réelles), assigne le ticket : écrit
     `sprint: <slug>` dans son frontmatter, l'ajoute à la liste du
     `Sprint`.
4. Écrit le `Sprint` dans `kb/sprints/<slug>.md`, `state: planned`.
5. Log dans `kb/sprints/log.md` et `kb/tickets/log.md` (frontmatter des
   tickets modifié) — OKF §9.

### Output

```
## Sprint composé
- `kb/sprints/<slug>.md` — [nom] (capacité: N, state: planned)

## Tickets inclus
- `kb/tickets/<slug>.md` — [titre]

## Tickets écartés (manque technique)
- `kb/tickets/<slug>.md` — [ce qui manque, proposé et décliné/différé]

## Open Questions
[Si rien : "None"]
```

### No Commits

Ne commit jamais — même règle que tous les agents Hosa.

### Project Memory

Sauvegarde : la cadence de sprint déjà convenue avec l'utilisateur (durée,
capacité habituelle), pour ne pas la redemander à chaque fois. Ne
sauvegarde pas : le contenu d'un sprint déjà écrit — relisible depuis
`kb/sprints/`.

## Skill `skills/sprint/SKILL.md`

**Trigger manuel :** `/sprint [capacité]`. **Auto :** immédiatement après
`backlog`, ou "planifie un sprint", "compose le prochain sprint".

**Flow :** voir Process ci-dessus (le skill reprend le rôle de l'agent en
ligne, même principe que `stack`/`architecture`/`backlog`).

**Sortie :** voir format agent ci-dessus, plus :
```
## Suite
Sprint prêt. Je lance un autre sprint pour le reste du backlog, ou on
s'arrête là ?
```

## Modification à `backlog`

Le `## Suite` actuel ("Pipeline de structuration des données terminé.")
est retiré. À la place : "Je lance `sprint` maintenant ?"

## Registre dans `using-simflow`

`sprint` est ajouté à la table des skills — décrit comme la suite du
pipeline de structuration des données plutôt que comme une de ses étapes
(cf. note de nommage ci-dessus) — et à la table de triggers auto.

## Hors scope (v1)

- Exécution du sprint une fois composé (passage des tickets à `doing`,
  suivi d'avancement) — reste piloté manuellement par l'utilisateur et
  `hosa-product-owner`, comme aujourd'hui.
- Estimation de complexité/effort par ticket — pas de nouveau champ sur
  `Ticket` en v1 ; la capacité reste un nombre de tickets donné par
  l'utilisateur.
- Rotation automatique (clore un sprint `active` et en ouvrir un nouveau)
  — un `Sprint` change de `state` manuellement, comme tout concept OKF
  suivi dans le temps.
- Rétro-planification si un ticket déjà dans un sprint change de note
  technique/architecture après coup — pas de détection de drift, même
  principe que le reste du pipeline.
