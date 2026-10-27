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
        cls.card = load_json("docs/data/run-card.json")

    def test_negative_card_fails_closed(self):
        card = self.card
        self.assertEqual(card["schema"], "apart-gems-run-card-v1")
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["slot_selected"])
        self.assertFalse(card["slot_used"])
        self.assertEqual(card["experiments"]["performed"], 0)
        self.assertIsNone(card["raster"]["path"])
        self.assertIsNone(card["raster"]["sha256"])
        self.assertEqual(card["raster"]["status"], "NO TIFF GENERATED")

    def test_no_unrun_score_or_validation_is_fabricated(self):
        holdout = self.card["holdout"]
        self.assertEqual(holdout["label"], "HOLDOUT-DTI")
        self.assertEqual(holdout["status"].split(" — ")[0], "NOT RUN")
        self.assertIsNone(holdout["value"])
        self.assertIsNone(holdout["ci95"])
        self.assertIsNone(holdout["evaluator_version"])
        self.assertIsNone(holdout["withheld_positive_count"])
        self.assertEqual(self.card["validator"]["status"].split(" — ")[0], "NOT RUN")
        self.assertIsNone(self.card["validator"]["crs_matches"])
        self.assertIsNone(self.card["registry_comparison"]["preplacement_abs_spearman_max"])
        self.assertIsNone(self.card["registry_comparison"]["final_dot_max_fraction_within_3px"])

    def test_submission_note_limit_is_validated(self):
        self.assertEqual(self.card["submission_note_character_limit"], 140)
        self.assertIsNone(self.card["submission_note"])
        self.assertIsNone(self.card["submission_name"])


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
