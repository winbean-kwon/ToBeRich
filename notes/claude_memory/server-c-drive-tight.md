---
name: server-c-drive-tight
description: "서버 노트북 C: 여유가 거의 없음 — WSL vhdx·스왑·pagefile이 C:에 있어 WSL 작업이 봇 디스크를 위협"
metadata:
  node_type: memory
  type: project
  originSessionId: 5b46bd77-5b92-43e9-b37f-ae593511024b
  modified: 2026-11-22T09:11:46.115Z
---

서버(DESKTOP-U6SI9TA) C:는 254GB인데 2026-11-22에 여유가 22MB, 136MB까지 떨어졌다. WSL `ext4.vhdx`(약 23GB), WSL `swap.vhdx`(Temp, 최대 약 1GB), pagefile(시스템 관리, 메모리 압박 시 커짐)이 모두 C:에 있다. 디스크가 차면 WSL이 I/O 오류(Bus error)로 멈추고, 실계좌 봇도 같은 디스크를 쓴다.

**Why:** FRONTIER F7을 5개 동시에 돌릴 때 메모리·스왑·vhdx가 함께 커졌다. WSL 메모리는 3.8GB뿐이다.
**How to apply:** 서버 WSL에서 큰 작업을 시작하기 전에 C: 여유(`(Get-PSDrive C).Free`)와 WSL `free -m`을 확인하고, 동시 프로세스 수는 메모리로 정한다. 감시할 때는 C: 하한을 같이 건다. 이미 한 정리: 최대 절전 끔(hiberfil), WU·Edge 캐시, vhdx 압축, Downloads의 NVIDIA 설치 파일·Android NDK zip 삭제, LWS.exe 종료(자동 실행은 남아 있음). [[live-bot-setup]]
