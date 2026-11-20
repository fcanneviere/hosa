"""cdc.py assembles the cahier des charges and finds every empty cell of its completeness matrices."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "redaction" / "scripts" / "cdc.py"
spec = importlib.util.spec_from_file_location("cdc", SCRIPT)
cdc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdc)

IDENTITY = """---
type: Project
title: Courses
---
## Description
Une liste partagée.

## Contexte et enjeux
Les demandes arrivent par SMS.

## Objectifs mesurables
| Id | Objectif | Indicateur | Cible | Mesure |
|---|---|---|---|---|
| O1 | Zéro oubli | Articles oubliés par liste | 0 | Foyer pilote, 4 semaines |

## Hypothèses, dépendances et risques
- Hypothèse : chacun a un téléphone.
"""

PERSONA = "---\ntype: Persona\ntitle: Les parents\n---\n## Besoins\n- Envoyer la liste.\n"

EXIGENCE = """---
type: Exigence
title: Envoyer la liste
espace: [front-office]
domaine: "Listes"
priorite: indispensable
lot: 1
objectifs: [O1]
status: stable
---
## Objectif du processus
Remettre la liste.

## Déclencheur
La liste est complète.

## Règles de gestion
- **RG1** — Une seule notification.

## Responsable
Parent.

## Besoin(s) persona répondu(s)
- [Les parents](../personnas/les-parents.md) : envoyer la liste.

## Schéma du processus
```mermaid
flowchart LR
  A[Liste complète] --> B[Parent : envoyer] --> C[Ados notifiés]
```

## Contraintes de sécurité
- Rôle vérifié côté serveur.
"""
EXIGENCE = EXIGENCE.replace("status: stable\n", f"status: stable\nschema_valide: \"2026-11-18 {cdc.empreinte(EXIGENCE)}\"\n")

MODELE = """---
type: Modèle Métier
title: Modèle métier
---
## Liste
### Cycle de vie
- **TR1** — (début) → en préparation : un parent crée la liste — [Envoyer la liste](envoyer-la-liste.md)
- **TR2** — en préparation → envoyée : un parent l'envoie — [Envoyer la liste](envoyer-la-liste.md)
- **TR3** — envoyée → (fin) : les courses sont terminées — [Envoyer la liste](envoyer-la-liste.md)

### Droits
| Rôle | Créer | Consulter | Modifier | Supprimer |
|---|---|---|---|---|
| Parent | oui | oui | oui | oui |

