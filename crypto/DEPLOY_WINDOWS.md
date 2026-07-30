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
git clone https://github.com/winbean-kwon/ToBeRich.git
cd ToBeRich
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r crypto\requirements.txt
```

(`--extra-index-url ...cpu`는 CPU 전용 torch를 설치해 용량과 설치 시간을 줄인다 — 이 봇은 GPU가
필요 없다.)

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
돌면 정상이다. `Ctrl+C`로 종료.

## 5. 상시 구동 설정 (재부팅/로그아웃에도 계속 돌게)

### 5.1 재시작 루프 배치파일

크래시 시 자동 재시작되도록 감싸는 배치파일을 만든다. `C:\ToBeRich\run_live.bat`:

```bat
@echo off
cd /d C:\ToBeRich
:loop
call venv\Scripts\activate.bat
python -m crypto.live_trading_loop_binance --model-dir crypto\models --live
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

저장 후 컴퓨터를 재부팅해서 실제로 잘 뜨는지 확인. 로그는 `crypto\live_trading.log`와
`crypto\live_trading_supervisor.log`에서 확인.

## 6. 확인 체크리스트

- [ ] `.env`가 새 컴퓨터에만 있고 git에는 안 올라갔는지 (`git status`에 안 보여야 정상)
- [ ] dry-run 한 번 통과했는지
- [ ] Task Scheduler 트리거로 재부팅 후에도 자동 시작되는지
- [ ] **기존 컴퓨터의 프로세스는 반드시 종료했는지** — 두 컴퓨터에서 동시에 돌리면 같은 실계좌에
      중복 리밸런싱/중복 주문이 나간다. 새 컴퓨터에서 정상 확인된 뒤에만 기존 쪽을 끌 것.
