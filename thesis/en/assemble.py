"""Assemble the English thesis draft from the chapter files.

Chapter files in thesis/en/ stay the editable sources; this script renumbers the
working section labels (X.n, Y.n, Z.n), inserts Tables 1-3 from
notes/paper_tables_draft.md, and writes thesis/en/THESIS_EN_DRAFT.md.

    python3 thesis/en/assemble.py
"""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE / "THESIS_EN_DRAFT.md"


def read(name):
    return (HERE / name).read_text(encoding="utf-8")


def sections(text, level):
    """Split text into {heading: body} for headings of the given level ('#', '##')."""
    out, cur, buf = {}, None, []
    pat = re.compile(r"^" + re.escape(level) + r" (.+)$")
    for line in text.splitlines():
        m = pat.match(line)
        if m and not line.startswith(level + "#"):
            if cur is not None:
                out[cur] = "\n".join(buf).strip("\n")
            cur, buf = m.group(1).strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf).strip("\n")
    return out


def sec(text, prefix, level="##"):
    """Body of the unique heading starting with prefix; stops at the next heading of the same or higher level."""
    body, found = [], False
    for line in text.splitlines():
        if line.startswith("#"):
            hashes = len(line) - len(line.lstrip("#"))
            title = line[hashes:].strip()
            if found and hashes <= len(level):
                break
            if hashes == len(level) and title.startswith(prefix):
                found = True
                continue
        if found:
            body.append(line)
    assert found, prefix
    return "\n".join(body).strip("\n").rstrip("-").strip("\n")


def table(n):
    t = (ROOT / "notes" / "paper_tables_draft.md").read_text(encoding="utf-8")
    body = sec(t, f"Table {n}.")
    body = body.split("Notes for the text")[0].rstrip()
    title = [l for l in t.splitlines() if l.startswith(f"## Table {n}.")][0][3:]
    return f"**{title}**\n\n{body}"


def renumber(s):
    s = s.replace("Table Z0", "Table 4").replace("Table Z1", "Table 5").replace("Table Z2", "Table 6").replace("Table Z3", "Table 7")
    s = s.replace("Sections Z.3, Z.5 and Z.6", "Sections 5.3, 5.5 and 5.6")
    s = re.sub(r"\bZ\.(\d)", r"5.\1", s)
    for a, b in {"Y.1": "3.4", "Y.2": "4.3", "Y.3": "4.4", "Y.4": "4.5",
                 "X.1": "3.2.1", "X.2": "3.2.2", "X.3": "3.2.3", "X.4": "4.1", "X.5": "6.6"}.items():
        s = s.replace(a, b)
    s = s.replace("(the reproduction funnel, Section X)", "(the reproduction funnel, Section 3.2)")
    return s


intro, rw, meth = read("introduction.md"), read("related_work.md"), read("methods_limitations.md")
fun, ver, ree, dc, ab = (read(f) for f in ("funnel_methods_results.md", "reproduction_verdicts.md",
                                          "reevaluation_results.md", "discussion_conclusion.md", "abstract.md"))

# methods-file internal references shift by one (3.2 -> 3.3, ...) because the funnel becomes 3.2
meth = meth.replace("(Section 3.4)", "(Section @3.5@)").replace("(Section 3.5)", "(Section @3.6@)").replace("@", "")
meth = meth.replace(" The verdict criteria R1 (value within a tolerance band) and R2 (the paper's comparative claim holds in a pre-specified number of runs) are defined in Section Y.1.", "")

fun = fun.replace("criteria (Section X.4)", "criteria (Section @3.4@)").replace("@", "")
intro = intro.replace("Section 3.2 and Section Y.1", "Section 3.3 and Section 3.4")
ver = ver.replace("(Section 3.2 of the methods)", "(Section 3.3)")
x3 = sec(fun, "X.3")
x3_design, x3_rest = x3.split("**Results.**", 1)
x3_rest = "**Results.**" + x3_rest

