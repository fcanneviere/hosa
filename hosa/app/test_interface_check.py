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


if __name__ == "__main__":
    unittest.main()
