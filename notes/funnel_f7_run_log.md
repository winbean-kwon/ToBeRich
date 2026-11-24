# F7 서버 실행 기록 (RAT·Ensemble)

판정 기준은 바꾸지 않는다. 실행 중 생긴 일만 적는다. 결과 노트에 그대로 옮긴다.

- 2026-11-10 13:05:47 RAT P5 끝 → 드라이버가 R1 시도 1 시작(pid 12264).
- 13:05:56 순서 스크립트(ens_f7)가 RAT 종료 단계에서 `pkill -f "[f]unnel_f7_rat_local.py"`를 실행. tmux 서버 명령줄에 이 이름이 들어 있어 tmux 서버가 죽었고, ens_f7 세션의 순서 스크립트도 함께 종료됨. RAT 드라이버는 죽고 R1 학습 프로세스(pid 12264)만 고아로 남음.
- 13:48 확인. 7fbd9ab에서 python 프로세스만 골라 끝내도록 수정.
- 13:49:24 순서 스크립트 재실행. 고아 R1 학습을 종료(약 44분 학습, 드라이버 없음)한 뒤 Ensemble F7 시작(시작 기한 11-11 00:00 이전). R1 시도 1은 이후 재개 스크립트가 중단으로 기록한다. 사전 등록 2.2가 예상한 'R1 중단'과 같은 처리이며 끊긴 시간만 다르다.
- Ensemble 성과 파일·RAT R1 stdout은 열지 않았다.
- 13:51:30 WSL 가상머신이 유휴 종료됨(Windows 재부팅 아님, 부팅 11-09 19:40 유지). 원인: ssh로 띄운 뒤 연결이 끊겨 WSL 클라이언트가 없었고, 11-10에 넣은 `.wslconfig`(instanceIdleTimeout=-1, vmIdleTimeout=-1)는 VM 재시작 전이라 적용되지 않았음. 그 전 18시간은 서버 콘솔에서 연 WSL 창이 VM을 붙잡고 있었던 것으로 보임(13:05 tmux 서버 종료로 그 고리가 끊김 — 추정). Ensemble E1 시도 1은 약 2분에 중단(시작 기록으로 시도 수에 포함, 사전 등록 규칙대로).
- 14:28 맥 ssh 접속으로 WSL 재시작(.wslconfig 적용). 14:29:26 순서 스크립트 재실행, E1 시도 2 시작.
- 11-10 14:38:52 WSL이 다시 정상 종료(systemd poweroff, Windows 재부팅 아님). ssh 끊김 약 5분 뒤. `.wslconfig`의 유휴 설정으로는 막히지 않았음. E1 시도 2는 약 9분(PPO 학습 시작 직후)에 중단. 이후 11-11 18:38까지 서버 유휴.
- 11-11 20:39 사용자가 Windows 예약 작업 `wsl_keepalive`(로그온 시 `wsl.exe -e sleep infinity`) 등록·실행. 무접속 11분 생존 확인 후 20:51:23 재실행, E1 시도 3(마지막) 시작.
- 판정 영향: E1이 이번에 끝나지 않으면 사전 등록 규칙대로 failed_max_attempts. 일정: 5회 완료 예상 11-12 오전, 이후 RAT R.
- 11-11 20:51 E1 시도 3 시작 후 E1~E5 모두 완료(E5 끝 11-12 02:09:04, `ens_all_done`). 이어서 RAT R1~ 재개.
- 11-12 04:00:06 Ensemble 판정 스크립트 1회 실행(`judge_result.json`). 실행한 세션은 결과 노트를 남기지 않음. 11-12 12시대 별도 폴더에서 재계산해 JSON 동일 확인 → 결과 `notes/funnel_f7_ensemble_result.md`(부분 재현).
- 11-12 R1~R5 완료(R5 끝 16:19). RAT 판정 스크립트 1회 실행(첫 호출은 시스템 python3에 numpy 없음 → 계산 전 정지, `~/f4work/p37` python으로 재호출) → 결과 `notes/funnel_f7_rat_result.md`(부분 재현). 판정 시점이 P5 직후가 아니라 R5 뒤인 것은 경미한 시점 이탈(노트 0절).

## F7x Ensemble 난류 문턱 반사실 — 실행기 시작(2026-11-23 00:09 KST)
- 사전 등록 034c734. 서버 WSL clone을 034c734로 pull, 실행기·판정 sha256이 맥과 같음(run 9fc003ec…17d6, judge 1c4a89a3…23b1).
- tmux `ens_turb`, 드라이버 로그 `~/ToBeRich/data/funnel/ensemble_turb_driver.log`. FRONTIER F7이 돌고 있어 대기 중(`wait.jsonl` 첫 줄 why=frontier_running). `pip_freeze.txt` 기록됨(열람은 판정 때).
- 진행 확인은 `ls ~/ToBeRich/data/funnel/ensemble_turb/*/done.json`, `tail -1 .../wait.jsonl`만. 성과 파일은 열지 않는다(사전 등록 3절).

## F7x Ensemble 난류 문턱 — 대기 원인 확인(2026-11-24 18:00 KST, 성과 없음)
- 상태: 실행 0회, `done.json` 0개. `wait.jsonl` 252줄이 모두 `frontier_running`이다(마지막 2026-11-24 17:59).
- 원인: FRONTIER F7은 끝났다(8e8f35f). 그런데 tmux 서버 프로세스(pid 673)는 처음 `tmux new-session -d -s frontier_f7 bash …/f7_all.sh`로 떴고, 그 명령줄을 그대로 갖고 있다. 실행기의 `busy()`는 `pgrep -f` 패턴(`f7_all.sh` 포함)으로 FRONTIER를 찾는데, 이 tmux 서버의 명령줄이 패턴에 걸려 계속 "돌고 있음"으로 판정한다. `ens_turb` 세션도 같은 tmux 서버 아래에 있다.
- 조치안(실행기 코드는 바꾸지 않음):
  1. 실행기(pid 6932)를 끝낸다.
  2. `tmux kill-server`로 tmux 서버를 끝낸다.
  3. `tmux new-session -d -s ens_turb "bash -c 'cd ~/ToBeRich && python3 replication/funnel_f7x_ensemble_turb_run.py >> ~/ToBeRich/data/funnel/ensemble_turb_driver.log 2>&1'"`로 다시 시작한다.
  - 시작된 실행이 없으므로 재시작은 시도로 세지 않는다.
  - Claude가 이 조치를 하려 했으나 자동 권한 검사에서 프로세스 종료가 거부되었다. 사용자 승인 뒤 진행한다.
- 일정: 첫 실행 시작 마감 2026-11-27 00:00 KST(사전 등록 1.3). 17회 약 19시간.
