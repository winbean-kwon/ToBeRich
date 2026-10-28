#!/bin/sh
# T3 O2 학습 160회 실행기. 몇 번을 다시 실행해도 된다: 결과 CSV가 있는 실행은 건너뛰고, 끊긴 실행은 처음부터 다시 한다.
# 세션이 끝나도 계속 돌도록 nohup으로 띄우고, 맥이 잠들지 않게 caffeinate를 건다.
#   sh replication/run_t3_o2.sh        # 백그라운드 시작(이미 돌고 있으면 아무것도 안 함)
#   tail -f .t3env/logs/o2.log         # 진행 확인
ROOT=$(cd "$(dirname "$0")/.." && pwd); E=$ROOT/.t3env; P=4
if [ "$1" != "--fg" ]; then
  if [ -f "$E/logs/o2.pid" ] && kill -0 "$(cat "$E/logs/o2.pid")" 2>/dev/null; then echo "이미 실행 중 (pid $(cat "$E/logs/o2.pid"))"; exit 0; fi
  sh "$ROOT/replication/setup_t3env.sh" || exit 1
  nohup caffeinate -i sh "$0" --fg >> "$E/logs/o2.log" 2>&1 &
  echo $! > "$E/logs/o2.pid"; echo "시작 (pid $!), 로그 $E/logs/o2.log"; exit 0
fi
rm -f "$ROOT"/replication/finrl_t3/o2/*.tmp
echo "== $(date '+%F %T') 시작, 남은 실행: $(for a in ddpg td3 ppo a2c; do for w in W0 W1 W2; do for c in a b c; do [ "$w$c" = W0a ] && continue; for s in 0 1 2 3 4; do [ -f "$ROOT/replication/finrl_t3/o2/${a}_${w}_${c}_s${s}.csv" ] || echo x; done; done; done; done | wc -l)"
for a in ddpg td3 ppo a2c; do for w in W0 W1 W2; do for c in a b c; do [ "$w$c" = W0a ] && continue; for s in 0 1 2 3 4; do
  [ -f "$ROOT/replication/finrl_t3/o2/${a}_${w}_${c}_s${s}.csv" ] || echo "$a $s $w $c"
done; done; done; done | xargs -P $P -n 4 sh -c 'PYTHONPATH="'"$E"'/pylib" python3 "'"$ROOT"'/replication/finrl_t3_run.py" --fm "'"$E"'/fm" train "$0" "$1" "$2" "$3" 2>&1 | grep "학습\|Error\|Traceback\|assert"'
echo "== $(date '+%F %T') 종료, 결과 $(ls "$ROOT"/replication/finrl_t3/o2/*_s?.csv 2>/dev/null | wc -l)/160"
