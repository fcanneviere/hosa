---
type: Security Rule
title: En-têtes et CORS
description: CSP/HSTS/X-Frame-Options présents, origines CORS explicites — jamais `*` avec credentials.
tags: [owasp]
status: stable
generated: { by: human:fcanneviere, at: 2026-09-27T00:00:00Z }
---
Les réponses HTTP portent des en-têtes de sécurité (CSP, HSTS, X-Frame-Options). La configuration CORS liste les origines autorisées explicitement — un wildcard `*` combiné à `credentials: true` n'est jamais acceptable.
