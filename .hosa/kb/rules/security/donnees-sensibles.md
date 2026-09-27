---
type: Security Rule
title: Données sensibles
description: Pas de PII en log ni en réponse d'erreur ; finalité et durée de rétention définies, suppression effective y compris backups/caches.
tags: [owasp]
status: stable
generated: { by: human:fcanneviere, at: 2026-09-27T00:00:00Z }
---
Aucune donnée personnelle identifiable dans les logs applicatifs ou les messages d'erreur renvoyés au client. Chaque catégorie de donnée sensible a une finalité et une durée de rétention définies, et une suppression demandée doit être effective y compris dans les sauvegardes et caches, pas seulement la base primaire.
