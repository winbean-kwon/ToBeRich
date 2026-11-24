"""F1 층 1 저자 계정 점검(절차: notes/f1_author_account_sweep_prereg.md). 후보만 낸다. 판정은 사람이 아닌 Claude 판독 → 사람 확인.

python3 replication/f1_author_sweep.py → notes/lit/f1/f1_author_sweep.json
GitHub 토큰 없이 돈다(core 60/시간). 한도가 바닥나면 초기화 시각까지 기다린다.
"""
import csv
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import f1_recheck as F  # noqa: E402

ROOT = F.ROOT
OUT = ROOT / "notes/lit/f1/f1_author_sweep.json"
CAND = ROOT / "notes/lit/f1/f1_candidates.csv"
UA = {"User-Agent": "f1-author-sweep (academic reproducibility study)"}
STOP = set("""a an the of for and with in on to via using based from by under into toward towards its their
deep reinforcement learning portfolio management financial finance optimization optimisation trading stock stocks
framework approach model models network networks agent agents strategy strategies market markets asset assets
allocation policy multi dynamic investment selection method novel study comparative""".split())


def get(url, accept="application/vnd.github+json", tries=4):
    for k in range(tries):
        req = urllib.request.Request(url, headers={**UA, "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
        except urllib.error.HTTPError as e:
            h = dict(e.headers)
            if e.code in (403, 429) and "api.github.com" in url:
                reset = int(h.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(5, reset - time.time() + 5) if h.get("X-RateLimit-Remaining") == "0" else 65
                print(f"  rate limit, {int(wait)}s 대기", flush=True)
                time.sleep(wait)
                continue
            return e.code, "", h
        except Exception:
            time.sleep(5 * (k + 1))
    return 0, "", {}


def gh(path):
    st, body, _ = get("https://api.github.com" + path)
    return json.loads(body) if st == 200 and body else None


def arxiv_id(s):
    m = re.search(r"(\d{4}\.\d{4,5})", s or "")
    return m.group(1) if m else None


def authors_arxiv(ax):
    st, body, _ = get(f"http://export.arxiv.org/api/query?id_list={ax}", accept="application/atom+xml")
    if st != 200:
        return None, None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = ET.fromstring(body).find("a:entry", ns)
    if e is None:
        return None, None
    names = [a.find("a:name", ns).text.strip() for a in e.findall("a:author", ns)]
    return names, " ".join(e.find("a:title", ns).text.split())


def authors_s2(doi=None, title=None):
    base = "https://api.semanticscholar.org/graph/v1/paper/"
    if doi:
        st, body, _ = get(base + "DOI:" + urllib.parse.quote(doi) + "?fields=title,authors", accept="application/json")
        if st == 200:
            d = json.loads(body)
            return [a["name"] for a in d.get("authors", [])], d.get("title")
    if title:
        st, body, _ = get(base + "search?limit=1&fields=title,authors&query=" + urllib.parse.quote(title), accept="application/json")
        if st == 200 and json.loads(body).get("data"):
            d = json.loads(body)["data"][0]
            kw = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]+", title) if w.lower() not in STOP]
            if kw and all(w.lower() in d["title"].lower() for w in kw[:2]):
                return [a["name"] for a in d.get("authors", [])], d["title"]
    time.sleep(3)
    return None, None


def keywords(title):
    acr = [w for w in re.findall(r"\b[A-Z][A-Za-z0-9\-]*[A-Z][A-Za-z0-9\-]*\b", title) if len(w) >= 3]
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z\-]{5,}", title) if w.lower() not in STOP]
    return sorted(set(a.lower() for a in acr)), words[:4]


def phrase_hit(readme, title):
    t = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", title)]
    r = " ".join(re.findall(r"[a-z0-9]+", readme.lower()))
    return any(" ".join(t[i:i + 4]) in r for i in range(max(0, len(t) - 3)))


def readme(full):
    for br in ("HEAD",):
        for fn in ("README.md", "readme.md", "Readme.md", "README.rst", "README"):
            st, body, _ = get(f"https://raw.githubusercontent.com/{full}/{br}/{fn}", accept="text/plain")
            if st == 200:
                return body
    return ""


def main():
    s1, _ = F.strata()
    ids1 = {r["id"] for r in s1}
    sheet = {r["id"]: r for r in csv.DictReader(open(F.SHEET, encoding="utf-8"))}
    cand_title = {r.get("id"): r for r in csv.DictReader(open(CAND, encoding="utf-8"))} if CAND.exists() else {}
    targets = [i for i in sheet if i in ids1 and sheet[i]["판정"] != "찾음"]
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for pid in targets:
        if pid in out and out[pid].get("done"):
            continue
        r = sheet[pid]
        ax = arxiv_id(r["식별자"])
        doi = None
        m = re.search(r"(10\.\d{4,}/[^\s;]+)", r["식별자"] or "")
        if m:
            doi = m.group(1).rstrip(")")
        title = r["제목"]
        ct = cand_title.get(pid, {})
        for k in ("title", "제목"):
            if ct.get(k) and len(ct[k]) > len(title):
                title = ct[k]
        names, t2 = authors_arxiv(ax) if ax else (None, None)
        if not names:
            names, t2 = authors_s2(doi=doi, title=None if doi else re.sub(r"\(.*?\)", "", title).strip())
        rec = {"id": pid, "arxiv": ax, "doi": doi, "title": t2 or title, "authors": names, "checked": []}
        if not names:
            rec.update(status="저자 확인 불가", done=True)
            out[pid] = rec
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
            print(pid, "저자 확인 불가", flush=True)
            continue
        acr, words = keywords(rec["title"])
        who = [names[0]] + ([names[-1]] if len(names) > 1 else [])
        hits = []
        for name in who:
            q = urllib.parse.quote(f'fullname:"{name}" type:user')
            res = gh(f"/search/users?per_page=3&q={q}") or {}
            time.sleep(7)
            for u in res.get("items", [])[:3]:
                repos = gh(f"/users/{u['login']}/repos?per_page=100&type=owner") or []
                rec["checked"].append({"author": name, "login": u["login"], "repos": len(repos)})
                for rp in repos:
                    if rp.get("fork"):
                        continue
                    text = (rp["name"] + " " + (rp.get("description") or "")).lower()
                    why = [a for a in acr if a in text] + ([" ".join(words[:2])] if len(words) >= 2 and all(w in text for w in words[:2]) else [])
                    rd = readme(rp["full_name"])
                    if ax and ax in rd:
                        why.append("readme:arxiv")
                    if rd and phrase_hit(rd, rec["title"]):
                        why.append("readme:title4")
                    if why:
                        hits.append({"repo": rp["full_name"], "author": name, "why": why, "created": rp["created_at"][:10]})
        if ax:
            res = gh("/search/repositories?per_page=10&q=" + urllib.parse.quote(f'"{ax}" in:readme')) or {}
            time.sleep(7)
            for it in res.get("items", []):
                own = it["owner"]["login"]
                u = gh(f"/users/{own}") or {}
                nm = (u.get("name") or "").lower()
                if any(p.lower() in nm or nm and nm in p.lower() for p in names):
                    hits.append({"repo": it["full_name"], "author": u.get("name"), "why": ["arxiv-readme-search"], "created": it["created_at"][:10]})
        rec.update(status="후보 있음" if hits else "후보 없음", hits=hits, done=True)
        out[pid] = rec
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
        print(pid, rec["status"], len(hits), flush=True)
    print("끝", len(out))


if __name__ == "__main__":
    main()
