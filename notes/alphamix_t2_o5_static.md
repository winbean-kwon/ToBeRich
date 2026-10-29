# T2 AlphaMix+ env O5 — 코드 읽기 예측

대상 `PRUDEX-Compass @2b62831 AlphaMix+/PM/rl_env/portfolio_management.py` `TrainEnv`.
**주의:** 이 문서는 구현 시험 실행(`notes/alphamix_t2_o1_prereg.md` 5장) 뒤에 커밋한다. 그래서 읽기 오류율 측정에는 쓰지 않고, 코드 근거 기록으로만 둔다.

| 점검 | 예측 | 근거(행) |
|---|---|---|
| C1 | **설정됐지만 부과 안 됨**: 보상열·수익열 모두 c와 무관 | `transaction_cost_pct`는 26행에서 읽기만 한다. `step`(56–132행)의 수익은 `np.sum((close_t/close_{t−1} − 1) * weights[:, 1:])`이고 비용 항이 없다. config는 947·958·970행에서 0.001이다 |
| C2 | 일치 | `reward = (new_value − value) * reward_scaling`(115·127행), reward_scaling = 1e−4(952·963·975행) |
| C3 | 기록 | reset 때 가치는 1e6이다. `actions_memory[0] = 1/stock_dim`이지만 계산에 쓰이지 않는다. 관측은 11개 지표 × 종목(42·105행)으로 직전 보유가 없다. 학습·검증·테스트가 같은 `TrainEnv`를 쓴다 |
| S1 | 측정 비용 0 → 비율 0 | C1과 같다 |
| 시점 | 행동 a_t → softmax 가중치가 다음 날 close 수익에 적용 | 95–111행. 현금이 행동 0번이고 수익 0이다 |

**U1 규칙상 결과:** C1을 통과하지 못하면 O2의 평가와 조건 (b)(c) 학습은 참조 명세 U1으로 교체한다. 저장 행동이 있고 관측에 보유가 없으므로(무상태), 평가는 저장 행동으로 사후 계산할 수 있다. 조건 (b)(c) 학습은 env 교체가 필요하며, O2 노트북에서 따로 고정한다.
