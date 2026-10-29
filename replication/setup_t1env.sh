#!/bin/sh
# T1 DeepAries 실행 환경 재구성. 저장소 루트의 .t1env/ (git 제외)에 공식 코드 @634f559의 필요한 파일만 받는다
# (데이터 2개 포함 약 80MB, 공개 체크포인트·이미지는 받지 않음). 시스템 python3(3.9)의 numpy 2.0.2, pandas 2.3.3,
# torch 2.6.0, scipy 1.13.1, matplotlib 3.9.4, yfinance 0.2.66을 쓰고 einops만 .t1env/pylib에 넣는다.
# timm은 layers/Transformer_Module.py만 import하고 그 파일은 어디서도 import되지 않아 설치하지 않는다.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); E=$ROOT/.t1env; R=$E/DeepAries
C=634f559cf4603eeb2ba7509e31319d076b21c16c
mkdir -p "$E/logs"
grep -q '^/.t1env' "$ROOT/.git/info/exclude" || echo '/.t1env/' >> "$ROOT/.git/info/exclude"
for f in complete_dj30_tickers.csv data/dj30/dj30_general_data.csv data/dj30/dj30_data.csv \
  data_provider/data_factory.py data_provider/data_loader.py data_provider/data_prep.py exp/exp_DeepAries.py exp/exp_basic.py \
  layers/Embed.py layers/SelfAttention_Family.py layers/Transformer_EncDec.py layers/Transformer_Module.py main.py \
  models/Transformer.py models/iTransformer.py models/ppo.py utils/masking.py utils/preprocessor.py utils/timefeatures.py utils/tools.py; do
  [ -f "$R/$f" ] && continue
  mkdir -p "$R/$(dirname "$f")"; curl -sfL "https://raw.githubusercontent.com/dmis-lab/DeepAries/$C/$f" -o "$R/$f.tmp" && mv "$R/$f.tmp" "$R/$f"
done
[ "$(md5 -q "$R/data/dj30/dj30_general_data.csv")" = 1c3432510aa93980f6534d6906315041 ] || { echo '데이터 해시 불일치'; exit 1; }
[ -d "$E/pylib/einops" ] || python3 -m pip install -q --no-cache-dir --no-deps --target "$E/pylib" einops==0.8.1
python3 -c "import numpy, pandas, torch, scipy, matplotlib, yfinance; print('numpy', numpy.__version__, 'pandas', pandas.__version__, 'torch', torch.__version__, 'scipy', scipy.__version__)"
