#!/usr/bin/env python3
"""Recompute file hashes listed in a manifest and compare. Usage: verify_manifest.py manifest.json DIR"""
import hashlib, json, os, sys
m = json.load(open(sys.argv[1])); d = sys.argv[2]; bad = []
def h(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
for name, want in m["files"].items():
    p = os.path.join(d, name)
    if not os.path.exists(p) or h(p) != want: bad.append(name)
sp = os.path.join(d, m["script"])
if os.path.exists(sp) and h(sp) != m["script_sha256"]: bad.append(m["script"])
print("MANIFEST OK" if not bad else "MANIFEST MISMATCH: " + ", ".join(bad)); sys.exit(1 if bad else 0)
