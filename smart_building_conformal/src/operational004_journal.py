"""Execution-only guards and durable measurements for a bounded operational run.

No model, event, selection or replay setting is changed here.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
import pandas as pd
from .pilot_resources import ResourceMeter, hardware
from .unit_checkpoint import digest, signature, json_value
from . import split_integrity as SI


class RunJournal:
    def __init__(self, out, resume=False):
        self.root = Path(str(out) + '_execution')
        self.root.mkdir(parents=True, exist_ok=True)
        self.prefix = 'resume' if resume else 'run'
        self.path = self.root / (self.prefix + '_phases.jsonl')
        # Every invocation gets its own record; prior commands are immutable.
        if self.path.exists():
            raise FileExistsError(f'preserve execution journal: {self.path}')
        self.emit('process_start', pid=os.getpid(), parent_pid=os.getppid(),
                  hardware=hardware(), disk=shutil.disk_usage(Path.cwd())._asdict())

    def emit(self, event, **values):
        record = dict(event=event, utc=datetime.now(timezone.utc).isoformat(), **values)
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, default=json_value) + '\n')
            f.flush(); os.fsync(f.fileno())
        print(json.dumps(record, default=json_value), flush=True)

    @contextmanager
    def phase(self, name):
        self.emit('phase_start', phase=name)
        status = 'failed'
        try:
            with ResourceMeter() as meter:
                yield
            status = 'complete'
        finally:
            self.emit('phase_end', phase=name, status=status, **meter.result)

    def freeze(self, spec, frozen, meta, roles, freq):
        entry = next(x for x in frozen['resolved_datasets'] if x['dataset'] == spec['dataset'])
        if spec['resolved_config'] != entry['resolved_dataset_config']:
            raise ValueError('resolved configuration differs from frozen preflight')
        if spec['data_hash'] != entry['data_hash'] or len(meta) != entry['eligible_rows']:
            raise ValueError('prepared feature/data identity differs from frozen preflight')
        if meta.group_id.nunique() != entry['groups'] or str(freq) != entry['freq']:
            raise ValueError('group membership/frequency differs from frozen preflight')
        if spec['horizon'] != entry['horizon']:
            raise ValueError('horizon differs from frozen preflight')
        proposal = json.loads(Path('../review/amendment004_20260913/next_bounded_proposal.json').read_text(encoding='utf-8'))
        if (spec['dataset'], spec['outer_fold'], spec['model_seed']) != ('bdg2', 2, 42):
            raise ValueError('this execution journal authorizes only the published BDG2 unit')
        if spec['candidate_grid'] != proposal['candidate_grid']:
            raise ValueError('candidate grid differs from authorized proposal')
        preflight = Path('outputs/amendment004') / frozen['preflight_run']
        old = pd.read_csv(preflight / 'memberships_summary.csv')
        old = old[(old.dataset == spec['dataset']) & (old.outer_fold == spec['outer_fold'])].set_index('role')
        records = []
        for role, indices in roles.items():
            mh = SI.membership_hash(meta, indices)
            if mh != old.loc[role, 'membership_hash'] or len(indices) != old.loc[role, 'n']:
                raise ValueError(f'preflight membership mismatch: {role}')
            records.append(dict(role=role, n=len(indices), groups=meta.iloc[indices].group_id.nunique(),
                asset_days=len(indices)*float(freq/pd.Timedelta(days=1)), membership_hash=mh))
        spec['membership_hashes'] = {r['role']: r['membership_hash'] for r in records}
        identity = dict(spec=spec, spec_hash=signature(spec), memberships=records,
            preflight_memberships_sha256=digest(preflight/'memberships_summary.csv'),
            proposal_sha256=digest('../review/amendment004_20260913/next_bounded_proposal.json'),
            git_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip())
        path = self.root / 'prefit_identity.json'
        if self.prefix == 'resume':
            prior = json.loads(path.read_text(encoding='utf-8'))
            if prior['spec_hash'] != identity['spec_hash']:
                raise ValueError('pre-fit execution identity mismatch on resume')
        else:
            with path.open('x', encoding='utf-8') as f:
                json.dump(identity, f, indent=2, default=json_value)
                f.flush(); os.fsync(f.fileno())
            pd.DataFrame(records).to_csv(self.root/'membership_summary.csv', index=False)
            members = [meta.iloc[ix][['row_id','group_id','origin_time','target_time']].assign(role=role)
                       for role, ix in roles.items()]
            pd.concat(members,ignore_index=True).to_csv(self.root/'memberships.csv.gz',index=False)
            with zipfile.ZipFile(self.root/'evaluated_source.zip','x',zipfile.ZIP_DEFLATED) as archive:
                for p in sorted(Path('src').rglob('*.py')): archive.write(p,p.as_posix())
        self.emit('prefit_identity_verified', spec_hash=identity['spec_hash'],
            source_hash=spec['source_hash'], membership_roles=len(records),
            candidate_count=len(spec['candidate_grid']))
