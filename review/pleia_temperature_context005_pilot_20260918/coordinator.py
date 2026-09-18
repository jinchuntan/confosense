"""Adopt the verified temperature run and continue only post-run stages."""
import json,subprocess,time,psutil
from pathlib import Path
R=Path(__file__).resolve().parents[2]; S=R/'smart_building_conformal'; O=S/'outputs/conditional_context005/pleia_f2_s42_C_v1'; C=S/'outputs/conditional_context005/pleia_temperature_f2_context005_pilot_v1_coordinator'; M=R/'review/pleia_temperature_context005_pilot_20260918/pleia_f2_s42_C_v1_execution_manifest.json'; D=S/'protocols/conditional_context005/pleia_f2_s42_C_v1'
state=C/'coordinator_status.json'; launch=json.loads((C/'RUN_LAUNCH.json').read_text()); pid=launch['logger_pid']
def save(**kw): state.write_text(json.dumps(kw,indent=2))
def alive(p): return psutil.pid_exists(p)
save(status='adopted_run',logger_pid=pid,logger_created_utc=launch['created_utc'],expected_complete=str(O/'COMPLETE.json'))
while alive(pid): time.sleep(20)
if not (O/'COMPLETE.json').exists(): save(status='run_exited_without_complete',logger_pid=pid); raise SystemExit(2)
for action,receipt in [('validate',C/'validation'),('resume',C/'completed_resume.json')]:
 save(status=action,logger_pid=pid)
 cmd=['C:/cfs_venv/Scripts/python.exe','-B','-m','src.conditional_context005',action,'--manifest',str(M),'--design',str(D),'--out',str(O),'--readiness',str(D/'readiness.json'),'--receipt',str(receipt)]
 subprocess.run(cmd,cwd=S,check=True)
save(status='validated_and_resumed',logger_pid=pid)

