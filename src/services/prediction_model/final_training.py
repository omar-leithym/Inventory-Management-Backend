"""
File: final_training.py
Description: Final model training utilities for fitting a LightGBM regressor using tuned hyperparameters.
Dependencies: dataclasses, typing, pandas, lightgbm, scikit-learn
Author: SOFIDA Team

Notes:
- This module trains the final model on the combined train and validation splits.
- Categorical features are aligned across dataset splits to prevent category mismatch issues.
- A reference feature matrix is returned to support category alignment during inference.
"""

from dataclasses import dataclass
from typing import List

import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error

from .feature_engineering import FeatureEngineeringOutput, build_train_matrices, ensure_categorical_slices
from .hyperparameter_tuning import TuningResult


@dataclass
class FinalTrainingResult:
    """
    Container for the final training output.

    Attributes:
        final_model (lgb.Booster): Trained LightGBM model fit on train + validation data.
        test_mae_log (float): Mean absolute error on the test split in log space.
        X_trainval_ref (pd.DataFrame): Reference feature matrix for category alignment at inference.
        categorical_features (List[str]): Names of categorical features used during training.
    """

    final_model: lgb.Booster
    test_mae_log: float
    X_trainval_ref: pd.DataFrame
    categorical_features: List[str]


def train_final_model(
    out: FeatureEngineeringOutput,
    tuning: TuningResult,
) -> FinalTrainingResult:
    """
    Trains the final LightGBM model using the best tuned parameters.

    This function aligns categorical features across splits, combines train and validation
    into a single training set, trains a final model for the tuned number of boosting rounds,
    and evaluates performance on the held-out test split.

    Args:
        out (FeatureEngineeringOutput): Feature engineering output containing splits and column names.
        tuning (TuningResult): Tuning result containing best parameters, best iteration, and categorical features.

    Returns:
        FinalTrainingResult: Final trained model, test MAE in log space, and a reference matrix for inference alignment.
    """
    cat_cols = tuning.categorical_features

    train_df2, valid_df2, test_df2, _ = ensure_categorical_slices(out.train_df, out.valid_df, out.test_df, cat_cols)

    out2 = FeatureEngineeringOutput(
        df=out.df,
        feature_cols=out.feature_cols,
        target_col=out.target_col,
        time_col=out.time_col,
        train_df=train_df2,
        valid_df=valid_df2,
        test_df=test_df2,
    )

    X_train, y_train, X_valid, y_valid, X_test, y_test = build_train_matrices(out2)

    trainval_df = pd.concat([out2.train_df, out2.valid_df], axis=0).copy()
    X_trainval = trainval_df[out2.feature_cols].copy()
    y_trainval = trainval_df[out2.target_col].copy()

    trainval_data = lgb.Dataset(
        X_trainval, label=y_trainval,
        categorical_feature=cat_cols,
        free_raw_data=False,
    )

    final_model = lgb.train(tuning.best_params, trainval_data, num_boost_round=tuning.best_iter)

    pred_lgb_log = final_model.predict(X_test)
    test_mae_log = mean_absolute_error(y_test, pred_lgb_log)

    return FinalTrainingResult(
        final_model=final_model,
        test_mae_log=float(test_mae_log),
        X_trainval_ref=X_trainval,
        categorical_features=cat_cols,
    )
