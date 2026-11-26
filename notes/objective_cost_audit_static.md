# 목적 함수 비용 감사 — 정적 읽기와 예측 (2026-11-26, 동적 점검 전)

> 사전 등록 `notes/objective_cost_audit_prereg.md`(2a9b424, 정정 5597384). 이 문서는 4장 2단계 산출물이다. 동적 결과를 보기 전에 고정한다.
> 방식: 코드 읽기만 했다(실행·기울기·보상 계산 없음). 로컬 사본(`.audit/`, `.t1env/`, `.t3env/`, `.t4env/`, `.marswork/`), 서버 기존 체크아웃 읽기 전용 열람(Ensemble, Margin Trader), 고정 커밋의 개별 소스 파일 다운로드(FinRL POE, rlportfolio, TradeMaster, PRUDEX-Compass, MMB 스크립트와 FinRL StockTradingEnv; scratchpad, 15개 파일).
> 행 번호는 표기한 커밋 기준이다. "미확인"은 읽어서 확정하지 못한 항목이다.
> 사용 시간: 16개 대상 전체 정적 읽기에 약 1시간이 걸렸다(벽시계 기록이 대상별로 정확하지 않아 대상별로는 "≤ 15분"으로만 적는다). 모든 대상이 1시간 상한 안이다.

## 요약 표 (정적 예측, 판정 아님)

| # | 대상 @커밋 | 유형 | 비용 → 학습 신호 | 평가 경로 비용 | O1 정적 예측 | 동적 실행 |
|---|---|---|---|---|---|---|
| 1 | PGPortfolio @48cc5a4 | L | μ가 net.output의 함수, 그래프 안 | 부과 | S | 서버 TF1(사용자 확인 필요) |
| 2 | FinRL POE @7e98df4 | L | trf_mu = 버퍼에 저장된 상수 | 부과 | B | Mac |
| 3 | FinRL SPE (FinRL-Meta @286fef6) | R | 없음 | 미부과 | N | Mac |
| 4 | RAT @9a65269 | L | pure_pc가 w의 함수, 그래프 안 | 부과 | S | Mac(AST 추출, .cuda 항등) |
| 5 | Ensemble @f02a762 | R | 현금에서 차감 → 보상 | 부과 | S | Mac(env 파일 1개 필요) 또는 서버 |
| 6 | DeepTrader @4b00b2a | L(혼합) | MSU의 MDD 보상 가중치로만 | 부과 | S(약함, MSU 경로만) | Mac |
| 7 | WaveCorr @20ff832 | L | μ가 action의 함수, TF 그래프 안 | 부과 | S | 정적만(TF1.14) 또는 서버 TF1 |
| 8 | TradeMaster @1747cc1 | R | 가치에서 차감 → 보상 | 부과 | S | Mac(AST 추출) |
| 9 | AlphaMix+ @2b62831 | R | 없음 | 미부과 | N | Mac |
| 10 | EarnMore @810ff59 | R | 없음 | 미부과 | N | Mac |
| 11 | MASA @d97ef0e | R | 가치에서만 차감, 보상에서 빠짐 | 부과 | B | Mac(기존 하네스) |
| 12 | jackieli PGPortfolio @a7c1333 | L | #1과 같음 | 부과 | S | 서버 TF1(사용자 확인 필요) |
| 13 | DeepAries @634f559 | R | 가치에서 차감 → 보상 | 부과(시점 편차) | S | Mac(AST 추출) |
| 14 | MARS L @2561606 / N @6ca2051 | R | 수익률 + 달러 비용 직접 차감 | 부과 | S | Mac(run_episode 하네스, 부담 큼) |
| 15 | Margin Trader @7b7fa9e | R | 현금·신용에서 차감 → 보상 | 부과 | S | 서버(py310; Mac은 Python 3.9라 `match` 구문 불가) |
| 16 | Markowitz Meets Bellman @93c273f | R | FinRL StockTradingEnv, 현금에서 차감 | 부과 | S | Mac(env 파일 1개) 또는 서버 |

