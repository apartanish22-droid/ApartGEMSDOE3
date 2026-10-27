from __future__ import annotations

import json

import pytest

import refresh_feed as feed


BOARD = """<html><body>
<table><tr><th>Other rank</th><th>Score</th></tr><tr><td>1</td><td>0.9999</td></tr></table>
<table><thead><tr><th>Rank</th><th>Team members</th><th>Participant</th>
<th>Best<br>public<br> DW-Tversky<br>(in descending order)</th><th>Shared work</th></tr></thead>
<tbody><tr><td>#1</td><td></td><td><a>Team A</a><br>32 submissions</td><td>0.4544</td><td></td></tr>
<tr><td>#2</td><td></td><td>Team B</td><td>0.3916</td><td></td></tr></tbody></table>
<table><tr><td>1</td><td>fake</td><td>fake</td><td>0.8</td></tr></table>
</body></html>"""


def test_parse_public_score_from_same_table_only():
    assert feed.parse_leaderboard(BOARD) == .4544
    # A harmless column reordering should still select the named score column.
    reordered = "<table><tr><th>Public DW-Tversky</th><th>Rank</th></tr><tr><td>0.8</td><td>#1</td></tr></table>"
    assert feed.parse_leaderboard(reordered) == .8


@pytest.mark.parametrize("html", [
    "<html>login required</html>",
    "<table><tr><th>Rank</th><th>Private Tversky</th></tr><tr><td>1</td><td>0.9</td></tr></table>",
    "<table><tr><th>Rank</th><th>Public Tversky</th></tr><tr><td>1</td><td>1.01</td></tr></table>",
    "<table><tr><th>Rank</th><th>Public Tversky</th></tr><tr><td>1</td><td>NaN</td></tr></table>",
    "<table><tr><th>Rank</th><th>Public Tversky</th></tr><tr><td>1</td></tr></table>",
    "<table><tr><th>Rank</th><th>Public Tversky</th><th>Other public Tversky</th></tr></table>",
    "<table><tr><th>Rank</th><th>Public Tversky</th></tr><tr><td>1</td><td>0.9</td></tr><tr><td>#1</td><td>0.8</td></tr></table>",
    ("<table><tr><th>Rank</th><th>Public Tversky</th></tr><tr><td>1</td><td>0.9</td></tr></table>" * 2),
])
def test_rejects_unrecognized_or_ambiguous_pages(html):
    with pytest.raises(ValueError):
        feed.parse_leaderboard(html)


def test_refresh_retains_failed_observations_and_records_partial_heads(monkeypatch):
    monkeypatch.setattr(feed, "SITES", ("GEMSDOE24", "GEMSDOE25"))
    previous = {
        "leaderboard": {"value": .4544, "observed_utc": "2026-10-27T00:00:00Z"},
        "site_heads": {
            "GEMSDOE24": {"sha": "a" * 40, "observed_utc": "2026-10-27T01:00:00Z"},
            "GEMSDOE25": {"sha": "b" * 40, "observed_utc": "2026-10-27T02:00:00Z"},
        },
    }
    def fake_fetch(url, token=None):
        if url == feed.LEADERBOARD or "GEMSDOE25" in url:
            raise OSError("offline")
        return json.dumps({"sha": "c" * 40})
    monkeypatch.setattr(feed, "fetch", fake_fetch)
    result = feed.refresh(previous)
    assert result["leaderboard"] == previous["leaderboard"]
    assert result["leaderboard_status"] == "error" and "offline" in result["leaderboard_error"]
    assert result["site_heads"]["GEMSDOE25"] == previous["site_heads"]["GEMSDOE25"]
    assert result["site_heads"]["GEMSDOE24"]["sha"] == "c" * 40
    assert result["site_heads"]["GEMSDOE24"]["observed_utc"] == result["last_attempt_utc"]
    assert result["site_heads_status"] == "partial_or_failed" and "GEMSDOE25" in result["site_head_errors"]
    # The caller's previous snapshot was not mutated.
    assert previous["site_heads"]["GEMSDOE24"]["sha"] == "a" * 40


def test_refresh_updates_valid_score_and_explicitly_marks_skips(monkeypatch):
    monkeypatch.setattr(feed, "fetch", lambda *args: BOARD)
    prior = {"leaderboard": {"value": .3, "observed_utc": "old"}}
    result = feed.refresh(prior, skip_heads=True)
    assert result["leaderboard"]["value"] == .4544
    assert result["leaderboard"]["observed_utc"] == result["last_attempt_utc"]
    assert result["leaderboard_status"] == "success"
    assert result["site_heads_status"] == "skipped"
    monkeypatch.setattr(feed, "fetch", lambda *args: pytest.fail("must not fetch when skipped"))
    skipped = feed.refresh(result, skip_heads=True, skip_leaderboard=True)
    assert skipped["leaderboard"] == result["leaderboard"]
    assert skipped["leaderboard_status"] == "skipped"


def test_non_dictionary_github_response_is_retained_as_error(monkeypatch):
    monkeypatch.setattr(feed, "SITES", ("GEMSDOE24",))
    monkeypatch.setattr(feed, "fetch", lambda *args: "[]")
    result = feed.refresh({"site_heads": {}}, skip_leaderboard=True)
    assert result["site_heads_status"] == "partial_or_failed"
    assert "GEMSDOE24" in result["site_head_errors"]
