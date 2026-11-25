# EB013 preregistration addendum 1 (written before the baseline run)

Reason: the C1 isolated design needs a baseline comparison. The C1 results (EB013-C1-RESULTS.md, section 4) state that no run yet shows the EB012 shared-secret design accepting a forgery when the attacker holds the gate's verification material.

## Mode added
| id | change | attack | prediction |
|---|---|---|---|
| base-forge-with-gate-key | none (baseline, EB012 HMAC design) | the handler holds the shared GATE_KEY (models a leak or compromise of the gate's verification material), forges an authorization for the protected issue, and signs it with GATE_KEY | gate COMMITTED an unauthorized comment on the protected issue; observer DIVERGENT, no_unauthorized_effect=False |

## Reading the result
- If the prediction holds, the C1 improvement is attributed to key separation: with the shared secret the forgery succeeds, with C1 (s-forge-with-public-key) it is refused.
- If the gate REFUSES instead, the baseline did not reproduce the weakness, and the C1 improvement claim is withdrawn pending a correct baseline.
- This mode models key leakage to the handler. It does not show how a real attacker would obtain the key.
- Mismatches are reported as they are and the run is not repeated to match.
  
