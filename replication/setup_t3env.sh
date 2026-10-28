#!/bin/sh
# T3 실행 환경 재구성(세션 임시 폴더가 지워져도 다시 만들 수 있게). 저장소 루트의 .t3env/ (git 제외)에 만든다.
# 시스템 python3(3.9)에 numpy 2.0.2, pandas 2.3.3, torch 2.6.0, stable-baselines3 2.7.1, gym 0.26.2, scipy 1.13.1이
# 이미 있어야 한다(O1 실행과 같은 버전). 없는 것만 --no-deps로 .t3env/pylib에 넣는다.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); E=$ROOT/.t3env
mkdir -p "$E/logs"
grep -q '^.t3env' "$ROOT/.git/info/exclude" || echo '.t3env/' >> "$ROOT/.git/info/exclude"
if [ ! -f "$E/fm/meta/env_portfolio_allocation/env_portfolio_yahoofinance.py" ]; then
  mkdir -p "$E/fm"
  curl -sL https://codeload.github.com/AI4Finance-Foundation/FinRL-Meta/tar.gz/286fef6 | tar -xz -C "$E/fm" --strip-components=1 '*/meta' '*/agents'
  rm -rf "$E/fm/meta/env_future_trading"   # 쓰지 않는 400MB 데이터
fi
[ "$(md5 -q "$E/fm/meta/env_portfolio_allocation/env_portfolio_yahoofinance.py")" = 2db3df6d2395986a27585e8de7050027 ] || { echo 'env 파일 해시 불일치'; exit 1; }
[ -d "$E/pylib/absl" ] || python3 -m pip install -q --no-cache-dir --no-deps --target "$E/pylib" shimmy==2.0.0 stockstats==0.6.10 tensorboard==2.21.0 absl-py==2.3.1 grpcio==1.80.0 markdown==3.9 werkzeug==3.1.9 markupsafe==3.0.4 tensorboard-data-server==0.7.2
python3 -c "import numpy, pandas, torch, stable_baselines3, gym, scipy; print('numpy', numpy.__version__, 'pandas', pandas.__version__, 'torch', torch.__version__, 'sb3', stable_baselines3.__version__, 'gym', gym.__version__)" 2>/dev/null
