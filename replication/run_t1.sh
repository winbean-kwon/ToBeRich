#!/bin/sh
# T1 DeepAries 실행기(replication/deeparies_run.py). 다시 실행해도 된다: 결과 CSV가 있는 실행은 건너뛴다.
# O1(W0 조건 a, 시드 0–9)을 먼저 돌리고 judge1을 계산한다. 등급이 재현·부분 재현이면 O2 실행(50회)을 이어서 한다(v3 4장).
# T3 O6가 돌고 있으면 끝날 때까지 기다린다(CPU 경합 방지).
#   sh replication/run_t1.sh       # 백그라운드 시작
#   tail -f .t1env/logs/t1.log     # 진행 확인
ROOT=$(cd "$(dirname "$0")/.." && pwd); E=$ROOT/.t1env; P=4; O=$ROOT/replication/deeparies/runs
PY="PYTHONPATH=$E/pylib python3 $ROOT/replication/deeparies_run.py"
if [ "$1" != "--fg" ]; then
  if [ -f "$E/logs/t1.pid" ] && kill -0 "$(cat "$E/logs/t1.pid")" 2>/dev/null; then echo "이미 실행 중 (pid $(cat "$E/logs/t1.pid"))"; exit 0; fi
  sh "$ROOT/replication/setup_t1env.sh" || exit 1
  nohup caffeinate -i sh "$0" --fg >> "$E/logs/t1.log" 2>&1 &
  echo $! > "$E/logs/t1.pid"; echo "시작 (pid $!), 로그 $E/logs/t1.log"; exit 0
fi
while [ -f "$ROOT/.t3env/logs/o6.pid" ] && kill -0 "$(cat "$ROOT/.t3env/logs/o6.pid")" 2>/dev/null; do sleep 60; done
rm -f "$O"/*.tmp; rm -rf "$E/work"
go() { xargs -P $P -n 3 sh -c "$PY"' run "$0" "$1" "$2" 2>&1 | grep "분, CAGR\|Error\|Traceback\|assert"'; }
o1() { for s in 0 1 2 3 4 5 6 7 8 9; do [ -f "$O/W0_a_s$s.csv" ] || echo "W0 a $s"; done; }
o2() { for c in b c; do for s in 0 1 2 3 4 5 6 7 8 9; do [ -f "$O/W0_${c}_s$s.csv" ] || echo "W0 $c $s"; done; done
       for w in W1 W2 W3; do for c in a b; do for s in 0 1 2 3 4; do [ -f "$O/${w}_${c}_s$s.csv" ] || echo "$w $c $s"; done; done; done; }
echo "== $(date '+%F %T') O1 시작, 남은 실행: $(o1 | wc -l)"
o1 | go
[ "$(ls "$O"/W0_a_s?.csv 2>/dev/null | wc -l)" -eq 10 ] || { echo "O1 미완료 — 중단"; exit 1; }
sh -c "$PY judge1" | tail -3
G=$(python3 -c "import json;print(json.load(open('$ROOT/replication/deeparies/judge_o1.json'))['등급'])")
echo "== O1 등급: $G"
case "$G" in 재현|"부분 재현") ;; *) echo "O2 대상 아님 — 종료"; exit 0;; esac
echo "== $(date '+%F %T') O2 시작, 남은 실행: $(o2 | wc -l)"
o2 | go
echo "== $(date '+%F %T') 종료, 결과 $(ls "$O"/*_s?.csv 2>/dev/null | wc -l)/60"
