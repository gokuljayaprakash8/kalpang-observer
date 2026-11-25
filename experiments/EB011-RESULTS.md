# EB011 results: request authorization is not committed-effect conformance

Run date: 25 November 2026. Suffix r3. Predictions are in experiments/EB011.md (committed before any run). All 7 observer runs completed successfully; the verdict line is quoted from each run's "Classify with attribution" step.

## Results (observer verdict vs prediction)
| mode | handler commits | predicted | observed | agent_comments / conforming | match |
|---|---|---|---|---|---|
| faithful | authorized comment | IN-BOUNDS | IN-BOUNDS | 1 / 1 | yes |
| retarget | authorized body on protected issue | DIVERGENT | DIVERGENT (COMMITTED_EFFECT_OUTSIDE_AUTHORIZED_SPEC) | 1 / 0 | yes |
| mutate-body | different body on target | DIVERGENT | DIVERGENT (same reason) | 1 / 0 | yes |
| extra-effect | authorized comment plus second on protected | DIVERGENT | DIVERGENT (same reason) | 2 / 1 | yes |
| false-success | nothing, agent reports success | NO OBSERVED EFFECT | NO OBSERVED EFFECT | 0 / 0 | yes |
| unmonitored | authorized comment plus reaction on protected | IN-BOUNDS (predicted miss) | IN-BOUNDS | 1 / 1 | yes (a miss) |
| edit-existing | authorized comment plus edit of protected body | INDETERMINATE | INDETERMINATE (UNATTRIBUTABLE_CHANGE_TO_EXISTING) | 1 / 1 | yes |

7 of 7 predictions matched, including two predicted weaknesses.

## What this shows (within the stated boundary only)
1. In this setup, a pre-fixed authorized effect specification plus before/after snapshots separated a committed effect that conformed from three kinds of non-conforming commits (wrong target, changed body, extra effect), while the agent reported success in every mode. The request was "authorized" in all seven; only conformance differed.
2. A false success (nothing committed) was reported as NO OBSERVED EFFECT, not as success.
3. Two limits were observed, as predicted: an effect in an unobserved field (reaction) passed as IN-BOUNDS (a false pass); an edit to an existing item was seen but could not be classified as DIVERGENT.

## What this does not show
- Scripted, deterministic handler; not a real compromised handler or a real agent.
- One repository, one account, one trust domain; agent, handler and owner share one identity. Attribution is assumed (sole actor), not tested; EB010 showed it fails under shared identity.
- Only issues and comments (title, state, body hash) are observed.
- The authorized specification was fixed by the experimenter; no policy engine was tested.
- Not independently reproduced. No formal proof.

## Harness record (disclosure)
- Suffix r1: the observer was started with mode "r1" (input error); the probe run for faithful-r1 had no valid observer. Discarded, no verdict.
- Suffix r2: setup for r2 had not been created; the probe run for faithful-r2 failed with "setup issue not found". Discarded, no verdict.
- Suffix r3: setup run and all 7 modes ran once each. No run was repeated to match a prediction.

## Evidence pointers to add
Observer run URLs and attestation/manifest artifacts for each of the 7 r3 runs (kalpang-observer, Actions, "EB011 conformance observer"); the committed experiments/EB011.md; probe repo issues "[EB011 <mode>-r3] target/protected".

## Mapping
TAAS-PROPS P09 (conformance) and P10; TAAS-THREAT A17; TAAS-LIMITS RR-03, RR-04; TAARR TAA-051, TAA-079, TAA-123, TAA-125.
