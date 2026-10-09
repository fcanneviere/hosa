# Hosa

**Hosa est un plugin Claude Code qui pilote un projet logiciel de bout en bout** : du cahier des charges aux sprints livrés, avec une équipe d'agents spécialisés (Product Owner, UX designer, architecte, expert sécurité, DBA, testeur…). Tout ce qui est décidé est écrit dans une base de connaissances versionnée, dans le projet lui-même.

## Installer le plugin

Dans Claude Code :

```text
/plugin marketplace add fcanneviere/hosa
/plugin install hosa@hosa
```

Pour mettre à jour : `/plugin`, puis mettre à jour `hosa`. Hosa démarre tout seul à chaque session ouverte dans un projet.

Prérequis côté projet géré : `git`, Docker et Python 3.10 ou plus.

## Comment ça marche

### Trois enchaînements

1. **Cahier des charges** — `hosa` (identité du projet, personas) → `interview` → `redaction` → `fondamentaux` → `securite` → `relecture` → `contestation`.
   Les fonctions de base (administration, utilisateurs, logs, sauvegarde, import/export…) et les contraintes de sécurité y entrent dès le départ, pas à la fin.
2. **Structuration** — `stack` → `infra` → `donnees` → `schema-app` → `schema-db` → `architecture` → `securite` (modèle de menaces) → `interface` → `backlog`.
   `infra` installe aussi les outils qualité : tests, tests navigateur, linter, formateur, CI.
   Chaque ticket du backlog naît complet : story, critères d'acceptation, notes technique, architecture, interface et sécurité. Les gros besoins sont découpés en tickets livrables, avec leurs dépendances. Les exigences non fonctionnelles (performance, accessibilité…) forment une « définition de terminé » vérifiée sur chaque ticket.
3. **Chaque sprint** — `sprint` → `qa-plan` → démarrage (`git`) → `develop` → `qa` → `validation` → fusion (`git`) → `bilan-sprint` → `livraison`.
   Les tests sont écrits avant le code, sécurité comprise. Chaque ticket passe la suite complète, le linter et une revue de code avant son commit. Un défaut trouvé est corrigé dans le sprint. Avant la fusion, tu fais une courte démo (tests T1, T2…). Chaque sprint a sa branche, son worktree et son propre environnement Docker. La fusion ne touche la branche principale qu'avec du code déjà testé.
   La livraison passe un audit qualité, crée une version testée et taguée, puis la déploie si tu le demandes, après une sauvegarde de la base.

Hosa enchaîne les étapes tout seul. Il ne s'arrête que pour tes vraies décisions : choix produit, validation du cahier des charges, proposition de sprint, démo, fusion, livraison.

Tu n'as pas besoin de connaître ces noms : décris ce que tu veux (« prépare le prochain sprint », « où en est-on ? ») et Hosa lance le bon skill. Tu peux aussi taper `/<skill>`.

### Les agents

Les skills orchestrent, les agents font le travail, chacun dans son domaine : `hosa-product-owner`, `hosa-key-user` (incarne un persona), `hosa-challenger`, `hosa-security`, `hosa-senior-dev`, `hosa-infra`, `hosa-data-engineer`, `hosa-dba`, `hosa-architect`, `hosa-ux-designer`, `hosa-sprint-planner`, `hosa-qa-lead`, `hosa-tech-lead`, `hosa-developer`, `hosa-tester`, `hosa-git`, `hosa-documentation`. Chaque agent tourne sur le modèle adapté à son travail (Opus, Sonnet ou Haiku).

### La base de connaissances (KB)

- Elle vit dans le projet, dans `.hosa/kb/`, sur sa **propre branche git `hosa-kb`** : elle ne se mélange jamais au code ni aux sprints.
- Chaque commit de la KB note le commit du code correspondant.
- `/kb-commit` la committe ; sur un projet existant, `/kb-commit migrer` la déplace sur sa branche (le plan est montré avant toute action).
- Sur un nouveau poste, Hosa extrait la branche `hosa-kb` tout seul.

### Reprendre où on s'est arrêté

Hosa tient un **plan d'avancement** (`.hosa/kb/project/avancement.md`). Si une session s'arrête (limite atteinte, coupure), la suivante reprend à l'étape, au ticket et à la tâche exacts. Il refuse aussi de sauter une étape sans ton accord.

