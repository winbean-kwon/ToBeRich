Stop-ScheduledTask -TaskName "crypto-live-trading" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Remove-Item "C:\Users\ksbda\ToBeRich\crypto\live_trading.log" -ErrorAction SilentlyContinue
Remove-Item "C:\Users\ksbda\ToBeRich\crypto\live_trading_supervisor.log" -ErrorAction SilentlyContinue

Start-ScheduledTask -TaskName "crypto-live-trading"

Write-Output "Restarted with clock-resync fix. Waiting 30s..."
Start-Sleep -Seconds 30

Get-Process python -ErrorAction SilentlyContinue | Format-Table Id
Write-Output "==== live_trading.log (tail 30, utf8) ===="
Get-Content "C:\Users\ksbda\ToBeRich\crypto\live_trading.log" -Tail 30 -Encoding utf8 -ErrorAction SilentlyContinue
