# Hosa

**Hosa est un plugin Claude Code qui pilote un projet logiciel de bout en bout** : du cahier des charges aux sprints livrés, avec une équipe d'agents spécialisés (Product Owner, UX designer, architecte, expert sécurité, DBA, testeur…). Tout ce qui est décidé est écrit dans une base de connaissances versionnée, dans le projet lui-même.

## Installer le plugin

Dans Claude Code :

```text
/plugin marketplace add fcanneviere/hosa
/plugin install hosa@hosa
```

Dans l'extension VS Code, `/plugin` n'existe pas : lance les mêmes commandes dans un terminal, `claude plugin marketplace add fcanneviere/hosa` puis `claude plugin install hosa@hosa`, puis recharge la fenêtre.

Pour mettre à jour : `/plugin`, puis mettre à jour `hosa`. Hosa démarre tout seul à chaque session ouverte dans un projet.

Prérequis côté projet géré : `git`, Docker et Python 3.10 ou plus.

## Comment ça marche

### Trois enchaînements

1. **Cahier des charges** — `hosa` (identité du projet, personas) → `interview` → `redaction` → `fondamentaux` → `juridique` → `securite` → `relecture` → `contestation`.
   Tu as déjà un brief en markdown ? `/hosa chemin/vers/brief.md` : Hosa en extrait les réponses et les personas, te les fait confirmer, et ne pose que les questions restantes.
   Les exigences restent des fiches, une par processus, avec leur domaine, leur priorité, leur lot et les objectifs qu'elles servent. Hosa les assemble en un document lisible, `kb/project/cahier-des-charges.md` : contexte, objectifs chiffrés, périmètre par lot, cartographie des processus, objets métier, contraintes, risques, décisions. Avant ta signature, un contrôle de complétude croise les matrices : objectifs × exigences, besoins des personas × exigences, états et droits de chaque objet, notifications, questions ouvertes. Une case vide bloque la signature.
   Les fonctions de base (administration, utilisateurs, logs, sauvegarde, import/export…) et les contraintes de sécurité y entrent dès le départ, pas à la fin.
2. **Structuration** — `stack` → `infra` → `donnees` → `schema-app` → `schema-db` → `architecture` → `securite` (modèle de menaces) → `interface` → `backlog`.
   `infra` installe aussi les outils qualité : tests, tests navigateur, linter, formateur, CI.
   Chaque ticket du backlog naît complet : story, critères d'acceptation, notes technique, architecture, interface, sécurité et juridique. L'expert sécurité et l'expert juridique transforment chaque cas d'abus et chaque contrainte juridique en critère d'acceptation : ils sont développés et testés avec le ticket, pas découverts à la recette. Les gros besoins sont découpés en tickets livrables, avec leurs dépendances, et les mécanismes de sécurité et de conformité passent avant les tickets qui les utilisent. Les exigences non fonctionnelles (performance, accessibilité…) forment une « définition de terminé » vérifiée sur chaque ticket.
3. **Chaque sprint** — `sprint` → `qa-plan` → démarrage (`git`) → `develop` → audit (`qualite`) → `qa` → `validation` → fusion (`git`) → `bilan-sprint` → `livraison`.
   Les tests sont écrits avant le code, sécurité comprise. Chaque ticket passe la suite complète, le linter et une revue de code avant son commit. Un défaut trouvé est corrigé dans le sprint. Chaque critère d'acceptation (CA1, CA2…) est prouvé par un test nommé. Avant la fusion, le code du sprint passe un audit qualité et sécurité, puis tu fais une courte démo (tests T1, T2…). Chaque sprint a sa branche, son worktree et son propre environnement Docker. La fusion ne touche la branche principale qu'avec du code déjà testé.
   Ces étapes ne sont pas que des consignes : un hook refuse le commit d'un ticket sans revue PASS, et la fusion d'un sprint sans audit, démo ou recettes validées. Après deux revues FAIL de suite sur un ticket, il refuse une 3ᵉ correction : c'est toi qui décides de la suite.
   La livraison passe un audit qualité, crée une version testée et taguée, puis la déploie si tu le demandes : en test, sans sauvegarde ni porte juridique ; en production, après une sauvegarde de la base et toutes les portes. Une version essayée en test passe en production sans refaire ses contrôles.

