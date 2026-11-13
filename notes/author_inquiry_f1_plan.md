# F1 저자 문의 계획 — **초안, 사용자 결정 전 (미확정·미발송)**

이 파일은 사용자가 결정하기 전의 초안이다. 결정하면 아래 "이탈 기록"과 함께 커밋해 고정하고, 그 뒤에 발송한다.

## 이탈 기록 (발송하기로 결정하면 이 문단을 확정한다)
`notes/funnel_protocol.md`에서 이 계획과 부딪히는 부분은 두 곳이다.
- 3.1(71행): "저자 일괄 문의는 하지 않는다(사용자 결정)".
- 3.2: 2026-11-07까지 발송하고 14일 기다린다.

이 계획은 F1 결과를 본 뒤에 결정을 뒤집는 것이므로 **사후 이탈**이다. 이유는 독립 심사의 지적이다. "찾지 못함(문의 안 함)"이 표제 숫자의 대부분이어서, 문의 결과가 그 해석을 좌우한다.

문의 결과는 **탐색적 보조 결과**로만 보고하고, F1 판정과 깔때기 표는 바꾸지 않는다. 받은 코드는 이번 일정에서 실행하지 않는다.

## 대상
F1 재확인(`notes/f1_recheck_prereg.md`)이 끝난 뒤에도 "없음", "링크 사망", "요청 시 제공"으로 남은 논문의 교신저자에게 보낸다.
- 같은 사람이 여러 편의 교신저자이면 한 통으로 묶는다(예: Benhamou 2편).
- 주소를 구할 수 없으면 "주소 없음"으로 적고 보내지 않는다.

## 일정 (마감 12월 중순 기준)
| 단계 | 날짜 |
|---|---|
| 개별 발송 | 2026-11-17까지 |
| 리마인더 1회 | 발송 10일째 |
| 마감 | 2026-12-08 |

창은 약 3주다. 선행 연구보다 짧으므로 논문에는 "preliminary, 3-week window"로 적는다.

## 응답 범주 (사전 고정)
| 값 | 뜻 |
|---|---|
| `공개 링크 제공` | 공개 URL을 알려 줌 |
| `비공개 공유` | 코드를 개인적으로 보내 줌. F1 통과로 치지 않음 |
| `요청 시 제공이라 했으나 미제공` | 마감까지 받지 못함 |
| `공유 불가` | 공유할 수 없다고 답함 |
| `무응답` | 마감까지 답이 없음 |
| `반송` | 메일이 되돌아옴 |

## 보고 방식
- 범주별 편수만 집계해 보고한다. 논문별·저자별 표는 논문에 넣지 않는다(저자 지목 방지).
- 메일에 "응답은 집계로만 보고한다"고 적는다.
- 발송 전에 지도교수에게 IRB 면제 여부를 한 번 확인한다(사람이 아닌 산출물 조사이지만 응답을 데이터로 씀).

## 메일 문안 (영어, 개별 발송, 지도교수 참조 권장)
**Subject:** Code availability for "[Title]" ([Venue Year])

Dear Dr. [Surname],

I am an undergraduate student at Hanyang University, working on a graduation thesis that surveys code availability and reproducibility in deep reinforcement learning for portfolio management. Your paper "[Title]" is part of the survey sample.

I could not find a public implementation linked from the paper or the authors' pages. Could you let me know whether official code is available, or whether it could be shared?

Responses will be reported only in aggregate (e.g., the number of papers for which code was provided), and no individual paper or author will be named in connection with a response. Any reply, including that the code cannot be shared, is helpful.

Thank you for your time.

Best regards,
Seungbin Kwon
[Department], Hanyang University
