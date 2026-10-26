# Socle comptes 1.0

Account management is the same from one application to the next: signup or invitation, login, session, password, recovery, roles, deactivation, deletion, security log. Rewriting it for every project gave 9 relecture anomalies and a login shipped without rate limiting (pilot2, sprint 1: a third of the sprint). This file is the standard: exigences already written, reviewed once, with their security controls built in and their ticket split.

**Who reads it.** `fondamentaux` (variants and parameters, then `hosa-product-owner` copies the exigences), `securite` (`hosa-security` Mode 1: the controls are already there), `relecture` (only what the project filled in is checked), `backlog` (the split below), `stack` (`hosa-senior-dev`: the authentication library).

**Rules of use.**
- Copy each kept exigence **as written**: same sections, same rules, same error cases. Replace each `{paramètre}` with its value and each generic role with the project's role (`Utilisateur` → the front-office persona's role, `Administrateur` → the back-office one). Add a project rule if the project needs one; never remove or weaken a socle rule — a rule the project really doesn't want is a parameter or a variant here, or an accepted risk in `securite`.
- Frontmatter: `tags: [socle-comptes]` (plus the exigence's own tags), `status: draft`, `generated: { by: hosa-product-owner/1.0, at: <ISO8601> }`. Slug = the heading's slug (`compte-connexion`…).
- An exigence the project already has on the same process (a project `connexion` exigence, say) → merge: the socle's rules and error cases are added to it, its own are kept, `socle-comptes` goes into its tags. Never two exigences for one process.
- The only part the socle can't write is the project's **matrice des rôles** (`compte-roles-droits`): which role sees and does what. The PO writes it with the user.

---

## Variantes

Three questions, asked once by `fondamentaux` Step 3. The default is the first option.

| Question | Options | Effet |
|---|---|---|
| **V1. Mode d'authentification du front office** | `mot-de-passe` · `sso` (OpenID Connect : Google, Microsoft Entra, Keycloak…) · `lien-magique` (lien de connexion par email, sans mot de passe) | `sso` : retire `compte-mot-de-passe`, `compte-mot-de-passe-oublie` et la partie mot de passe de `compte-connexion` (le fournisseur d'identité les porte) ; ajoute la règle « compte rattaché par email vérifié chez le fournisseur » ; l'invité active son compte à sa première connexion par le fournisseur ; la double authentification est celle du fournisseur. `lien-magique` : retire `compte-mot-de-passe` et `compte-mot-de-passe-oublie` ; la connexion envoie un lien de `{duree_lien_magique}`, usage unique. |
| **V2. Accès au front office** | `invitation` (un administrateur crée chaque compte) · `auto-inscription` (chacun crée son compte) | `invitation` : pas de `compte-inscription`. `auto-inscription` : `compte-inscription` gardé. Le back office est **toujours** sur invitation, quelle que soit la réponse. |
| **V3. Organisations** | `mono` (une seule organisation) · `multi-organisation` (chaque compte appartient à une organisation cliente) | `multi-organisation` : ajoute `compte-organisation`. |

The back office follows the V1 answer too, unless the user says otherwise. No front office at all (back-office-only application) → V2 is not asked.

## Paramètres

One block, shown with the defaults already filled in; the user changes only what they want. Each value goes into `kb/cdc/fondamentaux.md` under `## Socle comptes`.

