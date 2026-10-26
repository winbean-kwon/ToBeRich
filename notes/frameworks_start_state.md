# 공개 RL 포트폴리오 프레임워크의 평가 시작 상태 점검 (F)

확인일 2026-10-26. 모든 판정은 아래 커밋의 원본 코드를 raw.githubusercontent.com에서 내려받아 직접 읽은 결과다. 줄 번호는 해당 커밋 기준이다.
- FinRL `7e98df461cbc7772f16a545a2f13b521e5d0b8f4`
- PGPortfolio `48cc5a4af5edefd298e7801b95b0d4696f5175dd`
- TradeMaster `1747cc18db3fe2639af12defc80e138c51a625c0`
- wassname/rl-portfolio-management `e73339ffb51739b2881fa234363ed336bc74f5a2`

## 요약 표

| 프레임워크 / 환경 | reset 때 초기 보유 | 정책이 직전 보유를 입력으로 받는가 | 첫 리밸런싱에 비용을 매기는가 | 테스트도 같은 reset을 쓰는가 | 판정 |
|---|---|---|---|---|---|
| FinRL `StockPortfolioEnv` | `actions_memory`만 EW이고 수익 계산에는 쓰이지 않음 | 아니오 | 아니오. `transaction_cost_pct`는 저장만 하고 쓰지 않음 | 예 (`day=0`) | **편향 가능성 낮음.** 무기억 정책에 비용도 없음 |
| FinRL `PortfolioOptimizationEnv` + EIIE/PVM | **현금 100%** `[1,0,…,0]` | 예. `return_last_action=True`이면 관측에 들어가고, EIIE `mu(obs, last_action)`에는 항상 들어감. 테스트 PVM도 현금으로 초기화 | 예 (TRF/WVM, `last_weights`가 현금) | 예 (`test()`에서 `reset()`과 `test_pvm.reset()`) | **편향 가능** (현금에서 출발하고 직전 가중치를 입력받으며 비용이 있음) |
| PGPortfolio (EIIE, Jiang+ 2017) | 백테스트 `_last_omega` = **현금(BTC) 100%** | 예 (`previous_w` 입력, PVM) | 예 (`calculate_pv_after_commission(omega, _last_omega)`) | 해당 없음 (백테스트 1회가 곧 테스트) | **편향 가능.** 학습 때 PVM은 코인 EW로 초기화되어 테스트 시작 상태(현금)와 다름 |
| TradeMaster `PortfolioManagementEnvironment` (기본) | 현금 100% | 아니오 (관측은 기술지표뿐) | 예. 첫 스텝은 현금에서 목표 가중치로 옮기는 비용 | 예 | **편향 가능성 낮음.** 첫날 수수료 한 번뿐 |
| TradeMaster `PortfolioManagementEIIEEnvironment` | **EW** `1/(N+1)` (현금 포함). `__init__`에서는 현금이라 둘이 다름 | 아니오 (원 논문 EIIE와 달리 직전 가중치 입력 없음) | 예 (EW에서 옮기는 비용) | 예 (`test()`에서 `reset()`) | **편향 가능성 낮음.** 첫 스텝 비용 한 번뿐 |
| TradeMaster DeepTrader env | EW `1/N` (현금 없음) | 아니오 (환경 관측 기준) | 예 | 예 | **편향 가능성 낮음.** 단 DeepTrader 에이전트 내부 상태는 확인하지 않음 |
| TradeMaster Investor-Imitator env | EW `1/N`. 관측의 `s_history_action`도 EW | **예** (`weights_memory[-1]`을 관측에 넣음) | 예 | 예 | **편향 가능** (EW 시작이고 직전 가중치를 관측함) |
| wassname `PortfolioEnv` (gym) | 현금 100%. reset이 현금 행동으로 한 스텝을 먼저 실행 | 예 (관측 `weights`) | 예 (`c1 = cost·Σ|dw1−w1|`) | `random_reset=True`이면 무작위 시점에서 시작하고, 꺼도 같은 reset을 씀 | **편향 가능** |

어느 프레임워크에도 정책 고유의 보유를 만들기 위한 **보유 워밍업/번인은 코드에 없다.** 시작 시점을 미루는 것(`time_window-1`, `time_steps-1`)은 가격 lookback 창을 채우려는 것일 뿐, 보유를 안정 상태로 맞추는 장치가 아니다.

---

## 1. FinRL

### 1a. `finrl/meta/env_portfolio_allocation/env_portfolio.py` (StockPortfolioEnv)
https://github.com/AI4Finance-Foundation/FinRL/blob/7e98df461cbc7772f16a545a2f13b521e5d0b8f4/finrl/meta/env_portfolio_allocation/env_portfolio.py
- reset (L203–226): `self.day = 0`, `self.portfolio_value = self.initial_amount`, `self.actions_memory = [[1 / self.stock_dim] * self.stock_dim]` (L224). `# self.cost = 0`은 주석 처리돼 있다.
- step (L167–189): `weights = self.softmax_normalization(actions)`, `portfolio_return = sum(((close_t/close_{t-1}) - 1) * weights)`. 직전 보유나 비용은 쓰지 않는다. `transaction_cost_pct`는 L89에서 대입만 한다.
- 관측: 공분산 행렬과 기술지표(L214–218)뿐이고 가중치는 없다.
- 판정: **편향 가능성 낮음.** 매 스텝 가중치를 새로 정하므로 보유가 경로에 의존하지 않고 비용도 없다. 초기 EW는 기록용이다.

