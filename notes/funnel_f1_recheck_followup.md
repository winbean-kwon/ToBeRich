# F1 재확인 찾음 논문의 후속 단계 (2026-11-24)

## 이탈 기록(실행 전, 사용자 결정)
- `notes/f1_recheck_prereg.md`의 결과 처리는 "찾음으로 바뀐 논문의 후속 단계(F2 이후)는 이번 일정에서 실행하지 않는다"였다. 이 규칙은 일정 때문에 둔 것이다.
- 2026-11-24에 사용자가 끝까지 진행하기로 결정했다. 이유는 깔때기가 "어디서 막히는가"를 보는 표인데, F1에서 멈추면 이 논문들이 어디서 막히는지 기록되지 않기 때문이다.
- 대상: F1 재확인에서 `찾음`이 된 W22_PretoriusVanZyl, jiang2017crypto, Y26-01, Y26-03.
  - W22_PretoriusVanZyl(FRONTIER)은 이미 2026-11-21에 같은 이탈을 기록했다(c858b86). 탐색적 F7x도 마쳤다(`notes/funnel_f7x_frontier_prereg.md`, 8e8f35f).
  - 나머지 3편은 이 문서에서 정적 층(F0, F2, F6, F3)부터 `notes/funnel_protocol.md` 2절의 기준을 그대로 적용한다.
- 이 문서의 결과는 모두 **탐색적(프로토콜 3.3 밖)**이다. 본 깔때기의 F7 자리와 순서에는 들어가지 않는다. 표에서는 `F1재확인` 행으로 분리해 적는다.
- jiang2017crypto와 Y26-03의 `찾음`은 공저자 계정 근거이고, Y26-01과 함께 사람 확인을 기다리고 있다(`notes/lit/f1/f1_human_confirm_list.md`). 사람 확인에서 뒤집히면 그 편의 후속 결과는 버리고 F1 판정으로 되돌린다.
- F4를 할지는 정적 층 결과를 본 뒤 사용자가 정한다. 성과 비노출 등 2.2절 규칙은 그대로 적용한다.

## 정적 층 결과(2026-11-24, Claude 판정)
원문은 arXiv PDF 텍스트로 읽었다. 저장소는 GitHub API와 raw 파일로 읽었다. 코드는 실행하지 않았다. 성과 파일은 열지 않았다(저장소 `results/`의 CSV 이름만 봄).
Y26-01의 `results/table_4_switching.csv`는 저장소 설정과 논문의 차이를 확인하려고 한 번 열었다. 이 논문은 F6에서 멈추므로 F7 비노출과는 관계가 없다.

| id | F0 대상 | F2 코드 | F6 비교 대상 | F3 데이터 | 멈춘 곳 |
|---|---|---|---|---|---|
| jiang2017crypto | 통과(CNN 정책, 암호화폐 12종, 표본 외 백테스트) | 통과. 학습·백테스트 진입점이 있다(PGPortfolio). 비고 둘째 줄 참고 | 통과. Table III: 2016-05-14~07-03, CNN fAPV 16.305, SR 0.0369, MDD 0.296 | 재수집(Poloniex 공개 API) | **F4 실행 불가**. 데이터 경로가 막혔다 |
| Y26-01 | 통과(RL 전문가 5종 + 검색·LLM 전환, 3개 시장 각 30종) | 통과. `train_experts.py`, `run_indexing.py`, `run_backtest.py`가 있다. 비고 셋째 줄 참고 | **탈락: 평가 기간 미기재.** Table 6에 수치는 있지만 학습·검증·시험 구간을 본문 어디에도 적지 않았다(자산별 데이터 기간만 Table 2~4에 있음) | — | **F6** |
| Y26-03 | 통과(BERT 감성 + actor-critic, 미국 주식 2·4·6종) | 통과. `SBCA.py`(학습·검증·백테스트), `Bert.py`, `DataCreat.py`가 있다 | 통과. Table 1: 시험 2021–2022, 6종목 SBCA PV 1.5154, SR 0.8943 | **탈락: 규격 미정.** 비고 넷째 줄 참고 | **F3** |

