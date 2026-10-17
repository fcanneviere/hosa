# Interface du tableau de bord Hosa

## Vue d'ensemble
Page unique en HTML, CSS et JavaScript natifs. Pas de build, polices système, aucune ressource réseau.
Fichiers : `hosa/app/public/index.html` (coquille), `style.css`, `app.js` (vues, état, appels API).
Routage par le hash de l'URL.

Lancement : `python hosa/app/server.py` (port 3000). `HOSA_KB_ROOT=.hosa/kb` désigne la KB à lire.
`server.py` et `kb.py` ne changent pas : voir `docs/architecture.md`.

## Écrans
Un seul utilisateur, un seul menu, aucun rôle ni droit distinct. Tous les écrans sont accessibles.
Le menu est une barre haute qui défile horizontalement : Accueil, Plan d'avancement, Exigences, Tickets, Sprints, Recettes, Consommation, Traçabilité, Journal, Personas, puis Gestion ▾ (À valider, Concepts, Tickets).

| Route | Écran |
|---|---|
| `/` | Accueil |
| `/avancement` | Plan d'avancement |
| `/exigences`, `/exigences/<slug>` | Exigences |
| `/tickets`, `/tickets/<chemin>` | Tickets |
| `/sprints`, `/sprints/<sprint>` | Sprints |
| `/recettes` | Recettes |
| `/consommation` | Consommation |
| `/tracabilite` | Traçabilité (graphe construit automatiquement ; « Graphe absent » seulement hors d'un dépôt git) |
| `/journal` | Journal |
| `/personas` | Personas |
| `/gestion/validation` | À valider |
| `/gestion/concepts`, `/gestion/concepts/<chemin>` | Liste et éditeur de concepts |
| `/gestion/tickets` | Liste de gestion des tickets |

Page 404 « Écran introuvable ». Il n'y a pas de page 403.

## Accueil
Dans l'ordre :
1. bandeau d'état de la KB (sauvegarde) ;
2. prochaine étape, avec le skill à copier (Copier) et le point de reprise ;
3. « Peut-on livrer ? » et les points bloquants ;
4. plan d'avancement et preuves manquantes ;
5. « À valider », avec le bouton Valider ;
6. tickets du sprint actif ;
7. dernières recettes et les 2 premières lignes de consommation.

## Consommation
Tableau Agent · Appels · Part (en %), pour la période choisie. Sans donnée : « Aucune donnée de consommation trouvée pour ce projet. »

## Comportements
- Nom : demandé une seule fois, à la première validation, puis retenu. Le bouton « Mon nom » (en haut à droite) le modifie. Il sert à la traçabilité, pas à l'authentification.
- Filtres : pastilles que l'on retire d'un clic. Ils restent d'un écran à l'autre.
- La touche `/` place le curseur dans la recherche.
- Relire garde la position et les filtres.
- Valider : écrit `status: stable` et `verified: human:<nom>`. Annuler la validation : demande confirmation et efface `verified`.
- Éditeur de concept : onglet Aperçu, état de sauvegarde, confirmation avant de quitter avec des changements non enregistrés.
- Erreurs : un assainisseur retire chemins, noms de fichiers, routes et codes. Un « Réessayer » est proposé.
- Mobile : une seule colonne sous 700 px. Les entrées de Gestion rejoignent la barre de menu.
- Couverture des critères (« 2/3 ») : calculée par le serveur (`GET /api/couverture`, `avancement.py coverage`). Un critère CAn compte s'il est cité `[CAn]` dans le plan technique, ou « CAn — Oui » dans une recette. Si la route échoue, l'écran affiche « Couverture indisponible ».

## Identité visuelle
« Papier calme » : papier `#F5F2EC`, bleu nuit `#23407A`, brique `#9A3B12`, vert `#1F6B3A`.
Une seule densité, environ 15 px.
Un statut s'affiche par un mot, un symbole et une couleur. Pas de mode sombre, pas d'animation.
Les variables CSS sont dans `style.css`. Détail : `kb/project/identity.md`, section « Identité visuelle ».

## Vocabulaire
Un seul vocabulaire, pensé pour un vibecoder. Résultat d'une recette : « réussi », « réussi avec remarques », « échoué ». Validation : « validé par vous », « contrôlé automatiquement », « à valider ».
Lexique : `kb/interface/lexique.md`. Plan de navigation : `kb/interface/navigation.md`. Règles de conception : `kb/rules/design/*.md` (brouillon).

## Limites connues
Ces données serveur manquent. Les écrans affichent un état lisible à la place.
- `GET /api/kb-status` (`{git, changed}`) : alimente le bandeau de sauvegarde.
- `GET /api/usage?days=N` (agents, skills, modèles, via `usage_report.py`) : alimente Consommation.
- Recettes : lues dans `recettes` de `GET /api/overview` ; une recette est un concept de `kb/test/` dont le nom ne finit pas par `-technique.md`. Les tickets sont lus dans `kb/tickets/`.
