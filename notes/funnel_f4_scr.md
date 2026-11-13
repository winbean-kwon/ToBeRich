# F4 SCR 기록 (edrtfu531/rlscr1 @6e7330c) — 미시험

프로토콜 `notes/funnel_protocol.md`. 대상: Bendatu, Lu, "Reinforcement Learning with Scenario-Context Rollout in Portfolio Management", KDD 2026(S-Q). 정적 층 순서 13. F7 자리가 차서 F4까지만.

## 확인 내용(2026-11-13, 정적, 성과 미열람)
- 저장소 246MB. README가 데이터 출처와 빌드 순서(수익률 패널 → Fed 신호(FinBERT) → 충격 지수 → Tier1 → Tier2·ShockLedger → 매핑 → 시나리오(ABM) → 롤링 매퍼 → CCM 학습 `code/src/ccm/run_ccm.py`)를 적는다. 제3자 데이터는 재배포하지 않는다고 명시한다.
- 학습 설정 `code/code/output/configs/config_seed_0.yaml`이 읽는 입력 8개 중 번들된 것은 4개(`pred_rem.csv`, `pred_train.csv`, `edges_rem.csv`, `edges_train.csv`)다. 없는 것은 수익률 패널(`returns_run_00_market_proxy.csv`), 시나리오 문맥(`scenario_context.csv`), 롤링 충격(`r_tilde_online.csv`, `betas_online.csv`)이다.
- 이를 만들려면 다음 제3자 자료를 직접 모아야 한다. 코드는 형식(파일 이름·열)만 정한다.
  - FNSPID 종목별 가격(Hugging Face `Zihan1004/FNSPID`, `full_history/<티커>.csv`, 수 GB).
  - FRED 시리즈(BAMLH0A0HYM2, DGS10(와 2Y), DTWEXBGS, DCOILWTICO, DCOILBRENTEU, VIXCLS, EPU 등).
  - FOMC 성명서 2008-08 이후(`YYYYMMDD.txt`, 연준 웹사이트). **수집 코드가 저장소에 없다.**
  - GPR 지수(`data_gpr_export.csv`), FinBERT 사전 학습 모델.

## 판정
**F4 미시험(입력 구축 규모, 사용자 결정 2026-11-13).** 학습 입력의 절반을 제3자 자료로 구축해야 하고 그중 FOMC 성명 수집은 우리가 새 코드를 써야 한다(v3 2.3 허용 수정 밖으로 볼 여지). 예상 작업량(반나절~하루)이 F4 전용 대상(성과를 쓰지 않음)에 비해 크다고 보고 실행하지 않는다. "실행 불가"가 아니라 "미시험"으로 집계한다(재현 실패와 합치지 않음, 프로토콜 4절).
