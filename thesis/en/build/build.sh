#!/usr/bin/env bash
# Build thesis.tex and thesis.docx from ../THESIS_EN_DRAFT.md.
# Usage:  PANDOC=/path/to/pandoc bash thesis/en/build/build.sh
# Requires pandoc >= 3.1 and python3. No LaTeX needed (only .tex source is produced).
set -euo pipefail

PANDOC="${PANDOC:-/private/tmp/claude-501/-Users-seungbin-school-4-1-------/e9f6f6e8-2d56-4c96-a326-738b6cf12ec5/scratchpad/pandoc/pandoc-3.5-arm64/bin/pandoc}"
BUILD="$(cd "$(dirname "$0")" && pwd)"
EN="$(dirname "$BUILD")"
SRC="$EN/THESIS_EN_DRAFT.md"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

TITLE='[Title to be decided]'
AUTHOR='Seungbin Kwon [check]'

"$PANDOC" --version | head -1

# ---------------------------------------------------------------- 1. preprocess
# Make [check: ...] markers bold so they stay visible in both outputs.
python3 -I - "$SRC" "$TMP/src.md" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
# headings that follow a paragraph without a blank line (e.g. "# References")
t = re.sub(r"(?<=[^\n])\n(#{1,6} )", r"\n\n\1", t)
t = re.sub(r"\[check:[^\]\n]*\]", lambda m: "**" + m.group(0) + "**", t)
open(sys.argv[2], "w", encoding="utf-8").write(t)
PY

# ---------------------------------------------------------------- 2. Lua filter
cat > "$TMP/headings.lua" <<'LUA'
-- Heading handling.
--  LaTeX: '# Chapter N. Title' -> \chapter{Title}; '# Appendix A. Title' -> \appendix + \chapter{Title};
--         '## N.M Title' / '### N.M.K Title' -> \section / \subsection without the manual number;
--         Abstract and References -> unnumbered chapters; \tableofcontents after the abstract.
--  DOCX:  manual numbers are kept in the heading text (Word auto-numbering is not used).
--  Both:  the '# [check: title]' heading is dropped (title comes from metadata);
--         '## Abstract' is promoted to a level-1 unnumbered heading.
local is_latex = FORMAT:match("latex") ~= nil
local toc_done = false

local function drop_words(inlines, n)
  local out = pandoc.List(inlines)
  local dropped = 0
  while #out > 0 and dropped < n do
    local x = out:remove(1)
    if x.t == "Str" then dropped = dropped + 1 end
  end
  while #out > 0 and (out[1].t == "Space" or out[1].t == "SoftBreak") do out:remove(1) end
  return out
end

function Header(h)
  local txt = pandoc.utils.stringify(h)
  if h.level == 1 and txt:match("^%[check: title%]") then return {} end
  if h.level == 2 and txt == "Abstract" then
    h.level = 1
    h.classes:insert("unnumbered")
    return h
  end
  if h.level == 1 and txt == "References" then
    h.classes:insert("unnumbered")
    return h
  end
  if not is_latex then return h end

  local pre = {}
  if h.level == 1 and not toc_done then
    toc_done = true
    pre = { pandoc.RawBlock("latex", "\\tableofcontents") }
  end
  if h.level == 1 and txt:match("^Chapter %d+%.%s") then
    h.content = drop_words(h.content, 2)
  elseif h.level == 1 and txt:match("^Appendix %u%.%s") then
    h.content = drop_words(h.content, 2)
    table.insert(pre, pandoc.RawBlock("latex", "\\appendix"))
  elseif h.level >= 2 and txt:match("^%d+%.%d[%d%.]*%s") then
    h.content = drop_words(h.content, 1)
  end
  table.insert(pre, h)
  return pre
end

-- Figures: the Markdown has '![Figure N.M](...)' followed by a paragraph
-- '**Figure N.M.** text'. Move that paragraph into the figure caption.
-- LaTeX numbers figures itself (per chapter, giving the same N.M), so the label is dropped there;
-- in DOCX the caption keeps 'Figure N.M.' because Word captions are not numbered by pandoc.
function Blocks(blocks)
  local out = pandoc.List()
  local i = 1
  while i <= #blocks do
    local b, nxt = blocks[i], blocks[i + 1]
    if b.t == "Figure" and nxt and nxt.t == "Para" and nxt.content[1]
       and nxt.content[1].t == "Strong"
       and pandoc.utils.stringify(nxt.content[1]):match("^Figure %d+%.%d+%.?$") then
      local cap = pandoc.List(nxt.content)
      if is_latex then
        cap:remove(1)
        while #cap > 0 and cap[1].t == "Space" do cap:remove(1) end
      end
      b.caption = { long = { pandoc.Plain(cap) } }
      out:insert(b)
      i = i + 2
    else
      out:insert(b)
      i = i + 1
    end
  end
  return out
end

-- LaTeX: use the vector PDF versions of the figures, path relative to build/.
function Image(img)
  if is_latex then
    img.src = img.src:gsub("^figures/(.-)%.png$", "../figures/%1.pdf")
  end
  return img
