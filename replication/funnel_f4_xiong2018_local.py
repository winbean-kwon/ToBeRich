# -*- coding: utf-8 -*-
# xiong2018ddpg(Practical DRL) F4 로컬 실행(서버 WSL CPU). notes/funnel_f4_xiong2018ddpg.md 2절 그대로.
# 설치 → 관문 → 1에폭 학습 + 시험 경로(--play) 1회. 성과(표준출력·Adaptive DDPG.txt·그림)는 열지 않는다.
# 사용: python3 replication/funnel_f4_li2019_local.py [--install-only]
import json, os, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
SRC = HOME / 'f4work' / 'practical_drl_inspect' / 'repo'      # 정적 확인 때 받은 저장소(HEAD e59b994)
WORK = HOME / 'f4work' / 'xiong2018'
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'xiong2018'
CAP = 3 * 3600
MAX_ATT = 3
WORK.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

INSTALL_SH = r'''
set -e
mkdir -p "$W/out"
if [ -f "$W/out/env_ok" ]; then echo "환경이 이미 있음"; exit 0; fi
step(){ n=$1; shift; echo "== $n"; if ! "$@" > "$W/out/install_$n.log" 2>&1; then echo "실패: $n"; tail -25 "$W/out/install_$n.log"; exit 1; fi; tail -1 "$W/out/install_$n.log"; }
rm -rf "$W/src" "$W/p37"; mkdir -p "$W/src"
git -C "$S" archive e59b994 | tar -x -C "$W/src"
cd "$W/src"
sha256sum run.py gym/envs/rlstock/rlstock_env.py gym/envs/rlstock/rlstock_testenv.py | tee "$W/out/main_sha.txt"
grep -q '^b780bb890f499bc3f64b1a12b5e39af2028dcc6ac1f4ffa302ba72a43f4e5246  run.py' "$W/out/main_sha.txt"
grep -q '^81f7436a8d7c71faccf29077bdab42d04423e1fb6ae2601e202298a47a80d5ec  gym/envs/rlstock/rlstock_env.py' "$W/out/main_sha.txt"
grep -q '^3de1b4ae96b6c2585eeb48f4b02cd8a0f3938500d1497ec6fa66daff4f9020bb  gym/envs/rlstock/rlstock_testenv.py' "$W/out/main_sha.txt"
curl -sL https://github.com/openai/baselines/archive/7bfbcf177eca8f46c0c0bfbb378e044539f5e061.tar.gz | tar -xz -C "$W/src" && mv "$W/src/baselines-7bfbcf177eca8f46c0c0bfbb378e044539f5e061" "$W/src/baselines"
cd "$W"
cp "$W/src/run.py" "$W/src/baselines/baselines/run.py"
MM=$HOME/f4work/ensemble/bin/micromamba
step py37 $MM create -y -p "$W/p37" -c conda-forge python=3.7 pip
P="$W/p37/bin/python -m pip --default-timeout=120 --retries 5"
step core $P install -q numpy==1.16.4 pandas==1.0.3 scipy==1.4.1 matplotlib==3.2.1 tensorflow==1.14.0 "protobuf<3.20"
step gym $P install -q gym==0.15.7
step baselines $P install -q -e "$W/src/baselines"
step repin $P install -q --force-reinstall --no-deps numpy==1.16.4 pandas==1.0.3 scipy==1.4.1 matplotlib==3.2.1
# README Step 7·8: rlstock 폴더를 설치된 gym/envs로 복사하고 두 env를 등록한다
GE=$(cd / && "$W/p37/bin/python" -c "import gym,os;print(os.path.dirname(gym.__file__))")/envs
cp -r "$W/src/gym/envs/rlstock" "$GE/"
grep -q "RLStock-v0" "$GE/__init__.py" || printf "\nregister(\n    id='RLStock-v0',\n    entry_point='gym.envs.rlstock:StockEnv',\n)\nregister(\n    id='RLTestStock-v0',\n    entry_point='gym.envs.rlstock:StockTestEnv',\n)\n" >> "$GE/__init__.py"
PD="$GE/rlstock"
for f in "$PD/rlstock_env.py" "$PD/rlstock_testenv.py"; do
  sed -i "s#/Users/hongyangyang/Documents/GitHub/DQN_Stock_Trading/venv/lib/python3.6/site-packages/gym/envs/rlstock/#$PD/#g" "$f"
done
! grep -n "/Users/" "$PD/rlstock_env.py" "$PD/rlstock_testenv.py"
touch "$W/out/env_ok"
'''

