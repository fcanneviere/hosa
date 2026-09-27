---
type: Security Rule
title: Secrets
description: Aucune clé, mot de passe ou token en dur dans le code ni dans l'historique git.
tags: [owasp]
status: stable
generated: { by: human:fcanneviere, at: 2026-09-27T00:00:00Z }
---
Tout secret vient de la configuration d'environnement (jamais commité), y compris dans l'historique git (un secret retiré du code mais resté dans un ancien commit reste compromis).