### 1b. `finrl/meta/env_portfolio_optimization/env_portfolio_optimization.py` (PortfolioOptimizationEnv)
https://github.com/AI4Finance-Foundation/FinRL/blob/7e98df461cbc7772f16a545a2f13b521e5d0b8f4/finrl/meta/env_portfolio_optimization/env_portfolio_optimization.py
- reset (L371–401): `self._time_index = self._time_window - 1` (lookback용), `_reset_memory()`.
- `_reset_memory` (L533–553): `# initial action: all money is allocated in cash`, `_actions_memory = [np.array([1] + [0]*portfolio_size)]`, `_final_weights = [np.array([1] + [0]*portfolio_size)]`.
- step (L296–333): `last_weights = self._final_weights[-1]`. 비용 모델 `trf`(기본, L321–333)은 `mu`를 `np.maximum(last_weights[1:] - mu*weights[1:], 0)`로 계산하고, `wvm`(L308–320)은 `fees = sum(|weights - last_weights|·PV)`다. 따라서 첫 스텝에서 현금에서 목표로 옮기는 비용을 낸다. 기본값은 `comission_fee_pct=0`(L82)이라 비용을 켜야 효과가 생긴다.
- 관측: `return_last_action=True`면 `{"state", "last_action": _actions_memory[-1]}`(L565–567)이고, 첫 관측의 last_action은 현금이다.
- 에이전트: `finrl/agents/portfolio_optimization/utils.py` L24–27의 `PVM.reset()`은 `[1,0,…,0]`을 채운다. `architectures.py` L63의 `EIIE.mu(observation, last_action)`. `algorithms.py` L196–208 `test()`: `obs = self.test_env.reset()`, `self.test_pvm.reset()`, `last_action = self.test_pvm.retrieve()`, `action = self.test_policy(obs_batch, last_action_batch)`.
- 판정: **편향 가능.** 평가가 현금 100%에서 시작하고, 정책은 직전 행동을 입력받으며 비용도 인식하도록 학습된다(loss에 `trf_mu`). 정책 출력이 직전 가중치에 의존하므로 초기 며칠의 노출이 정상 상태와 다를 수 있다. 방향은 우리 사례(EW 시작으로 과대 노출)와 반대로 현금 시작이라 과소 노출 쪽이다. 실제 크기는 측정하지 않았다.

## 2. PGPortfolio (Jiang, Xu, Liang 2017)
- `pgportfolio/trade/trader.py` L42–43: `self._last_omega = np.zeros((self._coin_number+1,))`, `self._last_omega[0] = 1.0`. 즉 **BTC(현금) 100%**에서 시작한다.
  https://github.com/ZhengyaoJiang/PGPortfolio/blob/48cc5a4af5edefd298e7801b95b0d4696f5175dd/pgportfolio/trade/trader.py#L42-L43
- L91–92: `omega = self._agent.decide_by_history(self.generate_history_matrix(), self._last_omega.copy())`
- `pgportfolio/learn/nnagent.py` L203–213: `decide_by_history`가 `self.__net.previous_w: last_w[np.newaxis, 1:]`을 넘긴다. `network.py` L97/L107–108은 `previous_w`를 네트워크에 concat한다(EIIE의 PVM 입력).
- `pgportfolio/trade/backtest.py` `trade_by_strategy`: `pv_after_commission = calculate_pv_after_commission(omega, self._last_omega, self._commission_rate)`, `self._last_omega = pv_after_commission*omega*future_price/portfolio_change`. 즉 첫 스텝에 현금에서 목표로 옮기는 수수료를 내고, 이후에는 가격 변동으로 드리프트된 가중치를 다음 입력으로 쓴다.
- 학습 PVM은 `pgportfolio/marketdata/datamatrices.py` L56–58에서 `self.__PVM.fillna(1.0 / self.__coin_no)`, 즉 비현금 코인 EW로 채워지고, 학습 중에 `setw`로 갱신된다(L161–164). **학습 때의 초기 직전 가중치(코인 EW)와 테스트 시작(현금)이 서로 다르다.**
- 판정: **편향 가능.** 직전 가중치를 입력받고 비용을 인식하는 정책이 현금이라는 임의 상태에서 출발하며 첫 거래에 수수료를 낸다. 관성 계수가 없으므로 영향은 우리 사례(α=0.01)보다 짧게 지속될 것으로 보이지만 측정하지 않았다.
- 논문: Jiang et al. 2017(arXiv:1706.10059)에 초기 가중치를 `w_0 = (1,0,…,0)`(전액 현금)으로 둔다는 서술이 있는 것으로 기억하지만, **이번에 원문으로 확인하지는 않았다.** 워밍업이나 번인 언급도 확인하지 못했다.

