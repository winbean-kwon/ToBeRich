# -*- coding: utf-8 -*-
# SmartFolio(IJCAI 2025) F4 로컬 실행(서버 WSL CPU). notes/funnel_f4_smartfolio.md 2절 그대로.
# 설치 → 관문 → main.py 기본 설정 1회(코드상 외곽 1에폭: IRL 보상 학습 후 학습 배치마다 PPO 10,000스텝 + 시험 예측).
# 성과(표준출력의 예측 지표)는 열지 않는다. 판정은 종료 코드·시간·래퍼 이벤트(예측 호출 횟수)로만 한다.
# 사용: python3 replication/funnel_f4_smartfolio_local.py [--install-only]
import json, os, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
REPO = HOME / 'f4work' / 'smartfolio' / 'repo'      # ChloeWenyiZhang/SmartFolio clone
HEAD = '013e089'
WORK = HOME / 'f4work' / 'smartfolio'
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'smartfolio'
CAP = 3 * 3600
MAX_ATT = 3
WORK.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

INSTALL_SH = r'''
set -e
mkdir -p "$W/out"
if [ -f "$W/out/env_ok" ]; then echo "환경이 이미 있음"; exit 0; fi
step(){ n=$1; shift; echo "== $n"; if ! "$@" > "$W/out/install_$n.log" 2>&1; then echo "실패: $n"; tail -25 "$W/out/install_$n.log"; exit 1; fi; tail -1 "$W/out/install_$n.log"; }
[ "$(git -C "$R" rev-parse --short=7 HEAD)" = "$H" ]
rm -rf "$W/p39"
MM=$HOME/f4work/ensemble/bin/micromamba
step py39 $MM create -y -p "$W/p39" -c conda-forge python=3.9 pip
P="$W/p39/bin/python -m pip --default-timeout=120 --retries 5"
# gym 0.21은 새 setuptools·wheel로 빌드가 깨진다(알려진 문제) → 설치 도구를 그 시점 판으로 내린다
step tools $P install -q "pip<24" "setuptools==65.5.0" "wheel==0.38.4"
step torch $P install -q torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu
step core $P install -q "numpy==1.23.5" "pandas==1.5.3" "scipy==1.10.1" "scikit-learn==1.2.2"
step gym $P install -q --no-build-isolation gym==0.21.0
step sb3 $P install -q stable-baselines3==1.8.0
step pyg $P install -q torch_geometric==2.3.1
touch "$W/out/env_ok"
'''

GATE = r'''
import sys, numpy, pandas, torch, gym, stable_baselines3, torch_geometric
print('python', sys.version.split()[0], 'torch', torch.__version__, 'gym', gym.__version__, 'sb3', stable_baselines3.__version__,
      'pyg', torch_geometric.__version__, 'numpy', numpy.__version__, 'pandas', pandas.__version__)
sys.path.insert(0, sys.argv[2]); sys.path.append(sys.argv[2] + '/model')   # 경로 수정: policy.py의 'from model import HGAT'
import os; os.chdir(sys.argv[2])
from dataloader.data_loader import *
from policy.policy import *
from trainer.irl_trainer import *
from torch_geometric.loader import DataLoader
print('import ok')
open(sys.argv[1], 'w').write('1')
'''

# 허용 수정 4(결과 기록): model_predict 호출 시작·끝만 이벤트로 남긴다(동작은 그대로).
RUNNER = r'''
import json, sys, time, runpy
ev = open(sys.argv[1], 'a')
def mark(e, **k):
    ev.write(json.dumps(dict(ev=e, t=time.time(), **k)) + '\n'); ev.flush()
import trainer.irl_trainer as T
_mp = T.model_predict
_n = [0]
def model_predict(*a, **k):
    _n[0] += 1; mark('predict_start', n=_n[0])
    r = _mp(*a, **k)
    mark('predict_end', n=_n[0]); return r
T.model_predict = model_predict
mark('main_start')
sys.argv = ['main.py']
runpy.run_path('main.py', run_name='__main__')
mark('main_end', n_predict=_n[0])
'''


def sh(cmd, **kw):
    return subprocess.run(['bash', '-c', cmd], **kw)


