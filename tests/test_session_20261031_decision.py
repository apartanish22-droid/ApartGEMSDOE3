"""Consistency checks for the 2026-10-31 decision block: every headline number must trace to an evidence file."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _page() -> str:
    return (ROOT / "docs/executive-summary.html").read_text(encoding="utf-8")


def test_decision_block_is_first_and_says_no_download() -> None:
    page = _page()
    assert page.index('id="decision"') < page.index("Start here: the verified answer")
    assert "Download: NONE. Submit: NONE." in page


def test_e1_numbers_match_run_card_and_holdout() -> None:
    card = json.loads((ROOT / "evidence/euler_n1_E1_run_card.json").read_text())
    holdout = json.loads((ROOT / "evidence/euler_n1_E1_holdout_20261031.json").read_text())
    page = _page()
    sgmc = card["holdout_dti"]["HOLDOUT-DTI_sgmc_prevalence_calibrated"]["calibrated_dti"]
    hr = holdout["hide_and_recover"]["pooled_dti"]
    assert f"{sgmc:.4f}" == "0.0147" and "0.0147" in page
    assert f"{hr:.4f}" == "0.0196" and "0.0196" in page
    assert card["verdict"] == "negative" and card["ok_to_download"] is False and card["ok_to_submit"] is False
    assert len(card["submission_note"]) <= 140


def test_e1_candidate_hash_matches_run_card_when_present() -> None:
    import hashlib

    card = json.loads((ROOT / "evidence/euler_n1_E1_run_card.json").read_text())
    path = ROOT / card["candidate_path"]
    if not path.exists():  # .cache is regenerable and not committed
        return
    assert hashlib.sha256(path.read_bytes()).hexdigest() == card["candidate_sha256"]


def test_uniqueness_flags_match_evidence() -> None:
    uniq = json.loads((ROOT / "evidence/euler_n1_E1_uniqueness_20261031.json").read_text())
    page = _page()
    assert uniq["n_duplicates"] == 4 and uniq["n_compared"] == 131
    assert "4 of 131" in page
    assert f"{uniq['worst_within_3px_fraction'] * 100:.2f}" == "99.97"


def test_champion_mechanism_numbers_match_measurement() -> None:
    prox = json.loads((ROOT / "evidence/champion_catalogue_proximity_20261031.json").read_text())
    champion = next(v for k, v in prox["rows"].items() if k.startswith("GEMSDOE32 champion"))
    assert champion["within_2px"] == 0.0
    assert prox["facts"]["d28_dots_within_2px_of_labels"] == 6436
    assert prox["facts"]["d28_dots_removed_to_make_champion"] == 44090 - 37654
    assert "6,436" in _page()


def test_random_controls_cover_both_seeds() -> None:
    ctl = json.loads((ROOT / "evidence/random_dot_controls_20261031.json").read_text())["controls"]
    hr = [ctl[k]["hide_and_recover_pooled_dti"] for k in ("random_seed0", "random_seed1")]
    assert all(0.04 < x < 0.05 for x in hr)
    assert re.search(r"0\.045–0\.049", _page())


def test_no_download_cta_for_failed_main_candidates() -> None:
    """Main-branch H-GEO-1 and H1 were shown as downloadable; both fail uniqueness, so no CTA may remain."""
    for rel in ("docs/executive-summary.html", "docs/executive-summary/index.html", "docs/index.html"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        # match live CTA elements only; the withdrawal note quotes these phrases as plain text
        assert not re.search(r">\s*(⬇\s*)?Download: YES", text), rel
        assert not re.search(r">\s*(H1 )?OK TO DOWNLOAD ONLY", text), rel
        assert 'href="downloads/' not in text, rel
        assert 'href="../downloads/' not in text, rel


def test_main_candidate_uniqueness_recheck_matches_evidence() -> None:
    for name in ("hgeo1", "h1"):
        d = json.loads((ROOT / f"evidence/{name}_uniqueness_recheck_20261031.json").read_text())
        assert d["n_compared"] == 131 and d["n_duplicates"] == 7 and d["passed_all"] is False, name
    assert json.loads((ROOT / "evidence/hgeo1_uniqueness_recheck_20261031.json").read_text())["worst_within_3px_fraction"] > 0.999
    page = _page()
    assert "99.94%" in page and "99.78%" in page
