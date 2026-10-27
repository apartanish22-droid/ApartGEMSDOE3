import json
import subprocess
from html.parser import HTMLParser

import pytest

import build_site
import refresh_inventory
from audit_priority import ROOT


class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = 0
        self.downloads = []
        self.disabled_buttons = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self.rows += 1
        if tag == "a":
            self.links.append(a.get("href", ""))
            if "download" in a:
                self.downloads.append(a.get("href", ""))
        if tag == "button" and "disabled" in a:
            self.disabled_buttons += 1


def test_pages_are_generated_and_no_submission_file_is_downloadable():
    pages = build_site.render()
    for name, text in pages.items():
        assert (ROOT / name).read_text() == text
        page = Structure()
        page.feed(text)
        assert not any(link.lower().endswith((".tif", ".tiff", ".zip")) for link in page.downloads)
        assert not any(link.lower().startswith("javascript:") for link in page.links)
        if name in ("index.html", "executive-summary.html"):
            assert page.disabled_buttons >= 1
    landing = Structure()
    landing.feed(pages["index.html"])
    assert landing.rows == 10  # header plus the nine pinned sites
    assert "USER-REPORTED / UNVERIFIED" in pages["index.html"]
    assert "No competition-ready TIFF is available" in pages["index.html"]


def test_peer_reference_is_research_only_and_lattice_failure():
    peer = json.loads((ROOT / "evidence/peer_reference_audit.json").read_text())
    assert peer["new_raster"] is False
    assert peer["ok_to_submit"] is False
    assert peer["complete_registry_checked"] is False
    assert peer["maximum_vs_historical_nine"]["candidate_within_3px_fraction"] < .70
    assert peer["literal_lattice_duplicate"] is True
    assert peer["candidate_within_3px_of_lattice"] > .70
    holdout = peer["recorded_holdout_not_replayed"]
    assert holdout["label"] == "HOLDOUT-DTI"
    assert holdout["evaluator_version"] and holdout["withheld_positive_pixels"] > 0
    assert len(holdout["ci95"]) == 2


def test_truncated_or_inconsistent_remote_tree_fails_closed(monkeypatch):
    row = {"site": "test", "repo": "owner/repo", "ref": "abc", "path": "a.tif", "git_blob": "sha", "size": 5}
    monkeypatch.setattr(refresh_inventory, "github_json", lambda _: {"truncated": True, "tree": []})
    with pytest.raises(RuntimeError, match="Incomplete"):
        refresh_inventory.get_tree(row)
    monkeypatch.setattr(refresh_inventory, "github_json", lambda _: {"truncated": False, "tree": []})
    with pytest.raises(RuntimeError, match="differs"):
        refresh_inventory.get_tree(row)


def test_failed_head_fetch_is_unknown_not_fresh(monkeypatch):
    row = {"site": "x", "repo": "owner/repo", "ref": "abc"}
    def fail(_):
        raise subprocess.CalledProcessError(1, "gh")
    monkeypatch.setattr(refresh_inventory, "github_json", fail)
    result = refresh_inventory.get_head(row)
    assert result["head"] is None
    assert result["state"].startswith("unknown")


def test_current_card_supersedes_parallel_claim_and_preserves_evidence():
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    parallel = json.loads((ROOT / "evidence/parallel_mrcj_audit.json").read_text())
    assert card["verdict"] == "negative" and card["ok_to_submit"] is False
    assert card["raster_sha256"] == parallel["raster"]["sha256"]
    assert card["holdout_dti"]["value"] == parallel["recorded_holdout_not_replayed"]["value"]
    assert "NOT REPLAYED" in card["holdout_dti"]["status"]
    assert card["correlation_overlap_vs_registry"]["final_dots_lattice_overlap"] == 1.0
    assert card["correlation_overlap_vs_registry"]["duplicate_stop"] is True
    assert card["weekly_slots_used_in_this_review"] == 0
    assert card["experiments_run_in_this_review"] == 0 and card["parallel_run_experiments_reported"] <= card["experiment_budget"]
    assert len(card["submission_note"]) <= 140
