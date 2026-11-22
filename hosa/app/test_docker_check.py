"""docker_check.py: a sprint project is checked against its worktree, with that worktree's compose files only."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "infra" / "scripts" / "docker_check.py"
spec = importlib.util.spec_from_file_location("docker_check", SCRIPT)
dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc)

ROOT = "C:/dev/p"
WT = f"{ROOT}/.worktrees/sprint/s1"


def container(name, workdir, configs):
    return {"Name": f"/{name}", "State": {"Running": True}, "Mounts": [],
            "Config": {"Labels": {dc.PROJECT: "p-sprint-s1", dc.WORKDIR: workdir, dc.CONFIG: ",".join(configs)}}}


class DockerCheck(unittest.TestCase):
    def test_sprint_checked_against_the_root_fails(self):
        self.assertIn("projet de sprint", dc.problems([container("app", WT, [f"{WT}/docker-compose.yml"])], ROOT)[0])

    def test_pilot2_case(self):
        found = dc.problems([
            container("mailpit", ROOT, [f"{ROOT}/docker-compose.yml"]),
            container("db", WT, [f"{WT}/docker-compose.yml", "C:/Temp/scratchpad/sans-port-db.yml"]),
        ], WT)
        self.assertEqual(len(found), 3)  # mailpit: started from the root, compose file of the root; db: the override
        self.assertTrue(any("sans-port-db.yml" in f for f in found))

    def test_clean_sprint(self):
        self.assertEqual(dc.problems([container("app", WT, [f"{WT}/docker-compose.yml"])], WT), [])



def image(project, tags, size=6.6e9):
    return {"Id": "sha256:" + "a" * 64, "RepoTags": tags, "Size": size, "Config": {"Labels": {dc.PROJECT: project}}}


class Orphans(unittest.TestCase):
    """rieki: 6 images of 6.6 GB, sprints 1-3 merged long ago, and a `rieki-ux` started from the root."""

    def find(self, projects, images, live=()):
        return dc.orphans(projects, "C:/dev/rieki", images,
                          exists=lambda f: any(f.replace("\\", "/").endswith(l) for l in live))

    def test_image_of_a_merged_sprint_is_removed(self):
        found = self.find([], [image("rieki-sprint-sprint-1", ["rieki-sprint-sprint-1-app:latest"])])
        self.assertEqual([(o["sur"], o["cmd"]) for o in found],
                         [(True, [["image", "rm", "rieki-sprint-sprint-1-app:latest"]])])

    def test_image_of_the_live_sprint_and_of_the_base_stay(self):
        sprint4 = {"Name": "rieki-sprint-sprint-4", "ConfigFiles": "C:/dev/rieki/.worktrees/sprint/sprint-4/docker-compose.yml"}
        base = {"Name": "rieki", "ConfigFiles": "C:/dev/rieki/docker-compose.yml"}
        self.assertEqual(self.find([sprint4, base], [image("rieki-sprint-sprint-4", ["x:latest"]),
                                                     image("rieki", ["rieki-app:latest"])],
                                   live=[".worktrees/sprint/sprint-4"]), [])

    def test_image_whose_worktree_still_exists_stays(self):
        self.assertEqual(self.find([], [image("rieki-sprint-s5", ["y:latest"])], live=[".worktrees/sprint/s5"]), [])

    def test_dangling_image_of_the_base_is_removed(self):
        found = self.find([], [image("rieki", [])])
        self.assertTrue(found[0]["sur"])
        self.assertEqual(found[0]["cmd"][0][:2], ["image", "rm"])

    def test_extra_project_from_the_root_is_asked_never_cleaned(self):
        ux = {"Name": "rieki-ux", "ConfigFiles": "C:/dev/rieki/docker-compose.yml"}
        found = self.find([ux], [])
        self.assertEqual([(o["nom"], o["sur"]) for o in found], [("rieki-ux", False)])
        self.assertIn("à confirmer", dc.line(found[0]))

    def test_environment_on_a_vanished_worktree_is_removed(self):
        gone = {"Name": "rieki-sprint-s2", "ConfigFiles": "C:/dev/rieki/.worktrees/sprint/s2/docker-compose.yml"}
        self.assertEqual([o["sur"] for o in self.find([gone], [])], [True])

    def test_other_projects_images_are_never_touched(self):
        self.assertEqual(self.find([], [image("junbi", []), image("riekiplus-sprint-a", ["z:latest"])]), [])

    def test_base_project_follows_compose_naming(self):
        self.assertEqual(dc.base_project(r"C:\dev\Japon2026"), "japon2026")


if __name__ == "__main__":
    unittest.main()