Hosa enchaîne les étapes tout seul. Il ne s'arrête que pour tes vraies décisions : choix produit, validation du cahier des charges, proposition de sprint, démo, fusion, livraison.

Tu n'as pas besoin de connaître ces noms : décris ce que tu veux (« prépare le prochain sprint », « où en est-on ? ») et Hosa lance le bon skill. Tu peux aussi taper `/<skill>`.

### Les agents

Les skills orchestrent, les agents font le travail, chacun dans son domaine : `hosa-product-owner`, `hosa-key-user` (incarne un persona), `hosa-challenger`, `hosa-legal`, `hosa-security`, `hosa-senior-dev`, `hosa-infra`, `hosa-data-engineer`, `hosa-dba`, `hosa-architect`, `hosa-ux-designer`, `hosa-sprint-planner`, `hosa-qa-lead`, `hosa-tech-lead`, `hosa-developer`, `hosa-tester`, `hosa-git`, `hosa-documentation`. Chaque agent tourne sur le modèle adapté à son travail (Opus, Sonnet ou Haiku).

### Quel modèle pour ta session

Les skills tournent dans ta session, sur le modèle choisi par `/model` : elle consomme l'essentiel des tokens, bien plus que les agents.

- **Toutes les phases** : Sonnet. La session orchestre : elle lance les agents, relaie leurs questions et écrit ce que tu décides. Les jugements difficiles restent sur Opus, portés par leurs agents : `hosa-challenger`, `hosa-legal`, `hosa-security`, `hosa-senior-dev`, `hosa-architect`, `hosa-reviewer`, `hosa-debugger`. Sur le pilote 2, Opus dans la session principale faisait 81 % de son coût.
- **Une session par étape.** La session relit tout son historique à chaque tour. Après chaque étape ou chaque ticket, lance `/clear`, puis « reprends » (ou `/reprendre`) : le plan d'avancement garde tout. Une session laissée ouverte une semaine a dépassé 500 000 tokens de contexte.
- **La reprise après `/clear`.** « reprends » lance le skill `reprendre` : un seul appel (`avancement.py reprendre`) donne la fiche de reprise — l'étape, son skill, le sprint, les tâches des agents faites et à faire, ce qui reste à prouver — et l'action suivante, faite dans le même tour. Avant, une reprise coûtait 11 appels et environ 530 000 tokens de contexte avant sa première action (médiane sur rieki, pilote 2 et hosa-ui). Si un agent de la session effacée travaille encore, la fiche le nomme : son rapport arrive dans la nouvelle session, qui ne relance pas son travail. La nouvelle session reçoit aussi, au démarrage, le chemin de la KB, la commande `<hosa>`, le point de reprise du plan, puis la session effacée : tes deux dernières demandes, la dernière réponse, les fichiers modifiés et l'état git. « reprends » repart donc de la tâche en cours, pas seulement de l'étape, dans un projet Hosa comme dans n'importe quel dépôt. Pour couper le rappel de la session effacée : `HOSA_REPRISE=0`.
- **Un démarrage que le modèle lit en entier.** Au-delà de 10 Ko, Claude Code range le contexte d'un hook dans un fichier et n'en montre que les 2 premiers Ko. Jusqu'à la 0.1.78, le démarrage en faisait 17 à 20 Ko : le modèle ne voyait ni les règles de `using-hosa` ni la commande `<hosa>`. Depuis la 0.1.79, deux hooks de moins de 10 Ko chacun : l'essentiel d'abord (KB, `<hosa>`, plan, session effacée), puis `using-hosa`, dont le détail des règles est dans `skills/using-hosa/regles.md`, lu à la demande.
- **Un seul compresseur : celui de Hosa.** Hosa condense déjà les sorties de commandes, mais laisse entiers les rapports d'agents et les fichiers lus. Un proxy qui compresse le contexte (Headroom, par exemple) coupe ces rapports sans que la session le voie : sur rieki, l'option C d'une question de `hosa-dba` a disparu, et la session a relancé l'agent pour rien. Dans un projet Hosa, ne passe pas par un tel proxy (`ANTHROPIC_BASE_URL` dans `.claude/settings.local.json`) et coupe RTK. Les agents recopient aussi leurs questions ouvertes dans le fichier KB qu'ils écrivent : une question survit à un rapport coupé. Au-delà de 10 000 caractères, une sortie de commande garde son début, sa fin et ses lignes d'erreur ; le texte entier reste sur disque (`HOSA_COMPRESS_MAX` règle le seuil).
- **Lire une fois, et seulement la partie utile.** Le hook `read-guard.js` refuse une fois la relecture d'un fichier qui n'a pas changé. Il refuse aussi une fois la première lecture complète d'un fichier de plus de 40 Ko (environ 10 000 tokens), et propose `kb_query` ou une plage de lignes. Le sommaire de la KB, les images et les PDF passent toujours. Une 2ᵉ tentative passe toujours. Le seuil se règle avec `HOSA_READ_MAX` (en octets). Pour couper ce hook : `HOSA_READ_GUARD=0`.
- **Des rapports d'agents courts.** Chaque rapport reste dans la session principale jusqu'au `/clear`, relu à chaque appel : sur rieki, 37 % dépassaient 4 000 caractères. Un agent garde son rapport sous 3 000 caractères, hors `## Open Questions` et `## Reprise` (toujours entiers), et met le détail dans les fichiers qu'il écrit. Au-delà de 4 000, `budget.js` refuse le rapport une fois ; le 2ᵉ essai passe. Les agents sans `Write` (challenger, reviewer, tech-lead), dont le rapport est le livrable, n'ont pas cette borne.
- **Les réveils.** Chaque agent qui finit réveille la session principale deux fois (son rapport, puis sa notification), et chaque réveil relit tout son contexte : 49 à 66 % des tokens de la session principale sur rieki et pilote 2. La session traite un rapport tout de suite, ce qui absorbe la notification, et finit sans texte un tour qui n'a rien à faire. `usage_report.py` mesure ces réveils.
- **Des règles communes aux agents, écrites une fois.** Le hook `subagent-start.js` les donne à chaque agent Hosa (lecture, rapport, format des questions) au lieu de 22 copies : grouper les appels indépendants dans un seul message, ne lire ni `retours` ni les skills de l'orchestrateur.
- **Des chemins entre agents, pas du texte.** Un agent qui a écrit des fichiers renvoie leurs chemins, avec une ligne sur ce qu'il faut en documenter. La session transmet ces lignes telles quelles à `hosa-documentation`, qui lit les sources. Elle ne réécrit plus le contenu dans la consigne : c'était des jetons de sortie, les plus chers, et une occasion d'oublier un détail.

