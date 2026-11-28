# Chapter 3. Forecasting and RL allocation on equities

> Working note (remove before submission). Sources: `methodology_report.md` (Korean; KOSPI pipeline, backbone comparisons, frequency features, clustering), `backbone_results.csv`, `backbone_results_extended.csv`, `preprocess_sequences.ipynb` (features, splits), `hybrid_model_colab.ipynb`, `freq_features_colab.ipynb`, `dtw_clustering_colab.ipynb`, `kospi_rerun_colab.ipynb`, `kospi_hrl_generalization_colab.ipynb`, `us_equity_*_colab.ipynb`, `paper/DRAFT.md` Sections 1.1, 3.1, 7.1–7.3 (read only), `notes/PROGRESS_SUMMARY_2026-11-01.md` Section 2. Every result in this chapter predates the pre-registration rules and is exploratory. Sections 3.4–3.6 were carried out after the final design of Chapter 4 had been reached and are reported here because they use equity data. [check: verify and add Kim et al. 2022 (RevIN), Ansari et al. 2024 (Chronos), Wu et al. 2020 (MTGNN), Liu et al. 2024 (iTransformer), Nie et al. 2023 (PatchTST), Fan and Shen 2024 (StockMixer), Hu et al. 2022 (LoRA), Gu and Dao 2023 (Mamba), Ke et al. 2017 (LightGBM), Cuturi and Blondel 2017 (soft-DTW), Tavenard et al. 2020 (tslearn), Jiang et al. 2017 (EIIE); only Schulman et al. 2017 is in the verified list. Chapter numbers follow the chronological outline and will be reconciled with THESIS_EN_DRAFT.md at assembly.]

---

**Summary.** The project began with a different question: can deep time-series models forecast Korean stock returns well enough to drive a portfolio? Across eight forecasting backbones, directional accuracy on the held-out test sequences lay between 0.496 and 0.515, around the share of up-moves (0.505). The forecasting signal was weak at best. An encoder built from these backbones then served as the state of a PPO agent allocating among five clusters of stocks. The first result, +0.28% against +34.33% for equal weight over two test years, was unreliable: the same code with a different encoder gave +137.22%, and inspection of the pipeline revealed four defects, including overlaps between the periods used to build the clusters and the encoder and the test period. After these and the cost accounting were corrected, the agent beat equal weight in nine of ten runs, but a static portfolio holding its average training-period weights performed almost identically: it had learned a fixed tilt, not a timing rule. A hierarchical variant chosen on validation failed in the test period. On U.S. large-capitalization stocks, single runs found a raw-price PPO agent tied with equal weight, an embedding-based agent behind it, and a hierarchical variant close to it. None of these equity experiments found an RL allocation that beat equal weight through decisions made period by period.

---

## 3.1 Data

The Korean universe consists of stocks listed on the KOSPI market at the time of data collection. Of 837 stocks, those with fewer than 500 trading days or more than 10% missing volume over 2020–2026 were removed, leaving 781. Because the universe consists of currently listed stocks and the filters use the whole sample, delisted stocks are excluded and the universe is subject to survivorship bias, which favors equal weight and any static tilt as much as it favors a learned policy. Daily data from January 2020 to May 2026 (about 1.18 million stock-days) provide twenty input features per stock: open, high, low, close and volume, and fifteen technical indicators (moving averages, MACD and its signal and histogram, RSI, Bollinger bands and width, volume ratio, one-day return, 20-day volatility and ATR). Each input is a 60-day window normalized per window with reversible instance normalization (RevIN; Kim et al., 2022) and split into twelve five-day patches; the forecasting target is the direction of the five-day forward return.

For the forecasting experiments, the sequences were split by date into training (to June 2024), validation (second half of 2024) and test (January 2025 to May 2026). These splits differ from the RL periods of Section 3.3, and the forecasting test period overlaps the RL test period (2024–2025). The share of up-moves is 0.505 in the forecasting test split and 0.450 in validation, so directional accuracy has to be read against the share of the majority direction in the same split.

## 3.2 Forecasting

**Frequency-domain features.** A gradient-boosting classifier (LightGBM; Ke et al., 2017) on 40 summary statistics of the features reached an area under the ROC curve of 0.512 on the validation split, which also served for early stopping. Adding sixteen discrete-wavelet features raised it to 0.523, and adding thirteen Fourier features as well to 0.525; Fourier features alone lowered it to 0.509. These are single-split results without intervals. One possible reading is that wavelet features help because they retain when a frequency component occurs, but differences of about 0.01 in this range do not establish it; the level of predictability stays close to chance.

