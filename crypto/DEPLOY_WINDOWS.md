# Windows에서 24/7 실거래 봇 돌리기

크립토 HRL 실거래 루프(`live_trading_loop_binance.py`)를 상시 켜져 있는 Windows PC에서
재부팅/로그아웃과 무관하게 계속 돌리기 위한 셋업 가이드.

**주의**: 이 저장소는 API 키(`crypto/.env`)를 포함하지 않는다 — git에 절대 올리지 않는 파일이라
별도로(USB, AirDrop, 클라우드 저장소 등 원하는 방법으로) 안전하게 옮겨야 한다.

## 1. 준비물 설치

1. **Python 3.10 이상** 설치 — [python.org](https://www.python.org/downloads/windows/) 에서
   설치 시 반드시 **"Add python.exe to PATH"** 체크
2. **Git for Windows** 설치 — [git-scm.com](https://git-scm.com/download/win)

## 2. 저장소 클론 + 가상환경

PowerShell에서:

```powershell
cd C:\
git clone -b audit-fix-1004 https://github.com/winbean-kwon/ToBeRich.git
cd ToBeRich
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r crypto\requirements.txt
```

(`--extra-index-url ...cpu`는 CPU 전용 torch를 설치해 용량과 설치 시간을 줄인다 — 이 봇은 GPU가
필요 없다.)

⚠️ 실계좌 정책(β=30 재학습)은 아직 `main`에 병합되지 않았으므로 반드시 `-b audit-fix-1004`로
클론한다. `main`을 받으면 예전 β=-30 정책 코드가 돈다. 이미 클론해 둔 경우:
`git fetch origin; git checkout audit-fix-1004; git pull`.

## 2.5 재학습 모델 파일 받기 (git에 없음)

라이브 정책은 `crypto\models\rt1006\crypto_hrl_pool_v4\agent_beta_30.zip`(약 38.5MB)을 불러온다.
이 파일은 git에 올라가 있지 않으므로 Google Drive에서 직접 받아 둔다.

1. Drive `models/rt1006/crypto_hrl_pool_v4/agent_beta_30.zip` 다운로드
   (같은 이름의 파일이 `asset_scaling/N1~N20`, `crypto_hrl_pool_v4_topk_sweep`에도 있으니 헷갈리지 말 것 —
   폴더가 `rt1006/crypto_hrl_pool_v4`인 것, 크기 38,538,412바이트인 것이 맞다)
2. 압축을 **풀지 말고** zip 그대로 아래 경로에 둔다:

```powershell
mkdir crypto\models\rt1006\crypto_hrl_pool_v4 -Force
move $HOME\Downloads\agent_beta_30.zip crypto\models\rt1006\crypto_hrl_pool_v4\
```

백본 `crypto\models\crypto_hybrid_best.pt`는 git에 포함돼 있어 따로 받을 필요 없다. 첫 실행 때
Chronos 사전학습 가중치를 HuggingFace에서 내려받으므로 인터넷 연결이 필요하다.

## 3. `.env` 파일 배치

기존 컴퓨터의 `crypto\.env` 파일을 그대로 복사해서 새 컴퓨터의 `C:\ToBeRich\crypto\.env`
경로에 두기만 하면 된다(git과 무관하게 별도 전달). 내용은 다음 3개 변수:

```
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
BINANCE_LIVE_MODE=real
```

⚠️ 이 API 키에 바이낸스 쪽 "IP access restriction"이 걸려 있다면, 새 컴퓨터의 공인 IP를
바이낸스 API Management에서 반드시 추가/갱신해야 한다 — 안 그러면 `-2015 Invalid API-key,
IP, or permissions` 에러가 난다.

## 4. 동작 확인 (dry-run)

`--live` 없이 먼저 실행해서 초기화·모델 로드·바이낸스 조회까지 정상인지 확인:

```powershell
cd C:\ToBeRich
.\venv\Scripts\Activate.ps1
python -m crypto.live_trading_loop_binance --model-dir crypto\models
```

로그에 `[v4] 초기화 완료`, `실거래 루프 시작 | ... dry_run=True`가 뜨고 에러 없이 한 사이클이
돌면 정상이다. `Ctrl+C`로 종료. `재학습 모델 없음: ...` 에러가 나면 2.5절의 모델 경로를 확인한다.

시작 로그에서 다음 세 줄을 반드시 확인한다:
- `코드 버전 | 브랜치 audit-fix-1004 | 커밋 ...` — `main`이면 예전 β=-30 정책이 돈다(2026-10-25 실제로 서버가
  `main`에서 돌고 있었음). 브랜치를 바꾸거나 `audit-fix-1004`를 `main`에 병합한 뒤 다시 켠다.
- `[v4] 모델 파일 ...rt1006...agent_beta_30.zip | 38,538,412바이트` — 크기가 다르면 시작 단계에서 오류로 멈춘다.
- `⚠️ API 키 점검: ...` 경고가 없어야 한다(출금 권한 꺼짐, IP 제한 켜짐, 선물/마진 꺼짐).

처음 실계좌로 켤 때는 `--max-capital 500`처럼 운용 금액 상한을 걸어 소액으로 며칠 지켜보는 것을
권장한다(계좌 잔고가 더 커도 그 금액까지만 운용).

⚠️ 상한을 너무 작게 잡으면 주문이 거의 나가지 않는다. 바이낸스는 대부분 심볼에서 **주문당 최소 5 USDT**를
요구하는데, 이 정책은 위험자산 노출이 10~20%이고 그것을 10종목에 나눈다 — 종목당 비중이 운용금의 1~2%다.
`--max-capital 100`이면 종목당 1~2 USDT라 루프가 전부 최소금액 미달로 거른다. 종목당 5 USDT를 넘기려면
최소 250~500 USDT는 필요하다. 거래정지 종목(2026-10 기준 TON·UTK·VANRY)은 루프가 자동으로 주문에서 뺀다.

## 5. 상시 구동 설정 (재부팅/로그아웃에도 계속 돌게)

### 5.1 재시작 루프 배치파일

크래시 시 자동 재시작되도록 감싸는 배치파일을 만든다. `C:\ToBeRich\run_live.bat`:

```bat
@echo off
cd /d C:\ToBeRich
:loop
call venv\Scripts\activate.bat
python -m crypto.live_trading_loop_binance --model-dir crypto\models --live >> crypto\live_trading.log 2>&1
echo [%date% %time%] 프로세스 종료됨 — 10초 후 재시작 >> crypto\live_trading_supervisor.log
timeout /t 10 /nobreak
goto loop
```

### 5.2 작업 스케줄러(Task Scheduler)에 등록

1. **작업 스케줄러** 실행 → **작업 만들기**(마법사 말고 "Create Task")
2. **일반** 탭: 이름 지정(예: `crypto-live-trading`), **"사용자가 로그온했는지 여부에 관계없이
   실행"** 선택, **"가장 높은 권한으로 실행"** 체크
3. **트리거** 탭 → 새로 만들기 → **"컴퓨터 시작 시"** 선택
4. **동작** 탭 → 새로 만들기 → 프로그램: `C:\ToBeRich\run_live.bat`
5. **조건** 탭 → "컴퓨터가 AC 전원에 연결된 경우에만" 체크 해제(데스크탑이면 상관없지만 노트북이면
   꺼두지 않으면 배터리 모드에서 안 돌 수 있음), **"작업을 시작하기 위해 절전 모드 종료"** 체크
6. **설정** 탭 → **"요청 시 작업 실행 허용"** 체크, **"작업이 이미 실행 중이면 다음 새 인스턴스 시작
   안 함"**으로 설정(중복 실행 방지 — 중요: 두 프로세스가 동시에 돌면 같은 계좌에 중복 주문이 나감)

`--live`로 켜면 `crypto\live_trading.lock` 파일 잠금을 잡는다 — 같은 컴퓨터에서 두 번째 프로세스는
"이미 다른 실거래 프로세스가 실행 중" 메시지와 함께 바로 종료된다(다른 컴퓨터끼리는 못 막는다).
서킷브레이커의 당일 기준 잔고는 `crypto\live_state.json`에 저장되므로 같은 날 재시작해도 손실 한도가 유지된다.

저장 후 컴퓨터를 재부팅해서 실제로 잘 뜨는지 확인. 로그는 `crypto\live_trading.log`와
`crypto\live_trading_supervisor.log`에서 확인.

(루프 코드는 로그를 화면에만 찍으므로, 위처럼 `>> crypto\live_trading.log 2>&1`로 파일에
남겨야 작업 스케줄러로 백그라운드 실행할 때 기록을 볼 수 있다. 실시간으로 보려면
`Get-Content crypto\live_trading.log -Wait -Tail 50`.)

### 5.3 코드 업데이트할 때

```powershell
cd C:\ToBeRich
schtasks /End /TN crypto-live-trading
git pull
schtasks /Run /TN crypto-live-trading
```

## 6. 확인 체크리스트

- [ ] `.env`가 새 컴퓨터에만 있고 git에는 안 올라갔는지 (`git status`에 안 보여야 정상)
- [ ] `audit-fix-1004` 브랜치로 클론했는지 (`git branch`로 확인)
- [ ] `crypto\models\rt1006\crypto_hrl_pool_v4\agent_beta_30.zip`이 있는지
- [ ] dry-run 한 번 통과했는지
- [ ] Task Scheduler 트리거로 재부팅 후에도 자동 시작되는지
- [ ] **기존 컴퓨터의 프로세스는 반드시 종료했는지** — 두 컴퓨터에서 동시에 돌리면 같은 실계좌에
      중복 리밸런싱/중복 주문이 나간다. 새 컴퓨터에서 정상 확인된 뒤에만 기존 쪽을 끌 것.

## 부록: 서버가 Linux(Ubuntu 등)인 경우

```bash
git clone -b audit-fix-1004 https://github.com/winbean-kwon/ToBeRich.git ~/ToBeRich
cd ~/ToBeRich
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip
pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r crypto/requirements.txt
mkdir -p crypto/models/rt1006/crypto_hrl_pool_v4   # 여기에 agent_beta_30.zip 복사 (2.5절)
# crypto/.env 복사 (3절)
python -m crypto.live_trading_loop_binance --model-dir crypto/models   # dry-run 확인
```

상시 구동은 systemd 서비스로 등록한다. `/etc/systemd/system/crypto-live.service`
(`<user>`는 서버 계정명으로 바꿀 것):

```ini
[Unit]
Description=crypto live trading
After=network-online.target
Wants=network-online.target

[Service]
User=<user>
WorkingDirectory=/home/<user>/ToBeRich
ExecStart=/home/<user>/ToBeRich/venv/bin/python -m crypto.live_trading_loop_binance --model-dir crypto/models --live
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now crypto-live     # 시작 + 부팅 시 자동 시작
journalctl -u crypto-live -f                # 로그 실시간 확인
sudo systemctl restart crypto-live          # git pull 후 재시작
```

systemd는 한 서비스를 한 프로세스로만 띄우므로 중복 실행 걱정은 없다(다른 컴퓨터에서 도는 것은 별개 —
6절 마지막 항목 참고).