### Le dépôt git

Hosa gère le dépôt dès le premier fichier : il l'initialise et commite à chaque étape (le code sur la branche principale, la KB sur `hosa-kb`). Tu n'as pas à le lui demander.

### Les retours sur Hosa

Quand un agent bute sur une consigne de Hosa (contradiction, étape manquante, contournement), il le note dans `.hosa/kb/retours-hosa/journal.md`. `/status` montre les retours les plus fréquents : c'est la liste des améliorations à apporter au plugin.

### Ce que tu reçois en retour

- La réponse d'abord, en phrases courtes.
- Les questions qui attendent ta réponse sont numérotées, avec des options : réponds en une ligne, par exemple `Q1 a, Q2 b`.
- Les tests à faire toi-même sont numérotés T1, T2…, avec le lien, le compte de test et le résultat attendu : réponds `T1 OK, T2 KO : …`.

## Recommandé : la recherche par le sens avec `ccc`

Hosa indexe déjà le code (graphe des fonctions, appels, impacts) et la KB (sommaire, extraction précise). Avec [cocoindex-code](https://github.com/cocoindex-io/cocoindex-code), les agents peuvent en plus **chercher par ce que fait le code, et pas seulement par son nom** (« où sont gérées les sessions ? »). Ils lisent moins de fichiers, donc consomment moins.

Hosa l'utilise s'il est installé, et ne l'installe jamais lui-même :

```bash
pipx install 'cocoindex-code[full]'      # modèle local inclus, environ 1 Go
# ou, sans le modèle local (clé d'API d'un fournisseur d'embeddings) :
pipx install cocoindex-code
```

Les agents l'initialisent et le tiennent à jour. Tu peux aussi le faire toi-même, à la racine du projet et dans la KB :

```bash
ccc init && ccc index
(cd .hosa/kb && ccc init && ccc index)
```

## L'interface : choisir sur des pages de comparaison

Le skill `interface` ne te décrit pas l'interface en paragraphes. Il te la montre, en trois manches, chacune sur une page de comparaison à ouvrir dans ton navigateur :
1. **Styles** — 4 à 6 cartes de style sur le vrai contenu du projet. Tu en choisis une.
2. **Directions** — la navigation, le lexique et 2 ou 3 mises en page vraiment différentes de l'écran principal.
3. **Pages** — une page complète par espace (front office, back office), à valider avant la construction.

L'interface construite est ensuite vérifiée sur des captures (ordinateur et mobile), puis notée par une revue indépendante. Pour les captures, le poste a besoin de Node 22 et d'un Chrome ou Chromium. Sans eux, Hosa te donne des tests à faire toi-même.

La méthode et les outils viennent d'[oil-ui](https://github.com/oil-oil/oil-ui) (licence MIT), copiés dans `skills/interface/vendor/oil-ui/`.

## Commandes utiles

| Tu veux… | Demande ou tape |
|---|---|
| savoir où en est le projet | « où en est-on ? » ou `/status` |
| voir ce que consomme chaque agent | « consommation par agent » |
| démarrer le cahier des charges | « initialise le projet », puis « rédige le cahier des charges » |
| préparer et lancer un sprint | « planifie un sprint » |
| développer un ticket | « développe le ticket X » |
| tester un ticket du point de vue d'un persona | « fais une recette de X avec [persona] » |
| auditer le code | `/qualite` |
| opérer la base de données | `/bdd` (migrations, sauvegarde, base de test…) |
| livrer | « prépare la release » |

## L'application web

Une interface locale affiche la KB : pipelines, backlog, sprints, personas.

```bash
python run.py
```

Elle installe ses dépendances (`hosa/app/requirements.txt`) et démarre sur http://localhost:3000. Variables optionnelles :
- `PORT` : port d'écoute (défaut `3000`) ;
- `HOSA_KB_ROOT` : chemin vers la KB à afficher.

## Développer Hosa

- Les tests : `node --test hooks/*.test.js` et, dans `hosa/app`, `python -m unittest`. Ils tournent aussi sur GitHub à chaque push.
- Les règles communes à tous les skills et agents sont dans `skills/using-hosa/SKILL.md` ; le standard des retours dans `skills/retours/SKILL.md`.
