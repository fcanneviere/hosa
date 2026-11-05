"""cdc.py assembles the cahier des charges and finds every empty cell of its completeness matrices."""
import importlib.util
import tempfile
import unittest
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
- Une seule notification.

## Responsable
Parent.

## Besoin(s) persona répondu(s)
- [Les parents](../personnas/les-parents.md) : envoyer la liste.

## Contraintes de sécurité
- Rôle vérifié côté serveur.
"""

MODELE = """---
type: Modèle Métier
title: Modèle métier
---
## Liste
### Cycle de vie
- (début) → en préparation : un parent crée la liste — [Envoyer la liste](envoyer-la-liste.md)
- en préparation → envoyée : un parent l'envoie — [Envoyer la liste](envoyer-la-liste.md)
- envoyée → (fin) : les courses sont terminées — [Envoyer la liste](envoyer-la-liste.md)

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
            model = MODELE.replace("- envoyée → (fin) : les courses sont terminées — [Envoyer la liste](envoyer-la-liste.md)\n",
                                   "- envoyée → archivée : les courses sont terminées\n")
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
