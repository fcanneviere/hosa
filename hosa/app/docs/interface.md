# Interface du tableau de bord Hosa

## Vue d'ensemble
Page unique en HTML, CSS et JavaScript natifs. Pas de build, polices du système, aucune ressource réseau.
Fichiers : `hosa/app/public/index.html` (coquille), `style.css`, `app.js` (vues, état, appels API).
Routage par le hash de l'URL.

Lancement : `python hosa/app/server.py` (port 3000). `HOSA_KB_ROOT=.hosa/kb` désigne la KB à lire.
Recette locale : `python fixtures/jeu.py`, puis `HOSA_KB_ROOT="$TMP/hosa-ui-recette/.hosa/kb" python server.py`.

## Ce que l'interface permet
- **Savoir ce que Claude attend de vous** : « À vous », lu dans le plan et la KB, jamais deviné.
- **Suivre** : la prochaine étape (on la reprend toujours par « reprends »), le plan d'avancement, les sprints, les tickets, les recettes, les audits, la consommation.
- **Lire** : le cahier des charges, les personas, toute la KB, la traçabilité exigence → ticket → code, le journal.
- **Agir** : écrire une remarque pour Claude. Modifier un document que Hosa ne tient pas lui-même. Valider un document que l'app peut signer.

## Ce que l'interface n'écrit jamais
Une preuve d'étape ne s'écrit pas à la main. Le serveur refuse (`kb.protection`, `kb.PROOF_FIELDS`), l'app cache le bouton et dit pourquoi :
- l'état et l'acceptation d'un ticket (`accepte`, le PO) ;
- le statut et la signature d'une exigence (la signature porte sur le cahier des charges entier, à `contestation`) ; une exigence stable change par `changement` ;
- les fichiers que Hosa tient : `project/avancement.md`, `project/cahier-des-charges.md`, `sommaire.md`, `code/` ;
- les preuves : `test/`, `jugements/`, `sprints/` ; les remarques, fermées par la réponse de Claude.

L'app ne crée aucun document : un ticket naît complet dans `backlog`. Une idée devient une remarque.

## Écrans
Un seul utilisateur, aucun rôle. Le menu suit le parcours de Hosa (un tiroir sous 900 px). Sa seule définition est `NAV` dans `app.js` ; un test vérifie que ce tableau la suit.

| Groupe | Route | Écran |
|---|---|---|
| Aujourd’hui | `/` | Vue d’ensemble |
| Aujourd’hui | `/a-vous` | À vous |
| Aujourd’hui | `/remarques` | Remarques pour Claude |
| Cahier des charges | `/exigences`, `/exigences/<slug>` | Exigences |
| Cahier des charges | `/personas`, `/personas/<slug>` | Personas |
| Structuration | `/structuration` | Stack et conception |
| Sprints | `/sprints`, `/sprints/<sprint>` | Sprints |
| Sprints | `/planification`, `/planification/graphe/<ticket>` | Planification |
| Sprints | `/tickets`, `/tickets/<chemin>` | Tickets |
| Sprints | `/recettes` | Recettes et qualité |
| Suivi | `/avancement` | Plan d’avancement |
| Suivi | `/journal` | Journal |
| Suivi | `/consommation` | Consommation |
| Suivi | `/tracabilite` | Traçabilité |
| Base de connaissance | `/kb`, `/kb/<chemin>`, `/modifier/<chemin>` | Documents |
| Base de connaissance | `/aide` | Documentation de Hosa |

Les anciennes adresses `/gestion/validation`, `/gestion/tickets` et `/gestion/concepts…` redirigent vers leur écran. Page 404 « Écran introuvable ».

## Vue d'ensemble
Dans l'ordre : la question « Où en est <projet> ? » ; le bandeau de la prochaine étape, avec « reprends » à copier.
Une étape bloquée change le bandeau : « Claude attend votre réponse », couleur de l'action.
Puis « À vous » (les trois premiers points, les remarques en attente, les dernières réponses de Claude) et le plan d'avancement en frise ;
« Peut-on livrer ? », le sprint en cours et l'activité récente ; enfin 4 indicateurs, chacun mène à son écran.

## À vous
Ce que Claude attend de vous, dans l'ordre où cela bloque le travail :
1. l'étape ou la tâche bloquée et ses questions (le point de reprise du plan) ;
2. les anomalies de la relecture routées vers vous (`→ utilisateur — ouverte`) ;
3. les questions ouvertes de `cdc/decisions.md` ;
4. les schémas de processus pas encore validés (`cdc.py`).

