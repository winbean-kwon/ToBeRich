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

**설치 정정(2026-11-12, 실행 전, 성과 미열람):** 환경 설치는 끝났고(python 3.9.23, torch 2.0.1+cpu, gym 0.21.0, sb3 1.8.0, pyg 2.3.1), 관문에서 `policy/policy.py`의 `from model import HGAT`가 실패했다. `model/` 폴더에 `__init__.py`가 없어 `model`이 이름공간 패키지로 잡히기 때문이다(클래스는 `model/model.py`에 있음). 허용 수정 1(경로)에 하나를 더한다: `PYTHONPATH`에 `model/`을 덧붙여 `model`이 `model/model.py` 모듈로 해석되게 한다(일반 모듈이 이름공간 패키지보다 우선). 코드는 고치지 않는다. 기본 정책은 MLP라 HGAT는 import만 된다.

## 3. 시도 1(2026-11-12 16:27, 성과 미열람)
- rc 1, 4.9초. `trainer/irl_trainer.py` 136행 `data_dict['pyg_data']`에서 `KeyError: 'pyg_data'`.
- 원인 확인(데이터 구조만 봄): 번들 `dataset/data_train_predict_hs300/1_hy/*.pkl` 1,697개의 키는 corr·ts_features·features·industry_matrix·pos_matrix·neg_matrix·labels·mask이고 `pyg_data`가 없다. 첫 파일에서 `ts_features`·`features`·`labels`가 **크기 0인 빈 텐서**다. 번들 학습 데이터는 코드가 쓸 수 있는 형태가 아니다(F3 "번들" 분류 재검토 필요).
- 저자 생성 스크립트 `gen_data/train_predict_data.py`가 `pyg_data`를 포함한 pkl을 만든다(184행). 입력(`dataset/hs300_org.csv`, `dataset/corr/hs300/`, `dataset/A_stock_industry_matrx.csv`)은 저장소에 있다. 이 스크립트 실행은 2.2의 허용 수정 목록에 없으므로 사용자 결정 전에는 돌리지 않는다.

## 4. 시도 2 사전 등록(2026-11-13, 실행 전, 성과 미열람, 사용자 결정)
- **이탈(사용자 결정 2026-11-13):** 번들 학습 데이터가 쓸 수 없는 형태이므로, 저자 저장소의 생성 스크립트 `gen_data/train_predict_data.py`를 **무수정으로** 실행해 번들 원자료(`hs300_org.csv`, `corr/hs300/`, 업종 행렬)에서 학습 데이터를 다시 만든다. FinRL 계열의 "저자 다운로드 코드로 재수집"과 같은 수준으로 본다. F3 유형은 "번들"에서 **"구축 필요(저자 스크립트, 번들 원자료)"**로 재분류한다(규격은 코드가 정함 → F3 통과 규칙 충족).
- 실행 폴더: 저장소 `013e089`를 `git archive`로 `run2/code`에 풀고(원본 clone은 건드리지 않음), 생성 스크립트를 `gen_data/`에서 실행한다(스크립트가 `../dataset/` 상대 경로를 씀). 사본의 번들 pkl은 생성 결과로 덮인다.
- 생성 스크립트가 import하는 networkx 3.1·tqdm 4.66.1을 env에 더한다.
- 생성 단계 판정: rc 0이고 생성된 pkl에 `pyg_data` 키가 있어야 본 실행으로 간다. 아니면 "F4 실패(시도)"로 기록한다(stderr 마지막 40줄만). 생성 단계 상한 3시간(`timeout`).
- 본 실행·판정·상한·성과 비노출은 2절 그대로다(`main.py` 기본 설정 1회, rc 0·`main_end`·`predict_end` ≥ 1).

## 5. 결과(2026-11-13)
- **시도 2:** 저자 생성 스크립트 rc 0, 2,439.8초. 생성 pkl 1,697개에 `pyg_data` 포함(첫 파일 2018-01-03의 `features`는 여전히 크기 0 — 앞쪽 날짜의 lookback 부족으로 보이며 확인하지 않음). 이어진 `main.py`는 rc 1, 5.3초: `gen_data/generate_expert.py` 105행이 `dataset_default/data_train_predict_hs300/industry.npy`를 열다가 `FileNotFoundError`.
- `industry.npy`는 저장소에 없고, 이 파일을 쓰는 코드(`np.save`)도 저장소 어디에도 없다(`train_predict_data.py` 134행도 `../dataset/{market}/industry.npy`를 읽기만 함). 업종 행렬 CSV(`A_stock_industry_matrx.csv`)에서 만들 수는 있겠지만 형식·종목 순서를 우리가 정해야 하므로 허용 수정(v3 2.3) 밖이다.
- **판정: F4 실행 불가(필수 입력 `industry.npy` 누락, 생성 코드 없음).** 시도 3은 하지 않는다. 시도 1·2 모두 성과 출력 전 단계에서 멈췄다.
- F3 비고 갱신: 번들 학습 데이터는 빈 placeholder(`pyg_data` 없음, `features`·`labels` 빈 텐서)이고, 저자 스크립트로 구축하더라도 `industry.npy`가 빠져 있다.
