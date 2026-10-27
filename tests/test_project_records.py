import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


class FocusSiteRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = load_json("docs/data/focus-sites.json")

    def test_exact_focus_site_set_and_schema(self):
        self.assertEqual(self.record["schema"], "apart-gems-focus-sites-v1")
        sites = self.record["sites"]
        self.assertEqual(len(sites), 9)
        self.assertEqual(
            {site["site"] for site in sites},
            {
                "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28",
                "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33",
                "GEMSDOE36",
            },
        )
        self.assertEqual(len({site["site"] for site in sites}), len(sites))
        self.assertIn("not a current-main best-of review", self.record["snapshot_scope"])
        self.assertIn("freshness", self.record["freshness_caveat"].lower())

    def test_scores_are_owner_claims_not_verified_receipts(self):
        for site in self.record["sites"]:
            with self.subTest(site=site["site"]):
                self.assertTrue(site["reported_score_label"].startswith("OWNER-REPORTED"))
                self.assertIsNone(site["holdout_dti_estimate"])
                self.assertFalse(site["unique_vs_other_eight"])
                self.assertGreater(site["max_overlap_vs_other_eight"], 0.70)
                self.assertTrue(site["method_tag"])
                self.assertTrue(site["method_summary_provenance"])
                self.assertEqual(len(site["sha256"]), 64)
                self.assertRegex(site["sha256"], r"^[0-9a-f]{64}$")

    def test_h33_b2_is_highest_of_the_nine_reported_claims(self):
        leader = max(self.record["sites"], key=lambda item: item["reported_score"])
        self.assertEqual(leader["site"], "GEMSDOE32")
        self.assertEqual(leader["reported_score"], 0.2778)
        self.assertIn("OWNER-REPORTED", leader["reported_score_label"])


class RunCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = load_json("docs/data/latest-run-card.json")

    def test_current_review_fails_closed_and_identifies_research_artifact(self):
        card = self.card
        self.assertEqual(card["schema_version"], "apartgemsdoe3-current-review-v2")
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["ok_to_submit"])
        self.assertEqual(card["selector"]["decision"], "DO_NOT_SUBMIT")
        self.assertFalse(card["selector"]["ok_to_submit"])
        self.assertTrue(card["ok_to_download_for_research"])
        self.assertEqual(card["new_experiments"], 0)
        self.assertEqual(card["submission_slots_used"], 0)
        self.assertTrue(card["submission_name"].endswith("-zeros.tif"))
        self.assertEqual(card["raster_sha256"], card["validator_output"]["sha256"])
        self.assertRegex(card["raster_sha256"], r"^[0-9a-f]{64}$")

    def test_prior_holdout_is_labeled_and_not_represented_as_a_projection(self):
        holdout = self.card["holdout_dti"]
        self.assertEqual(holdout["label"], "HOLDOUT-DTI")
        self.assertEqual(holdout["evaluator_version"], "gems-segment-pooled-v1")
        self.assertEqual(holdout["withheld_positive_count"], 60988)
        self.assertEqual(len(holdout["ci_95"]), 2)
        self.assertIn("not replayed", holdout["provenance"].lower())
        self.assertIsNone(self.card["score_estimate"])
        self.assertIsNone(self.card["organizer_confirmed_score"])

    def test_core_raster_checks_do_not_override_official_format_failure(self):
        output = self.card["validator_output"]
        checks = output["checks"]
        self.assertTrue(output["format_valid"])
        self.assertFalse(output["official_format_compliant"])
        self.assertFalse(output["ok_to_upload"])
        self.assertTrue(checks["single_band"]["pass"])
        self.assertTrue(checks["dtype_float32"]["pass"])
        self.assertTrue(checks["footprint_all_finite"]["pass"])
        self.assertTrue(checks["footprint_range_0_1"]["pass"])
        self.assertTrue(checks["shape_matches_template"]["pass"])
        self.assertTrue(checks["geotransform_matches_template"]["pass"])
        self.assertFalse(checks["nodata_tag_is_nan"]["pass"])
        self.assertFalse(checks["outside_is_nan_official_text"]["pass"])

    def test_current_run_card_note_is_under_140_chars_and_not_historical_claim(self):
        note = self.card["submission_note"]
        self.assertIsInstance(note, str)
        self.assertLessEqual(len(note), 140)
        self.assertIn("DO NOT SUBMIT", note)
        self.assertIn("null/NaN", note)
        self.assertIn("automated gates passed", self.card["recorded_experiment_note"].lower())


class LeaderboardSnapshotTests(unittest.TestCase):
    def test_snapshot_has_explicit_provenance(self):
        record = load_json("docs/data/leaderboard.json")
        self.assertEqual(record["observed_on_utc"], "2026-10-27")
        self.assertIn("not a submission-page receipt", record["evidence_label"].lower())
        self.assertTrue(record["rows"])
        self.assertEqual(record["rows"][0]["rank"], 1)
        self.assertEqual(record["rows"][0]["participant"], "xiaofanhu")
        self.assertEqual(record["rows"][0]["public_score"], 0.4544)


if __name__ == "__main__":
    unittest.main()
