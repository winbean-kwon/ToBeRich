# AlphaMix+ 실행 가능성 파일럿 결과 (T2)

노트북 `replication/alphamix_pilot.ipynb`. 공식 코드 TradeMaster-NTU/PRUDEX-Compass @2b62831 `AlphaMix+/PM`, 호환 shim 4개(노트북 첫 셀, v3 2.3 (1))만 적용.
원자료: Drive `data/alphamix_pilot/` → 저장소 `replication/alphamix_pilot/`(A_data.log, B_train_seed12345.log, B_result.csv). 학습은 2026-10-27, 데이터 단계는 2026-10-29에 다시 실행됨(같은 출력).

## 기록(판정 아님)
- 환경: Colab GPU(T4), Python 3.13. 설치·임포트 오류 없음.
- 데이터: Yahoo에서 받은 dj30 목록 중 WBA 다운로드 실패("possibly delisted") → 28종목, 71180행.
  분할 train 2012-01-03~2019-12-31, valid 2020-01-02~2020-12-31, test 2021-01-04~2021-12-31. 비용률 0.001.
- 학습 1회(시드 12345, 10 epoch): 1238초 ≈ 20.6분.
- epoch 10 테스트 TR 19.55%, SR 1.61. 논문 Table 5 US 2021(시드 5개 평균): TR 20.7 ± 1.8%, SR 1.64. 시드 1개라 비교하지 않는다.
- epoch별 테스트 TR 15.8~22.5%, 검증 TR 최고 epoch는 2(테스트 TR 22.5%).

## 실행 가능성
- 디버깅 상한(8시간) 안에서 허용 수정(shim 4개)만으로 실행됨 → v3 1.1 기준 '실행 불가' 아님. T2 = AlphaMix+로 확정.

## 남은 문제(O1 실행 전에 해결)
- **데이터 스냅샷이 아직 고정되지 않았다.** 노트북은 실행마다 Yahoo에서 다시 받으며, 받은 데이터를 Drive에 저장하지 않았다. v3 1장은 "파일럿 때 받은 스냅샷을 Drive에 저장해 고정"이라 했으므로, O1 노트북은 먼저 데이터를 한 번 받아 해시와 함께 저장하고 이후 실행은 그 파일만 쓰게 해야 한다(파일럿 시점 데이터와 같다는 보장은 없음 — 한계로 적음).
- WBA 누락(28종목)은 T3의 A1과 같은 성격이다. 논문 종목 수와 다를 수 있다.
