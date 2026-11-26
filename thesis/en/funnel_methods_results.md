# Reproduction funnel — methods and results (English draft, 2026-11-25)

> Working draft for the thesis chapter on the reproduction funnel. Sources: `notes/funnel_protocol.md`, `notes/f1_recheck_prereg.md`, `notes/lit/f1/f1_recheck_log.md`, `notes/f1_author_account_sweep_prereg.md`, `notes/funnel_f1_recheck_followup.md`, `notes/lit/f1/funnel_table.csv`, `notes/paper_tables_draft.md`. Process details (commit hashes, run counts, audit history) stay in the repository and are not part of the text below. Numbers marked [check] must be re-verified against the source note before submission.

---

## X.1 Sample

We assembled three samples of papers that propose a reinforcement-learning method for multi-asset portfolio allocation and report out-of-sample performance.

- **S56.** A collection of 56 papers (2017–2026) compiled earlier for a different purpose. Its search strings and selection rules were not recorded at the time, so we treat it as a convenience sample and do not reconstruct a search after the fact. Four of these papers (T1–T4) had been selected for in-depth reproduction before the funnel protocol was fixed; they are reported separately, leaving 52.
- **S-Q.** A documented title search (Semantic Scholar Graph API, titles containing both "portfolio" and "reinforcement learning", 2017–2026, restricted to AAAI, IJCAI, KDD, WWW, CIKM, NeurIPS, ICML, ICLR, AAMAS, ICAIF and TMLR), yielding 12 papers not already in S56. The search was run after S56 was known and is not a systematic review.
- **Supplementary.** Five papers added because code was already known to exist. They are excluded from any code-availability rate.

The unit of analysis is the paper. Papers sharing a code lineage are counted separately.

## X.2 Stages

Each paper passes through a fixed sequence of stages and is counted once, at the first stage it does not pass; the outcomes are reported in Table 1. The stages were fixed before any stage judgment was made.

| Stage | Question | Pass criterion |
|---|---|---|
| F0 Eligibility | Does the paper propose a multi-asset RL method and report out-of-sample results? | Both hold; platforms and surveys are excluded |
| F1 Official code | Is the authors' code publicly available? | The paper or an author page points to the repository, or it is hosted on an author's (or the authors' organization's) account, and it opens on the check date |
| F2 Code completeness | Are training and evaluation entry points present? | Training and evaluation scripts plus environment and reward code |
| F6 Comparison target | Are reported values available to compare against? | An evaluation period and values in a table or the text (values read from a figure are marked) |
| F3 Data | Can the original data be obtained without author request or paid subscription? | Bundled, same public snapshot, re-collected, or to be constructed; the last two pass only if the asset list and input specification are fixed by the paper or code |
| F4 Execution | Does a minimal training-and-evaluation path run with permitted modifications only? | Judged by actual execution, with performance outputs left unopened |
| F5 Compute | Does one seed fit the budget? | ≤ 10 hours per seed on the stated device, extrapolated from a short run by a formula fixed in advance |
| F7 Verdict | Are the reported values reproduced? | Per-target pre-registered criteria (Section X.4) |

F6 is placed before F3 because it is a static judgment. Papers that pass F0–F3 and F6 enter the execution stages in a fixed order (main-track venues first, then most recent year, then smallest repository), and at most two papers in that order receive an F7 verdict. "Not executable" and "over budget" are outcomes under our environment and time limits; they are not counted as reproduction failures.

## X.3 Checking the F1 judgments

F1 was the stage at which most papers exited, and its initial judgments were made with the assistance of a large language model. We therefore re-checked them under a pre-registered procedure.

