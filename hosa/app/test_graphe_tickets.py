"""graphe_tickets.py: a sprint is computed from the `depends_on` graph — the path to an objective in build order,
cut at the ticket and demo bounds, then the ready tickets; an objective whose path can't be built is refused."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "sprint" / "scripts" / "graphe_tickets.py"
spec = importlib.util.spec_from_file_location("graphe_tickets", SCRIPT)
gt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gt)


def t(slug, prio, deps=(), state="todo", sprint=None, ecran=False, manques=(), pts=1):
    return slug, {"slug": slug, "title": slug, "state": state, "sprint": sprint, "priority": prio, "points": pts,
                  "depends_on": list(deps), "ecran": ecran, "manques": list(manques)}


def graph(*rows):
    return dict(rows)


class Path_(unittest.TestCase):
    """rieki: « Supprimer un run » waited for 32 tickets; the planner only saw priorities."""

    def setUp(self):
        self.g = graph(t("socle", None, state="done"), t("import", 40, ["socle"]), t("nettoyage", 18, ["import"]),
                       t("run", 72, ["nettoyage", "import"]), t("supprimer", 124, ["run"]), t("polish", 9))

    def test_the_path_is_in_build_order_without_what_is_done(self):
        self.assertEqual(gt.path_to(self.g, "supprimer"), (["import", "nettoyage", "run", "supprimer"], []))
        self.assertEqual(gt.ready(self.g), ["polish", "import"])

    def test_the_sprint_is_the_objective_path_ready_tickets_only_on_request(self):
        c = gt.compose(self.g, "run", 20, 15)
        self.assertEqual(([r["slug"] for r in c["tickets"]], c["atteint"]), (["import", "nettoyage", "run"], True))
        c = gt.compose(self.g, "run", 20, 15, remplir=True)
        self.assertEqual([(r["slug"], r["objectif"]) for r in c["tickets"]],
                         [("import", True), ("nettoyage", True), ("run", True), ("polish", False), ("supprimer", False)])

    def test_a_path_over_a_bound_stops_at_whole_milestones(self):  # tolerance 0: small bounds, the cut itself
        # supprimer ← run ← {nettoyage ← import, ecran ← import}: 2 tickets fit — never half a branch
        g = dict(self.g, ecran=t("ecran", 50, ["import"])[1], run=t("run", 72, ["nettoyage", "ecran"])[1])
        c = gt.compose(g, "supprimer", 2, 15, tolerance=0)
        self.assertEqual(([r["slug"] for r in c["tickets"]], c["atteint"], c["jalon"], c["reste"]),
                         (["import", "nettoyage"], False, ["nettoyage"], 3))
        c = gt.compose(g, "supprimer", 3, 15, tolerance=0)  # both branches: two milestones
        self.assertEqual((sorted(r["slug"] for r in c["tickets"]), c["jalon"]), (["ecran", "import", "nettoyage"], ["nettoyage", "ecran"]))
        g["nettoyage"] = t("nettoyage", 18, ["import"], ecran=True)[1]
        g["ecran"] = t("ecran", 50, ["import"], ecran=True)[1]
        self.assertEqual(gt.compose(g, "supprimer", 20, 1, tolerance=0)["jalon"], ["nettoyage"])  # one demo test: one screen

    def test_a_path_a_little_over_the_bounds_is_taken_whole(self):
        # 21 tickets for a ceiling of 20 (rieki: the first run) — no round trip to the user for one ticket
        rows = [t(f"t{i}", i, [f"t{i - 1}"] if i else [], ecran=i < 16) for i in range(21)]
        g = graph(*rows)
        c = gt.compose(g, "t20", 20, 15)
        self.assertEqual((len(c["tickets"]), c["atteint"], c["tolere"], c["jalon"]), (21, True, True, None))
        self.assertEqual(gt.with_tolerance(20, 5), 21)
        self.assertEqual(gt.with_tolerance(15, 5), 16)
        g["t21"] = t("t21", 21, ["t20"])[1]  # 22 tickets: over the tolerance, cut at a milestone
        c = gt.compose(g, "t21", 20, 15)
        self.assertEqual((c["tolere"], c["atteint"], len(c["tickets"])), (False, False, 15))  # 15 screens: the demo bound
        self.assertFalse(gt.compose(g, "t20", 20, 15, tolerance=0)["tolere"])  # the switch: strict bounds

    def test_the_objective_goes_further_on_its_own_way_while_it_fits(self):
        # rieki sprint-3: « importer les ventes » (8 tickets) while « lancer un run » (21) fitted on the same path
        c = gt.compose(self.g, "import", 20, 15, prolonger=True)
        self.assertEqual((c["demande"], c["objectif"], c["etendu"]), ("import", "supprimer", True))
        self.assertEqual([r["slug"] for r in c["tickets"]], ["import", "nettoyage", "run", "supprimer"])
        self.assertEqual(gt.compose(self.g, "import", 3, 15, tolerance=0, prolonger=True)["objectif"], "run")  # the furthest that fits
        c = gt.compose(self.g, "import", 20, 15)  # by default the objective stays as given
        self.assertEqual((c["objectif"], c["etendu"], len(c["tickets"])), ("import", False, 1))
        g = dict(self.g, supprimer=t("supprimer", 124, ["run"], manques=["x"])[1])  # an incomplete one stops the way
        self.assertEqual(gt.compose(g, "import", 20, 15, prolonger=True)["objectif"], "run")
        self.assertEqual(gt.compose(self.g, "polish", 20, 15, prolonger=True)["objectif"], "polish")  # nothing waits for it

    def test_an_objective_whose_path_cant_be_built_is_refused(self):
        g = dict(self.g, nettoyage=t("nettoyage", 18, ["import"], manques=["section absente"])[1],
                 run=t("run", 72, ["nettoyage", "absent"])[1])
        c = gt.compose(g, "run", 20, 15)
        self.assertEqual(c["tickets"], [])
        self.assertEqual(c["obstacles"][0], "`absent` : ticket introuvable (cité dans un `depends_on`)")
        self.assertIn("`nettoyage` : incomplet → `/backlog nettoyage`", c["obstacles"][1])
        g["polish"] = t("polish", 9, sprint="sprint-3")[1]
        self.assertIn("`polish` : déjà dans le sprint `sprint-3`", gt.compose(g, "polish", 20, 15)["obstacles"])

    def test_a_composed_sprint_brings_its_tickets_only_in_the_preview(self):
        g = dict(self.g, nettoyage=t("nettoyage", 18, ["import"], sprint="sprint-3")[1],
                 **{"import": t("import", 40, ["socle"], sprint="sprint-3")[1]})
        self.assertEqual(gt.path_to(g, "supprimer", apercu=True)[0], ["run", "supprimer"])
        self.assertEqual([r["slug"] for r in gt.compose(g, "supprimer", 20, 15, apercu=True)["tickets"]], ["run", "supprimer"])
        # a real sprint starts from main, without sprint-3's code: `done sprint` would refuse it
        self.assertIn("`import` : déjà dans le sprint `sprint-3`", gt.compose(g, "supprimer", 20, 15)["obstacles"])

    def test_no_objective_takes_the_first_ticket_whose_path_can_be_built(self):
        g = dict(self.g, polish=t("polish", 9, manques=["x"])[1])
        c = gt.compose(g, None, 20, 15)  # polish (9) can't; nettoyage (18) can, through import
        self.assertEqual((c["objectif"], [r["slug"] for r in c["tickets"]]), ("nettoyage", ["import", "nettoyage"]))


class Roadmap(unittest.TestCase):
    """Every sprint to come, computed once the milestones are validated: each ticket lands once, each sprint can
    be built when the earlier ones are delivered."""

    def setUp(self):
        rows = [t("socle", None, state="done")]
        rows += [t(f"imp{i}", 10 + i, [f"imp{i - 1}"] if i else ["socle"], ecran=True) for i in range(6)]   # import
        rows += [t(f"net{i}", 20 + i, [f"net{i - 1}"] if i else ["imp5"]) for i in range(10)]               # cleaning
        rows += [t(f"run{i}", 40 + i, [f"run{i - 1}"] if i else ["net9"], ecran=i % 2 == 0) for i in range(12)]
        rows += [t("polish", 1), t("secu", 2, ["imp2"]), t("trou", 3, manques=["CA1 cite `x`"]), t("apres-trou", 4, ["trou"])]
        self.g = graph(*rows)

    def check_invariants(self, r):
        seen = [s for sp in r["sprints"] for s in sp["tickets"]]
        self.assertEqual(len(seen), len(set(seen)))  # each ticket once
        left = {s for s, x in self.g.items() if x["state"] == "todo"} - set(seen)
        self.assertEqual(left, {a["slug"] for a in r["a_completer"]} | set(r["en_attente"]))  # and every one somewhere
        done = {s for s, x in self.g.items() if x["state"] == "done"}
        for sp in r["sprints"]:  # buildable in order, the earlier sprints delivered
            for s in sp["tickets"]:
                self.assertTrue(set(self.g[s]["depends_on"]) <= done, (s, self.g[s]["depends_on"]))
                done.add(s)
            self.assertLessEqual(len(sp["tickets"]), gt.with_tolerance(20, 5))
            self.assertLessEqual(sp["demo"], gt.with_tolerance(15, 5))

    def test_milestones_in_order_then_the_rest_by_priority(self):
        r = gt.roadmap(self.g, ["imp5", "net9", "run11"])
        self.check_invariants(r)
        self.assertEqual([sp["jalons"] for sp in r["sprints"]][:2], [["imp5", "net9"], ["run11"]])
        self.assertEqual(r["sprints"][-1]["nature"], "hors parcours")
        self.assertEqual(r["sprints"][-1]["tickets"], ["polish", "secu"])  # by priority, after the journey
        self.assertEqual(([a["slug"] for a in r["a_completer"]], r["en_attente"]), (["trou"], ["apres-trou"]))

    def test_a_milestone_longer_than_a_sprint_is_cut_at_whole_sub_paths(self):
        r = gt.roadmap(self.g, ["run11"], plafond=8, demo=15, tolerance=0)
        self.check_invariants(r)
        self.assertEqual([len(sp["tickets"]) for sp in r["sprints"] if sp["nature"] == "parcours"], [8, 8, 8, 4])
        self.assertEqual(r["sprints"][3]["jalons"], ["run11"])  # the milestone closes the sprint that ends its path

    def test_a_milestone_behind_an_incomplete_ticket_is_blocked_and_named(self):
        g = dict(self.g, net3=t("net3", 23, ["net2"], manques=["lit `ventes`…"])[1])
        r = gt.roadmap(g, ["imp5", "run11"])
        self.assertEqual(r["sprints"][0]["jalons"], ["imp5"])
        self.assertEqual(r["bloques"][0]["jalon"], "run11")
        self.assertIn("`net3` : incomplet", r["bloques"][0]["obstacles"][0])
        self.assertEqual([sp["nature"] for sp in r["sprints"]], ["parcours"])  # nothing past it, no bag of the rest
        r = gt.roadmap(g, ["run11", "imp5"])  # the first milestone blocked: no sprint at all, the fix comes first
        self.assertEqual((r["sprints"], [b["jalon"] for b in r["bloques"]]), ([], ["run11", "imp5"]))

    def test_the_roadmap_file_keeps_the_validated_milestones(self):
        kb = Path(tempfile.mkdtemp())
        r = gt.roadmap(self.g, ["imp5"])
        f = gt.write_roadmap(kb, self.g, r, "2026-11-15T12:00:00Z", ["imp5"])
        self.assertEqual(gt.read_jalons(kb), ["imp5"])
        text = f.read_text(encoding="utf-8")
        self.assertIn("## Sprints\n### Sprint 1 — `imp5`", text)
        self.assertIn("type: Feuille de route", text)
        gt.write_roadmap(kb, self.g, gt.roadmap(self.g, ["imp5"], plafond=3), "2026-11-15T13:00:00Z")
        self.assertEqual(gt.read_jalons(kb), ["imp5"])  # recomputed: the milestones unchanged
        self.assertIn("### Sprint 2 — `imp5`", f.read_text(encoding="utf-8"))  # cut at whole sub-paths
        self.assertEqual(gt.read_bornes(kb), (3, 15, 5))  # the bounds written are the ones read back
        self.assertEqual(gt.read_bornes(Path(tempfile.mkdtemp())), (20, 15, 5))


class Cli(unittest.TestCase):
    def setUp(self):
        self.kb = Path(tempfile.mkdtemp())
        (self.kb / "tickets").mkdir()
        ui = "## Placement interface (UX/UI)\n- **Écran / route** : Résultats (`/resultats`)\n"
        (self.kb / "tickets" / "a.md").write_text(f"---\ntype: Ticket\nstate: todo\npriority: 1\nestimate: 3\n---\n{ui}", encoding="utf-8")
        (self.kb / "tickets" / "b.md").write_text("---\ntype: Ticket\nstate: todo\nsprint: s3\ndepends_on: [a]\n---\n", encoding="utf-8")

    def run_(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gt.main([str(self.kb), *args])
        return code, out.getvalue()

    def test_a_ticket_file_is_read_with_its_points_screen_and_gaps(self):
        g = gt.load(self.kb)
        self.assertEqual((g["a"]["points"], g["a"]["ecran"], g["b"]["points"], g["b"]["ecran"]), (3, True, 2, False))
        self.assertTrue(g["a"]["manques"])  # incomplete: no story, no notes

    def test_the_roadmap_prints_every_one_fix_line_as_the_checker_wrote_it(self):
        (self.kb / "tickets" / "e.md").write_text("---\ntype: Ticket\nstate: todo\n---\n## Critères d'acceptation\n"
                                                  "- CA1 — voir [a](a.md)\n", encoding="utf-8")
        line = "CA1 cite `a` (à faire), hors de ses dépendances → `depends_on: [a]`, ou porter ce critère dans `a`"
        _, out = self.run_("feuille", "--jalons", "a")
        self.assertIn("Corrections uniques (1)", out)
        self.assertIn(f"- `e` : {line}", out)
        _, out = self.run_("feuille", "--jalons", "a", "--json")
        self.assertEqual(json.loads(out)["corrections"], [{"slug": "e", "ligne": line}])

    def test_a_sprint_written_from_the_composition_passes_done_sprint(self):
        av_path = SCRIPT.parents[2] / "status" / "scripts" / "avancement.py"
        sp = importlib.util.spec_from_file_location("avancement", av_path)
        av = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(av)
        for slug, deps in (("c", "[a]"), ("d", "[c, a]")):
            (self.kb / "tickets" / f"{slug}.md").write_text(
                f"---\ntype: Ticket\nstate: todo\npriority: 3\ndepends_on: {deps}\n---\n", encoding="utf-8")
        with mock.patch.object(gt.ticket_check(), "gaps", lambda p: []):  # bare tickets: their notes aren't the point
            c = gt.compose(gt.load(self.kb), "d", 20, 15)
        self.assertEqual([r["slug"] for r in c["tickets"]], ["a", "c", "d"])
        (self.kb / "sprints").mkdir()
        (self.kb / "sprints" / "s4.md").write_text("---\ntype: Sprint\n---\n## Tickets\n" + "".join(
            f"- [{r['slug']}](../tickets/{r['slug']}.md)\n" for r in c["tickets"]), encoding="utf-8")
        self.assertEqual(av.proofs(self.kb, "sprint", "s4"), [])

    def test_the_roadmaps_first_sprint_passes_done_sprint(self):
        av_path = SCRIPT.parents[2] / "status" / "scripts" / "avancement.py"
        sp = importlib.util.spec_from_file_location("avancement", av_path)
        av = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(av)
        for slug, deps in (("c", "[a]"), ("d", "[c, a]"), ("e", "[d]")):
            (self.kb / "tickets" / f"{slug}.md").write_text(
                f"---\ntype: Ticket\nstate: todo\npriority: 3\ndepends_on: {deps}\n---\n", encoding="utf-8")
        with mock.patch.object(gt.ticket_check(), "gaps", lambda p: []):
            r = gt.roadmap(gt.load(self.kb, "s3"), ["d", "e"], plafond=3, tolerance=0)
        first = r["sprints"][0]["tickets"]
        self.assertEqual((first, r["sprints"][0]["jalons"]), (["a", "c", "d"], ["d"]))
        (self.kb / "sprints").mkdir()
        (self.kb / "sprints" / "s5.md").write_text("---\ntype: Sprint\n---\n## Tickets\n" + "".join(
            f"- [{s}](../tickets/{s}.md)\n" for s in first), encoding="utf-8")
        self.assertEqual(av.proofs(self.kb, "sprint", "s5"), [])

    def test_recomposing_a_sprint_frees_its_tickets(self):
        code, out = self.run_("composer", "--objectif", "b", "--json")
        self.assertEqual(code, 1)
        self.assertIn("`b` : déjà dans le sprint `s3`", json.loads(out)["obstacles"])
        code, out = self.run_("composer", "--objectif", "b", "--sprint", "s3", "--json")
        self.assertNotIn("`b` : déjà dans le sprint `s3`", json.loads(out)["obstacles"])


if __name__ == "__main__":
    unittest.main()
