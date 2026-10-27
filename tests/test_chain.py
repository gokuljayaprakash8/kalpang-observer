import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "observer"))
import run_probe as rp
import chain_gateway as gw

RID = "r5"
NOW = 1_800_000_000

def issue(n, title, body, upd="t1"):
    return {"number": n, "id": 1000 + n, "title": title, "state": "open", "body_sha256": rp.sha(body), "updated_at": upd}

def snap(issues, comments=()):
    return {"stable": True, "status": "OBSERVED", "core": {"issues": list(issues), "comments": list(comments)}, "runs": [], "runs_status": "OBSERVED"}

BASE = [issue(1, "old", "x")]
TARGET = issue(11, rp.TARGET_TITLE.format(run_id=RID), rp.TARGET_BODY.format(run_id=RID))
SIDE = issue(12, "[EB004 SIDE] " + RID, "side")
BAD = issue(11, rp.TARGET_TITLE.format(run_id=RID), "wrong body")
ADM = gw.admit(gw.build_chain(RID, "valid", NOW), RID)
REJ = gw.admit(gw.build_chain(RID, "widened", NOW), RID)

class Gateway(unittest.TestCase):
    def test_valid_chain_admitted_with_authorized_effect(self):
        self.assertTrue(ADM["admitted"], ADM["reasons"])
        self.assertEqual(ADM["authorized_effect"]["title"], rp.TARGET_TITLE.format(run_id=RID))
    def test_widened_last_hop_rejected_by_I4(self):
        self.assertFalse(REJ["admitted"]); self.assertIn("I4 at depth 2", REJ["reasons"]); self.assertNotIn("authorized_effect", REJ)
    def test_request_outside_leaf_scope_rejected(self):
        doc = gw.build_chain("other", "valid", NOW)             # chain authorises run "other"
        rec = gw.admit(doc, RID)                                   # but the agent requests run RID
        self.assertFalse(rec["admitted"]); self.assertTrue(any(r.startswith("LEAF_CONSTRAINT") for r in rec["reasons"]))
    def test_chain_without_its_root_rejected(self):
        doc = gw.build_chain(RID, "valid", NOW); doc["chain"] = doc["chain"][1:]   # root token removed
        self.assertIn("CHAIN_LENGTH", gw.admit(doc, RID)["reasons"])
    def test_expired_chain_rejected(self):
        doc = gw.build_chain(RID, "valid", NOW); doc["now"] = NOW + 5000
        self.assertIn("I3 at depth 1", gw.admit(doc, RID)["reasons"])

class Scenarios(unittest.TestCase):
    def cls(self, after, adm, expect=None):
        return rp.classify_chain(snap(BASE), snap(BASE + after), RID, adm, expect)
    def test_A_clean_admitted_effect(self):
        r = self.cls([TARGET], ADM, "IN-BOUNDS")
        self.assertEqual((r["effect_verdict"], r["admission_only_says"], r["observer_disagrees_with_admission"]), ("IN-BOUNDS", "PASS", False))
        self.assertTrue(r["harness_expectation_met"])
    def test_B_admitted_but_side_effect_is_missed_by_admission(self):
        r = self.cls([TARGET, SIDE], ADM, "DIVERGENT")
        self.assertEqual((r["effect_verdict"], r["reason"], r["admission_only_says"]), ("DIVERGENT", "EXTRA_EFFECT", "PASS"))
        self.assertTrue(r["observer_disagrees_with_admission"]); self.assertEqual(r["target_only_view"], "TARGET_MATCH")
    def test_C_no_admission_record_but_effect_exists(self):
        r = self.cls([TARGET], None, "DIVERGENT")
        self.assertEqual((r["effect_verdict"], r["reason"], r["admission_only_says"]), ("DIVERGENT", "UNADMITTED_EFFECT", "NO RECORD"))
        self.assertTrue(r["observer_disagrees_with_admission"])
    def test_D_rejected_and_nothing_happened(self):
        r = self.cls([], REJ, "IN-BOUNDS")
        self.assertEqual((r["effect_verdict"], r["reason"], r["admission_only_says"]), ("IN-BOUNDS", "NO_EFFECT_AS_REQUIRED", "BLOCKED"))
        self.assertFalse(r["observer_disagrees_with_admission"])
    def test_D2_rejected_but_effect_happened(self):
        r = self.cls([TARGET], REJ)
        self.assertEqual((r["effect_verdict"], r["reason"]), ("DIVERGENT", "EFFECT_DESPITE_REJECTION"))
        self.assertTrue(r["observer_disagrees_with_admission"])
    def test_admitted_wrong_body(self):
        r = self.cls([BAD], ADM); self.assertEqual((r["effect_verdict"], r["reason"]), ("DIVERGENT", "TARGET_MISMATCH"))
    def test_admitted_nothing_happened_is_not_a_pass(self):
        self.assertEqual(self.cls([], ADM)["effect_verdict"], "NO OBSERVED EFFECT")
    def test_unstable_or_mismatched_is_indeterminate(self):
        u = {"stable": False, "status": "INDETERMINATE", "reason": "SNAPSHOT_UNSTABLE"}
        self.assertEqual(rp.classify_chain(u, snap(BASE), RID, ADM)["effect_verdict"], "INDETERMINATE")
        wrong = dict(ADM, run_id="zzz")
        self.assertEqual(self.cls([TARGET], wrong)["reason"], "ADMISSION_RUN_MISMATCH")
    def test_no_bodies_or_keys_in_outputs(self):
        out = json.dumps([ADM, REJ, self.cls([TARGET, SIDE], ADM)])
        self.assertNotIn("Controlled target", out); self.assertNotIn("SECRET", out)

class Cli(unittest.TestCase):
    def test_exit_codes(self):
        d = tempfile.mkdtemp(); p = lambda n: os.path.join(d, n)
        for n, v in (("b.json", snap(BASE)), ("a.json", snap(BASE + [TARGET])), ("adm.json", ADM)):
            with open(p(n), "w") as f: json.dump(v, f)
        base = ["classify-chain", "--before", p("b.json"), "--after", p("a.json"), "--run-id", RID, "--admission", p("adm.json"), "--out", p("o.json")]
        self.assertEqual(rp.main(base + ["--expect", "IN-BOUNDS"]), 0)
        self.assertEqual(rp.main(base + ["--expect", "DIVERGENT"]), 1)
        none = [x if x != p("adm.json") else "none" for x in base]
        self.assertEqual(rp.main(none + ["--expect", "DIVERGENT"]), 0)

if __name__ == "__main__":
    unittest.main()
