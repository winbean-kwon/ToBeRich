# Paper tables — draft (2026-11-14, Table 3 추가 2026-11-25)

> Working note (Korean header for the repo; table text is in paper English).
> 상태: 초안. 출처는 `notes/lit/f1/funnel_table.csv`(funnel_table.py 출력)와 `replication/reproduction_synthesis.csv`. F1 재확인은 반영했다(2026-11-24, 54편 사람 확인 완료, `notes/lit/f1/f1_recheck_log.md`). 대장 A절(보고값 원문 대조)은 2026-11-14 사용자 확인으로 모두 "일치"다(Table 2 보고값 확정). Table 2 각주 c(AlphaMix+ 판정 민감도)는 2026-11-25 사용자 결정으로 넣는다. 재현율을 한 수치로 합치지 않는다(프로토콜 0장). 표 본문에는 과정 기록(커밋·시도 횟수·감사 경위)을 넣지 않는다.

---

## Table 1. Reproduction funnel: first stage at which each paper exited, by sample

Each paper is counted once, at the first stage it did not pass. Stages follow the pre-registered protocol: F0 eligibility, F1 official code, F2 code completeness, F3 data availability, F4 execution, F5 compute budget (10 h per seed), F7 reproduction verdict. No paper in the fixed order exited at F6 (reported comparison values). S56: an existing literature collection (56 papers, of which four were the in-depth targets T1–T4 and are listed separately). S-Q: a documented title search (Semantic Scholar, 2017–2026, selected venues). Supplementary: papers added because code was already known to exist; they are excluded from code-availability rates.

| Exit stage / outcome | S56 (n = 52) | S-Q (n = 12) | Suppl. (n = 5) | T1–T4 (n = 4) |
|---|---:|---:|---:|---:|
| F0 not eligible | 4 | 0 | 1 | 0 |
| F1 no official code found (authors not contacted)ᵇ | 25 | 9 | 0 | 0 |
| F1 link dead | 2 | 0 | 1ᵃ | 0 |
| F1 third-party code only | 2 | 0 | 0 | 0 |
| F1 full text unavailable | 2 | 0 | 0 | 0 |
| Official code located at the F1 check; later stages exploratoryᶜ | 5 | 0 | 0 | 0 |
| F2 incomplete code | 0 | 0 | 2 | 0 |
| F3 data not obtainable as specified | 3 | 0 | 0 | 0 |
| F4 not executable | 1 | 1 | 1 | 0 |
| F4 not tested (input construction out of scope) | 0 | 1 | 0 | 0 |
| Passed F4 (and F5 where measured), no F7 placeᵈ | 4 | 1 | 0 | 0 |
| F5 over compute budget | 2 | 0 | 0 | 0 |
| F7 verdict reached | 2 | 0 | 0 | 4 |

ᵃ A copy of the repository exists elsewhere; the official link is dead.
ᵇ A human check of all papers that did not pass F1 located official code for 4 of 44 (95% Wilson interval 0.04–0.21; 2 of 44 when only first- or corresponding-author accounts are accepted); a subsequent search of first- and last-author GitHub accounts located one more (5 of 44, 0.05–0.24). In every case the paper contained no link, and the repository was identifiable only through an author's personal GitHub account. Author accounts were not searched exhaustively for the remaining papers, so this count is a lower bound on missed code.
ᶜ These papers were examined outside the fixed execution order. One exited at F3 (dataset link not public, news source unspecified), one at F4 (legacy exchange API no longer serves data), one at F6 (evaluation period not reported), and two reached an exploratory F7 comparison (Table 3).
ᵈ The two F7 places were filled in the fixed order before these papers; one of them also passed F5 (3.9 h per seed).

Notes for the text (not table content):
- F1 check (methods/limitations): one human rater, not blind to the original LLM-assisted judgments; disagreements were resolved by inspecting the cited repository or sentence, with an LLM proposing the evidence and the rater confirming it. Report the rater's original judgments as well (random sample of F1 passes: 7 of 10 initially judged as not found; all 7 had an open official repository on inspection). Second rater on 15 papers: pending.
- "Not executable" and "over compute budget" are outcomes under our environment and time limits; they are not counted as reproduction failures.
- F7 for the two S56 papers: Ensemble strategy (ICAIF 2020) and RAT (IJCAI 2020), both *partially reproduced* (Table 2).

