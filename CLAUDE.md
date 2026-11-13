# 졸업프로젝트 — Claude 작업 지침

새 대화를 시작하면 **`HANDOFF_2026-11-13.md`를 먼저 읽는다**(이전 맥락은 `HANDOFF_2026-11-05.md`, `HANDOFF_2026-11-03.md`, `HANDOFF_2026-10-27.md`, `HANDOFF_2026-10-26.md`, 전체 경과는 `notes/PROGRESS_SUMMARY_2026-11-01.md`). Claude 메모리 백업은 `notes/claude_memory/`에 있다.

**서버 노트북(DESKTOP-U6SI9TA, Windows)에서 시작한 세션이면 `notes/server_gtx1650_runbook.md`를 먼저 읽고 그대로 진행한다**(PPN·RAT F4·F5 측정을 GTX 1650으로, 2026-11-07 결정). 봇 폴더는 건드리지 않는다.
사용자와는 한국어로 대화한다. 결과는 포장하지 말고 직설적으로 말한다.

## 반드시 지킬 원칙
- **사전 등록**: 새 실험은 실행 전에 선택 규칙·판정 기준을 노트북/스크립트에 고정하고 커밋한다. 결과를 본 뒤 기준·설정을 바꾸지 않고, 실패해도 사전 판정 그대로 보고한다. 사후 패턴은 "탐색적"으로 표시한다.
- 미지 구간(2026-07-14~10-26)은 이미 1회 사용됨 — 새 가설 검증에 다시 쓰지 않는다.
- **부풀리지 않는다**: "핵심 증거", "흔한 문제" 같은 과장 금지. 보고 순서는 사전 판정 → 냉정한 해석 → 한계. 새 주장·다음 방향은 사용자에게 보고하기 전에 별도 에이전트(반박·심사자 역할, 선행연구 검색 포함)로 검증하고 그 반론을 함께 보고한다.
- **논문 문장에 과정 기록 금지**: 커밋 해시, 실행 횟수, 감사 경위 등은 저장소 기록에만 남기고 논문 초안에는 표준 학술 문체로 결과·방법만 쓴다.
- `paper/`(DRAFT*.md, RETRAIN_1006.md)와 `README.md`에는 사용자의 커밋 안 된 수정이 있다 — **직접 편집하지 말고** 초안은 별도 파일로 쓴다. `results/`, `submissions/`도 사용자 파일이므로 건드리지 않는다.
- 디스크 여유가 적다 — 큰 파일 다운로드 금지.

## git
- 작업 브랜치 `audit-fix-1004`. 푸시: `git push origin audit-fix-1004 && git push origin audit-fix-1004:main`(fast-forward). 실계좌 서버는 `main`을 pull해 재시작하므로 봇 코드 변경은 신중히.
- 로컬 `main` 브랜치의 미푸시 커밋 `857461b`는 건드리지 않는다.

## 실계좌 봇
Windows 서버 desktop-u6si9ta, `main`, β=30(rt1006) 정책, 약 330 USDT. 대시보드 `https://desktop-u6si9ta.tail1ae2f7.ts.net/`(Tailscale, JSON은 `/api/status`). 이 맥의 IP는 바이낸스 API 허용 목록에 없어 직접 조회 시 -2015 — 대시보드로 확인한다. 2026-11-05 확인, 정상.

## 서버 원격 조작(맥에서, 2026-11-09 설정)
- **맥에서 처음이면** `bash tools/mac_remote_setup.sh`를 한 번 실행한다(사용자가 터미널에서 직접 실행. 서버 Windows 비밀번호를 한 번 묻는다). 키 생성, `~/.ssh/config`의 `Host tb`, 서버 administrators_authorized_keys 등록, 시험까지 한다. 비밀번호 입력이 필요하므로 Claude가 대신 실행하지 않는다.
- 맥 `~/.ssh/config`의 호스트 `tb` = Tailscale `desktop-u6si9ta`, 사용자 `ksbda`, 키 인증. Windows OpenSSH이고 기본 셸은 PowerShell이다.
- WSL 명령은 `ssh tb "wsl -e bash -lc '<명령>'"`으로 보낸다. 재현 작업은 WSL의 `~/ToBeRich`(별도 clone)와 `~/f4work`에서 한다. Windows 쪽 `C:\Users\ksbda\ToBeRich`는 봇 폴더이므로 건드리지 않는다.
- RAT F7: tmux `rat_f7`. 상태는 `cat ~/ToBeRich/data/funnel/rat_f7_gtx1650/*/done.json`, 재부팅 후 재개는 `~/f4work/f7_resume.sh`로 한다. 성과 파일은 열지 않는다(런북 6절).
- tmux 화면을 직접 볼 때는 `ssh -t tb wsl tmux attach -t rat_f7`. 빠져나올 때는 Ctrl+b d를 쓴다. Ctrl+C를 누르면 실행이 죽는다.
