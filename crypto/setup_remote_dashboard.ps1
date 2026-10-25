# 실거래 봇 대시보드(localhost:8787)를 Tailscale로 내 기기(휴대폰·노트북)에만 공유한다.
#
# 서버 컴퓨터의 PowerShell(관리자 권한)에서 한 번만 실행:
#   cd C:\ToBeRich
#   powershell -ExecutionPolicy Bypass -File crypto\setup_remote_dashboard.ps1
#
# 하는 일: Tailscale 설치(없으면) → 로그인(브라우저가 열림) → 8787 포트를 tailnet에 HTTPS로 공유
# → 접속 주소 출력. 공유 설정은 재부팅해도 유지된다. 인터넷에 공개되지 않고, 같은 Tailscale 계정에
# 로그인한 기기에서만 열린다.

$ErrorActionPreference = "Stop"
$Port = 8787

function Find-Tailscale {
    $cmd = Get-Command tailscale -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $default = Join-Path $env:ProgramFiles "Tailscale\tailscale.exe"
    if (Test-Path $default) { return $default }
    return $null
}

# 1. 설치
$ts = Find-Tailscale
if (-not $ts) {
    Write-Host "[1/4] Tailscale 설치 중 (winget)..."
    winget install --id tailscale.tailscale -e --accept-source-agreements --accept-package-agreements
    $ts = Find-Tailscale
    if (-not $ts) {
        Write-Host "설치 후에도 tailscale.exe를 찾지 못했습니다. https://tailscale.com/download 에서 직접 설치한 뒤 다시 실행하세요."
        exit 1
    }
} else {
    Write-Host "[1/4] Tailscale 이미 설치됨: $ts"
}

# 2. 로그인 (이미 로그인돼 있으면 그대로 통과)
Write-Host "[2/4] Tailscale 로그인 — 브라우저가 열리면 휴대폰과 같은 계정으로 로그인하세요."
& $ts up --unattended   # --unattended: 윈도우 사용자가 로그아웃해도 서버 연결 유지
if ($LASTEXITCODE -ne 0) { Write-Host "로그인 실패 — 위 메시지를 확인하세요."; exit 1 }

# 3. 대시보드 공유 (HTTPS, tailnet 내부 전용)
Write-Host "[3/4] 대시보드(localhost:$Port)를 tailnet에 공유..."
& $ts serve --bg $Port
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "공유 설정 실패. 처음 쓰는 계정이면 위에 출력된 링크에서 'HTTPS / Serve 사용'을 허용한 뒤"
    Write-Host "이 스크립트를 다시 실행하세요."
    exit 1
}

# 4. 접속 주소 출력
$dns = ((& $ts status --json) | ConvertFrom-Json).Self.DNSName.TrimEnd(".")
Write-Host ""
Write-Host "[4/4] 완료. 휴대폰/노트북에 Tailscale 앱을 설치하고 같은 계정으로 로그인한 뒤 아래 주소를 여세요:"
Write-Host ""
Write-Host "    https://$dns/"
Write-Host ""
Write-Host "봇이 꺼져 있으면 '봇 응답 없음' 또는 연결 오류가 보입니다(정상). 공유 해제: tailscale serve reset"
