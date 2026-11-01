# 공개 코드 감사 — 정적 예측 (2026-11-01, 동적 점검 전에 커밋)

> 사전 등록: `notes/prereg_code_audit.md`(b5a83ce). 이 문서는 3장 2단계의 산출물이다. 동적 결과를 보기 전에 고정한다.
> 저장소는 `.audit/`(git 제외)에 코드만 받았다. 1MB를 넘는 파일과 데이터는 받지 않았다.

## 0. 해석 결정 (동적 결과 전에 고정)
- **P1의 0 가중치 처리**: 2.2의 "두 가중치의 최대 비"는 문자 그대로 모든 자산에 적용한다. 상위 k개만 고르는 구조처럼 0 가중치가 가능하면 R은 무한이다. 보유 종목 안에서의 비 상한은 기술 열에 따로 적는다.
- **#5 ICAIF 2020**: 리디렉트 대상(AI4Finance-Foundation/FinRL-Trading @4409abe)은 지금 다른 프로젝트(FinRL-X)다. 원 논문의 앙상블 주식 거래 env가 없다. 감사 단위가 없으므로 **"대상 env 부재"**로 분류해 R 분모에서 뺀다. 참고로 이 저장소의 DRL 전략(`src/strategies/fundamental_portfolio_drl.py` 21행)은 기지 대상인 FinRL `StockPortfolioEnv`를 import한다.
- **동적 실행 방식**: 대상 env·비용 함수만 AST로 추출하거나 import한다. 코드는 고치지 않는다.
  - RAT의 비용은 torch `Test_Loss` 안에 있고 `.cuda()`가 하드코딩돼 있다. `torch.Tensor.cuda`를 CPU 항등으로 바꿔 실행한다. 이는 장치만 바꾸며 계산은 같다.
  - WaveCorr는 모듈 머리에서 tensorflow를 import한다. 이를 스텁으로 막고, numpy인 `calculateMu`를 쓴다.

## 1. 대상별 정적 예측

| # | 대상 @커밋 | 계보(코드 기준) | 비용 상태 | C1 예측 | S1 예측 | P1 예측 |
|---|---|---|---|---|---|---|
| 4 | RAT @9a65269 | PGPortfolio env(README 94행이 PGPortfolio 툴박스를 사용했다고 밝힘, `HistoryManager`·`DataMatrices` 구조 동일) | 명시 비용 0.0025(`main.py` 50행) | 통과 | 위험자산 사이 이동은 ≈1.0. 현금 칸도 τ에 포함(1096–1098행)하므로 현금이 바뀌는 이동은 최대 2배. 표준 행동열은 현금이 eps로 고정이라 ≈1.0, 시점 일치. 첫 스텝은 비용 없음(1100행) | 출력 = 2·softmax(선형) − softmax(선형)(645–650행). 무경계, 공매도 가능 → R 무한 |
| 5 | ICAIF 2020 → FinRL-Trading @4409abe | — | — | 대상 env 부재 | — | — |
| 6 | DeepTrader @4b00b2a | 독립 | 명시 비용 0.001(`hyper.json` 17행) | 통과 | DJIA·HSI는 `allow_short=True`(`run.py` 71·79행). 롱 쪽 비용은 매도분에만 부과(`portfolio_env.py` 294–295행) → 롱 이동 비율 ≈0.5 "관례 차이". 롱 전용(CSI100, 320행)은 양방향이라 ≈1.0. 시작은 현금(376행), 시점 일치 | 점수 = sigmoid(`ASU.py` 267행, Δ=1), 상위 G=4 softmax(`agent.py` 41–61행). 보유 4종목 안 비 ≤ e, w_max ≤ e/(e+3) = 0.475. 나머지 0 → R 무한(0장 규칙) |
| 8 | WaveCorr @20ff832 | 독립(EIIE 구조를 TF로 재구현했으나 코드 동일성 없음) | 명시 비용 0.0005(`wavecorr_run.py` 23행) | 통과 | 반복 해 μ(`wavecorr_agent.py` 122–134행), 매수·매도 양방향이라 ≈1.0, 같은 스텝에 반영(156–158행). 현금 칸 없음, 시작 등가중(102–104행) | 선형 출력 softmax(`wavecorr_network.py` 222–224행) → R 무한. `constrain_action=False` 기본 |
| 13 | MASA @d97ef0e | FinRL SPE 파생(`config.py` 13행 "Trading environment: FinRL", 클래스명 `StockPortfolioEnv`) | 명시 비용 0.0003(`config.py` 157행) | 통과 | 드리프트 가중치 대비 c·Σ\|Δw\|를 같은 스텝 자본에서 뗌(`tradeEnv.py` 203행) → ≈1.0. 첫 스텝은 자본 × (1−c)(189행), 종료 시 청산 비용(164행). 슬리피지 난수가 있어 두 실행의 시드를 같게 둔다 | `norm_method='sum'`(`config.py` 83행): w = a/Σ\|a\|, a ∈ Box(0,1)(73행) → a_i → 0이 가능하므로 R 무한 |
| 14 | jackieli19/PGPortfolio(Stock) @a7c1333 | PGPortfolio env(포크) | 명시 비용 0.0025(`net_config.json` 32행) | 통과 | `calculate_pv_after_commission`(`tools/trade.py` 39–52행) 반복 해, 현금 제외 → ≈1.0, 같은 스텝(`trade/backtest.py` 74–77행) | 현금 편향 + 선형 출력 softmax(`learn/network.py` 115–122행) → R 무한 |

## 2. 정적 예측 기준 반복성 (판정 아님 — 판정은 동적 결과로 한다)
- R-비용: 신규 5개(#5 제외) 모두 비용을 부과할 것으로 예측한다. 비용 결함 0 → **"기지 대상 밖에서는 반복이 확인되지 않았다"**로 예상된다.
- R-매개화: 신규 가중치 매개화 5개 모두 R 무한으로 예측한다. **"반복 확인 안 됨"**으로 예상된다.
- 기술 관찰: MASA는 FinRL SPE에서 파생됐지만 비용을 구현했다. DeepTrader는 유계 점수(sigmoid) 뒤 상위 G개 softmax를 쓰므로, DeepAries처럼 보유 종목 안에서는 비가 묶인다.

## 3. 사용 시간(대략)
클론과 정적 읽기에 6개 합계 약 1시간 30분이 걸렸다. 저장소당 상한 2시간 이내다.
