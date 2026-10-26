"""S1 pipeline extracted from the final fixed training implementation."""
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from phase3.preprocessing import CATEGORIES, RawLoanCleaner

def build_pipeline():
    parameters = dict(C=1.0, solver='lbfgs', fit_intercept=True, class_weight=None,
                      max_iter=1000, tol=0.0001, random_state=20261019)
    # sklearn >=1.8以l1_ratio=0表达L2，避免显式penalty='l2'的弃用警告。
    release = tuple(int(part) for part in sklearn.__version__.split('.')[:2])
    parameters.update({'l1_ratio': 0.0} if release >= (1, 8) else {'penalty': 'l2'})
    transform = ColumnTransformer([
        ('credit', StandardScaler(), ['fico_n']),
        ('category', OneHotEncoder(handle_unknown='ignore', drop=None, sparse_output=True),
         list(CATEGORIES)),
    ], remainder='drop', sparse_threshold=1.0)
    model = Pipeline([('clean', RawLoanCleaner()), ('features', transform),
                      ('model', LogisticRegression(**parameters))])
    return model, parameters
