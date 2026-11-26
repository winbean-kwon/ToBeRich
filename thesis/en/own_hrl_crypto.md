# Chapter 4. A hierarchical RL allocation system for cryptocurrency

> Working note (remove before submission). Sources: `paper/DRAFT.md` Sections 3–6 (read only), `paper/RETRAIN_1006.md`, `notes/PROGRESS_SUMMARY_2026-11-01.md` Section 3, `HANDOFF_2026-10-26.md` Section 3, `crypto/notebooks/crypto_hybrid_model_colab.ipynb` (encoder split). Performance figures are from retrained policies in the corrected environment; the few pre-correction figures are marked as such in the text. Cross-references follow the chronological outline (Chapter 3 equities, Chapter 5 checks of the author's own result, Chapters 6–7 reproduction and re-evaluation). [check: add EarnHFT, FreQuant, DeepClair, Chronos, MTGNN, PPO, DQN, double DQN to the verified reference list.]

---

**Summary.** This chapter describes the reinforcement-learning allocation system developed before the reproduction study, and the sequence of designs that led to it. A single-policy PPO agent over 44 cryptocurrency pairs lost most of its capital in the test period. Porting the hierarchical structure of EarnHFT (Qin et al., 2024), a pool of agents trained under different risk preferences and a router that selects among them, did not by itself fix this: the pre-cost signal was weak and was erased by the cost of rebalancing every 30 minutes. Two changes produced most of the later improvement: damping the policy's weight changes at execution time, and replacing the dense allocation over all assets with a top-10 selection and a separate exposure gate. The router contributed nothing; it collapsed to always choosing one agent. The configuration finally selected, one agent ($\beta=30$) without a router, earned +8.73% with a Sharpe ratio of 2.60 in the test period, against −0.81% and 0.26 for equal weight. These figures are development results from a single seed. All design choices in this chapter were made before the pre-registration rules of Chapters 5–7 were adopted, and several were made after seeing test-period results. Chapter 5 shows that the evaluation convention used here raised the result in these windows, that most seeds of the same configuration lost money in validation, and that the advantage did not hold in an unseen period.

---

## 4.1 Why the study moved to cryptocurrency

The Korean-equity experiments of Chapter 3 used daily bars. A study of intraday rebalancing and live execution in that market required historical minute bars and a brokerage interface that were not available in the computing environment used for this project. Binance provides both historical intraday bars and an execution API, so the allocation problem was moved to cryptocurrency spot pairs.

## 4.2 Data and state representation

**Universe and bars.** The universe consists of 44 USDT spot pairs on Binance, chosen from an initial set of 50 after excluding pairs with less than six months of history. Five-minute bars from January 2021 to mid-July 2026 were collected; the portfolio is rebalanced every 30 minutes (six bars). The pairs were chosen by their trading volume at the time of data collection, not at each historical date, which can introduce survivorship bias; Chapter 5 reports a check of this.

**Periods.** Unless stated otherwise, policies are trained on calendar year 2025 and tested on the first half of 2026 (9,319 rebalancing steps). The fourth quarter of 2025 (4,416 steps) serves as the validation period. In the main pool this quarter is also part of the training period; Chapter 5 reports a retraining that removes this overlap. The period from mid-July to late October 2026 was not used for any decision in this chapter and is used once, in Chapter 5, as an unseen period.

**State.** Each asset is represented by a 64-dimensional embedding produced by a fixed encoder that concatenates a frozen pretrained Chronos encoder (Ansari et al., 2024) applied to the closing-price series with a small graph encoder over the 20 input features of the same asset (open, high, low, close, volume and 15 technical indicators on the 5-minute grid), in the style of MTGNN (Wu et al., 2020), and fuses the two with a multilayer perceptron. The architecture is that of Chapter 3, trained separately on cryptocurrency data. The graph connects features of one asset, not different assets. The architecture was adopted after the comparison of forecasting backbones on Korean stocks in Chapter 3, where every backbone's directional accuracy was close to the share of up-moves and the hybrid's was below that of MTGNN alone, so it should be regarded as a representation with weak predictive content rather than as a forecaster. The encoder was trained on data up to June 2025 and its checkpoint chosen on July–December 2025; the test period is therefore unseen by the encoder, but the validation quarter was used in choosing it. Each embedding uses data up to and including the current step only. The encoder is held fixed in all experiments of this chapter, so differences between designs are not due to the encoder.

## 4.3 Environment

At step $t$ the agent observes $s_t = [e_{1,t},\dots,e_{N,t},\tilde w_{t-1}]$, where $e_{i,t}$ is the embedding of asset $i$ and $\tilde w_{t-1}$ is the portfolio actually held: the previous target weights after they have drifted with the previous step's returns $\rho_{t-1}$,

$$\tilde w_{t-1,i} = \frac{w_{t-1,i}(1+\rho_{t-1,i})}{1 + w_{t-1}^\top \rho_{t-1}}.$$

The policy's action is mapped to target weights $w_t$, and the environment charges a proportional cost on the realized turnover, $c_t = \tau \lVert w_t - \tilde w_{t-1}\rVert_1$ with $\tau = 0.001$ (the standard taker fee on Binance). The reward is the net portfolio return $r_t = w_t^\top \rho_t - c_t$. Because turnover is measured against drifted holdings, a strategy with a constant target, such as equal weight, pays the cost of rebalancing back to its target, as in the formulation of Jiang et al. (2017). Assets without data at a step (before listing or after delisting) receive zero weight. The cost model is linear and includes neither slippage nor market impact.

The first implementation of this environment measured turnover against the previous target rather than the drifted holding, so that rebalancing was free, and allowed assets without data to be held at zero return. All policies in this chapter were retrained after this was corrected. The correction changed which agent appeared best in validation (Section 4.8), so accounting errors in the reward can alter conclusions drawn from model comparisons, not only the reported levels.

**Training.** All agents are trained with PPO (Stable-Baselines3) using one fixed set of hyperparameters (learning rate $3\times10^{-4}$, 1,024 steps per update, batch size 64, ten epochs, $\gamma=0.99$, GAE $\lambda=0.95$, clip range 0.2, entropy coefficient 0.01) and 100,000 environment steps per agent. Routers are DQNs (learning rate $10^{-3}$, replay buffer 20,000, $\gamma=0.95$, $\epsilon$ annealed from 0.3 to 0.05) trained for 20,000 steps. These budgets are the same for every design, so that the comparisons below are not confounded by unequal compute. Each design was trained with a single seed; the seed-to-seed variation of the final configuration is reported in Chapter 5.

**Benchmark.** Equal weight over the tradable assets, rebalanced to its target every step with the same cost, returns −0.81% in the test period (Sharpe 0.255, maximum drawdown −40.46%) and −32.56% in the validation period (Sharpe −0.459).

**Evaluation convention.** Every evaluation in this chapter starts the portfolio fully invested in equal weight on the first day. For policies that adjust their weights slowly (Section 4.5), this initial holding persists for some time and affects the result. Chapter 5 shows that, for the final configuration, starting instead from the policy's own holdings after a two-week warm-up lowers the test return from +8.73% to +2.86% (Sharpe 2.60 to 1.03) and the validation return from +2.98% to −0.08%. Across many shorter windows the start-state effect averages close to zero, so it adds variance rather than a consistent upward bias, but in the two windows used for selection and testing here it raised the results. The figures in this chapter, including the validation figures used to choose an agent in Section 4.8, should be read with that in mind.

## 4.4 A single policy and the motivation for a hierarchy

The first design was a single PPO policy whose action is a softmax over the 44 assets. In the test period it lost 79.68% (Sharpe −4.44, maximum drawdown −82.48%), against −0.81% for equal weight. (A later single-run check on U.S. large-capitalization stocks, reported in Chapter 3, is consistent with the state design playing a part: replacing a raw-price state with pretrained embeddings raised turnover roughly eightfold and lowered the test Sharpe ratio from 1.48 to 1.25, against 1.46 for equal weight.)

EarnHFT (Qin et al., 2024) reports that its hierarchical method outperforms single-policy PPO and DQN agents on four cryptocurrency datasets, in total return on all four and in Sharpe ratio on three. Its authors attribute the failure of policy-based agents to convergence to a "dummy" policy and that of value-based agents to a lack of robustness across market trends. EarnHFT first uses a dynamic-programming teacher, which provides optimal action values under different risk preferences $\beta$, to train many agents biased toward those preferences; a second stage distils these into a small pool with distinct behavior; in a third stage, a router selects among them according to the market state. EarnHFT was designed for a single asset, discrete positions and second-level decisions. We ported its second and third stages to a continuous allocation over 44 assets with 30-minute decisions; the router was trained on regime chunks and, at test time, chose an agent once per chunk-length interval. The first stage, which presupposes a small discrete action space, was not ported. The port therefore changes the number of assets, the form of the action, the decision frequency and the state together, and the results below describe the ported structure as a whole.

## 4.5 The ported hierarchy and the cost of trading

**Direct port (v1).** The 2025 equal-weight price path was segmented into 123 chunks of about three days, each labeled with one of five regimes (bear, pullback, sideways, rally, bull) from smoothed local extrema. Four agents were trained with $\beta\in\{-90,-30,30,90\}$. Without the teacher, $\beta$ entered only through the sampling priority of training chunks, favoring regimes in which a preference of that sign would have done well; the PPO objective was the same for all four. A DQN router chose an agent at each chunk boundary from market features.

The system lost 32.88% in the test period (Sharpe −1.07, maximum drawdown −50.68%). Without costs it would have gained 3.54%, against 2.71% for equal weight without costs. Average turnover was 4.65% of portfolio value per step, which compounded into a cost of 35.17% over the period. The hierarchy produced, at best, a weak signal, and 30-minute rebalancing cost far more than that signal earned.

**Damping at execution time.** The direct remedy is to trade less. An exponential filter applied only when the trained policy is executed,

$$w_t = (1-\alpha)\,w_{t-1} + \alpha\,\mathrm{softmax}(a_t),$$

moves the portfolio only a fraction $\alpha$ of the way toward the policy's target at each step. As $\alpha$ decreased from 1 to 0.01, the net test return of the same v1 policy rose monotonically from −32.88% to +3.76% (Sharpe 0.403), while the cost-free return stayed between +1.53% and +4.97%. This is consistent with damping mainly protecting an existing weak signal from costs. It did not change the risk profile: the maximum drawdown stayed at −39.25%, close to equal weight. The value $\alpha=0.01$ was chosen on the test period in this experiment and is not an out-of-sample result; in later designs it was chosen on the validation period, which selected the same value.

At the same stage, eight further execution-time overlays (a cash gate, averaging over the pool, top-10 concentration and volatility targeting, in combinations) were tried on the v1 pool. The best reached +28.43% net in the test period. These overlays were compared on test results, so the figure carries selection bias, and none was carried forward.

**Damping during training (v2).** If damping helps at execution, training the policy inside a damped environment might teach it to trade less from the start. With $\alpha = 0.03$ inside the training environment, the net test return was −8.02% (Sharpe 0.006), worse than the −0.62% of the same $\alpha$ applied at execution only, and the cost-free return fell from +3.54% to −2.84%. A plausible explanation is that damping inside the environment weakens the link between the action the policy emits and the reward that follows, which makes credit assignment harder; this was not measured. In the remaining designs, agents were trained without damping and damping was applied only at execution.

## 4.6 A closer reimplementation (v3)

v1 differs from EarnHFT in more than the missing teacher: it has no cash position, and its agent selection was not separated from the test period. v3 added a 45th action component for cash and split 2025 into nine months of training and three months of validation. Twenty candidates (four $\beta$ values by five checkpoints) were scored per regime on validation, the best candidate was kept for each regime, and the router and $\alpha$ were also chosen on validation, as in the original procedure.

v3 returned −5.23% net in the test period (Sharpe 0.102; cost-free −2.89%), below equal weight. The selected agents differed by regime, but in the same design trained in the uncorrected environment the cash weight stayed at $1/45$, its value at initialization, for almost the entire test period, and validation scores of the twenty candidates were within one percentage point of each other: agents trained under four different preferences behaved almost identically. One reading is that a preference expressed only through which data are sampled does not move a 45-dimensional continuous policy away from a near-uniform allocation, and that EarnHFT's teacher is what supplies preference-specific behavior. A minimal test of this reading added a reward term pushing the cash weight in a direction set by the sign of $\beta$. The rank correlation between $\beta$ and the mean cash weight was −0.40 without the term and −0.80 and −0.60 with two strengths of it; with four $\beta$ values this statistic moves in steps of 0.2, and even at the stronger setting the mean cash weights remained between 0.9% and 4.3%. The test does not support the reading, which remains a hypothesis. A separate single-asset branch of the project, which included a teacher and discrete positions, showed position differences across $\beta$ that were neither large nor monotone in $\beta$, and is at most weak qualitative evidence.

## 4.7 A sparse action with an exposure gate (v4) and the router collapse

**Design.** Instead of reintroducing a teacher, v4 changed the form of the action. The policy emits 44 asset scores and one gate value. The ten assets with the highest scores are kept and weighted by a softmax over their scores, following the top-$K$ selection of FreQuant (Jeon et al., 2024); the resulting portfolio is scaled by $\sigma(\text{gate}) \in (0,1)$, following the exposure gate of DeepClair (Choi et al., 2024), and the remainder is held in cash. The regime chunks, sampling priorities and training budgets were those of v1, so the form of the action was the only change.

**Diversity.** The agents of v4 behaved differently from one another. Run alone over the test period, their mean exposures were 0.256 ($\beta=-90$), 0.265 ($\beta=-30$), 0.093 ($\beta=30$) and 0.446 ($\beta=90$), and their top-10 holdings rotated through 20 to 31 of the 44 assets. Exposure was not monotone in $\beta$; the most conservative agent was $\beta=30$.

**Performance.** Without damping, the v4 router and pool had essentially no cost-free return (−0.81%) and lost 24.79% net. With execution-time damping ($\alpha=0.01$, chosen on the test period) it returned +5.97% (Sharpe 1.231, maximum drawdown −6.50%), better than damped v1 in both return and drawdown. In v4, unlike v1, damping also raised the cost-free return, from −0.81% at $\alpha=1$ to +6.65% at $\alpha=0.01$: the filter changed which positions were held, not only how much trading cost was paid. Why it had this effect was not established. Turnover remained positive at every step, so the policy was not static, but returns were concentrated in the first half of the test period (+5.36% against +0.57% in the second half).

**Router collapse.** The router observed, among other features, the fraction of the current chunk that had elapsed, a quantity with no counterpart in live execution, where it had been set to 0.5. Retraining only the router with this input fixed at 0.5 during training (the "matched" router) appeared to improve results to +8.73% (Sharpe 2.602, maximum drawdown −4.38%). Running the $\beta=30$ agent alone, with no router, gave exactly the same figures. The router had ignored its inputs and chosen $\beta=30$ for every chunk of the validation and test periods. A router retrained with double DQN collapsed in the same way, onto the worst agent ($\beta=90$, −17.17% in the test period). In a later ablation that varied only the number of assets from 1 to 44 (three seeds each), the router used a single agent in 13 of 15 test runs, including with one asset, so collapse is not caused by the move to many assets. Collapse also occurred at decision intervals of 4 hours and 1 day. It did not occur with a pool of factor-based agents and a router given informative features, nor in a controlled experiment designed to diagnose it in advance (0 of 32 runs), so its cause was not identified.

## 4.8 Choosing an agent

With the router contributing nothing, the remaining question was which agent to run. Table 4.1 shows the four agents alone, with $\alpha=0.01$, in the validation and test periods.

**Table 4.1.** Agents of the v4 pool run alone ($\alpha = 0.01$).

| $\beta$ | Validation Sharpe | Test Sharpe | Validation return | Test return | Test max. drawdown |
|---|---|---|---|---|---|
| −90 | −0.111 | 0.743 | −2.70% | +5.51% | −10.80% |
| −30 | −1.155 | 0.448 | −7.39% | +3.09% | −14.06% |
| 30 | 0.653 | 2.602 | +2.98% | +8.73% | −4.38% |
| 90 | −0.971 | −1.065 | −13.41% | −17.17% | −30.41% |
| Equal weight | −0.459 | 0.255 | −32.56% | −0.81% | −40.46% |

The selection rule was the highest validation Sharpe ratio. The rule itself uses no test information, but the candidates it chooses among were reached through design choices that did (v4, $K=10$, and $\alpha$ at earlier stages). It selects $\beta=30$, the only agent with a positive Sharpe ratio in both periods; choosing $\alpha$ on validation gives the same 0.01. The final configuration is therefore the $\beta=30$ agent alone with execution-time damping, which is what the collapsed router was doing.

Two features of this selection limit what it shows. First, before the environment correction of Section 4.3, the same comparison pointed the other way: $\beta=30$ had a validation Sharpe of 0.189 and a test Sharpe of 3.033, $\beta=-30$ had the highest validation Sharpe (0.914), and the gap between validation and test was read as overfitting of $\beta=30$. After retraining, $\beta=-30$ loses 7.39% in validation. Which agent looked overfit was determined by an accounting error in the reward. Second, the gap between validation and test Sharpe is largest for the selected agent (1.950; 0.094 to 1.603 for the others). The validation quarter was a crash (equal weight −32.56%) and the test half-year was nearly flat, so most agents improve from one to the other, and the size of the gap reflects the difference between the two periods at least as much as overfitting. The smallest gap belongs to $\beta=90$, which loses in both. The selection also rests on one validation window and one seed, and that seed is favorable: among sixteen seeds of the same configuration (Chapter 5) it has the second-highest test Sharpe ratio, and thirteen of the sixteen have a negative validation Sharpe ratio. The block-bootstrap 95% interval of its test Sharpe ratio, [−0.95, 5.43], includes zero.

## 4.9 Summary of the designs

Table 4.2 collects the designs on the same test period.

**Table 4.2.** Designs in the test period (first half of 2026, 9,319 steps). Equal weight is rebalanced every step with costs.

| # | Design | Router | Damping | Net return | Sharpe | Max. drawdown |
|---|---|---|---|---|---|---|
| 0 | Equal weight | — | — | −0.81% | 0.255 | −40.46% |
| 1 | Single PPO | — | — | −79.68% | −4.440 | −82.48% |
| 2 | v1: hierarchy, sampling-priority preferences | DQN | — | −32.88% | −1.071 | −50.68% |
| 3 | v1 with execution-time damping | DQN | $\alpha=0.01$ᵃ | +3.76% | 0.403 | −39.25% |
| 4 | v2: damping during training | DQN | in training | −8.02% | 0.006 | −40.85% |
| 5 | v3: cash, validation-based selection | DQN | $\alpha=0.01$ᵇ | −5.23% | 0.102 | −39.51% |
| 6 | v4: top-10 and exposure gate, no damping | DQN | — | −24.79% | −6.524 | −25.21% |
| 7 | v4 with damping | DQN | $\alpha=0.01$ᵃ | +5.97% | 1.231 | −6.50% |
| 8 | v4, matched router | DQN, collapsed | $\alpha=0.01$ᵇ | +8.73% | 2.602 | −4.38% |
| 9 | $\beta=30$ alone (final) | none | $\alpha=0.01$ᵇ | +8.73% | 2.602 | −4.38% |

ᵃ Chosen on the test period. ᵇ Chosen on the validation period.

Along this sequence, the large gains in net return coincided with execution-time damping, which reduced trading cost (rows 2→3 and 6→7), and the fall in drawdown coincided with the exposure gate of the sparse action (rows 3→7). None came from the router; rows 8 and 9 are identical. All rows are single-seed results. The final configuration's low drawdown went with low exposure: in the test period the $\beta=30$ agent held on average about a tenth of the portfolio in risky assets (about a fifth in validation), and equal weight held along the same exposure path reaches a test Sharpe ratio of 2.00 and a maximum drawdown of −4.60% (Chapter 5). Much of the result is therefore exposure timing rather than asset selection.

On the figures of this chapter, the system appeared to beat equal weight by a wide margin on a risk-adjusted basis. A policy from this line of work was also run on a small live account; the account was too small to follow the policy's weights, and the live run is reported in Chapter 5 as an operational record, not as evidence about performance. Three questions remained open: whether the result depended on the seed and on the overlap of validation with training, whether it depended on how the evaluation was set up, and whether it would hold in a period not used for any decision. Chapter 5 addresses them.
