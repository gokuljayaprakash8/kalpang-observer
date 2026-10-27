# Experiment 005: chain-bound effect verification

Run on 27 October 2026. One run per scenario. A demonstration, not a proof.

## Question

If a gateway admits a delegation chain (attenuation rules I1-I5 from
draft-niyikiza-oauth-attenuating-agent-tokens-01, checked at claims level), does a
post-execution observer still add information? And can the observer verdict be tied
to the admission record?

## Results

| Run | Chain mode | Gateway | Probe run | Observer verdict | Expected | Met |
|---|---|---|---|---|---|---|
| A1 | valid | admitted | normal | IN-BOUNDS | IN-BOUNDS | yes |
| B1 | valid | admitted | extra-effect | DIVERGENT | DIVERGENT | yes |
| C1 | none | no admission record | normal | DIVERGENT | DIVERGENT | yes |
| D1 | widened | REJECTED (I4 at depth 2) | none started | IN-BOUNDS | IN-BOUNDS | yes |

I read the gateway log text for D1. For A1 and B1 the gateway step passed, and the
verdicts depend on it.

## What it shows

- B1: the chain was valid and admission passed, but one issue that was not authorized
  was created. Admission alone would have said nothing; the observer reported DIVERGENT.
- C1: the effect itself was clean, but no chain authorized it, so it is not IN-BOUNDS.
- D1: a child chain that widened its parent was refused before execution. The observer
  waited 2.5 minutes, saw no executor run, and agreed.

## Limits

- Agents are simulated. The gateway is my own code and checks claims only. It does not
  verify signatures or proof of possession.
- Observer, gateway and probe are under one GitHub account. Not an independent trust
  domain.
- The extra effect in B1 was injected on purpose. This shows the observer sees such an
  effect, not that it finds unplanned ones.
- D1 IN-BOUNDS means: refused, and no effect observed in the declared boundary
  (issues and issue comments of one repository). It says nothing about an agent that
  ignores the refusal.
- One run per scenario, one platform. Attestations were created but not yet verified
  with `gh attestation verify`.
- No novelty is claimed for admission checking (the IETF draft above) or for
  post-execution effect comparison (EffectMatch, Schrock's drafts). This is a small
  reproducible live check of the two together.

Developed with substantial LLM assistance.
