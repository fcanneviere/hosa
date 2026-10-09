---
name: securite
description: "Use for the managed project's security, in three moments: constraints in the cahier des charges (CDC stage 4, mandatory), threat model after `architecture` (STRIDE, abuse cases), Go/No-Go before a release; also a code audit on request. Dispatches `hosa-security`. Triggers: \"sécurité dès la conception\", \"modèle de menaces\", \"audite la sécurité\"."
---

# Sécurité

Security by design, then by check. `hosa-security` gives its constraints while the cahier des charges is written, so they reach the stack, the architecture, every ticket and every task. Once the architecture exists, it models how the real application can be attacked: the abuse cases become tests. Before each release, it audits what changed and refuses to ship a known exploitable flaw.

## Modes

| Mode | When | Agent mode | Writes |
|---|---|---|---|
| **Analyse** | CDC stage 4, right after `fondamentaux` (default inside the CDC pipeline) | Mode 1 | `kb/cdc/securite.md`, security exigences, `## Contraintes de sécurité`, `kb/rules/security/*` |
| **Menaces** | Right after `architecture`, chained; again when the architecture changes | Mode 3 | `kb/securite/modele-menaces.md`, `kb/rules/security/*` |
| **Audit** | On request, or from `qualite` | Mode 2 | `kb/securite/audit-<date>-<scope>.md` |
| **Livraison** | Inside `livraison`, after the quality audit | Mode 4 | `kb/securite/livraison-<version>.md` |

No mode stated and none obvious from the context → one numbered question (Analyse, Menaces, Audit, Livraison).

## Flow

```
Détermine le mode (et le projet géré : kb/infra/)
        ↓
Analyse : hosa-security Mode 1 Phase 1 → propositions → l'utilisateur
          valide, ajuste ou accepte un risque → Phase 2 écrit
Menaces : hosa-security Mode 3 → ADR (hosa-documentation)
Audit   : hosa-security Mode 2 → Bloquant = ticket priorité 1
Livraison : hosa-security Mode 4 → Go / No-Go
        ↓ Open Questions → Q1, Q2… à l'utilisateur, redispatch
        ↓ Installation nécessaire → hosa-infra (Mode 2), redispatch
Checkpoint hosa-git (Mode 3), puis enchaîne : relecture
(Analyse) / interface (Menaces) / retour à livraison
```

## Trigger

Manual: `/securite [analyse|menaces|audit|livraison]`. Auto: immediately after `fondamentaux` (Analyse) and after `architecture` (Menaces); "analyse la sécurité du cahier des charges", "sécurité dès la conception" (Analyse); "modèle de menaces" (Menaces); "fais une revue de sécurité", "audite la sécurité du code", "est-ce que c'est sécurisé ?" (Audit). `contestation` invokes Analyse itself if `kb/cdc/securite.md` is missing or out of date; `livraison` invokes Livraison.

Progress-plan stages: `securite` (Analyse, CDC pipeline) and `menaces` (Structuration, after `architecture`).

---

## Analyse (Mode 1)

1. Dispatch `hosa-security` (Mode 1 Phase 1). Relay its `## Open Questions` (data classification, regulatory scope) and redispatch with the answers until the analysis is complete.
2. Present the data and their sensitivity, then per exigence the threats and the proposed measure, then the proposed security exigences, constraints and rules. The user validates, adjusts, or drops a measure. A dropped measure on a real threat is an **accepted risk**: ask for the reason and keep it, recorded rather than forgotten.
3. Redispatch `hosa-security` (Mode 1 Phase 2) with the validated choices and the accepted risks. It seeds `kb/rules/security/`, writes the security exigences (`status: draft`, `tags: [securite]`), adds `## Contraintes de sécurité` to the exigences concerned, and writes `kb/cdc/securite.md`.

## Menaces (Mode 3)

`kb/infra/` has no `## Documentation d'architecture` → run `architecture` first. Dispatch `hosa-security` (Mode 3). It refines `kb/cdc/securite.md` on the real architecture: trust boundaries, STRIDE, abuse cases (`qa-plan` turns them into tests), new `Security Rule`s. Relay its Open Questions: decisions already taken in Analyse aren't asked again. Its `## Documentation à produire` → `hosa-documentation` (Mode 1): each structuring security decision becomes an ADR.

## Audit (Mode 2)

Read `kb/infra/` for the root — missing → stop. Scope: the file list given by `qualite` or `livraison`; right after a ticket or sprint, the files touched; otherwise one numbered question (whole codebase, recommended for a first audit, or recent files). Dispatch `hosa-security` (Mode 2). For each **Bloquant**, dispatch `hosa-product-owner` to create a `Ticket` (`state: todo`, `priority: 1` — an exploitable flaw jumps the queue) linked to the audit and the finding's `fichier:ligne`, then run `backlog`'s Single-Ticket Mode on it. **À corriger** and **Mineur** stay in the audit. A secret found in a pushed history: tell the user at once that it must be rotated first — purging the history doesn't un-leak it.

## Livraison (Mode 4)

Dispatch `hosa-security` (Mode 4) with the version and the date of the previous release. Return the verdict to `livraison`. **No-Go** → one numbered question: fix first (recommended), or ship anyway knowingly. Shipping anyway is written in `kb/securite/livraison-<version>.md` under `## Dérogation` with `generated.by: human:<user>` — the user's decision, written down, never implied.

## Commits

None here: the skill ends with the `hosa-git` checkpoint (`using-hosa`, Git checkpoints).

## Output

```
## Sécurité — <mode>
- [Analyse] Données sensibles : [liste et classification] — menaces traitées : N — risques acceptés : N — écrit : `kb/cdc/securite.md`, exigences, règles
- [Menaces] `kb/securite/modele-menaces.md` — N frontières, N menaces, N cas d'abus — règles ajoutées : N
- [Audit] `kb/securite/audit-<date>-<scope>.md` — [Propre / N constats dont B bloquants] — tickets créés : […]
- [Livraison] `kb/securite/livraison-<version>.md` — Go / No-Go

## Suite
[Analyse → `relecture`, lancé. Menaces → `interface`, lancé. Audit avec bloquant → le ticket entre au prochain sprint (`develop <ticket> correction` s'il touche le sprint actif). Livraison → retour à `livraison`.]
```