비고:
- **jiang2017crypto F4.** `curl -sIL 'https://poloniex.com/public?command=returnChartData&currencyPair=BTC_ETH&start=1463184000&end=1467504000&period=1800'`를 호출했다. 응답은 301이고, 리다이렉트된 `www.poloniex.com`이 403을 돌려준다(CloudFront, 2026-11-24 08:10 UTC). 같은 코드·데이터 경로를 쓰는 EIIE의 F4(`notes/funnel_f4_jiang2017eiie.md`)와 같은 판정이며, 판정 근거는 실제 호출 결과다.
- **jiang2017crypto F2 비고.** 저장소는 2017-11-12에 생성되어 초판(2016-12) 이후다. README는 이 판이 "several versions ahead of the article"이고 두 번째 논문(1706.10059) 기준이라고 적는다. 첫 논문의 설정 파일은 없다. 2저자 README(kumkee/SURF2016)는 첫 논문 코드도 이 저장소에 있다고 적는다.
- **Y26-01 F2 비고(논문–코드 불일치).** 저장소 `src/config/config.yaml`의 설정은 암호화폐 5종, 2018–2023, L=60, H=20이다. 논문은 시장별 30종, L=22, H=5다. 설정 파일에는 외부 LLM 서버 주소와 키가 들어 있다(값은 여기 적지 않음). 논문은 H100 1장과 공개 가중치 LLM(Gemma4·Qwen3.6-27B)을 쓴다.
- **Y26-03 F3 비고.** 논문이 공개 데이터로 적은 `huggingface.co/datasets/Changahou/Mamba`는 열리지 않는다(HF API: 인증 오류, 즉 비공개 또는 없음. 같은 계정의 다른 데이터셋은 공개되어 있다). 코드가 읽는 `Data/news_2012_2022.csv`와 종목별 가격 CSV는 저장소에 없고, 출처도 논문·코드에 없다("public financial data APIs"라고만 적음). 종목과 기간은 정해져 있지만 뉴스 원천이 정해지지 않아서 2절의 F3 통과 규칙상 "규격 미정"이다.
- **Y26-03 탐색적 관찰(정적 의심, 실행 안 함).** `Bert.py`는 데이터를 종목·날짜 순으로 정렬한 뒤 행 기준 앞 80%로 BERT를 미세조정한다. 레이블은 다음 날 종가 상승 여부다. 그러면 앞쪽 종목은 2021–2022(시험 구간) 행까지 학습에 들어간다. 이 BERT가 낸 `delta_bert`가 정책 입력이 되므로 시험 구간 정보가 새어 들어갈 수 있다. 실행으로 확인하지 않았으므로 판정에 쓰지 않는다.

## 요약
F1 재확인에서 찾음이 된 4편이 멈춘 곳:
- FRONTIER: 탐색적 F7x까지 진행(별도 노트)
- jiang2017crypto: F4 실행 불가
- Y26-01: F6
- Y26-03: F3

jiang2017crypto, Y26-01, Y26-03의 F1 `찾음`은 사람 확인을 기다린다.

## P24-07(Markowitz Meets Bellman, KDD) — 정적 층(2026-11-24, Claude 판정, F1 사람 확인 대기)
F1은 저자 계정 점검에서 찾았다(`notes/f1_author_account_sweep_prereg.md`). 저장소 `BMEgang/BellmanMarkwitzProject`는 계정 이름이 Gang Hu(1저자)이고 README가 arXiv 2405.05449를 가리킨다. 아직 사람 확인 전이다. 후속 단계는 앞 4편과 같은 이탈 결정에 따라 탐색적으로 본다.
- 성과 비노출: 저장소의 `draw/*.csv`(저자 결과 곡선)와 `data/trade_predictions.csv`는 열지 않았다.
- 저장소 크기: 약 1.3GB(GitHub API `size`).

| 단계 | 판정 | 근거 |
|---|---|---|
| F0 | 통과 | 마르코위츠 지식 증류 + DDPG, DJ30, 표본 외 거래 구간 |
| F2 | 통과(비고) | `profilo management/`에 학습(`agent.train_model`, 50,000 스텝)·거래(`DRL_prediction`) 경로가 있다(FinRL·SB3·PyPortfolioOpt). 비고 참고 |
| F6 | 통과(그림·코드 판독) | Table 1 KDD: TR 138.38%, AR 38.74%, Sharpe 2.03, MDD −11.46%. 본문에는 데이터 기간(2009-01-01~2018-09-30)만 있다. 거래 구간은 Fig. 1 축(2016-01~2018-09)과 코드(`TRADE_START_DATE='2016-01-01'`, `TRADE_END_DATE='2018-09-01'`)에서 읽었다 |
| F3 | 통과(번들) | `data/processed_full.csv`, `after_processed_full.csv`, `train_data.csv`, `trade_data.csv`(29종목, 2016-01-04~2018-08-30) |

F2 비고:
- 데이터·출력 경로가 저자 맥의 절대 경로(`/Users/ganghu/Desktop/...`)로 박혀 있다.
- 같은 파이프라인 판이 여러 개다(`knowledgement_drill.py`, `knowledgement_drill_ddpg.py`, `new_test.py`, `new_trial.py`, `share.py`, `backup.py`).
- 그림 스크립트 `draw/draw.py`는 "KDD"를 `richard.csv`~`richard4.csv` 5개의 평균으로 그린다. ~~이 다섯 파일은 저장소에 없다~~ → **정정(반박 심사):** `draw/richard.csv`~`richard5.csv`가 저장소에 있다. Claude가 파일 목록을 잘라 읽어 놓쳤다. 각 파일은 `final/2023-11-2x_*/data/` 실행 폴더의 파일과 blob이 같다(내용은 열지 않음).
- "DDPG" 기준선(`originate_ddpg.csv`)은 `knowledgement_drill_ddpg.py`가 만든다. 이 스크립트는 증류 없이 원 가격으로 학습하는 FinRL DDPG다.

