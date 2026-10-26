"""Compare rebuilt outputs to historical accepted aggregates and interval endpoints."""
import argparse
import json
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
KEYS={
 '01_status_distribution':['approval_year','term','loan_status'],
 '02_maturity':['approval_year','term'],
 '03_group_risk':['year','group_id'],
 '04_group_contributions':['comparison','group_id'],
 '05_decomposition_summary':['comparison'],
 '07_primary_metrics':['evaluation_year','strategy'],
 '08_strategy_cross':['evaluation_year','candidate','reference','group'],
 '09_group_exchange':['evaluation_year','candidate','reference','group_id'],
}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True)
    run=parser.parse_args().run;checks=[]
    def check(ok,name):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    def compare(actual,reference,keys,name):
        a=pd.read_csv(actual,float_precision='round_trip').set_index(keys).sort_index()
        b=pd.read_csv(reference,float_precision='round_trip').set_index(keys).sort_index()
        check(a.index.is_unique and b.index.is_unique and a.index.equals(b.index),name+': complete unique keys')
        skip={'model_version','model_version_S0','model_version_S1','model_version_S2'}
        for column in b.columns:
            if column in skip:continue
            check(column in a.columns,name+': column '+column)
            x,y=a[column],b[column]
            if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                if pd.api.types.is_integer_dtype(y):ok=np.array_equal(x.to_numpy(),y.to_numpy())
                else:ok=np.allclose(x.to_numpy(dtype=float),y.to_numpy(dtype=float),rtol=0,atol=1e-12,equal_nan=True)
            else:ok=x.fillna('__NULL__').astype(str).equals(y.fillna('__NULL__').astype(str))
            check(ok,name+': values '+column)
    result={'status':'running','checks':checks}
    try:
        record=json.loads((run/'run_record.json').read_text())
        check(record['status']=='computed_pending_audit','computation completed')
        compare(run/'scenario_metrics.csv',ROOT/'results/reference/scenario_metrics.csv',['evaluation_year','strategy','scenario'],'36 scenario metrics')
        # Historical interval annotations are descriptive metadata; endpoints/counts are checked explicitly.
        ref=pd.read_csv(ROOT/'results/reference/bootstrap_intervals.csv')
        columns=['evaluation_year','candidate','reference','evaluation_count','retained_count','point_difference','lower','upper','point_difference_pp','lower_pp','upper_pp','effective_repetitions','seed','independent_confirmation']
        temporary=run/'bootstrap_reference_check.csv';ref[columns].to_csv(temporary,index=False)
        compare(run/'bootstrap_intervals.csv',temporary,['evaluation_year','candidate','reference'],'9 bootstrap intervals')
        temporary.unlink()
        for name,keys in KEYS.items():compare(run/'sql'/(name+'.csv'),ROOT/'results/reference/sql'/(name+'.csv'),keys,'SQL '+name)
        with sqlite3.connect(run/'sql_reproduction.sqlite') as conn:
            check(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','database integrity')
            check(not conn.execute('PRAGMA foreign_key_check').fetchall(),'database foreign keys')
            check(conn.execute('SELECT COUNT(*) FROM loan_marks').fetchone()[0]==891702,'891702 unique loan marks')
            for year,n,k in [(2014,223102,178481),(2015,375543,300434),(2016,293057,234445)]:
                check(conn.execute('SELECT COUNT(*),SUM(keep_S0),SUM(keep_S1),SUM(keep_S2) FROM loan_marks WHERE evaluation_year=?',(year,)).fetchone()==(n,k,k,k),str(year)+': equal retained quantities')
        result.update(status='passed',check_count=len(checks),float_absolute_tolerance=1e-12)
    except Exception as exc:
        result.update(status='failed',error=str(exc));raise
    finally:(run/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'PASS: {len(checks)} checks; historical integers, NULLs and float outputs agree')
if __name__=='__main__':main()
