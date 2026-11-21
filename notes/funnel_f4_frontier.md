# 깔때기 FRONTIER 기록 (W22_PretoriusVanZyl, ruankie/frontier-rl)

대상: Pretorius & van Zyl, "Deep Reinforcement Learning and Convex Mean-Variance Optimisation for Portfolio Management", arXiv:2203.11318(TechRxiv 10.36227/techrxiv.19165745.v1, IEEE TAI 양식, 출판 미확인). 표본 S56. 프로토콜 `notes/funnel_protocol.md`.

## 0. 이탈 기록(2026-11-21, 정적 단계 시작 전, 성과 미열람)
- **F1:** 원래 판정 `not_found`(Claude, 본문만 확인하고 1저자 GitHub를 확인하지 않음). F1 재확인에서 사용자가 1저자 계정 저장소 `github.com/ruankie/frontier-rl`을 찾았다(`notes/lit/f1/f1_recheck_log.md`). 층 1 거짓 음성이다.
- **사전 등록 이탈:** `notes/f1_recheck_prereg.md`의 "미통과가 통과로 바뀐 논문은 후속 단계(F2 이후)를 이번 일정에서 실행하지 않는다"에서 이탈한다. 사용자 결정(2026-11-21)이다. 이유: 연구 질문이 공개 코드로 보고 수치 재현을 시도하는 것이고, 다른 작업과 병행할 수 있다. 이 이탈은 이 논문이 어떤 성과를 내는지 보기 전에 정했다.
- **집계 처리:** 프로토콜 3.3의 F7 두 자리(Ensemble, RAT)는 이미 찼다. 이 논문의 F2 이후 결과는 **탐색적(F1 재확인 후 추가, 프로토콜 3.3 밖)**이다. 깔때기 표에는 "F1 재확인에서 찾음"으로 적고 후속 단계는 탐색적 비고로만 적는다. F1 재확인의 주 지표 계산은 이 결과와 무관하다.
- **이미 본 정보(2026-11-21):** 원문의 표는 Table I(시장 데이터)과 Table II(Yang et al. 2020의 DDPG·PPO·A2C를 선형·비선형 거래비용으로 비교: 초과수익률·초과위험·Sharpe)뿐이다. 제안 모델 FRONTIER의 성과는 그림(파레토 프런티어)에만 있다. 저장소 커밋 메시지 목록을 보았다(`aaf09ac` "reproduced findings for long-only policy" 등). 저장소의 `experiments/*/backtests/*.csv`(저자 실행 결과)는 열지 않았다.
- **성과 비노출:** 저장소의 `experiments/` 아래 결과 파일과 노트북 출력 셀은 열지 않는다(저자 결과 노출 방지). 코드 셀만 읽는다. 우리 실행의 성과는 F7 사전 등록 전에는 열지 않는다(프로토콜 2.2).

## 1. 정적 단계(F2·F6·F3)
(작성 중)
