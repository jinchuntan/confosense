$ErrorActionPreference = 'Stop'
$taskRepo = 'C:/Users/nigel/OneDrive/Desktop/GitHub/confosense'
$taskProject = $taskRepo + '/smart_building_conformal'
$taskBackup = 'C:/Users/nigel/ConfoSenseBackups/matched_intervals005_bdg2_20260914'
$taskStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffff')
$taskLog = $taskBackup + '/coordinator_' + $taskStamp + '.log'
$taskArguments = @('-B',($taskProject + '/scripts/log_pilot_command.py'),'--log',$taskLog,'--','C:/cfs_venv/Scripts/python.exe','-B',($taskRepo + '/review/matched_intervals005_bdg2_20260914/coordinator.py'))
$taskProcess = Start-Process -FilePath 'C:/cfs_venv/Scripts/python.exe' -ArgumentList $taskArguments -WorkingDirectory $taskProject -RedirectStandardOutput ($taskLog + '.stdout') -RedirectStandardError ($taskLog + '.stderr') -WindowStyle Hidden -PassThru
@{launcher_pid=$taskProcess.Id; launched_utc=[DateTime]::UtcNow.ToString('o'); actual_exit=$null; command=$taskArguments; working_directory=$taskProject; durable_log=$taskLog} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath ($taskLog + '.launch.json') -Encoding UTF8
Write-Output ('Detached logger PID ' + $taskProcess.Id + '; actual exit will be in ' + $taskLog + '.json')
