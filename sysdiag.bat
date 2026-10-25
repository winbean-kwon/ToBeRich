@echo off
set LOG=C:\Users\ksbda\ToBeRich\sysdiag.log
echo ==== whoami ==== > "%LOG%" 2>&1
whoami >> "%LOG%" 2>&1
echo ==== initial CD ==== >> "%LOG%" 2>&1
echo %CD% >> "%LOG%" 2>&1
cd /d C:\Users\ksbda\ToBeRich >> "%LOG%" 2>&1
echo ==== CD after cd /d ==== >> "%LOG%" 2>&1
echo %CD% >> "%LOG%" 2>&1
echo ==== dir venv\Scripts\python.exe ==== >> "%LOG%" 2>&1
dir venv\Scripts\python.exe >> "%LOG%" 2>&1
echo ==== call activate.bat ==== >> "%LOG%" 2>&1
call venv\Scripts\activate.bat >> "%LOG%" 2>&1
echo ==== PATH after activate ==== >> "%LOG%" 2>&1
echo %PATH% >> "%LOG%" 2>&1
echo ==== where python ==== >> "%LOG%" 2>&1
where python >> "%LOG%" 2>&1
echo ==== python --version ==== >> "%LOG%" 2>&1
python --version >> "%LOG%" 2>&1
echo ==== python -c print ==== >> "%LOG%" 2>&1
python -c "print(1+1)" >> "%LOG%" 2>&1
echo ==== python -m crypto.live_trading_loop_binance --help ==== >> "%LOG%" 2>&1
python -m crypto.live_trading_loop_binance --help >> "%LOG%" 2>&1
echo ==== DONE ==== >> "%LOG%" 2>&1
