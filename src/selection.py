"""Frozen tie ordering and selection metrics, extracted without method changes."""
import hashlib
import numpy as np
import pandas as pd

def require(condition,message):
    if not condition: raise ValueError(message)

METRICS = {
    'actual_retained_ratio': ('K', 'N'), 'retained_chargeoff_ratio': ('B_keep', 'K'),
    'removed_chargeoff_ratio': ('B_remove', 'R'), 'chargeoff_capture_rate': ('B_remove', 'B'),
    'paid_exclusion_rate': ('G_remove', 'G'), 'paid_share_among_removed': ('G_remove', 'R'),
}

def rank_scores(loan_ids, scores, seed):
    ids = pd.Series(loan_ids, dtype=str).reset_index(drop=True)
    values = np.asarray(scores, dtype=float)
    require(len(ids) == len(values) and ids.is_unique and ids.str.fullmatch(r'[0-9]+').all(), '排序ID无效')
    require(np.isfinite(values).all(), '排序分数非有限')
    ties = ids.map(lambda loan: hashlib.sha256(f'{seed}:{loan}'.encode('utf-8')).hexdigest())
    keyed = pd.DataFrame(dict(score=values, tie=ties, loan_id=ids, position=np.arange(len(ids))))
    positions = keyed.sort_values(['score', 'tie', 'loan_id'], kind='stable').position.to_numpy()
    independent = np.lexsort((ids.to_numpy(), ties.to_numpy(), values))
    require(np.array_equal(positions, independent), '两种实现的排序不一致')
    ranks = np.empty(len(ids), dtype=int)
    ranks[positions] = np.arange(1, len(ids) + 1)
    return ranks, ties.to_numpy()

def selection_metrics(y, kept):
    y, kept = np.asarray(y, dtype=int), np.asarray(kept, dtype=int)
    require(len(y) == len(kept) and np.isin(y, [0, 1]).all() and np.isin(kept, [0, 1]).all(), '指标标签或标记无效')
    counts = dict(N=len(y), B=int(y.sum()), G=int((1-y).sum()), K=int(kept.sum()), R=int((1-kept).sum()),
                  B_keep=int((y*kept).sum()), B_remove=int((y*(1-kept)).sum()),
                  G_keep=int(((1-y)*kept).sum()), G_remove=int(((1-y)*(1-kept)).sum()))
    require(counts['B_keep'] + counts['B_remove'] == counts['B'] and
            counts['G_keep'] + counts['G_remove'] == counts['G'] and
            counts['K'] + counts['R'] == counts['N'], '指标计数不守恒')
    result = dict(counts, retained_count=counts['K'], removed_paid_count=counts['G_remove'])
    for metric, (numerator, denominator) in METRICS.items():
        result[metric + '_numerator'] = counts[numerator]
        result[metric + '_denominator'] = counts[denominator]
        result[metric] = counts[numerator] / counts[denominator] if counts[denominator] else None
    return result
