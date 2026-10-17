---
type: Sommaire
title: Sommaire de la KB
description: Une ligne par concept — lire ceci d'abord, puis seulement les fichiers utiles
tags: [pilotage]
generated: { by: process:hosa-kb-index, at: 2026-10-11T07:00:50Z }
---
11 concepts. Extraire une partie précise : `kb_query.py <kb> --type … --where … --sections …`. Code : `graph.py map` (bundle `code/`, non listé ici).

## cdc (1)
- [Exemple d'exigence](cdc/exemple-exigence.md) — Exigence · draft — Ceci est un exemple pour vérifier que l'app affiche bien la KB.

## personnas (1)
- [Exemple de persona](personnas/exemple-persona.md) — Persona · draft — Persona d'exemple pour vérifier l'affichage dans l'app.

## project (1)
- [Exemple de projet](project/exemple-identity.md) — Project · draft — Exemple d'objectif pour vérifier l'affichage de la page d'accueil.

## rules (7)
- [Authentification et autorisation](rules/security/authentification-autorisation.md) — Security Rule · stable — Contrôle d'accès sur chaque route sensible, pas d'IDOR — un utilisateur authentifié n'accède qu'à ses propres ressources.
- [Données sensibles](rules/security/donnees-sensibles.md) — Security Rule · stable — Pas de PII en log ni en réponse d'erreur ; finalité et durée de rétention définies, suppression effective y compris backups/caches.
- [En-têtes et CORS](rules/security/en-tetes-cors.md) — Security Rule · stable — CSP/HSTS/X-Frame-Options présents, origines CORS explicites — jamais `*` avec credentials.
- [Injection](rules/security/injection.md) — Security Rule · stable — Requêtes SQL paramétrées, aucune commande shell construite par concaténation d'une entrée utilisateur.
- [Limitation de débit sur l'authentification](rules/security/limitation-debit.md) — Security Rule · stable — Rate limiting sur les routes d'authentification, backé par un store partagé si plusieurs instances tournent.
- [Secrets](rules/security/secrets.md) — Security Rule · stable — Aucune clé, mot de passe ou token en dur dans le code ni dans l'historique git.
- [Validation des entrées aux frontières](rules/security/validation-entrees.md) — Security Rule · stable — Toute entrée (API publique, formulaire) est validée côté serveur — jamais côté client seul.

## tickets (1)
- [Exemple de ticket](tickets/exemple-ticket.md) — Ticket · todo — Ticket d'exemple pour vérifier le kanban de l'app.