Depuis Claude Code 2.1.290, Hosa le fait pour toi : la session passe d'elle-même sur Sonnet dans un projet Hosa. Une ligne sous le prompt affiche la phase et le remplissage du contexte. Quand une étape se termine et que le contexte dépasse 20 %, une notification propose `/clear`. Pour garder la main sur `/model` : `HOSA_MODELE=0`.

Un panneau « Hosa » montre où en est le projet : l'étape ouverte, les questions qui t'attendent, le point de reprise, les boucles ouvertes, les tâches des agents et l'avancement de chaque pipeline. Il lit le plan d'avancement et se met à jour à chaque changement. `/hosa-panneau` l'ouvre. Dans l'application de bureau et dans VS Code, il s'ouvre seul dans un projet Hosa ; pour l'empêcher : `HOSA_PANNEAU=0`.

Les barrières de budget (hook `budget.js`) :
- Les seuils de la session principale se comptent au-dessus de son contexte de départ, mesuré au 1ᵉʳ appel : un `/clear` n'économise que ce qui a grandi depuis. Ce départ est passé de 29 000 à 54 000 tokens le 8 novembre 2026, par le prompt système et les outils de Claude Code.
- Quand une étape s'est terminée dans une session qui a grandi de plus de 20 000 tokens depuis son départ, le skill de l'étape suivante est refusé une fois. Claude s'arrête et te propose `/clear`, puis « reprends ». Si tu préfères rester, il relance le skill, qui passe cette fois. Cette marge se règle avec `HOSA_CONTEXTE_MARGE` (en tokens).
- Au-delà de 70 000 tokens au-dessus du départ, tout skill Hosa et tout lancement d'agent sont refusés une fois, étape terminée ou non, puis de nouveau tous les 50 000 tokens de plus. Sur rieki et pilote 2, 45 % du contexte de la session principale était consommé au-delà de 120 000 tokens. Même proposition : `/clear`, puis « reprends ».
- Un agent Hosa est arrêté au-delà de 50 appels d'outils pour `hosa-ux-designer`, et de 150 pour les autres, ou quand son contexte atteint 120 000 tokens (`HOSA_AGENT_CONTEXTE_MAX`). À 80 % de ce plafond, il est prévenu une fois : il finit l'étape en cours et n'en commence pas d'autre. Il rend son rapport avec `## Reprise`, et un nouvel agent reprend à partir de là.
- Un agent inactif depuis plus de 5 minutes, avec plus de 50 000 tokens de contexte, n'est pas relancé par un message : son cache a expiré, et le message réécrirait tout son contexte. Claude lance un nouvel agent avec sa `## Reprise`. Si tu veux quand même relancer l'ancien, il renvoie le message, qui passe cette fois.
- Pendant une étape que `pipeline.json` (`dispatch`) déclare, le nombre d'agents Hosa en même temps et le modèle de certains agents sont imposés. Pendant `backlog` : 2 agents au plus, et `hosa-security` et `hosa-legal` sur Sonnet.

