# Methods and limitations (English draft, 2026-11-25)

> Working draft for thesis chapter 3 (Methods) and chapter 6 (Discussion and limitations), following `thesis/OUTLINE_KR.md`. Sources: `notes/prereg_reeval_v3.md` (chapters 0–4, 6–7), `notes/prereg_env_conformance_v2.md` (sections 1–3), `notes/mars_t4_o1_prereg.md`, `notes/prereg_stat_power_v2.md` (sections 0–4), `notes/funnel_protocol.md`, the exploratory pre-registrations (`notes/funnel_f7x_*_prereg.md`, `notes/degenerate_policy_baseline_prereg.md`, `notes/static_holding_test_prereg.md`), and `notes/references_verified_2026-11-25.md` for citations. The funnel stages are described in `thesis/en/funnel_methods_results.md` (X.1–X.3) and the verdict rules in `thesis/en/reproduction_verdicts.md` (Y.1); when the chapters are assembled, Y.1 and the protocol paragraph of Z.2 move here. [check] marks items to re-verify. No process details in the text.

---

# Chapter 3. Methods

## 3.1 Design and pre-registration

The study has two parts. The first follows a sample of papers through a sequence of stages, from eligibility to an attempted reproduction (the reproduction funnel, Section X). The second re-runs the official code of selected methods, asks whether the reported values and claims are reproduced (O1), and asks whether a reproduced advantage survives a common evaluation protocol with transaction costs (O2).

For every reproduction, the targets, reported values, aggregation over runs, decision rules and, where applicable, fixed interpretive statements were written down and fixed before the corresponding performance outputs were produced or opened. Outputs of runs still in progress were not inspected; progress was monitored through completion records only. Deviations were recorded with their reasons; deviations that could change a verdict led to the verdict being reported as exploratory, whereas behaviour-preserving changes verified by a pre-specified equality test did not. Analyses conceived after a result was known are labelled exploratory throughout; they were also specified in advance of their own runs, but their questions were motivated by earlier results.

## 3.2 Targets for in-depth reproduction

A repository was treated as official if the paper or a repository owned by the authors states that it implements the paper; a framework that is itself the contribution of the paper also counts. Forks, mirrors and third-party implementations were excluded.

Four methods were studied in depth: DeepAries (T1; Kim et al., 2025), AlphaMix+ from PRUDEX-Compass (T2; Sun et al., 2023), the FinRL portfolio-allocation agents A2C, PPO, DDPG and TD3 (T3; Liu et al., 2021), and MARS (T4; Chen et al., 2026). T1–T3 were fixed before the funnel protocol; a replacement order was fixed in advance for T2 in case it could not be run within an eight-hour debugging limit using permitted modifications only, but it ran without replacement. T4 was added later under its own pre-registration. Each repository was used at a fixed commit, and the bundled or first-downloaded data snapshot was frozen and not downloaded again.

**Permitted modifications.** We modified the official code only by (i) compatibility shims that restore deprecated library interfaces with the same meaning, (ii) date and split arguments, or truncating the input data where no argument exists, (iii) replacing the cost function, only in the unified protocol (Section 3.4), and (iv) logging. Algorithms, rewards, observations and hyperparameters were not changed. For MARS, its own pre-registration also permitted an execution wrapper setting the seed, output directory and device, disabling logging during training, and behaviour-preserving acceleration accepted only after an equality test against the original code. Every change is listed in the supplementary material.

## 3.3 Reproduction runs and verdicts (O1)

Each target was run under the paper's own procedure; settings not stated in the paper followed the code's defaults, and costs were left as implemented. Seeds and aggregation follow the paper where stated and were otherwise fixed in advance:

