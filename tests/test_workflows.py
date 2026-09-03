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


if __name__ == "__main__":
    unittest.main()