Pour les couper : `HOSA_BUDGET=0`.

Un tour peut finir sur une simple note d'avancement. Le hook `stop.js` le signale : si une étape du plan reste « en cours » à la fin d'un tour, sans `block` ni `done`, une ligne te prévient. Il ne bloque jamais, et ne prévient qu'une fois par étape et par session. Dis « continue » pour reprendre le travail. Pour le couper : `HOSA_STOP=0`.

**À l'essai.** Après chaque lancement d'agent, la session principale relit tout son contexte pour dire que l'agent tourne (sur rieki : 54 lancements sur 55, environ 4 M de tokens relus). Le hook `launch.js` finit le tour au lancement ; le rapport de l'agent réveille la session comme avant. Il est coupé par défaut tant qu'un sprint ne l'a pas mesuré. Pour l'essayer : `HOSA_ARRET_LANCEMENT=1`.

Une tâche d'agent se ferme seulement si sa sortie passe ses contrôles : fichiers présents et non vides, format OKF, puis les contrôles de la tâche déclarés dans `pipeline.json` (verdict de revue écrit…). Un refus donne les manques exacts, et l'agent est relancé avec eux. Après 2 refus pour la même cause, la tâche est bloquée et c'est toi qui décides. Pour chaque lot du backlog, `hosa-juge` (Haiku) passe en dernier, après la story, la note sécurité et la note juridique. Il répond Oui ou Non à des questions fermées sur chaque ticket, avec la ligne qui le prouve. Chaque Non retourne à l'agent responsable de sa question (PO, sécurité ou juridique), avec les manques exacts. Chaque décision du juge va dans `kb/jugements/log.md`. Demande « est-ce que le juge tient ? » : tu vois les refus par question et les fois où tu as passé outre. Pour couper ce juge : `HOSA_JUGE=0`.

À chaque bilan de sprint, `bilan-sprint` écrit `## Mesures` dans le fichier du sprint : coût par ticket, revues, passages du débogueur, contexte maximal, passages d'agent les plus longs, comparaison avec les sprints précédents. Il ajoute des propositions quand un seuil est dépassé, et c'est toi qui décides de les appliquer. Elles sont visibles aussi dans le tableau de bord, sur la page du sprint.

Les agents d'exécution (`hosa-developer`, `hosa-implementer`, `hosa-tester`, `hosa-qa-lead`, `hosa-key-user`, `hosa-git`, `hosa-documentation`, `hosa-infra`, `hosa-dba`) tournent sur Haiku depuis le 17/10/2026, environ 20 fois moins cher que Sonnet. Pour mesurer si la qualité tient : demande « consommation par agent » avant et après cette date (coût par ticket livré, verdicts de `hosa-reviewer`). Pour revenir sur Sonnet sans attendre une version : `HOSA_HAIKU=0`.

