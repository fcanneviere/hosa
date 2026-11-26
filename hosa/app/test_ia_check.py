"""The AI stages' proofs (`ia_check.py`) and how the progress plan applies them."""
import contextlib
import io
import os
import re
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "skills" / "ia" / "scripts"), str(ROOT / "skills" / "status" / "scripts")]
import avancement as av  # noqa: E402
import ia_check as ia  # noqa: E402

CADRAGE = """---
type: Cadrage IA
---
## Fonctions IA
- **IA1** — prévoit les ventes — [prévision](prevision.md)
  - Forme : appel simple
  - Limites : 1 lancement à la fois
  - Référence sans IA : même semaine l'an dernier
  - Métrique : part des séries mieux prévues
  - Seuil : 70 % des séries
  - Durée max : 900 s par lot
  - Exécution : local
  - Données : ventes hebdomadaires ; rien ne sort
  - Erreur du modèle : garder la référence
## Contraintes
- Machine cible : poste Windows sans GPU
- Budget : 0 €
## Choix validés
- 2026-01-01 — human:fabien — seuil 70 %, local seulement
## Révisions
- 2026-01-01T10:00Z — création
"""


def result(verdict="PASS", at="2026-01-02T10:00Z", print_="000000000000", place="local", code=0):
    return (f"- {at} — IA1 — {verdict} — modèle : m@abc — exécution : {place} — mesuré : 74 % — référence : 50 % — "
            f"durée : 212 s — mémoire : 3 Go — coût : 0 € — commande : `python eval/ia1.py` — exit {code} — "
            f"empreinte : {print_}")


SPEC = "- **IA1**\n  - Sortie : trois quantiles\n  - Suivi : durée de chaque lot\n"
NEED = "- torch — version : 2.4.1 — calcul — vérification : `python -c 'import torch'` — exit 0 — 2026-01-02"


def essai(*lines, spec=SPEC, need=NEED):
    return (f"---\ntype: Essai IA\n---\n## Spécification technique\n{spec}## Besoins d'installation\n{need}\n"
            "## Données d'essai\n- Source : ventes.csv, 2 ans\n## Résultats\n"
            + "\n".join(lines) + "\n## Fichiers suivis\n- IA1 — eval/ia1.py, src/moteur/**\n")


RAG = CADRAGE.replace("Forme : appel simple", """Forme : RAG, MCP
  - Corpus : 300 documents
  - Mise à jour : chaque nuit ; une source supprimée disparaît
  - Droits d'accès : par service
  - Sources citées : oui
  - Seuil de recherche : 90 % des questions
  - Rôle MCP : client
  - Serveurs : fichiers
  - Outils : lire
  - Authentification : aucune — stdio local
  - Actions confirmées : aucune — lecture seule""")
RAG_SPEC = SPEC + "".join(f"  - {f} : x\n" for f in ("Découpage", "Embeddings", "Base vectorielle", "Filtre d'accès",
                                                     "Transport", "Versions épinglées", "Droits des outils"))


def project(**files) -> Path:
    """A project with its KB at `<root>/.hosa/kb`; keys: `cadrage`, `essai`. Returns the KB."""
    root = Path(tempfile.mkdtemp())
    kb = root / ".hosa" / "kb"
    for rel, text in (("cdc/ia.md", files.get("cadrage")), ("stack/essai-ia.md", files.get("essai")),
                      ("cdc/prevision.md", "---\ntype: Exigence\n---\n")):
        if text is not None:
            (kb / rel).parent.mkdir(parents=True, exist_ok=True)
            (kb / rel).write_text(text, encoding="utf-8")
    (root / "eval").mkdir()
    (root / "eval" / "ia1.py").write_text("print(1)\n", encoding="utf-8")
    return kb


