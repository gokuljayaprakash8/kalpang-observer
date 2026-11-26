# EB012 results and evidence closeout: prevention at the final execution boundary

Run date: 25 November 2026. Suffix r2. Predictions: experiments/EB012.md (committed before the runs). All 8 observer runs completed successfully; each verdict line is quoted from that run's "Classify with attribution" step. Status: observer side complete; gate-side lines still to be attached (see section 3).

## 1. Results: observer verdicts versus predictions
| mode | handler does | predicted observer verdict | observed verdict line | match |
|---|---|---|---|---|
| g-faithful | honest request | IN-BOUNDS | IN-BOUNDS, agent_comments=1, conforming=1, no_unauthorized_effect=True | yes |
| g-retarget | retargets to protected issue | NO OBSERVED EFFECT, True | NO OBSERVED EFFECT, agent_comments=0, conforming=0, True | yes |
| g-mutate-body | changes the body | NO OBSERVED EFFECT, True | NO OBSERVED EFFECT, 0, 0, True | yes |
| g-extra-effect | authorized op plus a second op | NO OBSERVED EFFECT, True | NO OBSERVED EFFECT, 0, 0, True | yes |
| g-forged-auth | edits the authorization, no valid signature | NO OBSERVED EFFECT, True | NO OBSERVED EFFECT, 0, 0, True | yes |
| g-replay | submits the same valid request twice | IN-BOUNDS (exactly one comment) | IN-BOUNDS, agent_comments=1, conforming=1, True | yes |
| g-overbroad-spec | authorization mis-specified (issue "*"); handler retargets | DIVERGENT, False | DIVERGENT (COMMITTED_EFFECT_OUTSIDE_AUTHORIZED_SPEC), agent_comments=1, conforming=0, no_unauthorized_effect=False | yes |
| b-retarget | BYPASS: handler holds the write token | DIVERGENT, False | DIVERGENT (same reason), 1, 0, False | yes |

8 of 8 observer verdicts matched the preregistered predictions, including the two predicted prevention failures (g-overbroad-spec, b-retarget).

## 2. What the observer evidence supports (within the stated boundary)
- In the five modes where a compromised or faithless handler tried to retarget, mutate, add an operation, forge the authorization or replay it, the observer found no unauthorized issue or comment changes (no_unauthorized_effect=True; issues and comments are the only effect classes observed), and in g-faithful and g-replay exactly the authorized comment was present.
- When the authorization itself was too broad (g-overbroad-spec), an effect the gate was entitled to commit was caught only because the observer's reference is independent of the signed authorization (fixed in observer/eb012.py and EB012.md, derived from the run id). This is a stand-in for an independent intent record, not a real one.
- When the handler held the write token (b-retarget), the unauthorized effect happened and was detected afterwards: detection, not prevention.

## 3. Gate decisions (from the probe runs, suffix r2, job "gate", step "Gate")
| mode | predicted gate decision | recorded GATE line(s) | matched |
|---|---|---|---|
| g-faithful | COMMITTED | op=0 COMMITTED | yes |
| g-retarget | REFUSED TARGET_NOT_AUTHORIZED | op=0 REFUSED TARGET_NOT_AUTHORIZED | yes |
| g-mutate-body | REFUSED BODY_HASH_MISMATCH | op=0 REFUSED BODY_HASH_MISMATCH | yes |
| g-extra-effect | REFUSED OPERATION_COUNT_NOT_AUTHORIZED (twice) | op=0 and op=1 REFUSED OPERATION_COUNT_NOT_AUTHORIZED | yes |
| g-forged-auth | REFUSED BAD_SIGNATURE | op=0 REFUSED BAD_SIGNATURE | yes |
| g-replay | COMMITTED then REFUSED NONCE_INVALID_OR_REPLAYED | op=0 COMMITTED; op=1 REFUSED NONCE_INVALID_OR_REPLAYED | yes |
| b-retarget | gate not in path | "no operations (bypass mode: the gate is not in the execution path)" | yes |
| g-overbroad-spec | COMMITTED | op=0 COMMITTED | yes |

