# Développer Hosa

Tests : `node --test hooks/*.test.js` et, dans `hosa/app`, `python -m unittest`. Règles des skills et des agents : `skills/using-hosa/SKILL.md`.

## Toujours respecter les bonnes pratiques des graphes et des boucles

Chaque changement de Hosa (skill, agent, hook, script) les respecte. Un changement qui en casse une est refusé, même s'il marche.

### Le graphe

- **Une seule définition.** Les étapes, leur ordre, le skill de chaque étape et les boucles sont dans `skills/status/scripts/pipeline.json`, et nulle part ailleurs. Le code le lit (`avancement.py`, `budget.js`). Le mod lit le plan que `avancement.py` écrit. Jamais une 2ᵉ liste dans un fichier : un test vérifie que la prose de `using-hosa` et du README suit le graphe.
- **Une preuve de sortie par étape.** Chaque étape a sa preuve dans `avancement.py check` : le fichier que son skill écrit, ou le contrôleur qu'il doit passer. `done` refuse sans elle. Une nouvelle étape arrive avec sa preuve et son test. Une preuve se lit dans la KB, jamais dans la mémoire d'une session.
- **Chaque retour en arrière est une arête.** Un skill qui renvoie du travail à une étape précédente appelle `avancement.py back <de> <vers>`, et cette boucle est déclarée dans `pipeline.json`. Jamais un renvoi en prose seule.
- **L'état vit dans la KB.** Le plan d'avancement et la KB gardent tout : une session coupée reprend à l'étape, au ticket et à la tâche exacts.
- **Entre agents, des chemins.** Un agent rend les chemins des fichiers qu'il a écrits, pas leur contenu réécrit.

### Les boucles

- **Une sortie vérifiable par une machine.** Un test, un contrôleur (exit 0/1) ou un verdict écrit (PASS/FAIL). Jamais « quand ça semble bon ».
- **Un retour déterministe.** Chaque tour reçoit les manques exacts du tour précédent, pas un résumé.
- **Une borne.** 2 tours par défaut, comptés par cause : une autre cause recommence le compte.
- **L'humain décide au-delà de la borne.** La boucle s'arrête et montre ce que chaque tour a essayé. `--force` seulement sur la parole de l'utilisateur.
- **Appliquées par du code, pas seulement écrites.** Une borne ou une porte est un refus d'un hook ou d'un script (`gate.js`, `budget.js`, `avancement.py`), avec son test. Un hook ne bloque jamais sur sa propre erreur (fail-open) et a son interrupteur (`HOSA_GATE=0`…).
- **Mesurer pour apprendre.** Les mesures du bilan de sprint et `kb/retours-hosa/journal.md` sont la boucle au-dessus des boucles : on corrige Hosa à partir d'elles.
