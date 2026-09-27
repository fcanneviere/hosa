---
type: Security Rule
title: Validation des entrées aux frontières
description: Toute entrée (API publique, formulaire) est validée côté serveur — jamais côté client seul.
tags: [owasp]
status: stable
generated: { by: human:fcanneviere, at: 2026-09-27T00:00:00Z }
---
Une validation côté client (JS, contraintes HTML) est un confort d'usage, jamais une garantie de sécurité — elle est contournable. Chaque route/endpoint qui accepte une entrée doit la revalider côté serveur avant de l'utiliser.
