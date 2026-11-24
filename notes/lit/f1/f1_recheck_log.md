# F1 재확인 기록

## 2026-11-20 — 판정 도중 Claude 개입
- 시점: 사용자 판정 17/54편(17편 모두 판정 기입, 마지막 확인일 2026-11-19). 아직 집계는 하지 않았다.
- 경위: 사용자의 요청으로 Claude가 입력 화면의 저장 상태(브라우저 저장소)를 읽었다. 판정 정의를 잘못 적용한 것으로 보이는 사례 7편을 지적했다. 그중 P24-01과 W21_FinRL은 층 2에 속한다. (처음에는 W21_FinRL·SQ-XPM의 판정 칸이 비었다고 잘못 읽어 5편으로 적었다.)
  - P24-01: 논문 각주의 저자 저장소를 `제3자만`으로 적었다.
  - wang2019alphastock, W21_FinRL, SQ-XPM: ACM 저작권 안내문을 `요청 시 제공`의 근거로 적었다.
  - W22_PretoriusVanZyl, W22_MSPM, jiang2017crypto: 참고문헌의 라이브러리·논문 링크를 `제3자만`의 근거로 적었다.
- 조치: 정의를 예시로 풀어 쓴 `f1_judging_guide.md`를 추가했다. 판정 정의 자체(`notes/f1_recheck_prereg.md`)는 바꾸지 않았다.
- 이 개입 때문에 위 7편의 재판정은 Claude의 지적을 본 뒤에 이루어진다. 집계 때는 이 7편을 따로 표시하고, 원래 판정 기준과 수정 후 기준의 주 지표를 둘 다 보고한다.
- 두 번째 판정자에게도 `f1_judging_guide.md`를 함께 준다(판정 전).

## 2026-11-20 — 브라우저 저장 상태를 시트로 옮김(Claude)
- 입력 화면의 브라우저 저장 상태 17편을 `f1_recheck_sheet.csv`로 옮겼다. 판정 값은 바꾸지 않았다.
- 칸 정리: W22_PretoriusVanZyl의 URL 칸에 있던 참고문헌 문단을 메모로 옮겼다. wang2019alphastock, W21_FinRL, SQ-XPM의 메모에 있던 ACM 저작권 안내문(판정 근거 아님)은 지웠다.
- 단계 체크(s0, s1)는 시트 열이 없어 옮기지 않았다.

