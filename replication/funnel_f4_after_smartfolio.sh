#!/bin/bash
# F4 순서 스크립트 3(서버 WSL, tmux f4_seq3): SmartFolio F4가 끝난 뒤 ADRL F4를 돈다. 재부팅 뒤 같은 명령으로 다시 띄운다.
LOG=~/f4work/f4_seq.log
log(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
log "ADRL 대기: SmartFolio 끝 기다림"
until grep -q "SmartFolio 끝" "$LOG" && ! tmux has-session -t "=f4_seq2" 2>/dev/null; do
  if [ "$(date +%Y%m%d)" -ge 20261125 ]; then log "11-25 이후 새 실행 시작 안 함"; exit 0; fi
  sleep 60
done
log "ADRL 시작"
cd ~/ToBeRich && python3 replication/funnel_f4_adrl_local.py 2>&1 | tee -a "$LOG"
log "ADRL 끝"