def plan(kb, *argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = av.main([str(kb), *argv])
    return code, out.getvalue()


class Cadrage(unittest.TestCase):
    def test_a_complete_framing_passes(self):
        self.assertEqual(ia.cadrage_gaps(project(cadrage=CADRAGE)), [])

    def test_a_function_without_baseline_threshold_or_exigence_is_refused(self):
        bad = CADRAGE.replace("  - Référence sans IA : même semaine l'an dernier\n", "") \
            .replace("70 % des séries", "bon").replace("(prevision.md)", "(absente.md)").replace("- Budget : 0 €\n", "")
        gaps = "\n".join(ia.cadrage_gaps(project(cadrage=bad)))
        for word in ("Référence sans IA", "`Seuil :` sans chiffre", "aucune exigence", "Budget"):
            self.assertIn(word, gaps)

    def test_a_threshold_may_wait_for_its_measure(self):
        waiting = CADRAGE.replace("900 s par lot", "[à mesurer M1 : durée du lot — étape essai-ia]")
        self.assertEqual(ia.cadrage_gaps(project(cadrage=waiting)), [])

    def test_the_users_choices_stay_written(self):
        gone = CADRAGE.replace("- 2026-01-01 — human:fabien — seuil 70 %, local seulement\n", "")
        self.assertIn("`## Choix validés` vide", "\n".join(ia.cadrage_gaps(project(cadrage=gone))))

    def test_no_file_says_to_skip(self):
        self.assertIn("skip cadrage-ia", ia.cadrage_gaps(project())[0])


class Forms(unittest.TestCase):
    def test_each_form_asks_its_fields(self):
        self.assertEqual(ia.cadrage_gaps(project(cadrage=RAG)), [])
        for form, field in (("RAG", "Seuil de recherche"), ("MCP", "Actions confirmées"), ("agent", "Bornes")):
            bare = CADRAGE.replace("appel simple", form)
            self.assertIn(f"`{field} :`", "\n".join(ia.cadrage_gaps(project(cadrage=bare))), form)
        unknown = CADRAGE.replace("appel simple", "magie")
        self.assertIn("inconnue", "\n".join(ia.cadrage_gaps(project(cadrage=unknown))))

    def test_each_form_asks_its_specification_and_a_rag_its_retrieval_measure(self):
        gaps = "\n".join(ia.spec_gaps(project(cadrage=RAG, essai=essai())))
        for field in ("Base vectorielle", "Filtre d'accès", "Transport", "Droits des outils"):
            self.assertIn(f"`{field} :`", gaps)
        line = result()
        self.assertIn("`recherche :`", "\n".join(ia.essai_gaps(project(cadrage=RAG, essai=essai(line, spec=RAG_SPEC)))))
        line = line.replace("— référence", "— recherche : 93 % — référence")
        self.assertEqual(ia.essai_gaps(project(cadrage=RAG, essai=essai(line, spec=RAG_SPEC))), [])


class Needs(unittest.TestCase):
    def gaps(self, need):
        return "\n".join(ia.needs_gaps(project(cadrage=CADRAGE, essai=essai(need=need))))

    def test_each_need_is_pinned_and_verified(self):
        self.assertEqual(self.gaps(NEED), "")
        self.assertEqual(self.gaps("- aucun — la bibliothèque est déjà dans l'image"), "")
        self.assertIn("pas vérifié", self.gaps(NEED.replace(" — exit 0", "")))
        self.assertIn("pas vérifié", self.gaps(NEED.replace("exit 0", "exit 1")))
        self.assertIn("épinglée", self.gaps(NEED.replace("2.4.1", "latest")))
        self.assertIn("vérification", self.gaps("- qdrant — version : 1.9.0 — base vectorielle"))
        self.assertIn("vide", self.gaps(""))

    def test_a_secret_value_is_refused_and_its_check_is_not_one(self):
        key = "- clé — version : sans objet — appel — vérification : `test -n \"$OPENAI_API_KEY\"` — exit 0"
        self.assertEqual(self.gaps(key), "")
        for leak in ("OPENAI_API_KEY=abcdefgh12345678", "sk-proj-abcdefgh12345678abcd"):
            self.assertIn("secret", self.gaps(key + " — " + leak), leak)

    def test_a_need_added_later_stops_the_replay(self):
        kb = project(cadrage=CADRAGE, essai=essai(result(), need=NEED + "\n- qdrant — version : 1.9.0 — base"))
        self.assertIn("qdrant", "\n".join(ia.rejeu_gaps(kb, kb.parent.parent)))

    def test_the_trial_installs_before_it_measures(self):
        kb = project(cadrage=CADRAGE, essai=essai(need=NEED.replace(" — exit 0", "")))
        with contextlib.redirect_stdout(io.StringIO()):
            for s in [s for _, ss in av.PIPELINES for s in ss]:
                if s == "essai-ia":
                    break
                av.main([str(kb), "done", s, "--force"])
        sortie = ["--sortie", "kb/stack/essai-ia.md"]
        self.assertEqual(plan(kb, "start", "essai-ia")[0], 0)
        self.assertEqual(plan(kb, "task", "add", "essai-ia", "besoins", "--agent", "hosa-ia")[0], 0)
        self.assertEqual(plan(kb, "task", "add", "essai-ia", "installation", "--agent", "hosa-infra")[0], 1)
        self.assertEqual(plan(kb, "task", "done", "essai-ia", "besoins", *sortie)[0], 0)
        self.assertEqual(plan(kb, "task", "add", "essai-ia", "installation", "--agent", "hosa-infra")[0], 0)
        self.assertEqual(plan(kb, "task", "add", "essai-ia", "essai", "--agent", "hosa-ia")[0], 1)
        code, out = plan(kb, "task", "done", "essai-ia", "installation", *sortie)
        self.assertEqual(code, 1)
        self.assertIn("besoins-ia", out)


class Essai(unittest.TestCase):
    def gaps(self, *lines, cadrage=CADRAGE):
        return "\n".join(ia.essai_gaps(project(cadrage=cadrage, essai=essai(*lines))))

    def test_a_pass_with_its_measures_passes(self):
        self.assertEqual(self.gaps(result()), "")

    def test_no_ai_function_needs_no_trial(self):
        self.assertEqual(ia.essai_gaps(project()), [])

    def test_the_last_line_decides(self):
        self.assertIn("dernier résultat FAIL", self.gaps(result(), result("FAIL", code=1)))
        self.assertEqual(self.gaps(result("FAIL", code=1), result()), "")

    def test_a_pass_is_the_scripts_verdict_with_every_measure(self):
        self.assertIn("exit 0", self.gaps(result(code=1)))
        self.assertIn("`mémoire :`", self.gaps(result().replace(" — mémoire : 3 Go", "")))

    def test_a_result_older_than_the_framing_proves_nothing(self):
        self.assertIn("antérieur au cadrage", self.gaps(result(at="2025-12-31T10:00Z")))

    def test_the_place_framed_is_the_place_measured(self):
        self.assertIn("cadré `local`", self.gaps(result(place="cloud")))
        both = CADRAGE.replace("Exécution : local", "Exécution : à comparer")
        self.assertIn("à comparer", self.gaps(result(), cadrage=both))
        self.assertEqual(self.gaps(result(place="cloud"), result(), cadrage=both), "")


class Rejeu(unittest.TestCase):
    def test_a_changed_tracked_file_asks_for_a_new_run(self):
        kb = project(cadrage=CADRAGE, essai=essai(result()))
        root = kb.parent.parent
        now = ia.fingerprint(root, ia.files_of(root, ["eval/ia1.py", "src/moteur/**"]))
        (kb / "stack" / "essai-ia.md").write_text(essai(result(print_=now)), encoding="utf-8")
        self.assertEqual(ia.rejeu_gaps(kb, root), [])
        (root / "eval" / "ia1.py").write_bytes(b"print(1)\r\n")  # line endings alone change nothing
        self.assertEqual(ia.rejeu_gaps(kb, root), [])
        (root / "src" / "moteur" / "sous").mkdir(parents=True)
        (root / "src" / "moteur" / "sous" / "m.py").write_text("REVISION = 'b'\n", encoding="utf-8")
        self.assertIn("ont changé", ia.rejeu_gaps(kb, root)[0])

    def test_no_tracked_file_in_the_checkout_is_a_gap(self):
        kb = project(cadrage=CADRAGE, essai=essai(result()))
        (kb.parent.parent / "eval" / "ia1.py").unlink()
        self.assertIn("aucun fichier suivi", ia.rejeu_gaps(kb, kb.parent.parent)[0])

    def test_patterns_never_leave_the_project(self):
        root = project().parent.parent
        self.assertEqual(ia.files_of(root, ["../**", "/etc/*", "C:/Windows/*"]), [])

    def test_the_switch(self):
        kb = project(cadrage=CADRAGE)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ia.main([str(kb), "essai"]), 1)
            with unittest.mock.patch.dict(os.environ, {"HOSA_IA": "0"}):
                self.assertEqual(ia.main([str(kb), "essai"]), 0)


