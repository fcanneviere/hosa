"""ticket_check.py: a file cited as existing but created by another ticket needs a `depends_on` on it;
abuse cases and legal constraints are acceptance criteria; a dependency never ranks after its ticket."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "backlog" / "scripts" / "ticket_check.py"
spec = importlib.util.spec_from_file_location("ticket_check", SCRIPT)
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)


def ticket(placement: str, deps: str = "") -> str:
    return f"---\ntype: Ticket\nstate: todo\n{deps}---\n## Placement architecture (architecte)\n{placement}\n"


class PhantomPaths(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.tickets = self.root / ".hosa" / "kb" / "tickets"
        self.tickets.mkdir(parents=True)
        (self.root / "core").mkdir()
        (self.root / "core" / "views.py").write_text("", encoding="utf-8")
        (self.tickets / "limite.md").write_text(ticket("- `core/limitation.py` — à créer"), encoding="utf-8")

    def check(self, text):
        p = self.tickets / "inscription.md"
        p.write_text(text, encoding="utf-8")
        return tc.phantom_paths(p, *tc.split(text))

    def test_missing_dependency_names_the_creator(self):
        gaps = self.check(ticket("- **Points d'appel** : `core/views.py:connexion` ; `core/limitation.py`"))
        self.assertEqual(gaps, ["`core/limitation.py` cité comme existant, créé par `limite` → ajouter `depends_on: [limite]`"])

    def test_dependency_kb_path_and_unknown_path(self):
        self.assertEqual(self.check(ticket("- `core/limitation.py` ; `kb/interface/lexique.md`", "depends_on: [limite]\n")), [])
        self.assertIn("absent du projet", self.check(ticket("- `core/inconnu.py`"))[0])


class UnbuiltLabels(unittest.TestCase):
    """rieki sprint-3: the button hierarchy (priority 9) tested « Supprimer » of Résultats, which
    `supprimer-un-run` brings at priority 124: qa-plan found it, and asked the user what to do."""
    HIERARCHIE = ("- CA4 — Étant donné l'écran Résultats avec un run terminé, quand il s'affiche, alors « Exporter en CSV » "
                  "est secondaire et « Supprimer » est destructeur.\n"
                  "- CA8 — Étant donné « Tout effacer » et, dès qu'il existe, « Supprimer » (Résultats), quand un "
                  "attaquant clique une seule fois, alors rien n'est effacé.\n")

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.tickets = self.root / ".hosa" / "kb" / "tickets"
        self.tickets.mkdir(parents=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "resultats.py").write_text('st.button("Exporter en CSV")\n', encoding="utf-8")
        self.write("supprimer-un-run", "", "- CA1 — Étant donné R12, quand l'analyste clique sur « Supprimer » puis "
                                           "« Confirmer », alors R12 est supprimé.\n")
        tc.source_text.cache_clear()

    def write(self, slug, front, crit):
        p = self.tickets / f"{slug}.md"
        p.write_text(f"---\ntype: Ticket\nstate: todo\n{front}---\n## Critères d'acceptation\n{crit}", encoding="utf-8")
        return p

    def check(self, p):
        return tc.unbuilt_labels(p, *tc.split(p.read_text(encoding="utf-8")))

    def test_a_label_another_ticket_brings_needs_it_in_depends_on(self):
        gaps = self.check(self.write("hierarchie", "", self.HIERARCHIE))
        self.assertEqual(len(gaps), 3, gaps)  # CA8 conditional, CA4 and CA8 cite « Supprimer »
        self.assertTrue(gaps[0].startswith("CA8 conditionnel (« dès qu'il existe »)"))
        self.assertIn("CA4 cite « Supprimer », absent du code et livré par `supprimer-un-run` (à faire)", gaps[1])
        self.assertTrue(gaps[2].startswith("CA8 cite « Supprimer »"))

    def test_brought_by_a_dependency_by_itself_or_already_in_the_code(self):
        crit = self.HIERARCHIE.replace("dès qu'il existe, ", "")
        self.write("lien", "depends_on: [supprimer-un-run]\n", "- CA1 — rien\n")  # through another ticket
        self.assertEqual(self.check(self.write("hierarchie", "depends_on: [lien]\n", crit)), [])
        self.write("supprimer-un-run", "", "- CA1 — rien\n")  # nobody brings it: not this check's business
        self.assertEqual(self.check(self.write("hierarchie", "", crit)), [])
        self.write("supprimer-un-run", "", "- CA1 — quand l'analyste clique sur « Supprimer », alors R12 est supprimé.\n")
        (self.root / "src" / "resultats.py").write_text('st.button("Supprimer")\n', encoding="utf-8")
        tc.source_text.cache_clear()
        self.assertEqual(self.check(self.write("hierarchie", "", crit)), [])  # the code has it now

    def test_a_literal_in_any_form_counts_and_the_check_has_its_switch(self):
        (self.root / "src" / "resultats.py").write_text(
            '"""Supprimer une version supprime ses filles."""\nif c.button(":red[Confirmer]"):\n', encoding="utf-8")
        self.write("importer", "", "- CA1 — quand l'analyste clique sur « Confirmer », alors l'import est enregistré.\n")
        p = self.write("hierarchie", "", "- CA8 — « Supprimer » puis « Confirmer » : rien n'est effacé avant.\n")
        self.assertEqual([g[:20] for g in self.check(p)], ["CA8 cite « Supprimer"])  # a sentence's word isn't it
        os.environ["HOSA_LIBELLES"] = "0"
        try:
            self.assertEqual(self.check(p), [])
        finally:
            del os.environ["HOSA_LIBELLES"]


class HiddenDependencies(unittest.TestCase):
    """The dependencies a ticket's own text states, its `depends_on` missing — the rieki cases, as they were written."""

    def setUp(self):
        self.tickets = Path(tempfile.mkdtemp()) / ".hosa" / "kb" / "tickets"
        self.tickets.mkdir(parents=True)

    def write(self, slug, front="", crit="", donnees=None):
        place = f"## Placement architecture (architecte)\n- **Données** : {donnees}\n" if donnees else ""
        p = self.tickets / f"{slug}.md"
        state = "" if "state:" in front else "state: todo\n"
        p.write_text(f"---\ntype: Ticket\n{state}{front}---\n## Critères d'acceptation\n{crit}{place}", encoding="utf-8")
        return p

    def gaps(self, p):
        return tc.hidden_dependencies(p, *tc.split(p.read_text(encoding="utf-8")))

    def test_a_criterion_citing_a_ticket_to_build_needs_it(self):
        self.write("supprimer-un-article")
        p = self.write("consulter-les-articles", crit="- CA5 — Étant donné un article supprimé par "
                       "[supprimer-un-article](supprimer-un-article.md), quand le tableau s'affiche, alors il n'y est plus.\n")
        self.assertEqual(self.gaps(p), ["CA5 cite `supprimer-un-article` (à faire), hors de ses dépendances → "
                                        "`depends_on: [supprimer-un-article]`, ou porter ce critère dans `supprimer-un-article`"])
        p = self.write("consulter-les-articles", "depends_on: [supprimer-un-article]\n", p.read_text(encoding="utf-8").split("\n## Critères d'acceptation\n")[1])
        self.assertEqual(self.gaps(p), [])
        self.write("supprimer-un-article", "state: done\n")
        self.assertEqual(self.gaps(self.write("consulter-les-articles", crit="- CA5 — [s](supprimer-un-article.md)\n")), [])

    def test_two_tickets_citing_each_other_hold_one_behaviour_and_a_later_one_takes_the_criterion(self):
        v = self.write("importer-les-ventes", crit="- CA7 — l'erreur s'affiche ([p](proteger-les-rappels.md))\n")
        p = self.write("proteger-les-rappels", crit="- CA9 — un import de ventes qui échoue ([v](importer-les-ventes.md))\n")
        self.assertEqual(self.gaps(v), ["CA7 et `proteger-les-rappels` CA9 portent le même comportement (chacun cite "
                                        "l'autre) : un seul des deux le garde, l'autre le retire"])
        self.assertEqual(len(self.gaps(p)), 1)
        self.write("afficher-la-cause", "depends_on: [suivre-le-statut]\n")
        s = self.write("suivre-le-statut", crit="- CA4 — la cause ([a](afficher-la-cause.md))\n")
        self.assertEqual(self.gaps(s), ["CA4 cite `afficher-la-cause`, qui vient après ce ticket (il en dépend) → "
                                        "porter ce critère dans `afficher-la-cause`"])

    def test_a_table_read_needs_a_writer_done_or_among_its_dependencies(self):
        self.write("importer-les-ventes", donnees="`ventes`.`date`, `quantite` (DECIMAL) écrits ; `imports`.`id` écrit.")
        p = self.write("nettoyer", donnees="`versions`.`id`, `numero` ; `rapport` écrites ; `ventes` lue seulement.")
        self.assertEqual(tc.data_access(p.read_text(encoding="utf-8")), ({"versions", "rapport"}, {"ventes"}))
        self.assertEqual(self.gaps(p), ["lit `ventes`, qu'aucun ticket fait ni de ses dépendances n'écrit → "
                                        "`depends_on: [importer-les-ventes]` (le premier à l'écrire)"])
        # a later writer that rewrites columns isn't the one to wait for (rieki: the unknown-codes check)
        self.write("signaler-les-codes", "depends_on: [importer-les-ventes]\n", donnees="`ventes`.`code_client` écrits.")
        self.assertEqual(self.gaps(p), ["lit `ventes`, qu'aucun ticket fait ni de ses dépendances n'écrit → "
                                        "`depends_on: [importer-les-ventes]` (le premier à l'écrire)"])
        self.write("autre-source", donnees="`ventes`.`date` écrits.")  # two first writers: the product owner picks
        self.assertIn("l'écrivent d'abord (à faire) : `autre-source`, `importer-les-ventes`", self.gaps(p)[0])
        (self.tickets / "autre-source.md").unlink()
        p = self.write("nettoyer", "depends_on: [importer-les-ventes]\n", donnees="`ventes` lue seulement.")
        self.assertEqual(self.gaps(p), [])
        # every writer comes after the reader: it shows the empty state, no edge (rieki: versions list, runs later)
        self.write("lancer-un-run", "depends_on: [lister-les-versions]\n", donnees="`runs`.`id` écrit.")
        self.assertEqual(self.gaps(self.write("lister-les-versions", donnees="`runs`.`id` lus.")), [])
        os.environ["HOSA_DEPENDANCES"] = "0"
        try:
            self.assertEqual(self.gaps(self.write("nettoyer", donnees="`ventes` lue seulement.")), [])
        finally:
            del os.environ["HOSA_DEPENDANCES"]


