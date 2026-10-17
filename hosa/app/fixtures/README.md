# Jeu de données de test — sprint 1 « Tableau et socle »

L'application n'a pas de base de données : elle lit une KB de fichiers Markdown (`HOSA_KB_ROOT`).
Le jeu de données est donc une KB factice, écrite par `jeu.py`. Rien ici ne touche la vraie KB `.hosa/kb`.

`jeu.py` fournit :

| Élément | Contenu | Usage |
|---|---|---|
| `KB` | dict chemin → texte, la KB de référence (34 fichiers) | `jeu.ecrire(root)` |
| `NON_UTF8` | une recette en latin-1, hors `KB` | `jeu.ecrire(root, {**jeu.KB, **jeu.NON_UTF8})` |
| `SRC`, `depot(checkout, changes)` | projet git : KB sous `.hosa/kb`, `src/auth.py`, un commit `Hosa-Ticket: connexion`, puis 0 à 3 changements non sauvegardés | renvoie la racine KB |
| `transcripts(base, today)` | transcripts Claude Code factices (dates relatives à `today`) | `base` = `usage_report.project_dir` patché |

Dans les tests (`hosa/app`), même schéma que `setUp` de `test_app.py` :

```python
from fixtures import jeu
self.root = jeu.ecrire(Path(self.tmp.name))                 # KB hors git
root = jeu.depot(Path(self.tmp.name), changes=3)            # KB dans un dépôt git
jeu.ecrire(Path(self.tmp.name), {})                         # KB vide
jeu.ecrire(root, {k: v for k, v in jeu.KB.items() if not k.startswith("test/")})  # KB sans test/
base = jeu.transcripts(Path(self.tmp.name) / "usage")       # puis patcher usage_report.project_dir
```

Chaque test part d'un dossier temporaire neuf : pas de remise à zéro à faire.

## Remise à zéro

Pour la recette et les contrôles navigateur, depuis `hosa/app` :

```sh
python fixtures/jeu.py                    # KB avec 3 changements non sauvegardés (défaut)
python fixtures/jeu.py --changes 0        # KB propre (etat-kb-api-statut CA2)
python fixtures/jeu.py --changes 1        # 1 changement (CA4, cas limite)
HOSA_KB_ROOT="$TMP/hosa-ui-recette/.hosa/kb" python server.py
```

