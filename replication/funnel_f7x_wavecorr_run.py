# -*- coding: utf-8 -*-
"""Exploratory F7x WaveCorr runner (notes/funnel_f7x_wavecorr_prereg.md). Server WSL, CPU.

Reuses the F4 environment (~/f4work/wavecorr: p37 python, repo @20ff832, hash gate) and the F4 split-exec wrapper:
wavecorr_run.py is executed up to the data-loading marker, train_mode is set to 0 (blocks the 10-run dispatch),
everything else (epochs=3000, hyperparameters, data loading, network) is the author's code; then
runSingleExperiment(seed, 1) is called once per seed. Seeds = the first five seeds of the author's
differentSeedExperiments(seed=1111): 1112..1116.
Concurrency: at most 2 seeds at a time, a new seed starts only if MemAvailable >= 1.0 GB.
Completion (prereg 2, after review): rc == 0 and track_test_train_.csv has 3000 rows -> 'ok'; rc == 0 with fewer rows
or no file -> 'early_stop' (the code's zero-turnover return; a valid outcome, not retried); rc != 0 -> retried from
scratch (result folder deleted before every attempt), at most 3 attempts. Leftover seed_run.py processes are killed
at start-up.
Non-exposure: stdout/stderr go to files that are not opened; progress = done.json / attempts.jsonl only.
Usage: python3 funnel_f7x_wavecorr_run.py            (on the server, in ~/ToBeRich)
"""
import calendar
import hashlib
import shutil
import json
import os
import pathlib
import subprocess
import time

HOME = pathlib.Path.home()
WORK = HOME / 'f4work' / 'wavecorr'
SRC = WORK / 'repo' / 'src'
PY37 = str(WORK / 'p37' / 'bin' / 'python')
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'wavecorr_f7x'
SEEDS = [1112, 1113, 1114, 1115, 1116]
MAX_PAR, MIN_MEM_KB, MAX_ATTEMPTS = 2, 1_000_000, 3
DEADLINE = calendar.timegm(time.strptime('2026-11-29 00:00', '%Y-%m-%d %H:%M')) - 9 * 3600  # 2026-11-29 00:00 KST
HASHES = {
    'wavecorr_run.py': 'dbad7de02a87339dd2991ec2def926c81786920b6974b0c0896760f650436d3b',
    'wavecorr_agent.py': '1b9e83c18e339fdefc673e4409251a0e6886025e241bde2e52511cac34fc7193',
    'wavecorr_network.py': '69ee695e28c92c76861689e453f556045d75f1b1fe5e8d195d35742d67516559',
    'wavecorr_input.py': 'a5c3eaf90cf4281a1094d6c74283b743f412a1f2b6584a57ebf6e56e516252ae',
    'wavecorr_enum.py': '7df5a5ccee48c40293ac68547d63acf48258b351a1c0dd990485782a5285c2a5',
}

SEED_PY = r'''# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.getcwd())
SEED = int(os.environ['WC_SEED'])
os.makedirs('results', exist_ok=True)
src = open('wavecorr_run.py', encoding='utf-8').read()
CUTLINE = "\n# load the data from the assigned data set\n"
assert src.count(CUTLINE) == 1
head, rest = src.split(CUTLINE)
g = {'__name__': 'wavecorr_run_head', '__builtins__': __builtins__}
exec(compile(head, 'wavecorr_run.py', 'exec'), g)
assert g['epochs'] == 3000 and g['dataset_name'] == 'can' and g['tradeFee'] == 0.0005
g['train_mode'] = 0
exec(compile(CUTLINE.lstrip('\n') + rest, 'wavecorr_run.py', 'exec'), g)
g['runSingleExperiment'](SEED, 1)
'''


def mem_available_kb():
    for line in open('/proc/meminfo'):
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])
    return 0


def log(name, **kw):
    kw['t'] = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(OUT / name, 'a') as f:
        f.write(json.dumps(kw, ensure_ascii=False) + '\n')


def res_dir(seed):
    return SRC / 'results' / f'can_waveCorr_50stocks_seed{seed}_permutation1'


def track_rows(seed):
    p = res_dir(seed) / 'track_test_train_.csv'
    return sum(1 for line in open(p) if line.strip()) if p.exists() else 0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(['pkill', '-f', str(OUT / 'seed_run.py')])
    for f, h in HASHES.items():
        a = hashlib.sha256((SRC / f).read_bytes()).hexdigest()
        assert a == h, f'hash mismatch {f}'
    assert (WORK / 'out' / 'gate_ok.txt').exists(), 'F4 gate file missing'
    (OUT / 'seed_run.py').write_text(SEED_PY)
    files = os.listdir(str(SRC / 'data' / 'can'))
    (OUT / 'loaded_stocks.json').write_text(json.dumps({'listdir_order_first50': files[:50], 'n_files': len(files)}, indent=1))
    attempts = {s: 0 for s in SEEDS}
    done = {s: (OUT / f'seed{s}' / 'done.json').exists() for s in SEEDS}
    running = {}
    peak = {}
    while True:
        for s, (p, t0) in list(running.items()):
            try:
                for line in open(f'/proc/{p.pid}/status'):
                    if line.startswith('VmHWM:'):
                        peak[s] = max(peak.get(s, 0), int(line.split()[1]))
            except OSError:
                pass
            rc = p.poll()
            if rc is None:
                continue
            del running[s]
            rows = track_rows(s)
            status = ('ok' if rows == 3000 else 'early_stop') if rc == 0 else 'error'
            log('attempts.jsonl', seed=s, attempt=attempts[s], rc=rc, status=status, track_rows=rows,
                hours=round((time.time() - t0) / 3600, 3), peak_rss_kb=peak.get(s))
            if status != 'error':
                d = OUT / f'seed{s}'
                d.mkdir(exist_ok=True)
                (d / 'done.json').write_text(json.dumps({'status': status, 'attempt': attempts[s], 'track_rows': rows}))
                done[s] = True
        if all(done.values()):
            log('attempts.jsonl', event='all_done')
            break
        if time.time() > DEADLINE:
            log('attempts.jsonl', event='deadline', running=list(running))
            for p, _ in running.values():
                p.kill()
            break
        pending = [s for s in SEEDS if not done[s] and s not in running and attempts[s] < MAX_ATTEMPTS]
        if not pending and not running:
            log('attempts.jsonl', event='stopped_with_failures')
            break
        if pending and len(running) < MAX_PAR and mem_available_kb() >= MIN_MEM_KB:
            s = pending[0]
            attempts[s] += 1
            d = OUT / f'seed{s}'
            d.mkdir(exist_ok=True)
            shutil.rmtree(res_dir(s), ignore_errors=True)
            env = dict(os.environ, WC_SEED=str(s))
            p = subprocess.Popen([PY37, str(OUT / 'seed_run.py')], cwd=str(SRC), env=env,
                                 stdout=open(d / f'stdout.attempt{attempts[s]}.log', 'w'),
                                 stderr=open(d / f'stderr.attempt{attempts[s]}.log', 'w'))
            running[s] = (p, time.time())
            log('attempts.jsonl', seed=s, attempt=attempts[s], event='start', mem_available_kb=mem_available_kb())
            time.sleep(60)
        time.sleep(30)


if __name__ == '__main__':
    main()
