# -*- coding: utf-8 -*-
# 사전 등록 notes/prereg_stat_power_v2.md 그대로의 계산. 입력은 prep.py가 만든 inputs/*.csv(일별 순수익).
# 단계(순서 고정):
#   python run.py selftest            # 코드 점검(합성 자료, 실제 입력 안 씀)
#   python run.py calib               # §5 보정 점검: 크기(ΔSR·ΔG) + ΔG 경계. → out/calib.json
#   python run.py main                # §3 구간·p·MDE·ρ(범주 없음). → out/main.json  (δ_SR 확정 전에는 열지 않는다)
#   python run.py calib_srb           # §5 ΔSR 경계 점검. delta_sr.json(커밋된 δ_SR) 필요 → out/calib_srb.json
#   python run.py categorize          # §4 범주·Holm·블록 민감도·O2 대조. delta_sr.json 필요 → out/categories.json
# 공통 정의
# - 표본: 각 층(창) X = (T, 1+K) 행렬, 열 0 = 기준선, 열 1..K = 정책 실행(시드). 통계량 θ = 층 평균(층 안은 실행 평균) Δ.
# - ΔSR: SR = √252·μ/σ(모집단 적률, ddof=0). ΔG = 252·mean(log(1+r_p) − log(1+r_e)) (연율 로그 성장 차, 소수).
# - 영향 함수 φ_t: 층마다 실행 평균 IF(정책) − IF(기준선). Var(θ̂) = (1/S²)·Σ_s Ω_s/T_s.
#   원표본 Ω = HAC(Parzen, Andrews 1991 AR(1) 자동 대역폭, prewhitening 없음).
#   부트스트랩 Ω* = Götze–Künsch: (1/l)·Σ_j (b^{-1/2}·Σ_{t∈블록 j} φ*_t)².
# - 원형 블록 부트스트랩: 층마다 l = ⌊T/b⌋ 블록, 날짜 블록을 기준선·모든 실행에 공통으로(시드 조건부).
# - p(양측) = (1 + #{|t*| ≥ |θ̂|/se})/(B+1), t* = (θ* − θ̂)/se*  (LW 2008 식 9의 스튜던트화 양측 p).
#   95% CI = θ̂ ± q_{0.95}(|t*|)·se. 단측 경계(1 − a1): 상한 = θ̂ − q_{a1}(t*)·se, 하한 = θ̂ − q_{1−a1}(t*)·se, a1 = α/4.
#   [하한, 상한]이 TOST (1 − 2·a1) 구간이다. MDE = (z_.975 + z_.8)·sd(θ*).
# - 2단계(보조): 층마다 실행 열을 복원 추출한 뒤 날짜 블록 재표본, θ*의 2.5·97.5 백분위.
import sys, json, zlib, pathlib, time
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
INP = HERE / 'inputs'
OUT = HERE / 'out'
SEED = 20261113
ALPHA = 0.05
A1 = ALPHA / 4                 # Bonferroni 단측(비우월·TOST)
DELTA_G = float(np.log(1.3601 / 1.3284))   # 원 논문 최소 보고 우위(DDPG 36.01% − DJIA 32.84%, 복리 연수익)를 연율 로그 성장으로 환산 ≈ 0.02358
SQ = np.sqrt(252.0)
ALGOS = ('a2c', 'ppo', 'ddpg', 'td3')
WINS = ('W0', 'W1', 'W2')
B_MAIN, B_CAL = 4999, 999
BLOCKS = (5, 10, 20); B_PRIMARY = 20
N_SIZE, N_BOUND = 1000, 4000   # 경계 점검은 α/4 비율 판정의 이항 오차를 크기 점검과 맞추려 4,000회
GENS = (10, 20)                # 합성 생성: 정상 부트스트랩 평균 블록
TAIL_MAX = 0.04               # 크기 점검 꼬리별 상한(0.025 + 약 2.9 이항 SE, n = 1,000)
MDE_MULT = 1.959963984540054 + 0.8416212335729143


# ---------- 자료 ----------
def read(name):
    import csv
    with open(INP / f'{name}.csv') as fh:
        rows = list(csv.reader(fh))
    head = rows[0][1:]
    X = np.array([[float(v) for v in r[1:]] for r in rows[1:]])
    return head, X, [r[0] for r in rows[1:]]