## 판정 변경 (사용자가 기입)
| id | 원래 판정 | 바꾼 판정 | 이유 | 날짜 |
|---|---|---|---|---|
| P24-01 | 제3자만 | 찾음 | 논문 1쪽 각주 1이 github.com/DVampire/EarnMore를 가리키고, README의 인용(제목·저자 8명·WWW 2024)이 논문과 일치한다. 판정 가이드의 "각주에 저장소 → 찾음"에 해당한다. Claude가 확인한 뒤 사용자 요청으로 Claude가 시트에 기입했다. 7편 따로 표시 대상이다. | 2026-11-21 |
| SQ-XPM | 요청 시 제공 | 없음 | 원래 근거는 1쪽 ACM 저작권 안내였다. 사용자가 준 PDF 전체에 코드·요청 문장이 없다. ACM supplementary는 발표 영상뿐이다. 저자 GitHub·전체 제목 검색에서도 나오지 않았다. **Claude 판독**(Claude가 PDF·검색을 확인하고 시트에 기입) — 주 지표에서 뺀다. 7편 따로 표시 대상이다. | 2026-11-21 |
| wang2019alphastock | 요청 시 제공 | 없음 | 원래 근거는 1쪽 ACM 저작권 안내였다. arXiv PDF에서 request는 그 안내문에만 나오고, 각주 URL은 데이터 출처(WRDS, Wind)다. GitHub·전체 제목 검색 결과가 없다. **Claude 판독** — 주 지표에서 뺀다. 7편 따로 표시 대상이다. | 2026-11-21 |
| W22_PretoriusVanZyl | 제3자만 | 찾음 | 원래 근거는 참고문헌에 있는 사용 도구 링크(cvxportfolio, FinRL, stable-baselines3)였다. 논문에는 자기 코드 링크가 없다. 1저자 계정 github.com/ruankie(이름 Ruan Pretorius)의 frontier-rl README가 같은 논문의 TechRxiv 판(10.36227/techrxiv.19165745.v1)을 가리키고, 모델 이름 FRONTIER도 논문과 같다. 가이드의 "저자 계정, README가 이 논문을 가리킴 → 찾음"에 해당한다. **Claude 판독** — 주 지표에서 뺀다. 7편 따로 표시 대상이다. | 2026-11-21 |
| W22_PretoriusVanZyl | 제3자만 | 찾음 | 논문에는 코드 링크가 없다(참고문헌의 github 링크는 cvxportfolio·FinRL·SB3 등 사용 도구). 1저자 계정 github.com/ruankie(이름 Ruan Pretorius)의 frontier-rl README가 같은 논문(TechRxiv 10.36227/techrxiv.19165745.v1, 제목·저자 일치)을 가리키고, 모델 이름 FRONTIER가 본문과 같다. 확인 경로 3(1저자 GitHub)에 해당한다. 사용자가 찾았고 Claude가 확인했다. 층 1 거짓 음성이다. 7편 따로 표시 대상이다. 저장소 `main`은 공매도 확장판이고, 논문에 가까운 것은 첫 커밋 f04dbb3과 `long-only-policy` 브랜치다(후속 단계 미실행). | 2026-11-21 |
| W22_MSPM | 제3자만 | 제3자만(근거 교체) | 원래 근거는 참고문헌의 mlfinlab(사용 도구)이라 무효다. 논문(arXiv v4, PLOS 게재본 e0263689)에는 코드 링크가 없다. PLOS Data Availability는 유료 데이터만 언급한다. 저자와 무관한 비공식 재현 oft2026/mspm(2026-03 생성)만 있다. 1저자와 같은 이름의 GitHub 계정 Zhenhan-Huang은 동일인을 확인할 수 없고 MSPM 저장소도 없다. 시트 식별자의 doi …0265924는 정정 공지이고, 논문 본문 DOI는 …0263689다(식별자 칸은 사전 등록 값이라 그대로 두고 메모에 적음). **Claude 판독** — 주 지표에서 뺀다. 7편 따로 표시 대상이다. | 2026-11-21 |
| jiang2017crypto | 제3자만 | 찾음 | 원래 근거는 참고문헌의 인용 논문 링크(Springer, Nature, arXiv)라 무효다. 논문(arXiv v5)에는 코드 링크가 없다. 2저자 Jinjun Liang의 GitHub 계정 kumkee(프로필 이름 Jinjun Liang)의 SURF2016 README가 이 논문(IntelliSys2017, arXiv:1612.01277)을 명시하고, "the full source code (for the first and second paper)"가 github.com/ZhengyaoJiang/PGPortfolio에 공개되어 있다고 적었다. 1저자 계정의 PGPortfolio README는 두 번째 논문(1706.10059)만 언급한다. 가이드 4단계는 1저자·교신저자를 보라고 하지만, 공저자 계정의 README가 이 논문을 가리키므로 "저자 측 저장소" 사례로 보고 `찾음`으로 했다. 이 해석이 가이드 문언보다 넓다는 점을 기록해 둔다. **Claude 판독** — 주 지표에서 뺀다. 7편 따로 표시 대상이다. 깔때기의 Claude 판정(`not_found`, manual_check_list "PGPortfolio는 다른 논문 코드")은 이 README를 보지 못한 거짓 음성이다. | 2026-11-22 |
| W21_FinRL | 요청 시 제공 | 찾음 | 원래 근거는 1쪽 ACM 저작권 안내라 무효다. 논문에는 저장소 주소 없이 4절에 "configurations and commands are available on Github"만 있다(나머지 github 링크는 참고문헌의 사용 도구). 저자 조직 계정 AI4Finance-Foundation/FinRL README의 논문 목록에 ICAIF 2021 논문이 있다. 사용자가 판정 가이드 절차대로 직접 찾고 판정했다(Claude는 확인할 곳만 안내). 층 2. 7편 따로 표시 대상이다. | 2026-11-21 |

## 2026-11-24 — 54편 판정 완료, 시트 병합, Claude 점검 후 12편 재판정
- 사용자가 18~54번 37편을 판정해 브라우저 내보내기 CSV로 전달했다. Claude가 그 값(판정·URL·근거 위치·확인일)을 바꾸지 않고 시트에 옮겼다. 내보내기의 1~17번은 11-21~22 변경 이전의 브라우저 상태라서(jiang2017crypto `제3자만`, wang2019alphastock·SQ-XPM `요청 시 제공`) 디스크 시트 값을 유지했다.
- 사용자 요청으로 Claude가 판정을 점검했다. 하나는 Claude 깔때기 판정과의 비교이고, 다른 하나는 `없음`·`원문 미확보` 37편의 점검이다. 37편 점검에서는 arXiv 원문 31편을 github·code·request로 검색하고, GitHub 저장소를 제목으로 검색했다. 저자 계정을 하나씩 열어 보지는 않았다. arXiv 판이 없는 7편(SQ-XPM, SQ-ObjDriven, SQ-TwoLevel, SQ-DPSRRL, SQ-DGDRL, SQ-ALRL, P24-03)은 원문을 보지 않았다.
- 아래 12편은 Claude가 근거를 찾았고 사용자가 승인해 바꾸었다. 사용자가 저장소를 직접 열어 보지는 않았다. 그래서 모두 **Claude 판독**으로 표시하고 주 지표에서 뺀다. 집계 때는 원래 사람 판정 기준과 수정 후 기준을 둘 다 보고한다.
- 층 2에서 사람이 원래 `없음`으로 적은 5편은 모두 저장소가 열려 있었다(2026-11-24 HTTP 200). 이 5편은 원래 기준대로 집계하면 거짓 양성으로 잡힌다. 이 놓침은 주로 확인 경로 3(저자 GitHub)을 건너뛴 데서 생긴 것으로 보인다. P24-08은 논문 부록에 링크가 있는데도 놓쳤다. 따라서 층 1에서 사람과 Claude가 둘 다 `없음`으로 일치한 편도 거짓 음성을 걸러 냈다는 강한 근거가 되지 못한다. 이 점을 한계로 적는다.
- Y26-01과 Y26-03은 Claude 깔때기 판정(`not_found`, `placeholder`)에서도 놓친 거짓 음성이다. 앞서 확인한 W22_PretoriusVanZyl·jiang2017crypto와 같은 유형이다. 논문에 링크가 없고 저자 계정에만 저장소가 있다. `funnel_table.csv`에는 사전 등록의 결과 처리 단계에서 반영한다(집계 기준값이라 지금은 두지 않는다).

