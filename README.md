# kalpang-observer

A small read-only observer for KALPANG Experiment 004. It watches the issues and issue comments of
one GitHub repository from a **separate repository**, and publishes **hashes** of what it saw
(never issue or comment text), with a build-provenance attestation on the output files.

Status: first live runs on 24 October 2026. One run per scenario. A demonstration, not a proof.

## Question

If a controlled workflow (the "executor", in a private probe repository) is authorized to create
one issue, does a read-back of that one issue tell you whether anything else happened?

## Results (24 October 2026)

| Scenario | Target-only view | Observer verdict | Expected | Met |
|---|---|---|---|---|
| normal | TARGET_MATCH | IN-BOUNDS | IN-BOUNDS | yes |
| extra-effect | TARGET_MATCH | DIVERGENT (one unapproved new issue) | DIVERGENT | yes |
| target-mismatch | TARGET_MISMATCH | DIVERGENT | DIVERGENT | yes |

In `extra-effect` the issue that was authorized matched exactly, so a check that only read that
issue would have passed. The observer scanned all issues and comments in the repository and saw
one more issue that was not authorized (`missed_by_target_only: true` in its report).

## How it works

1. The observer takes a baseline snapshot (stable only when two reads in a row are identical).
2. It waits for the executor run whose display title is `EB004 / <scenario> / <run_id>` to finish.
3. It waits 30 seconds, takes a second stable snapshot, and compares the two.
4. It writes `report.json` and a manifest of file hashes, verifies the manifest, attests the
   files, and uploads them as a workflow artifact.

Verdicts: `IN-BOUNDS`, `DIVERGENT`, `INDETERMINATE` (observation incomplete or inconsistent),
`NO OBSERVED EFFECT` (a failure, not a pass). A verdict only speaks for the declared boundary:
**issues and issue comments of one repository.** It says nothing about workflow logs, pull
requests, notifications, repository contents, webhooks, or other repositories.

The token is a fine-grained, read-only token limited to the probe repository (Actions and Issues
read access). The observer sends only GET requests.

## Limits

- **Not an independent trust domain.** Observer and probe are separate repositories under the same
  GitHub account, using GitHub's own API. A GitHub-side fault, or the account owner, is outside
  what this can catch.
- **The extra effect was injected on purpose** by the test workflow. This shows the observer sees
  such an effect. It does not show it finds effects nobody planned.
- **Hashes, not content.** A body edited to a different text is detected through its hash. Nothing
  here shows or stores the text.
- **One run per scenario**, one platform, one repository.
- The attestation is created but **I have not yet verified it with `gh attestation verify`**.
- Related work: EffectMatch (arXiv 2609.31301) and Schrock's IETF drafts cover post-execution
  effect comparison and the in-bounds / divergent / indeterminate vocabulary. No novelty is
  claimed for those ideas. The contribution is a small, reproducible live check on GitHub.

## Reproduce

Read `observer/run_probe.py` (standard library only) and `tests/test_observer.py` (15 tests
against a fake GitHub server: `python3 -I tests/test_observer.py`).

Developed with substantial LLM assistance. MIT licensed.
