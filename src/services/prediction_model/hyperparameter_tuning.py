"""
File: hyperparameter_tuning.py
Description: Hyperparameter tuning utilities for training a LightGBM regressor on engineered discount features.
Dependencies: dataclasses, typing, numpy, lightgbm, scikit-learn
Author: SOFIDA Team

Notes:
- This module performs random search over a predefined parameter space.
- Categorical features are aligned across splits to avoid LightGBM category mismatch errors.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error

from .feature_engineering import FeatureEngineeringOutput, build_train_matrices, ensure_categorical_slices


@dataclass
class TuningResult:
    """
    Container for the best tuning outcome.

    Attributes:
        best_mae (float): Best validation mean absolute error achieved across trials.
        best_params (Dict): Parameter set that achieved the best validation MAE.
        best_iter (int): Best iteration selected by early stopping.
        best_model (lgb.Booster): Trained LightGBM model with the best validation MAE.
        categorical_features (List[str]): Names of categorical features used during training.
    """

    best_mae: float
    best_params: Dict
    best_iter: int
    best_model: lgb.Booster
    categorical_features: List[str]


def sample_params(rng: np.random.Generator, seed: int) -> Dict:
    """
    Samples a LightGBM parameter dictionary from a fixed candidate set.

    Args:
        rng (np.random.Generator): Random number generator used to sample parameters.
        seed (int): Seed value assigned to the LightGBM training parameters.

    Returns:
        Dict: LightGBM training parameters for a single trial.
    """
    return {
        "objective": "regression",
        "metric": "mae",
        "learning_rate": float(rng.choice([0.02, 0.03, 0.05, 0.08])),
        "num_leaves": int(rng.choice([31, 63, 127, 255])),
        "max_depth": int(rng.choice([-1, 6, 8, 10, 12])),
        "min_data_in_leaf": int(rng.choice([20, 50, 100, 200])),
        "feature_fraction": float(rng.choice([0.7, 0.8, 0.9, 1.0])),
        "bagging_fraction": float(rng.choice([0.7, 0.8, 0.9, 1.0])),
        "bagging_freq": int(rng.choice([0, 1, 5])),
        "lambda_l1": float(rng.choice([0.0, 0.1, 0.5, 1.0])),
        "lambda_l2": float(rng.choice([0.0, 0.1, 0.5, 1.0])),
        "verbosity": -1,
        "seed": int(seed),
        "feature_pre_filter": False,
    }


def tune_lightgbm(
    out: FeatureEngineeringOutput,
    random_seed: int = 42,
    n_trials: int = 25,
    num_boost_round: int = 5000,
    early_stopping_rounds: int = 200,
) -> TuningResult:
    """
    Tunes LightGBM hyperparameters using repeated random sampling and validation MAE.

    This function samples parameter configurations, trains a LightGBM model with early stopping,
    evaluates MAE on the validation set, and returns the best-performing configuration.

    Args:
        out (FeatureEngineeringOutput): Feature engineering output containing splits and column names.
        random_seed (int): Random seed used for parameter sampling and model training reproducibility.
        n_trials (int): Number of random parameter trials to evaluate.
        num_boost_round (int): Maximum number of boosting rounds for training.
        early_stopping_rounds (int): Early stopping patience based on validation performance.

    Returns:
        TuningResult: Best model, parameters, and validation MAE obtained from the tuning process.

    Raises:
        RuntimeError: If tuning completes without producing a valid best model and parameters.
    """
    categorical_features = [
        c
        for c in ["discount_kind_final", "daypart", "campaign_segment", "place_id", "item_id"]
        if c in out.feature_cols
    ]

    train_df2, valid_df2, test_df2, _ = ensure_categorical_slices(
        out.train_df, out.valid_df, out.test_df, categorical_features
    )

    out2 = FeatureEngineeringOutput(
        df=out.df,
        feature_cols=out.feature_cols,
        target_col=out.target_col,
        time_col=out.time_col,
        train_df=train_df2,
        valid_df=valid_df2,
        test_df=test_df2,
    )

    X_train, y_train, X_valid, y_valid, _, _ = build_train_matrices(out2)

    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=categorical_features, free_raw_data=False)
    valid_data = lgb.Dataset(X_valid, label=y_valid, categorical_feature=categorical_features, free_raw_data=False)

    rng = np.random.default_rng(random_seed)
    best_mae = float("inf")
    best_params: Optional[Dict] = None
    best_iter: Optional[int] = None
    best_model: Optional[lgb.Booster] = None

    for _ in range(n_trials):
        params = sample_params(rng, seed=random_seed)
        model = lgb.train(
            params,
            train_data,
            num_boost_round=num_boost_round,
            valid_sets=[valid_data],
            valid_names=["valid"],
            callbacks=[lgb.early_stopping(stopping_rounds=early_stopping_rounds, verbose=False)],
        )
        pred = model.predict(X_valid, num_iteration=model.best_iteration)
        mae = mean_absolute_error(y_valid, pred)

        if mae < best_mae:
            best_mae = float(mae)
            best_params = params
            best_iter = int(model.best_iteration)
            best_model = model

    if best_params is None or best_iter is None or best_model is None:
        raise RuntimeError("Tuning failed to produce a best model/params.")

    return TuningResult(
        best_mae=best_mae,
        best_params=best_params,
        best_iter=best_iter,
        best_model=best_model,
        categorical_features=categorical_features,
    )
