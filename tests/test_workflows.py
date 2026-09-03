from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_COMMANDS = [
    'pip install "pyyaml==6.0.2"',
    "python .github/scripts/validate_notes.py",
    "python scripts/summarize_ratings.py --check",
    "python -m unittest discover -s tests",
    "python scripts/generate_research_map.py",
    "git diff --exit-code -- generated/research-map.html",
]
ACTION_PINS = {
    "actions/checkout": ("11d5960a326750d5838078e36cf38b85af677262", "v4.4.0"),
    "actions/setup-python": ("a26af69be951a213d495a4c3e4e4022e16d87065", "v5.6.0"),
    "actions/configure-pages": ("983d7736d9b0ae728b81ab479565c72886d7745b", "v5.0.0"),
    "actions/upload-pages-artifact": ("56afc609e74202658d3ffba0e8f6dda462b719fa", "v3.0.1"),
    "actions/deploy-pages": ("d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e", "v4.0.5"),
}


def assert_actions_are_pinned(test_case, workflow_path, workflow):
    workflow_text = workflow_path.read_text(encoding="utf-8")
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if "uses" not in step:
                continue
            action, reference = step["uses"].split("@", 1)
            sha, version = ACTION_PINS[action]
            test_case.assertEqual(reference, sha)
            test_case.assertIn(f"uses: {action}@{sha} # {version}", workflow_text)


class LintWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / ".github/workflows/lint.yml").open(encoding="utf-8") as workflow_file:
            cls.workflow = yaml.safe_load(workflow_file)
        cls.workflow_path = ROOT / ".github/workflows/lint.yml"

    def test_validation_commands_run_in_order(self):
        run_steps = [
            step for step in self.workflow["jobs"]["validate"]["steps"] if "run" in step
        ]
        commands = [step["run"] for step in run_steps]

        self.assertEqual(
            commands,
            VALIDATION_COMMANDS,
        )
        self.assertEqual(
            [step["name"] for step in run_steps[-2:]],
            ["Generate research map", "Verify generated map is checked in"],
        )

    def test_uses_read_only_permissions_and_immutable_action_pins(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        assert_actions_are_pinned(self, self.workflow_path, self.workflow)

    def test_path_filters_cover_validation_inputs_and_workflows(self):
        triggers = self.workflow.get("on", self.workflow.get(True))
        required_paths = {
            "research/**",
            "ideas/**",
            "scripts/**",
            "generated/**",
            "tests/**",
            ".github/workflows/lint.yml",
            ".github/workflows/pages.yml",
        }

        self.assertEqual(triggers["push"]["branches"], ["main"])
        for event in ("pull_request", "push"):
            with self.subTest(event=event):
                self.assertTrue(required_paths.issubset(triggers[event]["paths"]))


class PagesWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / ".github/workflows/pages.yml").open(encoding="utf-8") as workflow_file:
            cls.workflow = yaml.safe_load(workflow_file)
        cls.workflow_path = ROOT / ".github/workflows/pages.yml"

    def test_deploys_generated_map_from_main(self):
        triggers = self.workflow.get("on", self.workflow.get(True))

        self.assertEqual(self.workflow["name"], "Deploy research map to Pages")
        self.assertEqual(set(triggers), {"push"})
        self.assertEqual(triggers["push"]["branches"], ["main"])
        self.assertEqual(
            set(triggers["push"]["paths"]),
            {
                "research/**",
                "ideas/**",
                "scripts/**",
                "generated/**",
                "tests/**",
                ".github/workflows/pages.yml",
                ".github/workflows/lint.yml",
            },
        )
        self.assertEqual(
            self.workflow["permissions"],
            {"contents": "read"},
        )
        self.assertEqual(
            self.workflow["concurrency"],
            {"group": "pages", "cancel-in-progress": True},
        )

    def test_build_validates_and_packages_generated_map(self):
        steps = self.workflow["jobs"]["build"]["steps"]

        self.assertEqual(self.workflow["jobs"]["build"]["runs-on"], "ubuntu-latest")
        self.assertEqual(self.workflow["jobs"]["build"]["permissions"], {"contents": "read"})
        self.assertEqual(steps[1]["with"]["python-version"], "3.12")
        self.assertEqual(
            [step["run"] for step in steps if "run" in step],
            VALIDATION_COMMANDS
            + ["mkdir _site", "cp generated/research-map.html _site/index.html"],
        )
        self.assertEqual(steps[-1]["with"]["path"], "_site")

    def test_deploy_uses_pages_environment(self):
        deploy = self.workflow["jobs"]["deploy"]

        self.assertEqual(deploy["needs"], "build")
        self.assertEqual(
            deploy["permissions"], {"pages": "write", "id-token": "write"}
        )
        self.assertEqual(
            deploy["environment"],
            {
                "name": "github-pages",
                "url": "${{ steps.deployment.outputs.page_url }}",
            },
        )
        self.assertEqual(
            deploy["steps"],
            [
                {
                    "name": "Deploy to GitHub Pages",
                    "id": "deployment",
                    "uses": f"actions/deploy-pages@{ACTION_PINS['actions/deploy-pages'][0]}",
                }
            ],
        )

    def test_uses_immutable_action_pins(self):
        assert_actions_are_pinned(self, self.workflow_path, self.workflow)


if __name__ == "__main__":
    unittest.main()
