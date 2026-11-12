# F4 SmartFolio 기록 (ChloeWenyiZhang/SmartFolio @013e089)

프로토콜 `notes/funnel_protocol.md`. 대상: SmartFolio(IJCAI 2025, S-Q). 정적 층 `notes/lit/f1/static_layer.csv` 순서 10. F7 자리가 차서 **F4까지만**. 서버 대기열에서 xiong2018 다음에 실행한다(맥은 디스크 부족, 저장소 667MB).

## 1. 코드 읽기(정적, 2026-11-12)
- 저장소는 커밋 1개(`013e089`, 2025-02-12). README·requirements 없음. 번들 데이터 `dataset/`(hs300 등, `data_train_predict_hs300/1_hy` 1,697개 pkl).
- `main.py`: 인자를 받지만 `__main__`에서 모두 덮어쓴다(hs300, hy, 학습 2019-01-02~2022-12-30, 검증 2023, 시험 2024-01-02~2024-12-30, batch 32, `max_epochs` 60, seed 123, 102종목, 다중 보상). 장치는 CUDA가 있으면 GPU, 없으면 CPU. 데이터 경로는 `dataset_default/...`인데 저장소 폴더는 `dataset/`이다(정적 층 비고 그대로).
- `trainer/irl_trainer.py`의 `train_model_and_predict`: 전문가 궤적 10,000개 생성 → MaxEnt IRL 보상망 → 외곽 반복 `for i in range(max_epochs)` 안에서 IRL 학습(`num_epochs=max_epochs`) 후, 학습 배치마다 env를 새 보상으로 만들고 PPO `learn(10000)` → `evaluate_policy` → `model_predict(test)`. **`return trained_model`이 외곽 반복 안에 있어 외곽 반복은 1회만 돈다**(코드 판독, 정적). 따라서 기본 실행이 곧 "학습 1회 + 배치마다 시험 예측" 경로다.
- `model_predict`는 시험 지표를 출력만 하고 파일을 남기지 않는다.
- env는 옛 `gym` API(`reset()`이 관측만 반환, `seed()` 메서드)를 쓴다 → stable-baselines3 1.x(gym 0.21)와 맞는다.

## 2. F4 사전 등록(2026-11-12, 실행 전, 성과 미열람)

### 2.1 환경(서버 WSL2 CPU)
- Python 3.9(conda-forge), torch 2.0.1 CPU, numpy 1.23.5, pandas 1.5.3, scipy 1.10.1, scikit-learn 1.2.2, gym 0.21.0(빌드를 위해 pip<24·setuptools 65.5.0·wheel 0.38.4), stable-baselines3 1.8.0, torch_geometric 2.3.1. 저장소에 버전 기록이 없어, 코드가 요구하는 API(gym 구 API·SB3 1.x·`torch_geometric.loader`)를 만족하는 2023년 판으로 고정한다.
- 장치: CPU(`CUDA_VISIBLE_DEVICES=""`). RAT F7이 끝난 뒤라 GPU가 비어 있어도, 서버 F4는 CPU로 통일한다.

### 2.2 허용 수정(v3 2.3)
1. **경로:** 저장소 안에 `dataset_default → dataset` 심볼릭 링크를 둔다. 추적 파일은 고치지 않는다(실행 전 `git diff --quiet` 확인).
2. **결과 기록(2.3-4):** 실행 래퍼가 `trainer.irl_trainer.model_predict` 호출의 시작·끝 시각만 이벤트로 남긴다(함수 동작은 그대로). 저자 `main.py`는 `runpy`로 그대로 실행한다.

### 2.3 판정
- **F4 통과:** rc = 0, `main_end` 이벤트, 시험 예측 완료(`predict_end`) ≥ 1회.
- **F4 실패:** 그 밖. stderr 마지막 40줄만 연다(예측 지표는 stdout으로만 나감). 허용 수정 범위 안에서 고칠 수 있으면 고쳐 최대 3회. 설치 실패는 본 실행 시도로 세지 않는다.
- **상한:** 1회 벽시계 3시간. 넘으면 "상한 내 미완"이고, 그때까지 끝난 시험 예측 횟수를 함께 적는다(≥1이면 학습·평가 경로가 적어도 한 번 끝까지 돈 것).
- **성과 비노출:** stdout(예측 지표 print), 모델 파일을 열지 않는다. F7 대상이 아니다.

스크립트: `replication/funnel_f4_smartfolio_local.py`, 순서: `replication/funnel_f4_after_xiong.sh`(xiong2018 F4가 끝난 뒤 실행).