SECURITE = """## Note sécurité (expert cybersécurité)
- **Règles** : `limitation-de-debit` — 10 échecs par 15 min par couple
- **Cas d'abus** :
  - Étant donné un attaquant, quand il essaie 11 mots de passe, alors le 11e est refusé → CA2
  - Étant donné un attaquant, quand il forge `X-Forwarded-For`, alors l'adresse réelle compte
- **Contrôle d'accès** : aucun
- **Journalisation** : `connexion_refusee` au journal technique
- **Données sensibles** : mot de passe — jamais au journal
"""

JURIDIQUE = """## Note juridique (expert conformité)
- **Contraintes** : aucun
- **Données personnelles** : traitement 1 — identifiant — contrat — 12 mois
- **Hors logiciel** : aucun
"""


class OneFix(unittest.TestCase):
    """The checker lines that are their own decision: the product owner applies them, nobody is asked."""

    def test_one_ticket_named_is_one_fix_several_or_none_is_not(self):
        yes = ["lit `ventes`, qu'aucun ticket fait ni de ses dépendances n'écrit → `depends_on: [importer-les-ventes]` "
               "(le premier à l'écrire)",
               "CA5 cite `supprimer-un-article` (à faire), hors de ses dépendances → `depends_on: [supprimer-un-article]`, "
               "ou porter ce critère dans `supprimer-un-article`",
               "CA4 cite `afficher-la-cause`, qui vient après ce ticket (il en dépend) → porter ce critère dans `afficher-la-cause`",
               "CA7 et `proteger` CA9 portent le même comportement (chacun cite l'autre) : un seul des deux le garde, l'autre le retire",
               "`src/a.py` cité comme existant, créé par `creer-a` → ajouter `depends_on: [creer-a]`",
               "CA4 cite « Supprimer », absent du code et livré par `supprimer-un-run` (à faire) → ajouter le bon à `depends_on`"]
        no = ["lit `ventes`, qu'aucun ticket fait ni de ses dépendances n'écrit — l'écrivent d'abord (à faire) : `a`, `b` "
              "→ mettre celui qui la remplit dans `depends_on`",
              "CA4 cite « Supprimer », absent du code et livré par `a`, `b` (à faire) → ajouter le bon à `depends_on`",
              "CA8 conditionnel (« dès qu'il existe ») : un critère se teste à la fin de son ticket → `depends_on` le ticket "
              "qui livre l'élément, ou porter le critère dans ce ticket-là",
              "section `## Note sécurité` absente"]
        self.assertEqual([tc.one_fix(g) for g in yes], [True] * len(yes))
        self.assertEqual([tc.one_fix(g) for g in no], [False] * len(no))

    def test_single_fixes_lists_every_todo_ticket_s_lines(self):
        tickets = Path(tempfile.mkdtemp()) / "tickets"
        tickets.mkdir()
        body = "## Critères d'acceptation\n- CA1 — voir [b](b.md)\n"
        (tickets / "a.md").write_text(f"---\ntype: Ticket\nstate: todo\n---\n{body}", encoding="utf-8")
        (tickets / "b.md").write_text("---\ntype: Ticket\nstate: todo\n---\n", encoding="utf-8")
        (tickets / "c.md").write_text(f"---\ntype: Ticket\nstate: done\n---\n{body}", encoding="utf-8")
        self.assertEqual(tc.single_fixes(tickets), [("a", "CA1 cite `b` (à faire), hors de ses dépendances → "
                                                     "`depends_on: [b]`, ou porter ce critère dans `b`")])


