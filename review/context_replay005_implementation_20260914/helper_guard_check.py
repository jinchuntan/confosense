"""No-fit guard check: the future real coordinator stays inert without authorization."""
from common import *
manifest=REVIEW/'first_real_execution_manifest_v1.json'
assert not manifest.exists()
result=subprocess.run([PYTHON,'-B',str(REVIEW/'first_real_coordinator.py')],cwd=ROOT,capture_output=True,text=True)
assert result.returncode==1 and 'No real execution' in result.stderr and not manifest.exists()
assert not (SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1').exists()
atomic(REVIEW/'FUTURE_REAL_HELPER_GUARD.json',dict(passed=True,expected_refusal_exit_status=result.returncode,stderr=result.stderr,execution_manifest_absent=True,real_run_absent=True,models_fitted=0))
print('FUTURE REAL HELPER REFUSED AS EXPECTED; NO EXECUTION MANIFEST OR RUN CREATED')
