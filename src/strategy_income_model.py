"""可随joblib加载的固定收入增强模型；所有学习型处理只在fit中进行。"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted

from phase3.preprocessing import FEATURES, RawLoanCleaner


class IncomeFeatures(TransformerMixin, BaseEstimator):
    """有效正收入log1p、训练中位数填补及标准化，始终附加不可用标记。"""

    @staticmethod
    def parse(X):
        if not isinstance(X, pd.DataFrame) or list(X.columns) != ['revenue']:
            raise ValueError('收入输入必须仅有revenue列')
        values = pd.to_numeric(X['revenue'], errors='coerce').to_numpy(dtype=float, na_value=np.nan)
        valid = np.isfinite(values) & (values > 0)
        logged = np.full(len(values), np.nan)
        logged[valid] = np.log1p(values[valid])
        return logged, ~valid

    def fit(self, X, y=None):
        logged, missing = self.parse(X)
        if missing.all():
            raise ValueError('训练收入全部不可用，停止')
        self.median_log_income_ = float(np.median(logged[~missing]))
        filled = np.where(missing, self.median_log_income_, logged)
        self.scaler_ = StandardScaler().fit(filled.reshape(-1, 1))
        self.n_samples_seen_ = len(X)
        self.training_missing_count_ = int(missing.sum())
        self.feature_names_in_ = np.array(['revenue'], dtype=object)
        self.n_features_in_ = 1
        return self

    def transform(self, X):
        check_is_fitted(self, 'median_log_income_')
        logged, missing = self.parse(X)
        filled = np.where(missing, self.median_log_income_, logged)
        scaled = self.scaler_.transform(filled.reshape(-1, 1))
        return np.column_stack([scaled[:, 0], missing.astype(float)])

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, 'median_log_income_')
        return np.array(['log_income_scaled', 'income_unavailable'], dtype=object)


class IncomeLoanCleaner(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None):
        self.transform(X)
        self.feature_names_in_ = np.array([*FEATURES, 'revenue'], dtype=object)
        self.n_features_in_ = len(self.feature_names_in_)
        return self

    def transform(self, X):
        expected = [*FEATURES, 'revenue']
        if not isinstance(X, pd.DataFrame) or list(X.columns) != expected:
            raise ValueError(f'S2输入列及顺序必须为{expected}')
        result = RawLoanCleaner().transform(X.loc[:, FEATURES])
        if not result.fico_n.between(300, 850).all():
            raise ValueError('信用分超出300—850范围')
        result['revenue'] = X['revenue']
        return result

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, 'feature_names_in_')
        return self.feature_names_in_.copy()


def build_income_pipeline(parameters):
    transform = ColumnTransformer([
        ('credit', StandardScaler(), ['fico_n']),
        ('category', OneHotEncoder(handle_unknown='ignore', drop=None, sparse_output=True), list(FEATURES[1:])),
        ('income', IncomeFeatures(), ['revenue']),
    ], remainder='drop', sparse_threshold=1.0)
    return Pipeline([('clean', IncomeLoanCleaner()), ('features', transform),
                     ('model', LogisticRegression(**parameters))])
