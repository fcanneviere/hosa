---
name: securite
description: Use for anything about the managed project's security — threat-model it once its architecture is scaffolded (trust boundaries, STRIDE, abuse cases, `Security Rule` checklist), audit its code against OWASP / LLM / supply-chain / RGPD rules, or gate a release with a Go/No-Go. Dispatches `hosa-security`. Chained automatically after `architecture` (Mode Menaces) and inside `livraison` (Mode Livraison); audit usable anytime.
---

# Sécurité

Security by design, then by check: `hosa-security` models how the application can be attacked as soon as its architecture exists, turns that into the `Security Rule` checklist every later audit uses and abuse cases `qa-plan` turns into tests, audits the code against it, and refuses a release that ships a known exploitable flaw.

## Modes

| Mode | When | Writes |
|---|---|---|
| **Menaces** | Right after `architecture` (chained without asking), or on request when the architecture changes | `kb/securite/modele-menaces.md`, `kb/rules/security/*` |
| **Audit** | On request, anytime code exists | `kb/securite/audit-<date>-<scope>.md` |
| **Livraison** | Inside `livraison`, before release notes | `kb/securite/livraison-<version>.md` |

No mode stated and none obvious from the context → ask: "Q1. Modèle de menaces / audit du code / porte de livraison ?"

## Flow

```
Détermine le projet géré (kb/infra/) et le mode
        ↓
Dispatch hosa-security (mode)
        ↓ Open Questions → Q1, Q2… à l'utilisateur, réponses relayées,
          redispatch
        ↓ Installation nécessaire → hosa-infra (Mode 2), redispatch
Menaces : Documentation à produire → hosa-documentation (ADR)
Audit : Bloquant → hosa-product-owner crée un Ticket, propose debug
Livraison : No-Go → livraison s'arrête (sauf décision explicite)
        ↓
Checkpoint hosa-git (Mode 3), rapporte
```

## Trigger

Manual: `/securite [menaces|audit|livraison]`. Auto: "fais une revue de sécurité", "audite la sécurité du code", "check la sécurité du projet", "modèle de menaces", "est-ce que c'est sécurisé ?", "analyse les vulnérabilités" ; chained by `architecture` (Menaces) and `livraison` (Livraison).

---

## Step 1: Find the Managed Project and Scope

Read `kb/infra/` for the managed project's root path — missing → stop and say so, there's nothing to secure without it.

Audit scope: right after a ticket or sprint was implemented, default to the files touched; otherwise ask "Q1. Codebase entière (recommandé pour un premier audit) / fichiers récents ?" — never guess.

## Step 2: Dispatch `hosa-security`

Dispatch `hosa-security` (`agents/security.md`) with the mode, the scope (Audit), or the version and the previous release's date (Livraison).

- **`## Open Questions`** → relay them to the user as they come (already numbered, each with a recommended answer), then redispatch with the answers. These are the user's decisions (MFA, retention, sharing personal data with a third party) — never answer them yourself.
- **`## Installation nécessaire`** → dispatch `hosa-infra` (Mode 2) with the need, then redispatch `hosa-security` once it confirms. Never install a scanner from this skill.

## Step 3: Route the Results

- **Menaces** — dispatch `hosa-documentation` (Mode 1) with the `## Documentation à produire` field, if not "None", so each structuring security decision lands as an ADR in the managed project.
- **Audit** — for each **Bloquant**, dispatch `hosa-product-owner` (Responsibility 2/4) to create a `Ticket` (`state: todo`, `priority: 1` — an exploitable flaw jumps the queue) linked to the audit file and the finding's `fichier:ligne`, `generated: { by: hosa-security/1.0, at: <ISO8601> }`. Then propose `debug` on that ticket. **À corriger**/**Mineur** stay in the audit — one ticket per minor finding is backlog noise. A secret found in a pushed history is the exception: tell the user right away that it must be rotated before anything else — purging history doesn't un-leak it.
- **Livraison** — return the verdict to `livraison`. **No-Go** → ask the user: "Q1. Je corrige d'abord (recommandé) / je livre quand même en connaissance de cause ?" Shipping anyway is recorded in `kb/securite/livraison-<version>.md` under `## Dérogation` with `generated.by: human:<user>` — the user's decision, written down, never implied.

## No Commits

You don't commit. The checkpoint commit is `hosa-git`'s (Mode 3), dispatched at the end — see `using-hosa` Core Rules, "Git checkpoints".

## Output

```
## Sécurité — <mode>
- [Menaces] `kb/securite/modele-menaces.md` — N frontières, N menaces, N cas d'abus ; règles ajoutées : N
- [Audit] `kb/securite/audit-<date>-<scope>.md` — [Propre / N constats dont B bloquants]
- [Livraison] `kb/securite/livraison-<version>.md` — Go / No-Go

## Tickets créés
- `kb/tickets/<slug>.md` — [constat] (priorité 1)
[Si aucun : "Aucun"]

## Suite
[Menaces → "Je lance `interface` maintenant ?" / Audit avec bloquant → "Je lance `debug` sur <ticket> ?" / Livraison → retour à `livraison`]
```