limitations_contact = (
    "We contacted the authors of DeepAries and PRUDEX-Compass (AlphaMix+), and of one further paper, by e-mail "
    "with questions about settings not stated in the papers [check: dates sent]. No reply had been received by "
    "[check: date]. The verdicts therefore do not incorporate author input.")

own3, own4, own5, app = (read(f) for f in ("own_equity_forecasting.md", "own_hrl_crypto.md",
                                            "own_result_checks.md", "appendix_gaps.md"))

# Reproduction-study chapters: built in the earlier numbering (3 methods, 4 funnel/verdicts, 5 re-evaluation,
# 6 limitations), converted by renumber() from the working labels X/Y/Z, then mapped once to the chronological
# numbering by to_new(). Chapters written for the chronological outline are inserted unchanged.
repro = [
    "## 3.1 Design and pre-registration", sec(meth, "3.1"),
    "## 3.2 The reproduction funnel",
    "### 3.2.1 Sample", sec(fun, "X.1"),
    "### 3.2.2 Stages", sec(fun, "X.2"),
    "### 3.2.3 Checking the code-availability judgments", x3_design.strip(),
    "## 3.3 Targets for in-depth reproduction", sec(meth, "3.2"),
    "## 3.4 Reproduction runs and verdicts (O1)", sec(ver, "Y.1") + "\n\n" + sec(meth, "3.3"),
    "## 3.5 Unified evaluation protocol (O2)", sec(meth, "3.4"),
    "## 3.6 Checking the implemented transaction cost", sec(meth, "3.5"),
    "## 3.7 Statistical analysis", sec(meth, "3.6"),
    "## 3.8 Exploratory analyses", sec(meth, "3.7"),
    "## 3.9 Computing environment", sec(meth, "3.8"),
    "## 4.1 Results of the funnel", sec(fun, "X.4").replace("[Insert Table 1 from `notes/paper_tables_draft.md`.]", table(1)),
    "## 4.2 Check of the code-availability judgments", x3_rest,
    "## 4.3 Reproduction verdicts", sec(ver, "Y.2").replace("[Insert Table 2 from `notes/paper_tables_draft.md`.]", table(2)),
    "## 4.4 Exploratory verdicts outside the fixed order", sec(ver, "Y.3") + "\n\n" + table(3),
    "## 4.5 What the verdicts do and do not show", sec(ver, "Y.4"),
    "@@CH7@@",
]
for i, t in enumerate(["Do the implementations charge the configured transaction cost?",
                       "FinRL under the unified protocol",
                       "Why the outcomes look as they do (exploratory)",
                       "Effect sizes and detectable differences",
                       "A policy that holds what it buys on the first day (exploratory)",
                       "Sensitivity of the ensemble strategy to its turbulence threshold (exploratory)",
                       "Summary of the re-evaluation"], 1):
    repro += [f"## 5.{i} {t}", sec(ree, f"Z.{i}")]
repro += [
    "@@CH8@@",
    "## 6.4 What the verdicts can and cannot support", sec(meth, "6.1 What"),
    "## 6.5 Sample and selection", sec(meth, "6.2"),
    "## 6.6 Limitations specific to the funnel", sec(fun, "X.5"),
    "## 6.7 Data and universes", sec(meth, "6.3"),
    "## 6.8 Runs, seeds and power", sec(meth, "6.4"),
    "## 6.9 Protocol choices", sec(meth, "6.5"),
    "## 6.10 Exploratory findings", sec(meth, "6.6"),
    "## 6.11 Contact with authors", sec(meth, "6.7"),
]

SEC_MAP = {**{f"3.{i}": f"6.{i}" for i in range(1, 10)},
           **{f"4.{i}": f"6.{i + 9}" for i in range(1, 6)},
           **{f"5.{i}": f"7.{i}" for i in range(1, 8)},
           "6.1": "8.2", "6.2": "8.3", "6.3": "8.4",
           **{f"6.{i}": f"8.{i + 2}" for i in range(4, 12)}}
