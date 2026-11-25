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
- In the five modes where a compromised or faithless handler tried to retarget, mutate, add an operation, forge the authorization or replay it, the observer found no unauthorized effect (no_unauthorized_effect=True), and in g-faithful and g-replay exactly the authorized comment was present.
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
| g-overbroad-spec | COMMITTED | not recorded in this file (optional screenshot not collected) | not checked |

6 of 6 required g-mode gate decisions and the b-retarget line matched the predictions. Combined with the observer verdicts, each refusal mode has both a recorded gate refusal and an observer finding of no unauthorized effect. That supports the statement: within this boundary, the gate refused these four attack classes before the effect, and the independent observer saw no unauthorized effect. The g-replay and g-faithful gate lines were seen in two screenshots of the same r2 runs (the g-replay line appeared twice, identical).

## 3b. What is NOT yet established
- The g-overbroad-spec gate line was not collected; the observer verdict (DIVERGENT) stands, the gate decision for that mode is unverified here.
- Gate decisions were read from screenshots of the run logs by the experimenter, not independently reproduced. Independent reproduction is still outstanding.
- Run identifiers and commit hashes: to be attached (observer run URLs for the 8 r2 runs; probe run URLs; commit hashes of eb012.py, eb012_gate.py, EB012.md, and the workflow files).

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
