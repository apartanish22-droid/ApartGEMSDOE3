#!/usr/bin/env python3
"""Fail closed on unsupported historical promotion and inconsistent release pages."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    card = json.loads((ROOT / 'run_card.json').read_text())
    if card.get('verdict') != 'negative' or card.get('ok_to_submit') is not False:
        raise SystemExit('Release must stay negative until the full protocol is rerun and independently reviewed')
    if card.get('correlation_vs_registry', {}).get('literal_all_rasters_final_passed') is not False:
        raise SystemExit('Historical literal uniqueness failure must remain recorded')
    gates = card.get('release_gate_decision', {}).get('gates', {})
    if any(gates.get(name) is not False for name in ('final', 'lane', 'scientific_integrity')):
        raise SystemExit('Known failed release gates must remain false')
    if card.get('release_gate_decision', {}).get('verdict') != 'negative':
        raise SystemExit('Release gate verdict must be negative')
    if card.get('selector_required') is not True or card.get('slot_used') is not False:
        raise SystemExit('Separate selector required and no slot spent')
    tif = ROOT / card['artifacts']['primary_zeros_tif']
    if hashlib.sha256(tif.read_bytes()).hexdigest() != card['raster_sha256']:
        raise SystemExit('Historical artifact checksum mismatch')
    for name in ('index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/release-status.html', 'docs/submissions.html'):
        if 'DO NOT SUBMIT' not in (ROOT / name).read_text():
            raise SystemExit(f'Missing release warning: {name}')
    print('PASS: negative release status; historical artifact hash matches; no slot used')

if __name__ == '__main__':
    main()
