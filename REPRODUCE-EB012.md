# Reproducing KALPANG EB012 (about 40 minutes, GitHub web only)

You are asked to run the experiment independently and compare your results to the preregistered predictions in experiments/EB012.md. Do not edit the predictions. Report every difference.

## What you need
- A GitHub account (a separate account from the author's is best).
- Two new repositories: an OBSERVER repo and a PROBE repo (public or private).
- Source files: observer/eb012.py, observer/eb010.py, observer/run_probe.py, .github/workflows/eb012.yml (observer repo); agent/eb012_gate.py, agent/eb008_scripted.py, .github/workflows/eb012-setup.yml, .github/workflows/eb012-run.yml (probe repo). Source: github.com/gokuljayaprakash8/kalpang-observer and kalpang-effect-boundary-probe.

## Credentials (create your own; never share them)
1. PROBE repo secret AGENT_PAT: a fine-grained personal access token limited to the PROBE repo, Issues: read and write only, 30 day expiry.
2. PROBE repo secret GATE_KEY: a generated random string of 40 or more characters.
3. OBSERVER repo secret OBS_TOKEN: a fine-grained token limited to the PROBE repo with read access to Issues and Actions. OBSERVER repo variable OBS_REPO: owner/probe-repo-name.

## Procedure
1. Commit experiments/EB012.md (predictions) to the OBSERVER repo first.
2. PROBE repo, Actions, "EB012 setup", Run, suffix r1. Confirm 16 issues were created.
3. For each mode in this order: g-faithful, g-retarget, g-mutate-body, g-extra-effect, g-forged-auth, g-replay, g-overbroad-spec, b-retarget:
   a. OBSERVER repo, Actions, "EB012 conformance observer", Run: mode, suffix r1, agent_login = your GitHub username.
   b. Wait about 1 minute.
   c. PROBE repo, Actions, "EB012 gate run", Run: same mode, suffix r1.
   d. Copy the GATE line(s) from the probe run (job gate, step Gate) and the verdict= line from the observer run (step Classify with attribution).
4. Run each mode once. Do not repeat a mode to match a prediction.
5. When finished, delete the tokens you created.

## What to report
For each mode: the GATE line(s), the verdict= line, and whether it matches the prediction in EB012.md. Report anything unexpected, any mode that failed to run, and anything unclear in these instructions. A mismatch is a valid and useful result.
