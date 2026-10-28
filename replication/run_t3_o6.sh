#!/bin/sh
# T3 O6 학습 60회 실행기(notes/finrl_t3_o6_prereg.md). run_t3_o2.sh와 같은 방식: 다시 실행해도 되고, det CSV가 있는 실행은 건너뛴다.
#   sh replication/run_t3_o6.sh        # 백그라운드 시작(이미 돌고 있으면 아무것도 안 함)
#   tail -f .t3env/logs/o6.log         # 진행 확인
ROOT=$(cd "$(dirname "$0")/.." && pwd); E=$ROOT/.t3env; P=4; O=$ROOT/replication/finrl_t3/o6
if [ "$1" != "--fg" ]; then
  if [ -f "$E/logs/o6.pid" ] && kill -0 "$(cat "$E/logs/o6.pid")" 2>/dev/null; then echo "이미 실행 중 (pid $(cat "$E/logs/o6.pid"))"; exit 0; fi
  sh "$ROOT/replication/setup_t3env.sh" || exit 1
  nohup caffeinate -i sh "$0" --fg >> "$E/logs/o6.log" 2>&1 &
  echo $! > "$E/logs/o6.pid"; echo "시작 (pid $!), 로그 $E/logs/o6.log"; exit 0
fi
rm -f "$O"/*.tmp
jobs() { for a in ppo a2c; do for w in W0 W1 W2; do for c in b a; do for s in 0 1 2 3 4; do
  [ -f "$O/${a}_${w}_${c}_s${s}_det.csv" ] || echo "$a $s $w $c"; done; done; done; done; }
echo "== $(date '+%F %T') 시작, 남은 실행: $(jobs | wc -l)"
jobs | xargs -P $P -n 4 sh -c 'PYTHONPATH="'"$E"'/pylib" python3 "'"$ROOT"'/replication/finrl_t3_run.py" --fm "'"$E"'/fm" det "$0" "$1" "$2" "$3" 2>&1 | grep "학습\|Error\|Traceback\|assert"'
echo "== $(date '+%F %T') 종료, 결과 $(ls "$O"/*_det.csv 2>/dev/null | wc -l)/60"
