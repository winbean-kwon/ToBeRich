@echo off
cd /d C:\Users\ksbda\ToBeRich
set PYTHONUTF8=1
:loop
call venv\Scripts\activate.bat
python -m crypto.live_trading_loop_binance --model-dir crypto\models --live >> crypto\live_trading.log 2>&1
echo [%date% %time%] process exited, restarting in 10s >> crypto\live_trading_supervisor.log
ping -n 11 127.0.0.1 >nul
goto loop
