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


if __name__ == "__main__":
    unittest.main()
