#!/bin/bash
# T4 MARS 대기열을 맥 launchd에 등록한다. 로그인할 때 자동으로 이어서 돌고, 오류로 죽으면 5분 뒤 다시 뜬다.
#   bash replication/mars_t4_launchd.sh install     등록하고 시작
#   bash replication/mars_t4_launchd.sh uninstall   중지하고 등록 해제(결과는 그대로 남는다)
#   bash replication/mars_t4_launchd.sh status      등록 상태와 진행 상황(성과 없음)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
LABEL=com.seungbin.mars_t4
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
export MARS_WORK="$ROOT/.marswork" MARS_OUT="$ROOT/data/mars_t4"

case "${1:-}" in
install)
  mkdir -p "$MARS_OUT" "$HOME/Library/LaunchAgents"
  /usr/bin/python3 "$ROOT/replication/mars_t4.py" setup
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/caffeinate</string><string>-i</string>
    <string>/usr/bin/python3</string><string>$ROOT/replication/mars_t4.py</string><string>queue</string>
  </array>
  <key>EnvironmentVariables</key><dict>
    <key>MARS_WORK</key><string>$MARS_WORK</string>
    <key>MARS_OUT</key><string>$MARS_OUT</string>
    <key>MARS_THREADS</key><string>1</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>ThrottleInterval</key><integer>300</integer>
  <key>StandardOutPath</key><string>$MARS_OUT/launchd.log</string>
  <key>StandardErrorPath</key><string>$MARS_OUT/launchd.log</string>
</dict></plist>
EOF
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  echo "등록함: $PLIST"
  ;;
uninstall)
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  pkill -f "$ROOT/replication/mars_t4.py" || true
  echo "해제함. 결과는 $MARS_OUT 에 남아 있음"
  ;;
status)
  launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null | grep -E "state =|pid =|last exit" || echo "등록 안 됨"
  /usr/bin/python3 "$ROOT/replication/mars_t4.py" status
  ;;
*)
  sed -n 2,5p "$0"; exit 1 ;;
esac
