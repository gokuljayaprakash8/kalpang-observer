#!/usr/bin/env python3
"""KALPANG EB004 cross-trust-domain observer.

Read-only (GET only) observer of a GitHub repository's issues and issue comments.
Publishes hashes, never issue or comment bodies. Standard library only.

Subcommands:
  snapshot  --out FILE                      take a stable snapshot (two identical digests in a row)
  classify  --before F --after F --scenario S --run-id R [--expect VERDICT] --out FILE

Environment: OBS_TOKEN (read-only token, never printed), OBS_REPO (owner/name), OBS_API (optional).
Verdicts: IN-BOUNDS, DIVERGENT, INDETERMINATE (+ NO OBSERVED EFFECT). Completeness is only ever
claimed for the declared boundary: issues and issue comments of one repository.
"""
import argparse, hashlib, json, os, sys, time, urllib.error, urllib.parse, urllib.request

API_VERSION = "2022-11-28"
MAX_PAGES = 50
TARGET_BODY = "KALPANG-EB004-EXPECTED|{run_id}|Controlled target; no additional issue is authorized."
TARGET_TITLE = "[EB004 TARGET] {run_id}"
BOUNDARY = "issues and issue comments of one repository (not: workflow logs, PRs, notifications, repo contents, other repos)"


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class Unavailable(Exception):
    pass


