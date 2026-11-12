# Develop — blocages

Read by `develop` only when an agent's report holds an ambiguity, a structural deviation or a `Blocked`.

## Plan

La sortie de `hosa-tech-lead` (étape 3) contient une entrée sous `Ambiguities` ou `Structural Deviation`. Rapporte-la telle quelle à l'utilisateur, propose la suite adaptée — combler l'ambiguïté avec l'utilisateur, ou, pour la déviation, la router vers le propriétaire qu'elle nomme : `architecture`/`hosa-architect` (module, couche), `schema-app`/`schema-db`/`hosa-data-engineer` (entité, champ), `hosa-ux-designer` (écran, composant, interaction) — ne dispatche aucune tâche, stoppe. Le ticket reste `state: doing`. Un fichier absent qu'un autre ticket crée (ambiguïté, pas déviation) : une seule question Q1 — A. créer le fichier dans ce ticket, avec le contrat de la `Note technique` du ticket créateur (recommandé quand le fichier est petit) — ce ticket le note `à créer`, le ticket créateur le note « existe, à étendre » ; B. sortir ce ticket du lot et ajouter le `depends_on` sur le ticket créateur. Puis relance le tech lead. **Tout ce qui touche l'interface (écran, parcours, composant, libellé visible) passe par `hosa-ux-designer`** en dispatch « Ticket gap » (slug, worktree, manque) : il complète l'écran dans le worktree et réécrit `## Placement interface (UX/UI)` ; puis relance cette étape.

## Lot

Si une tâche du lot revient avec `Structural Deviation` ou `Blocked` non vide (une valeur autre que `None`) : **arrête la boucle immédiatement (les tâches restantes ne sont pas tentées)**, rapporte à l'utilisateur — la même proposition que § Plan pour une déviation structurelle, ou la question posée telle quelle pour un blocage (un `Installation nécessaire` va à `hosa-infra`, Mode 2, puis redispatch du lot) — stoppe. Le ticket reste `state: doing`, aucun commit.
