# EB013 preregistration (v2 draft, reviewed once, not yet run): a protected enforcement boundary

Status: draft written 25 Nov 2026 before any EB013 code exists. Predictions below must be committed before the first run and must not be edited after results.

## 1. Question
EB012 showed that a gate holding a shared secret refused five scripted attacks by an untrusted handler. EB012 also left these weaknesses: the handler job can read the gate code and the workflow, the authorizer and the gate share one secret (so a gate compromise can forge authorizations), nonce use is not atomic, the write credential is long-lived, and workflow actions are not pinned.

EB013 asks: if each of those five weaknesses is removed one at a time, which attacks that succeeded or were possible before are now refused, and which still succeed?

## 2. Changes from EB012 (each tested separately)
| id | change | what it removes |
|---|---|---|
| C1 | Asymmetric signatures: issuer holds a private key; the gate holds only the public key | gate compromise can no longer forge an authorization |
| C2 | Gate code and workflow loaded from a separate repository at a pinned commit SHA; handler job has no checkout of it | handler cannot read or modify gate logic |
| C3 | All workflow actions pinned to commit SHAs | tampered action version |
| C4 | Short-lived, single-repository write credential, minted for the gate job only | stolen write credential has a short life |
| C5 | Atomic nonce consumption (one create-if-absent call; second use fails) | replay race under two parallel requests |

## 2b. Design: isolated first, then cumulative
Each change C1 to C5 is first tested **alone against the same EB012 baseline** (only that change differs), so that any difference can be attributed to it. After that, one **cumulative run** with C1 to C5 all enabled is reported separately and is not used for attribution. Every mode below names the change it tests.

## 3. Modes and predictions (written before running)
| id | change | attack or condition | prediction |
|---|---|---|---|
| s-faithful | all | handler passes the request unchanged | gate COMMITTED; observer IN-BOUNDS |
| s-forge-with-public-key | C1 | An attacker with the gate's public verification key, but without the issuer's private signing key, creates an authorization for a modified operation | gate REFUSED BAD_SIGNATURE; observer reports no unauthorized effect. This tests key separation only. It does not show that a compromised gate cannot bypass its own validation or misuse its write credential |
| s-read-gate-code | C2 | handler tries to read the gate source, both from its workspace and by a direct remote read with every credential its job holds | gate source absent from the handler workspace, and the remote read is denied. The gate repository is private, has separate permissions, and no read credential for it is exposed to the handler job. A missing workspace file alone would not count |
| s-modify-gate | C2 | handler alters its own working directory or a local copy of gate code, and tries to change the caller workflow, the pinned reference, or redirect execution around the gate | local changes do not change what the gate executes. The gate runs the pinned commit and its source digest equals that commit's digest. The executed version is verified, not assumed |
| s-parallel-replay | C5 | two simultaneous requests carry the same valid nonce and compete for one atomic create-if-absent on shared durable state | exactly one consumes the nonce and proceeds; the other is REFUSED as a duplicate; observer finds exactly one comment. Nonce consumption and external commitment are not one transaction: a crash between them could leave an indeterminate or incomplete operation. EB013 does not claim crash safety |
| s-stolen-token-late | C4 | an otherwise correctly scoped write credential is used after its verified expiry | platform rejects it; observer reports no unauthorized effect. A stolen credential may remain usable during its validity period. Short lifetimes shrink the exposure window; they do not remove theft or misuse before expiry |
| s-action-tag-retarget | C3 | a disposable test action's version tag is moved to a different commit after the workflow pinned the original SHA | execution continues to use the pinned commit, and the executed revision is verified. Also a static audit that every workflow action reference uses a full commit SHA. Pinning prevents mutable-tag substitution; it does not show the pinned code is trustworthy |
| s-overbroad-spec | none | authorization too broad (as in EB012) | still DIVERGENT, provided the observer's independently maintained intent reference is unchanged. That reference is a stand-in, not an authentic record of human intent; EB013 does not claim to solve human-intent integrity |
| L1-same-trust-domain | none | issuer, gate and observer remain under one GitHub account | independent trust-domain assurance NOT ESTABLISHED. A known limitation, not a pass or fail result |

Predicted to remain unfixed by C1 to C5: s-overbroad-spec (DIVERGENT) and L1 (not established). If s-overbroad-spec returns IN-BOUNDS, that is a surprise and is reported as such.

## 4. Outcome rules
- Each mode is reported as matched or mismatched against the prediction above. Mismatches are reported as they are and the run is never repeated to obtain a match.
- A run counts only if the observer was started first and the harness used a fresh run suffix.
- Prevention is claimed for a mode only with both a recorded gate decision and an observer verdict of no unauthorized effect.

## 5. Stated limits (before running)
Scripted handler; one GitHub account; the platform itself is trusted; the observer still shares the account with the issuer and gate; no real agent; sequential and one parallel case only; asymmetric key is stored as a GitHub secret, so secret handling is still a trust assumption.

## 6. Order of work
1. Wait for at least one independent reproduction attempt of EB012, or a stated reason from Iman not to proceed.
2. Commit this file with the predictions to kalpang-observer.
3. Build C1 first, run only s-faithful and s-forge-with-public-key against the EB012 baseline, then C2, C3, C4, C5 in order, each isolated; then one cumulative run.
4. Feasibility check before building C2: confirm a private gate repository can supply workflow code to the probe repository on this account, and that the handler job has no credential that reads it. If not feasible, report C2 as not testable here rather than weakening the prediction.
