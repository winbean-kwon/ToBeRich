# -*- coding: utf-8 -*-
# ADRLwIntReward(ICAIF 2024) F4 로컬 실행(서버 WSL CPU). notes/funnel_f4_adrl.md 2절 그대로.
# 설치 → 관문 → A2C_autoregressive_run.py를 그대로 실행하고, 첫 단위(보상 profit, 시드 6280, 18사이클 학습·검증·거래)가
# SUMMARYRESULTS.csv에 첫 줄을 쓰면 멈춘다(사전 고정한 정지 조건). 성과(stdout·results/ CSV)는 열지 않는다.
# 사용: python3 replication/funnel_f4_adrl_local.py [--install-only]
import json, os, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
REPO = HOME / 'f4work' / 'adrl' / 'repo'      # cspun/ADRLwIntReward clone
HEAD = '2e73349'
WORK = HOME / 'f4work' / 'adrl'
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'adrl'
CAP = 3 * 3600
MAX_ATT = 3
WORK.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

INSTALL_SH = r'''
set -e
mkdir -p "$W/out"
if [ -f "$W/out/env_ok" ]; then echo "환경이 이미 있음"; exit 0; fi
step(){ n=$1; shift; echo "== $n"; if ! "$@" > "$W/out/install_$n.log" 2>&1; then echo "실패: $n"; tail -25 "$W/out/install_$n.log"; exit 1; fi; tail -1 "$W/out/install_$n.log"; }
[ "$(git -C "$R" rev-parse --short=7 HEAD)" = "$H" ]
rm -rf "$W/p37"
MM=$HOME/f4work/ensemble/bin/micromamba
step py37 $MM create -y -p "$W/p37" -c conda-forge python=3.7 pip
P="$W/p37/bin/python -m pip --default-timeout=120 --retries 5"
# requirements.txt 고정값(numpy 1.16.4, pandas 1.0.3, scikit-learn 0.21.0, gym 0.15.3, tensorflow 1.15.4, joblib 0.15.1, matplotlib 3.2.1)
step core $P install -q numpy==1.16.4 pandas==1.0.3 scikit-learn==0.21.0 gym==0.15.3 tensorflow==1.15.4 joblib==0.15.1 matplotlib==3.2.1 "protobuf<3.20"
# requirements에 판이 없는 것: stockstats·quantstats(코드가 import)와 번들 stable_baselines 의존성
step extra $P install -q stockstats==0.3.2 quantstats==0.0.59 cloudpickle==1.6.0 opencv-python-headless==4.2.0.34
step repin $P install -q --force-reinstall --no-deps numpy==1.16.4 pandas==1.0.3 scikit-learn==0.21.0 matplotlib==3.2.1
touch "$W/out/env_ok"
'''

GATE = r'''
import os, sys
os.chdir(sys.argv[2]); sys.path.insert(0, sys.argv[2])
import numpy, pandas, tensorflow, gym, quantstats
print('python', sys.version.split()[0], 'tf', tensorflow.__version__, 'gym', gym.__version__, 'numpy', numpy.__version__, 'pandas', pandas.__version__)
from stable_baselines import A2C_autoregressive
from stable_baselines.common.vec_env import DummyVecEnv
from preprocessing.preprocessors import *
from env.EnvMultipleStock_train_A import StockEnvTrain
from env.EnvMultipleStock_validation_A import StockEnvValidation
from env.EnvMultipleStock_trade_A import StockEnvTrade
print('import ok')
open(sys.argv[1], 'w').write('1')
'''


def sh(cmd, **kw):
    return subprocess.run(['bash', '-c', cmd], **kw)


def main():
    r = sh(INSTALL_SH, env=dict(os.environ, W=str(WORK), R=str(REPO), H=HEAD))
    if r.returncode:
        raise SystemExit('설치 실패(본 실행 시도 아님)')
    py = str(WORK / 'p37' / 'bin' / 'python')
    (WORK / 'out' / 'gate.py').write_text(GATE)
    ok = WORK / 'out' / 'gate_ok'
    # 관문은 저장소 사본에서(config.py가 import 시 trained_models/<시각>을 만든다)
    g = WORK / 'gate_copy'
    sh(f'rm -rf {g} && mkdir -p {g} && git -C {REPO} archive {HEAD} | tar -x -C {g}')
    sh(f'MPLBACKEND=Agg {py} {WORK}/out/gate.py {ok} {g} > {WORK}/out/install_versions.log 2>&1')
    print((WORK / 'out' / 'install_versions.log').read_text()[-600:])
    if not ok.exists():
        raise SystemExit('관문 실패')
    if '--install-only' in sys.argv:
        return
    if (OUT / 'done.json').exists():
        print('이미 끝남', (OUT / 'done.json').read_text()); return
    atts = sorted(OUT.glob('attempt*.json'))
    if len(atts) >= MAX_ATT:
        (OUT / 'done.json').write_text(json.dumps({'status': 'F4 실패(시도 3회)'}, ensure_ascii=False)); return
    att = len(atts) + 1
    run = WORK / f'run{att}'
    sh(f'rm -rf {run} && mkdir -p {run} && git -C {REPO} archive {HEAD} | tar -x -C {run}')
    # 허용 수정(출력 폴더): 코드가 쓰는 results/·results/autoA2C/<보상>/를 만든다(코드 무수정)
    for rf in ['profit', 'logreturn', 'csr', 'dsr1', 'dsr2']:
        (run / 'results' / 'autoA2C' / rf).mkdir(parents=True, exist_ok=True)
    marker = run / 'results' / 'autoA2C' / 'profit' / 'SUMMARYRESULTS.csv'
    (OUT / f'attempt{att}.json').write_text(json.dumps({'attempt': att, 'start': time.time()}))
    t0 = time.time(); stopped = False; capped = False
    with open(run / 'stdout.log', 'w') as fo, open(run / 'stderr.log', 'w') as fe:
        p = subprocess.Popen([py, 'A2C_autoregressive_run.py'], cwd=str(run), stdout=fo, stderr=fe,
                             env=dict(os.environ, MPLBACKEND='Agg', CUDA_VISIBLE_DEVICES=''))
        while p.poll() is None:
            if marker.exists() and marker.stat().st_size > 0:      # 존재·크기만 확인, 열지 않음
                time.sleep(5); p.terminate(); p.wait(); stopped = True; break
            if time.time() - t0 > CAP:
                p.kill(); p.wait(); capped = True; break
            time.sleep(10)
    rc = p.returncode
    sec = time.time() - t0
    m = marker.exists() and marker.stat().st_size > 0
    res = {'attempt': att, 'rc': rc, 'capped': capped, 'stopped_at_marker': stopped, 'seconds': round(sec, 1), 'marker_exists': m}
    if stopped and m:
        res['status'] = 'F4 통과(첫 단위: profit·시드 6280·18사이클)'
    elif capped:
        res['status'] = '상한 내 미완'
    else:
        res['status'] = 'F4 실패(시도)'
        res['stderr_tail'] = (run / 'stderr.log').read_text(errors='ignore').splitlines()[-40:]
    (OUT / f'attempt{att}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    if res['status'] != 'F4 실패(시도)':
        (OUT / 'done.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != 'stderr_tail'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