def targets():
    # 반환: {키: {'strata': [X...], 'group': ..., 'two_stage': bool}}
    t = {}
    F = {w: read(f'F_{w}') for w in WINS}
    for a in ALGOS:
        strata = []
        for w in WINS:
            head, X, _ = F[w]
            cols = [0] + [head.index(f'{a}_s{s}') for s in range(5)]
            strata.append(X[:, cols])
            t[f'F/window/{a}/{w}'] = {'strata': [X[:, cols]], 'group': 'F_window', 'two_stage': False}
            for s in range(5):
                t[f'F/run/{a}/{w}/s{s}'] = {'strata': [X[:, [0, head.index(f'{a}_s{s}')]]], 'group': 'F_run', 'two_stage': False}
        t[f'F/algo/{a}'] = {'strata': strata, 'group': 'F_algo', 'two_stage': True}
    for tag in ('D', 'Dp', 'E'):
        head, X, _ = read(tag)
        t[f'{tag}/method'] = {'strata': [X], 'group': f'{tag}_method', 'two_stage': True}
        for j, n in enumerate(head[1:], start=1):
            t[f'{tag}/run/{n}'] = {'strata': [X[:, [0, j]]], 'group': f'{tag}_run', 'two_stage': False}
    return t


# ---------- 통계량 ----------
def stat(X, metric):
    # X: (..., T, 1+K). 반환 θ(...), φ(..., T) — φ는 표본 평균 0.
    if metric == 'G':
        L = np.log1p(X); d = L[..., 1:] - L[..., :1]
        dm = d.mean(-2)
        return 252.0 * dm.mean(-1), 252.0 * (d.mean(-1) - dm.mean(-1)[..., None])
    mu = X.mean(-2); sd = X.std(-2)
    Z = X - mu[..., None, :]; s = sd[..., None, :]; m = mu[..., None, :]
    IF = SQ * (Z / s - m * (Z ** 2 - s ** 2) / (2 * s ** 3))
    sr = SQ * mu / sd
    return (sr[..., 1:] - sr[..., :1]).mean(-1), IF[..., 1:].mean(-1) - IF[..., 0]


def hac(phi):
    # Parzen 커널, Andrews(1991) AR(1) 자동 대역폭, prewhitening 없음
    x = phi - phi.mean(); T = len(x)
    rho = float(np.clip((x[1:] @ x[:-1]) / (x[:-1] @ x[:-1]), -0.97, 0.97))
    a2 = 4 * rho ** 2 / (1 - rho) ** 4
    S = 2.6614 * (a2 * T) ** 0.2
    om = x @ x / T
    for j in range(1, T):
        z = j / S if S > 0 else np.inf
        if z > 1:
            break
        k = 1 - 6 * z ** 2 + 6 * z ** 3 if z <= 0.5 else 2 * (1 - z) ** 3
        om += 2 * k * (x[j:] @ x[:-j]) / T
    return om


def test(strata, metric, B, b, rng, two_stage=False, chunk=250):
    S = len(strata)
    ths, var = [], 0.0
    for X in strata:
        th, phi = stat(X, metric); ths.append(th); var += hac(phi) / len(phi)
    theta = float(np.mean(ths)); se = float(np.sqrt(var) / S)
    thstar = np.empty(B); tstar = np.empty(B)
    for c0 in range(0, B, chunk):
        n = min(chunk, B - c0); th = np.zeros(n); v = np.zeros(n)
        for X in strata:
            T = len(X); l = T // b
            st = rng.integers(0, T, (n, l))
            idx = ((st[:, :, None] + np.arange(b)) % T).reshape(n, l * b)
            t_, phi = stat(X[idx], metric)
            th += t_
            sums = (phi - phi.mean(-1, keepdims=True)).reshape(n, l, b).sum(-1)
            v += (sums ** 2).mean(-1) / b / (l * b)
        th /= S
        thstar[c0:c0 + n] = th; tstar[c0:c0 + n] = (th - theta) / (np.sqrt(v) / S)
    out = {'theta': theta, 'se_hac': se, 'sd_boot': float(thstar.std(ddof=1)),
           'p_two': float((1 + np.sum(np.abs(tstar) >= abs(theta) / se)) / (B + 1))}
    q95 = float(np.quantile(np.abs(tstar), 0.95))
    out['ci95'] = [theta - q95 * se, theta + q95 * se]
    out['upper_1s'] = theta - float(np.quantile(tstar, A1)) * se
    out['lower_1s'] = theta - float(np.quantile(tstar, 1 - A1)) * se
    out['mde80'] = MDE_MULT * out['sd_boot']
    if two_stage:
        th2 = np.zeros(B)
        for c0 in range(0, B, chunk):
            n = min(chunk, B - c0); th = np.zeros(n)
            for X in strata:
                T, K1 = X.shape; l = T // b
                cols = rng.integers(1, K1, (n, K1 - 1))
                st = rng.integers(0, T, (n, l))
                idx = ((st[:, :, None] + np.arange(b)) % T).reshape(n, l * b)
                Xb = X[idx]
                P = np.take_along_axis(Xb[..., 1:], (cols - 1)[:, None, :], axis=2)
                th += stat(np.concatenate([Xb[..., :1], P], axis=2), metric)[0]
            th2[c0:c0 + n] = th / S
        out['ci95_two_stage'] = [float(np.quantile(th2, 0.025)), float(np.quantile(th2, 0.975))]
    return out


