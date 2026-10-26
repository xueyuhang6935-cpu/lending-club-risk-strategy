"""Validate publisher CSV, isolate approved evaluation years, preserve source row order."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from selection import require

SOURCE_SHA256='207d65b2712f775a91404496ab27c786ac0da6b0f977f849e6d5d8149e925acc'
FIELDS='id issue_d revenue dti_n loan_amnt fico_n experience_c emp_length purpose home_ownership_n addr_state zip_code Default title desc'.split()
MONTHS={m:f'{i:02}' for i,m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(),1)}

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load_source(path,out):
    require(sha(path)==SOURCE_SHA256,'Source SHA-256 differs from the audited publisher CSV')
    # The date column alone is read for 2017/2018. No sealed features or labels are retained/evaluated.
    dates=pd.read_csv(path,usecols=['issue_d'],dtype=str,keep_default_na=False)
    require(len(dates)==1347681,'Expected 1,347,681 source rows')
    parts=dates.issue_d.str.strip().str.extract(r'^([A-Za-z]{3})-([0-9]{4})$')
    months=parts[1]+'-'+parts[0].map(MONTHS)
    require(months.notna().all() and months.between('2007-01','2018-12').all(),'Invalid source months')
    expected={'train':829347,'validation':293057,'sealed':225277}
    counts={'train':int(months.lt('2016-01').sum()),'validation':int(months.between('2016-01','2016-12').sum()),'sealed':int(months.ge('2017-01').sum())}
    require(counts==expected,'Annual split counts differ')
    pieces=[]
    for chunk in pd.read_csv(path,dtype=str,keep_default_na=False,chunksize=100000):
        require(list(chunk.columns)==FIELDS,'Unexpected 15-column schema')
        scope=months.loc[chunk.index].le('2016-12')
        # Chunks necessarily pass later rows in memory; only issue_d is inspected there.
        frame=chunk.loc[scope,['id','fico_n','purpose','emp_length','home_ownership_n','Default','revenue']].copy()
        frame['source_row']=frame.index+1
        frame['issue_month']=months.loc[frame.index]
        pieces.append(frame)
    frame=pd.concat(pieces,ignore_index=True).rename(columns={'id':'loan_id','Default':'y'})
    require(frame.loan_id.str.fullmatch('[0-9]+').all() and frame.loan_id.is_unique,'Invalid/duplicate development IDs')
    require(frame.y.isin(['0','1']).all(),'Label must be publisher 0/1')
    frame['y']=frame.y.astype(int)
    frame['fico_n']=pd.to_numeric(frame.fico_n,errors='raise')
    require(np.isfinite(frame.fico_n).all() and frame.fico_n.between(300,850).all(),'Invalid credit scores')
    frame['approval_year']=frame.issue_month.str[:4].astype(int)
    frame=frame.sort_values('source_row').reset_index(drop=True)
    train=frame.loc[frame.issue_month.lt('2016-01')]
    require(int(train.y.sum())==153062,'Training label counts differ')
    require(sha(path)==SOURCE_SHA256,'Source changed during read')
    audit=dict(source_filename=Path(path).name,source_sha256=SOURCE_SHA256,total_rows=len(dates),split_counts=counts,
        source_order='source_row ascending (matches original MySQL reads)',
        label_definition='publisher Default: 1 Charged Off, 0 Fully Paid; no new status filtering',
        sealed_2017_2018_features_evaluated=False,independent_validation=False)
    (out/'sample_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    return frame