- 정적 예측 기준으로 B는 #2(확인 대상)와 #11(MASA, FinRL SPE 파생) 둘이다. 분모 #3–#16에서 B는 1개 구현·1개 계보이므로, 동적 결과가 정적 예측과 같다면 6장 문장은 "FinRL POE 밖에서는 반복이 확인되지 않았다"가 된다. 이는 예측이며 판정이 아니다.
- 사전 예측(#1 S, #2 B, #3·#9 N)과 정적 읽기 결과가 모두 같았다.

---

## #1 PGPortfolio (ZhengyaoJiang/PGPortfolio @48cc5a4) — 확인 대상
(지시받은 기존 읽기를 그대로 옮긴다. 이번에는 서버 사본을 다시 열지 않았다. 같은 구조인 #12 로컬 사본으로 행 위치를 대조했다.)
1. **유형 L.** 기본 `loss_function6` = −mean(log pv_vector)(`net_config.json` 16행, `pgportfolio/learn/nnagent.py` 101–102행).
2. **경로.** pv_vector = Σ(output·future_price) × [1, μ](28–29행). μ = 1 − c·Σ|w_{t+1} − w′_t|를 그래프 안에서 계산한다(`__pure_pc` 180–186행, c = 0.0025). w′_t = future_omega는 net.output에서 만든다(24–25행). 비용 항은 정책 출력의 함수다.
3. **평가.** `tools/trade.py` 39–52행 반복 해 μ로 부과한다.
4. **예측 S.**
5. **동적.** TF1 그래프다. 서버 `adrl/p37`(TF 1.15.4)에서 `eiie_inspect/repo`로 실행할 수 있어 보인다. 이번 단계는 서버 읽기 전용이므로 "서버 TF1 환경 재사용 검토, 사용자 확인 필요"로 둔다. 안 되면 정적만.

## #2 FinRL POE EIIE·EI3 (AI4Finance-Foundation/FinRL @7e98df4) — 확인 대상
1. **유형 L.** `finrl/agents/portfolio_optimization/algorithms.py` `PolicyGradient._gradient_ascent`(225–257행)의 정책 손실을 직접 최적화한다. env 보상(`env_portfolio_optimization.py` 357–365행 log 수익)은 학습에 쓰이지 않는다.
2. **경로.** env가 `trf` 모형으로 μ를 numpy 반복 해로 계산해 `info["trf_mu"]`에 넣는다(`env_portfolio_optimization.py` 321–333행). 학습 루프는 이 값을 (obs, last_action, price_variation, trf_mu)로 버퍼에 저장한다(`algorithms.py` 123행, 검증 214행). 손실은 `-mean(log(Σ mu·price_variations·trf_mu))`(241–248행)다. trf_mu는 표본당 스칼라 상수이고, log 안의 상수배라 정책 매개변수에 대한 기울기에 기여하지 않는다. 비용 항은 **그래프 밖 상수**다. 또한 저장된 trf_mu는 표집 당시(노이즈를 넣은) 행동으로 계산한 값이고, 손실의 mu는 갱신 시점의 정책 출력이다.
3. **평가.** env 가치에 μ를 곱한다(333행). 부과한다.
4. **예측 B.**
5. **동적.** Mac에서 가능하다(torch 2.6). `algorithms.py`가 `.architectures`(EIIE)를 import하므로 동적 단계에서 `architectures.py` 1개를 같은 커밋에서 더 받아야 한다. 합성 env로 버퍼를 채우고 `_gradient_ascent`의 손실을 그대로 계산한다(optimizer step은 하지 않음).
- 부수 관찰(미확인): `info["trf_mu"]`는 `trf` 분기(332행)에서만 설정된다. `comission_fee_model="wvm"`이면 `algorithms.py` 123행이 KeyError가 날 것으로 보인다. 실행하지 않았다.

### rlportfolio 신규성 메모 (분류에 넣지 않음)
- 대상: CaioSBC/RLPortfolio @071cf75(2025-03-12, 최신). `rlportfolio/algorithm/policy_gradient.py`.
- `_gradient_ascent`는 μ를 버퍼에서 읽지 않고 **현재 정책 출력 `actions`로 다시 계산한다**(705–714행): `trf_mu = 1 − comission_rate · Σ|actions[:,1:] − last_actions[:,1:]|`.
- 그러나 이 계산이 **`with torch.no_grad():` 안에 있다**(711행). 따라서 trf_mu는 그래프에서 떨어진 상수이고, 손실 `-mean(log(Σ actions·price_variations·trf_mu))`(717–719행)에서 비용 기울기는 FinRL POE와 마찬가지로 0일 것으로 예측한다.
- `EpisodicPolicyGradient`, `FastPolicyGradient`는 이 메서드를 상속한다(`fast_policy_gradient.py` 165행 호출). 이 파일의 커밋 이력(d5a74e3 … 071cf75)에서 해당 부분을 바꾼 메시지는 보이지 않는다(내용 diff는 보지 않음, 미확인).
- 함의: rlportfolio는 μ를 행동 함수로 바꿨지만 그래프에는 연결하지 않았다. **이 패키지가 문제를 이미 고쳤다고 볼 근거는 코드에 없다.** 신규성 조정은 "후속 패키지도 같은 결과(비용 기울기 0)를 낼 것으로 정적 예측"으로 적는다. 동적 확인은 분류 밖이며, 하려면 Mac에서 같은 방식으로 가능하다(추가 파일 필요).
- 문서(README·docs)는 읽지 않았다. 문서가 이 설계를 의도로 밝히는지는 미확인이다.

## #3 FinRL SPE (FinRL-Meta `StockPortfolioEnv`, T3에서 쓴 판 @286fef6)
1. **유형 R.** SB3 A2C·PPO·DDPG·TD3가 env 보상을 쓴다.
2. **경로.** `.t3env/fm/meta/env_portfolio_allocation/env_portfolio_yahoofinance.py`: `transaction_cost_pct`는 91행에서 저장만 한다. step의 수익(200–205행)과 보상 `self.reward = new_portfolio_value`(213행)에 비용 항이 없다. 보상 스케일링은 주석 처리(215행).
3. **평가.** 미부과(7.1 표, `notes/finrl_t3_o5_result.md`: 보상·수익이 c = 0과 동일).
4. **예측 N.**
5. **동적.** Mac(gym 0.26, SB3 2.7, pandas 있음). T3 O5 실행기(`replication/finrl_t3_run.py o5`)의 행동 주입을 재사용할 수 있다.
- 커밋: `.t3env/fm`은 별도 git 저장소가 아니다. 286fef6은 이전 노트 기준이다.

## #4 RAT (Ivsxk/RAT @9a65269)
1. **유형 L.** `main.py` `Batch_Loss`(992–1035행)를 `SimpleLossCompute`(1037–1048행)가 `loss.backward()`로 최적화한다. 학습 손실 지정 1437행.
2. **경로.** future_omega = w·close/reward(1014행), pure_pc = 1 − Σ|wt − wt1|·commission_ratio(1017행), reward = reward·pure_pc(1024행), loss = −mean(log reward)(1027–1034행). w는 모델 출력이고 detach가 없다(파일 전체의 detach/no_grad는 1188·1264·1338행, 학습 손실 밖). 비용 항은 정책 출력의 함수다. 분산·비용 벌점 항은 주석 처리돼 있다(1032·1035행).
3. **평가.** `Test_Loss` 1095–1104행 같은 식으로 부과(이전 감사 C1 통과, S1 1.000).
4. **예측 S.**
5. **동적.** Mac. 이전 감사처럼 AST로 `Batch_Loss`와 모델 생성 함수를 꺼내 `.cuda()`를 CPU 항등으로 바꾼다. 모델 전체가 필요하므로(매개변수 기울기) 이전 감사보다 추출 범위가 넓다. 시간 안에 안 되면 X.

## #5 Ensemble (6장 공식 코드, 서버 `~/f4work/ensemble/repo` @f02a762)
1. **유형 R.** `model/models.py` 26–57행 A2C·DDPG·PPO `model.learn`(stable-baselines)이 env 보상을 쓴다.
2. **경로.** `env/EnvMultipleStock_train.py`: 매도 시 현금에 (1 − fee)(62–65행), 매수 시 (1 + fee)(80–82행)를 곱한다. TRANSACTION_FEE_PERCENT = 0.001은 모듈 상수다(19행). 보상 = end_total_asset − begin_total_asset(129·158·163행)이고 begin은 거래 전에 계산하므로 비용이 보상에 들어간다. 보상 스케일링 없음.
3. **평가.** `EnvMultipleStock_trade.py`·`_validation.py`도 같은 구조로 부과(19·75–109·194행, 190행).
4. **예측 S.**
5. **동적.** Mac(gym 있음)에서 env 파일만 쓰면 된다. 단 파일이 서버에만 있어 읽기 전용으로 가져와야 한다. 비용 값은 모듈 상수를 바꿔 주입한다(설정 변경이며 코드 수정 아님으로 해석, 동적 단계에서 확인). 서버 기존 환경에서도 가능.
- 이전 감사의 "ICAIF 2020 대상 env 부재"(리디렉트 저장소)와는 다른, 6장에서 실행한 코드다.

## #6 DeepTrader (CMACH508/DeepTrader @4b00b2a)
1. **유형 L(혼합).** 학습 스크립트가 직접 만든 손실을 최적화한다(`src/agent.py` 150–161행): loss = −(γ·gradient_rho + gradient_asu).
   - gradient_asu = log Σ(normed_ror · softmax(scores))(127–128·150행). 가격 수익만 쓰는 지도형 항이다.
   - gradient_rho = rewards_mdd · log p(ρ)(145·153행). MSU(ρ)의 REINFORCE 항이고 가중치는 에피소드 자산의 MDD다.
   - env 보상 `rewards.total − market_avg`(126행)은 정규화까지 하지만(147–148행) **손실에 쓰이지 않는다.**
   - msu_bool 기본 True(`run.py` 146행), γ = 0.05(`hyper.json`).
2. **경로.** 비용은 env(`environment/portfolio_env.py` 294–295·308행 공매도 허용, 320행 롱 전용)에서 자산 dv1에 들어가고, `info['total_value']`(364행) → agent_wealth(130행) → MDD(145행) → gradient_rho 가중치로 간다. 그래프 밖 상수지만 REINFORCE 가중치라 매개변수 기울기에 영향을 준다. ASU 항에는 비용 경로가 없다. 가중치는 topk 후 numpy로 만들어(`agent.py` 49–60행) 미분되지 않는다.
3. **평가.** env가 부과(이전 감사 C1 통과).
4. **예측 S(약함).** 전체 매개변수 기울기 기준으로는 MSU 항 때문에 차이가 날 것으로 본다. 단 (a) 합성 경로에서 낙폭이 없으면 MDD가 둘 다 0이라 차이가 없을 수 있고, (b) ASU 블록 기울기만 보면 차이 0일 것이다. 블록별 상대 차이를 기록용으로 함께 적는다(판정은 사전 등록대로 전체 기울기).
5. **동적.** Mac(torch). ASU·MSU 모델을 CPU로 만들고(`device` cuda 설정 무시) 고정 시드로 ρ 표본을 맞춘다.

## #7 WaveCorr (saeedmarzban/waveCorr @20ff832)
1. **유형 L.** `src/wavecorr_agent.py` 86–98행: loss = −(mean(reward)/std(reward) − L2 − 제약 항), Adam으로 최적화.
2. **경로.** `src/wavecorr_network.py` 기본 모델 waveCorr: RNN=False 분기 mu_norm = Σ|action − wIn|(225행), RNN 분기는 행동에서 만든 wPrime과 비교(244–246행). μ = 1 − mu_norm·tradeFee(248행), reward = log(cum_ret·μ)(251–252행). action은 softmax 정책 출력(224행)이다. 학습 시 wIn에는 드리프트 가중치 wPrime을 넣는다(`wavecorr_agent.py` 180–186행). 비용 항은 정책 출력의 함수, 그래프 안. tradeFee = 0.0005(`wavecorr_run.py` 23행).
3. **평가.** numpy 반복 해 `calculateMu`(122–134행)로 부과(154–158행, 이전 감사 S1 0.9995).
4. **예측 S.**
5. **동적.** TF 1.14 필요(`requirements.txt` 2행). Mac에 TF 없음. 서버 TF1 환경(#1과 같은 p37) 재사용 가능성은 미확인이며 사용자 확인이 필요하다. 아니면 정적만.

## #8 TradeMaster (TradeMaster-NTU/TradeMaster @1747cc1, 기본 `PortfolioManagementEnvironment`)
1. **유형 R.** `trademaster/trainers/portfolio_management/trainer.py` 31–41행 RLlib A2C·DDPG·PG·PPO·SAC·TD3가 env 보상을 쓴다.
2. **경로.** `trademaster/environments/portfolio_management/environment.py`: 수수료 = Σ|w_old − w_new|·c·V(151–156행), new_V = (V − fee)(1 + r)(159–160행), 보상 = new_V − V(163행). 비용이 보상에 들어간다. c 기본 0.001(40행).
   - 기록: EIIE 변형(`eiie_environment.py` 174–183행)도 보상 = log 가치 비율에 수수료 포함이며, 그 에이전트(`agents/portfolio_management/eiie.py`)는 이 보상으로 critic을 학습하는 actor-critic이다(90–153행).
3. **평가.** 같은 env가 부과(`notes/review_next_directions.md` 22행, 같은 스텝).
4. **예측 S.**
5. **동적.** Mac. 모듈이 `trademaster.utils`, `..custom`, `..builder`를 import하므로 AST로 클래스만 꺼내고 `get_attr`·기반 클래스를 import 차단용 스텁으로 둔다.

## #9 AlphaMix+ (TradeMaster-NTU/PRUDEX-Compass @2b62831)
1. **유형 R.** `AlphaMix+/PM/AlphaMix+_sz50.py`: rlkit SAC 앙상블(`NeurIPS20SACEnsembleTrainer`, 11·160–189행)이 env 보상을 쓴다.
2. **경로.** `AlphaMix+/PM/rl_env/portfolio_management.py`: `transaction_cost_pct`는 26행에서 읽기만 한다. 보상 = (new_V − V)·reward_scaling(115·127행), 비용 항 없음(`notes/alphamix_t2_o5_static.md`).
3. **평가.** 미부과(7.1 표, 정적 읽기).
4. **예측 N.**
5. **동적.** Mac(gym). env 파일 하나로 가능하다(T2 작업에서 이미 받은 파일과 같음).

## #10 EarnMore (DVampire/EarnMore @810ff59)
1. **유형 R.** 기본 설정(`configs/mask_sac_portfolio_management.py` 177행 `EnvironmentPV`)의 SAC 계열 에이전트가 env 보상을 버퍼에 넣는다(`pm/agent/sac/mask_sac.py` 202–235행 구조, `mask_sync_sac.py` 220·229·429행).
2. **경로.** `pm/environment/pm_based_portfolio_value.py`: `transaction_cost_pct`는 34행에서 저장만 한다. step(151–189행)의 보상 = 새 포트폴리오 가치(170–173행)이고 비용 항이 없다. 수익형 env(`pm_based_portfolio_return.py` 149행 reward = portfolio_ret)도 같다.
3. **평가.** 미부과(`notes/code_audit_result.md` 3장 기지 대상).
4. **예측 N.**
5. **동적.** Mac(gym, sklearn 1.6 있음). `pm.registry` import를 스텁으로 막는다.
- 기록(탐색적, 비용과 무관): 170행은 이미 종목 가중치를 곱한 portfolio_ret에 다시 (1 − w_cash)를 곱한다. 의도 여부는 미확인.

## #11 MASA (SteamerLee/MASA @d97ef0e)
1. **유형 R.** `RL_controller/TD3_controller.py` 499·513행이 `env.step`의 보상을 replay buffer에 넣는다.
2. **경로.** 비용은 새 가중치 시점에 자본에서 뗀다(`utils/tradeEnv.py` 203행). 그 뒤 당일 수익 `poDayReturn_withcost`(249행)는 비용을 뗀 자본을 분모로 계산되어 비용이 빠진다. 보상 profit_part = log(1 + poDayReturn_withcost)(303행), self.reward(354행). 제어기 분기(304–327행)도 같은 profit_part를 쓴다. 비용은 관측의 log 자본(252행)에는 들어간다.
3. **평가.** 자산 곡선에는 부과(203–205행; 이전 감사 C1 "부분 부과(가치만)", 동적으로 보상 차이 ≤ 1e−12).
4. **예측 B.**
5. **동적.** Mac. `replication/code_audit/` 하네스(AST 추출)를 S1 행동열과 c = 0.01/0으로 다시 쓴다. 이전 실행은 c = 0.0003이었다.

## #12 PGPortfolio 포크 (jackieli19/PGPortfolio @a7c1333)
1. **유형 L.** `pgportfolio/learn/nnagent.py` `loss_function6`(101–102행), 선택 119행. 기본 설정과 `train_package_jli/*/net_config.json` 9개 모두 loss_function6, trading_consumption 0.0025.
2. **경로.** #1과 같다: future_omega(24–25행), pv_vector × [1, μ](28–29행), `__pure_pc` μ = 1 − c·Σ|w_{t+1} − w′_t|(180–184행). 정책 출력의 함수, 그래프 안.
3. **평가.** `tools/trade.py` 39–52행, `trade/backtest.py` 74–77행(이전 감사 S1 0.9988).
4. **예측 S.**
5. **동적.** #1과 같다(TF1). 서버 TF1 환경 재사용은 사용자 확인 필요, 아니면 정적만.

## #13 DeepAries (dmis-lab/DeepAries @634f559)
1. **유형 R.** `exp/exp_DeepAries.py` PPO: 보상(222–226행, 최적 기간 보너스 ×1.2/×0.8)을 transition에 저장(240–245행)하고 `calc_advantage`·`train_net`(495–557행)이 쓴다. 예측 손실(548행)도 같이 최적화하지만 가격만 쓴다.
2. **경로.** 기본(`complex_fee` False, `main.py` 112행) `TradingEnvironment.step`(120–134행): 수수료 = Σ|w_old − w_new|·fee·V(124–127행), new_V = (V − fee)(1 + r)(128행), 보상 = 순수익률(129–130행). complex_fee 분기(105–119행)도 μ(fee 함수)로 가중치를 줄여 보상에 반영한다. fee 기본 0.0001(110행).
3. **평가.** 같은 env로 부과하나 시점·크기 편차가 있다(7.1: 교대 경로 기준 비용의 약 2%, 첫 매수 한 스텝 늦음).
4. **예측 S.** S1 교대 행동열에서 비용이 작게 잡히는 편차가 있어도 c = 0.01이면 |r_c − r_0| > 1e−12는 넘을 것으로 본다.
5. **동적.** Mac. `TradingEnvironment` 클래스만 AST로 꺼낸다(args에 fee_rate, complex_fee만 필요).

## #14 MARS (6장 공식 코드, 출판판 L @2561606, 저자 수정본 N @6ca2051)
1. **유형 R.** `main.py` `run_episode`가 보상을 각 에이전트 replay buffer에 넣고(L 368–374행) `agent.py`가 Q 목표에 쓴다(210–224행).
2. **경로.** 거래마다 현금에서 |거래액|·0.001을 뗀다(L 250–255행, `config.py` 24행). 보상 = return_component − total_monetary_transaction_cost_for_step − risk_penalty(L 348행, N 363행). return_component는 비용을 뗀 가치로 계산되고(280·293·328행), 비용은 **달러 단위로 한 번 더** 뺀다. 첫 스텝 보상은 0(L 354행).
3. **평가.** 같은 `run_episode`(train=False)로 부과(N 440행 등).
4. **예측 S**(L·N 모두).
5. **동적.** Mac(torch). `run_episode`에 고정 행동을 넣으려면 multi_agent를 대신하는 행동 공급자가 필요하다. 이전 감사의 행동 주입과 같은 성격이지만 함수가 커서 2시간 안에 못 끝나면 X.
- 기록(탐색적, O1 분류 밖): 보상에서 비율(return_component)과 달러 금액(거래비용 합)을 바로 더한다. 초기 자본 1e6(`config.py` 22행)이면 거래비용 항이 수익 항보다 수십~수천 배 클 수 있다(크기는 계산하지 않음, 미확인). 학습 신호가 비용을 "보는가"에는 영향이 없고, 판정은 바뀌지 않는다.

## #15 Margin Trader (6장 공식 코드, 서버 `~/f4work/mt/repo` @7b7fa9e)
1. **유형 R.** `trading_margin_a2c.py` SB3 A2C(17·114–125행), env `env/marginEnv.py` `MarginTradingEnv`(21행).
2. **경로.** 롱 매도 시 현금에 (1 − c)(124–150행), 매수 시 (1 + c)(196–220행), 공매도 쪽은 credit에서 차감(255·298·329행). `_update_state`(761–797행)가 long_equity = 현금 + 시장가치 − 대출, short_equity = credit − limit − 시장가치로 다시 계산하므로 비용이 반영된다(145·215행의 state[2] 직접 차감은 이 재계산으로 덮인다). 보상 = (end − begin)·1e−4 + sharpe·penalty(457·537·540·551행), sharpe도 비용 반영 자산열로 계산(542–548행). c = 0.001(95행).
3. **평가.** 같은 env로 test·trade(139·191행).
4. **예측 S.**
5. **동적.** 서버 py310 환경(`~/f4work/mt/py310`). Mac Python 3.9.6은 env의 `match` 구문(Python 3.10+, 498행)을 못 읽는다.

## #16 Markowitz Meets Bellman (BMEgang/BellmanMarkwitzProject @93c273f)
1. **유형 R.** `draw/algo/knowledgement_drill_ddpg.py`: FinRL `DRLAgent` DDPG(125·132행 `get_model("ddpg")`, `train_model`)가 `StockTradingEnv` 보상을 쓴다. 증류 블록은 주석 처리(`notes/funnel_f4_p2407_prereg.md` 16행).
2. **경로.** FinRL @55764e8 `finrl/meta/env_stock_trading/env_stocktrading.py`: 매도 (1 − c)(118행), 매수 (1 + c)(179·188행), 보상 = end − begin(310·343·349행) × reward_scaling 1e−4(351행). 스크립트 설정 c = 0.001(104행).
3. **평가.** 같은 env로 거래(스크립트 140–145행 `e_trade_gym`).
4. **예측 S.**
5. **동적.** Mac(gym, SB3). env 파일 하나만 쓰면 된다(finrl 패키지 설치 없이 AST 추출 또는 import 스텁). 서버 F7x 환경도 가능.

## 동적 단계 준비 메모
- 서버 TF1이 필요한 대상: #1, #7, #12. 서버 쓰기는 이번 단계에서 하지 않았다. 동적 단계 전에 사용자 확인이 필요하다.
- 서버 Python 3.10이 필요한 대상: #15.
- 나머지 12개(#2–#6, #8–#11, #13, #14, #16)는 Mac 기존 환경(torch 2.6, numpy 2.0, gym 0.26, SB3 2.7, sklearn 1.6)으로 가능해 보인다. 추가로 받을 파일: FinRL `architectures.py`(#2), Ensemble env 파일(#5, 서버에서 읽기).
- 보상형 비교는 학습 루프가 받는 값으로 한다. MARS·DeepTrader 버퍼는 float32로 저장되는데, c = 0.01에서 예상 차이가 1e−12보다 훨씬 커서 판정에는 영향이 없을 것으로 본다(미확인).
