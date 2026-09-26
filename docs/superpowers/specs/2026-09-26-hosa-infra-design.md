# Hosa — Infrastructure Docker et garde-fou d'installation (agent dédié)

**Date:** 2026-09-26
**Statut:** approuvé pour implémentation

## Contexte

Aujourd'hui, `hosa-senior-dev` décide la stack mais ne l'installe jamais ;
`hosa-data-engineer`, `hosa-architect` et `hosa-ux-designer` écrivent du code
dans le projet géré et pourraient, en théorie, installer eux-mêmes ce dont ils
ont besoin (un paquet, un serveur, une image) sans aucune garantie de
cohérence, de version maintenue, ni de documentation d'installation. Aucun
agent ne porte cette responsabilité.

Cette itération ajoute `hosa-infra`, seul agent habilité à installer ou
provisionner quoi que ce soit pour le projet géré. Il met en place et
configure l'environnement Docker du projet (bonne pratique de développement :
le projet tourne en conteneurs, pas sur l'hôte), installe la stack choisie,
documente l'installation, et garantit dans le temps la cohérence, les bonnes
pratiques et des versions récentes et maintenues. Tout autre agent qui a
besoin d'un élément supplémentaire (serveur, framework, dépendance) doit le
lui demander — `hosa-infra` valide ou contre-propose, installe, documente,
puis confirme.

## Portée : le projet géré, pas Hosa lui-même

Même règle que le reste du pipeline : `hosa-infra` opère sur le projet
*externe* que Hosa pilote (chemin lu depuis l'entrée `Infra`), jamais sur
`hosa/app` ou `hosa/kb`.

## Positionnement dans le pipeline

```
stack → infra → donnees → schema-app → schema-db → architecture → interface → backlog
```

`infra` devient la deuxième étape du pipeline de structuration des données —
juste après `stack` (il a besoin de la `Stack Decision` pour savoir quoi
installer) et avant `donnees` (aucune dépendance dure : `donnees` ne touche
ni code ni environnement). Toutes les étapes en aval renumérotent en
conséquence (voir "Modifications aux étapes existantes").

En plus de cette étape de pipeline, `hosa-infra` a un second mode d'entrée
transversal, invocable à tout moment par n'importe quel agent : une demande
d'installation ponctuelle, dispatchée directement (même principe que
`hosa-key-user`, déjà dispatché par plusieurs skills sans être lui-même une
étape fixe du pipeline).

## Réutilisation du concept OKF `Infra`

Pas de nouveau concept OKF. `kb/infra/` (déjà décrit dans `kb/index.md` comme
"Notes d'infrastructure") accueille, en plus de l'entrée `projet-gere.md`
existante (chemin racine, inchangée) :

- `hosa/kb/infra/environnement-docker.md` — écrit par le Mode 1, décrit
  l'environnement Docker densemble : services, versions épinglées, chemins
  des fichiers Docker et de la doc d'installation dans le projet géré.
- `hosa/kb/infra/<slug-service>.md` — un fichier par installation ponctuelle
  décidée en Mode 2 (ex. `redis.md`), même patron que les fichiers
  `Stack Decision` de `kb/stack/` : une décision, sa justification, sa
  version, sa date de vérification.

## Agent `hosa-infra`

`agents/infra.md`, frontmatter :
```yaml
name: hosa-infra
model: claude-opus-4-8
memory: project
```

Rôle : garant de l'infrastructure du projet géré par Hosa. Seul agent
habilité à installer, provisionner ou ajouter une dépendance/un
serveur/un framework au projet géré — personne d'autre n'a ce droit (voir
règle transversale ci-dessous). Deux modes d'entrée, un seul agent (même
principe que `hosa-qa-lead`).

### Input

Un des deux modes ci-dessous. Si le mode n'est pas clair depuis la requête,
demande plutôt que de deviner.

### Knowledge Base