**데이터 관찰 — 철회(2026-11-24 반박 심사).**
- 처음 기록: 번들 `data/trade_data.csv`의 가격이 Markowitz 비중으로 수정된 판이라는 관찰. 이 관찰 자체는 맞다. `new_test.py` 계열은 분할 전에 `close *= (1 + w)`를 하고, 비중 매칭은 날짜가 아니라 정수 위치다.
- 그러나 이 데이터는 KDD 표·그림 경로와 연결되지 않는다. git blob 대조로 확인했고 저자 결과 파일은 열지 않았다.
  - `richard*.csv`가 나온 실행 폴더의 `trade_data.csv`(blob eac58121)는 번들 파일과 다르다.
  - 심사자가 확인한 바로는 이 파일은 5종목(AAPL·BA·CRM·UNH·V)이고, 원 가격 기준 배율이 1.0이다.
  - 따라서 "KDD 계좌 가치를 수정된 가격으로 쟀다"는 주장은 **철회**한다.
- 대신 남는 정적 관찰(탐색적, 저자 결과 미열람). 이 셋은 F7 사전 등록 전에 확인할 항목이다.
  - **KDD와 DDPG가 같은 스크립트 출력이다.** `richard.csv`는 `final/2023-11-21_19-19-07/data/originate_ddpg.csv`와 같은 blob이다. `richard3.csv`는 `profilo management/originate_ddpg.csv`와 같다. 증류는 SB3 `td3/policies.py`를 직접 고친 것으로 주석에 적혀 있고, 수정본 사본이 `draw/algo/policies.py`(`HuFeatureExtractor` 등)에 있다. 이것이 Markowitz 교사 망과 어떻게 연결되는지는 아직 다 읽지 않았다.
  - **"5회 평균"에 같은 파일이 두 번 들어간다.** `richard.csv`와 `richard4.csv`가 같은 blob(adbb977c)이다.
  - **종목 구성이 다를 수 있다.** 논문은 DJ30이라고 하는데, KDD 실행 데이터는 5종목으로 보인다(심사자 확인). DDPG 기준선 `draw/originate_ddpg.csv`(f211805e)와 같은 blob인 실행 폴더는 없어서, 기준선이 어떤 데이터로 나왔는지는 알 수 없다.

### P24-07 — 종목 구성 확인과 5종목 등가중 기준(2026-11-25, 탐색적, 저자 결과 미열람)
- KDD 곡선 실행 폴더(`final/2023-11-21_19-19-07/data/trade_data.csv`, blob eac58121)의 거래 데이터는 **5종목(AAPL, BA, CRM, UNH, V)**, 2016-01-04~2018-08-30, 3,355행이다. 이른 실행(`final/2023-11-14_07-50-04`)의 데이터는 29종목이다.
- 논문 본문은 "Dow Jones 30"이라고만 적었고(386행), 5종목으로 줄였다는 서술이 없다. 수정 SB3 사본(`draw/algo/policies.py`)에 `tickers_to_keep = ['AAPL', 'CRM', 'V', 'UNH', 'BA']` 주석이 있다.
- **자체 계산(입력 종가만 사용, 거래비용 0, 670거래일).** 5종목 등가중:
  - 매일 재조정: 총수익 130.8%, 연 37.0%, Sharpe 2.14, MDD −14.0%
  - 매수 후 보유: 총수익 125.3%, 연 35.7%, Sharpe 2.08, MDD −13.9%
  - 논문 Table 1의 KDD 값은 총수익 138.38%, 연 38.74%, Sharpe 2.03, MDD −11.46%다.
  - 종목별 연수익은 29~45%다(BA 44.5%, UNH 38.9%, AAPL 35.5%, CRM 29.4%, V 29.2%).
- **해석(정적·탐색적).**
  - KDD의 보고 수익·Sharpe는 이 5종목을 등가중으로 들고 있기만 해도 나오는 수준과 비슷하다.
  - Table 1의 DJI·BAH·CRP 등 기준선(연 15~20%)은 DJ30 수준의 수익이다.
  - 따라서 KDD가 기준선보다 우위라는 표의 비교는 **서로 다른 투자 유니버스를 비교했을 가능성**이 있다.
- **확인하지 않은 것.**
  - 기준선과 DDPG 곡선이 몇 종목으로 계산됐는지 확인하지 않았다(저자 결과 파일 미열람).
  - 5종목을 왜 골랐는지는 논문과 코드에 없다.
  - 거래비용(코드 0.1%)은 위 등가중 계산에 넣지 않았다.
- F4·F7 여부: 이 관찰로 F7 비교 대상(보고값 대 자체 실행)의 의미가 달라진다. 사전 등록을 쓸 때 "논문 서술(DJ30) 기준"과 "저자 실행(5종목) 기준" 중 무엇으로 할지를 먼저 정해야 한다.
