import json, sys
SHA = sys.argv[1]
OUT = 'crypto/notebooks/retrain1006/'
def code(s): return {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':s}
def md(s): return {'cell_type':'markdown','metadata':{},'source':s}

MOUNT = "from google.colab import drive\ndrive.mount('/content/drive')\n!pip install -q stable-baselines3[extra] gymnasium h5py pyarrow\n"

RUNNER = f'''# 실행기 — GitHub의 원본 노트북(커밋 {SHA[:7]} 고정)을 불러와 셀을 순서대로 실행한다.
# (1) 설정 셀 직후 모델·결과 경로를 새 폴더(rt1006)로 바꿔 기존 결과를 덮어쓰지 않는다.
# (2) 모든 .learn() 호출 결과를 캐시에 저장 — 끊겨도 `모두 실행`을 다시 누르면 학습된 부분은 건너뛴다.
import json, urllib.request
from pathlib import Path
COMMIT = '{SHA}'
RAW = f'https://raw.githubusercontent.com/winbean-kwon/ToBeRich/{{COMMIT}}/'
TAG = 'rt1006'
_ip = get_ipython()

def fetch_cells(path):
    nb = json.loads(urllib.request.urlopen(RAW + path).read().decode('utf-8'))
    return {{i: (c['source'] if isinstance(c['source'], str) else ''.join(c['source']))
            for i, c in enumerate(nb['cells']) if c['cell_type'] == 'code'}}

PATCH = r"""
MODEL_DIR = DRIVE_ROOT / 'models' / TAG
CRYPTO_DIR = DATA_DIR / 'crypto' / TAG
MODEL_DIR.mkdir(parents=True, exist_ok=True); CRYPTO_DIR.mkdir(parents=True, exist_ok=True)
POOL_DIR = MODEL_DIR / 'crypto_hrl_pool'
ORIG_PPO_PATH = MODEL_DIR / 'crypto_ppo_portfolio.zip'
for _n in ('EIIE_MODEL_DIR', 'LSRE_CAAN_MODEL_DIR'):
    if _n in globals():
        globals()[_n] = MODEL_DIR / Path(globals()[_n]).name
        globals()[_n].mkdir(parents=True, exist_ok=True)
CACHE = MODEL_DIR / '_learn_cache'; CACHE.mkdir(exist_ok=True)
import stable_baselines3 as _sb3
_BASE_PPO, _BASE_DQN = _sb3.PPO, _sb3.DQN
def _cached(base):
    class _C(base):
        def learn(self, total_timesteps, *a, **k):
            _CTR[0] += 1
            p = CACHE / f'{{_NB[0]}}_c{{_CUR[0]}}_{{_CTR[0]}}_{{base.__name__}}.zip'
            if p.exists():
                self.set_parameters(str(p), exact_match=True, device=self.device)
                self.num_timesteps += total_timesteps
                print(f'[캐시] {{p.name}} 로드 — 학습 생략')
                return self
            out = super().learn(total_timesteps, *a, **k)
            self.save(str(p))
            return out
    _C.__name__ = _C.__qualname__ = base.__name__
    return _C
PPO, DQN = _cached(_BASE_PPO), _cached(_BASE_DQN)
print(f'[경로] 모델 → {{MODEL_DIR}} | 결과 CSV → {{CRYPTO_DIR}}')
"""

_NB, _CUR, _CTR = [''], [0], [0]

def run_cells(path, ids, patch_after, extra=None, subs=None):
    """extra: 경로 변경 직후 실행할 코드(예: β 변경). subs: {{셀번호: [(원문, 대체), ...]}} 문자열 치환."""
    cells = fetch_cells(path)
    _NB[0] = Path(path).stem
    for i in ids:
        _CUR[0], _CTR[0] = i, 0
        src = cells[i]
        for old, new in (subs or {{}}).get(i, []):
            assert old in src, f'셀 {{i}}에 치환 대상 없음: {{old!r}}'
            src = src.replace(old, new)
        print(f'\\n########## {{Path(path).name}} 셀 {{i}} ##########')
        r = _ip.run_cell(src)
        if not r.success:
            raise RuntimeError(f'{{path}} 셀 {{i}}에서 오류 — 위 오류 메시지를 확인하세요')
        if i == patch_after:
            for code in (PATCH, extra):
                if code and not _ip.run_cell(code).success:
                    raise RuntimeError('경로/설정 변경 실패')
print('실행기 준비 완료')
'''

MAIN = 'crypto/notebooks/crypto_hrl_earnhft_colab.ipynb'
V1 = [2, 4, 6, 8, 9, 11, 12, 14, 15, 17, 18, 19, 21, 23, 25]
V4 = [44, 46, 48, 50, 51, 52, 54, 56, 58, 60, 63, 64, 66, 72, 74, 76, 77, 80, 83, 87]
V2 = [27, 28, 29, 30, 31, 33]
V3 = [35, 36, 37, 38, 39, 40, 41]

cas = [md(f'''# [재학습 · 2026-10-06] 크립토 계층형 연쇄 전체 재학습 (v1 → v4 → v2 → v3)

회계 수정 후 환경에서 원본 노트북 `crypto_hrl_earnhft_colab.ipynb`의 학습·평가 셀을 **그대로** 다시 실행한다(GitHub 커밋 `{SHA[:7]}`의 코드).

- **`런타임 > 모두 실행`만 누르면 된다.** 중간에 끊기면 다시 `모두 실행` — 이미 학습된 모델은 캐시에서 불러와 건너뛴다.
- 모델은 `models/rt1006/`, 결과 CSV는 `data/crypto/rt1006/`에 저장된다. 기존 모델·결과는 건드리지 않는다.
- 순서: v1(풀+라우터) → **v4(배포 계열, 가장 중요)** → v2 → v3. PPO 약 16개 + 라우터 5개, 총 수 시간.
- v4 블록이 끝나면(§16 4개 β 단독 비교 출력) 그 결과만으로도 배포 β 선택을 확인할 수 있다.
'''), code(MOUNT), code(RUNNER),
 code(f"# v1: 직접 이식 풀 + 라우터 + 스무딩 스윕 (원본 §1~§9)\nrun_cells('{MAIN}', {V1}, patch_after=2)\n"),
 code(f"# v4: top-K+게이트 풀, 라우터, 매칭 라우터, valid 기반 α, 4개 β 단독 비교, IC (원본 §13~§17-A)\nrun_cells('{MAIN}', {V4}, patch_after=None)\n"),
 code(f"# v2: 스무딩 내장 재학습 (원본 §10~§11)\nrun_cells('{MAIN}', {V2}, patch_after=None)\n"),
 code(f"# v3: 현금 행동 + 검증 기반 선별 (원본 §12)\nrun_cells('{MAIN}', {V3}, patch_after=None)\nprint('\\n전부 완료')\n")]

bas = [md(f'''# [재학습 · 2026-10-06] 단일 PPO · EIIE · LSRE-CAAN 재학습

회계 수정 후 환경에서 세 원본 노트북의 셀을 **그대로** 다시 실행한다(GitHub 커밋 `{SHA[:7]}`의 코드). 크립토 연쇄 재학습 노트북과 **동시에 다른 Colab 세션에서** 돌려도 된다.

- **`런타임 > 모두 실행`만 누르면 된다.** 끊기면 다시 `모두 실행` — 학습된 모델은 캐시에서 불러온다.
- 모델은 `models/rt1006/`, 결과 CSV는 `data/crypto/rt1006/`에 저장된다.
- 단일 PPO는 30만 스텝이라 가장 오래 걸린다(약 45분).
'''), code(MOUNT), code(RUNNER),
 code("# 단일 정책 PPO (표 1의 행 1)\nrun_cells('crypto/notebooks/crypto_rl_trading_colab.ipynb', [2, 4, 6, 8, 9, 11, 13, 15, 16], patch_after=2)\n"),
 code("# EIIE (6.6절)\nrun_cells('crypto/notebooks/crypto_eiie_baseline_colab.ipynb', [3, 5, 7, 9, 11, 13, 15, 17, 18, 20], patch_after=3)\n"),
 code("# LSRE-CAAN (6.6절)\nrun_cells('crypto/notebooks/crypto_lsre_caan_baseline_colab.ipynb', [3, 5, 7, 9, 11, 13, 15, 17, 18, 20], patch_after=3)\nprint('\\n전부 완료')\n")]


V1_STATE = [2, 4, 6, 8, 9, 11, 12, 14, 15, 17, 18, 19, 21, 25]
rem = [md(f"""# [재학습 · 2026-10-06] 남은 부분: v2 · v3 (이어 실행)

`crypto_cascade_retrain_rt1006`이 Colab 12시간 제한으로 v2 시작 직후 끊겨서 남은 v2·v3만 돌리는 노트북이다.
v1은 v2·v3가 쓰는 변수를 다시 만들기 위해 실행하지만, 학습은 저장된 모델을 불러와 건너뛴다(평가만 30~40분). v4는 이미 끝나서 실행하지 않는다.

- **`런타임 > 모두 실행`만 누르면 된다.** 끊기면 다시 `모두 실행`.
- 드라이브 연결 창에서 **ksbdaniel7@gmail.com** 계정을 고른다.
"""), code(MOUNT), code(RUNNER),
 code(f"# v1 상태 복원 (학습은 캐시에서 로드)\nrun_cells('{MAIN}', {V1_STATE}, patch_after=2)\n"),
 code(f"# v2: 스무딩 내장 재학습 (원본 §10~§11)\nrun_cells('{MAIN}', {V2}, patch_after=None)\n"),
 code(f"# v3: 현금 행동 + 검증 기반 선별 (원본 §12)\nrun_cells('{MAIN}', {V3}, patch_after=None)\nprint('\\n전부 완료')\n")]

ROB = 'crypto/notebooks/crypto_beta_robustness_colab.ipynb'
CLEAN = 'crypto/notebooks/crypto_clean_valid_colab.ipynb'
ROB_IDS = [3, 5, 6, 8, 10, 12, 13, 15, 17, 19, 20, 22, 24, 26, 29, 30, 31, 32, 35, 36, 39, 40, 41, 43, 45]
CLEAN_IDS = [3, 5, 6, 8, 10, 12, 13, 15, 17, 19, 20, 22, 24]
ROB_EXTRA = """BETA = 30   # 재학습 후 검증 샤프 최고 β
POOL_DIR_ROBUST = MODEL_DIR / 'crypto_beta_robustness'
DEPLOYED_AGENT_PATH = MODEL_DIR / 'crypto_hrl_pool_v4' / f'agent_beta_{BETA}.zip'
assert DEPLOYED_AGENT_PATH.exists(), f'재학습한 v4 β={BETA} 모델 없음: {DEPLOYED_AGENT_PATH}'
print(f'[β 변경] BETA={BETA} | 기준 모델: {DEPLOYED_AGENT_PATH}')
"""
CLEAN_EXTRA = """BETA = 30
DEPLOYED_AGENT_PATH = MODEL_DIR / 'crypto_hrl_pool_v4' / f'agent_beta_{BETA}.zip'
CLEAN_MODEL_DIR = MODEL_DIR / 'crypto_clean_valid'
assert DEPLOYED_AGENT_PATH.exists(), f'재학습한 v4 β={BETA} 모델 없음: {DEPLOYED_AGENT_PATH}'
print(f'[β 변경] BETA={BETA} | 기준 모델: {DEPLOYED_AGENT_PATH}')
"""
TOPK_SETUP = [2, 4, 6, 8, 9, 11, 12, 44, 46, 52, 72]
TOPK_EXTRA = """# §17-C가 쓰는 smooth_perf_row(원본 §9 셀 25에 정의)를 그 셀에서 함수 부분만 가져와 정의
_s25 = fetch_cells(MAIN_PATH)[25]
exec(_s25[_s25.index('def smooth_perf_row'):_s25.index('smooth_results, smooth_curves = {}')], globals())
print('smooth_perf_row 정의 완료')
"""
TOPK_SUBS = {90: [('pool_models_v4[-30]', 'pool_models_v4[30]'), ('beta=-30,', 'beta=30,'),
                  ("f'agent_beta_-30_k{k}.zip'", "f'agent_beta_30_k{k}.zip'")],
             91: [('ALPHA_DIAG = BEST_ALPHA_V4_MATCHED', 'ALPHA_DIAG = 0.01  # 재학습 결과 valid·test 모두 α=0.01 선택')]}
rob = [md(f"""# [재학습 · 2026-10-06] β=30 강건성 검증 (B 묶음)

재학습 후 검증 샤프가 가장 높은 β=30을 새 배포 후보로 두고, 원본 노트북 셋을 β만 바꿔 그대로 다시 실행한다(GitHub 커밋 `{SHA[:7]}`의 코드).
1. 추가 시드 15개 + 앙상블 + DSR (`crypto_beta_robustness_colab`)
2. 클린 재학습: 1~9월만 학습, 10~12월에서 α 선택 (`crypto_clean_valid_colab`)
3. top-K 스윕 K∈{{5,7,15}} + IC (`crypto_hrl_earnhft_colab` §17-C)

- **`crypto_cascade_retrain_rt1006`의 v4 블록이 끝난 뒤에 실행해야 한다**(재학습한 β=30 모델 필요 — 이미 끝남).
- **`런타임 > 모두 실행`만 누르면 된다.** 끊기면 다시 `모두 실행`. PPO 19개, 약 5~6시간.
- 드라이브 연결 창에서 **ksbdaniel7@gmail.com** 계정을 고른다.
- 결과 CSV는 원본과 같은 이름으로 `data/crypto/rt1006/`에 저장된다(라벨의 'β=-30' 문구는 원본 그대로라 β=30으로 읽으면 된다).
"""), code(MOUNT), code(RUNNER),
 code(f"# 1. 추가 시드 15개 + 앙상블 + DSR (β=30)\nrun_cells('{ROB}', {ROB_IDS}, patch_after=3, extra={ROB_EXTRA!r})\n"),
 code(f"# 2. 클린 재학습 (β=30, seed=42, 2025년 1~9월만 학습)\nrun_cells('{CLEAN}', {CLEAN_IDS}, patch_after=3, extra={CLEAN_EXTRA!r})\n"),
 code(f"# 3. top-K 스윕 (β=30)\nMAIN_PATH = '{MAIN}'\nrun_cells(MAIN_PATH, {TOPK_SETUP}, patch_after=2, extra={TOPK_EXTRA!r})\nrun_cells(MAIN_PATH, [90, 91], patch_after=None, subs={TOPK_SUBS!r})\nprint('\\n전부 완료')\n")]
meta={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'},'colab':{'provenance':[]}}
for name, cells in [('crypto_cascade_retrain_rt1006.ipynb', cas), ('crypto_baselines_retrain_rt1006.ipynb', bas), ('crypto_v2v3_resume_rt1006.ipynb', rem), ('crypto_beta30_robustness_rt1006.ipynb', rob)]:
    json.dump({'cells':cells,'metadata':meta,'nbformat':4,'nbformat_minor':5}, open(OUT+name,'w'), ensure_ascii=False, indent=1)
print('built')