| id | 층 | 원래 판정 | 바꾼 판정 | 이유 | 날짜 |
|---|---|---|---|---|---|
| Y25-03 | 2 | 없음 | 찾음 | github.com/jiayiderekchen/MARS. 1저자 계정(이름 Jiayi Chen), README가 arXiv 2508.01173을 가리킨다. **Claude 판독** | 2026-11-24 |
| P24-10 | 2 | 없음 | 찾음 | github.com/jkcost/Deepclair. README 제목이 논문 제목과 같다. 계정 이름은 jinkyu다. **Claude 판독** | 2026-11-24 |
| P24-08 | 2 | 없음 | 찾음 | arXiv v1 부록 C 첫 문단이 github.com/jackieli19/PGPortfolio(Stock 브랜치)를 구현 저장소로 명시한다. **Claude 판독** | 2026-11-24 |
| SUP-LSRE | 2 | 없음 | 찾음 | github.com/jiahaoli57/LSRE-CAAN. 계정 이름이 Jiahao Li이고 README에 논문이 인용되어 있다. **Claude 판독** | 2026-11-24 |
| xiong2018ddpg | 2 | 없음 | 찾음 | 저자 조직 계정 AI4Finance-Foundation의 DDPG NIPS 2018 저장소. **Claude 판독** | 2026-11-24 |
| SUP-CLRS | 1 | 찾음 | 링크 사망 | 처음 적은 google-deepmind/clrs는 이름만 같은 다른 연구다. 이 논문이 가리키는 sophialien/FinTech-DPM은 404다. **Claude 판독** | 2026-11-24 |
| yu2019modelbased | 1 | 찾음 | 없음 | dybm은 논문이 사용한 라이브러리다(판정 가이드의 사용 도구 경우). **Claude 판독** | 2026-11-24 |
| SQ-Regret | 1 | 원문 미확보 | 없음 | arXiv 원문이 열린다. github 링크는 arch뿐이고 제목 검색 결과도 없다. **Claude 판독** | 2026-11-24 |
| Y26-01 | 1 | 없음 | 찾음 | github.com/ahmad-asadi/sopmoe. 1저자 계정(이름 Ahmad Asadi), README 제목이 논문 제목과 같다. 논문에는 링크가 없다. **Claude 판독** | 2026-11-24 |
| Y26-03 | 1 | 없음 | 찾음 | github.com/ChenJiahaoJNU/SBCA. README에 제목과 저자(Jinfeng Pan & Jiahao Chen, 1·2저자)가 있고 코드 파일이 있다. 공저자 계정이라 jiang2017crypto와 같은 넓은 해석이다. **Claude 판독** | 2026-11-24 |
| P24-04 | 1 | 없음 | 요청 시 제공 | 논문 끝: "models, or codes ... available from the corresponding author upon reasonable request". 이진 판정(미통과)은 그대로다. **Claude 판독** | 2026-11-24 |
| W21_DeepPocket | 1 | 없음 | 제3자만 | MCCCSunny/DeepPocket은 저자와 무관한 재구현이다(README "diplomski_projekt"). 이진 판정은 그대로다. **Claude 판독** | 2026-11-24 |
| Y25-08 | 1 | 없음 | 없음(유지) | shuttuu/my-hdrl에는 CITATION과 "게재 후 코드 공개" 안내만 있다. 논문은 이 저장소를 가리키지 않고 계정 주인도 확인할 수 없다. 사용자가 `없음`으로 결정했다. | 2026-11-24 |
