# 저자 문의 메일 초안 (미발송 — 사용자 확인 후 발송)

- 받는 사람: 각 논문의 교신저자. arXiv PDF 1쪽에서 주소를 확인한다.
- 발송하면 날짜와 응답을 이 파일과 v3 3장 규칙에 따라 기록한다.
- 결과 수치는 보내지 않는다. 설정만 묻는다. 결과 판정은 이미 사전 기준으로 고정돼 있다.
- (2026-11-02 추가) 코드 감사에서 확인한 비용 처리는 "제가 잘못 읽었는지" 묻는 형태로 넣는다. 재현 성과 수치는 계속 보내지 않는다.
- FinRL은 보내지 않는다. O1에서 재현됐고, StockPortfolioEnv는 문서에 무비용이라고 적혀 있다.
- EarnMore는 아직 재현 대상이 아니라서 보내지 않는다. 파일럿 뒤에 결정한다.
- 보내는 사람 이름·소속(Hanyang University)·주소는 발송 전에 사용자가 확인한다.

---

## 1. DeepAries (Kim et al., CIKM 2025, arXiv 2510.14985; dmis-lab/DeepAries)

**Subject:** Question on training/evaluation settings for DeepAries (CIKM 2025) results

Dear Dr. [교신저자],

I am an undergraduate student at Hanyang University working on a graduation thesis that re-runs published RL portfolio methods with their official code. Thank you for releasing the DeepAries code (dmis-lab/DeepAries).

I ran the official repository (commit 634f559) with the default arguments on the DJ30 split in the demo, and I would like to make sure that my setup matches the one behind the reported results (Table 2, CAGR 7.90%, MDD 13.67%). Could you let me know:

1. The number of training epochs and the learning-rate schedule used for the reported results. The README shows both `--train_epochs 1` (quick training) and `--train_epochs 10`.
2. The evaluation period and annualization used for CAGR. In particular, which start/end dates and which day-count (calendar days vs. 252 trading days) were used, including for the ^DJI benchmark (CAGR 6.15%).
3. How the reported run was selected among seeds (e.g., lowest validation loss), and whether the validation loss is the per-step sum as computed in `vali()`.
4. The hardware and library versions (PyTorch, NumPy) used.
5. Transaction-cost accounting. Section 3 of the paper charges cost against the drifted weights of the previous allocation, μ = 1 − c Σ|w(T_m) − w′(T_m)|. In `TradingEnvironment.step` (default `complex_fee=False`), my reading is that the cost is computed from the target two steps earlier (`[-3]` in the weight memory), so that (i) when the portfolio alternates between two disjoint sets of assets, the charged cost is about 2% of c·Σ|Δw|, and (ii) the cost of the first purchase from cash is charged one step later. Is this the intended accounting, or am I misreading the code? I may well be missing something, and I would like to describe it correctly.

Any pointer would help me report your method accurately. Thank you very much for your time.

Best regards,
Seungbin Kwon
Hanyang University

---

## 2. AlphaMix+ (PRUDEX-Compass, Sun et al., TMLR 2023, arXiv 2302.00586; TradeMaster-NTU/PRUDEX-Compass)

**Subject:** Question on result selection for AlphaMix+ in PRUDEX-Compass (TMLR 2023)

Dear Dr. [교신저자],

I am an undergraduate student at Hanyang University working on a graduation thesis that re-runs published RL portfolio methods with their official code. Thank you for releasing PRUDEX-Compass.

I ran AlphaMix+ for portfolio management (`AlphaMix+/PM`, commit 2b62831) on the dj30 splits (test 2019/2020/2021) with 5 seeds and 10 epochs, and I would like to confirm a few details behind the reported US total returns (20.7 / 12.7 / 25.1%):

1. Which epoch's test result was reported: the final epoch, or the epoch with the best validation return? In the code, each epoch's test evaluation runs before that epoch's training.
2. Whether the "market average" baseline (footnote 3) rebalances to equal weights every day or buys equal amounts once and holds.
3. The training variant used for dj30, e.g. `num_trains_per_train_loop`, `num_expl_steps_per_train_loop`, and `min_num_steps_before_training`. The script's `__main__` has commented-out dj_30 values.
4. The number of assets in the US pool (the paper lists 29). In my download, WBA was unavailable and DOW was dropped, leaving 28.
5. Transaction costs. The config sets `transaction_cost_pct = 0.001`, but in `rl_env/portfolio_management.py` (`TrainEnv`) this value is read in `__init__` and, as far as I can see, not used in `step()`, so the reported returns would be before costs. Were the reported results computed without transaction costs, or is the cost applied elsewhere?

Thank you very much for your time.

Best regards,
Seungbin Kwon
Hanyang University

---

## 3. MASA (Li, Tam & Yeung, AAMAS 2024, arXiv 2402.00515; SteamerLee/MASA)

> 발송 전 확인: 저자·학회·arXiv 번호는 기억에 의존한 것이다. 논문 PDF 1쪽에서 다시 확인한다. MASA는 재현 대상이 아니라 코드 감사 대상이므로 설정 질문은 하지 않고 비용 처리만 묻는다.

**Subject:** Question on transaction-cost handling in the MASA reward

Dear Dr. [교신저자],

I am an undergraduate student at Hanyang University working on a graduation thesis that examines how public RL portfolio implementations account for transaction costs. Thank you for releasing the MASA code (SteamerLee/MASA).

While reading the code (commit d97ef0e), I noticed the following and would like to check my understanding:

1. In `utils/tradeEnv.py`, the cost c·Σ|Δw| (c = 0.0003 in `config.py`) is deducted from capital when the new weights are set (around line 203), and it is written back into the previous step's entries of `asset_lst` and `profit_lst` (lines 204–205).
2. The daily return used for the reward, `poDayReturn_withcost` (around line 249), is computed with the post-cost capital as the denominator. In my run of the environment, the reward was unchanged when c was varied, while the portfolio value curve did change.

So, as far as I can tell, transaction costs enter the evaluated portfolio value but not the RL training reward. Is this the intended design (for example, costs handled by another component), or am I misreading the code?

Thank you very much for your time.

Best regards,
Seungbin Kwon
Hanyang University
