# Hosa — pipeline de rédaction du cahier des charges

**Date:** 2026-09-24
**Statut:** en attente de revue

## Contexte

Le skill `hosa` (voir `docs/simflow/specs/2026-09-23-hosa-pilotage-design.md` et
`skills/hosa/SKILL.md`) initialise l'identité du projet et les personas, puis
les enrichit via `hosa-key-user`. Une fois les personas finalisés, il n'existe
aucun moyen structuré de transformer leurs besoins en cahier des charges — les
`Exigence` de `kb/cdc/` restent à créer manuellement.

Cette itération construit ce pipeline : quatre skills qui interviewent,
rédigent, relisent et challengent le cahier des charges jusqu'à ce qu'il soit
précis, complet et cohérent — avec traçabilité OKF de bout en bout.

## Objectif

Obtenir, processus métier par processus métier, un cahier des charges
(`kb/cdc/`) qui précise pour chacun : son objectif, ses données en entrée, ses
données en sortie, qui fait quoi, qui est responsable, et quel(s) besoin(s)
persona il sert — sans zones vagues ni contradictions.

## 1. Agents

### Réutilisés

- **`hosa-product-owner`** — mène l'interview, rédige les `Exigence`, les
  relit, et challenge les personas en direct sur les points faibles.
- **`hosa-key-user`** — répond en restant dans la peau du persona interrogé.
  Gagne un troisième mode d'interaction (voir §1.3).

### Nouveau : `hosa-challenger`

`agents/challenger.md`, frontmatter `name: hosa-challenger`, `model:
claude-opus-4-8`, `memory: project`.

Rôle : auditer le cahier des charges *assemblé*, sans l'avoir écrit — un
regard neuf plutôt qu'une relecture par son propre auteur. Lit l'ensemble de
`kb/cdc/` et `kb/personnas/` et cherche :
- Contradictions entre exigences (ex : deux processus désignent des
  responsables incompatibles, la sortie d'un processus ne correspond pas à
  l'entrée attendue du suivant)
- Angles morts : besoins exprimés par un persona qui ne sont couverts par
  aucune exigence
- Hypothèses non dites (une exigence qui suppose un fait jamais vérifié)
- Risques (dépendances fragiles, responsabilité non assignée, cas limites
  non couverts)

Sortie : verdict `Aucune anomalie` / `Anomalies trouvées` + liste précise
(quelle exigence, quel problème, ce qui manque). Ne modifie jamais la KB — ne
fait que rapporter. Pas de commit. Mémoire projet : types d'angles morts
récurrents sur ce projet — pas le contenu d'une session d'audit donnée.

### 1.3 Nouveau mode pour `hosa-key-user`

En plus de l'identification et de la recette (déjà spécifiées dans
`agents/key-user.md`), `hosa-key-user` gagne un mode **interview processus** :
le PO lui pose des questions ciblées sur un processus métier précis (son
objectif pour ce persona, ce dont il a besoin en entrée, ce qu'il produit,
comment il procède concrètement). Il répond en restant dans la peau du
persona. Si une réponse révèle un nouveau pain point ou quick win, il l'ajoute
aux sections `Pain points` / `Quick wins` déjà présentes sur la fiche persona
— même logique que pendant une recette. Il ne réécrit pas les sections
`Besoins`/`Attentes` à cette occasion : celles-ci restent la responsabilité du
mode identification.

## 2. Schéma `Exigence` enrichi

Le frontmatter OKF de `Exigence` (type/title/description/tags/status/
generated/verified) reste inchangé — seul le corps markdown gagne une
structure obligatoire, sur le même principe que celle ajoutée à `Persona` :

```markdown
## Objectif du processus
<ce que ce processus accomplit, une à deux phrases concrètes>

## Données en entrée
- <donnée nécessaire pour déclencher/exécuter le processus>

## Données en sortie
- <donnée produite par le processus>

## Qui fait quoi
- <rôle/persona> : <action concrète>

## Responsable
<rôle ou persona responsable du bon déroulement du processus>

## Besoin(s) persona répondu(s)
- [persona](../personnas/<slug>.md) : <besoin précis auquel ce processus répond>
<ou "Aucun — exigence transverse" si le processus ne sert aucun persona en particulier>
```

Un fichier `Exigence` par processus métier, nommé
`kb/cdc/<slug-processus>.md`.

## 3. Les quatre skills

