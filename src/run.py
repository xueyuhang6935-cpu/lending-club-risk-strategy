"""Reproduce the existing, fixed strategy comparison from the publisher CSV."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import platform
import time
import warnings
from zoneinfo import ZoneInfo
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from models import build_pipeline
from strategy_income_model import build_income_pipeline
from phase3.preprocessing import FEATURES
from prepare import load_source, sha
from selection import rank_scores, selection_metrics, require
from bootstrap import paired_bootstrap, STRATEGIES
from sql_reproduce import reproduce_sql

ROOT=Path(__file__).resolve().parents[1]
WINDOWS=[('W1','2013-12',230702,2014,223102),('W2','2014-12',453804,2015,375543),('2016_seen','2015-12',829347,2016,293057)]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True,help='Unmodified Zenodo 15-column CSV')
    parser.add_argument('--output',type=Path,required=True,help='New output directory; existing directory is refused')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();out=args.output
    report=dict(status='running',started_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        python=platform.python_version(),platform=platform.platform(),numpy=np.__version__,pandas=pd.__version__,
        sklearn=sklearn.__version__,fixed_method_reproduction=True,hyperparameter_search=False,
        independent_validation=False,bootstrap_repetitions_per_year=2000,stages_seconds={},
        source_code_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').rglob('*.py')) if not p.name.startswith('._')})
    def save():
        report['elapsed_seconds']=time.perf_counter()-started
        (out/'run_record.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    save()
    try:
        tick=time.perf_counter();population=load_source(args.data,out)
        report['stages_seconds']['prepare']=time.perf_counter()-tick
        records=[];intervals=[];predictions=[]
        for window,end,fit_n,year,eval_n in WINDOWS:
            tick=time.perf_counter()
            fit=population.loc[population.issue_month.le(end)]
            evaluation=population.loc[population.approval_year.eq(year)].copy().reset_index(drop=True)
            require(len(fit)==fit_n and len(evaluation)==eval_n,'Window counts differ')
            require(fit.issue_month.max()<evaluation.issue_month.min() and not set(fit.loan_id)&set(evaluation.loan_id),'Training/evaluation overlap')
            directory=out/window;directory.mkdir()
            print(f'{window}: reproduce fixed S1/S2, train={fit_n}, evaluate={eval_n}',flush=True)
            s1,parameters=build_pipeline()
            s2=build_income_pipeline(parameters)
            evaluation['risk_S0']=-evaluation.fico_n
            for name,model,fields in [('S1',s1,list(FEATURES)),('S2',s2,[*FEATURES,'revenue'])]:
                with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=1):
                    warnings.simplefilter('always')
                    model.fit(fit[fields],fit.y.to_numpy(dtype=int))
                require(not any(issubclass(w.category,(ConvergenceWarning,DeprecationWarning,FutureWarning)) for w in caught),'Training warning; stopped')
                estimator=model.named_steps['model']
                require(np.isfinite(estimator.coef_).all() and np.isfinite(estimator.intercept_).all() and int(estimator.n_iter_.max())<1000,'Invalid fit')
                with threadpool_limits(limits=1):scores=model.predict_proba(evaluation[fields])[:,list(model.classes_).index(1)]
                evaluation['risk_'+name]=scores
                joblib.dump(model,directory/(name+'_model.joblib'),compress=3)
                with threadpool_limits(limits=1):reloaded=joblib.load(directory/(name+'_model.joblib')).predict_proba(evaluation[fields])[:,1]
                require(np.max(np.abs(scores-reloaded))<=1e-12,'Model reload differs')
            evaluation['evaluation_year']=year;evaluation['window']=window
            y=evaluation.y.to_numpy(dtype=int);orders=[]
            for strategy in STRATEGIES:
                ranks,ties=rank_scores(evaluation.loan_id,evaluation['risk_'+strategy],20261022)
                orders.append(np.argsort(ranks))
                evaluation['rank_'+strategy]=ranks
                evaluation['model_version_'+strategy]='REPRO_FIXED_'+strategy+'_'+window
                evaluation['keep_'+strategy]=(ranks<=80*len(y)//100).astype(int)
                for ratio in [60,70,80,90]:
                    keep=(ranks<=ratio*len(y)//100).astype(int)
                    records.append(dict(window=window,evaluation_year=year,strategy=strategy,scenario=f'retain_{ratio}',primary=ratio==80,
                        target_retained_ratio=ratio/100,**selection_metrics(y,keep)))
            evaluation.to_csv(directory/'loan_predictions.csv',index=False)
            predictions.append(evaluation)
            report['stages_seconds'][window+'_fit_select']=time.perf_counter()-tick
            tick=time.perf_counter();intervals.extend(paired_bootstrap(year,window,y,orders))
            report['stages_seconds'][window+'_bootstrap']=time.perf_counter()-tick
            pd.DataFrame(records).to_csv(out/'scenario_metrics.csv',index=False)
            pd.DataFrame(intervals).to_csv(out/'bootstrap_intervals.csv',index=False)
            save()
        metrics=pd.DataFrame(records)
        metrics.loc[metrics.primary].to_csv(out/'primary_metrics.csv',index=False)
        tick=time.perf_counter();report['sql_row_counts']=reproduce_sql(predictions,out)
        report['stages_seconds']['sql']=time.perf_counter()-tick
        report['status']='computed_pending_audit';save()
        print(f'Completed in {report["elapsed_seconds"]:.1f}s; run audit/verify.py next',flush=True)
    except Exception as exc:
        report.update(status='failed',error=str(exc));save();raise

if __name__=='__main__':main()
