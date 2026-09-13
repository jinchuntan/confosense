$ErrorActionPreference = 'Stop'
$batchRepo = 'C:/Users/nigel/OneDrive/Desktop/GitHub/confosense'
$batchProject = $batchRepo + '/smart_building_conformal'
$batchBackup = 'C:/Users/nigel/ConfoSenseBackups/matched_fold2_multiseed_20260914'
$batchStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffff')
New-Item -ItemType Directory -Path $batchBackup -Force | Out-Null
$batchLog = $batchBackup + '/coordinator_' + $batchStamp + '.log'
$batchArguments = @('-B',($batchProject + '/scripts/log_pilot_command.py'),'--log',$batchLog,'--','C:/cfs_venv/Scripts/python.exe','-B',($batchRepo + '/review/matched_fold2_multiseed_20260914/coordinator.py'))
$batchProcess = Start-Process -FilePath 'C:/cfs_venv/Scripts/python.exe' -ArgumentList $batchArguments -WorkingDirectory $batchProject -RedirectStandardOutput ($batchLog + '.stdout') -RedirectStandardError ($batchLog + '.stderr') -WindowStyle Hidden -PassThru
@{launcher_pid=$batchProcess.Id; launched_utc=[DateTime]::UtcNow.ToString('o'); actual_exit=$null; command=$batchArguments; working_directory=$batchProject; durable_log=$batchLog} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath ($batchLog + '.launch.json') -Encoding UTF8
Write-Output ('Detached logger PID ' + $batchProcess.Id + '; actual exit will be in ' + $batchLog + '.json')
