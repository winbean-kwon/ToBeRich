#!/bin/bash
# F7 재개: 기록 안 된 중단 시도를 attempts.jsonl에 남기고(재부팅·강제 종료), tmux rat_f7에서 본 실행 스크립트를 다시 띄운다.
# 사전 등록 스크립트(replication/funnel_f7_rat_local.py)는 수정하지 않는다. 끝난 실행은 그 스크립트가 건너뛴다.
OUT=~/ToBeRich/data/funnel/rat_f7_gtx1650
if tmux has-session -t rat_f7 2>/dev/null; then echo "rat_f7 세션이 이미 있습니다. tmux attach -t rat_f7"; exit 0; fi
if pgrep -f "[r]un_rat_f7.py" >/dev/null; then echo "학습 프로세스가 이미 돌고 있습니다. 중단합니다."; exit 1; fi
python3 - "$OUT" <<'PY'
import json, pathlib, sys, time
out = pathlib.Path(sys.argv[1])
for rd in sorted(out.glob('[PR][1-5]')):
    if (rd / 'done.json').exists():
        continue
    af = rd / 'attempts.jsonl'
    rec = [json.loads(l) for l in open(af)] if af.exists() else []
    nrec = {r['attempt'] for r in rec}
    for tf in sorted(rd.glob('times.attempt*.jsonl')):
        n = int(tf.stem.split('attempt')[1])
        if n in nrec:
            continue
        evs = []
        for l in open(tf, errors='ignore'):
            try: evs.append(json.loads(l))
            except ValueError: pass
        t0 = evs[0]['t'] if evs else None
        last = evs[-1] if evs else {}
        steps = [e['step'] for e in evs if e.get('ev') == 'step']
        r = {'attempt': n, 'rc': None, 'killed_at_cap': False, 'ok': False, 'interrupted': 'reboot_or_kill(기록 스크립트가 사후 기록)',
             'seconds': (last.get('t', t0) - t0) if t0 else None, 'last_step_mark': steps[-1] if steps else None,
             'events_tail': [e.get('ev') for e in evs[-6:]], 'recorded_at': time.time()}
        with open(af, 'a') as f: f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(rd.name, '중단 시도 기록:', json.dumps(r, ensure_ascii=False))
PY
if [ "$1" = "--record-only" ]; then echo "기록만 하고 시작하지 않음"; exit 0; fi
tmux new-session -d -s rat_f7 "cd ~/ToBeRich && python3 replication/funnel_f7_rat_local.py 2>&1 | tee -a ~/f4work/rat_f7_run.log"
sleep 5; tmux ls; echo "재개함. 진행: cat $OUT/*/done.json"
