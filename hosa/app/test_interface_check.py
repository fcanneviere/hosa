"""interface_check.py: every functional exigence has its screens — except a process with no screen."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "interface" / "scripts" / "interface_check.py"
spec = importlib.util.spec_from_file_location("interface_check", SCRIPT)
ic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ic)

NAV = """---
type: Plan de navigation
---
## Écrans
| Écran | Route | Rôle | Exigences | Accès depuis | Espace |
|---|---|---|---|---|---|
| Listes | /listes | Parent | [Envoyer](../cdc/envoyer.md) | Menu | front-office |
| Foyers | /admin | Admin | — | Menu | back-office |
"""


def exigence(espace: str) -> str:
    return f"---\ntype: Exigence\nstatus: stable\nespace: {espace}\n---\n"


def screen_gaps(cdc: dict[str, str]) -> list[str]:
    with tempfile.TemporaryDirectory() as d:
        kb = Path(d)
        (kb / "interface").mkdir()
        (kb / "interface" / "navigation.md").write_text(NAV, encoding="utf-8")
        (kb / "cdc").mkdir()
        for slug, text in cdc.items():
            (kb / "cdc" / f"{slug}.md").write_text(text, encoding="utf-8")
        return [g for g in ic.gaps(kb) if g.startswith("exigence")]


class Screens(unittest.TestCase):
    def test_a_functional_exigence_needs_its_screen(self):
        self.assertEqual(screen_gaps({"envoyer": exigence("[front-office]")}), [])
        self.assertEqual(screen_gaps({"purge": exigence("[back-office]")}), ["exigence `purge` servie par aucun écran"])

    def test_a_process_with_no_screen_needs_none(self):
        self.assertEqual(screen_gaps({"purge": exigence("[hors-application]")}), [])


BO_NAV = """---
type: Plan de navigation
---
## Écrans
| Écran | Route | Rôle | Exigences | Accès depuis | Espace |
|---|---|---|---|---|---|
| Tableau de bord | /admin | Gérant | [Pilotage](../cdc/pilotage.md) | connexion | back-office |
| Réservations | /admin/reservations | Gérant | — | menu | back-office |
| Réservation | /admin/reservations/:id | Gérant | — | Réservations | back-office |
{gestion}{tableaux}"""

MODELE = "---\ntype: Modèle Métier\n---\n## Réservation\n### Droits\n## Tarif\n### Droits\n## Notifications\n"
PILOTAGE = ("---\ntype: Exigence\nstatus: stable\nespace: [back-office]\n---\n## Indicateurs\n"
            "- **IN1** — Places vendues : … — source : Réservation\n- **IN2** — À payer : …\n"
            "- **IN3** — retiré : plus suivi\n")


def kb_gaps(gestion: str = "", tableaux: str = "", modele: str = MODELE) -> list[str]:
    with tempfile.TemporaryDirectory() as d:
        kb = Path(d)
        (kb / "interface").mkdir()
        (kb / "interface" / "navigation.md").write_text(BO_NAV.format(gestion=gestion, tableaux=tableaux), encoding="utf-8")
        (kb / "cdc").mkdir()
        (kb / "cdc" / "pilotage.md").write_text(PILOTAGE, encoding="utf-8")
        if modele:
            (kb / "cdc" / "modele-metier.md").write_text(modele, encoding="utf-8")
        return [g for g in ic.gaps(kb) if not g.startswith("fondamental") and "Fondamentaux" not in g]


class BackOfficeAndDashboards(unittest.TestCase):
    GESTION = ("\n## Gestion back office\n| Objet | Liste | Fiche | Historique | Actions |\n|---|---|---|---|---|\n"
               "| Réservation | Réservations | [Réservation](x) | Réservation | annuler, marquer payée |\n"
               "| Tarif | Non applicable : 3 tarifs fixes | Non applicable : dans Paramètres | Non applicable : aucun | modifier |\n")
    TABLEAUX = ("\n## Tableaux de bord\n| Indicateur | Exigence | Écran | Détail |\n|---|---|---|---|\n"
                "| IN1 Places vendues | [Pilotage](../cdc/pilotage.md) | Tableau de bord | Réservations |\n"
                "| IN2 À payer | [Pilotage](../cdc/pilotage.md) | Tableau de bord | /admin/reservations?etat=a-payer |\n")

    def test_a_back_office_only_application_needs_no_front_office(self):
        self.assertEqual(kb_gaps(self.GESTION, self.TABLEAUX), [])

    def test_every_object_of_the_business_model_has_its_back_office(self):
        self.assertIn("section `## Gestion back office` absente : une ligne par objet du modèle métier (Réservation, Tarif)",
                      kb_gaps("", self.TABLEAUX))
        gaps = kb_gaps(self.GESTION.replace("| Tarif |", "| Tarifs |").replace("| Réservations | [Réservation](x)",
                                                                              "| Réservations | Fiche résa"), self.TABLEAUX)
        self.assertIn("objet « Tarif » sans ligne dans `## Gestion back office` (liste, fiche, historique, actions)", gaps)
        self.assertIn("objet « Réservation » : fiche « Fiche résa » absent de `## Écrans`", gaps)
        self.assertEqual(kb_gaps("", self.TABLEAUX, modele=""), [])  # no business model yet: nothing to cover

    def test_every_indicator_is_on_a_screen_with_its_detail(self):
        self.assertIn("section `## Tableaux de bord` absente : 2 indicateur(s) à placer", kb_gaps(self.GESTION))
        gaps = kb_gaps(self.GESTION, self.TABLEAUX.replace("| /admin/reservations?etat=a-payer |", "| |")
                       .replace("| IN1 Places vendues |", "| IN9 |"))
        self.assertIn("indicateur IN1 de `pilotage` placé sur aucun écran (`## Tableaux de bord`)", gaps)
        self.assertTrue(any(g.startswith("indicateur IN2 de `pilotage` : pas d'écran de détail") for g in gaps), gaps)
        self.assertFalse(any("IN3" in g for g in gaps))  # a retired indicator needs no screen


if __name__ == "__main__":
    unittest.main()