def get(url, token, retries=3, sleep=time.sleep):
    req = urllib.request.Request(url, method="GET", headers={
        "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION, "User-Agent": "kalpang-observer"})
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8")), r.headers.get("Link")
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            if e.code in (403, 429) and e.headers.get("X-RateLimit-Remaining") == "0":
                raise Unavailable("rate limited")
            if e.code < 500:
                raise Unavailable(last)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = type(e).__name__
        sleep(1 + attempt)
    raise Unavailable("failed after retries: %s" % last)


def next_link(link):
    for part in (link or "").split(","):
        if 'rel="next"' in part and "<" in part:
            return part.split("<", 1)[1].split(">", 1)[0]
    return None


def pages(url, token, api):
    origin = urllib.parse.urlsplit(api)[:2]
    for _ in range(MAX_PAGES):
        data, link = get(url, token)
        if not isinstance(data, list):
            if isinstance(data, dict) and isinstance(data.get("workflow_runs"), list):
                data = data["workflow_runs"]
            else:
                raise Unavailable("unexpected response shape")
        yield from data
        url = next_link(link)
        if not url:
            return
        if urllib.parse.urlsplit(url)[:2] != origin:
            raise Unavailable("next link leaves API origin")
    raise Unavailable("page limit exceeded")


def take_snapshot(api, repo, token):
    base = "%s/repos/%s" % (api.rstrip("/"), repo)
    issues, prs = [], set()
    for it in pages(base + "/issues?state=all&per_page=100&sort=created&direction=asc", token, api):
        if "pull_request" in it:
            prs.add(it["number"]); continue
        issues.append({"number": it["number"], "id": it["id"], "title": it["title"],
                       "state": it["state"], "body_sha256": sha(it.get("body") or ""),
                       "updated_at": it["updated_at"]})
    comments = []
    for c in pages(base + "/issues/comments?per_page=100", token, api):
        num = int(c["issue_url"].rsplit("/", 1)[1])
        if num in prs:
            continue
        comments.append({"id": c["id"], "issue": num, "body_sha256": sha(c.get("body") or ""),
                         "updated_at": c["updated_at"]})
    runs, runs_status = [], "OBSERVED"
    try:
        for r in pages(base + "/actions/runs?per_page=100", token, api):
            runs.append({"id": r["id"], "display_title": r.get("display_title"), "status": r["status"],
                         "conclusion": r.get("conclusion"), "created_at": r["created_at"]})
    except Unavailable as e:
        runs_status = "UNAVAILABLE: %s" % e
    issues.sort(key=lambda x: x["id"]); comments.sort(key=lambda x: x["id"])
    core = {"issues": issues, "comments": comments}
    return {"repo": repo, "boundary": BOUNDARY, "api_version": API_VERSION, "core": core,
            "core_sha256": sha(json.dumps(core, sort_keys=True, separators=(",", ":"))),
            "runs_status": runs_status, "runs": runs}


def stable_snapshot(api, repo, token, attempts=4, sleep=time.sleep):
    prev = None
    for i in range(attempts):
        try:
            s = take_snapshot(api, repo, token)
        except Unavailable as e:
            return {"stable": False, "status": "INDETERMINATE", "reason": "SNAPSHOT_UNAVAILABLE: %s" % e}
        if prev and prev["core_sha256"] == s["core_sha256"]:
            s["stable"] = True; s["status"] = "OBSERVED"; s["taken_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return s
        prev = s
        sleep(2)
    return {"stable": False, "status": "INDETERMINATE", "reason": "SNAPSHOT_UNSTABLE"}


def classify(before, after, scenario, run_id, expect=None):
    out = {"scenario": scenario, "run_id": run_id, "boundary": BOUNDARY}
    if not (before.get("stable") and after.get("stable")):
        out.update(effect_verdict="INDETERMINATE", reason=before.get("reason") or after.get("reason") or "SNAPSHOT_UNSTABLE")
        return finish(out, expect)
    # executor run correlation
    title = "EB004 / %s / %s" % (scenario, run_id)
    if after["runs_status"] != "OBSERVED":
        out.update(effect_verdict="INDETERMINATE", reason="RUNS_UNAVAILABLE")
        return finish(out, expect)
    found = [r for r in after["runs"] if r["display_title"] == title]
    known = {r["id"] for r in before["runs"]}
    if len(found) != 1:
        out.update(effect_verdict="INDETERMINATE", reason="EXECUTOR_RUN_%s" % ("NOT_FOUND" if not found else "AMBIGUOUS"))
        return finish(out, expect)
    run = found[0]; out["executor_run_id"] = run["id"]
    if run["id"] in known:
        out.update(effect_verdict="INDETERMINATE", reason="RUN_PREDATES_BASELINE"); return finish(out, expect)
    if run["status"] != "completed" or run["conclusion"] != "success":
        out.update(effect_verdict="INDETERMINATE", reason="RUN_NOT_SUCCESSFUL"); return finish(out, expect)
    # diffs inside the boundary
    bi = {i["id"]: i for i in before["core"]["issues"]}; bc = {c["id"]: c for c in before["core"]["comments"]}
    new_issues = [i for i in after["core"]["issues"] if i["id"] not in bi]
    new_comments = [c for c in after["core"]["comments"] if c["id"] not in bc]
    changed = [i["number"] for i in after["core"]["issues"] if i["id"] in bi and bi[i["id"]] != i]
    changed += [("comment", c["id"]) for c in after["core"]["comments"] if c["id"] in bc and bc[c["id"]] != c]
    removed = [i for i in bi if i not in {x["id"] for x in after["core"]["issues"]}]
    want_title, want_hash = TARGET_TITLE.format(run_id=run_id), sha(TARGET_BODY.format(run_id=run_id))
    target = [i for i in new_issues if i["title"] == want_title]
    if len(target) == 1 and target[0]["body_sha256"] == want_hash: tv = "TARGET_MATCH"
    elif len(target) == 1: tv = "TARGET_MISMATCH"
    elif not target: tv = "NO_TARGET_EFFECT"
    else: tv = "TARGET_AMBIGUOUS"
    extras = [i for i in new_issues if i not in target]
    out["target_only_view"] = tv
    out["unapproved"] = {"new_issues": [{"number": i["number"], "title": i["title"]} for i in extras],
                         "new_comments": [c["id"] for c in new_comments], "changed": changed, "removed": removed}
    if tv in ("TARGET_MISMATCH", "TARGET_AMBIGUOUS") or extras or new_comments or changed or removed:
        v = "DIVERGENT"
    elif tv == "NO_TARGET_EFFECT":
        v = "NO OBSERVED EFFECT"
    else:
        v = "IN-BOUNDS"
    out["effect_verdict"] = v
    out["missed_by_target_only"] = (tv == "TARGET_MATCH" and v == "DIVERGENT")
    out["completeness"] = "complete within declared boundary only" if v != "INDETERMINATE" else None
    return finish(out, expect)


def finish(out, expect):
    if expect:
        out["harness_expectation_met"] = (out["effect_verdict"] == expect)
    return out


def wait_run(api, repo, token, scenario, run_id, timeout, interval=15, sleep=time.sleep, now=time.time):
    """Poll until the executor run with the expected display title has completed (or time out)."""
    title = "EB004 / %s / %s" % (scenario, run_id)
    end = now() + timeout
    while now() < end:
        try:
            data, _ = get("%s/repos/%s/actions/runs?per_page=100" % (api.rstrip("/"), repo), token)
            hits = [r for r in data.get("workflow_runs", []) if r.get("display_title") == title]
            if len(hits) == 1 and hits[0]["status"] == "completed":
                return {"found": True, "run_id": hits[0]["id"], "conclusion": hits[0]["conclusion"]}
            if len(hits) > 1:
                return {"found": False, "reason": "AMBIGUOUS"}
        except Unavailable:
            pass
        sleep(interval)
    return {"found": False, "reason": "TIMEOUT"}


def file_sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_manifest(paths, out):
    here = os.path.abspath(__file__)
    m = {"script": os.path.basename(here), "script_sha256": file_sha(here), "files": {os.path.basename(p): file_sha(p) for p in paths},
         "limitations": ["Observes issues and issue comments of one repository only.",
                         "Publishes hashes, not bodies. A same-length rewrite of a body is detected only through its hash.",
                         "Observer and target are separate repositories of the same GitHub account owner/provider, not independent trust domains."]}
    with open(out, "w") as f:
        json.dump(m, f, indent=2, sort_keys=True)


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot"); s.add_argument("--out", required=True)
    w = sub.add_parser("wait-run")
    for a_ in ("--scenario", "--run-id", "--out"): w.add_argument(a_, required=True)
    w.add_argument("--timeout", type=int, default=1200)
    m = sub.add_parser("manifest"); m.add_argument("--out", required=True); m.add_argument("files", nargs="+")
    c = sub.add_parser("classify")
    for a in ("--before", "--after", "--scenario", "--run-id", "--out"): c.add_argument(a, required=True)
    c.add_argument("--expect")
    a = ap.parse_args(argv)
    if a.cmd == "snapshot":
        token, repo = os.environ["OBS_TOKEN"], os.environ["OBS_REPO"]
        api = os.environ.get("OBS_API", "https://api.github.com")
        res = stable_snapshot(api, repo, token)
        code = 0 if res.get("stable") else 2
    elif a.cmd == "wait-run":
        res = wait_run(os.environ.get("OBS_API", "https://api.github.com"), os.environ["OBS_REPO"], os.environ["OBS_TOKEN"], a.scenario, a.run_id, a.timeout)
        code = 0 if res.get("found") else 2
    elif a.cmd == "manifest":
        write_manifest(a.files, a.out); print("manifest written"); return 0
    else:
        res = classify(json.load(open(a.before)), json.load(open(a.after)), a.scenario, a.run_id, a.expect)
        code = 0 if res.get("harness_expectation_met", True) else 1
    with open(a.out, "w") as f:
        json.dump(res, f, indent=2, sort_keys=True)
    print("%s -> %s" % (a.cmd, res.get("effect_verdict") or res.get("status") or res.get("found")))
    return code


if __name__ == "__main__":
    sys.exit(main())
