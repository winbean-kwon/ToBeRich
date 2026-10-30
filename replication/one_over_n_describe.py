# 탐색적 기술 통계(판정 아님): 공식 구현 세 편의 저장된 목표 가중치가 1/N에서 얼마나 떨어져 있는가.
# 지표: active share = ½·Σ|w − 1/N| (일별 → 실행 평균), 최대 비중, 최소/최대 비중의 구조적 범위(코드 매개화에서 유도).
# 사용: python3 replication/one_over_n_describe.py <AlphaMix+ 묶음 폴더>
import sys, glob, json, pathlib, numpy as np, pandas as pd
R = pathlib.Path(__file__).resolve().parent
def act(W, n=None):
    n = n or W.shape[1]
    return float(np.mean(0.5 * np.abs(W - 1 / n).sum(1))), float(W.max())
out = {}
# 구조적 범위: softmax(x), x ∈ [lo, hi]인 N칸 → [1/(1+(N−1)e^(hi−lo)), e^(hi−lo)/(e^(hi−lo)+N−1)]
def bounds(N, span): e = np.exp(span); return [round(1 / (1 + (N - 1) * e) * 100, 2), round(e / (e + N - 1) * 100, 2)]
out['구조적 범위(%)'] = {'FinRL: Box(0,1)+softmax, 28칸': bounds(28, 1), 'AlphaMix+: tanh+softmax, 29칸(현금 포함)': bounds(29, 2),
                     'DeepAries: tanh 점수 상위 20 softmax(T=1), 20칸': bounds(20, 2)}
for alg in ('a2c', 'ppo', 'ddpg', 'td3'):
    for kind, pat in (('공식 예측', f'finrl_t3/o1/{alg}_W0_a_s*.csv'), ('결정적 예측', f'finrl_t3/o6/{alg}_W0_a_s*_det.csv')):
        fs = sorted(glob.glob(str(R / pat)))
        if not fs: continue
        v = [act(pd.read_csv(f).filter(like='w_').to_numpy()[1:]) for f in fs]
        out[f'FinRL {alg.upper()} {kind}'] = {'시드 수': len(v), 'active share 중앙값': round(float(np.median([x[0] for x in v])), 4),
                                         '범위': [round(min(x[0] for x in v), 4), round(max(x[0] for x in v), 4)],
                                         '최대 비중 최댓값': round(max(x[1] for x in v), 4)}
bund = pathlib.Path(sys.argv[1])
for st in ('S2021', 'S2020', 'S2019'):
    for e in (0, 9):
        v = []
        for f in sorted(glob.glob(str(bund / 'o1' / f'{st}_s*' / f'test_daily_action_{e}.npy'))):
            a = np.load(f)[:, 0, :]; W = np.exp(a) / np.exp(a).sum(1, keepdims=True); v.append(act(W))
        out[f'AlphaMix+ {st} e{e}'] = {'시드 수': len(v), 'active share 중앙값': round(float(np.median([x[0] for x in v])), 4),
                                      '범위': [round(min(x[0] for x in v), 4), round(max(x[0] for x in v), 4)],
                                      '최대 비중 최댓값': round(max(x[1] for x in v), 4)}
v26, v20 = [], []
for f in sorted(glob.glob(str(R / 'deeparies/runs/W0_a_s*.csv'))):
    W = pd.read_csv(f).filter(like='w_').to_numpy(); v26.append(act(W))
    S = np.sort(W, 1)[:, -20:]; v20.append(act(S, 20))
for k, v in (('DeepAries W0 (a) 대 1/26', v26), ('DeepAries W0 (a) 상위 20 안에서 대 1/20', v20)):
    out[k] = {'시드 수': len(v), 'active share 중앙값': round(float(np.median([x[0] for x in v])), 4),
              '범위': [round(min(x[0] for x in v), 4), round(max(x[0] for x in v), 4)], '최대 비중 최댓값': round(max(x[1] for x in v), 4)}
(R / 'one_over_n_describe.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out, ensure_ascii=False, indent=1))