---

## Table 2. Reproduction verdicts against reported values

R1: our aggregate falls within the tolerance band (half the gap between the reported value and a comparator from the same table fixed in advance per target, usually the market index named in the paper's claim; for AlphaMix+, which reports no comparator, ±2σ/√n from the reported standard deviation). R2: the paper's comparative claim holds in our runs. Verdict: both → reproduced; one → partially reproduced; neither → not reproduced.

| Paper (target) | Metric | Reported | Tolerance | Ours | Runs in band | R1 | R2 | Verdict |
|---|---|---:|---:|---:|---:|:-:|:-:|---|
| DeepAries (T1) | CAGR (%) | 7.90 | ±0.87 | 5.04ᵃ | 2/10 | ✗ | ✗ | Not reproduced |
| AlphaMix+ (T2), US 2021 | TR (%) | 20.7 | ±1.61 | 18.47 | 1/5 | ✗ | ✗ᵇ | Not reproducedᵇ |
| AlphaMix+ (T2), US 2020 | TR (%) | 12.7 | ±1.52 | 9.42 | 1/5 | ✗ | ✗ᵇ | |
| AlphaMix+ (T2), US 2019 | TR (%) | 25.1 | ±1.27 | 26.09 | 3/5 | ✓ | ✗ᵇ | |
| FinRL (T3), A2C | Ann. return (%) | 42.57 | ±4.87 | 35.36 | 0/5 | ✗ | ✓ | Partially reproduced |
| FinRL (T3), PPO | Ann. return (%) | 36.17 | ±1.67 | 36.41 | 3/5 | ✓ | ✓ | Reproduced |
| FinRL (T3), DDPG | Ann. return (%) | 36.01 | ±1.59 | 37.60 | 2/5 | ✗ᶜ | ✓ | Partially reproduced |
| FinRL (T3), TD3 | Ann. return (%) | 39.38 | ±3.27 | 37.99 | 3/5 | ✓ | ✓ | Reproduced |
| MARS (T4), code at publication | CR (%) | 29.50 | ±7.07 | 15.26 | 1/10 | ✗ | ✗ | Not reproduced |
| MARS (T4), later author revision | CR (%) | 29.50 | ±7.07 | 26.41 | 7/10 | ✓ | ✓ | Reproducedᵈ (reported alongside) |
| Ensemble strategy (funnel) | Sharpe | 1.30 | ±0.415 | 1.01 | 4/5 | ✓ | ✗ | Partially reproduced |
| RAT (funnel) | fAPV | 156.53 | ±68.42 | 378.35 | 0/5 | ✗ (above) | ✓ | Partially reproduced |

ᵃ Seed selected by the paper's rule (lowest validation loss among 10 seeds).
ᵇ AlphaMix+ is judged over three test years (R1 and R2 each need ≥ 2 of 3). The verdict depends on two choices the paper leaves unspecified: which training epoch is reported, and whether the market-average baseline is rebalanced. Under validation-based epoch selection the verdict becomes *reproduced*; under a buy-and-hold market average it becomes *partially reproduced*.
ᶜ Outside the band by less than 0.01 percentage points.
ᵈ Not the pre-specified MARS verdict. The result depends on the evaluation window, which was inferred from the index row of the paper's table (partially reproduced under the alternative 251-day window), and the revision widened the range of episodes from which a checkpoint is selected.

Aggregation: DeepAries uses the paper's seed-selection rule; AlphaMix+ and RAT the seed mean; FinRL the seed median; MARS the median over 10 seeds; Ensemble the mean of five runs. FinRL uses 28 of the paper's 30 stocks.

Notes for the text (not table content):
- The FinRL family verdict is *partially reproduced* (two of four algorithms reproduced; family rule ≥ 3 for reproduced).
- MARS: the bundled checkpoint (single deterministic run) lies within the band (29.68); it is not used as general evidence because its selection procedure is undocumented.
- DeepAries 10-epoch variant: 6.38, not reproduced; not an independent result (five seeds identical to the 1-epoch runs).

---

## Table 3. Exploratory reproduction comparisons outside the fixed order

These comparisons lie outside the fixed execution order. For each paper the comparison target, tolerance band and decision rules were fixed before any of our results were inspected. R1: our aggregate lies within the band (half the gap between the reported value and the named comparator). R2 is paper-specific and stated in the column. The R2 rules differ, so the Table 2 verdict labels are not applied.

| Paper | Target | Reported | Tolerance | Ours | R1 | R2 rule | R2 | Pre-specified reading |
|---|---|---:|---:|---:|:-:|---|:-:|---|
| FRONTIER (Pretorius & van Zyl, 2022) | Mean Pareto-frontier excess return at the equal-weight excess risk of 14.78% (%) | 11.79ᵃ | ±1.01 | 11.71 | ✓ | Frontier dominates equal weight (≥ 4/5 seeds) | ✓ (5/5) | Matches the published figure |
| Markowitz Meets Bellman (Hu and Gu, 2024; method "KDD"), five-ticker run | Sharpe of the date-wise mean of run curves | 2.03 | ±0.525 | 1.81 | ✓ | Per-seed Sharpe above equal weight of the same five stocks (2.00, 0.1% cost) in ≥ 4/5 seeds | ✗ (0/5) | Reported value indistinguishable from holding the same five stocks |
| WaveCorr (Marzban et al., 2021), Canadian dataset | Mean test Sharpe over five seeds | 1.73 | ±0.295 | 1.75 | ✓ | Per-seed Sharpe above the strongest reported benchmark (CS-PPN, 1.14) in ≥ 4/5 seeds | ✓ (5/5) | Public code yields the reported figure under its own metric definitionsᵇ |
| Margin Trader (Gu et al., 2023), A2C long–short | Mean Sharpe over five seeds | 0.793 | ±0.0545 | 0.26 | ✗ | Per-seed Sharpe above the index (0.790) in ≥ 4/5 seeds | ✗ (0/5) | Not reproducedᶜ |

ᵃ Read from the published figure.
ᵇ The code trains on the paper's validation years and records the test-period value at every epoch; the released hyperparameters differ from those listed in the paper.
ᶜ A daily-rebalanced, long-only equal-weight portfolio of the same 28 stocks at the environment's cost rate had a Sharpe ratio of 0.92.

Origin of rows: FRONTIER and Markowitz Meets Bellman had official code located at the F1 check; WaveCorr and Margin Trader passed the fixed-order stages but had no place in the judged set.

Notes for the text (not table content):
- FRONTIER: the frontier is formed from 504 parameter pairs evaluated on the test period, as in the paper; the match is faithful to the published procedure but is not out-of-sample evidence of superiority over equal weight. Equal weight is a weak benchmark (long-only minimum variance has a higher Sharpe ratio). Our curve lies 0.1–0.5 percentage points below the figure at most risk levels.
- Markowitz Meets Bellman: the released code has the knowledge-distillation component disabled, so no statement is made about distillation. Re-evaluating the released checkpoint reproduces the authors' stored curve exactly; its actions are saturated at ±1 with a fixed sign per asset, and the curve equals a buy-and-hold position. All five stored run outputs averaged into the reported curve are integer-share buy-and-hold positions bought at the first day's close; their average reproduces the reported metrics exactly, and its Sharpe ratio (2.03) exceeds that of every constituent (1.61–1.81) because the averaged holdings are more diversified. Full wording: `notes/funnel_f7x_p2407_prereg.md` sections 6 and 7.1. Five-ticker restriction: the paper describes a Dow Jones 30 universe; the script producing the reported curve uses five tickers.
- Neither the FRONTIER nor the Markowitz Meets Bellman comparison has a previously published independent reproduction that we could find.
