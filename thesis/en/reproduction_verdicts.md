# Reproduction verdicts — methods and results (English draft, 2026-11-25)

> Working draft for the thesis chapter on reproduction verdicts (Table 2). Sources: `notes/paper_tables_draft.md` (Table 2), `notes/prereg_reeval_v3.md`, per-target result notes (`notes/deeparies_o1_result.md`, `notes/alphamix_t2_o1_result.md`, `notes/finrl_t3_o1_result.md`, `notes/mars_t4_o1_result.md`, `notes/funnel_f7_ensemble_result.md`, `notes/funnel_f7_rat_result.md`), exploratory notes (`notes/funnel_f7x_margintrader_result.md`, `notes/funnel_f7x_frontier_prereg.md` §8, `notes/funnel_f1_recheck_followup.md`). Reported values are cited only after the user has checked them against the original PDF (`notes/claim_ledger.md`, section A). [check] marks numbers to re-verify before submission. No process details in the text.

---

## Y.1 Verdict rules

For each target we fixed, before running anything, the reported value to be compared, the aggregation over runs, and two criteria.

- **R1 (value).** Our aggregate lies within a tolerance band around the reported value. The half-width of the band is half the gap between the reported value and the strongest external baseline reported in the same table, so that a result counts as reproduced only if it is closer to the reported value than to the point where the paper's advantage would vanish.
- **R2 (claim).** The paper's comparative claim — typically that the method outperforms its strongest reported baseline — holds in our runs, with a minimum number of runs specified per target.

A target is *reproduced* if both criteria hold, *partially reproduced* if exactly one holds, and *not reproduced* if neither holds. Aggregation follows the paper where it is stated (for example, a seed-selection rule) and is otherwise fixed in advance (mean or median over seeds). We used the authors' public code at the version closest to publication, modifying it only to run on our hardware, to log outputs, or to fix errors that prevent execution, and we report every such change.

## Y.2 Results

[Insert Table 2 from `notes/paper_tables_draft.md`.]

Six papers received a verdict: four selected in advance for in-depth study (T1–T4) and two that reached the final stage of the funnel.

**DeepAries (T1).** Following the paper's rule of reporting the seed with the lowest validation loss among ten, our compound annual growth rate was 5.04% against a reported 7.90% (band ±0.87); two of ten seeds fell inside the band, and the claimed advantage over the index did not hold. The paper's own index comparison value could not be reproduced over the period defined in the code. A variant trained for ten epochs, as suggested in the repository, was also not reproduced (6.38%). Verdict: not reproduced.

**AlphaMix+ (T2).** Judged over three test years, the reported total return was matched in one year (2019) and missed in two; the claimed advantage over the market average did not hold. This verdict depends on two choices that the paper leaves unspecified: which training epoch is reported and whether the market-average baseline is rebalanced. Selecting the epoch by validation performance would make the verdict *reproduced*, and a buy-and-hold market average would make it *partially reproduced*. Verdict under the pre-specified definitions: not reproduced.

**FinRL (T3).** Each of the four algorithms was judged separately on annualized return, using 28 of the paper's 30 stocks. PPO and TD3 were reproduced; A2C (35.36% against 42.57%) and DDPG (37.60% against 36.01%, outside the band by less than 0.01 percentage points) were partially reproduced. The claimed advantage over the Dow Jones Industrial Average held for all four. Under our family rule (at least three of four algorithms reproduced), the paper is partially reproduced.

**MARS (T4).** With the code as of publication, the median cumulative return over ten seeds was 15.26% against a reported 29.50% (band ±7.07), close to the index; the verdict is not reproduced. A later revision of the repository by the authors gives a median of 26.41% with seven of ten seeds in the band, which is reproduced. A bundled checkpoint also lies within the band, but its selection procedure is undocumented, so we do not use it as evidence.

**Ensemble strategy (funnel).** The mean Sharpe ratio over five runs was 1.01 against a reported 1.30 (band ±0.415), satisfying R1; however, only one of five runs exceeded the strongest reported baseline, so R2 failed. Verdict: partially reproduced.

**Relation-Aware Transformer (funnel).** The mean final accumulated portfolio value was 378.35 against a reported 156.53 (band ±68.42) — outside the band on the high side — while the claimed ranking against baselines held in all runs. Verdict: partially reproduced. A value far above the reported one is not evidence of a stronger method; candidate explanations include checkpoint selection on the test period, leverage permitted by the code, and differences between the released code and the version used in the paper, none of which we could isolate.

## Y.3 Exploratory verdicts outside the fixed order

Three further papers were run outside the fixed order, under the same kind of pre-registered criteria. They are reported separately and are not counted with the verdicts above.

- **Margin Trader (ICAIF 2023).** The authors' script runs only A2C, so we compared against the paper's A2C long–short row (Sharpe 0.793). The mean Sharpe over five seeds was 0.148 (SD 0.153); no seed reached the band. Exploratory verdict: not reproduced.
- **FRONTIER (Pretorius and van Zyl).** The paper reports the method's performance only as a Pareto frontier in a figure. At an excess risk of 14.78%, our mean frontier was 11.71% against 11.79% read from the figure (band [10.78, 12.80]), and it dominated the strongest comparator in all five seeds. Exploratory verdict: both criteria hold. The comparison is to values read from a figure, and the equal-weight comparator in the paper is weak.
- **Markowitz Meets Bellman (KDD).** In the authors' public code, the script producing the reported curve restricts the universe to five tickers (AAPL, BA, CRM, UNH, V), whereas the paper describes a Dow Jones 30 universe, and the knowledge-distillation component is disabled. We therefore compared against the authors' five-ticker run. Re-evaluating the released checkpoint reproduced the authors' stored curve exactly. Retraining with five seeds gave an averaged-curve Sharpe ratio of 1.81 against a reported 2.03 (band ±0.525); no seed exceeded an equal-weight portfolio of the same five stocks (Sharpe 2.00, 0.1% cost). Pre-specified reading: the reported value is indistinguishable from holding the same five stocks. The policies behind the reported curve hold what they buy on the first day (Section Z.5).

## Y.4 What the verdicts do and do not show

- At the paper level, with the code at publication and the definitions fixed in advance, no paper was fully reproduced: three were partially reproduced (FinRL, the ensemble strategy and the Relation-Aware Transformer) and three were not reproduced (DeepAries, AlphaMix+ and MARS). Within FinRL, two of four algorithms were reproduced, and MARS was reproduced with a later revision of the authors' code. [check against Table 2 before submission.]
- We do not aggregate these into a single reproduction rate: the six papers are not a random sample, four were chosen before the protocol, and verdicts for two (AlphaMix+, MARS) change with choices the papers leave unspecified or with the code version.
- A failed verdict does not show that a paper's numbers are wrong. Our runs differ from the authors' in hardware, library versions and nondeterminism, and in several cases the paper does not specify the procedure that produced the reported value.
