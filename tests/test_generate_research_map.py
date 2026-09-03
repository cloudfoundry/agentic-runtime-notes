import html as html_lib
import json
import pathlib
import re
import unittest
from types import SimpleNamespace

from scripts.generate_research_map import (
    FOCUS_USE_CASES_PATH,
    PRIMITIVES_PATH,
    derive_position,
    extract_summary,
    github_url,
    generate_html,
    group_payload,
    load_focus_use_cases,
    load_primitives,
    load_plots,
    load_notes,
    parse_note,
    validate_focus_use_cases,
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
PRIMITIVE_IDS = {
    "durable-addressable-execution",
    "attested-workload-authority",
    "session-scoped-isolated-execution",
}
FOCUS_USE_CASE = {
    "id": "cf-hosted-coding-harnesses",
    "title": "CF-hosted coding harnesses",
    "workshop_outcome": "Determine the minimum CF platform contract for hosted coding harnesses.",
    "primary_actor": "A developer deploying a coding harness to Cloud Foundry.",
    "beneficiary": "A software team using the harness to change a repository.",
    "lifecycle": "Stage an environment, start a session, execute tools, suspend it, and resume it.",
    "authority_boundary": "The harness delegates only scoped repository and tool access.",
    "unique_capabilities": ["Reusable staged environments", "Resumable isolated sessions"],
    "failure_domain": "A failed sandbox must not lose the session workspace or affect another session.",
    "poc": "Run and resume two isolated coding sessions from one staged environment.",
    "rfc_decisions": ["Session resource and lifecycle", "Workspace and network policy"],
    "core": ["ideas/per-session-sandboxes.md", "research/k8s-agent-sandbox.md"],
    "supporting": ["research/firecracker-microvm.md"],
    "primitive_applicability": {
        "durable-addressable-execution": "supporting",
        "attested-workload-authority": "core",
        "session-scoped-isolated-execution": "core",
    },
}


def focus_use_cases(first=FOCUS_USE_CASE):
    return [
        first,
        {**FOCUS_USE_CASE, "id": "user-facing-agentic-applications"},
    ]


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
        "supporting": [paths[2].as_posix(), paths[4].as_posix()],
    }
    use_case = {
        **FOCUS_USE_CASE,
        "core": [paths[0].as_posix(), paths[2].as_posix()],
        "supporting": [paths[4].as_posix()],
    }
    return notes, {"mixed:plot": plot}, [primitive], focus_use_cases(use_case)