La commande :
1. supprime `$TMP/hosa-ui-recette` (dépôt git, `.hosa/graph/` construit par l'app, écritures des tests) ;
2. supprime les transcripts factices `~/.claude/projects/<chemin de la copie>` ;
3. réécrit la KB, le code et le commit, applique les changements demandés ;
4. réécrit les transcripts factices ;
5. lance `## Vérification`.

Elle est idempotente. Un autre dossier : `python fixtures/jeu.py <dest>`.
Hors de ce dossier, l'app ne garde ni cache, ni file, ni session, ni fichier envoyé.

## Comptes de test

Aucun compte : outil local mono-utilisateur, sans authentification ni rôle (décision human:fabien 2026-10-11).
Le nom saisi à la validation (`human:<nom>`) est libre : utiliser `test` ou `fabien`, jamais un vrai tiers.

| Persona | Recette | Données utilisées |
|---|---|---|
| Karim, responsable technique | `consommation-api-usage` | transcripts factices de la copie |
| Karim | `graphe-trace-sans-index` | copie git sans `.hosa/graph/` |
| Camille, développeuse | `etat-kb-api-statut` | copie avec 3 changements, puis `--changes 0` |
| Martine, commanditaire | `qualite-recettes-api` | recettes PASS, FAIL, PASS-WITH-NOTES de `test/` |
| Martine | `validation-provenance-liste` | concepts produits par agent, validés machine, validés humain, `deprecated` |

## Vérification

```sh
python fixtures/jeu.py --check [--changes N]
```

Sortie `OK : état de référence` et code 0, sinon la liste des écarts et code 1. Elle contrôle :
- chaque fichier de `KB` existe, aucun fichier en trop (hors changements prévus) ;
- `git status --short` compte exactement N lignes ;
- `.hosa/graph/` est absent ;
- les transcripts factices existent.

## Données par plan de test

### `tickets-tableau-colonnes`
| Fichier | Cas |
|---|---|
| `tickets/annuaire.md` (doing, p1, L), `export-csv.md` (doing, p1, M), `connexion.md` (doing, p2, M) | CA1, CA2 (p1 avant p2, égalité triée par titre), CA4 (11 points) |
| `tickets/recherche.md` (todo, S), `titre-hostile.md` (blocked, `estimate: 2`), `inscription.md` (done) | CA1 quatre états, CA4 S=1 et estimation numérique |
| `tickets/etat-inconnu.md` (`state: foo`, `estimate: à voir`), `sans-etat.md` (ni état, ni priorité, ni estimation) | CA1 classés « À faire », CA2 sans priorité en dernier, CA4 texte libre → 0 |
| `connexion` (`human:fabien`, vérifié humain), `export-csv` (agent, vérifié `hosa-lint`), `annuaire` (agent, non vérifié) | CA3 origine et validation |
| `titre-hostile.md` (`<img src=x onerror=alert(1)>`) | sécurité, titre en texte |
| `jeu.ecrire(root, {})` | CA5 KB sans ticket |

### `tickets-changer-etat`
| Fichier | Cas |
|---|---|
| `tickets/recherche.md` (todo) | CA1, CA3, sécurité (YAML hostile, champs en plus, `type`) |
| `tickets/log.md` | CA2, lignes précédentes intactes |
| `tickets/casse.md` (YAML invalide) | CA4, erreur lisible |
| `tickets/index.md`, `tickets/log.md` | sécurité, noms réservés intacts |
| slug absent (`tickets/supprime.md`) | CA4, 404 |

### `validation-provenance-liste`
| Fichier | Cas |
|---|---|
| `cdc/export.md` (agent, non vérifié, le plus ancien) | CA1, CA5 |
| `tickets/export-csv.md` (vérifié `hosa-lint`) | CA1 « contrôlé automatiquement » |
| `cdc/login.md`, `tickets/connexion.md` (`human:fabien`) | CA2 « validé par vous » |
| `personnas/karim.md` (`human:martine`) | CA2 autre nom humain |
| `cdc/ancienne.md`, `obsolete-lint.md`, `obsolete-humain.md` (`deprecated`) | CA3 |
| `tickets/annuaire.md` (agent, le plus récent), `sprints/s1.md` (agent) | CA4 Ticket et Sprint, CA5 tête de liste |
| `personnas/martine.md` (Persona, agent) | CA4 non-régression |
| `tickets/sans-etat.md`, `etat-inconnu.md` (sans `generated`) | CA5 tri sans date |

### `qualite-couverture-criteres-api`
| Fichier | Cas |
|---|---|
| `tickets/export-csv.md` + `test/export-csv-technique.md` ([CA1], [CA3]) + recette `- CA2 — Non` | CA1 (CA1, CA3 couverts), CA2 « Non » ne couvre pas |
| `tickets/connexion.md` + plan [CA1] + recette `- CA2 — Oui` | CA2 couvert par la recette |
| `tickets/annuaire.md` sans plan + recette `- CA1 — Oui` | CA3 `plan=false`, CA1 couvert |
| `tickets/recherche.md`, `sans-etat.md` (sans critère) | CA4 `criteres=[]` |
| `tickets/inscription.md` (CA1 à CA11) + plan [CA10], [CA11], `ACA1` | cas limite 10+ critères, `CA10`/`ACA1` ne couvrent pas `CA1` |
| `tickets/titre-hostile.md` (`CA1)(`) | sécurité, motif hostile |
| `KB` sans `test/` | cas limite, `plan=false` sans exception |

### `qualite-recettes-api`
| Fichier | Cas |
|---|---|
| `test/connexion-martine.md` (PASS, « FAIL » cité avant et après) | CA1 premier mot-clé après `## Verdict` |
| `test/export-csv-karim.md` (FAIL), `annuaire-camille.md` (PASS-WITH-NOTES) | CA1, CA2 FAIL en tête |
| `test/inscription-martine.md` (sans `## Verdict`) | CA1 `verdict: null` |
| `test/*-technique.md` | CA3 exclus de la liste |
| `test/recherche-karim.md` (titre `<script>`, verdict `PASS<script>`) | sécurité, injection et verdict hostile |
| `test/recherche-camille.md` (vide), `annuaire-martine.md` (frontmatter invalide), `NON_UTF8` | sécurité, fichiers illisibles |
| `jeu.ecrire(root, {})`, KB sans `test/` | CA4 liste vide |

### `etat-kb-api-statut`
| Données | Cas |
|---|---|
| `depot(tmp, 3)` : `recherche.md` modifié, `cdc/brouillon.md` non suivi, `brouillons/` (2 fichiers) | CA1 `changed: 3`, cas limite dossier = 1 ligne |
| `depot(tmp, 0)` | CA2 |
| `depot(tmp, 1)`, puis commit | CA4, recalcul sans cache |
| `jeu.ecrire(tmp)` | CA3 hors git |

### `graphe-trace-sans-index`
| Données | Cas |
|---|---|
| `depot(tmp)` : `src/auth.py`, commit `Hosa-Ticket: connexion`, `connexion` → `cdc/login.md`, pas de `.hosa/graph/` | CA1 (`find?q=login`), CA2, sécurité écriture sous `.hosa/graph/` |
| `jeu.ecrire(tmp)` | CA3 hors git, 404 |

### `consommation-api-usage`
`transcripts(base, today)` : session `s1.jsonl` et sous-agent `s1/subagents/agent-a1.jsonl`.

| Ligne | Acteur, modèle | 7 jours | 30 jours |
|---|---|---|---|
| aujourd'hui, appel du skill `qa-plan` et de l'agent | session principale, opus | oui | oui |
| aujourd'hui | skill qa-plan, sonnet | oui | oui |
| aujourd'hui, sous-agent `a1` | agent hosa-data-engineer, haiku | oui | oui |
| aujourd'hui − 7 (= `since`) | session principale, opus | oui | oui |
| aujourd'hui − 8 | session principale, opus | non | oui |
| aujourd'hui − 20 | session principale, sonnet | non | oui |
| aujourd'hui − 40 | session principale, opus | non | non |
| `{ligne cassée` | ignorée | — | — |

Appels attendus : 7 jours → session principale 2, skill qa-plan 1, agent hosa-data-engineer 1 ; 30 jours → session principale 4.
CA3 : dossier absent (rien d'écrit) ou vide (`mkdir`) → 404.
