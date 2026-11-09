#!/bin/bash
# 맥에서 1회 실행: 서버(desktop-u6si9ta, Windows OpenSSH)에 키 인증을 설정한다.
# 서버 비밀번호(Windows 로그인 비밀번호)를 한 번 묻는다. 끝나면 `ssh tb ...`가 비밀번호 없이 된다.
# ksbda는 관리자 계정이라 키는 C:\ProgramData\ssh\administrators_authorized_keys에 들어간다
# (관리자 계정의 비밀번호 SSH 세션은 관리자 권한으로 실행됨).
set -e
HOST=desktop-u6si9ta; USERN=ksbda
KEY=~/.ssh/id_ed25519
[ -f "$KEY.pub" ] || ssh-keygen -t ed25519 -N "" -f "$KEY"
PUB=$(cat "$KEY.pub")

if ! grep -qE '^Host tb$' ~/.ssh/config 2>/dev/null; then
  mkdir -p ~/.ssh
  printf '\nHost tb\n  HostName %s\n  User %s\n  IdentityFile %s\n  ServerAliveInterval 30\n' "$HOST" "$USERN" "$KEY" >> ~/.ssh/config
  chmod 600 ~/.ssh/config
  echo "~/.ssh/config에 Host tb 추가"
fi

if ssh -o BatchMode=yes -o ConnectTimeout=10 tb "echo ok" >/dev/null 2>&1; then
  echo "이미 키 인증이 됩니다."
else
  PS="\$k='$PUB'; \$f='C:\\ProgramData\\ssh\\administrators_authorized_keys';
if (-not (Test-Path \$f) -or -not ((Get-Content \$f) -contains \$k)) { Add-Content -Path \$f -Value \$k -Encoding ascii };
icacls \$f /inheritance:r /grant 'Administrators:F' /grant 'SYSTEM:F' | Out-Null; Write-Output 'key added'"
  ENC=$(printf '%s' "$PS" | iconv -f UTF-8 -t UTF-16LE | base64 | tr -d '\n')
  echo "서버 비밀번호(Windows 로그인 비밀번호)를 입력하세요."
  ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password,keyboard-interactive tb "powershell -NoProfile -EncodedCommand $ENC"
fi

echo "--- 시험(비밀번호 없이 되어야 함) ---"
ssh -o BatchMode=yes tb "wsl -e bash -lc 'hostname; tmux ls; grep -h status ~/ToBeRich/data/funnel/rat_f7_gtx1650/*/done.json'"