CH_MAP = {"3": "6", "4": "6", "5": "7", "6": "8", "7": "9"}
TAB_MAP = {"1": "6.1", "2": "6.2", "3": "6.3", "4": "7.1", "5": "7.2", "6": "7.3", "7": "7.4"}
FIG_MAP = {"1": "6.1", "2": "7.1"}


def to_new(s):
    """Map the earlier chapter/section/table/figure numbers to the chronological outline, in one pass."""
    def secnum(m):
        n = m.group(0)
        head = ".".join(n.split(".")[:2])
        return SEC_MAP.get(head, head) + n[len(head):]
    s = re.sub(r"^(#{2,3}) (\d\.\d+(?:\.\d)?)", lambda m: m.group(1) + " " + re.sub(r"\d\.\d+(?:\.\d)?", secnum, m.group(2)), s, flags=re.M)
    s = re.sub(r"(Sections? )(\d\.\d+(?:\.\d)?(?:(?:,| and|,? or| to|–)\s?\d\.\d+(?:\.\d)?)*)",
               lambda m: m.group(1) + re.sub(r"\d\.\d+(?:\.\d)?", secnum, m.group(2)), s)
    s = re.sub(r"\b(Chapters? )(\d)(?!\.?\d)", lambda m: m.group(1) + CH_MAP.get(m.group(2), m.group(2)), s)
    s = re.sub(r"\bTable (\d)(?!\.?\d)", lambda m: "Table " + TAB_MAP.get(m.group(1), m.group(1)), s)
    s = re.sub(r"\bFigure (\d)(?!\.?\d)", lambda m: "Figure " + FIG_MAP.get(m.group(1), m.group(1)), s)
    return s


repro_text = to_new(renumber("\n\n".join(p.strip() for p in repro)))
ch6, rest = repro_text.split("@@CH7@@")
ch7, lim = rest.split("@@CH8@@")

parts = [
    "# [check: title]",
    "## Abstract", sec(ab, "Abstract"),
    "# Chapter 1. Introduction", sections(intro, "#")["Chapter 1. Introduction"],
    "# Chapter 2. Related work", sections(rw, "#")["Chapter 2. Related work"],
    "# Chapter 3. Forecasting and RL allocation on equities", sections(own3, "#")["Chapter 3. Forecasting and RL allocation on equities"],
    "# Chapter 4. A hierarchical RL allocation system for cryptocurrency", sections(own4, "#")["Chapter 4. A hierarchical RL allocation system for cryptocurrency"],
    "# Chapter 5. Checking the result of the author's own system", sections(own5, "#")["Chapter 5. Checking the result of the author's own system"],
    "# Chapter 6. The reproduction study: design, funnel and verdicts", ch6,
    "# Chapter 7. Re-evaluation of official code", ch7,
    "# Chapter 8. Discussion and limitations", sections(dc, "#")["Chapter 8. Discussion and limitations"], lim,
    "# Chapter 9. Conclusion", sections(dc, "#")["Chapter 9. Conclusion"],
    "# Appendix A. A team entry to an ETF investment competition", sections(app, "#")["Appendix A. A team entry to an ETF investment competition"],
]


RENAME = {"Xiong 2018": "Liu et al. 2018", "Wang 2021 HRPM": "Wang et al. 2021a", "Wang 2021 DeepTrader": "Wang et al. 2021b", "Bailey 2016/2017 PBO": "Bailey et al. 2017", "Ledoit & Wolf 2004b": "Ledoit & Wolf 2004"}
TITLES = {
    "HARLF …": "HARLF: Hierarchical reinforcement learning and lightweight LLM-driven sentiment integration for financial portfolio optimization",
    "FinRL-Meta: Market environments and benchmarks …": "FinRL-Meta: Market environments and benchmarks for data-driven financial reinforcement learning.",
    "The generalization of 'Student's' problem …": "The generalization of 'Student's' problem when several different population variances are involved.",
    "HAC covariance matrix estimation": "Heteroskedasticity and autocorrelation consistent covariance matrix estimation",
    "deep RL(ICLR 2016)": "deep RL. ICLR 2016",
    "A systematic literature review …": "A systematic literature review … [check: full title]",
    "State of the art: Reproducibility in AI": "State of the art: Reproducibility in artificial intelligence",
}


