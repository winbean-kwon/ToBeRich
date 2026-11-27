# 공식 코드 저장소 지속성 점검 — 사전 등록 (기술 통계, 조회 전)

작성 2026-11-27. 이 문서를 커밋한 뒤에 조회한다. 판정·가설 없음: 표와 개수만 낸다. 결과를 본 뒤 모집단·측정 정의를 바꾸지 않는다.

## 1. 모집단
- 원천: `notes/lit/f1/f1_status.csv`(funnel_table.csv와 같은 id).
- 포함: F1이 `pass`, `link_dead`, `link_dead_copy`이고 `repo_or_note`에 공식 저장소(owner/repo) 또는 공식 URL이 적힌 행. 저장소 단위로 중복 제거하고 논문 id 대응은 표에 남긴다.
- 제외: `not_found`, `original_missing`, `third_party_only`(공식이 아님), `pass_tutorial`(W21_GuanLiu_XDRL: 특정 저장소가 적혀 있지 않음).
- 같은 논문에 공식 저장소가 둘이면 둘 다 넣는다: W21_FinRL → AI4Finance-Foundation/FinRL, AI4Finance-Foundation/FinRL-Meta.
- link_dead_copy(SUP-CLRS)는 논문 링크 `sophialien/FinTech-DPM`만 측정한다(사본은 소유자 미확인).
- 비 GitHub: HARLF Colab 각주 2(`https://colab.research.google.com/drive/1FPX9_8z0X39Pg3tf1bSvoByEWbbQ_juF`), SCR Zenodo DOI(`https://doi.org/10.5281/zenodo.20410374`) — HTTP 상태만.

## 2. 우리가 쓴 커밋(노트에 기록된 것만; 없으면 (d) 미측정)
| 저장소 | 커밋 | 근거 노트 |
|---|---|---|
| dmis-lab/DeepAries (T1) | 634f559 | prereg_reeval_v3.md, objective_cost_audit_static.md |
| TradeMaster-NTU/PRUDEX-Compass (T2) | 2b62831 | 같음 |
| AI4Finance-Foundation/FinRL-Meta (T3) | 286fef6 | 같음 |
| jiayiderekchen/MARS (T4) | 2561606(L), 6ca2051(N) | mars_t4_o1_prereg.md |
| Ivsxk/RAT (F7) | d1cbe96(F7 실행), 9a65269(감사) | funnel_f4_rat.md, objective_cost_audit_static.md |
| AI4Finance-LLC/…Ensemble-Strategy-ICAIF-2020 (F7) | f02a762 | funnel_f4_ensemble.md |
| saeedmarzban/waveCorr | 20ff832 | funnel_f4_wavecorr.md |
| kshre/PPN | 0210924 | funnel_f4_ppn.md |
| JingyiGu/Margin-Trader | 7b7fa9e | funnel_f4_margintrader.md |
| YinchuanLl/Reinforcement-learning-for-portfolio-allocation | 326640a | funnel_f4_li2019adaptive.md |
| AI4Finance-Foundation/…DDPG-Algorithm-NIPS-2018 | e59b994 | funnel_f4_xiong2018ddpg.md |
| ruankie/frontier-rl | e019ce4 | funnel_f4_frontier.md |
| BMEgang/BellmanMarkwitzProject | 93c273f | funnel_f4_p2407_prereg.md |
| ChloeWenyiZhang/SmartFolio | 013e089 | funnel_f4_smartfolio.md |
| DVampire/EarnMore | 810ff59 | objective_cost_audit_static.md |
| SteamerLee/MASA | d97ef0e | 같음 |
| CMACH508/DeepTrader | 4b00b2a | 같음 |
| TradeMaster-NTU/TradeMaster | 1747cc1 | 같음 |
| ZhengyaoJiang/PGPortfolio | 48cc5a4 | 같음 |
| jackieli19/PGPortfolio | a7c1333 | 같음 (비교 대상 브랜치: 논문이 가리킨 `Stock`, 기본 브랜치도 병기 가능하면 병기) |
| AI4Finance-Foundation/FinRL | 7e98df4 | 같음 |

## 3. 측정(저장소마다)
- (a) 지금 열리는가: `GET api.github.com/repos/{o}/{r}` HTTP 상태(리디렉션 따라감).
- (b) `archived` 플래그.
- (c) 기본 브랜치 최신 커밋 날짜: `https://github.com/{o}/{r}/commits/{default}.atom`의 첫 항목 날짜. 실패하면 API의 `pushed_at`으로 대신하고 그렇다고 표시.
- (d) 우리 커밋이 있으면 `GET repos/{o}/{r}/compare/{ours}...{default}` → `ahead_by`, `status`, 바뀐 경로 목록(내용은 보지 않음). 바뀐 경로 중 코드 경로(확장자 .py .sh .ipynb .yaml .yml .cfg .toml, 또는 이름이 requirements*) 수. "우리가 돌린 파일" 변경 여부는 아래 지정 경로가 목록에 있는지로 본다:
  - RAT: `main.py`, `run_main.sh` 및 저장소 전체 코드 경로
  - Ensemble: `run_DRL.py`, `model/models.py`, `env/EnvMultipleStock_{train,validation,trade}.py`, `preprocessing/preprocessors.py`, `config/config.py`
  - T2: `AlphaMix+/PM/` 아래 코드 경로. T3: 경로에 `env_portfolio_yahoofinance`가 들어간 파일 및 `meta/data_processors/` 아래 코드 경로.
  - 그 밖: 저장소 전체 코드 경로(지정 파일 목록이 노트에 없으므로).
  - compare 응답 파일 목록은 최대 300개로 잘린다 — 잘리면 표시한다.
- (e) 기록된 URL `https://github.com/{o}/{r}`의 `curl -sI` 상태와 `Location`(다른 곳으로 리디렉션되는지). 논문에 링크가 없던 저장소(저자 계정에서 찾은 것)도 같은 방식으로 재되 그 점을 표에 표시.

## 4. 도구·제약
- `gh` CLI가 이 맥에 없다 → 인증 없는 `curl`로 api.github.com 호출(User-Agent `generic-client`, 개인정보 없음). 시간당 60회 한도 안에서 저장소당 repos 1회 + compare 커밋당 1회. 404 저장소는 compare 생략. 한도에 걸리면 남은 항목을 "미측정(한도)"으로 적고 재시도는 한도 리셋 뒤 같은 절차로 한다.
- 클론·설치·ssh 없음. 파일 내용·성과 파일은 열지 않는다.

## 5. 산출
- `notes/repo_durability_result.md`: 표 + 개수(열림, archived, 우리 커밋 이후 기본 브랜치 변경 있음, 우리가 돌린 파일 변경 있음).
- `replication/repo_durability.json`: 원자료(상태·플래그·날짜·ahead_by·바뀐 경로).
- 해석·판정 문장 없음. 6장 판정과 관련된 사실(예: MARS 저자 수정본은 이미 알려짐)만 사실로 적는다.