def main():
    r = sh(INSTALL_SH, env=dict(os.environ, W=str(WORK), R=str(REPO), H=HEAD))
    if r.returncode:
        raise SystemExit('설치 실패(본 실행 시도 아님)')
    py = str(WORK / 'p39' / 'bin' / 'python')
    (WORK / 'out' / 'gate.py').write_text(GATE)
    ok = WORK / 'out' / 'gate_ok'
    sh(f'cd {REPO} && CUDA_VISIBLE_DEVICES="" {py} {WORK}/out/gate.py {ok} {REPO} > {WORK}/out/install_versions.log 2>&1')
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
    run = WORK / f'run{att}'; sh(f'rm -rf {run}'); run.mkdir()
    # 시도 2부터(사용자 결정 2026-11-13): 저장소 사본을 실행 폴더에 풀고, 저자 생성 스크립트로 학습 데이터를 다시 만든다(코드 무수정).
    code = run / 'code'
    assert sh(f'mkdir -p {code} && git -C {REPO} archive {HEAD} | tar -x -C {code}').returncode == 0
    (code / 'dataset_default').symlink_to('dataset')   # 허용 수정(경로)
    pip = f'{py} -m pip --default-timeout=120 --retries 5'
    assert sh(f'{pip} install -q networkx==3.1 tqdm==4.66.1 > {run}/install_gen.log 2>&1').returncode == 0
    (OUT / f'attempt{att}.json').write_text(json.dumps({'attempt': att, 'start': time.time(), 'stage': 'build'}))
    tb = time.time()
    rb = sh(f'cd {code}/gen_data && CUDA_VISIBLE_DEVICES="" PYTHONPATH={code}:{code}/model timeout {CAP} {py} train_predict_data.py > {run}/build_stdout.log 2> {run}/build_stderr.log')
    build = {'rc': rb.returncode, 'seconds': round(time.time() - tb, 1)}
    chk = sh(f'cd {code} && {py} -c "import pickle,glob; fs=sorted(glob.glob(\'dataset/data_train_predict_hs300/1_hy/*.pkl\')); d=pickle.load(open(fs[0],\'rb\')); print(len(fs), sorted(d.keys()), tuple(d[\'features\'].shape))"',
             capture_output=True, text=True)
    build['check'] = chk.stdout.strip()[-300:]
    if rb.returncode != 0 or 'pyg_data' not in chk.stdout:
        res = {'attempt': att, 'stage': 'build', 'build': build, 'status': 'F4 실패(시도)',
               'stderr_tail': (run / 'build_stderr.log').read_text(errors='ignore').splitlines()[-40:]}
        (OUT / f'attempt{att}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
        print(json.dumps({k: v for k, v in res.items() if k != 'stderr_tail'}, ensure_ascii=False)); return
    (run / 'runner.py').write_text(RUNNER)
    t0 = time.time()
    with open(run / 'stdout.log', 'w') as fo, open(run / 'stderr.log', 'w') as fe:
        p = subprocess.Popen([py, str(run / 'runner.py'), str(run / 'events.jsonl')], cwd=str(code), stdout=fo, stderr=fe,
                             env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=f'{code}:{code}/model'))
        try:
            rc = p.wait(timeout=CAP); capped = False
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); rc = None; capped = True
    sec = time.time() - t0
    evs = [json.loads(l) for l in open(run / 'events.jsonl')] if (run / 'events.jsonl').exists() else []
    n_pred = sum(e['ev'] == 'predict_end' for e in evs)
    main_end = any(e['ev'] == 'main_end' for e in evs)
    res = {'attempt': att, 'build': build, 'rc': rc, 'capped': capped, 'seconds': round(sec, 1), 'n_predict_end': n_pred, 'main_end': main_end}
    if capped:
        res['status'] = '상한 내 미완' + (f'(시험 예측 {n_pred}회 완료)' if n_pred else '')
    elif rc == 0 and main_end and n_pred >= 1:
        res['status'] = 'F4 통과(main.py 기본 설정 1회)'
    else:
        res['status'] = 'F4 실패(시도)'
        res['stderr_tail'] = (run / 'stderr.log').read_text(errors='ignore').splitlines()[-40:]
    (OUT / f'attempt{att}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    if res['status'] != 'F4 실패(시도)':
        (OUT / 'done.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != 'stderr_tail'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