**Design.** One human rater re-judged every paper that had not passed F1 (44 papers, excluding two whose full text could not be obtained) and a random sample of 10 of the 27 papers that had passed F1 at the time of the check (before the five papers below were found). For each paper the rater searched the full text for code-related terms, the venue's supplementary material, the first and corresponding authors' GitHub accounts and home pages, and the Hugging Face paper page, and assigned one of six labels (found; third-party only; link dead; available on request; none; full text unavailable). The rater had seen the original judgments, so the check is not blind. Where the rater's label disagreed with the original judgment, the disagreement was resolved by inspecting the cited repository or sentence; the rater's confirmed label is final.

**Results.** Among the 44 papers that had not passed F1, official code was located for 4 (9.1%; 95% Wilson interval 4–21%). If only first- or corresponding-author accounts are accepted, the count is 2 of 44. In all four cases the paper itself contained no link, and the repository could be identified only through an author's personal GitHub account. None of the 10 sampled passes was overturned (0/10; 95% interval 0–28%). Binary agreement over the 54 checked papers was 0.926 (Cohen's κ 0.787; because the sample is stratified, this is not a population agreement rate). Before disagreements were resolved, the rater's own initial labels differed more: the rater had found code for 2 of the 44 papers and had labelled 7 of the 10 sampled passes as having no official code; on inspection, all 7 had an open official repository, mostly on an author's GitHub account that the rater had not checked (agreement 0.833, κ 0.315). The final labels above therefore rely on the resolution step.

**Author-account search.** Because every missed repository sat on an author's personal account, we additionally searched the GitHub accounts of the first and last authors of the remaining papers. The search was exploratory and its procedure was fixed before it was run. It covered 30 of the 40 remaining papers (for the others the authors could not be identified or the account search returned nothing) and located one more official repository, confirmed by the rater (5 of 44 in total; 95% interval 5–24%). Applied to papers whose author repositories were already known, the same search found 2 of 5, so its sensitivity is low and the absence of a candidate is weak evidence that no code exists. The figures above are lower bounds on official code that our F1 stage missed.

**Consequence for Table 1.** The five papers whose code was located are shown in a separate row. Their later stages were examined outside the fixed execution order and are reported as exploratory: one exited at F3 (the dataset link given in the paper is not public and the news source is unspecified), one at F4 (the legacy exchange API used by the code no longer serves data), one at F6 (the evaluation period is not reported), and two reached exploratory F7 comparisons, one of them against values read from a figure (Table 3).

## X.4 Results

[Insert Table 1 from `notes/paper_tables_draft.md`.]

Of the 52 S56 papers, 4 were not eligible (F0). Thirty-one exited at F1 — 25 with no official code found (authors not contacted), 2 with a dead link, 2 with third-party code only and 2 with full text unavailable — and a further 5 had official code located only at the F1 check. Of the papers that passed F1 within the fixed order, 3 exited at F3, 1 at F4 (not executable) and 2 at F5 (over budget); 4 passed F4 (one of them also F5) without an F7 attempt because the two F7 places were filled, and 2 reached an F7 verdict.

In S-Q, 9 of 12 papers exited at F1 with no official code found; of the remaining three, one was not executable, one was not tested because its inputs would have to be constructed from sources the code does not collect, and one passed F4. Among the five supplementary papers, which were included because code was known to exist, one was not eligible (F0), one had a dead official link with a copy elsewhere, two exited at F2 (incomplete code) and one was not executable.

Two S56 papers reached F7 under the fixed order — the ensemble strategy (ICAIF 2020) and the Relation-Aware Transformer (IJCAI 2020) — and both were partially reproduced (Table 2).

## X.5 Limitations specific to the funnel

- S56 was assembled without a recorded search, and S-Q was run after S56 was known. Proportions describe these samples only.
- "No official code found" includes the limits of our search; authors were not contacted. The F1 check shows that this category contains at least 5 of 44 papers whose code exists.
- The F1 check was carried out by a single rater who was not blind to the original judgments.
- Execution outcomes (F4, F5) depend on our hardware, software environment and time budget. Ordering by repository size may bias untested papers toward larger repositories, and older frameworks may be disadvantaged.
