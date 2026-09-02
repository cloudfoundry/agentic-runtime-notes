import html as html_lib
import json
import pathlib
import re
import unittest
from types import SimpleNamespace

from scripts.generate_research_map import (
    PRIMITIVES_PATH,
    derive_position,
    extract_summary,
    github_url,
    generate_html,
    group_payload,
    load_primitives,
    load_plots,
    load_notes,
    parse_note,
    validate_primitives,
    validate_ratings,
)
from scripts.summarize_ratings import summarize_ratings, validate_summary


PLOT = {"x": {"rating": "maturity"}, "y": {"rating": "platform-impact"}}
REQUIRED_RATINGS = ("platform-impact", "maturity", "novelty", "actionability")
PRIMITIVE = {
    "id": "durable-addressable-execution",
    "title": "Durable, Addressable Execution",
    "proposition": "Keep execution durable while compute remains replaceable.",
    "cf_gap": "CF tasks have no durable execution identity or suspend/resume lifecycle.",
    "strategic_decision": "Decide whether CF should own durable execution lifecycle semantics.",
    "poc": "Resume a checkpointed task on replacement compute.",
    "rfc_scope": "Execution identity, lifecycle, events, timers, and retries.",
    "core": ["ideas/durable-tasks-for-cf.md", "research/temporal.md"],
    "supporting": ["research/dapr-agents.md"],
}


def rating_notes(values):
    return [
        SimpleNamespace(metadata={"ratings": ratings})
        for ratings in (
            {
                name: {"value": value, "note": "reason"}
                for name, value in zip(REQUIRED_RATINGS, row)
            }
            for row in values
        )
    ]


def mixed_cluster_fixture():
    paths = [pathlib.Path(f"research/cluster-{index}.md") for index in range(5)]
    notes = [
        SimpleNamespace(
            path=path,
            kind="research",
            title=f"Cluster note {index}",
            summary=f"Summary {index}",
            metadata={
                "ratings": {
                    "maturity": {"value": 42, "note": "reason"},
                    "platform-impact": {"value": 37, "note": "reason"},
                }
            },
        )
        for index, path in enumerate(paths)
    ]
    plot = {
        "title": "Mixed cluster",
        "x": {"rating": "maturity", "label": "Maturity", "low": "Low", "high": "High"},
        "y": {
            "rating": "platform-impact",
            "label": "Platform impact",
            "low": "Low",
            "high": "High",
        },
    }
    primitive = {
        **PRIMITIVE,
        "core": [paths[1].as_posix()],
        "supporting": [paths[3].as_posix()],
    }
    return notes, {"mixed:plot": plot}, [primitive]


