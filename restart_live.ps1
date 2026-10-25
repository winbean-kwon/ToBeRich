Stop-ScheduledTask -TaskName "crypto-live-trading" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Remove-Item "C:\Users\ksbda\ToBeRich\crypto\live_trading.log" -ErrorAction SilentlyContinue
Remove-Item "C:\Users\ksbda\ToBeRich\crypto\live_trading_supervisor.log" -ErrorAction SilentlyContinue

Start-ScheduledTask -TaskName "crypto-live-trading"

Write-Output "Started. Waiting 30s for model load + first cycle..."
Start-Sleep -Seconds 30

Write-Output "==== task info ===="
Get-ScheduledTaskInfo -TaskName "crypto-live-trading" | Format-List LastRunTime, LastTaskResult

Write-Output "==== running python processes ===="
Get-Process python -ErrorAction SilentlyContinue | Format-Table Id, StartTime

Write-Output "==== live_trading.log (tail 40) ===="
Get-Content "C:\Users\ksbda\ToBeRich\crypto\live_trading.log" -Tail 40 -ErrorAction SilentlyContinue

Write-Output "==== live_trading_supervisor.log (full) ===="
Get-Content "C:\Users\ksbda\ToBeRich\crypto\live_trading_supervisor.log" -ErrorAction SilentlyContinue
