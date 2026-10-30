"""Fail-closed metadata gate, before any new loan outcomes are evaluated.
Evidence quality still requires human review; an automated pass is necessary, not sufficient.
python3 improvement_v1/admission.py request.json
"""
import argparse, hashlib, json
from pathlib import Path
REQUIRED=['same_population','origination_features','stable_loan_ids','full_batch_including_nonterminal',
          'snapshot_date','outcome_occurrence_dates','outcome_record_available_dates',
          'evaluation_observation_sufficient','training_information_available_before_evaluation',
          'no_prior_outcome_based_selection','model_and_rules_frozen']
def evaluate(request,root):
 reasons=[];root=Path(root).resolve()
 if request.get('target') not in ['contract_final_chargeoff','fixed_horizon_chargeoff']:
  reasons.append('target_not_defined')
 if request.get('target')=='fixed_horizon_chargeoff' and not isinstance(request.get('horizon_months'),int):
  reasons.append('fixed_horizon_not_defined')
 for key in REQUIRED:
  e=request.get('evidence',{}).get(key,{})
  if e.get('confirmed') is not True:
   reasons.append(key+':not_confirmed');continue
  if not e.get('review_note') or not e.get('reviewed_by'):
   reasons.append(key+':no_documented_review');continue
  p=(root/e.get('path','')).resolve()
  if not p.is_relative_to(root) or not p.is_file():
   reasons.append(key+':missing_or_external_evidence');continue
  with p.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
  if digest!=e.get('sha256'):reasons.append(key+':hash_mismatch')
 return {'eligible_for_manual_signoff':not reasons,'independent_validation_complete':False,'reasons':reasons,
         'note':'metadata gate only; reviewer must verify dates, cohort independence and content before scoring'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('request',type=Path);a=p.parse_args()
 result=evaluate(json.loads(a.request.read_text()),a.request.parent)
 print(json.dumps(result,ensure_ascii=False,indent=2))
 raise SystemExit(0 if result['eligible_for_manual_signoff'] else 2)
