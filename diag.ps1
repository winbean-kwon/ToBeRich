Write-Output "==== task info ===="
Get-ScheduledTaskInfo -TaskName "crypto-live-trading" | Format-List *
Write-Output "==== task action/settings ===="
(Get-ScheduledTask -TaskName "crypto-live-trading").Actions | Format-List *
(Get-ScheduledTask -TaskName "crypto-live-trading").Principal | Format-List *
Write-Output "==== stopping task ===="
Stop-ScheduledTask -TaskName "crypto-live-trading"
Start-Sleep -Seconds 2
Get-Process python -ErrorAction SilentlyContinue | Format-Table Id, StartTime
Write-Output "==== live_trading.log (full) ===="
Get-Content "C:\Users\ksbda\ToBeRich\crypto\live_trading.log" -ErrorAction SilentlyContinue
Write-Output "==== live_trading_supervisor.log (full) ===="
Get-Content "C:\Users\ksbda\ToBeRich\crypto\live_trading_supervisor.log" -ErrorAction SilentlyContinue
