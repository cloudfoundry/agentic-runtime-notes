import pathlib
import unittest

from scripts.generate_research_map import (
    derive_position,
    extract_summary,
    github_url,
    generate_html,
    load_plots,
    load_notes,
    parse_note,
    validate_ratings,
)


PLOT = {"x": {"rating": "maturity"}, "y": {"rating": "platform-impact"}}


class ResearchMapTests(unittest.TestCase):
    def test_parse_note_extracts_metadata_and_research_summary(self):
        text = """---
title: Example
author: A Person
date: 2026-01-01
ratings: {}
---

## Summary

A concise summary.
"""
        note = parse_note(pathlib.Path("research/example.md"), text)
        self.assertEqual(note.title, "Example")
        self.assertEqual(note.kind, "research")
        self.assertEqual(note.summary, "A concise summary.")

    def test_extract_summary_uses_idea_section(self):
        self.assertEqual(
            extract_summary("ideas/example.md", "## The idea\n\nA useful spark.\n"),
            "A useful spark.",
        )

    def test_validate_ratings_rejects_out_of_range_value(self):
        with self.assertRaisesRegex(ValueError, "0..100"):
            validate_ratings({"maturity": {"value": 101, "note": "reason"}})

    def test_validate_ratings_requires_note(self):
        with self.assertRaisesRegex(ValueError, "non-empty note"):
            validate_ratings({"maturity": {"value": 50, "note": ""}})

    def test_derive_position_maps_x_and_y_from_named_ratings(self):
        ratings = {
            "maturity": {"value": 55, "note": "reason"},
            "platform-impact": {"value": 80, "note": "reason"},
        }
        self.assertEqual(derive_position(ratings, PLOT), {"x": 55, "y": 80})

    def test_missing_plot_rating_is_unplaced(self):
        self.assertIsNone(
            derive_position({"maturity": {"value": 55, "note": "reason"}}, PLOT)
        )

    def test_github_url_uses_canonical_repository_path(self):
        self.assertEqual(
            github_url(pathlib.Path("research/langgraph.md")),
            "https://github.com/cloudfoundry/agentic-runtime-notes/blob/main/research/langgraph.md",
        )

    def test_all_current_notes_have_initial_ratings_and_justifications(self):
        required = {"platform-impact", "maturity", "novelty", "actionability"}
        notes = load_notes()
        self.assertEqual(len(notes), 41)
        for note in notes:
            ratings = note.metadata["ratings"]
            self.assertTrue(required.issubset(ratings), note.path)
            for name in required:
                self.assertIsInstance(ratings[name]["value"], int)
                self.assertIn(ratings[name]["value"], range(101))
                self.assertTrue(ratings[name]["note"].strip(), note.path)

    def test_generated_html_contains_markers_dialog_and_source_links(self):
        html = generate_html(load_notes(), load_plots())
        self.assertEqual(html.count('class="marker '), 41)
        self.assertIn('<dialog id="detail">', html)
        self.assertIn("Read the full Markdown note on GitHub", html)
        self.assertIn("Initial working-group ratings", html)


if __name__ == "__main__":
    unittest.main()
