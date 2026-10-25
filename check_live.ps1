Write-Output "==== running python processes ===="
Get-Process python -ErrorAction SilentlyContinue | Format-Table Id

Write-Output "==== live_trading.log (tail 40, utf8) ===="
Get-Content "C:\Users\ksbda\ToBeRich\crypto\live_trading.log" -Tail 40 -Encoding utf8 -ErrorAction SilentlyContinue

Write-Output "==== live_trading_supervisor.log (utf8) ===="
Get-Content "C:\Users\ksbda\ToBeRich\crypto\live_trading_supervisor.log" -Encoding utf8 -ErrorAction SilentlyContinue

Write-Output "==== now ===="
Get-Date
