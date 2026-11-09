# F4 EIIE 기록 (ZhengyaoJiang/PGPortfolio) — 데이터 입수 불가로 중단

프로토콜 `notes/funnel_protocol.md`. 대상: Jiang, Xu, Liang, "A Deep Reinforcement Learning Framework for the Financial Portfolio Management Problem"(EIIE, arXiv 1706.10059). 순서상 Practical DRL 다음이다(3.3, `notes/lit/f1/static_layer.csv` 순서 8). 코드는 "기지"(이미 비용·매개화를 읽은 대상, `notes/prereg_code_audit.md` 1행·`notes/code_audit_static.md` 등)라 1절 코드 로직 재조사는 생략하고, `static_layer.csv`가 지정한 대로 **"F4에서 데이터 입수 먼저 확인"**만 했다.

## 확인 내용 (2026-11-09)

- `static_layer.csv` 비고: "재수집(Poloniex API; 동작 미확인)" — F3 단계에서는 "이론상 API로 재수집 가능"으로 pass 처리됐지만 실제 동작은 그때 확인되지 않았다.
- 저장소(`ZhengyaoJiang/PGPortfolio`) `pgportfolio/marketdata/poloniex.py`가 쓰는 엔드포인트는 `https://poloniex.com/public?command=...`(2017년 당시 Poloniex의 레거시 공개 REST API)다.
- **직접 호출해 확인함:** `curl -sIL 'https://poloniex.com/public?command=returnChartData&currencyPair=BTC_ETH&start=1498867200&end=1498953600&period=300'` → `poloniex.com`이 **301로 `www.poloniex.com/public?...`로 리다이렉트하고, 그 최종 요청이 403 Forbidden을 반환한다**(CloudFront 응답, 2026-11-09 04:14 UTC 확인). 즉 이 레거시 공개 API는 더 이상 데이터를 주지 않는다(동작 안 함, 키 유무와 무관한 접근 차단으로 보임 — `command=returnChartData`는 공개 엔드포인트라 API 키가 필요 없다).

## 판정

**F4: 실행 불가(데이터 입수 불가).** 코드 실행 자체를 시도하기 전에 데이터 재수집 경로가 막혀 있다는 것이 확인됐다. 번들 데이터도 없다(저장소에 포함된 샘플 DB가 있는지는 추가 확인하지 않았다 — 레거시 API가 막힌 이상 대규모 과거 데이터 재수집은 불가능하므로 추가 조사의 실익이 적다고 판단했다).

**다음 큐 항목으로 넘어간다**(3.3, 성과·이 결과와 무관하게 고정 순서).

**사용자에게 알릴 점:** 이 발견은 `static_layer.csv` 순서 8행의 F3 비고("재수집... 동작 미확인")를 "동작 안 함"으로 확정하는 새 사실이다. F3 단계의 표 자체를 고치는 것은 그 표를 관리하는 범위를 벗어난다고 판단해 손대지 않았다 — 필요하면 사용자가 `notes/lit/f1/static_layer.csv`·`f1_status.csv`를 갱신할 수 있도록 여기 남겨둔다.