**Clustering.** To give an allocation policy a small action space, stocks were grouped by the shape of their price paths rather than by industry. K-means with the soft dynamic-time-warping distance (Cuturi and Blondel, 2017; implemented in tslearn, Tavenard et al., 2020) was applied to standardized monthly cumulative returns of the 757 stocks with at least 700 trading days in 2022–2024. Over $K$ from 5 to 20, the Euclidean silhouette score was highest at $K = 5$, the smallest value tried; one cluster held 299 of the 757 stocks. The clustering window overlapped the later RL test period, one of the defects of Section 3.4.

**Forecasting backbones.** Eight backbones were compared: StockMixer (Fan and Shen, 2024), PatchTST (Nie et al., 2023), iTransformer (Liu et al., 2024), Chronos without further training (Ansari et al., 2024), Chronos fine-tuned with low-rank adaptation (LoRA; Hu et al., 2022), MTGNN (Wu et al., 2020), a bidirectional GRU in place of Mamba (Gu and Dao, 2023), which could not be installed in the available environment, and a hybrid of Chronos and MTGNN. All were evaluated on the same test sequences; the learned models were trained on subsamples of 80,000 to 100,000 training sequences.

**Table 3.1.** Forecasting backbones on the KOSPI test sequences (January 2025 to May 2026; single runs).

| Backbone | Directional accuracy | Spearman correlation |
|---|---|---|
| MTGNN | 0.5145 | 0.0356 |
| Chronos (no further training) | 0.5096 | 0.0192 |
| iTransformer | 0.5057 | 0.0056 |
| Chronos + MTGNN (hybrid) | 0.5056 | 0.0259 |
| Chronos with LoRA | 0.5038 | −0.0079 |
| StockMixer | 0.5033 | 0.0072 |
| Bidirectional GRU | 0.4987 | 0.0001 |
| PatchTST | 0.4960 | 0.0096 |
| Share of up-moves | 0.505 | — |

All directional accuracies lie within about one percentage point of the share of up-moves. Each backbone was run once, so the ranking cannot be distinguished from run-to-run variation. Fine-tuning Chronos with LoRA lowered its rank correlation below that of the untrained model. The backbones were compared on the test split, and the encoder chosen from them was later used in an RL test period that overlaps it, so the choice of encoder used information from the RL test period.

**The encoder.** The encoder concatenates a frozen Chronos encoder, applied to the closing-price series, with an MTGNN-style graph encoder over the twenty features of the same stock, fused into a 64-dimensional embedding. The graph connects features of one stock, not different stocks. It was chosen to combine the two strongest backbones of Table 3.1, although its own accuracy (0.506) was below that of MTGNN alone. An earlier hybrid of Chronos and iTransformer (test accuracy 0.508) was also built and is used in Section 3.4. The same Chronos–MTGNN architecture was later trained separately on cryptocurrency data for Chapter 4.

## 3.3 From forecasting to allocation

The first plan was to add news text to the price series. Sufficient Korean news data aligned to 781 stocks over several years could not be obtained, so the project turned to reinforcement learning: rather than forecasting returns and building a portfolio from the forecasts, a policy would learn to allocate directly from the encoder's representation. The state is the mean embedding of each of the five clusters (5 × 64) together with the current cluster weights, 325 dimensions in all; the action is a softmax over the five clusters; the reward is the daily portfolio return less a proportional cost of 0.1% of turnover. The policy is trained with PPO (Schulman et al., 2017) on 2021–2023 and tested on 2024–2025.

## 3.4 The first result and its correction

The first agent returned +0.28% over the two test years (Sharpe 0.100, maximum drawdown −27.21%), against +34.33% for equal weight (Sharpe 1.043). An initial interpretation attributed this to the size of the state relative to the training data and to the noise of a daily-return reward.

The result was not reliable. With the same code and seed, replacing only the encoder with the Chronos–iTransformer hybrid gave +137.22%. Inspection of the pipeline revealed four defects: the embeddings were extracted without the RevIN normalization used in training; the features were fed in a different order from training; the clustering window (2022–2024) overlapped the test period; and the encoders had been trained on data up to June 2024, also inside the test period. The four defects were not removed one at a time, so their separate contributions are unknown. With all four corrected (clusters built on 2021–2023, both encoders retrained on data to June 2023, normalization applied, feature order matched) and the cost measured against drifted holdings as in Chapter 4, the agent was retrained with each of the two encoders and five seeds.

**Table 3.2.** Corrected single-policy PPO on KOSPI clusters, test period 2024–2025.

| | Return | Sharpe | Runs above equal weight (Sharpe) |
|---|---|---|---|
| Chronos + iTransformer encoder (5 seeds) | +44.2% ± 9.3% | 1.09 ± 0.22 | 4 of 5 |
| Chronos + MTGNN encoder (5 seeds) | +41.7% ± 2.6% | 1.07 ± 0.09 | 5 of 5 |
| Equal weight (corrected accounting) | +31.0% | 0.943 | — |

