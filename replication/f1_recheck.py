"""F1 재확인(사전 등록 notes/f1_recheck_prereg.md).

python3 replication/f1_recheck.py sheet   → notes/lit/f1/f1_recheck_sheet.csv (Claude 판정 없음, 순서 섞음)
python3 replication/f1_recheck.py score   → 사람이 채운 시트를 Claude 판정과 비교해 지표 출력·notes/lit/f1/f1_recheck_score.json
"""
import csv
import json
import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FT = ROOT / "notes/lit/f1/funnel_table.csv"
LIT = ROOT / "notes/lit/lit_survey_merged.csv"
SHEET = ROOT / "notes/lit/f1/f1_recheck_sheet.csv"
SEED = 20261113
EXCLUDE = {"original_missing"}
PASS = {"pass", "pass_tutorial"}
LABELS = {"찾음", "제3자만", "링크 사망", "요청 시 제공", "없음", "원문 미확보"}
# lit_survey에 식별자가 없는 S-Q·보충 논문(manual_check_list·static_layer 기록)
EXTRA_ID = {"SQ-APTS": "arXiv 2110.05299", "SQ-Regret": "arXiv 2502.02619", "SQ-MAPS": "arXiv 2007.05402"}


def strata():
    rows = list(csv.DictReader(open(FT, encoding="utf-8")))
    s1 = [r for r in rows if r["F1"] not in PASS and r["F1"] not in EXCLUDE]
    passed = sorted((r for r in rows if r["F1"] in PASS), key=lambda r: r["id"])
    s2 = random.Random(SEED).sample(passed, 10)
    return s1, s2


def sheet():
    if SHEET.exists():
        sys.exit(f"{SHEET} 이미 있음(사용자 기입 보호) — 지우지 않는다")
    lit = {r["id"]: r for r in csv.DictReader(open(LIT, encoding="utf-8-sig"))}
    s1, s2 = strata()
    items = s1 + s2
    random.Random(SEED + 1).shuffle(items)
    with open(SHEET, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["순번", "id", "제목", "1저자", "연도", "학회", "식별자", "판정", "URL", "근거 위치", "소요(분)", "확인일", "메모"])
        for n, r in enumerate(items, 1):
            l = lit.get(r["id"], {})
            w.writerow([n, r["id"], l.get("title") or r["paper"], l.get("first_author", ""), l.get("year", ""),
                        l.get("venue", ""), l.get("doi_or_arxiv") or EXTRA_ID.get(r["id"], ""), "", "", "", "", "", ""])
    print(f"층 1 {len(s1)}편, 층 2 {len(s2)}편 → {SHEET}")


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


def agreement(pairs):
    n = len(pairs)
    a = sum(x == y for x, y in pairs) / n
    p1, p2 = sum(x for x, _ in pairs) / n, sum(y for _, y in pairs) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    kappa = None if pe == 1 else (a - pe) / (1 - pe)
    pi = (p1 + p2) / 2
    pe_ac1 = 2 * pi * (1 - pi)
    ac1 = None if pe_ac1 == 1 else (a - pe_ac1) / (1 - pe_ac1)
    r = lambda v: None if v is None else round(v, 3)
    return {"n": n, "원일치율": r(a), "kappa": r(kappa), "PABAK": r(2 * a - 1), "AC1": r(ac1)}


def score():
    claude = {r["id"]: r["F1"] for r in csv.DictReader(open(FT, encoding="utf-8"))}
    s1, s2 = strata()
    ids1, ids2 = {r["id"] for r in s1}, {r["id"] for r in s2}
    rows = list(csv.DictReader(open(SHEET, encoding="utf-8")))
    bad = [r["id"] for r in rows if r["판정"] not in LABELS]
    if bad:
        sys.exit(f"판정 칸이 비었거나 허용값이 아님: {bad}")
    claude_read = {r["id"] for r in rows if "Claude 판독" in r["메모"]}  # 주 지표에서 뺀다
    used = [r for r in rows if r["id"] not in claude_read]
    fn = [r["id"] for r in used if r["id"] in ids1 and r["판정"] == "찾음"]
    fp = [r["id"] for r in used if r["id"] in ids2 and r["판정"] != "찾음"]
    n1 = sum(r["id"] in ids1 for r in used)
    n2 = sum(r["id"] in ids2 for r in used)
    cross = {}
    for r in used:
        k = f"{claude[r['id']]} → {r['판정']}"
        cross[k] = cross.get(k, 0) + 1
    out = {
        "주: 층1 미통과→찾음": {"k": len(fn), "n": n1, "ids": fn, "Wilson95": wilson(len(fn), n1)},
        "주: 층2 통과→미통과": {"k": len(fp), "n": n2, "ids": fp, "Wilson95": wilson(len(fp), n2)},
        "보조: 54편 이진 일치(층별 표집이라 모집단 일치도 아님)": agreement(
            [(claude[r["id"]] in PASS, r["판정"] == "찾음") for r in used]),
        "교차표(Claude → 사람)": dict(sorted(cross.items())),
        "Claude 판독이라 제외": sorted(claude_read),
    }
    (ROOT / "notes/lit/f1/f1_recheck_score.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"sheet": sheet, "score": score}[sys.argv[1]]()
