"""可随 joblib 模型加载的原始字段清洗器；不依赖训练脚本的 __main__。"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted


FEATURES = ('fico_n', 'purpose', 'emp_length', 'home_ownership_n')
CATEGORIES = FEATURES[1:]
MISSING = '__MISSING__'


class RawLoanCleaner(TransformerMixin, BaseEstimator):
    """仅接受四个原始特征；原生空值先判断，文本 NA/NULL 等保持原义。"""

    def fit(self, X, y=None):
        self.transform(X)
        self.feature_names_in_ = np.array(FEATURES, dtype=object)
        self.n_features_in_ = len(FEATURES)
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame) or list(X.columns) != list(FEATURES):
            raise ValueError(f'评分输入须为 DataFrame，列及顺序严格为 {FEATURES}')
        result = X.copy()
        raw = result['fico_n']
        text = raw.map(lambda x: '' if pd.isna(x) else str(x).strip())
        number = pd.to_numeric(text, errors='coerce').to_numpy(dtype=float)
        invalid = ~np.isfinite(number)
        if invalid.any():
            raise ValueError(f'信用分缺失、无效或非有限：{int(invalid.sum())}条；停止，不填补')
        result['fico_n'] = number
        for name in CATEGORIES:
            raw = result[name]
            empty = raw.isna()
            text = raw.map(lambda x: '' if pd.isna(x) else str(x).strip())
            # 防止原始类别与程序保留标记混淆。
            if text.eq(MISSING).any():
                raise ValueError(f'{name}原始数据包含程序保留类别{MISSING}，须核实后处理')
            result[name] = text.mask(empty | text.eq(''), MISSING)
        return result

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, 'feature_names_in_')
        return self.feature_names_in_.copy()
