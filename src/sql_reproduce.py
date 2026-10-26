"""Load rebuilt decisions into the original SQLite schema and execute all nine queries."""
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
from selection import require

ROOT=Path(__file__).resolve().parents[1]

def reproduce_sql(predictions,out):
    temporary=tempfile.TemporaryDirectory(prefix='risk-sql-')
    database=Path(temporary.name)/'sql_reproduction.sqlite'
    config=json.loads((ROOT/'config/groups.json').read_text())
    groups=[]
    for purpose in config['purpose_order']:
        for band in config['main']['fico_bands']:
            groups.append(dict(group_id=json.dumps(['main',purpose,band['group']],ensure_ascii=False,separators=(',',':')),
                purpose_group=purpose,fico_band=band['group'],group_order=len(groups)+1))
    definitions=pd.DataFrame(groups)
    with sqlite3.connect(database) as conn:
        conn.executescript((ROOT/'sql/schema.sql').read_text())
        pd.read_csv(ROOT/'data/cohort_status.csv',keep_default_na=False).to_sql('cohort_status',conn,if_exists='append',index=False)
        definitions.to_sql('groups',conn,if_exists='append',index=False)
        for frame in predictions:
            labels=frame[['evaluation_year','loan_id','source_row','issue_month','y']].rename(columns={'evaluation_year':'year'})
            labels.to_sql('labels',conn,if_exists='append',index=False)
            membership=labels.drop(columns='y').copy()
            purposes=frame.purpose.str.strip().replace('', '__MISSING__')
            require(purposes.isin(config['purpose_order']).all(),'Unregistered purpose group')
            bands=np.searchsorted([660,680,700,720,740],frame.fico_n.to_numpy(),side='right')
            membership['purpose_group']=purposes.to_numpy()
            membership['fico_band']=['F'+str(i+1) for i in bands]
            membership['group_id']=[json.dumps(['main',p,b],ensure_ascii=False,separators=(',',':')) for p,b in zip(membership.purpose_group,membership.fico_band)]
            membership=membership[['year','loan_id','source_row','issue_month','group_id','purpose_group','fico_band']]
            membership.to_sql('membership',conn,if_exists='append',index=False)
            decisions=frame[['evaluation_year','loan_id','source_row','issue_month','y','window',
                'model_version_S0','model_version_S1','model_version_S2','keep_S0','keep_S1','keep_S2']].rename(columns={'evaluation_year':'year'})
            decisions.to_sql('decisions',conn,if_exists='append',index=False)
        require(not conn.execute('PRAGMA foreign_key_check').fetchall(),'Foreign key mismatch')
        require(conn.execute('''SELECT COUNT(*) FROM labels l JOIN membership m USING(year,loan_id)
            JOIN decisions d USING(year,loan_id) WHERE l.source_row<>m.source_row OR l.source_row<>d.source_row
            OR l.issue_month<>m.issue_month OR l.issue_month<>d.issue_month OR l.y<>d.y''').fetchone()[0]==0,'Loan joins differ')
        sql_out=out/'sql';sql_out.mkdir()
        rows={}
        for path in sorted((ROOT/'sql').glob('[0-9]*.sql')):
            query=path.read_text().strip().rstrip(';')
            table={'03':'group_risk','04':'group_contributions','06':'loan_marks'}.get(path.name[:2])
            if table:
                conn.execute(f'CREATE TABLE {table} AS '+query)
                query=f'SELECT * FROM {table}'
                if table=='loan_marks':
                    conn.execute('CREATE UNIQUE INDEX loan_identity ON loan_marks(evaluation_year,loan_id)')
                    conn.execute('CREATE INDEX loan_group ON loan_marks(evaluation_year,group_id)')
            count=0
            for chunk in pd.read_sql_query(query,conn,chunksize=100000):
                chunk.to_csv(sql_out/(path.stem+'.csv'),mode='w' if count==0 else 'a',header=count==0,index=False)
                count+=len(chunk)
            rows[path.stem]=count
            print(f'SQL {path.name}: {count} rows',flush=True)
        require(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity failure')
    shutil.copyfile(database,out/'sql_reproduction.sqlite')
    temporary.cleanup()
    return rows