class ResearchMapTests(unittest.TestCase):
    def test_load_primitives_loads_the_three_approved_primitives(self):
        primitives = load_primitives()

        self.assertEqual(PRIMITIVES_PATH.name, "platform_primitives.yaml")
        self.assertEqual(
            [primitive["id"] for primitive in primitives],
            [
                "durable-addressable-execution",
                "attested-workload-authority",
                "session-scoped-isolated-execution",
            ],
        )

    def test_validate_primitives_preserves_core_and_supporting_order(self):
        primitive = {**PRIMITIVE, "core": ["b.md", "a.md"], "supporting": ["d.md", "c.md"]}

        validated = validate_primitives([primitive], {"a.md", "b.md", "c.md", "d.md"})

        self.assertEqual(validated[0]["core"], ["b.md", "a.md"])
        self.assertEqual(validated[0]["supporting"], ["d.md", "c.md"])

    def test_validate_primitives_rejects_non_list_configuration(self):
        with self.assertRaisesRegex(ValueError, "non-empty list"):
            validate_primitives({"primitives": [PRIMITIVE]}, set(PRIMITIVE["core"] + PRIMITIVE["supporting"]))

    def test_validate_primitives_rejects_blank_required_fields(self):
        for field in ("id", "title", "proposition", "cf_gap", "strategic_decision", "poc", "rfc_scope"):
            with self.subTest(field=field):
                primitive = {**PRIMITIVE, field: "  "}
                with self.assertRaisesRegex(ValueError, f"non-empty '{field}'"):
                    validate_primitives([primitive], set(PRIMITIVE["core"] + PRIMITIVE["supporting"]))

    def test_validate_primitives_rejects_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate primitive id"):
            validate_primitives([PRIMITIVE, dict(PRIMITIVE)], set(PRIMITIVE["core"] + PRIMITIVE["supporting"]))

    def test_validate_primitives_rejects_empty_core_membership(self):
        with self.assertRaisesRegex(ValueError, "non-empty core"):
            validate_primitives([{**PRIMITIVE, "core": []}], set(PRIMITIVE["supporting"]))

    def test_validate_primitives_rejects_duplicate_membership(self):
        primitive = {**PRIMITIVE, "supporting": [PRIMITIVE["core"][0]]}
        with self.assertRaisesRegex(ValueError, "duplicate note path"):
            validate_primitives([primitive], set(PRIMITIVE["core"]))

    def test_validate_primitives_rejects_unknown_note(self):
        with self.assertRaisesRegex(ValueError, "unknown note path.*research/temporal.md"):
            validate_primitives([PRIMITIVE], {"ideas/durable-tasks-for-cf.md", "research/dapr-agents.md"})

    def test_summarize_ratings_reports_distribution_correlations_and_quadrants(self):
        notes = rating_notes(
            [
                (10, 90, 10, 10),
                (30, 70, 30, 70),
                (50, 50, 50, 50),
                (70, 30, 70, 30),
                (90, 10, 90, 90),
            ]
        )

        summary = summarize_ratings(notes)

        self.assertEqual(
            summary["ratings"]["platform-impact"],
            {
                "count": 5,
                "minimum": 10,
                "maximum": 90,
                "median": 50,
                "first_quartile": 30.0,
                "third_quartile": 70.0,
                "distinct": 5,
                "duplicates": 0,
            },
        )
        self.assertEqual(summary["correlations"]["platform-impact:maturity"], -1.0)
        self.assertEqual(summary["correlations"]["platform-impact:novelty"], 1.0)
        self.assertEqual(len(summary["correlations"]), 6)
        self.assertEqual(
            summary["matrices"]["platform-impact-maturity"],
            {"low-low": 1, "low-high": 2, "high-low": 2, "high-high": 0},
        )
        self.assertEqual(len(summary["matrices"]), 6)

    def test_summarize_ratings_reports_duplicate_count(self):
        summary = summarize_ratings(
            rating_notes([(10, 10, 10, 10), (10, 10, 10, 10), (20, 20, 20, 20)])
        )

        self.assertEqual(summary["ratings"]["maturity"]["duplicates"], 1)

    def test_validate_summary_checks_all_missing_ratings_before_sparse_distribution(self):
        notes = rating_notes([(50, 50, 50, 50)])
        notes[0].metadata["ratings"].pop("novelty")

        summary = summarize_ratings(notes)

        with self.assertRaisesRegex(ValueError, "missing required rating.*novelty"):
            validate_summary(summary)

    def test_validate_summary_checks_all_malformed_ratings_before_sparse_distribution(self):
        notes = rating_notes([(50, 50, 50, 50), (60, 60, 60, 60)])
        notes[0].metadata["ratings"]["novelty"] = {}

        summary = summarize_ratings(notes)

        with self.assertRaisesRegex(ValueError, "missing required rating.*novelty"):
            validate_summary(summary)

    def test_validate_summary_rejects_missing_required_rating(self):
        notes = rating_notes([(value, value, value, value) for value in (10, 30, 50, 70, 90)])
        notes[0].metadata["ratings"].pop("novelty")
        summary = summarize_ratings(notes)
        with self.assertRaisesRegex(ValueError, "missing required rating.*novelty"):
            validate_summary(summary)

    def test_validate_summary_rejects_fewer_than_five_distinct_values(self):
        summary = summarize_ratings(
            rating_notes([(10, 10, 10, 10), (20, 20, 20, 20)] * 3)
        )
        with self.assertRaisesRegex(ValueError, "fewer than 5 distinct values"):
            validate_summary(summary)

    def test_validate_summary_rejects_values_strictly_on_one_side_of_midpoint(self):
        for values, side in (
            ((10, 20, 30, 40, 45), "below"),
            ((55, 60, 70, 80, 90), "above"),
        ):
            with self.subTest(side=side):
                summary = summarize_ratings(
                    rating_notes([(value, value, value, value) for value in values])
                )
                with self.assertRaisesRegex(ValueError, f"strictly {side} 50"):
                    validate_summary(summary)

    def test_validate_summary_rejects_boundary_without_values_on_both_sides(self):
        for values, side in (
            ((10, 20, 30, 40, 50), "below"),
            ((50, 60, 70, 80, 90), "above"),
        ):
            with self.subTest(side=side):
                summary = summarize_ratings(
                    rating_notes([(value, value, value, value) for value in values])
                )
                with self.assertRaisesRegex(ValueError, f"strictly {side} 50"):
                    validate_summary(summary)

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
        for note in notes:
            ratings = note.metadata["ratings"]
            self.assertEqual(set(ratings), required, note.path)
            for name in required:
                self.assertIsInstance(ratings[name]["value"], int)
                self.assertIn(ratings[name]["value"], range(101))
                self.assertTrue(ratings[name]["note"].strip(), note.path)

    def test_generated_html_contains_markers_dialog_and_source_links(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        self.assertGreater(html.count('class="marker '), 0)
        self.assertIn('<dialog id="detail">', html)
        self.assertIn("Read the full Markdown note on GitHub", html)
        self.assertIn("Recalibrated working-group ratings", html)

    def test_generated_html_contains_one_matrix_for_each_configured_plot(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        for plot in load_plots().values():
            self.assertIn(plot["title"], html)
        self.assertEqual(html.count('class="map"'), len(load_plots()))

    def test_generated_html_contains_primitive_card_controls_and_details(self):
        primitives = load_primitives()
        html = generate_html(load_notes(), load_plots(), primitives)

        self.assertEqual(html.count('class="primitive-select"'), 3)
        self.assertEqual(html.count('aria-pressed="false"'), 3)
        self.assertIn('class="show-all"', html)
        self.assertIn('>Show all</button>', html)
        for primitive in primitives:
            self.assertIn(f'data-primitive="{primitive["id"]}"', html)
            self.assertIn(primitive["proposition"], html)
            self.assertIn(primitive["strategic_decision"], html)
            self.assertIn(primitive["cf_gap"], html)
            self.assertIn(primitive["poc"], html)
            self.assertIn(primitive["rfc_scope"], html)
            for path in primitive["core"] + primitive["supporting"]:
                self.assertIn(f'href="{github_url(pathlib.Path(path))}"', html)

    def test_generated_html_contains_accessible_matrix_tabs_and_panels(self):
        plots = load_plots()
        html = generate_html(load_notes(), plots, load_primitives())

        self.assertEqual(html.count('role="tablist"'), 1)
        self.assertEqual(html.count(' role="tab" aria-selected='), 6)
        self.assertEqual(html.count('role="tabpanel"'), 6)
        self.assertEqual(html.count('role="tab" aria-selected="true"'), 1)
        self.assertEqual(html.count('role="tab" aria-selected="false"'), 5)
        for index, plot_id in enumerate(plots):
            selected = "true" if index == 0 else "false"
            hidden = "" if index == 0 else " hidden"
            self.assertIn(
                f'id="tab-{plot_id}" role="tab" aria-selected="{selected}" '
                f'aria-controls="panel-{plot_id}"',
                html,
            )
            self.assertIn(
                f'id="panel-{plot_id}" class="matrix" role="tabpanel" '
                f'aria-labelledby="tab-{plot_id}"{hidden}',
                html,
            )

    def test_generated_html_embeds_primitive_membership_once_and_stable_control_ids(self):
        primitives = load_primitives()
        html = generate_html(load_notes(), load_plots(), primitives)

        self.assertEqual(html.count("const primitiveMemberships="), 1)
        self.assertIn(
            '"ideas/durable-tasks-for-cf.md": {"durable-addressable-execution": "core"}',
            html,
        )
        for primitive in primitives:
            self.assertIn(f'id="primitive-{primitive["id"]}"', html)

    def test_generated_html_persistently_refreshes_marker_highlighting(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn("let selectedPrimitive=null", html)
        self.assertIn("function selectPrimitive", html)
        self.assertIn("function clearPrimitiveSelection", html)
        self.assertIn("function refreshMarkers", html)
        self.assertIn("aria-pressed',String", html)
        self.assertIn("classList.toggle('related'", html)
        self.assertIn("classList.toggle('dimmed'", html)
        self.assertIn("--selected-accent", html)
        marker_buttons = re.findall(r'<button class="marker [^"]+"[^>]*>', html)
        self.assertTrue(marker_buttons)
        for marker in marker_buttons:
            self.assertNotIn(" disabled", marker)
            self.assertNotIn('tabindex="-1"', marker)

    def test_dimmed_markers_restore_visible_keyboard_focus(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertRegex(
            html,
            r"\.marker\.dimmed:focus-visible\s*\{\s*opacity:1;"
            r"\s*outline:3px solid #fff;\s*outline-offset:3px;\s*\}",
        )

    def test_generated_html_shows_selected_primitive_relationship_in_note_detail(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn("function relationshipBadge", html)
        self.assertIn('class="primitive-badge"', html)
        self.assertIn("relationship==='core'?'Core':'Supporting'", html)

    def test_generated_html_has_one_dialog_close_button(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        self.assertEqual(html.count('class="close"'), 1)

    def test_generated_html_contains_cluster_marker_and_picker(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        self.assertIn('data-cluster=', html)
        self.assertIn('function showCluster', html)
        self.assertIn('picker-item', html)

    def test_mixed_cluster_embeds_ordered_note_ids_and_updates_selected_count(self):
        notes, plots, primitives = mixed_cluster_fixture()

        html = generate_html(notes, plots, primitives)

        marker = re.search(r'<button class="marker cluster"[^>]+>5</button>', html).group(0)
        note_ids = [note.path.as_posix() for note in notes]
        encoded_ids = html_lib.escape(json.dumps(note_ids), quote=True)
        self.assertIn(f'data-note-ids="{encoded_ids}"', marker)
        self.assertIn("const relatedCount=noteIds.filter", html)
        self.assertIn("m.textContent=relatedCount?`${relatedCount}/${noteIds.length}`:String(noteIds.length)", html)
        self.assertIn("m.classList.toggle('related',relatedCount>0)", html)
        self.assertIn("m.classList.toggle('dimmed',Boolean(selectedPrimitive&&!relatedCount))", html)

    def test_mixed_cluster_updates_and_restores_accessible_count(self):
        notes, plots, primitives = mixed_cluster_fixture()

        html = generate_html(notes, plots, primitives)

        self.assertIn('aria-label="5 notes at this position"', html)
        self.assertIn(
            "m.setAttribute('aria-label',relatedCount?`${relatedCount} of ${noteIds.length} related notes at this position`:`${noteIds.length} notes at this position`)",
            html,
        )

    def test_mixed_cluster_picker_sorts_a_copy_related_first_and_labels_relationships(self):
        notes, plots, primitives = mixed_cluster_fixture()

        html = generate_html(notes, plots, primitives)

        self.assertIn("const ordered=selectedPrimitive?[...items.filter(isRelated),...items.filter(note=>!isRelated(note))]:[...items]", html)
        self.assertIn("${relationshipBadge(note)}", html)
        self.assertIn("const noteIds=JSON.parse(m.dataset.noteIds)", html)
        self.assertIn("noteIds.map(id=>plots[m.dataset.plot].find(note=>note.id===id))", html)
        self.assertNotIn("m.dataset.cluster.split", html)

    def test_generated_html_wires_singletons_and_close_button(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        self.assertIn("show(plots[m.dataset.plot].find(n=>n.id===m.dataset.id))", html)
        self.assertIn("document.querySelector('.close').onclick=()=>dialog.close()", html)

    def test_generated_html_styles_note_lists_and_picker_items(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        self.assertIn(".unplaced li", html)
        self.assertIn(".picker-item", html)
        self.assertIn("font:inherit", html)

    def test_unplaced_list_distinguishes_ideas_and_research(self):
        notes = [next(note for note in load_notes() if note.kind == kind) for kind in ("research", "idea")]
        notes[0].metadata["ratings"].pop("maturity")
        notes[1].metadata["ratings"].pop("maturity")
        html = generate_html(notes, load_plots(), load_primitives())
        self.assertIn('class="note-kind research"', html)
        self.assertIn('class="note-kind idea"', html)
        self.assertIn('class="note-type research"', html)
        self.assertIn('class="note-type idea"', html)

    def test_picker_items_distinguish_ideas_and_research(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        self.assertIn('class="picker-kind ${note.kind}"', html)
        self.assertIn('.picker-kind.research', html)
        self.assertIn('.picker-kind.idea', html)


if __name__ == "__main__":
    unittest.main()
