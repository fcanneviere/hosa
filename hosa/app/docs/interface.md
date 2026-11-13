# Interface du tableau de bord Hosa

## Vue d'ensemble
Page unique en HTML, CSS et JavaScript natifs. Pas de build, polices du système, aucune ressource réseau.
Fichiers : `hosa/app/public/index.html` (coquille), `style.css`, `app.js` (vues, état, appels API).
Routage par le hash de l'URL.

Lancement : `python hosa/app/server.py` (port 3000). `HOSA_KB_ROOT=.hosa/kb` désigne la KB à lire.
Recette locale : `python fixtures/jeu.py`, puis `HOSA_KB_ROOT="$TMP/hosa-ui-recette/.hosa/kb" python server.py`.

## Ce que l'interface permet
- **Suivre** : prochaine étape et commande à copier, plan d'avancement, sprints, tickets, recettes et audits, consommation.
- **Lire** : cahier des charges, personas, toute la KB, traçabilité exigence → ticket → code, journal.
- **Agir** : valider ce que Claude a écrit, modifier un document, déplacer un ticket, écrire une remarque pour Claude.

## Écrans
Un seul utilisateur, aucun rôle. Menu latéral en trois groupes (un tiroir sous 900 px).

| Groupe | Route | Écran |
|---|---|---|
| Pilotage | `/` | Vue d'ensemble |
| Pilotage | `/avancement` | Plan d'avancement |
| Pilotage | `/sprints`, `/sprints/<sprint>` | Sprints |
| Pilotage | `/tickets`, `/tickets/<chemin>` | Tickets (tableau à 4 colonnes) ; `/gestion/tickets` y mène aussi |
| Pilotage | `/recettes` | Recettes et qualité |
| Pilotage | `/consommation` | Consommation |
| Produit | `/exigences`, `/exigences/<slug>` | Cahier des charges |
| Produit | `/personas`, `/personas/<slug>` | Personas |
| Produit | `/kb`, `/kb/<chemin>` | Base de connaissance (lecteur) |
| Produit | `/tracabilite` | Traçabilité |
| Vos actions | `/gestion/validation` | À valider (compteur dans le menu) |
| Vos actions | `/remarques` | Remarques pour Claude (compteur des remarques en attente) |
| Vos actions | `/journal` | Journal |
| Vos actions | `/gestion/concepts`, `/gestion/concepts/<chemin>` | Concepts, éditeur |

Page 404 « Écran introuvable ».

## Vue d'ensemble
Dans l'ordre : la question « Où en est <projet> ? » ; le bandeau de la prochaine étape (commande à copier, preuves manquantes) ;
4 indicateurs (exigences validées, tickets faits, sprint actif, consommation de la période comparée à la période d'avant), chacun mène à son écran ;
le plan d'avancement en frise ; « À vous » (documents à valider, remarques en attente, dernières réponses de Claude) ; « Peut-on livrer ? » ;
le sprint en cours ; l'activité récente ; vos remarques.

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
- Tickets : glisser une carte vers une colonne, ou « Déplacer… » au clavier. Écrit `state` et une ligne de log.
- Valider : écrit `verified: human:<nom>` (et `status: stable` pour une exigence). Annuler la validation demande confirmation.
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
Recette : « réussi », « réussi avec remarques », « échoué ». Validation : « validé par vous », « contrôlé automatiquement », « à valider ».
Remarque : « en attente de Claude », « traitée par Claude ».

## Limites connues
- La consommation compare à la période d'avant de même durée ; elle n'a pas de courbe par jour (`usage_report.scan` ne la donne pas).
- Une remarque n'est lue par Claude qu'à la prochaine « reprends » (ou « traite mes remarques ») : l'app ne le réveille pas.
