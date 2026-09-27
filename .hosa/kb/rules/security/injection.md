---
type: Security Rule
title: Injection
description: Requêtes SQL paramétrées, aucune commande shell construite par concaténation d'une entrée utilisateur.
tags: [owasp]
status: stable
generated: { by: human:fcanneviere, at: 2026-09-27T00:00:00Z }
---
Toute requête vers une base de données doit être paramétrée (jamais de concaténation de chaîne avec une entrée utilisateur). Toute commande shell doit éviter la concaténation d'une entrée utilisateur — utiliser un appel avec arguments séparés, jamais une chaîne interprétée par un shell.