The corrected agent beat equal weight in nine of ten runs by Sharpe ratio and in all ten by return, although seven of ten had a deeper maximum drawdown than equal weight (−16.1%). The source of the advantage, checked for one seed per encoder, was not timing. Holding the agent's average training-period cluster weights fixed throughout the test period gave almost the same Sharpe ratio (1.108 against 1.134 for the agent with the Chronos–iTransformer encoder, 1.099 against 1.168 with Chronos–MTGNN), and holding the test-period average weights closed the gap to within 0.01. The agent with the Chronos–MTGNN encoder kept about 96% of the portfolio in one cluster throughout the test period, with almost no variation over time; holding that cluster alone, a choice made with knowledge of the test period, gave a Sharpe ratio of 1.185. On validation, the directional accuracy of both encoders (0.495 and 0.515) was below the share of the majority direction in that period (0.533). In the two runs checked, the corrected agent therefore beat equal weight through a tilt toward one group of stocks fixed during training, which an investor could hold without RL, and the embeddings appear to carry almost no timing information.

## 3.5 A hierarchical variant on KOSPI

Before the corrections of Section 3.4, the final recipe of Chapter 4 without its sparse action, a pool of four agents trained under different risk preferences $\beta$ with execution-time damping and no router, was ported to the five-cluster environment. The agents were trained on 2021–2022, 2023 served as validation, and the test period was 2024–2025. This experiment used the uncorrected embeddings and clusters and was re-evaluated, but not retrained, after the accounting correction.

The agents were partly distinct: $\beta = 30$ differed from the others (correlations of weight paths 0.22–0.51), while $\beta = \pm 90$ behaved almost identically (0.955); with two years of daily data, the regime segmentation produced only seven chunks for training. Damping helped only one agent in validation, possibly because daily decisions leave little high-frequency trading for damping to remove; this was not tested. The candidate chosen on validation Sharpe ($\beta = 90$, $\alpha = 0.3$) beat equal weight in validation (1.477 against 1.302) and failed in the test period (0.137 against 1.038). Because the embeddings had the defects of Section 3.4, part of this failure may be due to them.

## 3.6 U.S. large-capitalization stocks

Three single-run checks were made on 44 large-capitalization U.S. stocks from ten sectors, chosen by hand among current S&P 500 members listed before 2015, so this universe too favors any long-only strategy that holds it. The agents rebalance daily with a cost of 0.1%, are trained on 2015–2022 for 100,000 steps, use 2023 for validation and are tested on 2024–2025, with the corrected accounting.

- **Raw-price state.** A single PPO agent whose state is a 50-day window of close, high and low price ratios, processed by an EIIE-style convolutional feature extractor (Jiang et al., 2017), with a cash position, finished close to equal weight (+45.58%, Sharpe 1.482, against +45.00%, 1.454).
- **Embedding state.** A PPO agent whose state is instead built from Chronos embeddings, reduced to 64 dimensions by principal components fitted on all dates including the test period, had a lower test Sharpe ratio (1.251 against 1.458 for the equal weight computed in the same evaluation), and its average turnover rose from 1.22% to about 9.2–9.5% per step. The two agents differ in network and state, not only in the embeddings. With one run per arm, the change in Sharpe ratio may be partly run-to-run noise; the eightfold rise in turnover is large enough that noise is an unlikely explanation for it.
- **Hierarchical variant.** The pool-and-damping recipe of Section 3.5 on the raw-price state produced agents with highly similar weight paths (correlations 0.86–0.98), and damping did not help any agent in validation. The candidate chosen on validation ($\beta = -90$, no damping) had a test Sharpe ratio of 1.465, within 0.03 of equal weight (1.454) and of the single raw-price agent (1.482) in a single run. Its gap between validation and test Sharpe ratios was small (0.074), but it had no advantage to be consistent about: a small gap does not by itself indicate a good policy.

## 3.7 What carried forward

Three observations from the equity work recur in the rest of the thesis. First, the forecasting signal available to these models was close to zero, so any advantage of an RL allocation built on them had to come from somewhere other than prediction. Second, the one advantage that did appear, on KOSPI, was reproduced by a simple fixed allocation, a static cluster tilt; on U.S. stocks the agents finished close to or below equal weight. Third, results could be produced by defects in the pipeline and by overlaps between the periods used for building the model and the periods used for testing it, and these were found only by inspecting the pipeline after the fact. Chapter 4 moved to cryptocurrency, where intraday data and execution were available, and Chapter 5 shows that the same observations applied there.
