# Paper tables — draft (2026-11-14)

> Working note (Korean header for the repo; table text is in paper English).
> 상태: 초안. 출처는 `notes/lit/f1/funnel_table.csv`(funnel_table.py 출력)와 `replication/reproduction_synthesis.csv`. **잠정:** F1 재확인 시트(사용자 판정 대기)와 대장 A절(보고값 원문 대조) 결과에 따라 수치가 바뀔 수 있다. 재현율을 한 수치로 합치지 않는다(프로토콜 0장). 표 본문에는 과정 기록(커밋·시도 횟수·감사 경위)을 넣지 않는다.

---

## Table 1. Reproduction funnel: first stage at which each paper exited, by sample

Each paper is counted once, at the first stage it did not pass. Stages follow the pre-registered protocol: F0 eligibility, F1 official code, F2 code completeness, F3 data availability, F4 execution, F5 compute budget (10 h per seed), F7 reproduction verdict. No paper exited at F6 (reported comparison values). S56: an existing literature collection (56 papers, of which four were the in-depth targets T1–T4 and are listed separately). S-Q: a documented title search (Semantic Scholar, 2017–2026, selected venues). Supplementary: papers added because code was already known to exist; they are excluded from code-availability rates.

| Exit stage / outcome | S56 (n = 52) | S-Q (n = 12) | Suppl. (n = 5) | T1–T4 (n = 4) |
|---|---:|---:|---:|---:|
| F0 not eligible | 4 | 0 | 1 | 0 |
| F1 no official code found (authors not contacted) | 29 | 9 | 0 | 0 |
| F1 link dead | 2 | 0 | 1ᵃ | 0 |
| F1 third-party code only | 2 | 0 | 0 | 0 |
| F1 placeholder link | 1 | 0 | 0 | 0 |
| F1 full text unavailable | 2 | 0 | 0 | 0 |
| F2 incomplete code | 0 | 0 | 2 | 0 |
| F3 data not obtainable as specified | 3 | 0 | 0 | 0 |
| F4 not executable | 1 | 1 | 1 | 0 |
| F4 not tested (input construction out of scope) | 0 | 1 | 0 | 0 |
| F4 passed, no F7 attempt | 3 | 1 | 0 | 0 |
| F5 over compute budget | 3 | 0 | 0 | 0 |
| F7 verdict reached | 2 | 0 | 0 | 4 |

ᵃ A copy of the repository exists elsewhere; the official link is dead.

Notes for the text (not table content):
- "Not executable" and "over compute budget" are outcomes under our environment and time limits; they are not counted as reproduction failures.
- F7 for the two S56 papers: Ensemble strategy (ICAIF 2020) and RAT (IJCAI 2020), both *partially reproduced* (Table 2).

---

## Table 2. Reproduction verdicts against reported values

R1: our aggregate falls within the tolerance band (half the gap between the reported value and the strongest reported external baseline). R2: the paper's comparative claim holds in our runs. Verdict: both → reproduced; one → partially reproduced; neither → not reproduced.

| Paper (target) | Metric | Reported | Tolerance | Ours | Runs in band | R1 | R2 | Verdict |
|---|---|---:|---:|---:|---:|:-:|:-:|---|
| DeepAries (T1) | CAGR (%) | 7.90 | ±0.87 | 5.04ᵇ | 2/10 | ✗ | ✗ | Not reproduced |
| AlphaMix+ (T2), US 2021 | TR (%) | 20.7 | ±1.61 | 18.47 | 1/5 | ✗ | ✗ᶜ | Not reproducedᶜ |
| AlphaMix+ (T2), US 2020 | TR (%) | 12.7 | ±1.52 | 9.42 | 1/5 | ✗ | ✗ᶜ | |
| AlphaMix+ (T2), US 2019 | TR (%) | 25.1 | ±1.27 | 26.09 | 3/5 | ✓ | ✗ᶜ | |
| FinRL (T3), A2C | Ann. return (%) | 42.57 | ±4.87 | 35.36 | 0/5 | ✗ | ✓ | Partially reproduced |
| FinRL (T3), PPO | Ann. return (%) | 36.17 | ±1.67 | 36.41 | 3/5 | ✓ | ✓ | Reproduced |
| FinRL (T3), DDPG | Ann. return (%) | 36.01 | ±1.59 | 37.60 | 2/5 | ✗ᵈ | ✓ | Partially reproduced |
| FinRL (T3), TD3 | Ann. return (%) | 39.38 | ±3.27 | 37.99 | 3/5 | ✓ | ✓ | Reproduced |
| MARS (T4), code at publication | CR (%) | 29.50 | ±7.07 | 15.26 | 1/10 | ✗ | ✗ | Not reproduced |
| MARS (T4), later author revision | CR (%) | 29.50 | ±7.07 | 26.41 | 7/10 | ✓ | ✓ | Reproduced |
| Ensemble strategy (funnel) | Sharpe | 1.30 | ±0.415 | 1.01 | 4/5 | ✓ | ✗ | Partially reproduced |
| RAT (funnel) | fAPV | 156.53 | ±68.42 | 378.35 | 0/5 | ✗ (above) | ✓ | Partially reproduced |

ᵇ Seed selected by the paper's rule (lowest validation loss among 10 seeds).
ᶜ AlphaMix+ is judged over three test years (R1 and R2 each need ≥ 2 of 3). The verdict depends on two choices the paper leaves unspecified: which training epoch is reported, and whether the market-average baseline is rebalanced. Under validation-based epoch selection the verdict becomes *reproduced*; under a buy-and-hold market average it becomes *partially reproduced*.
ᵈ Outside the band by less than 0.01 percentage points.

Aggregation: DeepAries uses the paper's seed-selection rule; AlphaMix+ and RAT the seed mean; FinRL the seed median; MARS the median over 10 seeds; Ensemble the mean of five runs. FinRL uses 28 of the paper's 30 stocks.

Notes for the text (not table content):
- The FinRL family verdict is *partially reproduced* (two of four algorithms reproduced; family rule ≥ 3 for reproduced).
- MARS: the bundled checkpoint (single deterministic run) lies within the band (29.68); it is not used as general evidence because its selection procedure is undocumented.
- DeepAries 10-epoch variant: 6.38, not reproduced; not an independent result (five seeds identical to the 1-epoch runs).
