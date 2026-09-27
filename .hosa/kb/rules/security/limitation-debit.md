---
type: Security Rule
title: Limitation de débit sur l'authentification
description: Rate limiting sur les routes d'authentification, backé par un store partagé si plusieurs instances tournent.
tags: [owasp]
status: stable
generated: { by: human:fcanneviere, at: 2026-09-27T00:00:00Z }
---
Les routes de login/inscription/réinitialisation de mot de passe limitent le nombre de tentatives par identifiant/IP. Si l'application tourne en plusieurs instances, le compteur est backé par un store partagé (pas une variable en mémoire locale à une instance).