class ResearchMapTests(unittest.TestCase):
    def test_load_focus_use_cases_loads_the_two_approved_use_cases(self):
        use_cases = load_focus_use_cases()

        self.assertEqual(FOCUS_USE_CASES_PATH.name, "focus_use_cases.yaml")
        self.assertEqual(
            [use_case["id"] for use_case in use_cases],
            ["cf-hosted-coding-harnesses", "user-facing-agentic-applications"],
        )

    def test_coding_harness_use_case_covers_edit_to_trusted_deployment_lifecycle(self):
        use_case = load_focus_use_cases()[0]
        narrative = " ".join(
            str(use_case[field])
            for field in (
                "workshop_outcome",
                "lifecycle",
                "authority_boundary",
                "unique_capabilities",
                "failure_domain",
                "poc",
                "rfc_decisions",
            )
        ).lower()

        for required_phrase in (
            "mutable edit/test",
            "candidate artifact",
            "trusted deployment broker",
            "target, policy, provenance, and approval",
            "package, build, deployment, and revision",
            "capi, git, model, and package-registry credentials",
            "stale-base",
            "concurrency",
            "rollback",
            "audit",
        ):
            with self.subTest(required_phrase=required_phrase):
                self.assertIn(required_phrase, narrative)

    def test_validate_focus_use_cases_preserves_use_case_and_membership_order(self):
        first = {
            **FOCUS_USE_CASE,
            "core": ["b.md", "a.md"],
            "supporting": ["d.md", "c.md"],
        }

        validated = validate_focus_use_cases(
            focus_use_cases(first),
            {"a.md", "b.md", "c.md", "d.md", *FOCUS_USE_CASE["core"], *FOCUS_USE_CASE["supporting"]},
            PRIMITIVE_IDS,
        )

        self.assertEqual([item["id"] for item in validated], [first["id"], "user-facing-agentic-applications"])
        self.assertEqual(validated[0]["core"], ["b.md", "a.md"])
        self.assertEqual(validated[0]["supporting"], ["d.md", "c.md"])

    def test_validate_focus_use_cases_requires_exactly_two_approved_ids(self):
        known_paths = set(FOCUS_USE_CASE["core"] + FOCUS_USE_CASE["supporting"])
        with self.assertRaisesRegex(ValueError, "exactly 2"):
            validate_focus_use_cases([FOCUS_USE_CASE], known_paths, PRIMITIVE_IDS)
        with self.assertRaisesRegex(ValueError, "approved focus use case ids"):
            validate_focus_use_cases(
                focus_use_cases({**FOCUS_USE_CASE, "id": "another-use-case"}), known_paths, PRIMITIVE_IDS
            )

    def test_validate_focus_use_cases_rejects_invalid_required_fields(self):
        known_paths = set(FOCUS_USE_CASE["core"] + FOCUS_USE_CASE["supporting"])
        string_fields = (
            "id", "title", "workshop_outcome", "primary_actor", "beneficiary", "lifecycle",
            "authority_boundary", "failure_domain", "poc",
        )
        list_fields = ("unique_capabilities", "rfc_decisions")
        for field in string_fields:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, f"non-empty '{field}'"):
                validate_focus_use_cases(focus_use_cases({**FOCUS_USE_CASE, field: "  "}), known_paths, PRIMITIVE_IDS)
        for field in list_fields:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, f"non-empty '{field}'"):
                validate_focus_use_cases(focus_use_cases({**FOCUS_USE_CASE, field: []}), known_paths, PRIMITIVE_IDS)

    def test_validate_focus_use_cases_rejects_duplicate_ids(self):
        known_paths = set(FOCUS_USE_CASE["core"] + FOCUS_USE_CASE["supporting"])
        with self.assertRaisesRegex(ValueError, "duplicate focus use case id"):
            validate_focus_use_cases([FOCUS_USE_CASE, dict(FOCUS_USE_CASE)], known_paths, PRIMITIVE_IDS)

    def test_validate_focus_use_cases_rejects_empty_core_membership(self):
        with self.assertRaisesRegex(ValueError, "non-empty core"):
            validate_focus_use_cases(focus_use_cases({**FOCUS_USE_CASE, "core": []}), set(FOCUS_USE_CASE["supporting"]), PRIMITIVE_IDS)

    def test_validate_focus_use_cases_rejects_duplicate_membership(self):
        use_case = {**FOCUS_USE_CASE, "supporting": [FOCUS_USE_CASE["core"][0]]}
        with self.assertRaisesRegex(ValueError, "duplicate note path"):
            validate_focus_use_cases(focus_use_cases(use_case), set(FOCUS_USE_CASE["core"]), PRIMITIVE_IDS)

    def test_validate_focus_use_cases_rejects_unknown_note(self):
        known_paths = {FOCUS_USE_CASE["core"][0], *FOCUS_USE_CASE["supporting"]}
        with self.assertRaisesRegex(ValueError, "unknown note path.*research/k8s-agent-sandbox.md"):
            validate_focus_use_cases(focus_use_cases(), known_paths, PRIMITIVE_IDS)

    def test_validate_focus_use_cases_rejects_unknown_or_missing_primitive_ids(self):
        known_paths = set(FOCUS_USE_CASE["core"] + FOCUS_USE_CASE["supporting"])
        applicability = {**FOCUS_USE_CASE["primitive_applicability"]}
        applicability.pop("attested-workload-authority")
        applicability["unknown-primitive"] = "core"
        with self.assertRaisesRegex(ValueError, "primitive applicability must contain exactly"):
            validate_focus_use_cases(
                focus_use_cases({**FOCUS_USE_CASE, "primitive_applicability": applicability}),
                known_paths,
                PRIMITIVE_IDS,
            )

    def test_validate_focus_use_cases_rejects_invalid_applicability(self):
        known_paths = set(FOCUS_USE_CASE["core"] + FOCUS_USE_CASE["supporting"])
        applicability = {**FOCUS_USE_CASE["primitive_applicability"], "attested-workload-authority": "optional"}
        with self.assertRaisesRegex(ValueError, "invalid applicability.*optional"):
            validate_focus_use_cases(
                focus_use_cases({**FOCUS_USE_CASE, "primitive_applicability": applicability}),
                known_paths,
                PRIMITIVE_IDS,
            )

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
        primitives = [
            primitive,
            {**PRIMITIVE, "id": "second"},
            {**PRIMITIVE, "id": "third"},
        ]

        validated = validate_primitives(
            primitives,
            {"a.md", "b.md", "c.md", "d.md", *PRIMITIVE["core"], *PRIMITIVE["supporting"]},
        )

        self.assertEqual(validated[0]["core"], ["b.md", "a.md"])
        self.assertEqual(validated[0]["supporting"], ["d.md", "c.md"])

    def test_validate_primitives_rejects_non_list_configuration(self):
        with self.assertRaisesRegex(ValueError, "non-empty list"):
            validate_primitives({"primitives": [PRIMITIVE]}, set(PRIMITIVE["core"] + PRIMITIVE["supporting"]))

    def test_validate_primitives_requires_exactly_three_initial_primitives(self):
        primitives = load_primitives()[:2]
        known_paths = {path for primitive in primitives for path in primitive["core"] + primitive["supporting"]}

        with self.assertRaisesRegex(ValueError, "exactly 3"):
            validate_primitives(primitives, known_paths)

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
        self.assertIn('<dialog id="detail"', html)
        self.assertIn("Read the full Markdown note on GitHub", html)
        self.assertIn("summarizes the workshop results", html)

    def test_generated_html_presents_workshop_results_in_outcome_hierarchy(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn("Workshop results", html)
        self.assertNotIn("seed discussion", html.lower())
        self.assertNotIn("workshop input", html.lower())
        use_case_position = html.index('class="use-case-grid"')
        primitive_position = html.index('class="primitive-grid"')
        tabs_position = html.index('class="matrix-tabs"')
        self.assertLess(use_case_position, primitive_position)
        self.assertLess(primitive_position, tabs_position)
        self.assertEqual(html.count('class="use-case-card"'), 2)
        self.assertEqual(html.count('class="primitive-card"'), 3)

    def test_generated_html_contains_use_case_controls_and_expandable_results(self):
        use_cases = load_focus_use_cases()
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertEqual(html.count('class="use-case-select"'), 2)
        self.assertEqual(html.count('class="use-case-select" type="button"'), 2)
        self.assertEqual(html.count('use-case-show-all"'), 1)
        self.assertEqual(html.count('primitive-show-all"'), 1)
        for use_case in use_cases:
            self.assertIn(
                f'data-use-case="{use_case["id"]}" aria-pressed="false"', html
            )
            self.assertIn(use_case["title"], html)
            self.assertIn(html_lib.escape(use_case["workshop_outcome"]), html)
            self.assertIn(html_lib.escape(use_case["poc"]), html)
            for value in (
                use_case["primary_actor"],
                use_case["beneficiary"],
                use_case["lifecycle"],
                use_case["authority_boundary"],
                use_case["failure_domain"],
            ):
                self.assertIn(html_lib.escape(value), html)
            for value in use_case["unique_capabilities"] + use_case["rfc_decisions"]:
                self.assertIn(html_lib.escape(value), html)
            for primitive_id, applicability in use_case["primitive_applicability"].items():
                self.assertIn(f'data-primitive-applicability="{primitive_id}"', html)
                self.assertIn(f'>{applicability.title()}</span>', html)
            for path in use_case["core"] + use_case["supporting"]:
                self.assertIn(f'href="{github_url(pathlib.Path(path))}"', html)

    def test_generated_html_styles_use_cases_responsively_with_dark_card_language(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn(".use-case-grid { display:grid", html)
        self.assertIn(".use-case-card { min-width:0; background:#15211e", html)
        self.assertIn(".use-case-details summary", html)
        self.assertIn("@media(max-width:800px) { .use-case-grid", html)

    def test_generated_html_escapes_all_dynamic_dialog_content(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn("function escapeHtml(value)", html)
        for expression in (
            "escapeHtml(note.kind)",
            "escapeHtml(note.title)",
            "escapeHtml(note.summary)",
            "escapeHtml(t)",
            "escapeHtml(name)",
            "escapeHtml(r.value)",
            "escapeHtml(r.note)",
            "escapeHtml(note.url)",
        ):
            self.assertIn(expression, html)

    def test_hostile_dynamic_content_is_not_emitted_as_raw_executable_markup(self):
        attack = '<img src=x onerror="alert(1)">'
        note = SimpleNamespace(
            path=pathlib.Path("research/hostile.md"),
            kind=attack,
            title=attack,
            summary=attack,
            metadata={
                "tags": [attack],
                "ratings": {
                    "maturity": {"value": 50, "note": attack},
                    "platform-impact": {"value": 50, "note": attack},
                },
            },
        )
        primitive = {
            **PRIMITIVE,
            "id": attack,
            "title": attack,
            "proposition": attack,
            "cf_gap": attack,
            "strategic_decision": attack,
            "poc": attack,
            "rfc_scope": attack,
            "core": [note.path.as_posix()],
            "supporting": [],
        }

        generated = generate_html([note], {"hostile": {
            "title": "Hostile",
            "x": {"rating": "maturity", "label": "Maturity", "low": "Low", "high": "High"},
            "y": {"rating": "platform-impact", "label": "Impact", "low": "Low", "high": "High"},
        }}, [primitive], focus_use_cases({
            **FOCUS_USE_CASE,
            "id": attack,
            "title": attack,
            "workshop_outcome": attack,
            "primary_actor": attack,
            "beneficiary": attack,
            "lifecycle": attack,
            "authority_boundary": attack,
            "unique_capabilities": [attack],
            "failure_domain": attack,
            "poc": attack,
            "rfc_decisions": [attack],
            "core": [note.path.as_posix()],
            "supporting": [],
            "primitive_applicability": {attack: attack},
        }))

        static_markup, script = generated.split("<script>", 1)
        self.assertNotIn(attack, static_markup)
        self.assertNotIn("${note.title}", script)
        self.assertNotIn("${note.summary}", script)
        self.assertNotIn("${r.note}", script)

    def test_generated_dialog_has_a_stable_accessible_name_in_both_states(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn('<dialog id="detail" aria-labelledby="dialog-title">', html)
        self.assertEqual(html.count('<h2 id="dialog-title">'), 2)

    def test_generated_html_contains_one_matrix_for_each_configured_plot(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        for plot in load_plots().values():
            self.assertIn(plot["title"], html)
        self.assertEqual(html.count('class="map"'), len(load_plots()))

    def test_generated_html_contains_primitive_card_controls_and_details(self):
        primitives = load_primitives()
        html = generate_html(load_notes(), load_plots(), primitives)

        self.assertEqual(html.count('class="primitive-select"'), 3)
        self.assertEqual(
            len(re.findall(r'class="primitive-select"[^>]+aria-pressed="false"', html)),
            3,
        )
        self.assertIn('class="show-all primitive-show-all"', html)
        self.assertIn('>Show all primitives</button>', html)
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
            tab_index = "0" if index == 0 else "-1"
            hidden = "" if index == 0 else " hidden"
            self.assertIn(
                f'id="tab-{plot_id}" role="tab" aria-selected="{selected}" '
                f'tabindex="{tab_index}" aria-controls="panel-{plot_id}"',
                html,
            )
            self.assertIn(
                f'id="panel-{plot_id}" class="matrix" role="tabpanel" '
                f'aria-labelledby="tab-{plot_id}"{hidden}',
                html,
            )

    def test_generated_html_activates_tabs_for_clicks_and_keyboard_navigation(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn("function activateTab(index)", html)
        self.assertIn("tab.setAttribute('aria-selected',String(selected))", html)
        self.assertIn("tab.tabIndex=selected?0:-1", html)
        self.assertIn("panels[i].hidden=!selected", html)
        self.assertIn("tabs[index].focus()", html)
        self.assertIn("tab.onclick=()=>activateTab(index)", html)
        self.assertIn("case 'ArrowLeft':next=(index-1+tabs.length)%tabs.length;break", html)
        self.assertIn("case 'ArrowRight':next=(index+1)%tabs.length;break", html)
        self.assertIn("case 'Home':next=0;break", html)
        self.assertIn("case 'End':next=tabs.length-1;break", html)
        self.assertIn("event.preventDefault();activateTab(next)", html)

    def test_tab_activation_preserves_primitive_selection_and_updates_markers(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        activate_tab = html.split("function activateTab(index)", 1)[1].split(
            "function handleTabKey", 1
        )[0]

        self.assertNotIn("selectedPrimitive=", activate_tab)
        self.assertIn("updateMarkers()", activate_tab)

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

    def test_generated_html_embeds_use_case_membership_once(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertEqual(html.count("const useCaseMemberships="), 1)
        self.assertIn(
            '"ideas/staged-sandbox-environments.md": {"cf-hosted-coding-harnesses": "core"}',
            html,
        )

    def test_generated_html_manages_use_case_and_primitive_selection_independently(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn("let selectedUseCase=null,selectedPrimitive=null", html)
        for function_name in (
            "selectUseCase",
            "clearUseCaseSelection",
            "selectPrimitive",
            "clearPrimitiveSelection",
            "updateUseCaseControls",
            "updatePrimitiveControls",
        ):
            self.assertIn(f"function {function_name}", html)

        select_use_case = html.split("function selectUseCase", 1)[1].split(
            "function clearUseCaseSelection", 1
        )[0]
        select_primitive = html.split("function selectPrimitive", 1)[1].split(
            "function clearPrimitiveSelection", 1
        )[0]
        self.assertNotIn("selectedPrimitive=", select_use_case)
        self.assertNotIn("selectedUseCase=", select_primitive)
        self.assertIn("button.dataset.useCase===selectedUseCase", html)
        self.assertIn("button.dataset.primitive===selectedPrimitive", html)
        self.assertIn("document.querySelector('.use-case-show-all').onclick=clearUseCaseSelection", html)
        self.assertIn("document.querySelector('.primitive-show-all').onclick=clearPrimitiveSelection", html)

    def test_generated_html_matches_evidence_against_both_independent_selections(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertEqual(html.count("function noteMatchesSelection(noteId)"), 1)
        predicate = html.split("function noteMatchesSelection(noteId)", 1)[1].split(
            "function updateMarkers", 1
        )[0]
        self.assertIn("!selectedUseCase||useCaseMemberships[noteId]?.[selectedUseCase]", predicate)
        self.assertIn("!selectedPrimitive||primitiveMemberships[noteId]?.[selectedPrimitive]", predicate)
        self.assertIn("return Boolean(matchesUseCase&&matchesPrimitive)", predicate)
        self.assertIn("const related=noteMatchesSelection(m.dataset.id)", html)
        self.assertIn("noteIds.filter(noteMatchesSelection)", html)
        self.assertIn("classList.toggle('related'", html)
        self.assertIn("classList.toggle('dimmed'", html)
        marker_buttons = re.findall(r'<button class="marker [^"]+"[^>]*>', html)
        self.assertTrue(marker_buttons)
        for marker in marker_buttons:
            self.assertNotIn(" disabled", marker)
            self.assertNotIn('tabindex="-1"', marker)

    def test_generated_html_persistently_refreshes_marker_highlighting(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn("selectedPrimitive=null", html)
        self.assertIn("function selectPrimitive", html)
        self.assertIn("function clearPrimitiveSelection", html)
        self.assertIn("function updateMarkers", html)
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
        notes, plots, primitives, use_cases = mixed_cluster_fixture()

        html = generate_html(notes, plots, primitives, use_cases)

        marker = re.search(r'<button class="marker cluster"[^>]+>5</button>', html).group(0)
        note_ids = [note.path.as_posix() for note in notes]
        encoded_ids = html_lib.escape(json.dumps(note_ids), quote=True)
        self.assertIn(f'data-note-ids="{encoded_ids}"', marker)
        self.assertIn("const matchingCount=hasSelection?noteIds.filter(noteMatchesSelection).length:0", html)
        self.assertIn("m.textContent=hasSelection?`${matchingCount}/${noteIds.length}`:String(noteIds.length)", html)
        self.assertIn("m.classList.toggle('related',matchingCount>0)", html)
        self.assertIn("m.classList.toggle('dimmed',Boolean(hasSelection&&!matchingCount))", html)

    def test_mixed_cluster_updates_and_restores_accessible_count(self):
        notes, plots, primitives, use_cases = mixed_cluster_fixture()

        html = generate_html(notes, plots, primitives, use_cases)

        self.assertIn('aria-label="5 notes at this position"', html)
        self.assertIn(
            "m.setAttribute('aria-label',hasSelection?`${matchingCount} of ${noteIds.length} matching notes at this position`:`${noteIds.length} notes at this position`)",
            html,
        )

    def test_mixed_cluster_fixture_covers_each_combined_match_category(self):
        notes, _, primitives, use_cases = mixed_cluster_fixture()

        primitive_paths = set(primitives[0]["core"] + primitives[0]["supporting"])
        use_case_paths = set(use_cases[0]["core"] + use_cases[0]["supporting"])
        categories = []
        for note in notes:
            path = note.path.as_posix()
            categories.append((path in use_case_paths, path in primitive_paths))

        self.assertEqual(
            categories,
            [(True, False), (False, True), (True, True), (False, False), (True, True)],
        )

    def test_mixed_cluster_picker_sorts_a_copy_by_combined_match_and_labels_both_relationships(self):
        notes, plots, primitives, use_cases = mixed_cluster_fixture()

        html = generate_html(notes, plots, primitives, use_cases)

        self.assertIn("const ordered=hasSelection?[...items.filter(isRelated),...items.filter(note=>!isRelated(note))]:[...items]", html)
        self.assertIn("const isRelated=note=>noteMatchesSelection(note.id)", html)
        self.assertIn("${relationshipBadges(note)}", html)
        self.assertIn("useCaseMemberships[note.id]?.[selectedUseCase]", html)
        self.assertIn("primitiveMemberships[note.id]?.[selectedPrimitive]", html)
        self.assertIn("escapeHtml(label)", html)
        self.assertIn("const noteIds=JSON.parse(m.dataset.noteIds)", html)
        self.assertIn("noteIds.map(id=>plots[m.dataset.plot].find(note=>note.id===id))", html)
        self.assertNotIn("m.dataset.cluster.split", html)

    def test_combined_empty_selection_announces_exact_status_and_clear_restores_it(self):
        notes, plots, primitives, use_cases = mixed_cluster_fixture()

        html = generate_html(notes, plots, primitives, use_cases)

        self.assertIn('<p id="filter-status" role="status" aria-live="polite"></p>', html)
        self.assertIn(
            "filterStatus.textContent=selectedUseCase&&selectedPrimitive&&!hasMatches?'No directly linked evidence for this use-case and primitive combination.':''",
            html,
        )
        self.assertIn(
            "const hasMatches=Object.values(plots).some(notes=>notes.some(note=>noteMatchesSelection(note.id)))",
            html,
        )
        for function_name in ("clearUseCaseSelection", "clearPrimitiveSelection"):
            function = html.split(f"function {function_name}", 1)[1].split("function ", 1)[0]
            self.assertIn("updateMarkers()", function)

    def test_generated_html_wires_singletons_and_close_button(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())
        self.assertIn("show(plots[m.dataset.plot].find(n=>n.id===m.dataset.id))", html)
        self.assertIn("document.querySelector('.close').onclick=()=>dialog.close()", html)

    def test_generated_html_retains_dialog_dismissal_interactions(self):
        html = generate_html(load_notes(), load_plots(), load_primitives())

        self.assertIn("if(e.target===dialog)dialog.close()", html)
        self.assertIn("if(e.key==='Escape')dialog.close()", html)

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
        self.assertIn('class="picker-kind ${escapeHtml(note.kind)}"', html)
        self.assertIn('.picker-kind.research', html)
        self.assertIn('.picker-kind.idea', html)


if __name__ == "__main__":
    unittest.main()