## Notifications
| Événement | Destinataires | Canal | Moment | Exigence |
|---|---|---|---|---|
| Liste envoyée | adolescents | push | à l'envoi | [Envoyer la liste](envoyer-la-liste.md) |
"""

DECISIONS = "---\ntype: Journal des décisions\ntitle: Décisions\n---\n## Questions ouvertes\nAucune.\n\n## Décisions\n- 2026-10-18 — human:x — décidé.\n"

RELECTURE = """---
type: Revue Relecture
title: Relecture
---
## Couverture des personas
| Persona | Besoin ou irritant | Couvert par |
|---|---|---|
| Les parents | Envoyer la liste | [Envoyer la liste](envoyer-la-liste.md) |
"""


def kb(tmp: str, **override: str) -> Path:
    root = Path(tmp)
    files = {"project/identity.md": IDENTITY, "personnas/les-parents.md": PERSONA,
             "cdc/envoyer-la-liste.md": EXIGENCE, "cdc/modele-metier.md": MODELE,
             "cdc/decisions.md": DECISIONS, "cdc/relecture.md": RELECTURE}
    files.update({k.replace("__", "/").replace("_", "-") + ".md": v for k, v in override.items()})
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    return root


def holes(root: Path) -> list[str]:
    return [h["trou"] for h in cdc.holes(cdc.load(root), root)]


class Completeness(unittest.TestCase):
    def test_complete_cdc_has_no_hole(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(holes(kb(d)), [])

    def test_objective_served_by_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            found = holes(kb(d, cdc__envoyer_la_liste=EXIGENCE.replace("objectifs: [O1]\n", "")))
            self.assertIn("aucune exigence ne sert cet objectif", found)
            self.assertIn("ne sert aucun objectif (`objectifs` vide)", found)

    def test_missing_priority_lot_and_trigger(self):
        with tempfile.TemporaryDirectory() as d:
            text = EXIGENCE.replace("priorite: indispensable\n", "").replace("lot: 1\n", "")
            text = text.replace("## Déclencheur\nLa liste est complète.\n", "")
            found = " | ".join(holes(kb(d, cdc__envoyer_la_liste=text)))
            for word in ("`priorite`", "`lot`", "`## Déclencheur`"):
                self.assertIn(word, found)

    def test_no_objective_at_all(self):
        with tempfile.TemporaryDirectory() as d:
            ident = IDENTITY.split("## Objectifs mesurables")[0] + "## Objectifs mesurables\nAucun encore défini.\n"
            self.assertTrue(any("aucun objectif mesurable" in h for h in holes(kb(d, project__identity=ident))))

    def test_state_without_exit_and_transition_without_exigence(self):
        with tempfile.TemporaryDirectory() as d:
            model = MODELE.replace("- **TR3** — envoyée → (fin) : les courses sont terminées — [Envoyer la liste](envoyer-la-liste.md)\n",
                                   "- **TR3** — envoyée → archivée : les courses sont terminées\n")
            found = holes(kb(d, cdc__modele_metier=model))
            self.assertIn("état « archivée » sans sortie (ni transition, ni `(fin)`)", found)
            self.assertIn("envoyée → archivée : aucune exigence ne porte cette transition", found)

    def test_undecided_right_and_notification(self):
        with tempfile.TemporaryDirectory() as d:
            model = MODELE.replace("| Parent | oui | oui | oui | oui |", "| Parent | oui | oui | ? | oui |")
            model = model.replace("| push | à l'envoi |", "| push | |")
            found = holes(kb(d, cdc__modele_metier=model))
            self.assertIn("droit non décidé pour « Parent »", found)
            self.assertIn("destinataire, canal ou moment non décidé", found)

    def test_open_question_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            dec = DECISIONS.replace("Aucune.", "- **Q1** — 2026-10-31 — qui valide ?")
            self.assertIn("2026-10-31 — qui valide ?", holes(kb(d, cdc__decisions=dec)))

    def test_uncovered_persona_need(self):
        with tempfile.TemporaryDirectory() as d:
            rel = RELECTURE + "| Les parents | Dupliquer une liste | Non couvert |\n"
            self.assertIn("non couvert : Dupliquer une liste", holes(kb(d, cdc__relecture=rel)))

    def test_every_persona_need_is_judged(self):
        with tempfile.TemporaryDirectory() as d:
            persona = PERSONA + "- Dupliquer une liste.\n## Pain points\n- Les SMS se perdent.\n"
            self.assertIn("3 besoin(s) et irritant(s), 1 ligne(s) dans la couverture",
                          holes(kb(d, personnas__les_parents=persona)))
            rel = RELECTURE + ("| [Les parents](../personnas/les-parents.md) | Dupliquer une liste | Écarté : lot 2 |\n"
                               "| Les parents | Irritant : les SMS se perdent | [Envoyer la liste](envoyer-la-liste.md) |\n")
            self.assertEqual(holes(kb(d, personnas__les_parents=persona, cdc__relecture=rel)), [])
            other = "---\ntype: Persona\ntitle: Les ados\n---\nUn adolescent du foyer.\n"
            found = holes(kb(d, personnas__les_ados=other))
            self.assertIn("persona sans `## Besoins` : rien à couvrir, rien de prouvé", found)

    def test_a_deduced_line_never_confirmed_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            text = EXIGENCE.replace("Une seule notification.", "Une seule notification.\n- **RG2** — Au plus 50 articles. [à confirmer]")
            self.assertIn("1 ligne(s) `[à confirmer]` : déduite(s), jamais confirmée(s) par l'utilisateur",
                          holes(kb(d, cdc__envoyer_la_liste=text)))

    def test_each_rule_and_error_case_has_its_id_and_numerote_never_moves_one(self):
        with tempfile.TemporaryDirectory() as d:
            text = EXIGENCE.replace("- **RG1** — Une seule notification.\n",
                                    "- Au plus 50 articles (51e refusé).\n  - détail de la règle\n- **RG4** — Une seule notification.\n"
                                    "- **RG4** — Envoi une fois.\n\n## Cas d'erreur\n- Liste vide → refus.\n- Aucun.\n")
            root = kb(d, cdc__envoyer_la_liste=text)
            found = holes(root)
            self.assertIn("2 règle(s) ou cas d'erreur sans identifiant `RGn`/`CEn` : `cdc numerote` les numérote", found)
            self.assertIn("identifiant en double : RG4", found)
            fiche = root / "cdc" / "envoyer-la-liste.md"
            self.assertEqual(cdc.numerote(fiche), 2)
            body = fiche.read_text(encoding="utf-8")
            self.assertIn("- **RG5** — Au plus 50 articles (51e refusé).\n  - détail de la règle\n- **RG4** — Une seule", body)
            self.assertIn("- **CE1** — Liste vide → refus.\n- Aucun.\n", body)
            self.assertEqual(cdc.numerote(fiche), 0)                       # written once
            self.assertEqual(cdc.rule_ids(body + "- **CE2** — retirée : doublon de CE1\n"), ["RG5", "RG4", "RG4", "CE1"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cdc.main(["numerote", str(root)]), 0)

    def test_a_dashboard_indicator_is_numbered_like_a_rule_and_says_all_it_needs(self):
        with tempfile.TemporaryDirectory() as d:
            text = EXIGENCE.replace("## Responsable", "## Indicateurs\n"
                                    "- Listes envoyées : nombre de listes passées à « envoyée » — source : Liste — "
                                    "période : 7 jours glissants — cible ou seuil : 5 — action : relancer le foyer\n"
                                    "- **IN4** — Articles oubliés : articles ajoutés après l'envoi — source : Liste\n\n"
                                    "## Responsable")
            root = kb(d, cdc__envoyer_la_liste=text)
            found = holes(root)
            self.assertIn("IN4 sans période, cible ou seuil, action "
                          "(`— source : … — période : … — cible ou seuil : … — action : …`)", found)
            self.assertIn("1 règle(s) ou cas d'erreur sans identifiant `RGn`/`CEn` : `cdc numerote` les numérote", found)
            fiche = root / "cdc" / "envoyer-la-liste.md"
            self.assertEqual(cdc.numerote(fiche), 1)
            self.assertIn("- **IN5** — Listes envoyées", fiche.read_text(encoding="utf-8"))
            self.assertEqual(cdc.rule_ids(fiche.read_text(encoding="utf-8")), ["RG1", "IN5", "IN4"])

    def test_obligation_serves_only_a_legal_security_or_basic_exigence(self):
        with tempfile.TemporaryDirectory() as d:
            legal = EXIGENCE.replace("tags: []\n", "").replace("title: Envoyer la liste", "title: Purge\ntags: [juridique]")
            found = holes(kb(d, cdc__purge=legal.replace("objectifs: [O1]", "objectifs: [obligation]")))
            self.assertEqual(found, [])
            found = holes(kb(d, cdc__purge=EXIGENCE.replace("objectifs: [O1]", "objectifs: [obligation]")))
            self.assertIn("`obligation` sans tag juridique, securite, rgpd ou fondamentaux : citer l'objectif servi", found)

    def test_process_needs_a_valid_espace(self):
        with tempfile.TemporaryDirectory() as d:
            bad = "`espace` absent ou invalide : front-office et/ou back-office, ou hors-application seul"
            for espace in ("", "espace: [boutique]\n", "espace: [hors-application, back-office]\n"):
                text = EXIGENCE.replace("espace: [front-office]\n", espace)
                self.assertIn(bad, holes(kb(d, cdc__envoyer_la_liste=text)), espace)
            text = EXIGENCE.replace("espace: [front-office]", "espace: [hors-application]")
            self.assertEqual(holes(kb(d, cdc__envoyer_la_liste=text)), [])

    def test_nfr_needs_target_and_measure(self):
        with tempfile.TemporaryDirectory() as d:
            nfr = "---\ntype: Exigence\ntitle: Perf\ntags: [nfr]\ndomaine: Q\npriorite: important\nlot: 1\n---\n## Exigence\n- 1 s.\n"
            self.assertIn("`## Mesure` absent ou vide : cible chiffrée et façon de la vérifier",
                          holes(kb(d, cdc__perf=nfr)))


def review(tmp: str, lines: str, route: str | None = None) -> list[str]:
    root = kb(tmp, cdc__relecture=RELECTURE.replace("## Couverture", f"## Anomalies\n{lines}\n## Couverture"))
    return cdc.revue(cdc.anomalies(cdc.load(root)), route)


class Diagrams(unittest.TestCase):
    """Each process is drawn and the user validated the diagram as it is; so is the infrastructure."""

    def test_a_process_without_a_validated_diagram_is_a_hole(self):
        bare = EXIGENCE.split("## Schéma du processus")[0] + "## Contraintes de sécurité\n- x\n"
        with tempfile.TemporaryDirectory() as t:
            self.assertIn("`## Schéma du processus` absent ou sans bloc ```mermaid", holes(kb(t, cdc__envoyer_la_liste=bare)))
        unstamped = "\n".join(x for x in EXIGENCE.splitlines() if not x.startswith("schema_valide")) + "\n"
        with tempfile.TemporaryDirectory() as t:
            root = kb(t, cdc__envoyer_la_liste=unstamped)
            self.assertIn("schéma pas encore validé par l'utilisateur (`cdc valide`)", holes(root))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cdc.main(["schemas", str(root)]), 1)
                self.assertEqual(cdc.main(["valide", str(root), "envoyer-la-liste"]), 0)
                self.assertEqual(cdc.main(["schemas", str(root)]), 0)
            self.assertEqual(holes(root), [])
            # changed after its validation: the user sees it again
            f = root / "cdc" / "envoyer-la-liste.md"
            f.write_text(f.read_text(encoding="utf-8").replace("Ados notifiés", "Ados prévenus"), encoding="utf-8")
            self.assertTrue(any("modifié depuis sa validation" in h for h in holes(root)))

    def test_valide_refuses_a_slug_or_a_diagram_that_is_not_there(self):
        with tempfile.TemporaryDirectory() as t:
            root = kb(t)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cdc.main(["valide", str(root), "inconnu", "infra"]), 1)
            self.assertIn("inconnu : aucune exigence", out.getvalue())
            self.assertIn("infra : aucune entrée `Infra`", out.getvalue())

    def test_the_database_is_drawn_with_its_formats_and_validated(self):
        """The user validates the tables, their relations and each column's type and format before any migration."""
        head = "---\ntype: Infra\ntitle: Schéma de la base\n---\n## Schéma de la base de données\n```mermaid\nerDiagram\n"
        bare = head + "  famille ||--o{ ado : compte\n  famille {\n    uuid id PK\n  }\n  ado {\n    uuid id PK \"v4\"\n  }\n```\n"
        full = (head + "  famille ||--o{ ado : compte\n  famille {\n    uuid id PK \"v4, généré\"\n"
                "    varchar(254) email UK \"e-mail, minuscules\"\n  }\n  ado {\n    uuid id PK \"v4\"\n"
                "    uuid famille_id FK \"famille.id, non nul\"\n    date naissance \"AAAA-MM-JJ\"\n  }\n```\n")
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "kb"
            (root / "infra").mkdir(parents=True)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cdc.main(["schemas", str(root), "--db"]), 1)  # nothing drawn yet
                f = root / "infra" / "schema-base-de-donnees.md"
                f.write_text(bare, encoding="utf-8")
                self.assertEqual(cdc.main(["valide", str(root), "db"]), 1)  # a column without its format
            self.assertIn("`famille` : colonne sans type ou sans format", out.getvalue())
            self.assertNotIn("schema_valide", f.read_text(encoding="utf-8"))
            f.write_text(full, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cdc.main(["schemas", str(root), "--db", "--apercu"]), 1)  # drawn, not validated
                self.assertIn("Schéma de la base de données", (root.parent / "schemas.html").read_text(encoding="utf-8"))
                self.assertEqual(cdc.main(["valide", str(root), "db"]), 0)
                self.assertEqual(cdc.main(["schemas", str(root), "--db"]), 0)
            # a column changed after its validation: the user sees it again
            f.write_text(f.read_text(encoding="utf-8").replace("AAAA-MM-JJ", "JJ/MM/AAAA"), encoding="utf-8")
            self.assertTrue(any("modifié depuis sa validation" in g for _, g in cdc.db_schema_gaps(root)))

    def test_the_database_diagram_needs_relations_between_its_tables(self):
        two = ("```mermaid\nerDiagram\n  a {\n    int id PK \"auto\"\n  }\n  b {\n    int id PK \"auto\"\n  }\n```")
        self.assertEqual(cdc.db_gaps(two), ["aucune relation entre les tables"])
        # Mermaid draws no type with a comma: the precision goes in the format
        comma = "```mermaid\nerDiagram\n  a {\n    numeric(10,2) prix \"euros\"\n  }\n```"
        self.assertIn("colonne sans type ou sans format", cdc.db_gaps(comma)[0])
        self.assertEqual(cdc.db_gaps("```mermaid\nflowchart LR\n  a --> b\n```"),
                         ["le schéma de la base n'est pas un `erDiagram` (tables, colonnes, relations)"])

    def test_nfr_needs_no_diagram_and_the_switch_turns_the_check_off(self):
        nfr = ("---\ntype: Exigence\ntitle: Vite\ntags: [nfr]\npriorite: important\nlot: 1\ndomaine: x\n---\n"
               "## Exigence\n- 1 s\n\n## Mesure\n- test\n")
        with tempfile.TemporaryDirectory() as t:
            self.assertFalse(any("Schéma" in h for h in holes(kb(t, cdc__vite=nfr))))
        bare = EXIGENCE.split("## Schéma du processus")[0]
        with tempfile.TemporaryDirectory() as t, unittest.mock.patch.dict(os.environ, {"HOSA_SCHEMAS": "0"}):
            self.assertEqual(holes(kb(t, cdc__envoyer_la_liste=bare)), [])

    def test_the_infrastructure_is_drawn_validated_and_put_in_the_document(self):
        infra = ("---\ntype: Infra\ntitle: Environnement Docker\n---\n## Services\n- app\n\n## Schéma de l'infrastructure\n"
                 "```mermaid\nflowchart LR\n  U[Navigateur] --> A[app :8000] --> D[(postgres 16)]\n```\n")
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "kb"
            kb(str(root))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cdc.main(["schemas", str(root), "--infra"]), 1)  # nothing drawn yet
                (root / "infra").mkdir()
                (root / "infra" / "environnement-docker.md").write_text(infra, encoding="utf-8")
                self.assertEqual(cdc.main(["schemas", str(root), "--infra", "--apercu"]), 1)  # drawn, not validated
                self.assertTrue((root.parent / "schemas.html").is_file())
                self.assertEqual(cdc.main(["valide", str(root), "infra"]), 0)
                self.assertEqual(cdc.main(["schemas", str(root), "--infra"]), 0)
                self.assertEqual(cdc.main(["assemble", str(root)]), 0)
            doc = (root / "project" / "cahier-des-charges.md").read_text(encoding="utf-8")
            annex = doc.split("### D. Schéma de l'infrastructure")[1]
            self.assertIn("validé le", annex)
            self.assertIn("D[(postgres 16)]", annex)
            self.assertIn("schéma validé le 2026-11-18", doc)  # the process fiche says it too
            self.assertIn("C[Ados notifiés]", doc)