| Target | Seeds | Aggregate compared with the reported value |
|---|---|---|
| T1 DeepAries | 10 | The seed with the lowest validation loss (the paper's rule) |
| T2 AlphaMix+ | 5 | Mean (as in the paper's tables), per test year |
| T3 FinRL | 5 per algorithm | Median (not stated in the paper) |
| T4 MARS | 10 | Median |

For T1, T3 and T4, the comparator defining the band is the market index reported in the same table. For DeepAries, a band for maximum drawdown (±5.0 percentage points) was also set without a comparator, because none was reported; it does not enter the verdict, which rests on the growth rate. For T2, which reports no comparator for the compared quantity, the band was ±2σ/√n from the reported standard deviation σ over n runs in each of three test years, and R1 required at least two of three years; R2 required the seed-mean total return to exceed the daily-rebalanced market average in at least two of three years. For T3, each algorithm received its own verdict; the paper counted as reproduced if at least three of four algorithms were reproduced, partially reproduced if one or two were, and not reproduced otherwise.

## 3.4 Unified evaluation protocol (O2)

Only the pre-selected targets (T1–T4) that were reproduced or partially reproduced under O1 with the code as of publication were judged under the unified protocol; in practice, these were the four FinRL algorithms. Papers that reached a verdict through the funnel were outside this rule, and the later MARS revision does not count as the MARS verdict.

- **Cost model (U1).** The charge is c·Σ_i |w_{t,i} − w̃_{t−1,i}|, where w̃_{t−1} is the previous allocation after drifting with prices, applied to the period in which the new weights earn returns. An implementation was kept only if, in the dynamic cost check (Section 3.5), the configured cost entered both rewards and returns and the ratio of measured to reference cost was within [0.9, 1.1]; otherwise it was replaced by the reference implementation. The cost rate was the one configured in each repository (0.1% for FinRL).
- **Start state (U2).** Policy and baselines start from cash and pay for the initial purchase.
- **Windows (U3).** For FinRL, the paper's test year (W0: July 2020–June 2021) and two earlier one-year windows (W1: July 2018–June 2019; W2: July 2019–June 2020). Because the FinRL procedure has no validation stage and uses the model at the end of training, each window was trained on all data from 2009 up to the day before the window.
- **Seeds (U4).** As in O1.
- **Baselines (U5).** The primary baseline is a daily-rebalanced equal-weight portfolio of all assets in the target environment under the same cost implementation. Monthly-rebalanced and buy-and-hold equal weight and the maximum of the three were used as sensitivity analyses; price indices, to which costs cannot be applied, are reported descriptively.
- **Training conditions (U6).** (a) the original code; (b) retraining with the reference cost at the configured rate (primary); (c) retraining at a higher rate (0.2% for FinRL). Hyperparameters were not re-tuned.

The primary metric Δ is the difference in annualized log growth between a policy and the primary baseline. A window is classified as *advantage* or *disadvantage* when at least four of five seeds share the sign of Δ, and as *indeterminate* otherwise. A method *retains* its advantage if W0 and at least two of three windows show an advantage, *loses* it if W0 or at least half of the windows show a disadvantage, and is *indeterminate* otherwise. In addition, a method was marked as showing a *small difference* if the seed-median |Δ| was below 2 percentage points per year in every window; this label does not affect the classification.

## 3.5 Checking the implemented transaction cost

For each official environment, we first predicted from the code whether, and how, the configured cost is charged. We then drove the unmodified environment with injected actions along three paths — holding equal weights, alternating between two disjoint sets of assets, and buying from an all-cash start — and compared the charged cost with the reference model. The checks establish whether a configured cost enters the return at all, whether it is charged on the drifted previous allocation, and whether the first purchase is charged. Where the environment could not be run, only the static reading is reported.

## 3.6 Statistical analysis

**Effect sizes.** This analysis was specified after the O2 classifications and point estimates were known; it adds interval and power information to existing verdicts, is not blind, and does not change them. For the FinRL algorithms under O2 condition (b), we estimated the difference in Sharpe ratio (ΔSR; daily simple net returns, zero risk-free rate) and in annualized log growth (ΔG) between each algorithm and the daily equal-weight baseline. The algorithm-level statistic averages over three windows and five seeds. Confidence intervals and p-values use a studentized circular block bootstrap in the manner of Ledoit and Wolf (2008), with a delta-method standard error, a heteroskedasticity- and autocorrelation-consistent variance (Parzen kernel, automatic bandwidth following Andrews, 1991, without prewhitening), block-based bootstrap standard errors (Götze and Künsch, 1996), block length 20 days (sensitivity: 5 and 10) and 4,999 replications. Windows are strata, and within each window the same date blocks are resampled for all seeds and the baseline, so the intervals are conditional on the seeds. A two-stage bootstrap that also resamples seeds is reported as a secondary interval. Holm's (1979) correction was applied across the four algorithms for each metric.

**Categories.** Equivalence margins were taken from the smallest advantage over the index reported in the original FinRL paper: δ_G = ln(1.3601/1.3284) = 2.36 percentage points per year and δ_SR = 0.09. An algorithm was classified as *superior* or *inferior* if the Holm-adjusted p-value was below 0.05, as *equivalent* if the two one-sided tests at α/4 placed the interval within (−δ, δ), as *non-superior* if only the upper one-sided limit was below δ (an advantage of δ or more is excluded), and as *undetermined* otherwise. A category that changed with block length is flagged. The minimum detectable effect at 80% power is (z_{0.975} + z_{0.80}) times the bootstrap standard error and is reported for reference only. Before the analysis, synthetic data were used to check the size of the tests, and the observed returns, transformed to satisfy the null hypothesis, were used for a calibration check; the main block length was conservative in most cases. Unlike Ledoit and Wolf (2008), we used a Parzen kernel without prewhitening and a fixed block length, which gives up some power. DeepAries (against equal weight) and the ensemble strategy (against the index) were analysed descriptively with the same tools, without categories.

**Exploratory contrasts.** Counterfactual experiments (for example, alternative turbulence thresholds, Section Z.6) used five runs per condition and report the mean difference with a Welch (1947) 95% interval, classified in advance as distinguishable or not. Proportions in the funnel use Wilson (1927) intervals; agreement between raters uses Cohen's (1960) κ.

## 3.7 Exploratory analyses

Three kinds of analysis were added after the confirmatory results and are labelled exploratory.

1. **Reproductions outside the fixed order** (Margin Trader, FRONTIER, Markowitz Meets Bellman, WaveCorr) follow the same R1/R2 structure, with reported values, bands and aggregation fixed before the runs. Their outcomes are not counted among the verdicts in Table 2.
2. **Policy diagnostics** describe what trained policies do: the share of actions on the boundary of the action space, day-to-day changes in target weights, active share relative to equal weight, and comparisons with untrained policies initialized with the same seeds. For share-based environments, we tested whether policies held their positions fixed: for Markowitz Meets Bellman, whether each stored account-value curve equals integer-share holdings bought on the first day (maximum absolute residual 0.01 USD); for the ensemble strategy, whose outputs contain only account values, whether each trading cycle is fitted by fixed non-negative holdings plus cash (least squares, maximum relative residual 10⁻⁹); and for Margin Trader, by comparing stored holdings day by day. We also permuted the order of asset columns while keeping the policy's input and output fixed to isolate the environment's order filling.
3. **Counterfactual code changes** alter one documented element of the released code (for example, a hard-coded threshold) and compare against the unchanged code with the same number of runs.

## 3.8 Computing environment

Runs were carried out on laptop CPUs (macOS, and Linux under WSL on a second laptop), a consumer GPU (GTX 1650) and a cloud GPU (Colab T4), depending on the target. Library versions follow each repository where it pins them; deviations are listed in the supplementary material. Bitwise reproducibility across devices was not established; in one DeepAries comparison, the same seed differed by 3.4 percentage points between environments.

---

# Chapter 6. Discussion and limitations

## 6.1 What the results can and cannot support

The verdicts state whether the released code, run under definitions fixed in advance, yields the reported values and claims. They do not show that a paper's numbers are wrong: there is no record linking the reported numbers to a specific run of the released code, and our runs differ from the authors' in hardware, library versions and nondeterminism. Where a verdict changes with a choice the paper leaves open (the reported epoch and the market-average definition for AlphaMix+; the code version and the evaluation window for MARS, which we inferred from the index row of the paper's table), we report both readings and keep the pre-specified one. An indeterminate classification under O2 is not evidence of no advantage, and the equivalences in Section Z.4 hold for the configuration tested (28 assets, 0.1% cost, three one-year windows); they are the outcome expected from the policy parameterization described in Section Z.3 rather than a general statement about these algorithms.

## 6.2 Sample and selection

The methods studied in depth are those with official code that we could run. This is a selected group with shared code lineages: the AlphaMix+ environment derives from the FinRL portfolio environment, and the ensemble strategy, Margin Trader and Markowitz Meets Bellman build on FinRL environments. The funnel samples were not drawn by a systematic search (Section X.5), and the exploratory reproductions were chosen after earlier results were known; in particular, of the five papers that passed the execution stages without receiving a verdict, two (Margin Trader and WaveCorr) were run further, WaveCorr after a correction to its compute-stage judgment. No rate of reproduction is computed from these papers.

## 6.3 Data and universes

Several targets use asset lists fixed after the test period: DeepAries uses constituents from the 2020s from 2000 onward (26 of the 27 listed assets are present in the data), the AlphaMix+ list includes later index members, and the released code of Markowitz Meets Bellman restricts the universe to five tickers, whereas the paper describes 30. Because our primary baselines use the same assets, relative comparisons are not affected by this choice, but absolute performance may be overstated for policy and baseline alike. FinRL was run with 28 of the paper's 30 stocks, after excluding, by a rule fixed before any FinRL output, stocks without data at the start of training. The MARS repository bundles 50 stocks that are not Dow Jones constituents, with no stated selection rule, and its index comparison sets a price index against strategy returns that include dividend effects. Data downloaded by the code (AlphaMix+) were frozen at our first download and may differ from the authors' snapshot. For WaveCorr, the released code reads the first 50 files in directory order, which need not match the paper's random selection, and two of the selected input files are shifted by three trading days after dates missing from them; we kept the code's behaviour.

## 6.4 Runs, seeds and power

Most targets were run with five or ten seeds. The four-of-five rule used for windows is a consistency criterion, not a significance test (a one-sided sign test of five of five positive seeds has p ≈ 0.03, and four of five p ≈ 0.19). The minimum detectable effects for FinRL were 0.07–0.19 in Sharpe ratio and 1.1–1.7 percentage points per year in log growth, so smaller differences cannot be excluded. The bootstrap intervals condition on the seeds, and the Sharpe category of DDPG depends on block length. Counterfactual experiments used five runs per condition; the primary turbulence-threshold contrast changes category if one run is removed from either condition in most cases, and was below the design's minimum detectable effect. The reference and counterfactual runs of the ensemble strategy were not run concurrently; two later repeats of the reference condition fell within the range of the original five runs.

## 6.5 Protocol choices

- Replacing a cost implementation that failed the check changes the original evaluation environment; we report the effect of the replacement separately.
- Retraining with costs used the original hyperparameters without re-tuning, which may disadvantage the retrained conditions.
- The equal-weight baseline is a demanding comparator in rising markets, and several test windows overlap the market fall of 2020.
- Margins for equivalence were derived from one paper (FinRL) and are not transferred to other targets. They come from the paper's advantage over the index but were applied against equal weight, so the equivalences do not show that the paper's advantage over the index is excluded. The statistical analysis was not blind, and the calibration check found the tests conservative in most cases.
- The loss classification of A2C depends on the official tutorial's stochastic prediction; with deterministic prediction it is indeterminate (Section Z.3).
- Where the released code and the paper differ (for example, the turbulence index computed from price levels rather than returns in the ensemble strategy, or WaveCorr hyperparameters that differ from the paper's appendix, with no public commit matching the paper in all respects), we followed the code and report the difference.

## 6.6 Exploratory findings

The diagnostics in Sections Z.3, Z.5 and Z.6 were motivated by earlier results and should be read as descriptions of particular code under particular settings. The buy-and-hold behaviour of Markowitz Meets Bellman was not observed in two other share-based environments, and we did not examine its cause or generality. The authors' later turbulence rule for the ensemble strategy was published after the end of the test period. Reference values for FRONTIER were read from a figure. Some released repositories omit components that the papers propose (for example, knowledge distillation in Markowitz Meets Bellman), so those components were not evaluated.

## 6.7 Contact with authors

We contacted the authors of DeepAries and PRUDEX-Compass (AlphaMix+), and of one further paper in our main sample (MASA), by e-mail with questions about settings not stated in the papers [check: dates sent]. No reply had been received by [check: date]. The verdicts therefore do not incorporate author input.
