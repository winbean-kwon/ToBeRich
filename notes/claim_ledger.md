# 주장–증거 대장 (2026-11-11 작성, 사용자가 채움)

논문에 들어갈 숫자·주장은 이 대장의 행과 연결돼야 하고, **`결과` 칸을 사용자가 직접 채운 행만** 논문에 쓴다. Claude가 채운 칸은 "Claude 기재"로 표시하며 확인으로 치지 않는다.

- 결과 표기: `일치(날짜)` / `불일치: 원문 값 …(쪽·표)` / `원문에 없음` / `확인 불가: 이유`.
- 불일치가 하나라도 나오면 해당 행과 그 값에서 계산된 허용 폭·판정을 모두 다시 본다.
- 허용 폭은 모두 논문 값에서 계산된다(T1·T3·T4: ½·(보고값 − 논문 비교 대상), T2: 2·σ/√5, 근거 `notes/prereg_reeval_v3.md` 60–62행, `notes/mars_t4_o1_prereg.md`). 그래서 A의 보고값을 확인하면 허용 폭도 함께 확인된다. 계산은 손으로 다시 해 본다.
- 표의 우리 값은 `python3 replication/reproduction_synthesis.py`가 judge JSON을 읽어 만든다(2026-11-11부터 손으로 옮겨 적지 않음).

## A. 논문 보고값 — 원문 PDF와 대조 (최우선, Claude가 가장 틀리기 쉬운 부분)

| ID | 논문 | 항목 | 대장 값 | 어디서 찾을지 | 결과 |
|---|---|---|---|---|---|
| A1 | DeepAries (CIKM 2025) | DJ30 CAGR | 7.90% | 주요 결과 표 | |
| A2 | DeepAries | DJ30 MDD | 13.67% | 같은 표 | |
| A3 | DeepAries | ^DJI CAGR(비교 대상) | 6.15% | 같은 표 | |
| A4 | DeepAries | 시드 10개 중 검증 손실 최소를 고른다는 절차 | 논문/코드 중 어디에 있는지 | 실험 설정 절·저장소 README | |
| A5 | AlphaMix+ | TR S2021 / S2020 / S2019 | 20.7 / 12.7 / 25.1 | 결과 표. **어느 판본인지(v3) 함께 적기** | |
| A6 | AlphaMix+ | 시드 σ S2021 / S2020 / S2019 | 1.8 / 1.7 / 1.42 | 같은 표 | |
| A7 | AlphaMix+ | 5시드 평균이라는 서술 | 5시드 평균 | 실험 설정 절 | |
| A8 | AlphaMix+ | SR S2021 | 1.64 | 결과 표 | |
| A9 | FinRL (Liu et al., ICAIF 2021) | 연수익 A2C / PPO / DDPG / TD3 | 42.57 / 36.17 / 36.01 / 39.38% | 포트폴리오 배분 결과 표 | |
| A10 | FinRL | 샤프 A2C / PPO / DDPG / TD3 | 2.36 / 2.11 / 2.21 / 2.28 | 같은 표 | |
| A11 | FinRL | DJIA / Min-Var 연수익 | 32.84 / 24.10% | 같은 표 | |
| A12 | FinRL | 종목 수 30(우리는 28) | 30 | 데이터 절 | |
| A13 | MARS | CR / AR / SR / AVol / MDD | 29.50 / 31.19 / 2.84 / 10.99 / −5.39 | 결과 표 | |
| A14 | MARS | DJI CR / AR / SR / AVol / MDD | 15.36 / 16.19 / 1.41 / 11.51 / −6.06 | 같은 표 | |
| A15 | MARS | 시드 42를 명시함 | 시드 42 | 실험 설정 | |
| A16 | MARS | 시험 구간 길이(우리는 240거래일 창으로 역산) | 2024-01-17~12-27 | 데이터 절. 원문이 다른 구간을 적었으면 판정 전제가 흔들림 | |

## B. "원문에 없다(미기재)"는 주장 — 원문 전체 검색

"없다"는 것도 논문에 대한 주장이다. PDF에서 seed, average, mean, run, select, checkpoint, episode, best, validation을 검색한다.