class Review(unittest.TestCase):
    def test_only_an_open_bloquante_holds(self):
        with tempfile.TemporaryDirectory() as d:
            lines = ("- A1 [p1, bloquante, texte] — [x](x.md) § Règles — flou — → redaction — corrigée\n"
                     "- A2 [p1, mineure, texte] — [x](x.md) § Glossaire — synonyme — → redaction — ouverte\n")
            self.assertEqual(review(d, lines), [])
            lines += "- A3 [p1, bloquante, texte] — [y](y.md) — besoin — → interview — ouverte\n"
            self.assertEqual(review(d, lines), ["anomalies bloquantes encore `ouverte` : A3"])
            self.assertEqual(review(d, lines, "redaction"), [])
            self.assertEqual(review(d, lines, "interview"), ["anomalies bloquantes → interview encore `ouverte` : A3"])

    def test_an_open_anomaly_needs_its_tag_a_closed_untagged_one_is_history(self):
        with tempfile.TemporaryDirectory() as d:
            lines = ("- A1 — [x](x.md) § Règles — flou — → redaction — corrigée\n"
                     "- A2 — [x](x.md) § Cas — manque — → redaction — ouverte\n"
                     "- A3 [p1, grave, texte] — [x](x.md) § Cas — manque — → redaction — corrigée\n")
            found = review(d, lines)
            self.assertEqual(found[0], "A2 : sans `[passe, gravité, origine]` valide (ex. `[p1, bloquante, texte]`)")
            self.assertTrue(found[1].startswith("A3 : sans"))
            self.assertEqual(found[2], "anomalies bloquantes encore `ouverte` : A2")  # untagged and open: held as bloquante

    def test_a_mineure_goes_to_redaction_and_a_repass_reads_only_the_fixes(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIn("une `mineure` va → redaction",
                          review(d, "- A1 [p1, mineure, texte] — [x](x.md) — choix — → utilisateur — ouverte\n")[0])
            self.assertIn("passe de reprise p2",
                          review(d, "- A1 [p2, mineure, texte] — [x](x.md) — virgule — → redaction — ouverte\n")[0])
            self.assertEqual(review(d, "- A1 [p2, mineure, correction] — [x](x.md) — copie — → redaction — ouverte\n"
                                       "- A2 [c1, mineure, texte] — [x](x.md) — mot — → redaction — ouverte\n"), [])

    def test_mesure_counts_by_pass_gravity_and_origin(self):
        with tempfile.TemporaryDirectory() as d:
            lines = ("- A1 — [x](x.md) — vieux — → redaction — corrigée\n"
                     "- A2 [p1, bloquante, texte] — [x](x.md) — a — → redaction — corrigée\n"
                     "- A3 [p2, mineure, correction] — [x](x.md) — b — → redaction — ouverte\n"
                     "- A4 [p2, bloquante, regle-hosa] — [x](x.md) — c — → utilisateur — ouverte\n")
            root = kb(d, cdc__relecture=RELECTURE.replace("## Couverture", f"## Anomalies\n{lines}\n## Couverture"))
            table = cdc.mesure(cdc.anomalies(cdc.load(root))).splitlines()
            self.assertEqual(table[2], "| p1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 |")
            self.assertEqual(table[3], "| p2 | 2 | 1 | 1 | 0 | 1 | 1 | 2 |")
            self.assertEqual(table[4], "| non classées | 1 | 0 | 0 | 0 | 0 | 0 | 0 |")
            self.assertEqual(table[5], "| **Total** | 4 | 2 | 1 | 1 | 1 | 1 | 2 |")


class Assemble(unittest.TestCase):
    def test_document_follows_the_plan_and_links_work_from_project(self):
        with tempfile.TemporaryDirectory() as d:
            root = kb(d)
            data = cdc.load(root)
            doc = cdc.assemble(data, root, cdc.holes(data, root))
            for heading in ("## 1. Contexte et enjeux", "## 2. Objectifs et indicateurs", "## 5. Processus métier",
                            "## 6. Objets métier", "## 11. Décisions et questions ouvertes", "## 12. Contrôle de complétude"):
                self.assertIn(heading, doc)
            self.assertIn("[Les parents](../personnas/les-parents.md)", doc)
            self.assertIn("[Envoyer la liste](../cdc/envoyer-la-liste.md)", doc)
            self.assertNotIn("Rôle vérifié côté serveur", doc)  # technical detail stays in the fiche
            self.assertIn("status: stable", doc)

    def test_holes_keep_the_document_draft(self):
        with tempfile.TemporaryDirectory() as d:
            root = kb(d, cdc__decisions=DECISIONS.replace("Aucune.", "- **Q1** — à trancher"))
            data = cdc.load(root)
            doc = cdc.assemble(data, root, cdc.holes(data, root))
            self.assertIn("status: draft", doc)
            self.assertIn("**1 trou(s).**", doc)


if __name__ == "__main__":
    unittest.main()


class Pending(unittest.TestCase):
    """rieki: « Repli de taille » signed with « mesure à prendre ; aucun chiffre n'est fixé avant », and a
    « Question ouverte (non décidée) » inside a rule — both became criteria nobody could test."""

    def test_a_line_waiting_for_a_choice_is_a_hole(self):
        for words in ("Question ouverte : la durée minimale.", "Le seuil reste à définir.",
                      "Le temps cible : mesure à prendre ; aucun chiffre n'est fixé avant."):
            with tempfile.TemporaryDirectory() as d:
                found = holes(kb(d, cdc__envoyer_la_liste=EXIGENCE.replace("- **RG1** — Une seule notification.",
                                                                            f"- **RG1** — {words}")))
                self.assertEqual(len(found), 1, words)
                self.assertIn("décider (`decisions.md`)", found[0])

    def test_a_measure_is_numbered_then_taken_by_its_stage(self):
        rule = "- **RG1** — Si le calcul dépasse le temps cible, Rieki propose moins. [à mesurer : temps du modèle — étape stack]"
        with tempfile.TemporaryDirectory() as d:
            root = kb(d, cdc__envoyer_la_liste=EXIGENCE.replace("- **RG1** — Une seule notification.", rule))
            self.assertEqual(holes(root), ["mesure sans identifiant : `cdc numerote` lui donne son `Mn`"])
            self.assertEqual(cdc.numerote_mesures(root), 1)
            self.assertEqual(holes(root), [])
            self.assertEqual([(m["id"], m["etape"]) for m in cdc.measures(root)], [("M1", "stack")])
            self.assertEqual(cdc.rule_measures((root / "cdc" / "envoyer-la-liste.md").read_text(encoding="utf-8")),
                             {"RG1": ["M1"]})
            self.assertEqual(cdc.measured(root), set())
            (root / "cdc" / "decisions.md").write_text(DECISIONS + "- 2026-11-18 — human:x — M1 : 42 s sur le poste.\n",
                                                       encoding="utf-8")
            self.assertEqual(cdc.measured(root), {"M1"})


class Transitions(unittest.TestCase):
    def test_each_transition_has_an_id_that_never_moves(self):
        with tempfile.TemporaryDirectory() as d:
            root = kb(d, cdc__modele_metier=MODELE.replace("**TR2** — ", "").replace("**TR3** — ", "**TR7** — "))
            self.assertEqual(holes(root), ["1 transition(s) sans identifiant `TRn` : `cdc numerote` les numérote"])
            self.assertEqual(cdc.numerote_transitions(root), 1)
            self.assertEqual(holes(root), [])
            got = cdc.model_transitions((root / "cdc" / "modele-metier.md").read_text(encoding="utf-8"))
            self.assertEqual([(t["id"], t["de"], t["vers"]) for t in got],
                             [("TR1", "(début)", "en préparation"), ("TR8", "en préparation", "envoyée"),
                              ("TR7", "envoyée", "(fin)")])
