$action = New-ScheduledTaskAction -Execute 'C:\Users\ksbda\ToBeRich\run_live.bat' -WorkingDirectory 'C:\Users\ksbda\ToBeRich'
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -WakeToRun `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName "crypto-live-trading" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force

Start-ScheduledTask -TaskName "crypto-live-trading"

Start-Sleep -Seconds 5
Get-ScheduledTaskInfo -TaskName "crypto-live-trading"
Write-Output "---- 최근 로그 ----"
Get-Content "C:\Users\ksbda\ToBeRich\crypto\live_trading.log" -Tail 20 -ErrorAction SilentlyContinue