## 3. TradeMaster (`trademaster/environments/portfolio_management/`)
기준 링크: https://github.com/TradeMaster-NTU/TradeMaster/tree/1747cc18db3fe2639af12defc80e138c51a625c0/trademaster/environments/portfolio_management
- `environment.py`: `reset` L77–94에서 `self.weights_memory = [[1] + [0] * self.stock_dim]`(현금). step L125–158: `weights = self.softmax(actions)`, 수수료는 `diff_weights = Σ|weights_memory[-3] - weights_memory[-2]|`, `transcationfee = diff_weights * transaction_cost_pct * portfolio_value`. 첫 스텝의 [-3]은 초기 현금이므로 현금에서 목표로 옮기는 수수료가 붙는다. 관측은 기술지표뿐이다(L131–135).
- `eiie_environment.py`: `__init__` L83은 현금 `[1]+[0]*N`인데 `reset` L102–103은 `[[1 / (self.stock_dim + 1)] * (self.stock_dim + 1)]`(EW)로 **서로 다르다.** 관측은 기술지표 창이고 가중치는 없다(L95–96). 수수료 계산은 위와 같다(L174–178).
- `deeptrader_environment.py`: reset L91 `[[1 / (self.stock_dim)] * (self.stock_dim)]`(현금 없는 EW), 수수료 계산은 같다(L143–147).
- `inverstor_imitator_environment.py`: reset의 `s_history_action = [1/len(tic_list)]*len(tic_list)`(L131, L189)가 관측에 들어가고, step L333은 `s_history_action = list(self.weights_memory[-1])`이다. **관측에 직전 가중치가 들어가는 유일한 TradeMaster 환경이다.**
- `sarl_environment.py`: reset L129 EW `1/action_space_shape`.
- 테스트: `trademaster/trainers/portfolio_management/eiie_trainer.py` L195 `state = self.test_environment.reset()`, 이후 `get_action = self.agent.act`로 상태만 입력한다. 학습과 같은 reset을 쓴다.
- 판정: 기본, EIIE, DeepTrader, SARL은 **편향 가능성 낮음.** 정책이 직전 보유를 보지 않으므로 효과는 첫 스텝 수수료 한 번(최대 약 2×0.1%)이다. Investor-Imitator는 **편향 가능**(EW 시작이고 직전 가중치를 관측함). DeepTrader와 Investor-Imitator 에이전트의 내부 순환 상태는 **확인하지 않았다.**

## 4. 기타
### wassname/rl-portfolio-management `rl_portfolio_management/environments/portfolio.py`
https://github.com/wassname/rl-portfolio-management/blob/e73339ffb51739b2881fa234363ed336bc74f5a2/rl_portfolio_management/environments/portfolio.py
- `PortfolioSim.reset` L202–205: `self.w0 = np.array([1.0] + [0.0]*len(self.asset_names))`. `PortfolioEnv._reset` L344–350은 `action = self.sim.w0`로 한 스텝을 실행한 뒤 첫 관측을 돌려준다.
- `_step` L154–177: `c1 = self.cost * (np.abs(dw1[1:] - w1[1:])).sum()`이고 `dw1`은 직전 가중치가 드리프트한 값이다. `p1 = p0*(1-c1)*np.dot(y1, w0)` 다음 `self.w0 = w1`. 이번 행동은 다음 기간 수익에 반영되고, 첫 이동에는 비용이 붙는다.
- 관측: `{'history': history, 'weights': weights}` (L342).
- `DataSrc.reset` L108–110: `random_reset=True`(기본)이면 무작위 시점에서 시작한다. 평가 시작 시점은 사용자 설정에 달려 있다.
- 판정: **편향 가능.** 현금에서 출발하고 직전 가중치를 관측하며 첫 이동에 비용이 붙는다.

### 확인하지 않은 것
- FinRL-Meta: FinRL과 같은 계열의 환경 사본으로 알려져 있으나 **코드를 확인하지 않았다.**
- Qlib RL: 주로 주문 집행(order execution)용이고 포트폴리오 RL 환경은 **확인하지 않았다.**
- DeepTrader 원 저장소, 논문 본문의 워밍업 언급: **확인하지 않았다.**

## 워밍업/번인 언급
- 확인한 코드와 docstring 어디에도 보유를 정상 상태로 맞추기 위한 워밍업이나 번인은 없다. FinRL PortfolioOptimizationEnv docstring은 "time_index must start a little bit in the future to implement lookback"(L392)이라고 하는데, 이는 가격 창을 채우기 위한 것이다.
- 확인한 모든 환경이 평가를 **현금 100% 또는 EW라는 임의 보유**에서 시작한다. 이 가운데 직전 가중치를 정책 입력으로 쓰는 FinRL POE+EIIE, PGPortfolio, TradeMaster Investor-Imitator, wassname은 우리가 찾은 시작 상태 편향의 조건 (a)와 (b)를 구조적으로 모두 만족한다. 다만 우리 정책처럼 α=0.01 수준의 명시적 관성은 어디에도 없으므로, 편향의 지속 기간과 크기는 훨씬 작을 가능성이 높다(**측정하지 않은 추정**).
