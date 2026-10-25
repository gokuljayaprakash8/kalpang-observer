#!/usr/bin/env python3
"""Experiment 005 gateway: admission of one tool request under a delegation chain.

Claim-level only. Reuses the independent checker for draft-niyikiza-oauth-attenuating-agent-tokens-01
(invariants I1-I4 plus the leaf argument check of Section 7 step 6 as I read it). It does NOT verify
signatures, par_hash (I5) or proof of possession (I6). The chain fixtures contain made-up public keys.

  make-chain --run-id R --mode valid|widened --out chain.json
  admit      --chain chain.json --run-id R --out admission.json
"""
import argparse, base64, hashlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aat_invariants as aat
import run_probe as rp

LIMITS = {"MAX_DELEGATION_DEPTH": 8, "MAX_IAT_SKEW": 30, "MAX_TOKEN_LIFETIME": 3600}
TOOL = "create_issue"
CHECKS = "claims-level I1-I4 and leaf argument check; no signatures, no I5/I6"


def fake_jwk(label):
    x = base64.urlsafe_b64encode(hashlib.sha256(label.encode()).digest()).rstrip(b"=").decode()
    return {"kty": "OKP", "crv": "Ed25519", "x": x}


def _token(depth, iss, jwk, tools, now):
    t = {"jti": "hop-%d" % depth, "iss": iss, "iat": now - 100, "exp": now + 1000, "cnf": {"jwk": jwk},
         "del_depth": depth, "del_max_depth": 4,
         "authorization_details": [{"type": "attenuating_agent_token", "tools": {TOOL: tools}}]}
    if depth:
        t["par_hash"] = "unchecked"
    return t


def build_chain(run_id, mode, now):
    exact = lambda v: {"constraint_type": "exact", "value": v}
    wild = {"constraint_type": "wildcard"}
    title, body = rp.TARGET_TITLE.format(run_id=run_id), rp.TARGET_BODY.format(run_id=run_id)
    keys = [fake_jwk("kalpang-hop-%d" % i) for i in range(3)]
    root = _token(0, "https://root.example", keys[0], {"title": wild, "body": wild}, now)
    hop1 = _token(1, aat.jwk_thumbprint_uri(keys[0]), keys[1], {"title": exact(title), "body": exact(body)}, now)
    leaf_tools = {"title": exact(title), "body": exact(body)}
    if mode == "widened":                      # the last hop quietly widens its authority
        leaf_tools = {"title": wild, "body": wild}
    leaf = _token(2, aat.jwk_thumbprint_uri(keys[1]), keys[2], leaf_tools, now)
    return {"now": now, "limits": LIMITS, "chain": [root, hop1, leaf], "mode": mode}


def satisfies(c, v):
    t = c.get("constraint_type")
    if t == "wildcard":
        return True
    if t == "exact":
        return aat._eq(v, c.get("value"))
    if t == "one_of":
        return any(aat._eq(v, x) for x in c.get("values", []))
    if t == "range":
        return aat._in_range(v, c)
    return False                                # anything else: deny (fail closed)


def admit(chain_doc, run_id):
    chain, now, limits = chain_doc["chain"], chain_doc["now"], chain_doc["limits"]
    reasons = []
    for p, c in zip(chain, chain[1:]):
        for code in aat.check_pair(p, c, now, limits):
            reasons.append("%s at depth %d" % (code, c["del_depth"]))
    if len(chain) != chain[-1]["del_depth"] + 1:
        reasons.append("CHAIN_LENGTH")
    # the request the agent makes: create the controlled target issue
    req = {"title": rp.TARGET_TITLE.format(run_id=run_id), "body": rp.TARGET_BODY.format(run_id=run_id)}
    leaf_tools = chain[-1]["authorization_details"][0]["tools"]
    cons = leaf_tools.get(TOOL)
    if cons is None:
        reasons.append("TOOL_NOT_IN_LEAF")
    else:
        if set(req) - set(cons):
            reasons.append("UNNAMED_ARGUMENT")
        for k, c in cons.items():
            if k not in req or not satisfies(c, req[k]):
                reasons.append("LEAF_CONSTRAINT:" + k)
    ok = not reasons
    rec = {"run_id": run_id, "admitted": ok, "reasons": reasons, "chain_depth": chain[-1]["del_depth"],
           "chain_mode": chain_doc.get("mode"), "checks": CHECKS}
    if ok:
        rec["authorized_effect"] = {"tool": TOOL, "title": req["title"], "body_sha256": rp.sha(req["body"])}
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make-chain"); m.add_argument("--run-id", required=True)
    m.add_argument("--mode", choices=["valid", "widened"], required=True); m.add_argument("--out", required=True)
    a_ = sub.add_parser("admit"); a_.add_argument("--chain", required=True)
    a_.add_argument("--run-id", required=True); a_.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "make-chain":
        res = build_chain(a.run_id, a.mode, int(time.time()))
    else:
        with open(a.chain) as f:
            res = admit(json.load(f), a.run_id)
        print("admit -> %s %s" % ("ADMITTED" if res["admitted"] else "REJECTED", res["reasons"]))
    with open(a.out, "w") as f:
        json.dump(res, f, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