| ID | 주장 | 결과 |
|---|---|---|
| B1 | FinRL은 연수익의 집계 방식(시드 수·평균/중앙값)을 적지 않았다 | |
| B2 | MARS는 에피소드·체크포인트 선택 규칙을 적지 않았다 | |
| B3 | MARS 번들 체크포인트(C)의 선택 경위가 적혀 있지 않다 | |
| B4 | DeepAries 논문 ^DJI 6.15%의 기간·연율화 정의가 적혀 있지 않다 | |

## C. 사전 등록이 결과보다 먼저인지

명령: `git log --format='%h %ad %s' --date=iso -- <파일>`. GitHub `audit-fix-1004`의 커밋 기록과도 대조한다. 로컬 날짜는 바꿀 수 있지만 푸시 기록은 GitHub에 남는다.

| ID | 대상 | 사전 등록(최초 커밋) | 결과(최초 커밋) — Claude 기재 | 확인할 것 | 결과 |
|---|---|---|---|---|---|
| C1 | T1 DeepAries·T3 FinRL | `notes/prereg_reeval_v3.md` 6f8f512 10-27 23:29 | FinRL judge ff48193 10-28 12:02, DeepAries judge bbe7ceb 10-29 23:59 | 순서, 그리고 사전 등록 뒤 판정 기준(60–67행)이 바뀌었는지 `git log -p 6f8f512.. -- notes/prereg_reeval_v3.md` | |
| C2 | T2 AlphaMix+ | `notes/alphamix_t2_o1_prereg.md` e2cfe8f 10-29 11:09 | judge eaebe7c 10-30 02:57 | 같음 | |
| C3 | DeepAries e1·e10 | `notes/deeparies_e10_prereg.md` 051eb94 10-30 14:31 | 결과 787f9e9 10-30 22:43 | 같음 | |
| C4 | T4 MARS | `notes/mars_t4_o1_prereg.md` 5e3cd6e 11-05 00:43 | 결과 9e0d81b 11-10 12:12 | 같음. 그리고 사전 등록 뒤 판정 코드 변경: `git log -p 5e3cd6e.. -- replication/mars_t4.py` | |
| C5 | T4 MARS 원시 출력 | — | **원시 출력과 judge JSON은 .gitignore 대상이라 커밋된 적이 없다.** 2026-11-11에 해시를 `notes/mars_t4_hashes_2026-11-11.txt`로 남김 | 11-10 판정 시점의 값이었다는 증거는 결과 노트(9e0d81b)의 숫자뿐이다. 노트의 숫자와 지금 JSON이 같은지 확인 | |

## D. 우리 값 재계산 — 판정을 다시 돌려 같은 값이 나오는지

Claude가 2026-11-12에 맥에서 D1~D5·D7을 실행했다. 모두 저장값과 일치했다. 다만 Claude 실행이므로 확인으로 치려면 사용자가 같은 명령을 직접 한 번 실행한다. 저장값이 같은 코드로 다시 나온다는 것만 보이고, 원시 출력 자체가 맞는지는 E(직접 재실행)가 맡는다.

추적 중인 JSON(T1·T2·T3)은 다시 돌린 뒤 `git diff`로 비교한다. 바뀐 게 없으면 재현된 것이다.

