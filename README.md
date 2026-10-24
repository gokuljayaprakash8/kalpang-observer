kalpang-observer
A small read-only observer for KALPANG Experiment 004. It watches the issues and issue comments of
one GitHub repository from a separate repository, and publishes hashes of what it saw
(never issue or comment text), with a build-provenance attestation on the output files.
Status: first live runs on 24 October 2026. One run per scenario. A demonstration, not a proof.
Question
If a controlled workflow (the "executor", in a private probe repository) is authorized to create
one issue, does a read-back of that one issue tell you whether anything else happened?
