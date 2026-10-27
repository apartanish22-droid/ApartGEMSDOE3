import json
import os
import sys

import pytest

import audit_peer_reference
import audit_priority
import build_site
import refresh_inventory
from io_safety import validate_output_path
from audit_priority import ROOT


def test_json_output_rejects_symlink_and_hardlink_aliases(tmp_path):
    source = tmp_path / 'original.json'
    source.write_text('{"unchanged":true}')
    link = tmp_path / 'linked.json'
    link.symlink_to(source)
    with pytest.raises(ValueError):
        validate_output_path(link, (source,))
    link.unlink()
    os.link(source, link)
    with pytest.raises(ValueError):
        validate_output_path(link, (source,))
    assert json.loads(source.read_text()) == {"unchanged": True}


def test_priority_output_cannot_overwrite_its_manifest():
    manifest = ROOT / 'registry/focus_sites.json'
    before = manifest.read_bytes()
    with pytest.raises(ValueError, match='overwrite'):
        audit_priority.run(offline=True, output=manifest)
    assert manifest.read_bytes() == before


def test_peer_audit_cannot_overwrite_its_manifest(monkeypatch):
    manifest = ROOT / 'registry/peer_research_reference.json'
    before = manifest.read_bytes()
    monkeypatch.setattr(sys, 'argv', ['audit_peer_reference.py', '--offline', '--output', str(manifest)])
    with pytest.raises(ValueError, match='overwrite'):
        audit_peer_reference.main()
    assert manifest.read_bytes() == before


def test_site_build_rejects_unexpected_authorization(tmp_path, monkeypatch):
    import shutil
    for directory in ('registry', 'evidence'):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    card_path = tmp_path / 'evidence/run_card.json'
    card = json.loads(card_path.read_text())
    card['ok_to_submit'] = True
    card_path.write_text(json.dumps(card))
    monkeypatch.setattr(build_site, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='negative run card'):
        build_site.render()


def test_malformed_remote_sha_is_unknown(monkeypatch):
    monkeypatch.setattr(refresh_inventory, 'github_json', lambda _: {'sha': 'not-a-sha'})
    result = refresh_inventory.get_head({'site': 'test', 'repo': 'owner/repo', 'ref': '0' * 40})
    assert result['head'] is None and result['state'].startswith('unknown')


def test_changed_head_is_nonzero_even_when_check_succeeded(tmp_path, monkeypatch):
    monkeypatch.setattr(refresh_inventory, 'github_json', lambda _: {'sha': 'f' * 40})
    monkeypatch.setattr(sys, 'argv', ['refresh_inventory.py', '--heads', '--output', str(tmp_path / 'result.json')])
    with pytest.raises(SystemExit, match='re-audit required'):
        refresh_inventory.main()
    data = json.loads((tmp_path / 'result.json').read_text())
    assert len(data['sources']) == 9
    assert all(row['state'].startswith('changed') for row in data['sources'])
    assert 'excludes the lattice' in data['scope']
