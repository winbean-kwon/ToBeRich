"""S-Q 검색(notes/funnel_protocol.md 1.2의 고정 조건). 원 결과와 학회 필터 결과를 이 폴더에 저장한다.

실행: python3 notes/lit/s_q/search.py  (저장소 루트에서)
"""
import csv, datetime, json, re, time, urllib.error, urllib.parse, urllib.request

UA = {"User-Agent": "academic-literature-check"}
HERE = "notes/lit/s_q/"
TODAY = str(datetime.date.today())
FILTER = 'title.search:portfolio,title.search:"reinforcement learning",from_publication_date:2017-01-01,to_publication_date:2026-10-31'
VENUES = [
    ("AAAI", r"\baaai\b|association for the advancement of artificial"),
    ("IJCAI", r"\bijcai\b|international joint conference on artificial"),
    ("KDD", r"\bkdd\b|knowledge discovery (and|&) data mining"),
    ("WWW", r"\bwww\b|the web conference|world wide web conference"),
    ("CIKM", r"\bcikm\b|conference on information and knowledge management"),
    ("NeurIPS", r"neurips|neural information processing systems"),
    ("ICML", r"\bicml\b|international conference on machine learning"),
    ("ICLR", r"\biclr\b|international conference on learning representations"),
    ("AAMAS", r"\baamas\b|autonomous agents and multi"),
    ("ICAIF", r"\bicaif\b|ai in finance"),
    ("TMLR", r"\btmlr\b|transactions on machine learning research"),
]


def venue(s):
    s = (s or "").lower()
    for k, p in VENUES:
        if re.search(p, s):
            return k


def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def get(u, tries=30, wait=60):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                b = r.read()
                if r.status == 200:
                    return json.loads(b)
                print("status", r.status, flush=True)
        except urllib.error.HTTPError as e:
            print("http", e.code, flush=True)
            if e.code != 429:
                raise
        time.sleep(wait)
    raise RuntimeError("재시도 초과: " + u[:80])


def main():
    rows, cur, n = [], "*", None
    while cur:
        d = get("https://api.openalex.org/works?per-page=200&filter=" + urllib.parse.quote(FILTER, safe=":,") + "&cursor=" + cur +
                "&select=id,doi,title,publication_year,type,primary_location,locations")
        n, cur = d["meta"]["count"], d["meta"].get("next_cursor")
        rows += d["results"]
        print("openalex", n, len(rows), flush=True)
        if not d["results"]:
            break
        time.sleep(3)
    json.dump({"query": FILTER, "date": TODAY, "count": n, "results": rows}, open(HERE + "openalex_raw.json", "w"))

    hits, dblp_note = [], None
    try:
        d = get("https://dblp.org/search/publ/api?format=json&h=1000&q=" + urllib.parse.quote("portfolio reinforcement learning"), tries=3, wait=30)
        hits = [h["info"] for h in d["result"]["hits"].get("hit", [])]
        json.dump({"query": "portfolio reinforcement learning", "date": TODAY, "results": hits}, open(HERE + "dblp_raw.json", "w"))
    except Exception as e:
        dblp_note = f"{type(e).__name__}: {e}"
    print("dblp", len(hits), dblp_note, flush=True)

    found = {}
    for w in rows:
        names = [(l.get("source") or {}).get("display_name") for l in (w.get("locations") or [])]
        v = next((venue(x) for x in names if venue(x)), None)
        if v and w.get("title"):
            found.setdefault(norm(w["title"]), dict(title=w["title"], year=w["publication_year"], venue=v, doi=w.get("doi"), src="openalex"))
    for h in hits:
        y, tt, vv = int(h.get("year", 0)), h["title"].lower(), h.get("venue")
        v = venue(vv if isinstance(vv, str) else " ".join(vv or []))
        if 2017 <= y <= 2026 and v and "portfolio" in tt and "reinforcement learning" in tt:
            found.setdefault(norm(h["title"]), dict(title=h["title"], year=y, venue=v, doi=h.get("doi"), src="dblp"))
    s56 = [norm(x["title"]) for x in csv.DictReader(open("notes/lit/lit_survey_merged.csv", encoding="utf-8-sig"))]
    out = sorted(found.values(), key=lambda x: (x["venue"], x["year"]))
    for x in out:
        x["in_S56"] = any(norm(x["title"])[:40] == s[:40] for s in s56)
    with open(HERE + "s_q_venue_filtered.csv", "w", newline="", encoding="utf-8") as f:
        c = csv.DictWriter(f, fieldnames=["venue", "year", "title", "doi", "src", "in_S56"])
        c.writeheader()
        c.writerows(out)
    json.dump({"date": TODAY, "openalex_count": n, "openalex_rows": len(rows), "dblp_rows": len(hits), "dblp_note": dblp_note,
               "venue_filtered": len(out), "in_S56": sum(x["in_S56"] for x in out)}, open(HERE + "meta.json", "w"), indent=1)
    print("venue filtered", len(out), "in S56", sum(x["in_S56"] for x in out), flush=True)


if __name__ == "__main__":
    main()