Nouveau dossier par skill, même conventions que l'existant (frontmatter
`name`/`description`, diagramme de flux, sections pas-à-pas). Chacun est
invocable seul (pas de point d'entrée forcé) mais ils forment un pipeline
naturel : interview → rédaction → relecture → contestation → (boucle vers
rédaction ou interview si besoin) → jusqu'à propre.

### 3.1 `skills/interview/SKILL.md`

**Trigger manuel :** `/interview`. **Auto :** "rédige le cahier des
charges", "interview les personas", ou acceptation de la proposition faite
par `hosa` en fin de flow personas (§4).

**Flow :**
1. Demande à l'utilisateur la liste des grands processus métier à couvrir
   (le PO ne peut pas la deviner — c'est une info transverse). Un processus à
   la fois, jusqu'à "terminé".
2. Pour chaque processus : identifie quels personas sont concernés (demande à
   l'utilisateur si ambigu). Pour chacun, dispatch `hosa-key-user` en mode
   interview processus (§1.3) : objectif du persona dans ce processus,
   données en entrée/sortie de son point de vue, ce qu'il fait concrètement.
3. Pour tout ce qui ne relève d'aucun persona en particulier (qui est
   responsable au global, contraintes transverses, priorité), le PO interroge
   directement l'utilisateur.
4. Le PO challenge en direct toute réponse vague ou un besoin qui semble
   injustifié — une relance, pas une boucle longue (l'audit approfondi est le
   rôle de `contestation`).
5. Ne touche pas la KB — restitue les notes structurées, processus par
   processus, prêtes pour `redaction`.

**Sortie :** notes structurées (par processus : objectif/entrée/sortie/
qui-fait-quoi/responsable/besoins persona), affichées à l'utilisateur, et
proposition d'enchaîner sur `redaction` avec ces notes.

### 3.2 `skills/redaction/SKILL.md`

**Trigger manuel :** `/redaction`. **Auto :** immédiatement après
`interview`, ou "rédige les exigences" avec des notes fournies inline si
`interview` n'a pas tourné dans cette session.

**Flow :**
1. Source des notes : la sortie d'`interview` dans cette session, ou notes
   inline de l'utilisateur.
2. Pour chaque processus, le PO écrit une `Exigence` (§2) dans `kb/cdc/`,
   `status: draft`. `generated: { by: hosa-product-owner/1.0, ... }` sauf si
   l'utilisateur a dicté le contenu mot pour mot (`human:<user>`).
3. Log dans `kb/cdc/log.md` (OKF §9).

**Sortie :** liste des `Exigence` créées/mises à jour, proposition
d'enchaîner sur `relecture`.

### 3.3 `skills/relecture/SKILL.md`

**Trigger manuel :** `/relecture`. **Auto :** immédiatement après
`redaction`, ou "relis le cahier des charges".

**Flow :**
1. Le PO relit chaque `Exigence` de `kb/cdc/` (ou seulement celles modifiées
   dans cette session, si appelé juste après `redaction`) : les 6 sections
   sont-elles remplies, précises, sans placeholder ni généralité ? Cohérence
   entre exigences (sorties/entrées qui s'enchaînent, responsables non
   contradictoires) ?
2. Pour chaque anomalie : quelle exigence, quel problème précis, ce qu'il
   faut pour corriger.

**Sortie :** `Propre` (aucune anomalie) ou liste des anomalies avec, pour
chacune, une proposition de retour vers `redaction` (contenu à corriger) ou
`interview` (info manquante). Si `Propre`, propose d'enchaîner sur
`contestation` pour la passe finale.

### 3.4 `skills/contestation/SKILL.md`

**Trigger manuel :** `/contestation`. **Auto :** immédiatement après une
`relecture` propre, ou "challenge le cahier des charges".

**Flow :**
1. **Passe PO → personas** : pour chaque point faible connu (des anomalies
   de `relecture`, ou si appelé seul, une relecture rapide par le PO
   lui-même), le PO re-questionne le(s) persona(s) concerné(s) via
   `hosa-key-user` — "pourquoi ce besoin précisément", "que se passe-t-il si
   on ne le fait pas", jusqu'à obtenir une réponse solide ou constater que le
   besoin ne tient pas.
2. **Passe `hosa-challenger`** : dispatch avec l'ensemble de `kb/cdc/` et
   `kb/personnas/`. Reçoit son verdict et sa liste d'anomalies.
3. Si l'une ou l'autre passe trouve des anomalies : route vers `redaction`
   (récriture) ou `interview` (info manquante réellement absente), puis
   reboucle sur `relecture` → `contestation` jusqu'à ce que les deux passes
   soient propres.
4. Une fois propre : demande à l'utilisateur la validation finale. Sur
   confirmation, le PO passe `status: stable` et ajoute
   `verified: { by: human:<user>, at: <ISO8601> }` sur chaque `Exigence`
   touchée dans ce cycle, puis log dans `kb/cdc/log.md`.

**Sortie :** verdict final, liste des `Exigence` passées en `stable`, et
tout point resté ouvert si l'utilisateur ne valide pas encore.

## 4. Déclenchement depuis `hosa`

Dans `skills/hosa/SKILL.md`, section "Enriching personas" (déjà en place) :
une fois l'enrichissement terminé pour tous les personas traités dans cette
session (que ce soit le flow d'init ou un ajout de persona standalone), le
skill propose — sans enchaîner automatiquement (choix validé avec
l'utilisateur, une interview de cahier des charges est trop longue pour
démarrer sans accord explicite) :

> "Personas prêts. Lancer l'interview du cahier des charges maintenant ?
> (skill `interview`)"

Oui → invoque `interview`. Non → s'arrête normalement ; `interview` reste
invocable manuellement plus tard.

## 5. Registre dans `using-simflow`

Les quatre skills sont ajoutés à la table de `skills/using-simflow/SKILL.md`
et à la table de triggers auto, même format que les entrées existantes
(`hosa`, `recette`).

## Hors scope (v1)

- Auto-enchaînement complet sans validation utilisateur à aucune étape
  (chaque transition se propose, ne s'impose pas, sauf interview→redaction
  qui est un pur passage de notes sans écriture KB donc non bloquant)
- Nouveau type OKF pour stocker le rapport de `contestation` — reste un
  rapport conversationnel, pas un concept KB (même logique que
  `simflow-reviewer`, dont le verdict n'est pas persisté)
- Détection automatique des processus métier à partir du code ou de la KB —
  la liste des processus est fournie par l'utilisateur en début d'`interview`
