# 크립토 실거래 루프(crypto/live_trading_loop_binance.py) 배포용.
# Railway에서 이 저장소를 연결하면 기본적으로 이 Dockerfile을 사용해 빌드한다.
# HTTP 포트를 열지 않는 백그라운드 워커이므로 Railway 서비스 타입은 "Worker"로 설정할 것.

FROM python:3.11-slim

WORKDIR /app

# torch는 CPU 전용 wheel로 설치 — CUDA 빌드를 받으면 이미지가 수 GB로 불어난다.
COPY crypto/requirements.txt crypto/requirements.txt
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r crypto/requirements.txt

COPY crypto/ crypto/

# 실거래 실행(--live). 대시보드에서 BINANCE_API_KEY / BINANCE_API_SECRET / BINANCE_LIVE_MODE=real
# 환경변수를 반드시 설정할 것 — 없으면 코드 상 기본값(테스트넷/dry-run 쪽)으로 동작한다.
CMD ["python", "-m", "crypto.live_trading_loop_binance", "--model-dir", "crypto/models", "--live"]
