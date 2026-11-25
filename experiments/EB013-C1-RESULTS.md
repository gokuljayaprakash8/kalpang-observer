# EB013 change C1 results: asymmetric authorization signatures (isolated)

Date: 25 Nov 2026. Preregistration: experiments/EB013-PREREG.md (v2, committed before any run). Code: agent/eb013_c1.py (probe repository), observer/eb013.py (observer repository). Suffix c2 is the counted run; c1 is disclosed below.

## 1. Result against the preregistered predictions
| mode | predicted | observed | matched |
|---|---|---|---|
| s-faithful (c2) | gate COMMITTED; observer IN-BOUNDS | gate COMMITTED; observer IN-BOUNDS (agent_comments=1, conforming=1, no_unauthorized_effect=True) | yes |
| s-forge-with-public-key (c2) | gate REFUSED BAD_SIGNATURE; observer NO OBSERVED EFFECT, no_unauthorized_effect=True | gate REFUSED BAD_SIGNATURE; observer NO OBSERVED EFFECT (agent_comments=0, conforming=0, no_unauthorized_effect=True) | yes |
| base-forge-with-gate-key (b2), baseline added by addendum 1 before running | gate COMMITTED the forged request; observer DIVERGENT, no_unauthorized_effect=False | gate COMMITTED; observer DIVERGENT (COMMITTED_EFFECT_OUTSIDE_AUTHORIZED_SPEC, agent_comments=1, conforming=0, no_unauthorized_effect=False) | yes |

## 2. What this supports
Within the stated boundary, an attacker who knows the gate's public verification key but not the issuer's private signing key could not make the gate accept a forged authorization for the protected issue, and the independent observer saw no unauthorized effect. An honest request signed by the issuer was committed and observed as in-bounds. This tests key separation only.

## 2b. Attribution to C1
Under the EB012 shared-secret design, when the handler held the gate's key, the forged authorization was signed validly, the gate committed the unauthorized comment, and the independent observer reported DIVERGENT. Under C1, with the attacker holding only the public key, the same forgery was refused. Within this scripted setup, the difference is attributable to key separation. This models a leaked or compromised verification key; it does not show how a real attacker would obtain one.

## 3. Disclosed harness faults (not counted)
The first s-faithful run (suffix c1) did NOT match the prediction: gate REFUSED BAD_SIGNATURE and the observer reported NO OBSERVED EFFECT. Cause, confirmed with a diagnostic workflow (EB013 key check): the ISSUER_PUBLIC_KEY variable and the ISSUER_PRIVATE_KEY secret came from two different keypairs (MATCH=False). The variable was replaced with the public key derived from the private key (MATCH=True), and a fresh suffix c2 was set up. The c1 run is recorded as a mismatch caused by key provisioning, not a finding about the design, and was not repeated to obtain a match. 

Baseline suffix b1: the gate decision matched (COMMITTED) but the observer returned INDETERMINATE with reason UNKNOWN_MODE, because the committed observer/eb013.py did not yet list the new mode (the edit had not saved). The observer-side mismatch is a harness fault. b1 was not repeated to obtain a match; a fresh suffix b2, set up after the observer file was corrected, is the counted baseline run. No other run was discarded.

## 4. What is NOT established
- The baseline models a handler that already holds the gate's key. How a real attacker would obtain verification material is not tested.
- This does not show that a compromised gate cannot bypass its own validation or misuse its write credential.
- The private key is stored as a GitHub secret, so secret handling remains a trust assumption.
- Scripted handler; one GitHub account and platform; the observer shares the account with issuer and gate; sequential runs only.
- Results are read from screenshots of run logs by the experimenter; not independently reproduced.

## 5. Not yet run
C2 (protected gate code), C3 (pinned actions), C4 (short-lived credentials), C5 (atomic nonce), s-overbroad-spec, and the cumulative run. Preregistered predictions for them are in EB013-PREREG.md and unchanged.

## 6. Run records (suffix c2)
Run URLs supplied by the experimenter in the order s-faithful, then s-forge-with-public-key; run numbers ascend in that order. Run titles were not independently read from the pages.
| mode | probe run | observer run |
|---|---|---|
| s-faithful | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45603430863 | https://github.com/gokuljayaprakash8/kalpang-observer/actions/runs/45603209442 |
| s-forge-with-public-key | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45604515353 | https://github.com/gokuljayaprakash8/kalpang-observer/actions/runs/45604374498 |
Baseline (b2), supplied by the experimenter (titles not independently read):
| mode | probe run | observer run |
|---|---|---|
| base-forge-with-gate-key (b2) | https://github.com/gokuljayaprakash8/kalpang-effect-boundary-probe/actions/runs/45609814664 | https://github.com/gokuljayaprakash8/kalpang-observer/actions/runs/45609674162 |
Still to attach: the key-check run and the c1 and b1 runs; commit hashes of eb013_c1.py, eb013.py and the workflow files.
