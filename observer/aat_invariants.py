"""Independent checker for the claim-level invariants I1-I5 and the constraint attenuation
rules of draft-niyikiza-oauth-attenuating-agent-tokens-01 (Sections 3.4, 4.2-4.6, 4.5).

Scope and honesty:
- Written from my reading of the draft text, not from any reference implementation.
- Checks CLAIMS only. Signature verification (I6, Section 7 steps 3-4 signatures) is out of scope.
- Where the text I could read did not settle a point, the code does NOT guess: see OPEN_QUESTIONS.md.
- Standard library only.
"""
import base64, hashlib, json

# Section 3.4 / 4.5 as read. Pairs are (parent_type -> child types explicitly allowed by the text).
# Cross-type pairs not listed here are REJECTED, as Section 4.5 says unlisted pairs must be.
EXACT_UNDER = {"exact", "range", "one_of", "wildcard"}  # a child `exact` may sit under these parents


def _eq(a, b):
    """JSON-strict equality: 1, 1.0 and true are different values (Python == conflates them).
    ASSUMPTION: the draft does not say how equality is defined; see OPEN_QUESTIONS.md."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True) and type(a) is type(b)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _in_range(v, r):
    if not _num(v):
        return False
    lo, hi = r.get("min"), r.get("max")
    if lo is not None and (v < lo or (v == lo and not r.get("min_inclusive", True))):
        return False
    if hi is not None and (v > hi or (v == hi and not r.get("max_inclusive", True))):
        return False
    return True


def subsumes(parent, child):
    """True if `child` constraint is valid under `parent` per Section 4.5 (as read)."""
    pt, ct = parent.get("constraint_type"), child.get("constraint_type")
    if ct == "exact" and pt in EXACT_UNDER:
        v = child.get("value")
        if pt == "exact":
            return _eq(v, parent.get("value"))
        if pt == "range":
            return _in_range(v, parent)
        if pt == "one_of":
            return any(_eq(v, x) for x in parent.get("values", []))
        return True  # parent wildcard
    if pt != ct:
        return False
    if pt == "range":
        def lo_ok():
            pm, cm = parent.get("min"), child.get("min")
            if pm is None:
                return True
            if cm is None or cm < pm:
                return False
            if cm == pm and parent.get("min_inclusive", True) is False and child.get("min_inclusive", True) is True:
                return False
            return True
        def hi_ok():
            pm, cm = parent.get("max"), child.get("max")
            if pm is None:
                return True
            if cm is None or cm > pm:
                return False
            if cm == pm and parent.get("max_inclusive", True) is False and child.get("max_inclusive", True) is True:
                return False
            return True
        return lo_ok() and hi_ok()
    if pt == "one_of":
        return set(map(json.dumps, child.get("values", []))) <= set(map(json.dumps, parent.get("values", [])))
    if pt == "not_one_of":
        return set(map(json.dumps, child.get("excluded", []))) >= set(map(json.dumps, parent.get("excluded", [])))
    if pt == "contains":
        return set(map(json.dumps, child.get("required", []))) >= set(map(json.dumps, parent.get("required", [])))
    if pt == "subset":
        return set(map(json.dumps, child.get("allowed", []))) <= set(map(json.dumps, parent.get("allowed", [])))
    if pt == "wildcard":
        return True
    if pt == "all":
        pc, cc = parent.get("constraints", []), child.get("constraints", [])
        if len(cc) < len(pc):
            return False
        return all(subsumes(p, c) for p, c in zip(pc, cc))  # one-to-one, in order; extra child clauses allowed
    if pt == "any":
        pc, cc = parent.get("constraints", []), child.get("constraints", [])
        return all(any(subsumes(p, c) for p in pc) for c in cc)
    return False  # unknown / unregistered type: reject (Section 3.5 / 4.5)


def _entry(token):
    ad = token.get("authorization_details", [])
    return ad[0] if len(ad) == 1 and ad[0].get("type") == "attenuating_agent_token" else None


def jwk_thumbprint_uri(jwk, prefix="urn:ietf:params:oauth:jwk-thumbprint:sha-256:"):
    """RFC 7638 thumbprint. ASSUMPTION: URI prefix is the RFC 9278 form; the draft's exact
    `jwk_thumbprint_uri` format was not confirmed from the text I could read."""
    members = {"OKP": ("crv", "kty", "x"), "EC": ("crv", "kty", "x", "y"), "RSA": ("e", "kty", "n")}[jwk["kty"]]
    s = json.dumps({k: jwk[k] for k in members}, separators=(",", ":"), sort_keys=True)
    return prefix + base64.urlsafe_b64encode(hashlib.sha256(s.encode()).digest()).rstrip(b"=").decode()


def par_hash(parent_signing_input: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(parent_signing_input.encode("ascii")).digest()).rstrip(b"=").decode()


def check_pair(parent, child, now, limits, parent_signing_input=None):
    """Return a sorted list of violation codes for one parent -> child link. Empty list = valid."""
    v = set()
    # I1
    if child.get("iss") != jwk_thumbprint_uri(parent["cnf"]["jwk"]):
        v.add("I1")
    # I2
    cd, pd = child.get("del_depth"), parent.get("del_depth")
    if cd != pd + 1 or cd > parent.get("del_max_depth") or cd > child.get("del_max_depth") \
            or cd > limits["MAX_DELEGATION_DEPTH"] or child.get("del_max_depth") > parent.get("del_max_depth"):
        v.add("I2")
    # I3
    if (child["exp"] > parent["exp"] or child["exp"] <= now or child["exp"] <= child["iat"]
            or child["iat"] < parent["iat"] or child["iat"] > now + limits["MAX_IAT_SKEW"]
            or child["exp"] > child["iat"] + limits["MAX_TOKEN_LIFETIME"]):
        v.add("I3")
    # I4
    pe, ce = _entry(parent), _entry(child)
    if pe is None or ce is None:
        v.add("I4")
    else:
        pt, ct = pe.get("tools", {}), ce.get("tools", {})
        if not set(ct) <= set(pt):
            v.add("I4")
        else:
            for tool, cargs in ct.items():
                pargs = pt[tool]
                if pargs and set(cargs) != set(pargs):   # same argument keys when parent map non-empty
                    v.add("I4"); continue
                for k, cc in cargs.items():
                    if k in pargs and not subsumes(pargs[k], cc):
                        v.add("I4")
    # I5
    if parent_signing_input is not None and child.get("par_hash") != par_hash(parent_signing_input):
        v.add("I5")
    return sorted(v)
