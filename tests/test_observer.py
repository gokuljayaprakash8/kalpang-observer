import hashlib, json, os, sys, threading, unittest, tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "observer"))
import run_probe as rp

RID = "r1"
def issue(n, title, body, upd="t1", pr=False):
    d = {"number": n, "id": 1000 + n, "title": title, "state": "open", "body": body, "updated_at": upd}
    if pr: d["pull_request"] = {}
    return d
def comment(i, n, body, upd="t1"):
    return {"id": i, "issue_url": "http://x/repos/o/r/issues/%d" % n, "body": body, "updated_at": upd}
def run(i, title, status="completed", concl="success"):
    return {"id": i, "display_title": title, "status": status, "conclusion": concl, "created_at": "t"}

class Fake:
    def __init__(self):
        self.state = {"issues": [], "comments": [], "runs": []}
        self.fail = None; self.requests = []; self.mutate = None; self.redirect_off_origin = False
        outer = self
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_GET(self):
                outer.requests.append(("GET", self.path, self.headers.get("Authorization")))
                if outer.fail == "500":
                    self.send_response(500); self.end_headers(); return
                if outer.mutate: outer.mutate()
                path, _, q = self.path.partition("?")
                page = int(dict(p.split("=") for p in q.split("&") if p.startswith("page=")).get("page", 1)) if "page=" in q else 1
                key = "issues" if path.endswith("/issues") else "comments" if path.endswith("/issues/comments") else "runs"
                items = outer.state[key]
                chunk = items[(page - 1) * 2: page * 2]
                body = {"workflow_runs": chunk} if key == "runs" else chunk
                self.send_response(200)
                if page * 2 < len(items):
                    host = "http://evil.example" if outer.redirect_off_origin else "http://127.0.0.1:%d" % outer.port
                    self.send_header("Link", '<%s%s?page=%d>; rel="next"' % (host, path, page + 1))
                self.end_headers(); self.wfile.write(json.dumps(body).encode())
            def do_POST(self): outer.requests.append(("POST", self.path, None)); self.send_response(405); self.end_headers()
        self.srv = HTTPServer(("127.0.0.1", 0), H); self.port = self.srv.server_port
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
    api = property(lambda s: "http://127.0.0.1:%d" % s.port)
    def close(self): self.srv.shutdown()

def snap(f, **kw):
    rp.time.sleep = lambda s: None
    return rp.stable_snapshot(f.api, "o/r", "SECRET-TOKEN", sleep=lambda s: None, **kw)

TARGET = lambda rid=RID: issue(11, "[EB004 TARGET] %s" % rid, rp.TARGET_BODY.format(run_id=rid))
SIDE = lambda rid=RID: issue(12, "[EB004 SIDE] %s" % rid, "side")

