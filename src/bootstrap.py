"""Loan-paired bootstrap with re-selection; fixed historical seeds and repetitions."""
import numpy as np
from selection import require
PAIRS = [('S1','S0'),('S2','S0'),('S2','S1')]
STRATEGIES = ['S0','S1','S2']

def weighted_bad_count(weights, order, y, k):
    """精确等价于展开重复贷款并排序取前k；避免每轮重复排序。"""
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights)
    require(0 < k <= int(cumulative[-1]), '抽样保留数无效')
    before = cumulative - sorted_weights
    selected = np.minimum(sorted_weights, np.maximum(k - before, 0))
    require(int(selected.sum()) == k, 'bootstrap保留数不等于k')
    return int(selected @ y[order])

def paired_bootstrap(year, window, y, orders):
    k=80*len(y)//100
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([20261022,year])))
    bad_counts=np.empty((2000,3),dtype=np.int64)
    for repeat in range(2000):
        sample=rng.integers(0,len(y),size=len(y),endpoint=False,dtype=np.int64)
        weights=np.bincount(sample,minlength=len(y))
        for j,order in enumerate(orders):
            bad_counts[repeat,j]=weighted_bad_count(weights,order,y,k)
        if (repeat+1)%250==0: print(f'{year}: bootstrap {repeat+1}/2000',flush=True)
    observed=[int(y[o[:k]].sum()) for o in orders]
    intervals=[]
    for candidate,reference in PAIRS:
        ci,ri=STRATEGIES.index(candidate),STRATEGIES.index(reference)
        low,high=np.quantile((bad_counts[:,ci]-bad_counts[:,ri])/k,[.025,.975],method='linear')
        point=(observed[ci]-observed[ri])/k
        intervals.append(dict(window=window,evaluation_year=year,candidate=candidate,reference=reference,
            evaluation_count=len(y),retained_count=k,point_difference=point,lower=float(low),upper=float(high),
            point_difference_pp=100*point,lower_pp=100*low,upper_pp=100*high,
            effective_repetitions=2000,seed=20261022,independent_confirmation=False))
    return intervals
