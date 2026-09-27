---
type: Security Rule
title: Authentification et autorisation
description: Contrôle d'accès sur chaque route sensible, pas d'IDOR — un utilisateur authentifié n'accède qu'à ses propres ressources.
tags: [owasp]
status: stable
generated: { by: human:fcanneviere, at: 2026-09-27T00:00:00Z }
---
Chaque route qui expose ou modifie une ressource vérifie à la fois que l'utilisateur est authentifié et qu'il a le droit d'agir sur cette ressource précise (pas seulement sur "une" ressource du même type — IDOR).
