# 저자 문의 메일 초안 (미발송 — 사용자 확인 후 발송)

- 받는 사람: 각 논문의 교신저자. arXiv PDF 1쪽에서 주소를 확인한다.
- 발송하면 날짜와 응답을 이 파일과 v3 3장 규칙에 따라 기록한다.
- 결과 수치는 보내지 않는다. 설정만 묻는다. 결과 판정은 이미 사전 기준으로 고정돼 있다.

---

## 1. DeepAries (Kim et al., CIKM 2025, arXiv 2510.14985; dmis-lab/DeepAries)

**Subject:** Question on training/evaluation settings for DeepAries (CIKM 2025) results

Dear Dr. [교신저자],

I am an undergraduate student at Hankuk University of Foreign Studies working on a graduation thesis that re-runs published RL portfolio methods with their official code. Thank you for releasing the DeepAries code (dmis-lab/DeepAries).

I ran the official repository (commit 634f559) with the default arguments on the DJ30 split in the demo, and I would like to make sure that my setup matches the one behind the reported results (Table 2, CAGR 7.90%, MDD 13.67%). Could you let me know:

1. The number of training epochs and the learning-rate schedule used for the reported results. The README shows both `--train_epochs 1` (quick training) and `--train_epochs 10`.
2. The evaluation period and annualization used for CAGR. In particular, which start/end dates and which day-count (calendar days vs. 252 trading days) were used, including for the ^DJI benchmark (CAGR 6.15%).
3. How the reported run was selected among seeds (e.g., lowest validation loss), and whether the validation loss is the per-step sum as computed in `vali()`.
4. The hardware and library versions (PyTorch, NumPy) used.

Any pointer would help me report your method accurately. Thank you very much for your time.

Best regards,
Seungbin Kwon
Hankuk University of Foreign Studies

---

## 2. AlphaMix+ (PRUDEX-Compass, Sun et al., TMLR 2023, arXiv 2302.00586; TradeMaster-NTU/PRUDEX-Compass)

**Subject:** Question on result selection for AlphaMix+ in PRUDEX-Compass (TMLR 2023)

Dear Dr. [교신저자],

I am an undergraduate student at Hankuk University of Foreign Studies working on a graduation thesis that re-runs published RL portfolio methods with their official code. Thank you for releasing PRUDEX-Compass.

I ran AlphaMix+ for portfolio management (`AlphaMix+/PM`, commit 2b62831) on the dj30 splits (test 2019/2020/2021) with 5 seeds and 10 epochs, and I would like to confirm a few details behind the reported US total returns (20.7 / 12.7 / 25.1%):

1. Which epoch's test result was reported: the final epoch, or the epoch with the best validation return? In the code, each epoch's test evaluation runs before that epoch's training.
2. Whether the "market average" baseline (footnote 3) rebalances to equal weights every day or buys equal amounts once and holds.
3. The training variant used for dj30, e.g. `num_trains_per_train_loop`, `num_expl_steps_per_train_loop`, and `min_num_steps_before_training`. The script's `__main__` has commented-out dj_30 values.
4. The number of assets in the US pool (the paper lists 29). In my download, WBA was unavailable and DOW was dropped, leaving 28.

Thank you very much for your time.

Best regards,
Seungbin Kwon
Hankuk University of Foreign Studies