class Plan(unittest.TestCase):
    def test_done_refuses_without_the_proof(self):
        kb = project(cadrage=CADRAGE, essai=essai(result("FAIL", code=1)))
        self.assertIn("dernier résultat FAIL", "\n".join(av.check(kb, "essai-ia", None)))
        self.assertEqual(av.check(kb, "cadrage-ia", None), [])
        self.assertTrue(av.check(project(), "cadrage-ia", None))

    def test_a_loop_asks_each_stage_for_a_line_dated_after_it(self):
        kb = project(cadrage=CADRAGE, essai=essai(result()))
        with contextlib.redirect_stdout(io.StringIO()):
            for s in [s for _, ss in av.PIPELINES for s in ss]:
                av.main([str(kb), "done", s, "--force"])
                if s == "infra":
                    break
        self.assertEqual(plan(kb, "back", "essai-ia", "cadrage-ia", "--cause", "IA1", "--detail", "seuil")[0], 0)
        self.assertIn("datée après la réouverture", "\n".join(av.check(kb, "cadrage-ia", None)))
        later = "- 2999-01-01T10:00Z — seuil à 60 %\n"
        (kb / "cdc" / "ia.md").write_text(CADRAGE + later, encoding="utf-8")
        self.assertEqual(av.check(kb, "cadrage-ia", None), [])
        self.assertTrue(av.check(kb, "essai-ia", None))
        (kb / "stack" / "essai-ia.md").write_text(essai(result(), result(at="2999-01-02T10:00Z")), encoding="utf-8")
        self.assertEqual(av.check(kb, "essai-ia", None), [])

    def test_a_loop_from_qa_reopens_the_trial_only(self):
        kb = project(cadrage=CADRAGE, essai=essai(result()))
        with contextlib.redirect_stdout(io.StringIO()):
            for s in [s for _, ss in av.PIPELINES for s in ss]:
                av.main([str(kb), "done", s, "--force"])
        (kb / "sprints").mkdir()
        (kb / "sprints" / "s1.md").write_text("---\ntype: Sprint\n---\n## Tickets\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            for s in av.SPRINT[:av.SPRINT.index("qa")]:
                av.main([str(kb), "done", s, "--sprint", "s1", "--force"])
        code, out = plan(kb, "back", "qa", "essai-ia", "--sprint", "s1", "--cause", "IA1", "--detail", "62 %")
        self.assertEqual(code, 0, out)
        status = {r[0]: r[1] for rows in av.load(kb / "project" / "avancement.md")[0].values() for r in rows}
        self.assertEqual((status["essai-ia"], status["cadrage-ia"], status["stack"]), (av.TODO, av.DONE, av.DONE))
        self.assertIn("datée après la réouverture", "\n".join(av.check(kb, "essai-ia", None)))

    def test_qa_and_livraison_replay_on_the_sprints_checkout(self):
        kb = project(cadrage=CADRAGE, essai=essai(result()))
        for stage in ("qa", "livraison"):
            self.assertIn("ont changé", "\n".join(av.ai_replay(kb, "---\ntype: Sprint\n---\n")), stage)
        (kb / "sprints").mkdir()
        (kb / "sprints" / "s1.md").write_text("---\ntype: Sprint\n---\n## Tickets\n", encoding="utf-8")
        for stage in ("qa", "livraison"):
            self.assertIn("ia_check", "\n".join(av.proofs(kb, stage, "s1")), stage)
        (kb / "cdc" / "ia.md").unlink()
        self.assertEqual(av.ai_replay(kb, ""), [])

    def test_a_plan_older_than_the_stages_is_not_blocked_by_them(self):
        kb = project()
        (kb / "project").mkdir()
        rows = "".join(f"| `{s}` | fait |  |  |\n" for s in av.PIPELINES[0][1] if s != "cadrage-ia")
        path = kb / "project" / "avancement.md"
        path.write_text(f"## Cahier des charges\n| Étape | Statut | Mis à jour | Détail |\n{rows}"
                        "## Structuration\n| `stack` | fait |  |  |\n| `infra` | fait |  |  |\n"
                        "| `donnees` | en cours |  |  |\n", encoding="utf-8")
        sections, _ = av.load(path)
        status = {r[0]: r[1] for rows_ in sections.values() for r in rows_}
        self.assertEqual((status["cadrage-ia"], status["essai-ia"]), (av.SKIPPED, av.SKIPPED))
        self.assertEqual(plan(kb, "start", "essai-ia")[0], 1)
        self.assertEqual(plan(kb, "start", "cadrage-ia", "--rouvre", "cadrer Timestral")[0], 0)

    def test_a_plan_still_before_them_keeps_them_to_do(self):
        kb = project()
        (kb / "project").mkdir()
        path = kb / "project" / "avancement.md"
        path.write_text("## Cahier des charges\n| `hosa` | fait |  |  |\n| `fondamentaux` | fait |  |  |\n",
                        encoding="utf-8")
        status = {r[0]: r[1] for rows in av.load(path)[0].values() for r in rows}
        self.assertEqual((status["cadrage-ia"], status["essai-ia"]), (av.TODO, av.TODO))


class Wiring(unittest.TestCase):
    def test_downstream_agents_read_the_ai_files(self):
        for name in ("infra", "architect", "tech-lead", "qa-lead"):
            self.assertIn("essai-ia.md", (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8"), name)

    def test_contestation_and_qa_send_back_by_an_edge(self):
        """An AI finding at the sign-off reopens the cadrage; a model that no longer holds at `qa` reopens the trial."""
        self.assertTrue(av.edge("contestation", "cadrage-ia"))
        self.assertTrue(av.edge("qa", "essai-ia"))
        self.assertIn("ia.md", (ROOT / "agents" / "challenger.md").read_text(encoding="utf-8"))
        for skill, call in (("contestation", "back contestation cadrage-ia"), ("qa", "back qa essai-ia")):
            self.assertIn(call, (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8"), skill)

    def test_the_agent_template_passes_the_checker(self):
        """The two templates of `agents/ia.md`, filled in, are what `ia_check` accepts."""
        agent = (ROOT / "agents" / "ia.md").read_text(encoding="utf-8")
        for field in ia.FIELDS + ia.CONSTRAINTS:
            self.assertIn(f"{field} :", agent)
        self.assertIn(f"## {ia.CHOICES}", agent)
        for field in [f for fields in (*ia.FORMS.values(), *ia.SPEC.values()) for f in fields]:
            self.assertIn(f"`{field}`", agent)
        line = next(x for x in agent.splitlines() if x.startswith("- <AAAA-MM-JJTHH:MMZ> — IA1"))
        for field in ia.RESULT_FIELDS:
            self.assertTrue(re.search(rf"— {field} : ", line), field)


if __name__ == "__main__":
    unittest.main()
