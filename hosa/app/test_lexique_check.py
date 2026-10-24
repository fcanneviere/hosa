"""lexique_check.py: a folder line keeps only its path; skipped folders and minified files are never scanned."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "interface" / "scripts" / "lexique_check.py"
spec = importlib.util.spec_from_file_location("lexique_check", SCRIPT)
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)

LEXIQUE = """## Termes
| Terme | Désigne | Où | Synonymes interdits |
|---|---|---|---|
| Liste | la liste de courses | partout | Panier |

## Dossiers analysés
- `core/templates/` — les gabarits
- core/static # scripts
"""


class LexiqueCheck(unittest.TestCase):
    def test_paths_and_skips(self):
        root = Path(tempfile.mkdtemp())
        files = {".hosa/kb/interface/lexique.md": LEXIQUE,
                 "core/templates/a.html": "<h1>Mon panier</h1>",
                 "core/static/app.min.js": "panier",
                 "core/static/docs/x.md": "panier",
                 "core/static/b.js": "liste"}
        for name, text in files.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(text, encoding="utf-8")
        terms, folders, _ = lc.lexicon(root / ".hosa" / "kb")
        self.assertEqual(folders, ["core/templates/", "core/static"])
        found = lc.scan(root, folders, terms)
        self.assertEqual(len(found), 1)
        self.assertIn("a.html:1", found[0])


if __name__ == "__main__":
    unittest.main()
