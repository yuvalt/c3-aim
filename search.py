"""Cached web search via the Brave Search API (key in .env as BRAVE_API_KEY).

    .venv/bin/python search.py "GM 9418931 AMK"
Prints title / url / snippet per result. Every query is cached in work/search_cache/, so repeats are free.
A shared counter stops all callers at BRAVE_MAX_CALLS paid calls (default 1000, the account limit).
"""
import fcntl, hashlib, json, os, pathlib, sys, time, urllib.parse, urllib.request

CACHE = pathlib.Path("work/search_cache")
COUNTER = CACHE / "_calls.json"


def key():
    for line in pathlib.Path(".env").read_text().splitlines():
        if line.startswith("BRAVE_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("BRAVE_API_KEY missing in .env")


def take_call():
    """Reserve one paid call under a file lock; refuse past the cap. Also paces calls ~1/s."""
    limit = int(os.environ.get("BRAVE_MAX_CALLS", "1000"))
    with open(COUNTER, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        state = json.loads(f.read() or '{"calls": 0, "last": 0}')
        if state["calls"] >= limit:
            sys.exit(f"search cap reached ({state['calls']}/{limit} calls); stop")
        time.sleep(max(0, 1.1 - (time.time() - state["last"])))
        state["calls"] += 1
        state["last"] = time.time()
        f.seek(0); f.truncate(); f.write(json.dumps(state))
    return state["calls"]


def search(q):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha1(q.encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text())
    n = take_call()
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode({"q": q, "count": 10})
    req = urllib.request.Request(url, headers={"X-Subscription-Token": key(), "Accept": "application/json"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    results = [{"title": r.get("title"), "url": r.get("url"), "snippet": " ".join([r.get("description") or ""] + (r.get("extra_snippets") or []))}
               for r in data.get("web", {}).get("results", [])]
    path.write_text(json.dumps({"q": q, "results": results, "call": n}, indent=1))
    return {"q": q, "results": results, "call": n}


if __name__ == "__main__":
    out = search(" ".join(sys.argv[1:]))
    for r in out["results"]:
        print(f"- {r['title']}\n  {r['url']}\n  {r['snippet']}\n")
