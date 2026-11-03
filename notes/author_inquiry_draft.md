# 저자 문의 메일 초안 (미발송 — 사용자 확인 후 발송)

- 받는 사람: 각 논문의 교신저자. arXiv PDF 1쪽에서 주소와 직함(Prof./Dr.)을 확인해 `[이름]` 자리에 성으로 넣는다.
- 발송하면 날짜와 응답을 이 파일과 v3 3장 규칙에 따라 기록한다.
- 결과 수치는 보내지 않는다. 설정만 묻는다. 결과 판정은 이미 사전 기준으로 고정돼 있다.
- (2026-11-02 추가) 코드 감사에서 확인한 비용 처리는 "제가 잘못 읽었는지" 묻는 형태로 넣는다. 재현 성과 수치는 계속 보내지 않는다.
- (2026-11-02 문체 수정)
  - 질문 목록이 심문처럼 읽히지 않도록 질문을 묶고 수를 줄였다.
  - "일부만 답해도 된다"를 명시했다.
  - 저자의 결과를 단정하는 문장(예: "보고 수익은 비용 전일 것")을 뺐다.
  - 확인에 쓴 스크립트를 공유하겠다고 제안했다.
- FinRL은 보내지 않는다. O1에서 재현됐고, StockPortfolioEnv는 문서에 무비용이라고 적혀 있다.
- EarnMore는 아직 재현 대상이 아니라서 보내지 않는다. 파일럿 뒤에 결정한다.
- 보내는 사람 이름·소속(Hanyang University)·주소는 발송 전에 사용자가 확인한다.

---

## 1. DeepAries (Kim et al., CIKM 2025, arXiv 2510.14985; dmis-lab/DeepAries)

**Subject:** A few questions about the DeepAries experimental setup

Dear Prof. [이름],

My name is Seungbin Kwon, and I am an undergraduate student at Hanyang University. For my graduation thesis, I am re-running several published RL portfolio methods using their official code, and DeepAries is one of them. Thank you for making the code publicly available; it is clearly written and was easy to run.

I want to make sure I describe your method accurately, and there are a few points I could not determine from the paper and the repository (commit 634f559). I would be grateful for any guidance, and a short answer to even some of them would be very helpful.

1. **Training and run selection.** How many training epochs were used for the reported results? The README mentions both `--train_epochs 1` and `--train_epochs 10`. Also, how was the reported run chosen among seeds, for example by the lowest validation loss?
2. **Evaluation period.** Which start and end dates, and which day-count convention (calendar days or 252 trading days), were used when annualizing CAGR for DeepAries and for the ^DJI benchmark?
3. **Transaction costs.** I am not sure I am reading `TradingEnvironment.step` correctly (default `complex_fee=False`). It looks to me as if the cost is computed against the target weights from two steps earlier, rather than against the drifted weights of the previous allocation as described in Section 3. If so, the charged cost would be smaller when the portfolio changes often. I may well be missing something, and I would much rather check with you than describe it incorrectly. I am happy to share the short script I used to check this if it would be useful.

Thank you very much for your time, and I understand if you are too busy to reply.

Best regards,
Seungbin Kwon
Hanyang University

---

## 2. AlphaMix+ (PRUDEX-Compass, Sun et al., TMLR 2023, arXiv 2302.00586; TradeMaster-NTU/PRUDEX-Compass)

**Subject:** A few questions about the AlphaMix+ portfolio experiments in PRUDEX-Compass

Dear Prof. [이름],

My name is Seungbin Kwon, and I am an undergraduate student at Hanyang University. For my graduation thesis, I am re-running several published RL portfolio methods using their official code. Thank you for releasing PRUDEX-Compass; having the full evaluation framework public made this kind of study possible.

I ran AlphaMix+ for portfolio management (`AlphaMix+/PM`, commit 2b62831) on the dj30 splits. I want to describe the setup accurately, and there are a few details I could not determine. Any guidance would be appreciated, even on only some of them.

1. **Reported epoch.** Does the reported test result come from the final epoch, or from the epoch with the best validation return?
2. **Market average baseline.** Does the "market average" baseline (footnote 3) rebalance to equal weights every day, or buy equal amounts once and hold?
3. **Training settings and asset pool.** Which values of `num_trains_per_train_loop`, `num_expl_steps_per_train_loop` and `min_num_steps_before_training` were used for dj30? The dj_30 values in `__main__` are commented out. Also, the paper lists 29 US assets. In my download WBA was unavailable, so I used 28. Is that a reasonable substitute?
4. **Transaction costs.** The config sets `transaction_cost_pct = 0.001`. I could not find where this value is used in `TrainEnv.step()`. Could you tell me whether the reported results include transaction costs? It is quite possible that I missed where it is applied.

Thank you very much for your time, and I understand if you are too busy to reply.

Best regards,
Seungbin Kwon
Hanyang University

---

## 3. MASA (Li, Tam & Yeung, AAMAS 2024, arXiv 2402.00515; SteamerLee/MASA)

> 발송 전 확인: 저자·학회·arXiv 번호는 기억에 의존한 것이다. 논문 PDF 1쪽에서 다시 확인한다. MASA는 재현 대상이 아니라 코드 감사 대상이므로 설정 질문은 하지 않고 비용 처리만 묻는다.

**Subject:** A question about transaction costs in the MASA code

Dear Prof. [이름],

My name is Seungbin Kwon, and I am an undergraduate student at Hanyang University. For my graduation thesis, I am reading public RL portfolio implementations to understand how they handle transaction costs. Thank you for releasing the MASA code; the multi-agent design was interesting to study.

There is one point I would like to check with you so that I describe it correctly. In `utils/tradeEnv.py` (commit d97ef0e), the cost (c = 0.0003 in `config.py`) is deducted from capital when the new weights are set (around line 203). As far as I can tell, this deduction appears in the portfolio value curve. The reward, however, comes from `poDayReturn_withcost` (around line 249), and it did not seem to change when I varied c. Is the cost meant to be handled elsewhere in training, or am I misreading this part of the code? I am happy to share the short script I used if that would help.

Thank you very much for your time, and I understand if you are too busy to reply.

Best regards,
Seungbin Kwon
Hanyang University
