# Thesis build (English)

Generated from `../THESIS_EN_DRAFT.md` by `build.sh` (pandoc 3.5). Do not edit `thesis.tex` / `thesis.docx` by hand; edit the Markdown and rerun:

```bash
PANDOC=/path/to/pandoc bash thesis/en/build/build.sh
```

`build.sh` needs pandoc >= 3.1 and python3. The default `PANDOC` path points to a temporary copy in a session scratchpad and will disappear; set `PANDOC` to your own binary (static releases: https://github.com/jgm/pandoc/releases).

## Outputs

- `thesis.tex`: standalone LaTeX, `report` class, 12pt, A4, 1-inch margins. It has a title page, abstract, table of contents, chapters 1 to 9, `\appendix` + Appendix A, and References. Abstract and References are unnumbered chapters. Figures are included as `../figures/*.pdf`.
- `thesis.docx`: Word file built with pandoc's default styles. It has a title, an author line, a TOC field, embedded PNG figures and native Word tables. Math is native Word equations.

## Heading numbering

- LaTeX: the manual numbers ("Chapter 3.", "6.2", "6.2.1") are removed from the heading text and LaTeX numbers the headings itself. The numbers come out the same because the Markdown numbering is sequential.
- DOCX: the manual numbers are kept in the heading text, and Word automatic heading numbering is not used.

## Compiling thesis.tex

The file is written for **pdfLaTeX**.

- Overleaf: upload `thesis.tex` into a folder `build/` and the figures into `figures/`, so that `../figures/fig1_funnel.pdf` resolves. The simplest way is to upload the whole `thesis/en/` folder (it must contain `build/thesis.tex` and `figures/`) and set `build/thesis.tex` as the main document. Alternatively, put `thesis.tex` at the project root and replace `../figures/` with `figures/`.
- Locally: `cd thesis/en/build && latexmk -pdf thesis.tex`. Run it twice, or let latexmk do it, so the TOC is filled in.

Packages used: geometry, inputenc, fontenc, lmodern, textcomp, amsmath, amssymb, graphicx, booktabs, longtable, array, calc, multirow, caption, pifont, newunicodechar, url, hyperref. All are in TeX Live.

## Known issues

- **Not compiled.** No LaTeX was available when this was generated. Environment and brace balance were checked by script only. Expect to fix a few small errors on the first compile.
- **Unicode.** The Markdown contains − ± Δ δ α σ κ Σ → ≥ ≤ ≈ × √ · ✓ ✗ ᵃ ᵇ ᶜ ᵈ ⁻ ¹ ³ ⁴ ⁹ and the combining tilde in "w̃". These are mapped with `\newunicodechar` in the preamble, and "w̃" is turned into `\tilde{w}` during post-processing. Any new non-ASCII character added to the Markdown needs a new mapping, or pdfLaTeX will stop with "Unicode character not set up". There are no Korean characters.
- **Wide tables.** Several tables have 7 to 9 columns (Tables 4.2, 6.1 to 6.3, 7.x). Pandoc turns them into `longtable`s with `p{}` columns whose widths come from the Markdown line widths. They fit the text width but wrap heavily, and they are set in `\small`. Consider `\footnotesize`, landscape (`pdflscape`) or manual column widths for the final version.
- **Table captions** are bold paragraphs ("**Table 3.1.** ...") above each table, not LaTeX/Word captions. As a result they are not in a list of tables and are not auto-numbered.
- **Figure captions.** The "**Figure N.M.** ..." paragraph is moved into the real caption. LaTeX numbers figures per chapter (6.1, 7.1), which matches the manual numbers. In DOCX the caption text keeps "Figure N.M.".
- **Footnotes** are written as Unicode superscript marks (¹, ᵃ ...) with the note as a plain paragraph. They are not converted to `\footnote`.
- **Cross-references** ("Section 6.6", "Chapter 7") are plain text, not `\ref` links.
- **[check: ...] markers** are kept in bold in both outputs (14). The title marker is replaced by the title page: title "[Title to be decided]", author "Seungbin Kwon [check]".
- **References** come from a hand-written list, not BibTeX. They appear as an itemized unnumbered chapter after the appendix.
- The DOCX table of contents is a field. Word asks to update it on opening, or you can right-click it and choose Update Field.
