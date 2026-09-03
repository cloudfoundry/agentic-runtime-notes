from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class LintWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / ".github/workflows/lint.yml").open(encoding="utf-8") as workflow_file:
            cls.workflow = yaml.safe_load(workflow_file)

    def test_validation_commands_run_in_order(self):
        run_steps = [
            step for step in self.workflow["jobs"]["validate"]["steps"] if "run" in step
        ]
        commands = [step["run"] for step in run_steps]

        self.assertEqual(
            commands,
            [
                'pip install "pyyaml>=6"',
                "python .github/scripts/validate_notes.py",
                "python scripts/summarize_ratings.py --check",
                "python -m unittest discover -s tests",
                "python scripts/generate_research_map.py",
                "git diff --exit-code -- generated/research-map.html",
            ],
        )
        self.assertEqual(
            [step["name"] for step in run_steps[-2:]],
            ["Generate research map", "Verify generated map is checked in"],
        )

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
            {"contents": "read", "pages": "write", "id-token": "write"},
        )
        self.assertEqual(
            self.workflow["concurrency"],
            {"group": "pages", "cancel-in-progress": True},
        )

    def test_build_validates_and_packages_generated_map(self):
        steps = self.workflow["jobs"]["build"]["steps"]

        self.assertEqual(self.workflow["jobs"]["build"]["runs-on"], "ubuntu-latest")
        self.assertEqual(steps[0]["uses"], "actions/checkout@v4")
        self.assertEqual(steps[1]["uses"], "actions/setup-python@v5")
        self.assertEqual(steps[1]["with"]["python-version"], "3.12")
        self.assertEqual(
            [step["run"] for step in steps if "run" in step],
            [
                'pip install "pyyaml>=6"',
                "python .github/scripts/validate_notes.py",
                "python scripts/summarize_ratings.py --check",
                "python -m unittest discover -s tests",
                "python scripts/generate_research_map.py",
                "git diff --exit-code -- generated/research-map.html",
                "mkdir _site",
                "cp generated/research-map.html _site/index.html",
            ],
        )
        self.assertEqual(steps[-2]["uses"], "actions/configure-pages@v5")
        self.assertEqual(steps[-1]["uses"], "actions/upload-pages-artifact@v3")
        self.assertEqual(steps[-1]["with"]["path"], "_site")

    def test_deploy_uses_pages_environment(self):
        deploy = self.workflow["jobs"]["deploy"]

        self.assertEqual(deploy["needs"], "build")
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
                    "uses": "actions/deploy-pages@v4",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
