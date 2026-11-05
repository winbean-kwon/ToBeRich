"""F1 자동 검색(notes/funnel_protocol.md 3.1). 표본 전 논문에 대해 공개 코드 후보 링크를 모은다. 판정은 사람이 한다.

경로: (1) Semantic Scholar 제목 매칭 → arXiv ID (2) arXiv abs 페이지·HTML 본문의 github 링크 (3) GitHub 저장소 검색(제목 핵심어).
출력: notes/lit/f1/f1_candidates.csv
"""
import csv, json, re, time, urllib.error, urllib.parse, urllib.request

UA = {"User-Agent": "academic-literature-check"}
OUT = "notes/lit/f1/f1_candidates.csv"
STOP = set("a an the for of with and in on via using to by from based deep reinforcement learning portfolio management optimization framework approach".split())


def fetch(u, js=True, tries=4, wait=20):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as r:
                b = r.read()
                return json.loads(b) if js else b.decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (403, 429):
                time.sleep(wait * (i + 1))
                continue
            return None
        except Exception:
            time.sleep(5)
    return None


def papers():
    P = []
    for x in csv.DictReader(open("notes/lit/lit_survey_merged.csv", encoding="utf-8-sig")):
        P.append(dict(sample="S56", id=x["id"], title=x["title"], year=x["year"], author=x["first_author"], hint=x["doi_or_arxiv"], recorded=x["code_url"]))
    ab = {a["title"]: a for a in json.load(open("notes/lit/s_q/s_q_abstracts.json")) if a}
    for x in csv.DictReader(open("notes/lit/s_q/s_q_f0.csv")):
        if x["F0"] in ("pass", "pending"):
            a = next((v for k, v in ab.items() if k.lower().startswith(x["title_short"].split(" (")[0].lower()[:18]) or x["title_short"].split(" (")[0].lower()[:18] in k.lower()), None)
            P.append(dict(sample="S-Q", id="SQ-" + x["title_short"][:20], title=a["title"] if a else x["title_short"], year=x["year"],
                          author="", hint=(a or {}).get("externalIds", {}).get("ArXiv") or "", recorded=""))
    for t, y in [("Contrastive Learning and Reward Smoothing for Deep Portfolio Management", 2023),
                 ("Regime-Adaptive Continual Learning for Portfolio Management", 2026),
                 ("Online portfolio management via deep reinforcement learning with high-frequency data", 2023),
                 ("Autoregressive DRL with Learned Intrinsic Rewards for Portfolio Optimisation", 2024),
                 ("Bayesian Robust Financial Trading with Adversarial Synthetic Market Data", 2026)]:
        P.append(dict(sample="보충", id="SUP-" + t[:20], title=t, year=y, author="", hint="", recorded=""))
    return P


def arxiv_id(p):
    m = re.search(r"(\d{4}\.\d{4,5})", p["hint"] or "")
    if m:
        return m.group(1)
    d = fetch("https://api.semanticscholar.org/graph/v1/paper/search/match?query=" + urllib.parse.quote(p["title"][:250]) + "&fields=externalIds,title")
    time.sleep(1.2)
    if d and d.get("data"):
        return (d["data"][0].get("externalIds") or {}).get("ArXiv")


GH = re.compile(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")


def arxiv_links(aid):
    links = set()
    for u in (f"https://arxiv.org/abs/{aid}", f"https://arxiv.org/html/{aid}"):
        t = fetch(u, js=False)
        time.sleep(1)
        if t:
            links |= {m.rstrip(".").removesuffix(".git") for m in GH.findall(t)}
    return sorted(l for l in links if not l.lower().startswith(("arxiv/", "openreview/", "ar5iv")))


def gh_search(title):
    words = [w for w in re.findall(r"[A-Za-z0-9+-]+", title) if w.lower() not in STOP]
    q = " ".join(words[:5])
    d = fetch("https://api.github.com/search/repositories?per_page=5&q=" + urllib.parse.quote(q), wait=30)
    time.sleep(7)  # 비인증 검색 10회/분
    return [f"{r['full_name']}(*{r['stargazers_count']})" for r in (d or {}).get("items", [])], q


def main():
    rows = []
    for i, p in enumerate(papers()):
        aid = arxiv_id(p)
        al = arxiv_links(aid) if aid else []
        gs, q = gh_search(p["title"])
        rows.append(dict(sample=p["sample"], id=p["id"], year=p["year"], title=p["title"][:120], recorded=p["recorded"][:120], arxiv=aid or "",
                         arxiv_github=" ".join(al), gh_query=q, gh_top5=" ".join(gs)))
        print(i, p["sample"], p["id"], aid, len(al), len(gs), flush=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("done", len(rows))


if __name__ == "__main__":
    main()
