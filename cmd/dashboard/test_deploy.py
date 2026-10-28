"""Rehearse only the documented file operations, using throwaway text binaries."""
from pathlib import Path
import hashlib
import os
import re
import subprocess
import tempfile
import unittest

DOC=Path(__file__).resolve().parents[2]/'docs/DASHBOARD_DEPLOY.md'
def block(name):
    return DOC.read_text().split('# BEGIN FILE '+name)[1].split('\n',1)[1].split('# END FILE '+name)[0]

class DeployTests(unittest.TestCase):
    def test_shell_syntax(self):
        for script in re.findall(r'```bash\n(.*?)```',DOC.read_text(),re.S):
            subprocess.run(['bash','-n'],input=script,text=True,check=True,capture_output=True)
    def test_activation_and_rollback_guards(self):
        for case in ('ok','backup_collision','changed_candidate','changed_installed','changed_backup'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as tmp:
                d=Path(tmp);run=d/'record';run.mkdir();binary=d/'binary';candidate=d/'candidate'
                binary.write_text('original-known-good-A');candidate.write_text('reviewed-candidate-B')
                def digest(file):return hashlib.sha256(file.read_bytes()).hexdigest()
                for file,name in ((binary,'installed-before'),(candidate,'candidate')):
                    (run/(name+'.sha256')).write_text(digest(file)+'  '+str(file)+'\n')
                env=dict(os.environ,run_dir=str(run),binary=str(binary),candidate=str(candidate))
                def shell(name):return subprocess.run(['bash','-euo','pipefail','-c',block(name)],env=env,capture_output=True,text=True)
                if case=='backup_collision':(run/'previous.binary').write_text('do-not-overwrite')
                if case=='changed_candidate':candidate.write_text('unreviewed-C')
                result=shell('ACTIVATION')
                if case in ('backup_collision','changed_candidate'):
                    self.assertNotEqual(result.returncode,0);self.assertEqual(binary.read_text(),'original-known-good-A')
                    if case=='backup_collision':self.assertEqual((run/'previous.binary').read_text(),'do-not-overwrite')
                    continue
                self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(binary.read_text(),'reviewed-candidate-B')
                self.assertEqual((run/'previous.binary').read_text(),'original-known-good-A')
                if case=='changed_installed':binary.write_text('newer-deployment-C')
                if case=='changed_backup':(run/'previous.binary').write_text('damaged-backup')
                result=shell('ROLLBACK')
                if case in ('changed_installed','changed_backup'):
                    self.assertNotEqual(result.returncode,0)
                    self.assertEqual(binary.read_text(),'newer-deployment-C' if case=='changed_installed' else 'reviewed-candidate-B')
                else:
                    self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(binary.read_text(),'original-known-good-A')
                    self.assertEqual((run/'previous.binary').read_text(),'original-known-good-A')

if __name__=='__main__':unittest.main()
