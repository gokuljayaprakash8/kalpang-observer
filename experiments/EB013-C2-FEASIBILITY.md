# EB013 C2 feasibility note (26 Nov 2026)

Preregistered check (EB013-PREREG.md, section 6, item 4): can a private gate repository supply workflow code to the probe repository on a free GitHub account, with the handler job holding no credential that reads it?

## Result
Feasible, with one constraint: the calling repository must itself be private.
- The gate repository (kalpang-gate-private, private) allows access from repositories owned by the same user. GitHub's own text for that setting reads: "Access is allowed only from private repositories."
- A call from the public probe repository failed to start with "workflow was not found".
- A call from a new private repository (kalpang-c2-probe) found the workflow and the called job ran green ("EB013 C2 feasibility #2", job call / ok).

## Errors disclosed
1. My first feasibility workflow in the gate repository had a YAML error (an unquoted colon followed by a space in the echo line). Its first failure and the "invalid workflow file ... line 9" error were my mistake. I earlier described the first red run as harmless; that description was wrong. The file was corrected and the second feasibility run passed.
2. The "workflow was not found" result for the public caller was not caused by that YAML error; it was reproduced as an access limit by the private-caller run.

## Consequences for the C2 experiment
- The C2 experiment must run from a private caller repository. The observer currently reads the public probe repository. C2 runs therefore need the observer pointed at the private caller repository (OBS_REPO variable and a read-only token scoped to it), recorded per run.
- The C1 and EB012 evidence in the public probe repository is unchanged.
- Logs of the C2 runs will not be publicly viewable while the caller repository is private. Evidence for C2 will rest on screenshots and a copy of the logs until the caller repository is made public after the runs (the gate repository stays private either way).
- Not yet tested: that the handler job cannot read the gate repository (s-read-gate-code), that the executed gate version equals the pinned commit (s-modify-gate). This note only shows that a private gate repository can supply workflow code.