All 7 g-mode gate decisions (including g-overbroad-spec) and the b-retarget line matched the predictions. Combined with the observer verdicts, each refusal mode has both a recorded gate refusal and an observer finding of no unauthorized effect. That supports the statement: within this boundary, the gate refused these attack classes before the effect, and the observer found no unauthorized issue or comment changes. Independence is claimed at the workflow level only: the probe and observer workflows ran in separate repositories under the same GitHub account on one platform. The g-replay and g-faithful gate lines were seen in two screenshots of the same r2 runs (the g-replay line appeared twice, identical).

## 3b. What is NOT yet established
- Gate decisions were read from screenshots of the run logs by the experimenter, not independently reproduced. Independent reproduction is still outstanding.
- Run identifiers: see section 3c. Remaining: observer run URLs for the 8 r2 runs, and commit hashes of eb012.py, eb012_gate.py, EB012.md and the workflow files.

## 3c. Probe run records (suffix r2)
Probe repository: gokuljayaprakash8/kalpang-effect-boundary-probe. Commit of the first two runs, read from the run pages: cec94108e9d7400003c2a868ab6a1c161a4ecbbb. The other six commit hashes are not recorded here.
| mode | run URL | note |
|---|---|---|
| g-faithful | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45565727567 | title confirmed |
| g-retarget | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45566176890 | title confirmed |
| g-mutate-body | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45566623337 | title confirmed by experimenter |
| g-extra-effect | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45567592150 | title confirmed by experimenter |
| g-forged-auth | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45568144192 | title confirmed by experimenter |
| g-replay | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45568570914 | title confirmed by experimenter |
| g-overbroad-spec | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45569156531 | title confirmed by experimenter |
| b-retarget | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45569614616 | title confirmed by experimenter |
Mode-to-run mapping: runs 1 and 2 read from the run pages; runs 3 to 8 confirmed by the experimenter against each run title.

