# F1 자동 독립 재검색 — 결과 (2026-11-27)

> 사전 등록 `notes/f1_second_coder_prereg.md` 추가 절(a7ad42f). 판정 시트 `notes/lit/f1/f1_auto_coder_sheet.csv`, 계산 `replication/f1_auto_agreement.py` → `replication/f1_auto_agreement.json`.
> 판정자: 새 맥락의 에이전트(언어 모델). 판정 절차와 15편 시트 두 파일만 읽음(이전 판정·결과 미열람). 사람 두 번째 판정은 미수행으로 남는다.

- 이진(찾음 = 통과) 일치 15/15, Cohen κ = 1.0(15편이라 정밀도 낮음; 근사 구간은 κ=1에서 퇴화).
- 6범주 일치 14/15. 불일치: wang2019alphastock — 사용자 '없음', 자동 '제3자만'(둘 다 미통과).
- 경계 사례(자동 판정자 메모): liang2018adversarial — 논문 링크 계정 404, 같은 이름 저장소가 DEEPCRYPTO LTD 조직에 있음(커밋 작성자 liangzp, README가 저자 명시). 엄격 규칙으로 '링크 사망'(사용자와 같음). P24-08 — 논문 부록 C가 가리키는 포크 가지, '찾음'(사용자와 같음).
- 한계: 사람이 아님, 같은 계열 모델이 이 연구 다른 작업에도 쓰임, 자동 판정자 일부 페이지 접근 실패(AAAI ojs 봇 차단, GitHub 검색 API 한도), 소요 시간은 판정자 추정치.
