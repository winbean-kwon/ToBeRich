#!/bin/bash
# 서버 WSL에서 tmux 'statpow'로 실행: 보정 점검 → 본 계산(봉인). 사전 등록 notes/prereg_stat_power_v2.md.
#   tmux new -d -s statpow 'bash ~/ToBeRich/replication/stat_power/run_server.sh'
set -e
PY=~/f4work/statpow/bin/python
cd ~/ToBeRich/replication/stat_power
mkdir -p out
git -C ~/ToBeRich rev-parse HEAD > out/commit.txt
$PY run.py selftest > out/selftest.log 2>&1
[ -f out/calib.json ] || $PY run.py calib > out/calib.log 2>&1
[ -f out/main.json ] || $PY run.py main > out/main.log 2>&1
date > out/done_stage1.txt
