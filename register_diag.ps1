Unregister-ScheduledTask -TaskName "crypto-live-trading-diag" -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute 'C:\Users\ksbda\ToBeRich\sysdiag.bat' -WorkingDirectory 'C:\Users\ksbda\ToBeRich'
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName "crypto-live-trading-diag" -Action $action -Principal $principal -Settings $settings -Force

Remove-Item "C:\Users\ksbda\ToBeRich\sysdiag.log" -ErrorAction SilentlyContinue

Start-ScheduledTask -TaskName "crypto-live-trading-diag"
Start-Sleep -Seconds 15

Write-Output "==== task info ===="
Get-ScheduledTaskInfo -TaskName "crypto-live-trading-diag" | Format-List LastRunTime, LastTaskResult

Write-Output "==== sysdiag.log ===="
Get-Content "C:\Users\ksbda\ToBeRich\sysdiag.log" -ErrorAction SilentlyContinue

Unregister-ScheduledTask -TaskName "crypto-live-trading-diag" -Confirm:$false -ErrorAction SilentlyContinue
