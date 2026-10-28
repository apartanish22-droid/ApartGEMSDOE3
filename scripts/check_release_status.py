#!/usr/bin/env python3
"""Data-independent fail-closed release consistency check (negative is a valid result)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check(card):
    gates = card.get('release_gate_decision', {}).get('gates', {})
    literal = card.get('correlation_vs_registry', {}).get('literal_all_rasters_final_passed')
    if card.get('selector_required') is not True or card.get('slot_used') is not False:
        raise ValueError('Separate selector required; no slot may be used')
    if card.get('verdict') == 'promote':
        required = {'lane','surface','final','canaries','holdout','paired_improvement','format'}
        if literal is not True or not required.issubset(gates) or not all(gates[k] is True for k in required):
            raise ValueError('Promotion requires literal all-raster uniqueness and every gate')
    elif card.get('verdict') != 'negative' or card.get('ok_to_submit') is not False:
        raise ValueError('Negative result must explicitly prohibit submission')
    if card['release_gate_decision']['verdict'] != card['verdict']:
        raise ValueError('Conflicting gate and card verdicts')

def main():
    card = json.loads((ROOT/'run_card.json').read_text())
    check(card)
    artifact = ROOT/card['download_files']['primary_download_path']
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != card['raster_sha256']:
        raise ValueError('Artifact hash mismatch')
    if card['verdict'] == 'negative':
        for name in ['index.html','executive-summary.html','release-status.html','submissions.html']:
            if 'DO NOT SUBMIT' not in (ROOT/'docs'/name).read_text():
                raise ValueError('Missing negative release warning')
    print(f"PASS: consistent {card['verdict']} verdict; artifact hash verified; no slot used")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
