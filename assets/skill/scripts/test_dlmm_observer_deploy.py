"""Execute the exact documented bash blocks against disposable executable stubs."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / 'docs/OBSERVE_BUNDLE_DEPLOY.md'
BASE = 'a' * 40  # synthetic reviewed production base
STUB = r'''#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
name=Path(sys.argv[0]).name; args=sys.argv[1:]; root=Path(os.environ['FIXTURE'])
with (root/'commands.jsonl').open('a') as out: out.write(json.dumps([name]+args)+'\n')
case=os.environ.get('CASE','ok')
if name=='git':
    args=args[2:]
    if args[:1]==['rev-parse']: print((root/'head').read_text().strip())
    elif args[:1]==['merge-base'] and case=='bad_tip': sys.exit(1)
    elif args[:1]==['merge']:
        if case=='merge_fail': sys.exit(1)
        (root/'head').write_text(args[-1])
elif name=='systemctl':
    if case=='restart_fail' and args==['--user','restart','azimuth-sol-monitor']: sys.exit(1)
    if args[:2]==['--user','show']: print('10')
elif name=='python3':
    if Path(args[0]).name=='dlmm_observer_idle.py':
        unit=args[args.index('--unit')+1]
        if case=='busy' or (case=='hermes_busy' and unit=='hermes-gateway'): sys.exit(1)
        count=sum(1 for line in (root/'commands.jsonl').read_text().splitlines()
                  if 'dlmm_observer_idle.py' in line and '"'+unit+'"' in line)
        if case=='busy_late' and count>1: sys.exit(1)
        print(json.dumps(dict(unit=unit,status='idle')));sys.exit(0)
    if '--component' in args and args[args.index('--component')+1]=='pipeline' and case=='pipeline_absent':
        print('synthetic no fresh pipeline child',file=sys.stderr);sys.exit(1)
    args[args.index('--timeout')+1]='0.5' if case in ('no_tick','stale_tick') else '3'
    args[0]=str(Path(os.environ['GATE']))
    proc=root/'proc';proc.mkdir(exist_ok=True);(proc/'stat').write_text('btime 0\n')
    for pid,parent in ((10,1),(11,10)):
        directory=proc/str(pid);directory.mkdir(exist_ok=True)
        fields=['S',str(parent)]+['0']*17+[str(int(time.time()*os.sysconf('SC_CLK_TCK')))]
        (directory/'stat').write_text(str(pid)+' (python3) '+' '.join(fields))
        (directory/'cmdline').write_bytes(b'/usr/bin/python3\0/synthetic/dlmm_pipeline.py\0')
        value=b'0' if os.environ.get('MODE')=='rollback' else b'1'
        (directory/'environ').write_bytes(b'DLMM_REJECT_IDENTITY='+value+b'\0')
    args+=['--proc-root',str(proc)]
    os.execv('/usr/bin/python3',['python3']+args)
elif name=='journalctl':
    if case=='journal_fail': sys.exit(1)
    if case=='no_tick': sys.exit(0)
    unit=args[args.index('-u')+1]; component={'azimuth-sol-monitor':'monitor','azimuth-sol-shadow':'shadow'}.get(unit,'pipeline')
    flag={'monitor':'DLMM_SHADOW_EXITS','pipeline':'DLMM_REJECT_IDENTITY','shadow':'DLMM_BRACKET_REJECTS'}[component]
    now=time.time(); stamp=now-1000 if case=='stale_tick' else now
    row=dict(component=component,pid=123,regular_tick=True,started_at=stamp,completed_at=stamp,
             flags={flag:os.environ.get('MODE')!='rollback' and case!='child_override'})
    print(json.dumps(dict(MESSAGE='OBSERVER_TICK '+json.dumps(row),_PID='99',__REALTIME_TIMESTAMP=str(int(now*1e6)))))
'''


# Generic operator drop-ins: the runbook must protect whatever the operator lists.
PROTECTED = ['azimuth.service.d/operator-override.conf', 'azimuth-sol-monitor.service.d/operator-flag.conf',
             'hermes-gateway.service.d/operator-flag.conf']


class DeployDocumentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); binaries = self.root / 'bin'; binaries.mkdir()
        for name in ('git', 'systemctl', 'journalctl', 'python3'):
            file = binaries / name; file.write_text(STUB); file.chmod(0o755)
        self.env = dict(os.environ, PATH=str(binaries) + ':' + os.environ['PATH'],
                        FIXTURE=str(self.root), GATE=str(ROOT / 'assets/skill/scripts/dlmm_observer_gate.py'),
                        P=str(self.root / 'checkout'), U=str(self.root / 'units'),
                        RUN_PARENT=str(self.root / 'runs'), TIP='b' * 40,
                        REVIEWED_STATUS='', HERMES='0', CASE='ok', EXPECTED_PRE=BASE,
                        PROTECTED_DROPINS=' '.join(PROTECTED))
        (self.root / 'head').write_text(BASE)
        self.protected = []
        for rel in PROTECTED:
            path = self.root / 'units' / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('[Service]\nEnvironment=OPERATOR_FLAG=1\n')
            self.protected.append(path)
        self.protected_before = {p: (p.read_bytes(), p.stat().st_ino) for p in self.protected}

    def block(self, name):
        return re.search(r'<!-- ' + name + r' -->\s*```bash\n(.*?)\n```', DOC.read_text(), re.S)[1]

    def run_block(self, name='activation', **changes):
        return subprocess.run(['bash', '-c', self.block(name)], env=dict(self.env, **changes),
                              capture_output=True, text=True, timeout=30)

    def commands(self):
        return [json.loads(line) for line in (self.root / 'commands.jsonl').read_text().splitlines()]

    def test_restart_failure_stops_before_daemon(self):
        self.assertNotEqual(self.run_block(CASE='restart_fail').returncode, 0)
        self.assertNotIn(['systemctl', '--user', 'restart', 'azimuth'], self.commands())

    def test_merge_failure_does_not_write_dropins_or_restart(self):
        self.assertNotEqual(self.run_block(CASE='merge_fail').returncode, 0)
        self.assertFalse(list((self.root / 'units').glob('*/observe-bundle.conf')))
        self.assertFalse(any(cmd[0] == 'systemctl' for cmd in self.commands()))

    def test_missing_stale_mismatched_or_unreadable_child_evidence_stops_daemon(self):
        for case in ('no_tick', 'stale_tick', 'child_override', 'journal_fail'):
            with self.subTest(case=case):
                for file in (self.root / 'units').glob('*/observe-bundle.conf'): file.unlink()
                (self.root / 'head').write_text(BASE)
                result = self.run_block(CASE=case)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertNotIn(['systemctl', '--user', 'restart', 'azimuth'], self.commands())

    def verify_protected(self):
        self.assertEqual({p: (p.read_bytes(), p.stat().st_ino) for p in self.protected}, self.protected_before)

    def mutations(self):
        return [cmd for cmd in self.commands() if cmd[0] == 'systemctl' and cmd[2] in ('restart', 'start', 'daemon-reload')]

    def assert_guarded_restarts(self, commands):
        for i, cmd in enumerate(commands):
            if cmd[:3] == ['systemctl', '--user', 'restart'] and cmd[-1] in ('azimuth', 'hermes-gateway'):
                previous = commands[i-1]
                self.assertEqual(previous[0], 'python3')
                self.assertTrue(previous[1].endswith('dlmm_observer_idle.py'))
                self.assertEqual(previous[previous.index('--unit')+1], cmd[-1])

    def test_activation_and_rollback_verify_every_requested_child_preserve_other_dropins(self):
        for hermes in ('0', '1'):
            with self.subTest(hermes=hermes):
                (self.root / 'head').write_text(BASE)
                result = self.run_block(HERMES=hermes, CASE='pipeline_absent')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Pipeline evidence PENDING', result.stdout)
                run = Path(result.stdout.splitlines()[0])
                proofs = list(run.glob('*-proof.json'))
                self.assertEqual(len(proofs), 2)  # monitor then shadow; no demand-driven child required
                commands = self.commands()
                starts = self.mutations()
                monitor = starts.index(['systemctl', '--user', 'restart', 'azimuth-sol-monitor'])
                shadow = starts.index(['systemctl', '--user', 'start', 'azimuth-sol-shadow'])
                azimuth = starts.index(['systemctl', '--user', 'restart', 'azimuth'])
                self.assertLess(monitor, shadow); self.assertLess(shadow, azimuth)
                self.assert_guarded_restarts(commands)
                self.verify_protected()
                count = len(list((self.root / 'runs').iterdir()))
                self.assertNotEqual(self.run_block().returncode, 0)  # never re-activate to retry evidence
                self.assertEqual(len(list((self.root / 'runs').iterdir())), count)
                for mode, prefix in (('activation', ''), ('rollback', 'rollback-')):
                    if mode == 'rollback':
                        result = self.run_block('rollback', RUN=str(run), MODE=mode, CASE='pipeline_absent')
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(len(list(run.glob('rollback-*-proof.json'))), 2)
                    before = self.mutations()
                    saved = {name: (run / (prefix+name)).read_text().strip() for name in
                             (['pipeline-since','hermes-since'] if hermes == '1' else ['pipeline-since'])}
                    absent = self.run_block('verification', RUN=str(run), MODE=mode, CASE='pipeline_absent')
                    self.assertEqual(absent.returncode, 0, absent.stderr)
                    self.assertIn('PENDING_NOT_VERIFIED', absent.stdout)
                    verified = self.run_block('verification', RUN=str(run), MODE=mode)
                    self.assertEqual(verified.returncode, 0, verified.stderr)
                    self.assertIn('VERIFIED expected=' + ('0' if mode == 'rollback' else '1'), verified.stdout)
                    self.assertEqual(self.mutations(), before)
                    recent = [x for x in self.commands()[len(commands):]
                              if x[0]=='python3' and '--component' in x and x[x.index('--component')+1]=='pipeline']
                    for cmd in recent[-(4 if hermes == '1' else 2):]:
                        stamp = 'hermes-since' if cmd[cmd.index('--unit')+1]=='hermes-gateway' else 'pipeline-since'
                        self.assertEqual(cmd[cmd.index('--since')+1], saved[stamp])
                    self.verify_protected()
                    commands = self.commands()
                self.assert_guarded_restarts(self.commands())
                self.assertFalse(list((self.root / 'units').glob('*/observe-bundle.conf')))

    def test_inflight_blocks_activation_before_dropins_or_any_restart(self):
        for case in ('busy', 'hermes_busy'):
            with self.subTest(case=case):
                (self.root / 'head').write_text(BASE)
                result = self.run_block(CASE=case, HERMES='1')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.mutations(), [])
                self.assertFalse(list((self.root / 'units').glob('*/observe-bundle.conf')))
                self.verify_protected()

    def test_inflight_blocks_rollback_before_removals_or_any_restart(self):
        result = self.run_block(HERMES='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        run = Path(result.stdout.splitlines()[0]); before = self.mutations()
        for case in ('busy', 'hermes_busy'):
            with self.subTest(case=case):
                result = self.run_block('rollback', RUN=str(run), MODE='rollback', CASE=case)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.mutations(), before)
                self.assertEqual(len(list((self.root / 'units').glob('*/observe-bundle.conf'))), 4)
                self.verify_protected()

    def test_new_busy_work_after_preflight_stops_actual_restart(self):
        result = self.run_block(CASE='busy_late')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(['systemctl', '--user', 'restart', 'azimuth'], self.commands())
        run = Path(result.stdout.splitlines()[0])
        self.assertNotEqual(self.run_block('verification', RUN=str(run)).returncode, 0)
        self.verify_protected()

    def test_wrong_base_or_sibling_tip_is_refused(self):
        (self.root / 'head').write_text('c' * 40)
        self.assertNotEqual(self.run_block().returncode, 0)
        (self.root / 'head').write_text(BASE)
        self.assertNotEqual(self.run_block(CASE='bad_tip').returncode, 0)
        self.assertFalse((self.root / 'runs').exists())
        self.verify_protected()

    def test_rollback_refuses_changed_dropin_before_removing_any(self):
        result = self.run_block()
        self.assertEqual(result.returncode, 0, result.stderr)
        run = Path(result.stdout.splitlines()[0])
        file = self.root / 'units/azimuth.service.d/observe-bundle.conf'
        file.write_text('somebody else edited this\n')
        self.assertNotEqual(self.run_block('rollback', RUN=str(run), MODE='rollback').returncode, 0)
        self.assertEqual(len(list((self.root / 'units').glob('*/observe-bundle.conf'))), 3)
        self.assertEqual(file.read_text(), 'somebody else edited this\n')

    def test_changed_canary_stops_rollback_before_removals_or_restart(self):
        result = self.run_block()
        self.assertEqual(result.returncode, 0, result.stderr)
        run = Path(result.stdout.splitlines()[0]); before = self.mutations()
        canary = self.root / 'units/azimuth-sol-monitor.service.d/operator-flag.conf'
        canary.write_text('a newer canary configuration\n')
        result = self.run_block('rollback', RUN=str(run), MODE='rollback')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), before)
        self.assertEqual(len(list((self.root / 'units').glob('*/observe-bundle.conf'))), 3)
        self.assertEqual(canary.read_text(), 'a newer canary configuration\n')


    def test_operator_variables_are_required_and_validated(self):
        for changes in (dict(EXPECTED_PRE=''), dict(EXPECTED_PRE='abc'),
                        dict(PROTECTED_DROPINS='../escape.conf'),
                        dict(PROTECTED_DROPINS='azimuth.service.d/observe-bundle.conf'),
                        dict(PROTECTED_DROPINS='azimuth.service.d/missing.conf')):
            with self.subTest(**changes):
                result = self.run_block(**changes)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / 'runs').exists())
                self.assertFalse((self.root / 'commands.jsonl').exists() and self.mutations())
        variables = dict(self.env)
        variables.pop('PROTECTED_DROPINS')
        result = subprocess.run(['bash', '-c', self.block('activation')], env=variables,
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)  # unset is refused; only an explicit empty list means none
        self.verify_protected()

    def test_empty_protected_list_still_activates_and_rolls_back(self):
        result = self.run_block(PROTECTED_DROPINS='')
        self.assertEqual(result.returncode, 0, result.stderr)
        run = Path(result.stdout.splitlines()[0])
        self.assertEqual((run / 'protected-dropins.sha256').read_text(), '')
        result = self.run_block('rollback', RUN=str(run), MODE='rollback')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.verify_protected()


if __name__ == '__main__':
    unittest.main()
