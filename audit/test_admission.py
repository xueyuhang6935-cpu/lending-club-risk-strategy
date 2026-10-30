import copy, hashlib, tempfile, unittest
from pathlib import Path
from admission import REQUIRED,evaluate
class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  p=self.root/'evidence.md';p.write_text('Synthetic evidence for gate tests only')
  self.r={'target':'contract_final_chargeoff','evidence':{k:{'confirmed':True,'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'review_note':'synthetic test only','reviewed_by':'unit-test'} for k in REQUIRED}}
 def tearDown(self):self.tmp.cleanup()
 def test_unknowns_and_string_true_fail(self):
  for v in [None,False,'true',1]:
   r=copy.deepcopy(self.r);r['evidence']['snapshot_date']['confirmed']=v
   self.assertFalse(evaluate(r,self.root)['eligible_for_manual_signoff'])
 def test_modified_evidence_fails(self):
  (self.root/'evidence.md').write_text('Changed')
  self.assertFalse(evaluate(self.r,self.root)['eligible_for_manual_signoff'])
 def test_missing_observation_evidence_fails(self):
  del self.r['evidence']['evaluation_observation_sufficient']
  self.assertFalse(evaluate(self.r,self.root)['eligible_for_manual_signoff'])
 def test_missing_fixed_horizon_fails(self):
  self.r['target']='fixed_horizon_chargeoff'
  self.assertFalse(evaluate(self.r,self.root)['eligible_for_manual_signoff'])
 def test_pass_is_never_completed_validation(self):
  r=evaluate(self.r,self.root)
  self.assertTrue(r['eligible_for_manual_signoff']);self.assertFalse(r['independent_validation_complete'])
if __name__=='__main__':unittest.main()