GATE = r'''
import sys, numpy, pandas, tensorflow, gym
assert sys.version_info[:2] == (3, 7) and tensorflow.__version__ == '1.14.0' and numpy.__version__ == '1.16.4'
print('python', sys.version.split()[0], 'tf', tensorflow.__version__, 'gym', gym.__version__, 'numpy', numpy.__version__, 'pandas', pandas.__version__)
import baselines.run, gym.envs.rlstock
print('import ok')
open(sys.argv[1], 'w').write('1')
'''


def sh(cmd, **kw):
    return subprocess.run(['bash', '-c', cmd], **kw)


def main():
    r = sh(INSTALL_SH, env=dict(os.environ, W=str(WORK), S=str(SRC)))
    if r.returncode:
        (OUT / 'done.json').write_text(json.dumps({'status': '실행 불가(환경)', 'stage': 'install', 'rc': r.returncode}))
        raise SystemExit('설치 실패')
    py = str(WORK / 'p37' / 'bin' / 'python')
    (WORK / 'out' / 'gate.py').write_text(GATE)
    ok = WORK / 'out' / 'gate_ok'
    sh(f'{py} {WORK}/out/gate.py {ok} > {WORK}/out/install_versions.log 2>&1')
    print((WORK / 'out' / 'install_versions.log').read_text()[-600:])
    if not ok.exists():
        raise SystemExit('관문 실패')
    if '--install-only' in sys.argv:
        return
    if (OUT / 'done.json').exists():
        print('이미 끝남', (OUT / 'done.json').read_text()); return
    atts = list(OUT.glob('attempt*.json'))
    if len(atts) >= MAX_ATT:
        (OUT / 'done.json').write_text(json.dumps({'status': 'F4 실패(시도 3회)'})); return
    att = len(atts) + 1
    run = WORK / f'run{att}'
    sh(f'rm -rf {run}'); run.mkdir()
    (OUT / f'attempt{att}.json').write_text(json.dumps({'attempt': att, 'start': time.time()}))
    t0 = time.time()
    with open(run / 'stdout.log', 'w') as fo, open(run / 'stderr.log', 'w') as fe:
        p = subprocess.Popen([py, '-m', 'baselines.run', '--alg=ddpg', '--env=RLStock-v0', '--network=mlp', '--num_timesteps=25000', '--seed=0', '--play'],
                             cwd=str(run), stdout=fo, stderr=fe, env=dict(os.environ, OPENAI_LOGDIR=str(run / 'oailog')))
        try:
            rc = p.wait(timeout=CAP); capped = False
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); rc = None; capped = True
    sec = time.time() - t0
    marker = (run / 'result_test.png').exists()   # 존재만 확인, 열지 않음
    res = {'attempt': att, 'rc': rc, 'capped': capped, 'seconds': round(sec, 1), 'marker_exists': marker}
    if capped:
        res['status'] = '상한 내 미완'
    elif rc == 0 and marker:
        res['status'] = 'F4 통과(1에폭 기준, 논문 학습 길이 미지정)'
    else:
        res['status'] = 'F4 실패(시도)'
        res['stderr_tail'] = (run / 'stderr.log').read_text(errors='ignore').splitlines()[-40:]
    (OUT / f'attempt{att}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    if res['status'] != 'F4 실패(시도)':
        (OUT / 'done.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != 'stderr_tail'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
