# 서버에 맥 SSH 공개키 등록 (2026-11-09, 서버 앞에서 1회)

**완료(2026-11-09): 등록됨, 맥에서 `ssh tb` 키 인증 확인.**

## 왜 하나
맥에서 `ssh tb`를 시도하면 서버까지는 연결되지만 `Permission denied (publickey,password,keyboard-interactive)`가 나온다. 비밀번호로 접속하면 PIN이 아니라 Microsoft 계정 비밀번호를 받고, 한/영 입력 상태도 문제를 일으킨다. 맥의 공개키를 서버에 직접 등록하면 비밀번호가 아예 필요 없다.

맥 쪽(`~/.ssh/id_ed25519`, `~/.ssh/config`의 `Host tb`)은 이미 준비되어 있다. 서버 쪽 등록만 남았다.

**자취방으로 떠나기 전에 꼭 끝낸다.** 이 등록은 서버 앞에서만 할 수 있다.

## 서버(Windows)에서 할 일
1. 시작 버튼 우클릭 → **터미널(관리자)** 또는 **Windows PowerShell(관리자)**를 연다.
2. 아래를 통째로 붙여넣고 Enter를 누른다.

```powershell
$k='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINvrwL7eUgZmdEYTlTTwzqBbUWtSdsDIiKKacMiXalIB macbookair-thesis'
$f='C:\ProgramData\ssh\administrators_authorized_keys'
if (-not (Test-Path $f) -or -not ((Get-Content $f) -contains $k)) { Add-Content -Path $f -Value $k -Encoding ascii }
icacls $f /inheritance:r /grant 'Administrators:F' /grant 'SYSTEM:F'
```

3. 마지막에 `Successfully processed 1 files`가 나오면 성공이다.

이 키는 맥의 **공개키**이므로 저장소에 있어도 괜찮다.

## 서버 쪽 Claude 세션에게
관리자 권한 세션이면 위 명령을 그대로 실행하고, 아래로 등록과 권한을 확인한다. 아니면 사용자에게 관리자 PowerShell에서 직접 실행하라고 안내한다. 봇 폴더(`C:\Users\ksbda\ToBeRich`)는 건드리지 않는다.

```powershell
Get-Content C:\ProgramData\ssh\administrators_authorized_keys
icacls C:\ProgramData\ssh\administrators_authorized_keys
Get-Service sshd
```
`sshd`가 Running이어야 한다.

## 끝난 뒤 (맥에서)
```bash
ssh -o BatchMode=yes tb "echo ok"   # ok가 나오면 성공
```
이어서 F7 상태를 확인한다(성과 파일은 열지 않는다).
```bash
ssh tb "wsl -e bash -lc 'cat ~/ToBeRich/data/funnel/rat_f7_gtx1650/*/done.json; tmux ls'"
```