| Paramètre | Défaut | Pourquoi ce défaut |
|---|---|---|
| `{inactivite_bo}` — déconnexion après inactivité, back office | 30 min | OWASP : 15-30 min pour un accès à privilèges |
| `{duree_max_bo}` — durée maximale d'une session back office | 8 h | une journée de travail, puis reconnexion |
| `{inactivite_fo}` — déconnexion après inactivité, front office | 7 jours | confort de l'utilisateur final, risque plus faible |
| `{duree_max_fo}` — durée maximale d'une session front office | 30 jours | |
| `{mdp_longueur_min}` — longueur minimale du mot de passe | 12 caractères | ANSSI ; NIST 800-63B (pas de règle de composition, pas d'expiration périodique) |
| `{echecs_identifiant}` — échecs consécutifs sur un identifiant avant délai | 5 | |
| `{delai_initial}` / `{delai_max}` — délai imposé après ces échecs, doublé à chaque nouvel échec | 1 min / 15 min | ralentit l'attaque sans permettre de bloquer un compte exprès |
| `{tentatives_ip}` — tentatives par adresse IP sur chaque route d'authentification | 10 par 15 min | règle « Limitation de débit » du catalogue |
| `{duree_jeton_reinit}` — validité du lien de réinitialisation | 1 h | |
| `{duree_invitation}` — validité du lien d'invitation | 7 jours | |
| `{duree_verif_email}` — validité du lien de vérification d'email | 24 h | |
| `{duree_lien_magique}` — validité du lien de connexion (V1 `lien-magique`) | 15 min | |
| `{mfa_bo}` — double authentification, back office | obligatoire (application TOTP) | un compte back office volé expose toutes les données |
| `{mfa_fo}` — double authentification, front office | proposée, facultative | |
| `{codes_secours}` — codes de secours MFA, usage unique | 10 | |
| `{conservation_journal}` — conservation du journal de sécurité | 1 an | CNIL : 6 mois à 1 an pour les journaux de connexion |
| `{mdp_compromis}` — contrôle des mots de passe compromis | liste locale (100 000 mots de passe les plus fréquents) | aucune donnée envoyée à un tiers ; un service externe (Have I Been Pwned) est un choix de l'utilisateur |

---

## Exigences

### compte-premier-administrateur

```markdown
---
type: Exigence
title: Création du premier administrateur
description: "Créer le premier compte administrateur sans compte ni mot de passe par défaut"
tags: [socle-comptes]
espace: [back-office]
---
## Objectif du processus
Donner un premier accès au back office à l'installation, sans aucun compte ni mot de passe écrit dans le code, la configuration ou les données de départ.

## Données en entrée
- Email du premier administrateur, passé à une commande d'exploitation

## Données en sortie
- Un compte Administrateur à l'état « invité »
- Un email d'invitation contenant un lien à usage unique

## Qui fait quoi
- Exploitant : lance la commande d'exploitation avec l'email
- Système : crée le compte invité et envoie l'invitation (`compte-invitation`)
- Administrateur : suit le lien et définit son mot de passe et sa double authentification

## Règles de gestion
- Aucun compte par défaut : le code, la configuration et les migrations ne créent aucun compte ; seul le jeu de données de test en crée, dans l'environnement de test.
- La commande refuse de créer un administrateur s'il existe déjà un administrateur actif (exemple : relancée une seconde fois → refus, aucun compte créé), sauf avec une option explicite de secours, journalisée.
- Le compte suit ensuite `compte-invitation` : lien valable `{duree_invitation}`, usage unique.

## Cas d'erreur
- Email invalide → la commande s'arrête avec un message clair, aucun compte créé
- Un administrateur actif existe déjà → refus, message « un administrateur existe déjà », aucun compte créé
- Envoi de l'email impossible → la commande affiche le lien une fois, dans la console de l'exploitant, et journalise l'échec d'envoi

## Responsable
Exploitant

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-invitation

```markdown
---
type: Exigence
title: Invitation d'un utilisateur
description: "Un administrateur crée un compte ; l'invité l'active par un lien à usage unique"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Créer un compte pour une personne précise, avec son rôle, sans que l'administrateur connaisse ni choisisse son mot de passe.

## Données en entrée
- Email, nom, rôle (saisis par l'Administrateur)
- Mot de passe choisi par l'invité

## Données en sortie
- Compte à l'état « invité », puis « actif » après activation
- Email d'invitation avec un lien à usage unique
- Événements du journal de sécurité : invitation envoyée, compte activé

## Qui fait quoi
- Administrateur : saisit email, nom et rôle ; peut renvoyer ou annuler une invitation en attente
- Invité : suit le lien, choisit son mot de passe (`compte-mot-de-passe`) et, en back office, active sa double authentification
- Système : envoie l'invitation, active le compte, journalise

## Règles de gestion
- Le lien d'invitation est valable `{duree_invitation}` et ne sert qu'une fois ; renvoyer une invitation invalide le lien précédent.
- Le lien contient un jeton aléatoire d'au moins 128 bits ; seule son empreinte est stockée.
- L'email est unique parmi les comptes, sans distinction de casse (exemple : `Anne@x.fr` et `anne@x.fr` sont le même compte).
- Un compte back office n'est actif qu'une fois la double authentification activée si `{mfa_bo}` est obligatoire.
- Un administrateur ne peut attribuer qu'un rôle de niveau inférieur ou égal au sien.

## Cas d'erreur
- Email déjà utilisé par un compte → refus, message « un compte existe déjà avec cet email », aucun email envoyé
- Lien expiré ou déjà utilisé → page « ce lien n'est plus valable, demandez une nouvelle invitation », aucun détail sur le compte
- Mot de passe refusé (`compte-mot-de-passe`) → message précis, l'invité corrige sans perdre le lien
- Envoi de l'email impossible → l'administrateur voit « invitation non envoyée » et peut la renvoyer ; l'échec est journalisé

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-inscription

Variante V2 `auto-inscription` uniquement.

```markdown
---
type: Exigence
title: Inscription
description: "Une personne crée elle-même son compte front office et vérifie son email"
tags: [socle-comptes]
espace: [front-office]
---
## Objectif du processus
Permettre à une personne de créer son compte front office seule, avec une adresse email qu'elle prouve détenir.

## Données en entrée
- Email, mot de passe (et les champs de profil propres au projet)
- Acceptation des conditions d'utilisation (`juridique`)

## Données en sortie
- Compte à l'état « non vérifié », puis « actif » après vérification de l'email
- Email de vérification avec un lien à usage unique
- Événement du journal de sécurité : compte créé

## Qui fait quoi
- Visiteur : saisit ses informations et suit le lien de vérification
- Système : crée le compte, envoie le lien, active le compte

## Règles de gestion
- Le lien de vérification est valable `{duree_verif_email}` et ne sert qu'une fois ; un nouveau lien peut être demandé, avec la limitation `{tentatives_ip}`.
- Un compte « non vérifié » ne peut pas se connecter ; il est supprimé s'il n'est pas vérifié sous 7 jours.
- La réponse est identique que l'email soit déjà utilisé ou non : « un email de confirmation a été envoyé » ; si l'email est déjà utilisé, le titulaire reçoit un email « quelqu'un a tenté de créer un compte avec votre adresse » au lieu du lien.
- La route d'inscription applique `{tentatives_ip}`.
- Le rôle attribué est toujours le rôle front office de base ; aucun champ du formulaire ne peut le changer.

## Cas d'erreur
- Mot de passe refusé (`compte-mot-de-passe`) → message précis à côté du champ
- Email invalide → message à côté du champ
- Lien expiré ou déjà utilisé → page « ce lien n'est plus valable » avec le bouton « renvoyer un lien »
- Limite de tentatives atteinte → « trop de tentatives, réessayez dans N minutes »

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-connexion

```markdown
---
type: Exigence
title: Connexion
description: "Connexion par identifiant et mot de passe, limitée en tentatives, avec double authentification"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Ouvrir une session pour un compte actif qui prouve son identité, en rendant les essais en masse inutiles.

## Données en entrée
- Email et mot de passe
- Code de double authentification ou code de secours, quand elle est active

## Données en sortie
- Une session (`compte-session`)
- Événements du journal de sécurité : connexion réussie, connexion échouée, délai imposé, code de double authentification refusé

## Qui fait quoi
- Utilisateur ou Administrateur : saisit ses identifiants, puis son code si demandé
- Système : vérifie, applique les limites, ouvre la session, journalise

## Règles de gestion
- Message d'échec unique : « identifiant ou mot de passe incorrect », que l'email existe ou non, que le compte soit désactivé ou non ; le temps de réponse est le même dans tous les cas.
- Limitation par identifiant : après `{echecs_identifiant}` échecs consécutifs sur un même email, chaque nouvelle tentative attend `{delai_initial}`, doublé à chaque échec, plafonné à `{delai_max}` (exemple avec les défauts : 6e échec → 1 min, 7e → 2 min, 8e → 4 min… jusqu'à 15 min). Une connexion réussie remet le compteur à zéro. Le compte n'est jamais bloqué définitivement.
- Limitation par adresse IP : `{tentatives_ip}` sur la route de connexion, réponse 429.
- Les compteurs sont dans un stockage partagé dès que plus d'une instance sert l'application.
- Les mêmes limites s'appliquent aux emails inexistants (sinon le délai révèle quels comptes existent).
- Double authentification : `{mfa_bo}` pour le back office, `{mfa_fo}` pour le front office ; le code (TOTP, 30 s, une période de tolérance) et les codes de secours suivent les mêmes limites ; un code de secours ne sert qu'une fois.
- Un compte invité, non vérifié ou désactivé ne peut pas se connecter.
- Le mot de passe est vérifié contre son empreinte (argon2id, scrypt ou bcrypt ≥ 12 tours) ; il n'apparaît jamais dans un journal, une erreur ou une réponse.

## Cas d'erreur
- Identifiants faux → « identifiant ou mot de passe incorrect »
- Délai en cours → « trop de tentatives, réessayez dans N minutes », sans dire si le compte existe
- Limite IP atteinte → 429, « trop de tentatives, réessayez plus tard »
- Code de double authentification faux → « code incorrect », le compteur avance
- Téléphone de double authentification perdu → connexion avec un code de secours ; sans code de secours, un autre administrateur réinitialise la double authentification (`compte-administration-utilisateurs`)

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-session

```markdown
---
type: Exigence
title: Session et déconnexion
description: "Durée de session, déconnexion et révocation des sessions"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Limiter dans le temps l'accès ouvert par une connexion, et le fermer dès que l'utilisateur ou la sécurité le demande.

## Données en entrée
- La session ouverte par `compte-connexion`
- Les événements qui la ferment : déconnexion, inactivité, durée maximale, changement de mot de passe, désactivation

## Données en sortie
- Session fermée côté serveur
- Événement du journal de sécurité : déconnexion

## Qui fait quoi
- Utilisateur ou Administrateur : se déconnecte ; voit ses sessions ouvertes et peut fermer les autres
- Système : expire les sessions, les révoque sur les événements ci-dessus

## Règles de gestion
- Back office : fermeture après `{inactivite_bo}` d'inactivité, et au plus tard `{duree_max_bo}` après la connexion. Front office : `{inactivite_fo}` et `{duree_max_fo}`.
- L'identifiant de session est renouvelé à la connexion et à chaque changement de privilège.
- Cookie de session `HttpOnly`, `Secure`, `SameSite=Lax` (ou `Strict`) ; aucun jeton d'authentification dans le `localStorage`.
- La déconnexion invalide la session côté serveur ; réutiliser l'ancien cookie ne donne plus accès.
- Changement de mot de passe → toutes les autres sessions du compte sont fermées. Réinitialisation du mot de passe, désactivation ou suppression du compte → toutes ses sessions sont fermées.
- Les actions sensibles (changer email, mot de passe, double authentification, supprimer le compte) redemandent le mot de passe, même dans une session ouverte.

## Cas d'erreur
- Session expirée pendant une saisie → retour à la connexion, puis à la page d'origine ; la saisie non envoyée est perdue et l'utilisateur en est prévenu
- Requête avec une session révoquée → 401 et retour à la connexion, aucune donnée renvoyée

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-mot-de-passe

Variante V1 `mot-de-passe` uniquement.

```markdown
---
type: Exigence
title: Mot de passe
description: "Politique de mot de passe et changement par l'utilisateur"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Fixer quels mots de passe sont acceptés, et permettre à chacun de changer le sien.

## Données en entrée
- Mot de passe actuel, nouveau mot de passe

## Données en sortie
- Nouvelle empreinte du mot de passe
- Email de notification « votre mot de passe a été changé »
- Événement du journal de sécurité : mot de passe changé

## Qui fait quoi
- Utilisateur ou Administrateur : change son propre mot de passe
- Système : vérifie la politique, enregistre l'empreinte, notifie, ferme les autres sessions

## Règles de gestion
- Au moins `{mdp_longueur_min}` caractères, au plus 128 ; tous les caractères acceptés, espaces et accents compris ; aucune règle de composition imposée (majuscule, chiffre…) ; aucune expiration périodique.
- Refusé s'il figure dans `{mdp_compromis}`, ou s'il contient l'email du compte.
- Stocké uniquement sous forme d'empreinte argon2id (ou scrypt, ou bcrypt ≥ 12 tours) ; jamais en clair, jamais réversible.
- Changer son mot de passe demande le mot de passe actuel, ferme les autres sessions (`compte-session`) et envoie la notification.
- Aucun administrateur ne voit ni ne choisit le mot de passe d'un autre compte : il ne peut que déclencher une réinitialisation.

## Cas d'erreur
- Trop court → « au moins N caractères »
- Mot de passe compromis → « ce mot de passe est trop courant, choisissez-en un autre »
- Mot de passe actuel faux → « mot de passe actuel incorrect », soumis aux limites de `compte-connexion`

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-mot-de-passe-oublie

Variante V1 `mot-de-passe` uniquement.

```markdown
---
type: Exigence
title: Mot de passe oublié
description: "Réinitialisation du mot de passe par un lien à usage unique"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Rendre l'accès à la personne qui détient l'adresse email du compte, sans révéler quels comptes existent.

## Données en entrée
- Email du compte
- Nouveau mot de passe

## Données en sortie
- Email avec un lien de réinitialisation à usage unique
- Nouvelle empreinte du mot de passe
- Événements du journal de sécurité : réinitialisation demandée, réinitialisation effectuée

## Qui fait quoi
- Utilisateur ou Administrateur : demande la réinitialisation, suit le lien, choisit un nouveau mot de passe
- Administrateur : peut déclencher l'envoi du lien pour un autre compte (`compte-administration-utilisateurs`)
- Système : envoie le lien, change le mot de passe, ferme les sessions

## Règles de gestion
- Réponse identique que l'email existe ou non : « si un compte existe pour cette adresse, un email a été envoyé ».
- Lien valable `{duree_jeton_reinit}`, usage unique, jeton aléatoire d'au moins 128 bits dont seule l'empreinte est stockée ; une nouvelle demande invalide le lien précédent.
- La route applique `{tentatives_ip}` et au plus 3 demandes par email et par heure.
- Le nouveau mot de passe suit `compte-mot-de-passe`.
- Après la réinitialisation : toutes les sessions du compte sont fermées, une notification est envoyée, le compteur d'échecs de connexion est remis à zéro ; la double authentification reste active.

## Cas d'erreur
- Lien expiré ou déjà utilisé → « ce lien n'est plus valable » avec le bouton « faire une nouvelle demande »
- Limite atteinte → « trop de demandes, réessayez plus tard », sans dire si le compte existe
- Compte désactivé → même réponse qu'un email inconnu, aucun email envoyé

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-email

```markdown
---
type: Exigence
title: Changement d'email
description: "L'utilisateur change l'email de son compte après vérification de la nouvelle adresse"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Permettre de changer l'adresse du compte sans qu'une session volée suffise à prendre le compte.

## Données en entrée
- Mot de passe actuel, nouvelle adresse email

## Données en sortie
- Lien de confirmation envoyé à la nouvelle adresse ; notification envoyée à l'ancienne
- Email du compte changé après confirmation
- Événement du journal de sécurité : email changé (ancienne et nouvelle adresse)

## Qui fait quoi
- Utilisateur ou Administrateur : demande le changement pour son propre compte et le confirme depuis la nouvelle adresse
- Système : vérifie, envoie, applique

## Règles de gestion
- La demande redemande le mot de passe actuel (en `sso`, l'email vient du fournisseur d'identité : ce processus n'existe pas).
- Le changement n'a lieu qu'après le clic sur le lien envoyé à la nouvelle adresse, valable `{duree_verif_email}`, usage unique.
- L'ancienne adresse reçoit « l'email de votre compte va être changé » au moment de la demande.
- La nouvelle adresse doit être libre (même règle d'unicité que `compte-invitation`).

## Cas d'erreur
- Mot de passe faux → refus, soumis aux limites de `compte-connexion`
- Adresse déjà utilisée → « cette adresse ne peut pas être utilisée », sans dire par qui
- Lien expiré → l'email reste inchangé, l'utilisateur peut refaire la demande

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-administration-utilisateurs

```markdown
---
type: Exigence
title: Administration des comptes
description: "Le back office liste, invite, désactive, réactive les comptes et change leur rôle"
tags: [socle-comptes]
espace: [back-office]
---
## Objectif du processus
Donner à l'administrateur la main sur tous les comptes, sans jamais lui donner accès à leurs secrets.

## Données en entrée
- Recherche (nom, email), filtres (rôle, état)
- Actions : inviter, renvoyer l'invitation, désactiver, réactiver, changer le rôle, envoyer un lien de réinitialisation, réinitialiser la double authentification

## Données en sortie
- Liste paginée des comptes : nom, email, rôle, état (invité, non vérifié, actif, désactivé), dernière connexion
- Événements du journal de sécurité pour chaque action, avec l'administrateur auteur

## Qui fait quoi
- Administrateur : consulte, recherche et agit sur les comptes
- Système : applique, ferme les sessions concernées, journalise

## Règles de gestion
- Désactiver est réversible : le compte ne peut plus se connecter, toutes ses sessions sont fermées, ses données restent.
- Il reste toujours au moins un administrateur actif : désactiver, rétrograder ou supprimer le dernier est refusé.
- Un administrateur ne peut pas agir sur un compte de rôle supérieur au sien.
- Réinitialiser la double authentification d'un compte oblige son titulaire à la réactiver à la prochaine connexion ; l'action est journalisée.
- L'administrateur ne voit jamais un mot de passe, un jeton, une empreinte ni un secret de double authentification.
- Chaque action est journalisée (`compte-journal-securite`).

## Cas d'erreur
- Dernier administrateur actif → refus, « il doit rester au moins un administrateur actif »
- Compte de rôle supérieur → l'action n'est pas proposée ; une requête directe reçoit 403
- Aucun résultat de recherche → « aucun compte ne correspond », filtres rappelés

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-roles-droits

```markdown
---
type: Exigence
title: Rôles et droits
description: "Chaque compte a un rôle ; chaque action et chaque donnée sont autorisées par rôle, côté serveur"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Que chacun ne voie et ne fasse que ce que son rôle permet, quelle que soit la façon dont la requête arrive.

## Données en entrée
- Le rôle du compte connecté
- La matrice des rôles ci-dessous

## Données en sortie
- Accès accordé ou refusé, pour chaque requête
- Événement du journal de sécurité : rôle changé (ancien, nouveau, auteur)

## Qui fait quoi
- Administrateur : attribue les rôles (`compte-administration-utilisateurs`)
- Système : vérifie le droit à chaque requête

## Règles de gestion
- Un rôle par compte.
- Refus par défaut : une route ou une action sans droit déclaré est refusée.
- Le droit est vérifié côté serveur, sur chaque requête, pour l'action **et** pour la donnée visée (un compte ne lit pas la donnée d'un autre en changeant un identifiant dans l'URL).
- Cacher un bouton n'est pas un contrôle : l'interface cache ce que le rôle ne permet pas, le serveur le refuse.
- Un changement de rôle s'applique dès la requête suivante.
- Matrice des rôles (propre au projet, écrite avec l'utilisateur) :

| Rôle | Espace | Peut voir | Peut faire |
|---|---|---|---|
| <rôle> | <front-office / back-office> | <données> | <actions> |

## Cas d'erreur
- Action non permise → 403, « vous n'avez pas accès à cette action », aucune donnée renvoyée
- Donnée d'un autre compte ou d'une autre organisation → 404, comme si elle n'existait pas

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-suppression

```markdown
---
type: Exigence
title: Suppression de compte
description: "Effacement réel des données personnelles d'un compte, à sa demande ou par un administrateur"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Effacer réellement les données personnelles d'un compte qui le demande (RGPD, droit à l'effacement), sans casser les données métier qui le citent.

## Données en entrée
- Demande de l'utilisateur (avec son mot de passe) ou action d'un administrateur

## Données en sortie
- Données personnelles du compte effacées
- Données métier liées conservées, rattachées à « Utilisateur supprimé »
- Email de confirmation à l'adresse du compte, envoyé avant l'effacement
- Événement du journal de sécurité : compte supprimé (sans donnée personnelle, avec l'auteur)

## Qui fait quoi
- Utilisateur : demande la suppression de son compte depuis son profil
- Administrateur : supprime un compte, sur demande écrite de son titulaire
- Système : efface, ferme les sessions, confirme

## Règles de gestion
- La suppression redemande le mot de passe (ou la double authentification en `sso`) et une confirmation explicite.
- Elle est effective au plus tard 30 jours après la demande ; jusque-là le compte est désactivé et la demande peut être annulée par le titulaire.
- Effacer veut dire effacer : nom, email, profil, empreintes et secrets supprimés de la base, des index de recherche et des caches ; pas un simple indicateur « supprimé ». Les sauvegardes s'effacent à leur rotation, durée écrite dans `kb/cdc/juridique.md`.
- Les données que la loi oblige à garder (factures…) sont conservées pour la durée légale, selon `kb/cdc/juridique.md`.
- Le dernier administrateur actif ne peut pas être supprimé.

## Cas d'erreur
- Mot de passe faux → refus, soumis aux limites de `compte-connexion`
- Dernier administrateur → refus, « il doit rester au moins un administrateur actif »
- Effacement incomplet (une copie n'a pas pu être effacée) → l'erreur est journalisée et signalée aux administrateurs ; l'opération est relancée

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-journal-securite

```markdown
---
type: Exigence
title: Journal de sécurité
description: "Journal des événements de sécurité des comptes, non modifiable, consultable par les administrateurs"
tags: [socle-comptes]
espace: [back-office]
---
## Objectif du processus
Savoir qui s'est connecté, qui a tenté, et qui a changé quoi sur les comptes, pour détecter une attaque et répondre à un incident.

## Données en entrée
- Les événements des exigences `socle-comptes`

## Données en sortie
- Entrées du journal : date et heure UTC, type d'événement, compte concerné, auteur, adresse IP, résultat
- Écran de consultation, filtrable par compte, type et période

## Qui fait quoi
- Système : écrit chaque événement
- Administrateur : consulte et filtre

## Règles de gestion
- Événements journalisés : connexion réussie, connexion échouée, délai imposé, code de double authentification refusé, déconnexion, réinitialisation demandée et effectuée, mot de passe changé, email changé, double authentification activée ou réinitialisée, invitation envoyée, compte activé, créé, désactivé, réactivé, supprimé, rôle changé.
- Jamais dans le journal : mot de passe, jeton, code, secret, cookie de session.
- Le journal n'est ni modifiable ni supprimable depuis l'application, administrateurs compris.
- Conservation `{conservation_journal}`, puis purge automatique.
- Consultation réservée aux administrateurs ; la consultation elle-même n'est pas journalisée.

## Cas d'erreur
- Écriture du journal impossible → l'action sensible est refusée (pas d'action sans trace), l'erreur va au journal des erreurs
- Aucun événement pour les filtres → « aucun événement », filtres rappelés

## Responsable
Administrateur

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

### compte-organisation

Variante V3 `multi-organisation` uniquement.

```markdown
---
type: Exigence
title: Organisations
description: "Chaque compte appartient à une organisation ; aucune donnée ne passe d'une organisation à l'autre"
tags: [socle-comptes]
espace: [front-office, back-office]
---
## Objectif du processus
Isoler complètement les données de chaque organisation cliente, et laisser chacune gérer ses propres comptes.

## Données en entrée
- Organisation : nom ; compte : son organisation

## Données en sortie
- Organisations et leurs comptes
- Événements du journal de sécurité, avec l'organisation

## Qui fait quoi
- Administrateur de la plateforme : crée une organisation et invite son premier administrateur
- Administrateur d'organisation : gère les comptes de son organisation seulement (`compte-administration-utilisateurs`, limité à son organisation)
- Système : filtre chaque requête par organisation

## Règles de gestion
- Un compte appartient à une seule organisation, fixée à sa création.
- Chaque lecture et chaque écriture de donnée métier est filtrée par l'organisation du compte connecté, côté serveur, dans la couche d'accès aux données (pas dans chaque écran).
- Un administrateur d'organisation ne voit ni n'agit sur aucun compte d'une autre organisation.
- Il reste au moins un administrateur actif par organisation.

## Cas d'erreur
- Donnée d'une autre organisation demandée → 404, comme si elle n'existait pas
- Dernier administrateur de l'organisation → refus, « il doit rester au moins un administrateur actif »

## Responsable
Administrateur de la plateforme

## Besoin(s) persona répondu(s)
Aucun — exigence transverse.
```

---

## Cas d'abus

`hosa-security` writes these under `## Cas d'abus` in `kb/cdc/securite.md` (Mode 1 Phase 2), one `###` per exigence kept; `backlog` copies the matching ones into each ticket's security note, and `hosa-qa-lead` makes each one a `[sécurité]` case.

- **compte-connexion** — Étant donné un compte existant, quand un attaquant enchaîne 20 mots de passe faux sur son email, alors à partir du `{echecs_identifiant}`+1e chaque tentative attend le délai, et le bon mot de passe pendant le délai est refusé. · Quand un attaquant essaie un mot de passe sur 50 emails depuis une IP, alors la limite IP répond 429 après `{tentatives_ip}`. · Quand il compare les réponses (message, code HTTP, délai) d'un email existant et d'un email inconnu, alors elles sont identiques. · Quand l'application tourne sur deux instances, alors le compteur est commun.
- **compte-session** — Quand un attaquant rejoue le cookie d'une session déconnectée, alors 401. · Quand il fixe un identifiant de session avant la connexion de la victime, alors l'identifiant change à la connexion. · Quand le mot de passe est changé, alors une autre session déjà ouverte reçoit 401.
- **compte-mot-de-passe-oublie** — Quand un attaquant réutilise un lien déjà utilisé ou expiré, alors refus. · Quand il demande la réinitialisation pour un email inconnu, alors la réponse est la même que pour un email connu. · Quand il envoie 10 demandes pour un même email en une heure, alors seules 3 partent.
- **compte-invitation / compte-inscription** — Quand un visiteur ajoute un champ `role=admin` à la requête, alors le rôle de base est attribué. · Quand un lien d'invitation est utilisé deux fois, alors la seconde est refusée.
- **compte-email** — Quand une session volée demande un changement d'email sans le mot de passe, alors refus.
- **compte-administration-utilisateurs** — Quand un administrateur appelle directement l'action « changer le rôle » sur un compte de rôle supérieur, alors 403. · Quand le dernier administrateur se désactive, alors refus.
- **compte-roles-droits** — Quand un compte demande la ressource d'un autre compte par son identifiant, alors 404 et rien n'est renvoyé. · Quand un rôle front office appelle une route back office, alors 403.
- **compte-journal-securite** — Quand un administrateur tente de modifier ou de supprimer une entrée du journal par une requête directe, alors refus. · Quand une connexion échoue, alors le mot de passe saisi n'apparaît ni dans le journal ni dans les journaux techniques.
- **compte-organisation** — Quand un compte de l'organisation A demande une donnée de l'organisation B par son identifiant, alors 404.

## Découpage en tickets

`backlog` Step 2 uses this split for the exigences tagged `socle-comptes` instead of re-slicing them; criteria still come from each exigence's rules and error cases, one scenario per rule. Rows whose exigence the variants removed are dropped, and `depends_on` follows to the next ticket kept. Proposed priority: these tickets first, in this order — every other ticket that needs a logged-in user depends on `connexion`.

| Ticket | Exigence(s) | Contenu | `depends_on` |
|---|---|---|---|
| `premier-administrateur` | compte-premier-administrateur, compte-invitation (activation) | commande d'exploitation, lien d'invitation, définition du mot de passe | — |
| `connexion` | compte-connexion, compte-session, compte-journal-securite (écriture) | connexion, **limitation par identifiant et par IP**, session, déconnexion, création du journal et écriture de ses événements | `premier-administrateur` |
| `double-authentification` | compte-connexion (double authentification) | activation TOTP, codes de secours, vérification à la connexion, mêmes limites | `connexion` |
| `administration-comptes` | compte-administration-utilisateurs, compte-invitation | liste, recherche, invitation, renvoi, désactivation, réactivation, réinitialisation de la double authentification | `connexion` |
| `roles-et-droits` | compte-roles-droits | rôles, matrice, contrôle serveur sur chaque route, changement de rôle | `administration-comptes` |
| `inscription` | compte-inscription | inscription, vérification d'email | `connexion` |
| `mot-de-passe-oublie` | compte-mot-de-passe-oublie | demande, lien, nouveau mot de passe | `connexion` |
| `changement-mot-de-passe` | compte-mot-de-passe | politique, changement, fermeture des autres sessions, liste des sessions ouvertes | `connexion` |
| `changement-email` | compte-email | demande, confirmation, notification | `connexion` |
| `suppression-compte` | compte-suppression | demande, délai d'annulation, effacement | `administration-comptes` |
| `journal-securite` | compte-journal-securite (consultation) | écran de consultation, filtres, purge | `administration-comptes` |
| `organisations` | compte-organisation | organisations, filtre par organisation, administrateur d'organisation | `roles-et-droits` |