### La base de connaissances (KB)

- Elle vit dans le projet, dans `.hosa/kb/`, sur sa **propre branche git `hosa-kb`** : elle ne se mélange jamais au code ni aux sprints.
- Chaque commit de la KB note le commit du code correspondant.
- `/kb-commit` la committe ; sur un projet existant, `/kb-commit migrer` la déplace sur sa branche (le plan est montré avant toute action).
- Sur un nouveau poste, Hosa extrait la branche `hosa-kb` tout seul.

### Reprendre où on s'est arrêté

Hosa tient un **plan d'avancement** (`.hosa/kb/project/avancement.md`). Si une session s'arrête (limite atteinte, coupure), la suivante reprend à l'étape, au ticket et à la tâche exacts. Il refuse aussi de sauter une étape sans ton accord.

Une étape n'est marquée faite qu'avec sa preuve dans la KB. Par exemple : pas de relecture faite avec une anomalie bloquante encore ouverte, pas de contestation faite sans exigences signées, pas de backlog fait sans tickets complets. Quand une étape renvoie du travail en arrière (la relecture vers la rédaction, la QA vers le développement…), le plan note la boucle et compte ses tours. Seule une anomalie bloquante fait une boucle : une anomalie mineure (un mot, une description en retard) se corrige en une fois. Chaque anomalie note aussi sa passe et son origine, et `cdc mesure` les compte : on voit si les corrections créent de nouveaux défauts. Après deux tours sans sortie propre, c'est toi qui décides de la suite. Les étapes et leurs boucles sont décrites dans un seul fichier, `skills/status/scripts/pipeline.json`.

Dans une étape, chaque travail confié à un agent est une tâche du plan : la QA d'un lot de tickets, la recette d'un persona, une manche de l'interface, un lot de développement. Une tâche n'est faite qu'avec les chemins des fichiers que l'agent a écrits, et ces fichiers doivent exister. L'étape n'est faite que quand toutes ses tâches sont faites ou écartées. Après un `/clear`, la session reprend à la première tâche ouverte, sans refaire une tâche déjà faite. `status` et le tableau de bord montrent les tâches de chaque étape en cours, avec les tâches bloquées et leur question.

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

Les scripts de Hosa passent tous par une seule commande, `<hosa> <script>` (la session et les agents la reçoivent au démarrage ; `<hosa> --list` donne les noms). Elle reste valable d'une version à l'autre et utilise toujours le Python de Hosa. Un script appelé par son chemin dans le cache du plugin est refusé, avec la bonne commande dans le message.

## Le tableau de bord

Une interface locale montre l'avancement du projet dans la méthode Hosa : le plan d'avancement (étape en cours, preuves manquantes, prochain skill à lancer), le tableau des tickets, les sprints, la KB, le graphe et le journal. Elle lit et modifie les fichiers de la KB, elle n'appelle jamais Claude.

Dans Claude Code, demande « ouvre le tableau de bord » ou tape `/pilotage`. Elle s'ouvre sur http://127.0.0.1:3000.

Ses dépendances Python s'installent toutes seules, en arrière-plan, à la première session après l'installation du plugin, dans son dossier de données (`~/.claude/plugins/data/hosa-hosa/venv`) : elles survivent aux mises à jour, et ne sont réinstallées que si leurs versions changent. Rien n'est installé dans le Python du système. Variables optionnelles :
- `PORT` : port d'écoute (défaut `3000`) ;
- `HOSA_KB_ROOT` : chemin vers la KB à afficher (par défaut, celle du dossier courant ou d'un parent).

## Développer Hosa

- Les tests : `node --test hooks/*.test.js` et, dans `hosa/app`, `python -m unittest`. Ils tournent aussi sur GitHub à chaque push.
- Les règles communes à tous les skills et agents sont dans `skills/using-hosa/SKILL.md` ; le standard des retours dans `skills/retours/SKILL.md`.
- Les règles de conception de Hosa (graphe des étapes, boucles bornées et vérifiables) sont dans `CLAUDE.md`.
