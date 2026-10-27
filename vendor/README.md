# Pinned shared template (locally restored, not redistributed)

Run `python scripts/fetch_template.py` to restore the unmodified shared template
into the Git-ignored `vendor/gems57/` directory from [57GEMSDOE at commit
`822a0ce5546c7b6749cdd82eb145b6b3e616603d`](https://github.com/buffedlizard55-lab/57GEMSDOE/tree/822a0ce5546c7b6749cdd82eb145b6b3e616603d).
`prepare_data.py` is upstream under `scripts/`; the other files are under
`src/gems57/`. Every source file is checked against both its immutable Git blob
ID and SHA-256 in `template-provenance.json` before import. This is the
user-requested public research template, not an organizer-authenticated scorer.

The upstream repository had no license file or GitHub license metadata when
checked on 2026-10-27; independent permission for redistribution was not
established. The restored code is therefore *not committed or published* by
this project. We have not made a private evaluator or writer fork. The derived
cached feature array was not published and is not present here.

Known issue: the `metric.py` **prose** incorrectly asserts that marginal truth
credit is always at most a dot's own nearest-truth kernel credit. The scoring
functions and exact `marginal_accept` need not have that same defect. Counterexample
and report: [GEMSDOE32 issue 50](https://github.com/buffedlizard55-lab/GEMSDOE32/issues/50).
We do not rely on the affected prose. Other upstream issues and the unresolved
cache-builder defect are catalogued in `docs/research/review.md`.
