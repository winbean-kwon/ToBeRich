#!/bin/bash
# Ensemble F7을 RAT F7의 P 5회와 R 5회 사이에 끼워 넣는다(사전 등록 notes/funnel_f7_ensemble_prereg.md 2.2).
# 1) RAT P5/done.json이 생길 때까지 기다린다. 2) rat_f7 세션과 RAT 드라이버·학습 프로세스를 끝낸다.
# 3) Ensemble F7 5회를 돈다(CPU, GPU 미사용). 4) RAT 재개 스크립트로 R 1→5를 이어서 돈다.
# RAT 실행 스크립트(replication/funnel_f7_rat_local.py)는 수정하지 않는다. tmux 세션 ens_f7에서 돌린다.
# 재부팅 뒤 다시 띄워도 된다: Ensemble이 다 끝났으면(ens_all_done) RAT를 끊지 않고 재개만 한다.
set -u
RAT=~/ToBeRich/data/funnel/rat_f7_gtx1650
ENS=~/ToBeRich/data/funnel/ensemble_f7
LOG=~/f4work/ens_f7_orchestrator.log
log(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
# python 프로세스만 고른다. tmux 서버의 명령줄에도 스크립트 이름이 들어 있어 pkill -f는 tmux 서버(이 세션 포함)를 죽인다.
ratpids(){ ps -eo pid=,comm=,args= | awk '$2 ~ /^python/ && /run_rat_f7\.py|funnel_f7_rat_local\.py/ {print $1}'; }
alive(){ [ -n "$(ratpids)" ]; }
RESUME=~/f4work/f7_resume.sh
[ -x "$RESUME" ] || RESUME=~/ToBeRich/replication/funnel_f7_rat_resume.sh

if [ -f "$ENS/ens_all_done" ]; then
  log "Ensemble 이미 끝남. RAT 재개만 시도"
  alive || bash "$RESUME" 2>&1 | tee -a "$LOG"
  exit 0
fi

log "대기 시작: $RAT/P5/done.json"
while [ ! -f "$RAT/P5/done.json" ]; do sleep 5; done
log "RAT P5 끝. rat_f7 세션과 RAT 프로세스 종료"
tmux kill-session -t rat_f7 2>/dev/null
p=$(ratpids); [ -n "$p" ] && kill $p
for k in 1 2 3 4 5 6; do alive || break; sleep 5; p=$(ratpids); [ -n "$p" ] && kill -9 $p; done
if alive; then log "RAT 프로세스가 남아 있음. Ensemble을 시작하지 않고 중단"; exit 1; fi
log "R1 폴더 상태: $(ls $RAT/R1 2>/dev/null | tr '\n' ' ')"

log "Ensemble F7 시작"
cd ~/ToBeRich && python3 replication/funnel_f7_ensemble_local.py 2>&1 | tee -a ~/f4work/ens_f7_run.log
rc=${PIPESTATUS[0]}
n=$(ls $ENS/E*/done.json 2>/dev/null | wc -l)
log "Ensemble F7 끝(rc=$rc, done.json $n개)"
[ "$n" -ge 5 ] || [ -f "$ENS/not_started.json" ] && touch "$ENS/ens_all_done"

log "RAT R 재개(끊긴 R1 시도는 재개 스크립트가 중단으로 기록)"
bash "$RESUME" 2>&1 | tee -a "$LOG"
log "RAT 재개 명령 완료"