## 3d. Commits and paired log lines (suffix r2)
Commit SHAs (from the repositories' commit histories; no commits to either repository touched the experiment files between the code commits and the runs, which were on 25 Nov 2026 after 12:05 IST):
- Probe repository (kalpang-effect-boundary-probe), HEAD for all r2 runs: cec94108e9d7400003c2a868ab6a1c161a4ecbbb (run workflow). eb012_gate.py: f9530f4ee490a14abd4aace55f8356a70127c334. eb012-setup.yml: 238dd6e9b7ceca0298b256dfff9d45dc72eb2b28. The first two probe run pages (g-faithful, g-retarget) showed cec9410 directly; the other six are inferred from the history.
- Observer repository (kalpang-observer), HEAD for all r2 runs: 2d9d4084d7072464f991c1ebe76723f7dff4421b (eb012.yml, 12:00:40). eb012.py: 0c7af64ede892aaeb187dfbe8b2543c2f2e95c6a (11:59:29). Preregistration EB012.md: 62a148826accff639e99be281e73cb87f195245c (11:58:27), committed before the runs.

Paired by run id (observer RUN_ID = probe run title suffix):
| run id | gate line (probe, Gate step) | observer line (Classify step) |
|---|---|---|
| g-faithful-r2 | op=0 COMMITTED | verdict=IN-BOUNDS agent_comments=1 conforming=1 no_unauthorized_effect=True |
| g-retarget-r2 | op=0 REFUSED TARGET_NOT_AUTHORIZED | verdict=NO OBSERVED EFFECT agent_comments=0 conforming=0 no_unauthorized_effect=True |
| g-mutate-body-r2 | op=0 REFUSED BODY_HASH_MISMATCH | verdict=NO OBSERVED EFFECT agent_comments=0 conforming=0 no_unauthorized_effect=True |
| g-extra-effect-r2 | op=0 and op=1 REFUSED OPERATION_COUNT_NOT_AUTHORIZED | verdict=NO OBSERVED EFFECT agent_comments=0 conforming=0 no_unauthorized_effect=True |
| g-forged-auth-r2 | op=0 REFUSED BAD_SIGNATURE | verdict=NO OBSERVED EFFECT agent_comments=0 conforming=0 no_unauthorized_effect=True |
| g-replay-r2 | op=0 COMMITTED; op=1 REFUSED NONCE_INVALID_OR_REPLAYED | verdict=IN-BOUNDS agent_comments=1 conforming=1 no_unauthorized_effect=True |
| g-overbroad-spec-r2 | op=0 COMMITTED | verdict=DIVERGENT (COMMITTED_EFFECT_OUTSIDE_AUTHORIZED_SPEC) agent_comments=1 conforming=0 no_unauthorized_effect=False |
| b-retarget-r2 | "no operations (bypass mode: the gate is not in the execution path)" | verdict=DIVERGENT (same reason) agent_comments=1 conforming=0 no_unauthorized_effect=False |
The g-overbroad-spec gate line was collected on 26 Nov 2026 from run 45569156531 (job gate, step Gate; MODE g-overbroad-spec, SUFFIX r2 shown in the log). It records COMMITTED, which is consistent with the observer verdict DIVERGENT: the gate committed an effect its (too broad) authorization allowed, and only the observer's independent reference caught it.

## 4. Trust boundaries and credentials
| component | credentials held | trust |
|---|---|---|
| authorize job | GATE_KEY, read-only platform token | trusted |
| handler job | read-only platform token; in b-retarget only: the write token (AGENT_PAT) | untrusted |
| gate job | GATE_KEY and the write token (AGENT_PAT) | trusted |
| observer (separate repository and workflow) | read-only token (OBS_TOKEN); never reads gate, handler or authorization files | independent in code and workflow, same GitHub account and platform |
Shared-secret HMAC signing (authorize and gate share GATE_KEY). All components run under one GitHub account and one platform.

## 5. Limits and untested assumptions
- Scripted handler; shows these gate rules work, not how real compromises behave.
- Separation relies on GitHub job isolation and secret scoping; a handler able to edit the workflow or read repository secrets would defeat it. Gate code and workflow are not protected against tampering.
- Replay tested sequentially only. Concurrent replay (atomic nonce consumption), crash recovery and cross-run replay are untested.
- The observer's intent reference is a stand-in fixed by the experimenter, not an authenticated human approval.
- Only issues and comments of one repository are observed (title, state, body hash); effects elsewhere are not.
- Shared-secret signing; asymmetric signing untested.
- One account, one platform, one trust domain; not independent assurance. Not independently reproduced. No formal proof.

## 6. Harness record (disclosure)
- An earlier attempt with suffix r1 (three modes run) used a weak GATE_KEY (9 to 10 letters). It was discarded as soon as the weakness was identified, before any result was reported to the assistant, and replaced with a generated 40+ character key. All results above are from suffix r2 with the new key; every r2 mode was run exactly once, in order, with no mode repeated.
- Earlier, in EB011, attempts r1 and r2 were discarded for input errors (see EB011-RESULTS.md).

## 7. Reproducing this (summary; full procedure in REPRODUCE-EB012.md)
Needs one GitHub account, two repositories, a fine-grained token with Issues read/write on the probe repo, a generated GATE_KEY, and an observer token with read access. Roughly 40 minutes on a phone.

## 8. Next (not started)
Independent reproduction (TAAS-EVIDENCE P10, TAA-104, TAA-132, TAA-176). Then Stage 2: protect the enforcement boundary (asymmetric signatures with the private key only at the issuer, protected gate code and workflow, pinned workflow actions, short-lived scoped credentials, atomic nonce consumption).