class T(unittest.TestCase):
    def setUp(self): self.f = Fake()
    def tearDown(self): self.f.close()
    def pair(self, before_state, after_state):
        self.f.state = before_state; b = snap(self.f)
        self.f.state = after_state; a = snap(self.f)
        return b, a
    def base(self): return {"issues": [issue(1, "old", "x")], "comments": [], "runs": [run(1, "EB004 / s / old")]}
    def after(self, issues, comments=(), runs=None):
        s = self.base(); s["issues"] = s["issues"] + issues; s["comments"] = list(comments)
        s["runs"] = s["runs"] + (runs if runs is not None else [run(2, "EB004 / s / %s" % RID)]); return s
    def c(self, b, a, exp=None): return rp.classify(b, a, "s", RID, exp)

    def test_clean_is_in_bounds(self):
        b, a = self.pair(self.base(), self.after([TARGET()]))
        r = self.c(b, a, "IN-BOUNDS")
        self.assertEqual((r["effect_verdict"], r["target_only_view"], r["harness_expectation_met"]), ("IN-BOUNDS", "TARGET_MATCH", True))
        self.assertIn("declared boundary only", r["completeness"])
    def test_side_issue_is_divergent_and_missed_by_target_only(self):
        b, a = self.pair(self.base(), self.after([TARGET(), SIDE()]))
        r = self.c(b, a, "DIVERGENT")
        self.assertEqual(r["effect_verdict"], "DIVERGENT"); self.assertTrue(r["missed_by_target_only"]); self.assertTrue(r["harness_expectation_met"])
    def test_wrong_body_is_divergent(self):
        t = TARGET(); t["body"] = "wrong"
        b, a = self.pair(self.base(), self.after([t]))
        r = self.c(b, a); self.assertEqual((r["target_only_view"], r["effect_verdict"]), ("TARGET_MISMATCH", "DIVERGENT"))
    def test_no_effect_is_not_a_pass(self):
        b, a = self.pair(self.base(), self.after([]))
        self.assertEqual(self.c(b, a)["effect_verdict"], "NO OBSERVED EFFECT")
    def test_extra_comment_and_edit_are_divergent(self):
        b, a = self.pair(self.base(), self.after([TARGET()], [comment(5, 1, "hi")]))
        self.assertEqual(self.c(b, a)["effect_verdict"], "DIVERGENT")
        st = self.after([TARGET()]); st["issues"][0] = issue(1, "old", "x", upd="t2")
        b, a = self.pair(self.base(), st); self.assertEqual(self.c(b, a)["effect_verdict"], "DIVERGENT")
    def test_prs_and_pr_comments_are_ignored(self):
        st = self.after([TARGET(), issue(30, "pr", "b", pr=True)], [comment(9, 30, "pr comment")])
        b, a = self.pair(self.base(), st); self.assertEqual(self.c(b, a)["effect_verdict"], "IN-BOUNDS")
    def test_pagination_collects_everything(self):
        many = [issue(100 + i, "n%d" % i, "b") for i in range(7)]
        st = self.base(); st["issues"] = st["issues"] + many; self.f.state = st
        s = snap(self.f); self.assertEqual(len(s["core"]["issues"]), 8)
    def test_off_origin_next_link_is_refused(self):
        st = self.base(); st["issues"] = st["issues"] + [issue(100 + i, "n", "b") for i in range(5)]
        self.f.state = st; self.f.redirect_off_origin = True
        s = snap(self.f); self.assertEqual((s["status"], s["reason"].split(":")[0]), ("INDETERMINATE", "SNAPSHOT_UNAVAILABLE"))
        self.assertTrue(all("evil" not in r[1] for r in self.f.requests))
    def test_server_errors_are_indeterminate(self):
        self.f.fail = "500"; rp.time.sleep = lambda s: None
        orig = rp.get
        rp.get = lambda url, token, retries=3, sleep=None: orig(url, token, retries, sleep=lambda s: None)
        try: s = snap(self.f)
        finally: rp.get = orig
        self.assertEqual(s["status"], "INDETERMINATE")
        self.assertEqual(self.c(s, s)["effect_verdict"], "INDETERMINATE")
    def test_concurrent_edits_make_snapshot_unstable(self):
        self.f.state = self.base(); n = [0]
        def m(): n[0] += 1; self.f.state["issues"][0]["updated_at"] = "t%d" % n[0]
        self.f.mutate = m; s = snap(self.f)
        self.assertEqual(s["reason"], "SNAPSHOT_UNSTABLE")
    def test_run_correlation_failures_are_indeterminate(self):
        for runs, reason in (([], "EXECUTOR_RUN_NOT_FOUND"),
                             ([run(2, "EB004 / s / %s" % RID), run(3, "EB004 / s / %s" % RID)], "EXECUTOR_RUN_AMBIGUOUS"),
                             ([run(2, "EB004 / s / %s" % RID, concl="failure")], "RUN_NOT_SUCCESSFUL")):
            b, a = self.pair(self.base(), self.after([TARGET()], runs=runs))
            r = self.c(b, a); self.assertEqual((r["effect_verdict"], r["reason"]), ("INDETERMINATE", reason))
        b, a = self.pair(self.base(), self.after([TARGET()], runs=[]))
        a["runs"] = b["runs"] + [run(1, "EB004 / s / %s" % RID)]; b["runs"] = [run(1, "EB004 / s / %s" % RID)]
        self.assertEqual(self.c(b, a)["reason"], "RUN_PREDATES_BASELINE")
    def test_read_only_and_token_and_bodies_not_leaked(self):
        b, a = self.pair(self.base(), self.after([TARGET(), SIDE()]))
        self.assertTrue(all(m == "GET" for m, _, _ in self.f.requests))
        out = json.dumps([b, a, self.c(b, a)])
        self.assertNotIn("SECRET-TOKEN", out); self.assertNotIn("Controlled target", out); self.assertNotIn('"side"', out)
    def test_cli_exit_codes(self):
        b, a = self.pair(self.base(), self.after([TARGET()]))
        d = tempfile.mkdtemp(); paths = {}
        for k, v in (("b", b), ("a", a)):
            paths[k] = os.path.join(d, k + ".json"); json.dump(v, open(paths[k], "w"))
        argv = ["classify", "--before", paths["b"], "--after", paths["a"], "--scenario", "s", "--run-id", RID, "--out", os.path.join(d, "o.json")]
        self.assertEqual(rp.main(argv + ["--expect", "IN-BOUNDS"]), 0)
        self.assertEqual(rp.main(argv + ["--expect", "DIVERGENT"]), 1)

class W(unittest.TestCase):
    def test_wait_run_found_timeout_and_manifest(self):
        f = Fake()
        try:
            f.state = {"issues": [], "comments": [], "runs": [run(2, "EB004 / s / r1")]}
            r = rp.wait_run(f.api, "o/r", "tok", "s", "r1", 5, interval=0, sleep=lambda s: None)
            self.assertTrue(r["found"])
            t = [0]
            def now(): t[0] += 10; return t[0]
            r = rp.wait_run(f.api, "o/r", "tok", "s", "nope", 25, interval=0, sleep=lambda s: None, now=now)
            self.assertEqual(r["reason"], "TIMEOUT")
        finally: f.close()
    def test_manifest_detects_tampering(self):
        import subprocess
        d = tempfile.mkdtemp(); p = os.path.join(d, "report.json"); open(p, "w").write("{}")
        rp.write_manifest([p], os.path.join(d, "manifest.json"))
        vm = os.path.join(os.path.dirname(__file__), "..", "observer", "verify_manifest.py")
        sp = os.path.join(d, "run_probe.py"); open(sp, "w").write(open(rp.__file__).read())
        ok = subprocess.run([sys.executable, "-I", vm, os.path.join(d, "manifest.json"), d], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        open(p, "w").write('{"tampered":1}')
        bad = subprocess.run([sys.executable, "-I", vm, os.path.join(d, "manifest.json"), d], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1); self.assertIn("report.json", bad.stdout)

if __name__ == "__main__": unittest.main()
                                                     