end
LUA

# ---------------------------------------------------------------- 3. LaTeX template
cat > "$TMP/template.tex" <<'TEX'
\documentclass[12pt,a4paper]{report}
\usepackage[margin=1in]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{textcomp}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs,longtable,array,calc}
\usepackage{multirow}
\usepackage{caption}
\usepackage{pifont}
\usepackage{newunicodechar}
\usepackage[hyphens]{url}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=black,urlcolor=blue,citecolor=black}
\setcounter{secnumdepth}{3}
\setcounter{tocdepth}{2}
\setlength{\emergencystretch}{3em}
% --- macros emitted by pandoc 3.x
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\makeatletter
\newsavebox\pandoc@box
\newcommand*\pandocbounded[1]{%
  \sbox\pandoc@box{#1}%
  \Gscale@div\@tempa{\textheight}{\dimexpr\ht\pandoc@box+\dp\pandoc@box\relax}%
  \Gscale@div\@tempb{\linewidth}{\wd\pandoc@box}%
  \ifdim\@tempb\p@<\@tempa\p@\let\@tempa\@tempb\fi
  \ifdim\@tempa\p@<\p@\scalebox{\@tempa}{\usebox\pandoc@box}%
  \else\usebox{\pandoc@box}\fi}
\makeatother
\newcounter{none} % used by pandoc for uncaptioned longtables
\setlength{\LTleft}{0pt}\setlength{\LTright}{0pt}
% --- Unicode characters used in the Markdown source (pdfLaTeX)
\newunicodechar{−}{\ensuremath{-}}
\newunicodechar{±}{\ensuremath{\pm}}
\newunicodechar{Δ}{\ensuremath{\Delta}}
\newunicodechar{δ}{\ensuremath{\delta}}
\newunicodechar{α}{\ensuremath{\alpha}}
\newunicodechar{σ}{\ensuremath{\sigma}}
\newunicodechar{κ}{\ensuremath{\kappa}}
\newunicodechar{Σ}{\ensuremath{\Sigma}}
\newunicodechar{→}{\ensuremath{\rightarrow}}
\newunicodechar{≥}{\ensuremath{\geq}}
\newunicodechar{≤}{\ensuremath{\leq}}
\newunicodechar{≈}{\ensuremath{\approx}}
\newunicodechar{×}{\ensuremath{\times}}
\newunicodechar{√}{\ensuremath{\surd}}
\newunicodechar{·}{\ensuremath{\cdot}}
\newunicodechar{✓}{\ding{51}}
\newunicodechar{✗}{\ding{55}}
\newunicodechar{ᵃ}{\textsuperscript{a}}
\newunicodechar{ᵇ}{\textsuperscript{b}}
\newunicodechar{ᶜ}{\textsuperscript{c}}
\newunicodechar{ᵈ}{\textsuperscript{d}}
\newunicodechar{⁻}{\textsuperscript{\ensuremath{-}}}
\newunicodechar{¹}{\textsuperscript{1}}
\newunicodechar{³}{\textsuperscript{3}}
\newunicodechar{⁴}{\textsuperscript{4}}
\newunicodechar{⁹}{\textsuperscript{9}}

\title{$title$}
\author{$author$}
\date{}

\begin{document}
\begin{titlepage}
\centering
\vspace*{0.25\textheight}
{\LARGE\bfseries $title$\par}
\vspace{2cm}
{\large $author$\par}
\vfill
{\large \today\par}
\end{titlepage}
\pagenumbering{roman}

$body$

\end{document}
TEX

# ---------------------------------------------------------------- 4. LaTeX
"$PANDOC" "$TMP/src.md" -f markdown -t latex \
  --template="$TMP/template.tex" \
  --top-level-division=chapter \
  --lua-filter="$TMP/headings.lua" \
  -M title="$TITLE" -M author="$AUTHOR" \
  -o "$TMP/thesis.tex"

# post-process: combining tilde (w̃) is not handled by inputenc; switch to arabic page
# numbers at Chapter 1; small tables.
python3 -I - "$TMP/thesis.tex" "$BUILD/thesis.tex" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
t = re.sub(r"(\w)\u0303", lambda m: r"\ensuremath{\tilde{" + m.group(1) + "}}", t)
# arabic numbering from the first numbered chapter
t = re.sub(r"(\\chapter\{)", r"\\clearpage\\pagenumbering{arabic}\n\1", t, count=1)
# smaller font for tables
t = t.replace(r"\begin{longtable}", "{\\small\n\\begin{longtable}").replace(r"\end{longtable}", "\\end{longtable}\n}")
open(sys.argv[2], "w", encoding="utf-8").write(t)
PY

# ---------------------------------------------------------------- 5. DOCX
"$PANDOC" "$TMP/src.md" -f markdown -t docx \
  --lua-filter="$TMP/headings.lua" \
  --resource-path="$EN" \
  --toc --toc-depth=2 \
  -M title="$TITLE" -M author="$AUTHOR" \
  -o "$BUILD/thesis.docx"

ls -l "$BUILD/thesis.tex" "$BUILD/thesis.docx"
