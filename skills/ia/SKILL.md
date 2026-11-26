---
name: ia
description: "Use for any AI feature, local or cloud: frame it (baseline, threshold, budget), then measure the models on real data. Triggers: \"intégrer une IA\", \"quel modèle ?\", \"évalue le modèle\"."
---

# IA

**Plan d'avancement.** `avancement.py` = `<hosa> avancement <root>/.hosa/kb`. Two stages, `cadrage-ia` (cahier des charges, after `fondamentaux`) and `essai-ia` (structuration, after `infra`). Before anything: `avancement.py start <stage>`; refused → name the missing stage to the user and stop; refused as already done or `non applicable` → a run only on the user's request: the same `start` with `--rouvre "<their request>"` (a project begun before these stages: `cadrage-ia` first, then `essai-ia`). Stopped on a user question: `block <stage> --detail "<question>"`. Once the output is written and committed: `done <stage>`.

**Tâches.** Before each dispatch, `avancement.py task add <stage> <id> --agent hosa-ia`; on its return, `task done <stage> <id> --sortie <the paths it wrote>`: `cadrage-ia` → `phase-1` (`kb/cdc/ia.md` `## Choix validés`), `phase-2` (`kb/cdc/ia.md` and the exigences); `essai-ia`, in order: `besoins` (`hosa-ia`, `kb/stack/essai-ia.md`), `installation` (`hosa-infra`, that file and what it installed), `essai` (`hosa-ia`, that file and the evaluation script). The first two are controlled: a specification or a need incomplete, or not verified, refuses `task done`, and each next task refuses `task add` before. Stopped on an Open Question → `task block <stage> <id> --detail "<la question>"`, and `task add` the same id again once answered.

`hosa-ia` does the AI work; this skill talks to the user and dispatches.

## Cadrage (`cadrage-ia`)

1. Look for AI in the exigences (`kb_query.py .hosa/kb --type Exigence --sections "Objectif,Règles de gestion"`) and in `fondamentaux.md` `## Contexte`: a function that predicts, classifies, ranks, extracts, generates, recognises or converses with a model.
   - **None** → `skip cadrage-ia --detail "aucune fonction d'IA"` and `skip essai-ia --detail "aucune fonction d'IA"`, say it in one line, chain `juridique`.
   - Unsure → one question to the user.
2. `hosa-ia` Mode 1 Phase 1. Relay its Open Questions: for each function, its form (single call, RAG, MCP, agent) and that form's fields (documents and who may read them; MCP servers, tools, actions to confirm; bounds), the baseline without AI, the threshold, the longest duration, local or cloud, the data that may leave the machine, the budget, what the product does when the model is wrong.
3. Write the answers in `kb/cdc/ia.md` (`type: Cadrage IA`, `status: draft`) under `## Choix validés`, then `task done cadrage-ia phase-1`.
4. `hosa-ia` Mode 1 Phase 2 with that file: it writes the cadrage and puts each threshold in its exigence.
5. `done cadrage-ia` refuses while a function lacks a field (`<hosa> ia_check .hosa/kb cadrage`). Checkpoint, chain `juridique`.

Reopened by a loop → the change is a new line under `## Révisions`; a signed (`stable`) exigence changes through `changement`.

## Essai (`essai-ia`)

1. `cadrage-ia` is `non applicable` → `skip essai-ia` with the same reason, chain `donnees`.
2. Task `besoins`: `hosa-ia` Mode 2a — the technical specification of each function and **everything** to install.
3. Task `installation`: `hosa-infra` Mode 2 (`infra`) with the whole `## Besoins d'installation`: it installs, runs each verification in the container and writes its exit code. Ask the user to put each API key in the untracked environment file — never in the chat.
4. Task `essai`: `hosa-ia` Mode 2b with `docker_project`. Relay the Open Questions (real data, yes before a cloud call or a paid one). A new `## Installation nécessaire` → `task add essai-ia installation` again, then `essai`.
5. Show the user one table: model, measure against the baseline and the threshold, duration, memory, cost, PASS or FAIL. Several models pass → one question: which one (recommend one).
6. **A function FAILS** → one question, then act:
   a) another model or library (recommended when one is untried): `back essai-ia stack --cause IA<n> --detail "<mesuré contre seuil>"`;
   b) change the threshold, or drop the function: `back essai-ia cadrage-ia --cause IA<n> --detail "…"`;
   c) go on knowing it: `done essai-ia --force`, their reason in `kb/cdc/decisions.md`.
   `back` refused (2 rounds for one cause) → show what each round measured; the user decides.
7. `done essai-ia` refuses without each specification, each need verified, a PASS per function (`<hosa> ia_check .hosa/kb essai`) or while a measure of this stage is unwritten. Checkpoint (the evaluation script included), chain `donnees`.

## Rejeu (from `qa` and `livraison`, not a stage)

`done qa` and `done livraison` refuse when a function's tracked files differ from the ones its last PASS measured. The calling skill dispatches `hosa-ia` Mode 3 as its own task (`ia-rejeu`). Its `## Installation nécessaire` goes to `hosa-infra` (Mode 2, which writes each exit code), then `hosa-ia` again. FAIL → a defect: in `qa`, `back qa develop`; in `livraison`, stop and make a ticket. `HOSA_IA=0` turns the AI checks off.

## Commits

None here: the skill ends with the `hosa-git` checkpoint (`using-hosa`, Git checkpoints).

## Output

```
## IA — <cadrage | essai>
- IA1 — <cadrée | PASS | FAIL> — <modèle, mesure contre référence>
- Écrit : <chemins>

## Suite
Suite : `juridique` | `donnees`, lancé sans attendre.
```
