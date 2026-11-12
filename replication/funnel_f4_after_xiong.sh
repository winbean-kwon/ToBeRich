#!/bin/bash
# F4 순서 스크립트 2(서버 WSL, tmux f4_seq2): funnel_f4_after_rat.sh(f4_seq)가 li2019 → xiong2018을 끝낸 뒤 SmartFolio F4를 돈다.
# f4_seq가 실행 중인 스크립트 파일은 고치지 않는다(bash가 실행 중 파일을 읽어 들이므로). 재부팅 뒤에는 같은 명령으로 다시 띄운다.
LOG=~/f4work/f4_seq.log
log(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
log "SmartFolio 대기: f4_seq 끝(F4 순서 끝) 기다림"
until grep -q "F4 순서 끝" "$LOG" && ! tmux has-session -t f4_seq 2>/dev/null; do
  if [ "$(date +%Y%m%d)" -ge 20261125 ]; then log "11-25 이후 새 실행 시작 안 함"; exit 0; fi
  sleep 60
done
log "SmartFolio 시작"
cd ~/ToBeRich && python3 replication/funnel_f4_smartfolio_local.py 2>&1 | tee -a "$LOG"
log "SmartFolio 끝"
