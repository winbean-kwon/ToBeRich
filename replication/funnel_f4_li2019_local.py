# -*- coding: utf-8 -*-
# li2019adaptive(Adaptive DDPG) F4 로컬 실행(서버 WSL CPU). notes/funnel_f4_li2019adaptive.md 2절 그대로.
# 설치 → 관문 → 1에폭 학습 + 시험 경로(--play) 1회. 성과(표준출력·Adaptive DDPG.txt·그림)는 열지 않는다.
# 사용: python3 replication/funnel_f4_li2019_local.py [--install-only]
import json, os, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
SRC = HOME / 'f4work' / 'adaptive_ddpg_inspect' / 'repo'      # 정적 확인 때 받은 저장소(HEAD 326640a)
WORK = HOME / 'f4work' / 'li2019'
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'li2019'
CAP = 3 * 3600
MAX_ATT = 3
WORK.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

INSTALL_SH = r'''
set -e
mkdir -p "$W/out"
if [ -f "$W/out/env_ok" ]; then echo "환경이 이미 있음"; exit 0; fi
step(){ n=$1; shift; echo "== $n"; if ! "$@" > "$W/out/install_$n.log" 2>&1; then echo "실패: $n"; tail -25 "$W/out/install_$n.log"; exit 1; fi; tail -1 "$W/out/install_$n.log"; }
cd "$S"
echo "8481a9c8594226389138d1b5efdb072933bf175f7168228315d881ead859c560  baselines.zip" | sha256sum -c
echo "d58a57f0add495ba434bc309fecf974d4132adeed5d1422e7c4d0d2bed12ffb4  gym.zip" | sha256sum -c
rm -rf "$W/src" "$W/p37"; mkdir -p "$W/src"
cd "$W/src" && unzip -q "$S/baselines.zip" && unzip -q "$S/gym.zip" && rm -rf "$W/gym_copy" && mv "$W/src/gym" "$W/gym_copy" && ls && cd "$W"
MM=$HOME/f4work/ensemble/bin/micromamba
step py37 $MM create -y -p "$W/p37" -c conda-forge python=3.7 pip
P="$W/p37/bin/python -m pip --default-timeout=120 --retries 5"
step core $P install -q numpy==1.16.4 pandas==1.0.3 scipy==1.4.1 matplotlib==3.2.1 tensorflow==1.15.2 "protobuf<3.20"
BL="$W/src/baselines"; echo "baselines=$BL gym=bundled package dir $W/gym_copy" > "$W/out/src_paths.txt"
# gym 사본은 site-packages의 패키지 폴더 자체(setup.py 없음, version 0.10.0)다. pip로 같은 버전을 깔아 의존성을 맞춘 뒤
# 설치된 gym 폴더를 사본으로 바꾼다(저자 환경 = site-packages gym을 고친 것과 같은 상태).
step gym $P install -q gym==0.10.0
SP=$(cd / && "$W/p37/bin/python" -c "import gym,os;print(os.path.dirname(os.path.dirname(gym.__file__)))")
[ -n "$SP" ] && rm -rf "$SP/gym" && cp -r "$W/gym_copy" "$SP/gym" && rm -rf "$SP/gym/__pycache__"
GYM="$SP"
step baselines $P install -q -e "$BL"
step repin $P install -q --force-reinstall --no-deps numpy==1.16.4 pandas==1.0.3 scipy==1.4.1 matplotlib==3.2.1
# 허용 수정 1: README가 지시한 경로 교체(접두어만)
PD="$GYM/gym/envs/portfolio"
for f in "$PD/portfolio_env.py" "$PD/portfolio_testenv.py"; do
  sed -i "s#E:/Anaconda3/envs/tensorflow/Lib/site-packages/gym/envs/portfolio/#$PD/#g; s#E:/Anaconda3/envs/tensorflow/Lib/site-packages/gym/envs/zxstock/#$PD/#g" "$f"
done
! grep -n "E:/" "$PD/portfolio_env.py" "$PD/portfolio_testenv.py"
mkdir -p "$PD/Data_Daily_Stock_Dow_Jones_30/DQN"
touch "$W/out/env_ok"
'''

GATE = r'''
import sys, numpy, pandas, tensorflow, gym
assert sys.version_info[:2] == (3, 7) and tensorflow.__version__ == '1.15.2' and numpy.__version__ == '1.16.4'
print('python', sys.version.split()[0], 'tf', tensorflow.__version__, 'gym', gym.__version__, 'numpy', numpy.__version__, 'pandas', pandas.__version__)
import baselines.run, gym.envs.portfolio
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
    sh(f'MPLBACKEND=Agg {py} {WORK}/out/gate.py {ok} > {WORK}/out/install_versions.log 2>&1')
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
        p = subprocess.Popen([py, '-m', 'baselines.run', '--num_timesteps=25000', '--seed=0', '--play'],
                             cwd=str(run), stdout=fo, stderr=fe, env=dict(os.environ, OPENAI_LOGDIR=str(run / 'oailog'), MPLBACKEND='Agg'))
        try:
            rc = p.wait(timeout=CAP); capped = False
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); rc = None; capped = True
    sec = time.time() - t0
    marker = (run / 'Adaptive DDPG.txt').exists()   # 존재만 확인, 열지 않음
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