| ID | 대상 | 명령 | 결과 |
|---|---|---|---|
| D1 | 종합표 | `python3 replication/reproduction_synthesis.py && git diff replication/reproduction_synthesis.csv` | Claude 실행 2026-11-12: 차이 없음 |
| D2 | DeepAries O1 | `python3 replication/deeparies_run.py judge1` (출력은 `replication/deeparies/runs/judge_o1.json`에 생기므로 추적 중인 `replication/deeparies/judge_o1.json`과 비교) | Claude 실행 2026-11-12: 시드별 값·선택·등급 동일. 새 출력에 기록용 항목 3개(검증 손실 기록·장치·분)만 추가됨 |
| D3 | AlphaMix+ | `python3 replication/alphamix_t2.py judge1 <결과 폴더>`(원본은 일일 파일이 없어 실패한다. 결과 노트대로 `python3 replication/alphamix_t2/judge1_without_daily_check.py judge1 replication/alphamix_t2` 사용) | Claude 실행 2026-11-12: JSON 완전 동일 |
| D4 | FinRL | `python3 replication/finrl_t3_run.py judge` | Claude 실행 2026-11-12: 파일 바이트 동일(git diff 없음) |
| D5 | MARS | `cp -r data/mars_t4/judge_o1.json /tmp/j_old.json && MARS_WORK=.marswork MARS_OUT=data/mars_t4 python3 replication/mars_t4.py judge && diff <(python3 -m json.tool /tmp/j_old.json) <(python3 -m json.tool data/mars_t4/judge_o1.json)` | Claude 실행 2026-11-12: JSON 완전 동일(C 결정적, CR 29.679) |
| D6 | 손 계산 1건 | 아무 행 하나를 골라 시드 값(JSON)으로 중앙값·평균·허용 폭 판정을 계산기로 직접 계산 | |
| D7 | FinRL DDPG 경계 | 판정이 0.005%p 차이로 실패다. JSON은 소수 2자리라 표에서는 재계산할 수 없다. 원시 CSV(`replication/finrl_t3/o1/ddpg_W0_a_s*.csv`)로 미반올림 중앙값을 계산 | Claude 실행 2026-11-12: 시드 41.9438·36.6951·38.9331·34.7620·37.6049, 중앙 37.6049, 차 1.5949 > 허용 1.59, 초과 0.0049%p. 기록과 일치 |

## E. 직접 다시 실행 — Claude 없이 (가장 강한 확인, 1건이면 충분)

| ID | 대상 | 기대값 | 결과 |
|---|---|---|---|
| E1 | MARS C(번들 체크포인트 평가, 결정적) | CR 29.68, SR 2.54(W240) | |
| E2 | (대안) FinRL PPO 시드 1개 | `judge_W0.json`의 같은 시드 연수익 | |

## F. 코드 존재 여부(F1)

`notes/lit/f1/manual_check_list.md`에서 다음을 확인한다.
- A: SQ-SCR, SUP-CLRS, P24-08
- "(약한 확인)" 6편: P24-03, SQ-DPSRRL, SQ-ALRL, SQ-XPM, SQ-DGDRL, SQ-ObjDriven
- "없음" 중 무작위 5편 이상(아래 명령으로 고른다). 하나라도 틀리면 B 전체를 다시 본다.

```
python3 -c "import random;random.seed(20261111);print(random.sample(['jiang2017crypto','ye2020sarl','yu2019modelbased','park2020dqn','benhamou2020bridging','W21_HRPM','W22_MetaTrader','W21_PigorschSchafer','W21_LFSS','W22_PretoriusVanZyl','W21_Benhamou_crisis','P24-04','P24-05','P24-06','P24-07','P24-09','Y25-04','Y26-01','Y25-05','Y25-06','Y25-07','Y25-08','Y25-09','Y25-10','Y26-02','Y26-04','SQ-APTS','SQ-Regret','SQ-MAPS','SQ-TwoLevel'],5))"
```

| ID | 결과(논문 ID별) |
|---|---|
| F1 | 사용자 제공 PDF, Claude 판독(2026-11-12; 결과 칸은 사용자가 PDF에서 github·code 검색으로 재확인 시 확정): P24-07·SQ-MAPS·W21_LFSS·P24-04·W21_HRPM 모두 "없음" 일치(0/5 불일치). P24-04는 "요청 시 제공"만 있음. 남은 F: A 남은 항목(SUP-CLRS PDF), 약한 확인 6편 |

## G. 문헌·기록

| ID | 확인할 것 | 결과 |
|---|---|---|
| G1 | 논문 참고문헌에 넣는 모든 문헌의 제목·저자·연도·학회가 실제와 같은지(arXiv·DOI로) | |
| G2 | 표본 목록(`notes/lit/lit_survey_merged.csv`)에서 무작위 10편이 실제로 있는 논문인지 | |
| G3 | 저자 문의(DeepAries, PRUDEX)가 실제로 발송됐는지(본인 메일함) | |
| G4 | MARS L 커밋 2561606이 "논문 시점 코드"라는 근거: 커밋 날짜와 논문 제출·게재일 비교 | |
| G5 | MARS N의 "BMID 대역이 체크포인트 추가 커밋에서 넓어짐": 해당 커밋 diff를 직접 보기 | |
