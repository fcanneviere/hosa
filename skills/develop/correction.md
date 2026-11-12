# Develop — Correction Mode

Read by `develop` when it is invoked with `correction`, or when a review of Step 4c is FAIL (point 4, the `## Corrections` line). The steps named here (4b, 4c, 5, 6, 7) are those of `SKILL.md`.

`/develop <slug-ticket> correction`, or chained by `qa`, `validation` (démo) or the review: a defect on a ticket of the **active** sprint is fixed in that sprint, on its worktree — never left as a backlog ticket while the sprint waits.
1. **Montre d'abord.** Le défaut a déjà un test en échec (QA) → passe-le. Démo, recette → dispatch `hosa-tester` en Écrire d'abord avec le rapport du défaut : un test qui le reproduit, en échec. Revue, audit → `hosa-developer` écrit ce test lui-même (point 3, son étape 11). Aucun constat reproduit → aucun code, aucun commit, le ticket garde son état ; écrit quand même la ligne `## Corrections` (point 4 : `0 prouvé(s)`, commit `aucun`), qu'elle soit mesurée — après une boucle, c'est elle qui prouve `develop` ; rapporte les `non reproduit` (test et sortie) à la source — l'utilisateur pour une démo, la revue de correction, ou le ré-audit (`qualite`, audit du sprint), qui les juge sur ce test.
2. Au moins un constat prouvé → écrit `state: doing` sur le ticket et retire `verified` (même s'il était `done`). Log, avec la source du défaut.
3. Pas de `hosa-tech-lead` : dispatch `hosa-developer` en `correction`, `model: sonnet`, avec le test, le rapport et les fichiers concernés. Cause floue ou défaut qui touche plusieurs modules → `debug` en mode auto, sur le worktree et le `docker_project` du sprint.
4. **Type de la correction**, d'après son diff :
   - **technique** — le diff ne touche ni un écran, un gabarit, un libellé ou un message visible du `## Placement interface` du ticket, ni un `CAn`. Cas courant d'une revue, d'un audit ou d'un test en échec.
   - **fonctionnelle** — sinon, et toujours pour un défaut de recette ou de démo. Nomme les `CAn` touchés.
   Ajoute une ligne sous `## Corrections` du ticket (KB de la racine) : `- <AAAA-MM-JJTHH:MMZ> — <source : revue | audit | qa | recette <persona> | démo> — <technique | fonctionnelle : CAn…> — <P> prouvé(s), <N> non reproduit(s) — <commit>`. `usage_report` en tire la pertinence des retours du sprint.
5. Puis étapes 4b, 4c (revue de correction), 5, 6 (commit `fix:` avec `Hosa-Ticket:`) et 7.
6. Suite. Correction d'un Bloquant de l'audit du sprint, avant la QA → ré-audit seulement : aucun test du sprint, aucune recette, aucune validation n'a encore tourné. Sinon, la boucle `back qa|validation develop` a rouvert `develop`, `audit` et `qa` : `done develop`, puis le ré-audit (`qualite sprint <slug>`, sur le diff de la correction seul), puis, selon le type — une correction technique ne change rien de ce qu'un persona voit, la rejouer chez lui ne prouve rien de plus :
   - **technique** → `qa <sprint> <ticket> technique` : les tests seuls, les recettes restent valables ; puis `validation` en reconfirmation.
   - **fonctionnelle** → `qa <sprint> <ticket>` : les tests, puis la recette des seuls `CAn` touchés, chez les seuls personas qui les recettent ; puis `validation`.
