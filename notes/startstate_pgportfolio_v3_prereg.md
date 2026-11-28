# 사전 등록 v3 — PGPortfolio 원조 학습된 관성·시작 상태 효과, 기간 2017년 (2026-11-28, 실행 전)

> 기반: v1 `notes/startstate_pgportfolio_prereg.md`(e5b124c), v2 `notes/startstate_pgportfolio_v2_prereg.md`(3ff53f2). 둘 다 관문 G1(데이터 결측)에서 실패했고 성과 지표는 보지 않았다(`notes/startstate_pgportfolio_result.md`). v2 기간에서 선택된 11종목 중 ZEC(DB 시작 2016-10-28)·STRAT(2016-12-19)만 결측이 컸다. v3는 **기간만** 11종목이 모두 있는 2017/01/01–2018/01/01로 바꾸고 나머지는 v2 그대로다(패키지 별도 설치 포함, 사용자 승인).
## 고정
- 기간 2017/01/01–2018/01/01. `test_portion` 등 그 밖 설정은 기본 `net_config.json` 그대로(학습 구간 약 11개월, 시험 약 1개월).
- 관문 G1 v3: 코드가 오프라인으로 고르는 코인 각각의 close 결측 ≤ 1%. 실패하면 "실행 불가"로 끝내고 **더는 기간을 바꾸지 않는다**(v3가 마지막 판). G2·G3·측정·판정(H-I, H-S)·자원 규칙은 v2와 같다.
## 한계(추가)
- 학습 구간이 기본(약 22개월)의 절반이다. 관성이 학습되지 않았다면 그것이 짧은 학습 때문일 수 있다는 점을 함께 적는다. 반대로 관성이 학습되었다면 짧은 학습에서도 나타난 것이다.
- 코드 기본과 다른 기간이므로 논문 수치 재현이 아니다.

## 정정(실행 전, 2026-11-28 16:05 KST — G1 v3 통과 뒤, G2 중, 성과 지표 보기 전)
- 승인된 설치(`pip install --no-deps --target ~/f4work/pgss/pylib Pillow pandas==0.25.3`; Pillow 9.5.0, pandas 0.25.3, 58.5 MB)는 했다. 그러나 pandas 0.25.0부터 `pd.Panel`이 제거되어 원 코드 `globaldatamatrix.py` 72행이 `TypeError: Panel() takes no arguments`로 멈췄다(G2 첫 시도, 데이터 매트릭스 생성 단계). 버전 지정 오류다.
- 정정: 추가 설치나 네트워크 작업 없이, 서버에 이미 있는 pandas 0.24.2(`~/f4work/p37` site-packages)를 심볼릭 링크로 `~/f4work/pgss/pylib_pd`에 두고 `PYTHONPATH=pylib_pd:pylib`(pandas 0.24.2, Pillow 9.5.0, TF 1.15.4, numpy 1.16.4)로 실행한다. `~/f4work/p37`와 `adrl/p37`은 고치지 않는다. 측정·판정·기간·자원 규칙은 바뀌지 않는다.