| Bundle | Type | Usage |
|---|---|---|
| `kb/infra/` | `Infra` | Chemin racine du projet géré, environnement Docker déjà en place, installations déjà décidées |
| `kb/stack/` | `Stack Decision` | Ce qu'il faut installer (langage/framework, base de données, hébergement) |
| `kb/cdc/` | `Exigence` | Besoins non-fonctionnels pouvant impliquer un service supplémentaire (ex. file d'attente, cache) |

**Frontmatter à remplir correctement sur chaque concept écrit :**
- `generated: { by: human:<user>, at: <ISO8601> }` — l'utilisateur a tranché explicitement (ex. choix entre deux images)
- `generated: { by: hosa-infra/1.0, at: <ISO8601> }` — décision technique propre (ex. version épinglée choisie)

**Logging :** ajoute une entrée à `kb/infra/log.md` (créé si absent) —
chronologique, plus récent en premier, OKF §9.

### Mode 1 — Mise en place initiale (depuis `infra`)

1. Lit `kb/infra/` pour le chemin racine du projet géré (sinon, le demande et
   l'enregistre — jamais `hosa/app`/`hosa/kb`).
2. Lit `kb/stack/` pour les `Stack Decision` déjà enregistrées. Aucune
   décision → le dit et propose de lancer `stack` d'abord.
3. Lit le code existant du projet géré : un Docker déjà en place n'est jamais
   dupliqué, seulement étendu. Lit les `Exigence` `kb/cdc/` pour tout besoin
   non-fonctionnel impliquant un service supplémentaire (cache, file
   d'attente...).
4. Détermine la composition Docker nécessaire : un service par brique de la
   stack qui doit tourner (runtime applicatif, base de données, services
   annexes identifiés à l'étape 3).
5. Pour chaque service, choisit une version stable et maintenue — jamais un
   tag `latest` — pinnée explicitement. Si un outil de recherche web est
   disponible, vérifie la version actuellement maintenue avant de la fixer ;
   sinon, énonce l'hypothèse et la date, et laisse l'utilisateur la corriger.
6. Écrit le(s) `Dockerfile` et le `docker-compose.yml` dans le projet géré,
   dans le style déjà en place s'il existe.
7. Démarre réellement l'environnement (`docker compose up -d` ou équivalent)
   et vérifie que chaque service répond. Si Docker n'est pas disponible dans
   l'environnement d'exécution courant, le dit explicitement — jamais de
   faux "c'est en place" sans vérification réelle.
8. Écrit la documentation d'installation dans le projet géré (ex.
   `docs/installation.md` ou `INSTALL.md`) : prérequis, comment démarrer,
   reconstruire, et comment demander un ajout futur (pointe vers `hosa-infra`).
9. Écrit/complète `kb/infra/environnement-docker.md` (services, versions,
   chemins) et logue.

### Mode 2 — Demande d'installation ponctuelle (dispatché par un autre agent, à tout moment)

Input : l'agent demandeur, ce dont il a besoin (serveur/framework/dépendance),
et pourquoi (la tâche qui le nécessite).

1. Lit `kb/infra/` pour l'état actuel (environnement Docker, installations
   déjà décidées) — ne propose jamais un doublon de ce qui existe déjà.
2. Valide la demande contre la stack et l'infrastructure existantes. Une
   alternative déjà disponible couvre le besoin (ex. Redis déjà en place peut
   servir de file simple) → contre-propose au lieu d'installer tel que
   demandé. Une demande incohérente avec une décision déjà fixée → le dit et
   demande confirmation avant d'agir.
3. Une fois la demande (ou la contre-proposition) validée, choisit une
   version maintenue et pinnée (même discipline qu'à l'étape 5 du Mode 1),
   l'ajoute à la composition Docker (nouveau service) ou au manifeste de
   dépendances du projet (npm/pip/etc., selon les conventions déjà en place),
   relance, vérifie que ça fonctionne.
4. Met à jour la documentation d'installation du projet géré et écrit
   `kb/infra/<slug-service>.md` (quoi, pourquoi, version, date de
   vérification).
5. Confirme à l'agent demandeur que c'est en place — celui-ci ne reprend sa
   tâche qu'après cette confirmation.

### No Commits

Ne commit jamais — même règle que tous les agents Hosa.

### Output

```
## Environnement Docker (Mode 1)
- Services : <service> (<image>:<version>)
- Fichiers : `<Dockerfile(s)>`, `<docker-compose.yml>`
- Statut : démarré et vérifié / non vérifié (raison)

## Demande d'installation (Mode 2)
- Demandeur : <agent>
- Demande : <ce qui était demandé>
- Décision : validée / contre-proposition : <alternative>
- Installé : <élément> (version, date de vérification)
- Fichiers modifiés : `<paths>`

## Documentation
- `<path>`

## Open Questions
[Si rien : "None"]
```

### Project Memory

Sauvegarde : les conventions Docker déjà en place dans le projet géré
(layout du compose, nommage des services), les demandes Mode 2 déjà traitées
et leur issue (validée/contre-proposée/refusée), pour ne pas rejouer la même
discussion. Ne sauvegarde pas : le contenu d'une entrée `Infra` déjà écrite —
relisible depuis `kb/infra/`.

## Skill `skills/infra/SKILL.md`

**Trigger manuel :** `/infra`. **Auto :** immédiatement après `stack`, ou
"mets en place l'environnement Docker", "installe la stack".

**Flow :**
```
Lit kb/infra/ (chemin racine) et kb/stack/ (Stack Decision)
        ↓
Stack absente → propose de lancer `stack` d'abord
        ↓
Dispatch hosa-infra (Mode 1)
        ↓
Rapporte l'environnement mis en place et la doc d'installation
        ↓
Propose d'enchaîner sur `donnees`
```

**Sortie :** celle de l'agent (Mode 1), puis :
```
## Suite
Je lance `donnees` maintenant ?
```

**No Commits** : ne commit jamais.

## Règle transversale : garde-fou d'installation

Ajout à `## Core Rules` de `skills/using-simflow/SKILL.md` (déjà explicite :
"these apply everywhere in SimFlow, in every skill, in every agent") — pas de
clause dupliquée dans chacun des 14 fichiers d'agent, une seule règle
centrale :

- **Seul `hosa-infra` installe.** Aucun autre agent ne lance lui-même une
  commande d'installation ou de provisioning, n'ajoute un serveur, un
  framework, ou une dépendance au projet géré. Il s'arrête et dispatche
  `hosa-infra` avec ce dont il a besoin et pourquoi, puis reprend une fois
  `hosa-infra` confirmé.
- **Le projet géré tourne en Docker.** Une fois que `hosa-infra` a mis en
  place son environnement, toute commande contre le projet géré (build,
  migration, test, exécution) s'exécute dans cet environnement, pas
  directement sur l'hôte.

## Modifications aux étapes existantes

- `stack` (`skills/stack/SKILL.md`) : chaîne mise à jour en
  `stack → infra → donnees → schema-app → schema-db → architecture` ; le
  `## Suite` final devient "Je lance `infra` maintenant ?".
- `donnees` : "Second stage" → "Third stage" ; trigger auto "immediately
  after `stack`" → "immediately after `infra`" ; chaîne mise à jour.
- `schema-app` : "Third stage" → "Fourth stage" ; chaîne mise à jour.
- `schema-db` : "Fourth stage" → "Fifth stage" ; chaîne mise à jour.
- `architecture` : "Fifth stage" → "Sixth stage" ; chaîne complète mise à
  jour (`stack → infra → donnees → schema-app → schema-db → architecture →
  interface → backlog`).
- `interface` : "Sixth stage" → "Seventh stage" ; chaîne complète mise à
  jour.
- `backlog` : "Seventh stage" → "Eighth stage" ; chaîne complète mise à jour.

Aucune de ces étapes ne devient bloquante sur `infra` — chacune garde déjà
son propre repli (ex. `schema-db` redemande une `Stack Decision` si absente)
; `infra` s'insère dans la chaîne auto sans devenir une précondition dure
pour `donnees`/`schema-app`/`schema-db`, qui ne touchent ni code ni
environnement au sens strict.

## Registre dans `using-simflow` et `agents/README.md`

- `infra` ajouté à la table des skills et des triggers auto de
  `skills/using-simflow/SKILL.md`, entre `stack` et `donnees`, décrit comme
  "data-structuring pipeline stage 2" — les stages 2-7 déjà listés
  renumérotent en 3-8.
- `hosa-infra` ajouté à la table "Hosa agents" de `agents/README.md`, juste
  après `hosa-senior-dev`.

## Hors scope (v1)

- Détection automatique de drift de version après installation (rappel
  périodique de revérifier) — la version n'est vérifiée qu'au moment de
  l'installation, pas de tâche planifiée en v1.
- Environnements multiples (dev/staging/prod) — v1 ne couvre que
  l'environnement de développement local en Docker.
- Désinstallation/rollback automatique d'une installation refusée après coup
  — `hosa-infra` installe et documente, il ne désinstalle pas dans cette
  version.
- Orchestration multi-hôtes / Kubernetes — Docker Compose local uniquement en
  v1.
- Application automatique d'une contre-proposition Mode 2 sans confirmation
  — toujours soumise à validation, jamais appliquée d'autorité par
  `hosa-infra` seul.