def references(body):
    """Entries from notes/references_verified_2026-11-25.md sections 1-3 whose first surname occurs in the text."""
    src = (ROOT / "notes" / "references_verified_2026-11-25.md").read_text(encoding="utf-8")
    src = src.split("## 4.")[0]
    add = (ROOT / "notes" / "references_verified_addendum_2026-11-26.md").read_text(encoding="utf-8")
    src += "\n" + add.split("## 내용 메모")[0]
    rows = []
    for line in src.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 3 or c[0] in ("키", "---") or set(c[0]) <= set("-"):
            continue
        if c[0] == "Ledoit & Wolf 2004a":  # not cited; the GAPS code uses the identity-target estimator (2004b)
            continue
        key0 = RENAME.get(c[0], c[0])
        name = re.split(r"[ ,&]", key0)[0]
        yr = re.findall(r"(\d{4})", key0)
        if name and yr and re.search(r"\b" + re.escape(name) + r"\b[^;()]{0,40}?[ (]" + yr[-1], body):
            bib = re.sub(r"\s*\(\d+인\)", "", c[1])
            bib = bib.replace(" 외", " et al.").replace("(석사논문)", " (master's thesis)").replace(" 프리프린트", " preprint")
            bib = re.sub(r"\(사전 등록 노트 기준\)", "", bib)
            for a, b in TITLES.items():
                bib = bib.replace(a, b)
            bib = re.sub(r"\bRL\b", "reinforcement learning", bib)
            bib = re.sub(r"\bML\b", "machine learning", bib)
            bib = re.sub(r"\bAI\b", "artificial intelligence", bib)
            key = re.sub(r"\s+(PPO|A2C/A3C|DDPG|TD3|SB3|Ensemble|RAT|FinRL library|FinRL|PRUDEX|DeepAries|MARS|Margin Trader|WaveCorr|EIIE|PPN|EarnMore|HARLF|FinRL-Meta|EarnHFT|FreQuant|DeepClair|LSRE-CAAN|MoEDRLPM|Chronos|MTGNN|iTransformer|PatchTST|StockMixer|RevIN|LoRA|Mamba|LightGBM|tslearn|CAPS|DQN|options|PBO)$", "", c[0])
            key = RENAME.get(c[0], key)
            rows.append(f"- {key}. {bib}. {re.sub(r'[(（].*[가-힣].*[)）]', '', c[2]).strip()}")
    extra = ["- André & Coqueret 2020. André, Coqueret. Dirichlet policies for reinforced factor portfolios. arXiv 2011.05381",
             "- Abbade & Costa 2026. Abbade, Costa. Realistic market impact modeling for reinforcement learning trading environments. arXiv 2603.29086"
]
    rows = [re.sub(r"(\d{4}\. )([a-z])", lambda m: m.group(1) + m.group(2).upper(), r, count=1).replace("artificial intelligence Review", "Artificial Intelligence Review").replace("et al..", "et al.").replace("..", ".")
            for r in rows]
    return "# References\n\n[check: convert to the required citation style; verify each title against the source.]\n\n" + "\n".join(sorted(set(rows) | {e for e in extra if re.search(re.split(r"[ ,&]", e[2:])[0], body)}, key=lambda r: r[2:].lower()))


body = "\n\n".join(p.strip() for p in parts) + "\n"
body = "\n".join(l for l in body.splitlines() if not l.startswith("> Working note"))
body = re.sub(r"\n{3,}", "\n\n", body)
text = body + "\n" + references(body) + "\n"
text = text.replace("(Section 3.2 of the methods)", "(Section 6.3)")
OUT.write_text(text, encoding="utf-8")
left = sorted(set(re.findall(r"\b[XYZ]\.\d", text)))
print(OUT.name, len(text.split()), "words;", text.count("[check"), "[check] items; leftover labels:", left)
