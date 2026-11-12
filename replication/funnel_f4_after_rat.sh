#!/bin/bash
# F4 순서 스크립트(서버 WSL, tmux f4_seq): RAT F7(R1~R5)이 끝난 뒤 li2019 → xiong2018 F4를 차례로 돈다.
# 메모리 3.9GB라 RAT 학습과 동시에 돌리지 않는다. 각 대상 스크립트는 끝난 대상(done.json)을 건너뛴다.
# 재부팅 뒤에도 같은 명령으로 다시 띄우면 된다.
LOG=~/f4work/f4_seq.log
log(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
RAT=~/ToBeRich/data/funnel/rat_f7_gtx1650
ratalive(){ ps -eo comm=,args= | awk '$1 ~ /^python/ && /run_rat_f7\.py|funnel_f7_rat_local\.py/' | grep -q .; }
log "대기 시작: RAT R5 done.json 그리고 RAT 프로세스 종료"
while [ ! -f "$RAT/R5/done.json" ] || ratalive; do
  # 11-24 이후 RAT가 멈춰 R5가 안 생겨도 RAT 프로세스가 없으면 진행한다
  if ! ratalive && [ "$(date +%Y%m%d)" -ge 20261124 ]; then break; fi
  sleep 60
done
log "RAT 끝 확인. li2019 시작"
cd ~/ToBeRich && python3 replication/funnel_f4_li2019_local.py 2>&1 | tee -a "$LOG"
log "li2019 끝. xiong2018 시작"
cd ~/ToBeRich && python3 replication/funnel_f4_xiong2018_local.py 2>&1 | tee -a "$LOG"
log "F4 순서 끝"