class SecurityAndLegalNotes(unittest.TestCase):
    def setUp(self):
        self.tickets = Path(tempfile.mkdtemp()) / "tickets"
        self.tickets.mkdir()

    def write(self, slug, front, body):
        p = self.tickets / f"{slug}.md"
        state = "" if "state:" in front else "state: todo\n"
        p.write_text(f"---\ntype: Ticket\n{state}{front}---\n{body}", encoding="utf-8")
        return p

    def test_abuse_case_without_criterion_and_unknown_criterion(self):
        body = "## Critères d'acceptation\n- CA1 — nominal\n" + SECURITE + JURIDIQUE
        gaps = tc.gaps(self.write("connexion", "", body))
        self.assertTrue(any("sans critère" in g and "X-Forwarded-For" in g for g in gaps))
        self.assertIn("`Note sécurité (expert cybersécurité)` cite `CA2`, absent des critères d'acceptation", gaps)

    def test_legal_note_required_with_its_bullets(self):
        body = "## Critères d'acceptation\n- CA1 — nominal\n- CA2 — refus\n" + SECURITE.replace(
            "l'adresse réelle compte", "l'adresse réelle compte → CA1")
        gaps = tc.gaps(self.write("connexion", "", body))
        self.assertIn("(à détailler) section `## Note juridique (expert conformité)` absente", gaps)
        self.assertFalse(any("sans critère" in g for g in gaps))
        gaps = tc.gaps(self.write("connexion", "", body + JURIDIQUE.replace("- **Hors logiciel** : aucun\n", "")))
        self.assertIn("`Note juridique (expert conformité)` : puce « Hors logiciel » absente", gaps)

    def test_more_than_ten_criteria_blocks_and_a_criterion_is_the_same_for_every_script(self):
        many = "## Critères d'acceptation\n" + "".join(f"- CA{i} — c\n" for i in range(1, 12))
        gaps = tc.gaps(self.write("gros", "priority: 1\n", many))
        self.assertIn("11 critères, 10 au plus — plusieurs variantes ou règles : découper le ticket", gaps)
        self.assertEqual(tc.criteria_ids("- CA1 — a\n  * CA2 — b\n- CA1 — a\n-CA3"), ["CA1", "CA2"])
        av_spec = importlib.util.spec_from_file_location("avancement", SCRIPT.parents[2] / "status" / "scripts" /
                                                         "avancement.py")
        av = importlib.util.module_from_spec(av_spec)
        av_spec.loader.exec_module(av)
        self.assertEqual(av.criteria("## Critères d'acceptation\n- CA1 — a\n  * CA2 — b\n"), ["CA1", "CA2"])

    def test_story_with_an_elided_que(self):
        for story in ("En tant qu'administrateur,", "En tant qu’administrateur,", "En tant que parent,"):
            self.assertNotIn("story « En tant que … » absente", tc.gaps(self.write("s", "", story + "\n")))
        self.assertIn("story « En tant que … » absente", tc.gaps(self.write("s", "", "En tant quelconque\n")))

    def test_skipped_stage_note_is_written_from_the_plan_and_accepted(self):
        plan = self.tickets.parent / "project" / "avancement.md"
        plan.parent.mkdir()
        plan.write_text("| Étape | Statut | Date | Détail |\n|---|---|---|---|\n"
                        "| `securite` | fait | 2026-11-01T10:00:00Z |  |\n"
                        "| `juridique` | non applicable | 2026-11-01T11:50:34Z | Utilisateur : usage de test |\n",
                        encoding="utf-8")
        waiting = "## Note juridique (expert conformité)\nAnalyse juridique pas encore faite — contraintes non déterminées.\n"
        body = "## Critères d'acceptation\n- CA1 — nominal\n" + waiting + "\n## Suite\nfin\n"
        p = self.write("import", "", body)
        self.assertTrue(any("encore au texte d'attente — étape `juridique` écartée" in g for g in tc.gaps(p)))
        skipped = tc.skipped_stages(self.tickets.parent)
        self.assertEqual(skipped, {"juridique": "Utilisateur : usage de test"})
        self.assertEqual(tc.write_skipped(p, skipped), ["## Note juridique (expert conformité)"])
        text = p.read_text(encoding="utf-8")
        self.assertIn("## Note juridique (expert conformité)\nNon applicable — étape `juridique` écartée : "
                      "Utilisateur : usage de test\n\n## Suite\nfin\n", text)
        self.assertTrue(text.startswith("---\ntype: Ticket\nstate: todo\n---\n## Critères d'acceptation\n"))
        self.assertFalse(any("Note juridique" in g for g in tc.gaps(p)))
        self.assertEqual(tc.write_skipped(p, skipped), [])  # written once
        absent = self.write("sans", "", "## Critères d'acceptation\n- CA1 — nominal\n")
        tc.write_skipped(absent, skipped)
        self.assertTrue(absent.read_text(encoding="utf-8").endswith(
            "\n\n## Note juridique (expert conformité)\nNon applicable — étape `juridique` écartée : "
            "Utilisateur : usage de test\n"))
        real = self.write("reel", "", JURIDIQUE)
        self.assertEqual(tc.write_skipped(real, skipped), [])  # a real note is never touched

    def test_a_stage_set_aside_needs_no_note_at_all(self):
        """rieki: `juridique` set aside, 44 KB of « Non applicable » lines over 148 tickets."""
        plan = self.tickets.parent / "project" / "avancement.md"
        plan.parent.mkdir()
        plan.write_text("| Étape | Statut | Date | Détail |\n|---|---|---|---|\n"
                        "| `juridique` | non applicable | 2026-11-01T11:50:34Z | usage de test |\n", encoding="utf-8")
        gaps = tc.gaps(self.write("sans", "", "## Critères d'acceptation\n- CA1 — nominal\n"))
        self.assertFalse(any("Note juridique" in g for g in gaps), gaps)
        self.assertTrue(any("(à détailler) section `## Note sécurité" in g for g in gaps))

    def test_a_ticket_without_notes_is_planned_not_complete(self):
        """`backlog` writes story, criteria and graph; `sprint` the notes of the tickets it takes."""
        p = self.write("plan", "", "En tant que analyste,\nLié à : [x](../cdc/x.md)\n## Critères d'acceptation\n- CA1 — a\n")
        self.assertEqual(sorted(g.split("`")[1] for g in tc.gaps(p) if not g.startswith("(info)")), sorted(tc.NOTES))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(tc.main([str(self.tickets.parent), str(p)]), 1)
            self.assertEqual(tc.main([str(self.tickets.parent), "--planifiable", str(p)]), 0)
        self.assertIn("✓ plan.md — planifiable, notes à détailler au sprint", out.getvalue())
        half = self.write("moitie", "", "En tant que analyste,\nLié à : [x](../cdc/x.md)\n## Critères d'acceptation\n"
                                        "- CA1 — a\n## Note technique (senior dev)\nStack pas encore choisie\n")
        with contextlib.redirect_stdout(io.StringIO()):  # a note on its fallback line is a gap, planned or not
            self.assertEqual(tc.main([str(self.tickets.parent), "--planifiable", str(half)]), 1)

    def test_an_abuse_case_is_deferred_only_while_the_project_is_explored(self):
        """rieki, a local single-user test of a model: 6 of 26 tickets hardened the import before any forecast."""
        kb = self.tickets.parent
        (kb / "project").mkdir()
        ident = kb / "project" / "identity.md"
        deferred = SECURITE.replace("l'adresse réelle compte", "l'adresse réelle compte — différé : usage exploratoire")
        body = "## Critères d'acceptation\n- CA1 — nominal\n- CA2 — refus\n" + deferred + JURIDIQUE
        p = self.write("connexion", "", body)
        self.assertTrue(any("différé alors que l'usage est réel" in g for g in tc.gaps(p)))  # no `## Usage`: réel
        ident.write_text("---\ntype: Project\n---\n## Usage\nexploratoire — tester le modèle sur de vraies ventes\n",
                         encoding="utf-8")
        self.assertEqual(tc.usage(kb), "exploratoire")
        self.assertFalse(any("Note sécurité" in g for g in tc.gaps(p)), tc.gaps(p))
        self.write("fait", "state: done\n", deferred)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(tc.main([str(kb), "--differes"]), 0)  # listed, not refused while explored
        self.assertIn("Usage : exploratoire — 2 cas d'abus différé(s)", out.getvalue())
        self.assertIn("fait (done) :", out.getvalue())  # done tickets too: real use builds them first
        ident.write_text("---\ntype: Project\n---\n## Usage\nréel\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tc.main([str(kb), "--differes"]), 1)

    def test_non_applicable_note_refused_when_the_plan_keeps_the_stage(self):
        p = self.write("import", "", "## Note sécurité (expert cybersécurité)\nNon applicable — étape `securite` écartée\n")
        self.assertIn("section `## Note sécurité (expert cybersécurité)` « Non applicable » alors que le plan "
                      "d'avancement n'écarte pas l'étape `securite`", tc.gaps(p))

    def test_a_criterion_cites_rules_its_exigence_has_and_every_rule_is_cited(self):
        kb = self.tickets.parent
        (kb / "cdc").mkdir()
        (kb / "cdc" / "envoi.md").write_text(
            "---\ntype: Exigence\n---\n## Règles de gestion\n- **RG1** — une seule notification\n"
            "- **RG2** — retirée : remplacée par RG3\n- **RG3** — 50 articles au plus\n"
            "## Cas d'erreur\n- **CE1** — liste vide → refus\n", encoding="utf-8")
        (kb / "cdc" / "ancien.md").write_text("---\ntype: Exigence\n---\n## Règles de gestion\n- **RG1** — a\n", encoding="utf-8")
        story = "En tant que parent,\nLié à : [p](../personnas/p.md), [e](../cdc/envoi.md)\n## Critères d'acceptation\n"
        p = self.write("envoyer", "", story + "- CA1 [RG1, CE1] — nominal\n- CA2 [RG2] — retirée\n- CA3 [RG9] — inconnue\n- CA4 — sans règle\n")
        gaps = tc.gaps(p)
        self.assertIn("un critère cite `RG2`, absent de l'exigence liée (ou retiré)", gaps)
        self.assertIn("un critère cite `RG9`, absent de l'exigence liée (ou retiré)", gaps)
        self.assertFalse(any("`RG1`" in g or "`CE1`" in g for g in gaps))
        self.write("avant", "state: done\n", story.replace("envoi.md", "ancien.md") + "- CA1 — écrit avant les identifiants\n")
        self.assertEqual(tc.rule_coverage(kb), ["✗ cdc/envoi.md — RG3 : aucun critère de ses tickets ne les cite (`- CAn [RG3] — …`)"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tc.main([str(kb), "--regles"]), 1)
        self.write("limite", "", story + "- CA1 [RG3] — 51e article refusé\n")   # another ticket of the exigence takes it
        self.assertEqual(tc.rule_coverage(kb), [])

    def test_a_behaviour_two_tickets_of_one_exigence_state_is_owned_by_one(self):
        kb = self.tickets.parent
        link = "En tant que analyste,\nLié à : [p](../personnas/p.md), [e](../cdc/import.md)"
        cancel = "- CA{} — Étant donné cette anomalie, quand l'analyste clique sur « Annuler », alors rien n'est enregistré.\n"
        crit = lambda n, extra="": f"{link}{extra}\n## Critères d'acceptation\n- CA1 — nominal\n" + cancel.format(n)  # noqa: E731
        self.write("signaler-date", "", crit(2))
        self.write("signaler-ligne", "", crit(5))
        self.assertEqual(tc.repeated_criteria(kb), [
            "✗ cdc/import.md — `signaler-date` CA2 ≈ `signaler-ligne` CA5 (100% de mots communs) : un seul ticket porte "
            "ce comportement ; l'autre le retire, ou le met en `depends_on` et ne garde que son branchement "
            "(ou la définition de terminé, si chaque écran le doit)"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tc.main([str(kb), "--repetes"]), 1)
        self.write("signaler-ligne", "depends_on: [signaler-date]\n", crit(5))  # the owner named: its screen's check stays
        self.assertEqual(tc.repeated_criteria(kb), [])
        self.write("signaler-ligne", "", crit(5, ", [f](../cdc/fondamentaux.md)"))  # two exigences: reported once
        self.assertEqual(len(tc.repeated_criteria(kb)), 1)
        self.write("signaler-date", "state: done\n", crit(2))  # a delivered ticket owns it; the todo one is to fix
        self.assertEqual(len(tc.repeated_criteria(kb)), 1)
        self.write("signaler-ligne", "state: done\n", crit(5))  # both delivered: nothing left to change
        self.assertEqual(tc.repeated_criteria(kb), [])
        self.write("court-a", "", f"{link}\n## Critères d'acceptation\n- CA1 — refus affiché\n")
        self.write("court-b", "", f"{link}\n## Critères d'acceptation\n- CA1 — refus affiché\n")  # too few words to judge
        self.write("autre", "", f"{link}\n## Critères d'acceptation\n- CA1 — Étant donné un fichier de 2 Mo, quand "
                                "l'analyste l'importe, alors 400 lignes sont enregistrées et le journal note l'import.\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tc.main([str(kb), "--repetes"]), 0)

    def test_an_indicator_criterion_states_the_value_the_dashboard_shows(self):
        kb = self.tickets.parent
        (kb / "cdc").mkdir()
        (kb / "cdc" / "pilotage.md").write_text(
            "---\ntype: Exigence\n---\n## Règles de gestion\n- **RG1** — semaine du lundi au dimanche\n"
            "## Indicateurs\n- **IN1** — Places vendues : vendues / ouvertes — source : Réservation — période : semaine — "
            "cible ou seuil : 80 % — action : relancer les élèves\n", encoding="utf-8")
        story = "En tant que gérant,\nLié à : [p](../personnas/p.md), [e](../cdc/pilotage.md)\n## Critères d'acceptation\n"
        p = self.write("tableau", "", story + "- CA1 [IN1] — la tuile affiche les places vendues\n- CA2 [IN2] — inconnu 3\n")
        gaps = tc.gaps(p)
        self.assertIn("CA1 cite IN1 sans la valeur attendue sur le jeu de test (un nombre)", gaps)
        self.assertIn("un critère cite `IN2`, absent de l'exigence liée (ou retiré)", gaps)
        p = self.write("tableau", "", story + "- CA1 [RG1, IN1] — avec 38 places vendues sur 48, la tuile affiche 38 / 48\n")
        self.assertFalse(any("IN1" in g for g in tc.gaps(p)))
        self.assertEqual(tc.rule_coverage(kb), [])

    def test_dependency_ranked_after_its_ticket(self):
        self.write("journal", "priority: 43\n", "")
        self.write("fait", "state: done\n", "")
        p = self.write("pas-moi", "priority: 17\ndepends_on: [journal, fait]\n", "")
        self.assertEqual(tc.late_dependencies(p, tc.split(p.read_text(encoding="utf-8"))[0]),
                         ["(info) dépend de `journal` (priorité 43), classé après lui : le graphe le construit avant quand même"])


if __name__ == "__main__":
    unittest.main()


class CrossReferences(unittest.TestCase):
    """rieki sprint-4: renvois `CAn` vers un critère absent, « Q2/Q3 du rapport de sécurité », un ticket cité par
    une note sans être une dépendance — tous vus seulement au `qa-plan`, six passages de hosa-qa-lead."""

    def setUp(self):
        self.tickets = Path(tempfile.mkdtemp()) / ".hosa" / "kb" / "tickets"
        self.tickets.mkdir(parents=True)
        (self.tickets.parent / "securite").mkdir()
        (self.tickets.parent / "securite" / "modele-menaces.md").write_text("x", encoding="utf-8")
        self.write("lancer-un-nettoyage-et-enregistrer-une-version", crit="- CA1 — a\n- CA2 — b\n")
        self.write("lister-les-versions", crit="- CA1 — a\n")

    def write(self, slug, front="", crit="- CA1 — a\n", note=""):
        p = self.tickets / f"{slug}.md"
        p.write_text(f"---\ntype: Ticket\nstate: todo\n{front}---\n## Critères d'acceptation\n{crit}"
                     f"## Note technique (senior dev)\n{note}", encoding="utf-8")
        return p

    def refs(self, p):
        return tc.cross_references(p, tc.split(p.read_text(encoding="utf-8"))[1])

    def test_a_criterion_cited_in_another_ticket_exists_there(self):
        p = self.write("t", note="- **Règles** : comme le CA11 de lancer-un-nettoyage ; voir "
                                 "[l](lister-les-versions.md) CA9 ; et [l](../tickets/lister-les-versions.md) (CA1)\n")
        self.assertEqual(self.refs(p), [
            "`Note technique (senior dev)` cite CA9 de `lister-les-versions`, qui n'a pas ce critère → corriger le renvoi",
            "`Note technique (senior dev)` cite CA11 de `lancer-un-nettoyage-et-enregistrer-une-version`, qui n'a pas "
            "ce critère → corriger le renvoi"])
        p = self.write("t", crit="- CA1 — comme CA2 de lancer-un-nettoyage, et CA1 à CA2 de lister-les-versions\n")
        self.assertEqual(len(self.refs(p)), 1)  # CA2 of lister is missing, CA2 of the cleaning exists
        self.assertIn("CA2 de `lister-les-versions`", self.refs(p)[0])

    def test_a_note_links_kb_files_and_never_an_agent_report(self):
        p = self.write("t", note="- **Source** : [m](../securite/modele-menaces.md) ; [x](../securite/absent.md) "
                                 "(Q2/Q3 du rapport de sécurité)\n")
        self.assertEqual(self.refs(p), [
            "`Note technique (senior dev)` cite `../securite/absent.md`, absent de la KB → lien à corriger",
            "`Note technique (senior dev)` cite « Q2/Q3 du rapport de sécurité », introuvable dans la KB → citer le "
            "fichier de la KB qui porte la décision"])
        os.environ["HOSA_RENVOIS"] = "0"
        try:
            self.assertEqual(self.refs(p), [])
        finally:
            del os.environ["HOSA_RENVOIS"]

    def test_a_ticket_a_note_uses_comes_before_it(self):
        self.write("mettre-en-file", "depends_on: [lancer]\n")
        self.write("verrou")
        p = self.write("lancer", note="- **Contrat** : appelle `demarrer` de [m](mettre-en-file.md) et le "
                                      "message de [v](verrou.md)\n- **Hors périmètre** : [l](lister-les-versions.md)\n")
        body = tc.split(p.read_text(encoding="utf-8"))[1]
        self.assertEqual(tc.note_tickets(p, body), ["verrou"])  # one coming after it is the planner's, not a gap
        self.assertIn("(info) une note cite `verrou`", " ".join(tc.gaps(p)))
        p = self.write("lancer", "depends_on: [verrou]\n", note="- le message de [v](verrou.md)\n")
        self.assertEqual(tc.note_tickets(p, tc.split(p.read_text(encoding="utf-8"))[1]), [])
