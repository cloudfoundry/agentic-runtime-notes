import pathlib
import unittest

from scripts.generate_research_map import (
    derive_position,
    extract_summary,
    github_url,
    generate_html,
    group_payload,
    load_plots,
    load_notes,
    parse_note,
    validate_ratings,
)


PLOT = {"x": {"rating": "maturity"}, "y": {"rating": "platform-impact"}}


class ResearchMapTests(unittest.TestCase):
    def test_group_payload_combines_only_exact_positions(self):
        payload = [
            {"id": "a", "position": {"x": 50, "y": 40}},
            {"id": "b", "position": {"x": 50, "y": 40}},
            {"id": "c", "position": {"x": 51, "y": 40}},
        ]
        groups = group_payload(payload)
        self.assertEqual([item["id"] for item in groups[(50, 40)]], ["a", "b"])
        self.assertEqual([item["id"] for item in groups[(51, 40)]], ["c"])

    def test_group_payload_leaves_unplaced_items_out_of_coordinate_groups(self):
        self.assertEqual(group_payload([{"id": "a", "position": None}]), {})

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
        self.assertGreater(html.count('class="marker '), 0)
        self.assertIn('<dialog id="detail">', html)
        self.assertIn("Read the full Markdown note on GitHub", html)
        self.assertIn("Initial working-group ratings", html)

    def test_generated_html_contains_one_matrix_for_each_configured_plot(self):
        html = generate_html(load_notes(), load_plots())
        for plot in load_plots().values():
            self.assertIn(plot["title"], html)
        self.assertEqual(html.count('class="map"'), len(load_plots()))

    def test_generated_html_has_one_dialog_close_button(self):
        html = generate_html(load_notes(), load_plots())
        self.assertEqual(html.count('class="close"'), 1)

    def test_generated_html_contains_cluster_marker_and_picker(self):
        html = generate_html(load_notes(), load_plots())
        self.assertIn('data-cluster=', html)
        self.assertIn('function showCluster', html)
        self.assertIn('picker-item', html)

    def test_generated_html_wires_singletons_and_close_button(self):
        html = generate_html(load_notes(), load_plots())
        self.assertIn("show(plots[m.dataset.plot].find(n=>n.id===m.dataset.id))", html)
        self.assertIn("document.querySelector('.close').onclick=()=>dialog.close()", html)

    def test_generated_html_styles_note_lists_and_picker_items(self):
        html = generate_html(load_notes(), load_plots())
        self.assertIn(".unplaced li", html)
        self.assertIn(".picker-item", html)
        self.assertIn("font:inherit", html)

    def test_unplaced_list_distinguishes_ideas_and_research(self):
        notes = [next(note for note in load_notes() if note.kind == kind) for kind in ("research", "idea")]
        notes[0].metadata["ratings"].pop("maturity")
        notes[1].metadata["ratings"].pop("maturity")
        html = generate_html(notes, load_plots())
        self.assertIn('class="note-kind research"', html)
        self.assertIn('class="note-kind idea"', html)
        self.assertIn('class="note-type research"', html)
        self.assertIn('class="note-type idea"', html)

    def test_picker_items_distinguish_ideas_and_research(self):
        html = generate_html(load_notes(), load_plots())
        self.assertIn('class="picker-kind ${note.kind}"', html)
        self.assertIn('.picker-kind.research', html)
        self.assertIn('.picker-kind.idea', html)


if __name__ == "__main__":
    unittest.main()