Les points 2 à 4 disparaissent une fois le cahier des charges signé. Le compteur du menu les additionne.
Sous la liste : ce que l'étape suivante vous demandera (`decisions` de `pipeline.json`), et vos validations passées.
Vous répondez dans Claude Code, en disant « reprends » : l'app ne réveille pas Claude.

## Peut-on livrer ?
« Rien à livrer » tant qu'aucun ticket n'est fait. Ensuite, « Pas encore » avec ce qui bloque :
une recette échouée, un ticket bloqué, le dernier audit qualité ou sécurité en échec, un sprint pas fusionné. Sinon « Oui ».

## Remarques pour Claude
- Le bouton « Remarque pour Claude » est sur chaque écran. Sur un document (ticket, exigence, persona, page de la KB, éditeur), la remarque le vise ; sinon elle est générale.
- Le tiroir : document visé, nature (À corriger, Question, Idée), texte (4 000 caractères), `Ctrl Entrée` envoie.
- `POST /api/remarques` écrit `kb/remarques/<horodatage>-<document>.md`, type `Remarque`, signé `human:<nom>`, `etat: ouverte`.
- L'app n'appelle jamais Claude. La fiche de reprise (`avancement.py reprendre`) liste les remarques ouvertes avant son `Action`.
  Claude traite chacune par la méthode, puis la ferme : `avancement.py <kb> remarque <chemin> --detail "<réponse>"` (`etat: traitee`, section `## Réponse de Claude`).
- L'écran montre l'état de chaque remarque (« en attente de Claude », « traitée par Claude ») et la réponse.

## Comportements
- Nom : demandé une seule fois, à la première validation ou remarque, puis retenu (bas du menu, « Mon nom »). Il signe, il n'authentifie pas.
- Recherche globale : `Ctrl K` ouvre la palette (écrans et documents) ; `/` place le curseur dans la recherche de l'écran, sinon ouvre la palette.
- Filtres : pastilles que l'on retire d'un clic ; ils restent d'un écran à l'autre (stockage de session).
- Tickets : tableau à 4 colonnes en lecture seule, filtré d'abord sur le sprint en cours (ou le prochain prévu). Le filtre se retire d'un clic.
- Valider : écrit `verified: human:<nom>` sur un document `validable` (ni exigence, ni ticket, ni fichier protégé). Annuler la validation demande confirmation.
- Lecture seule : un document protégé montre sa raison et le bouton « Remarque » à la place de « Modifier ».
- Éditeur : en-tête YAML repliable, Markdown et aperçu côte à côte, barre d'enregistrement collante, confirmation avant de quitter avec des changements. Un fichier modifié par Claude entre-temps est refusé (409).
- Erreurs : un assainisseur retire chemins, routes et codes. Un « Réessayer » est proposé.
- Thème : système, clair ou sombre (bas du menu), retenu sur ce poste.

## Identité visuelle « Atelier »
Papier chaud et encre ; pétrole `#1D5566` pour la navigation et les liens ; terre cuite `#A2481A` pour l'action (prochaine étape, remarques, compteurs).
Titres en serif de labeur (Iowan Old Style, Palatino), texte en sans humaniste (Segoe UI Variable, Avenir), chiffres tabulaires.
Mode sombre : ses propres teintes, pas une inversion. Un statut s'affiche toujours par un mot, un symbole et une couleur.
Graphique : barres horizontales d'une seule série (coût par agent), valeurs écrites à côté et tableau exact dessous.
Variables CSS dans `style.css`, sur `:root`, redéfinies pour le mode sombre.

## Vocabulaire
Recette : « réussi », « réussi avec remarques », « échoué ». Validation : « validé par vous », « contrôlé automatiquement », « non relu » (neutre : Hosa ne demande pas de relire chaque fichier).
Exigence : « stable », « brouillon ».
Remarque : « en attente de Claude », « traitée par Claude ».

## Limites connues
- La consommation compare à la période d'avant de même durée ; elle n'a pas de courbe par jour (`usage_report.scan` ne la donne pas).
- Une remarque n'est lue par Claude qu'à la prochaine « reprends » (ou « traite mes remarques ») : l'app ne le réveille pas.
