# F4 HARLF 기록 (논문 각주 2 Colab 노트북)

프로토콜 `notes/funnel_protocol.md`. 대상: Coriat et al., "HARLF: Hierarchical Reinforcement Learning and Lightweight LLM-Driven Sentiment Integration for Financial Portfolio Optimization", arXiv 2507.18560 v1(IJCAI 2025 FinLLM Workshop). 정적 층 순서 14(S56, F1 정정 2026-11-12). F7 자리가 차서 **F4까지만**. 맥 병행 이탈은 `notes/funnel_f4_margintrader.md` 0절·프로토콜 3.3 이탈 기록과 같다.

## 1. 코드 읽기(정적, 2026-11-12)
- 논문 3.4절 각주 1·2·3이 Colab 노트북 3개를 가리킨다. 학습·평가 코드는 **각주 2**(`1FPX9_8z0X39Pg3tf1bSvoByEWbbQ_juF`, "Fast Simulated RL Run", 논문 표기 "typically under 30 minutes")에만 있다. 각주 1·3은 뉴스 스크래핑·FinBERT 감성 추출이며 학습 코드가 없다(각주 3은 논문 설명과 달리 12셀, 사용자 확인).
- 각주 2 노트북(Drive에서 받은 파일 sha256 2552debf…d423, 셀 78개 중 코드 셀): yfinance로 14자산(지수·원자재) 2003-01-01~2024-12-31 종가를 받고, 월별 관측 벡터(변동성·상관 등)를 만들고, **감성 14개를 `np.random.uniform(-1,1,14)`로 시뮬레이션**한다. 하위 에이전트(SB3 PPO·SAC·DDPG·TD3, 시드 1–5, metrics·NLP 두 관측, `total_timesteps` 10,000) → 메타 에이전트(PPO 20,000) → 슈퍼 에이전트(PPO 1,000) → 백테스트 정리(`ALL_BACKTEST/`)·그림.
- 첫 코드 셀이 작업 폴더의 파일을 모두 지운다(`delete_all_except(os.getcwd())`). 빈 폴더에서 실행해야 한다.
- 여러 셀이 예외를 잡아 출력만 하고 넘어가므로, 종료 코드만으로는 끝까지 됐는지 알 수 없다.

## 2. F4 사전 등록(2026-11-12, 실행 전, 성과 미열람)

### 2.1 실행 단위
- 각주 2 노트북의 코드 셀 전체를 Colab "모두 실행"처럼 순서대로, 한 이름공간에서 1회 실행한다. 예외가 나면 그 셀에서 멈춘다(Colab 모두 실행과 같은 동작). 감성은 노트북 그대로 시뮬레이션이다(실제 감성 연결 코드는 공개되지 않음, F2 비고).
- 노트북의 셸 줄 3개(`!pip install --upgrade ipywidgets`, `!pip install --upgrade yfinance`, `!pip install stable_baselines3[extra]`)만 빼고, 같은 패키지를 env에 미리 설치한다. 그 밖의 코드는 한 글자도 바꾸지 않는다.

### 2.2 환경(맥 M1, CPU)
- Python 3.11(conda-forge; 2025년 Colab 기본과 같은 계열).
- 노트북이 고정하지 않은 패키지는 노트북 시점(2025년 중반) Colab 기본값에 가깝게 고정한다: pandas 2.2.2, numpy 2.0.2, matplotlib 3.10.0, stable-baselines3[extra] 2.7.0, gymnasium 1.2.0, seaborn 0.13.2, torch 2.15.0(macOS arm64 휠). 노트북이 `--upgrade`로 설치하는 yfinance는 최신(1.8.0)을 쓴다(지금 Yahoo에서 받히는 판).
- 허용 수정(v3 2.3): 없음. 그림 백엔드 `MPLBACKEND=Agg`, 사용자 site 차단 `PYTHONNOUSERSITE=1`.

### 2.3 판정
- **F4 통과:** rc = 0, 모든 코드 셀 정상 종료(`all_done`), 그리고 `ALL_BACKTEST/ROI.csv`·`ALL_BACKTEST/portfolio_value.csv`·`ALL_BACKTEST` 아래 슈퍼 에이전트 CSV가 존재. 존재만 확인하고 열지 않는다. 표기: "노트북 2 전체 1회, 감성 시뮬레이션".
- **F4 실패:** 그 밖. 멈춘 셀 번호와 traceback 마지막 12줄만 기록한다(성과 줄이 섞이면 옮기지 않는다). 허용 수정 범위 안에서 고칠 수 있으면 고쳐 최대 3회.
- **상한:** 1회 벽시계 3시간. 넘으면 "상한 내 미완".
- **성과 비노출:** 표준출력, 결과 CSV, 그림, 노트북에 저장된 원 출력은 열지 않는다. F7 대상이 아니라 성과를 쓰지 않는다.
- 데이터는 실행 시점 yfinance 재수집이다(F3 "재수집").

스크립트: `replication/funnel_f4_harlf_mac.py`(이 절과 같은 커밋). 노트북 파일은 성과 출력이 들어 있어 저장소에 넣지 않고 맥 `~/f4mac/harlf/nb2.ipynb`(sha256 고정)로 둔다.

## 3. 결과(2026-11-12)
- **F4 통과(노트북 2 전체 1회, 감성 시뮬레이션).** 시도 1: rc 0, 코드 셀 44/44 정상 종료, 표지 `ALL_BACKTEST/ROI.csv`·`portfolio_value.csv`·슈퍼 에이전트 CSV 모두 존재. 5,091초(1.41시간, 맥 M1 CPU). 논문 3.4절의 "typically under 30 minutes"(Colab 기준)보다 길다. 장치 차이가 있어 비교하지 않는다.
- 한계: 여러 셀이 예외를 잡아 출력만 하고 넘어가므로, "모든 셀 정상 종료 + 최종 표지 존재"가 중간 단계(예: 특정 시드·알고리즘)의 실패가 없었음을 보장하지 않는다. 표준출력을 열지 않았으므로 중간 오류 메시지 유무는 확인하지 않았다.
- 성과 파일·표준출력은 열지 않았다. 기록: `~/f4mac/out/harlf/attempt1.json`·`done.json`(맥 로컬).