def rho_runs(strata):
    return [float(np.corrcoef(X[:, 0], X[:, k])[0, 1]) for X in strata for k in range(1, X.shape[1])]


def provenance():
    import hashlib, subprocess
    try:
        head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=HERE, capture_output=True, text=True).stdout.strip()
    except Exception:
        head = None
    return {'git_head': head, 'inputs_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                                 for p in sorted(INP.glob('*.csv'))}, 'delta_g': DELTA_G}


def rng_for(*key):
    return np.random.default_rng([SEED] + [zlib.crc32(str(k).encode()) for k in key])


# ---------- 보정 점검 ----------
def stat_boot_idx(T, m, rng):
    # Politis–Romano(1994) 정상 부트스트랩 색인(원형), 평균 블록 m
    new = rng.random(T) < 1.0 / m; new[0] = True
    pos = np.arange(T); last = np.maximum.accumulate(np.where(new, pos, 0))
    starts = rng.integers(0, T, T)
    return (starts[last] + pos - last) % T


def null_pop(X, metric, shift=0.0):
    # 모집단 Δ = shift가 되도록 정책 열을 바꾼다(열마다). ΔSR: r' = (r − μ_p) + (SR_e/√252 + shift/√252)·σ_p.
    X = X.copy(); e = X[:, 0]
    for k in range(1, X.shape[1]):
        p = X[:, k]
        if metric == 'SR':
            X[:, k] = (p - p.mean()) + (e.mean() / e.std() + shift / SQ) * p.std()
        else:
            L = np.log1p(p); X[:, k] = np.expm1(L - L.mean() + np.log1p(e).mean() + shift / 252.0)
    return X


CAL_TARGETS = [f'F/algo/{a}' for a in ALGOS] + ['F/run/ddpg/W2/s0', 'F/run/td3/W2/s0']


def cal_job(args):
    key, metric, shift, m, reps, chunk_id, strata = args
    rng = rng_for('cal', key, metric, shift, m, chunk_id)
    pops = [null_pop(X, metric, shift) for X in strata]
    res = []
    for _ in range(reps):
        syn = [P[stat_boot_idx(len(P), m, rng)] for P in pops]
        r = test(syn, metric, B_CAL, B_PRIMARY, rng)
        res.append((r['p_two'], r['upper_1s'], r['lower_1s'], r['theta']))
    return key, metric, shift, m, res


def run_cal(jobs_spec, out_name, workers=8, per_job=50):
    from multiprocessing import Pool
    T = targets(); jobs = []
    for key, metric, shift, n in jobs_spec:
        for m in GENS:
            for c in range(n // per_job):
                jobs.append((key, metric, shift, m, per_job, c, T[key]['strata']))
    t0 = time.time(); acc = {}
    with Pool(workers) as pool:
        for i, (key, metric, shift, m, res) in enumerate(pool.imap_unordered(cal_job, jobs)):
            acc.setdefault((key, metric, shift, m), []).extend(res)
            if i % 20 == 0:
                print(f'{i + 1}/{len(jobs)} {time.time() - t0:.0f}s', flush=True)
    out = []
    for (key, metric, shift, m), res in sorted(acc.items()):
        a = np.array(res); row = {'target': key, 'metric': metric, 'shift': shift, 'gen_mean_block': m, 'n': len(a)}
        if shift == 0:
            rate = float((a[:, 0] < ALPHA).mean()); lo, hi = 0.03, 0.07; kind = 'size'
            up = float(((a[:, 0] < ALPHA) & (a[:, 3] > 0)).mean()); dn = float(((a[:, 0] < ALPHA) & (a[:, 3] < 0)).mean())
            row.update(reject_upper_tail=up, reject_lower_tail=dn, tail_max=TAIL_MAX)
        else:
            rate = float((a[:, 1] < shift).mean()) if shift > 0 else float((a[:, 2] > shift).mean())
            lo, hi = 0.6 * A1, 1.4 * A1; kind = 'boundary_upper' if shift > 0 else 'boundary_lower'
        row.update(kind=kind, reject_rate=rate, band=[lo, hi],
                   status='통과' if lo <= rate <= hi else ('보수적' if rate < lo else '보정 실패'))
        if kind == 'size' and max(row['reject_upper_tail'], row['reject_lower_tail']) > TAIL_MAX:
            row['status'] = '보정 실패'; row['tail_fail'] = True
        out.append(row)
    summary = {'n_fail': sum(r['status'] == '보정 실패' for r in out), 'n_conservative': sum(r['status'] == '보수적' for r in out),
               'seconds': time.time() - t0, 'B_cal': B_CAL, 'b': B_PRIMARY, 'provenance': provenance(), 'rows': out}
    OUT.mkdir(exist_ok=True)
    (OUT / out_name).write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print('보정 점검 저장', out_name, f"보정 실패 {summary['n_fail']}건, 보수적 {summary['n_conservative']}건")


def cmd_calib():
    spec = [(k, met, 0.0, N_SIZE) for k in CAL_TARGETS for met in ('SR', 'G')]
    spec += [(k, 'G', s, N_BOUND) for k in CAL_TARGETS for s in (DELTA_G, -DELTA_G)]
    run_cal(spec, 'calib.json')


def delta_sr():
    p = HERE / 'delta_sr.json'
    assert p.exists(), 'delta_sr.json(커밋된 δ_SR) 없음'
    return float(json.loads(p.read_text())['delta_sr'])


def cmd_calib_srb():
    d = delta_sr()
    run_cal([(k, 'SR', s, N_BOUND) for k in CAL_TARGETS for s in (d, -d)], 'calib_srb.json')


# ---------- 본 계산 ----------
def main_job(args):
    key, metric, b, strata, two = args
    r = test(strata, metric, B_MAIN, b, rng_for('main', key, metric, b), two_stage=two and b == B_PRIMARY)
    return key, metric, b, r


def cmd_main(workers=8):
    from multiprocessing import Pool
    T = targets(); jobs = []
    for key, v in T.items():
        for metric in ('SR', 'G'):
            for b in BLOCKS:
                jobs.append((key, metric, b, v['strata'], v['two_stage']))
    t0 = time.time(); res = {}
    with Pool(workers) as pool:
        for i, (key, metric, b, r) in enumerate(pool.imap_unordered(main_job, jobs)):
            res.setdefault(key, {}).setdefault(metric, {})[str(b)] = r
            if i % 50 == 0:
                print(f'{i + 1}/{len(jobs)} {time.time() - t0:.0f}s', flush=True)
    for key, v in T.items():
        res[key]['group'] = v['group']; res[key]['rho'] = rho_runs(v['strata'])
        res[key]['T'] = [len(X) for X in v['strata']]
    OUT.mkdir(exist_ok=True)
    import hashlib
    (OUT / 'main.json').write_text(json.dumps({'B': B_MAIN, 'seed': SEED, 'seconds': time.time() - t0,
                                               'provenance': provenance(), 'results': res}, ensure_ascii=False, indent=1))
    h = hashlib.sha256((OUT / 'main.json').read_bytes()).hexdigest()
    (OUT / 'main.sha256').write_text(h + '\n')
    print('본 계산 저장 out/main.json(내용 출력 안 함), sha256', h)


# ---------- 범주(δ_SR 확정 후) ----------
def holm(ps):
    order = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for i, j in enumerate(order):
        run = max(run, (m - i) * ps[j]); adj[j] = min(1.0, run)
    return adj


def category(r, p_holm, delta):
    if p_holm < ALPHA:
        return '우위' if r['theta'] > 0 else '열위'
    if r['lower_1s'] > -delta and r['upper_1s'] < delta:
        return '동등'
    if r['upper_1s'] < delta:
        return '비우월'
    return '판정 불가'


def cmd_categorize():
    M = json.loads((OUT / 'main.json').read_text())['results']
    deltas = {'SR': delta_sr(), 'G': DELTA_G}
    out = {'delta': deltas, 'algo': {}, 'block_sensitive': {}}
    for metric in ('SR', 'G'):
        for b in BLOCKS:
            rs = [M[f'F/algo/{a}'][metric][str(b)] for a in ALGOS]
            adj = holm(np.array([r['p_two'] for r in rs]))
            for a, r, pa in zip(ALGOS, rs, adj):
                d = deltas[metric]
                out['algo'].setdefault(a, {}).setdefault(metric, {})[str(b)] = {
                    'category': category(r, pa, d), 'p_holm': float(pa),
                    'tost_inside': bool(r['lower_1s'] > -d and r['upper_1s'] < d)}
        for a in ALGOS:
            cats = {out['algo'][a][metric][str(b)]['category'] for b in BLOCKS}
            out['block_sensitive'][f'{a}/{metric}'] = len(cats) > 1
    o2 = json.loads((HERE.parent / 'finrl_t3' / 'o2' / 'judge_o2.json').read_text())['주 판정(조건 b, c=0.001, 매일 등가중)']
    cal = []
    for f in ('calib.json', 'calib_srb.json'):
        cal += json.loads((OUT / f).read_text())['rows']
    for a in ALGOS:
        for metric in ('SR', 'G'):
            st = [r['status'] for r in cal if r['target'] == f'F/algo/{a}' and r['metric'] == metric]
            flag = '보정 실패' if '보정 실패' in st else ('보수적' if '보수적' in st else '통과')
            for b in BLOCKS:
                c = out['algo'][a][metric][str(b)]
                if b != B_PRIMARY:
                    c['calibration'] = '보정 점검 대상 아님'; continue
                c['calibration'] = flag
                if flag == '보정 실패':
                    c['category_raw'] = c['category']; c['category'] = '보정 실패(기술 통계만)'
    out['o2_compare'] = {a: {'O2 판정': o2[a]['판정'], 'O2 창별': {w: o2[a]['창별'][w]['분류'] for w in WINS},
                             'ΔG 범주(b=20)': out['algo'][a]['G'][str(B_PRIMARY)]['category'],
                             'ΔSR 범주(b=20)': out['algo'][a]['SR'][str(B_PRIMARY)]['category']} for a in ALGOS}
    (OUT / 'categories.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print('범주 저장 out/categories.json')


# ---------- 자기 점검 ----------
def cmd_selftest():
    rng = np.random.default_rng(0)
    # 1) 영향 함수 = 분포 오염 방향 도함수: θ((1−ε)F̂ + ε·δ_t) − θ(F̂) ≈ ε·φ_t
    X = rng.normal(0.0005, 0.01, (300, 4))
    th, phi = stat(X, 'SR'); eps = 1e-6

    def wsr(X, w):
        mu = w @ X; sd = np.sqrt(w @ (X - mu) ** 2); sr = SQ * mu / sd
        return (sr[1:] - sr[0]).mean()
    for t in (0, 17, 299):
        w = np.full(len(X), (1 - eps) / len(X)); w[t] += eps
        d = (wsr(X, w) - th) / eps
        assert abs(d - phi[t]) < 1e-4 * max(1, abs(phi[t])), (t, d, phi[t])
    # 2) ΔG 점추정
    thg, _ = stat(X, 'G')
    assert abs(thg - 252 * np.mean(np.log1p(X[:, 1:]) - np.log1p(X[:, :1]))) < 1e-12
    # 3) 귀무 모집단의 Δ가 정확히 shift
    for met, s in (('SR', 0.0), ('SR', 0.4), ('G', 0.0), ('G', DELTA_G)):
        assert abs(stat(null_pop(X, met, s), met)[0] - s) < 1e-9, (met, s)
    # 4) iid 귀무 크기(참고, 300회): 큰 모집단을 귀무로 바꾼 뒤 250행을 뽑는다
    pool = rng.normal(0.0004, 0.01, (20000, 2)); pool[:, 1] = 0.9 * pool[:, 0] + np.sqrt(0.19) * pool[:, 1]
    pool = null_pop(pool, 'SR'); rej = 0
    for i in range(300):
        rej += test([pool[rng.integers(0, len(pool), 250)]], 'SR', 499, 20, rng)['p_two'] < 0.05
    print('selftest 통과. iid 귀무 기각률(300회, 참고):', rej / 300)
    # 5) 2단계·holm 동작
    r = test([X, X[:250]], 'G', 199, 10, rng, two_stage=True)
    assert r['ci95_two_stage'][0] <= r['ci95_two_stage'][1]
    assert np.allclose(holm(np.array([0.01, 0.04, 0.03, 0.2])), [0.04, 0.09, 0.09, 0.2])


if __name__ == '__main__':
    {'selftest': cmd_selftest, 'calib': cmd_calib, 'main': cmd_main,
     'calib_srb': cmd_calib_srb, 'categorize': cmd_categorize}[sys.argv[1]]()
