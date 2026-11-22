# FRONTIER exploratory F7 (prereg d7878f0). One seed per copy; train then backtest; up to 3 attempts.
S=$1
cd ~/f4work/frontier
export PYTHONNOUSERSITE=1 MPLBACKEND=Agg TF_CPP_MIN_LOG_LEVEL=2
PY=~/f4work/frontier/env/bin/python
RUN=~/f4work/frontier/funnel_f7x_frontier_run.py
OUT=~/f4work/frontier/f7out; mkdir -p $OUT
D=~/f4work/frontier/f7run_s$S
[ -d $D ] || { git clone -q repo $D 2>/dev/null; (cd $D && git -c advice.detachedHead=false checkout -q e019ce4); }
cd $D/code/REINFORCE
for phase in train backtest; do
  for a in 1 2 3; do
    J=$OUT/${phase}_s${S}.json
    [ -f $J ] && python3 -c "import json,sys;d=json.load(open('$J'));sys.exit(0 if d['exception'] is None else 1)" && break
    echo "$(date -Is) $phase attempt $a" >> $OUT/s${S}.log
    [ $phase = train ] && rm -rf experiments/DOW_30/seeded/RL_CNN/seed_$S
    rm -f $J
    $PY $RUN $phase $S $J > /dev/null 2> $OUT/${phase}_s${S}_a$a.err
    echo "$(date -Is) $phase attempt $a rc=$?" >> $OUT/s${S}.log
  done
done
echo "$(date -Is) END" >> $OUT/s${S}.log
