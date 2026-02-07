"""
File: discount_main.py
Description: Training and inference entry points for the discount recommendation model pipeline.
Dependencies: os, typing, pandas, lightgbm, scikit-learn (via imported modules)
Author: SOFIDA Team

Notes:
- Use train_and_save_artifacts() to train the model and write artifacts to disk.
- Use predict_discount_item() to load artifacts and run discount recommendation without retraining.
- The main() function provides a simple runnable CLI-like entry point for local testing.
"""

import os
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from .feature_engineering import FEPaths, build_feature_table
from .hyperparameter_tuning import tune_lightgbm
from .final_training import train_final_model
from .decision import recommend_discount_item

from .model_io import save_artifacts, load_artifacts


ARTIFACT_PREFIX = "artifacts/discount_lgbm"


def train_and_save_artifacts(
    artifact_prefix: str = ARTIFACT_PREFIX,
    fct_campaigns_path: str = "../../data/fct_campaigns.txt",
    fct_order_items_path: str = "../../data/fct_order_items.txt",
    most_ordered_path: Optional[str] = "../../data/most_ordered.txt",
    n_trials: int = 25,
) -> None:
    """
    Trains a LightGBM model and saves model artifacts to disk.

    This function builds the feature table, performs hyperparameter tuning,
    trains a final model using the best tuned configuration, and saves the
    resulting model and metadata artifacts.

    Args:
        artifact_prefix (str): Output path prefix for artifacts (extensions are added automatically).
        fct_campaigns_path (str): Path to the campaigns dataset.
        fct_order_items_path (str): Path to the order items dataset.
        most_ordered_path (Optional[str]): Optional path to item popularity data.
        n_trials (int): Number of hyperparameter trials to run during tuning.

    Returns:
        None
    """
    os.makedirs(os.path.dirname(artifact_prefix), exist_ok=True)

    paths = FEPaths(
        fct_campaigns_path=fct_campaigns_path,
        fct_order_items_path=fct_order_items_path,
        most_ordered_path=most_ordered_path,
    )
    fe_out = build_feature_table(paths)

    tuning = tune_lightgbm(fe_out, n_trials=n_trials)
    final = train_final_model(fe_out, tuning)

    print("TEST MAE (log1p units/hr):", final.test_mae_log)

    save_artifacts(
        model=final.final_model,
        feature_cols=fe_out.feature_cols,
        categorical_features=final.categorical_features,
        X_ref_for_categories=final.X_trainval_ref,
        out_prefix=artifact_prefix,
    )


def artifacts_exist(artifact_prefix: str = ARTIFACT_PREFIX) -> bool:
    """
    Checks whether the expected model artifacts exist for a given prefix.

    Args:
        artifact_prefix (str): Artifact path prefix (without file extensions).

    Returns:
        bool: True if both the model file and metadata JSON file exist.
    """
    return os.path.exists(f"{artifact_prefix}.txt") and os.path.exists(f"{artifact_prefix}.meta.json")


def predict_discount_item(
    amount_left: float,
    expected_demand_for_remaining: float,
    now_ts_unix: int,
    window_end_ts_unix: int,
    place_id: int,
    item_id: int,
    num_items_targeted: int,
    pct_grid: List[float],
    baseline_pct: float = 0.0,
    aggressiveness: float = 5.0,
    return_debug: bool = True,
    artifact_prefix: str = ARTIFACT_PREFIX,
) -> Union[Dict, Tuple[Dict, pd.DataFrame]]:
    """
    Loads saved model artifacts and runs the discount recommendation logic.

    This function does not train a model. It loads a previously saved model and
    metadata, aligns categorical feature categories for inference, and calls the
    decision routine to recommend an item-level discount.

    Args:
        amount_left (float): Remaining inventory amount to clear.
        expected_demand_for_remaining (float): Baseline expected demand in the remaining time window.
        now_ts_unix (int): Current Unix timestamp (seconds).
        window_end_ts_unix (int): Unix timestamp (seconds) marking the end of the selling window.
        place_id (int): Store or venue identifier.
        item_id (int): Item identifier.
        num_items_targeted (int): Number of items targeted by the campaign.
        pct_grid (List[float]): Candidate discount percentages to evaluate (0..1).
        baseline_pct (float): Baseline discount percentage used for comparison.
        aggressiveness (float): Decision aggressiveness parameter affecting coverage and weighting.
        return_debug (bool): If True, returns an additional debug DataFrame.
        artifact_prefix (str): Artifact path prefix used to load the model and metadata.

    Returns:
        Union[Dict, Tuple[Dict, pd.DataFrame]]:
            - If return_debug is False: result dictionary.
            - If return_debug is True: (result dictionary, debug DataFrame).

    Raises:
        FileNotFoundError: If required artifact files are missing.
    """
    if not artifacts_exist(artifact_prefix):
        raise FileNotFoundError(
            f"Missing artifacts for prefix '{artifact_prefix}'. "
            f"Expected:\n- {artifact_prefix}.txt\n- {artifact_prefix}.meta.json\n"
            "Run train_and_save_artifacts(...) once first."
        )

    model, feature_cols, _, align = load_artifacts(artifact_prefix)

    X_ref_for_categories = align(pd.DataFrame({c: pd.Series([], dtype="object") for c in feature_cols}))

    return recommend_discount_item(
        model=model,
        feature_cols=feature_cols,
        X_ref_for_categories=X_ref_for_categories,
        amount_left=amount_left,
        expected_demand_for_remaining=expected_demand_for_remaining,
        now_ts_unix=now_ts_unix,
        window_end_ts_unix=window_end_ts_unix,
        place_id=place_id,
        item_id=item_id,
        num_items_targeted=num_items_targeted,
        pct_grid=pct_grid,
        baseline_pct=baseline_pct,
        aggressiveness=aggressiveness,
        return_debug=return_debug,
    )



def main(
    train_if_missing: bool = True,
    n_trials: int = 25,
    amount_left: float = 20,
    expected_demand_for_remaining: float = 18,
    place_id: int = 59897,
    item_id: int = 59932,
    num_items_targeted: int = 1,
    now_ts_unix: int | None = None,
    window_hours: float = 3.0,
    window_end_ts_unix: int | None = None,
    pct_grid: list[float] = None,
    baseline_pct: float = 0.00,
    aggressiveness: float = 1.0,
    return_debug: bool = True,
):
    """
    Runs a simple training-and/or-inference flow for local testing.

    If artifacts are missing and train_if_missing is True, this function trains and saves artifacts.
    It then resolves the time window, builds a default discount grid if needed, and calls
    predict_discount_item() to produce a recommendation.

    Args:
        train_if_missing (bool): If True, trains and saves artifacts if they are not found on disk.
        n_trials (int): Number of hyperparameter trials used during training (if training is triggered).
        amount_left (float): Remaining inventory amount to clear.
        expected_demand_for_remaining (float): Baseline expected demand in the remaining time window.
        place_id (int): Store or venue identifier.
        item_id (int): Item identifier.
        num_items_targeted (int): Number of items targeted by the campaign.
        now_ts_unix (int | None): Current Unix timestamp (seconds). If None, uses current UTC time.
        window_hours (float): Window length in hours when window_end_ts_unix is not provided.
        window_end_ts_unix (int | None): Unix timestamp (seconds) marking end of the selling window.
        pct_grid (list[float]): Candidate discount percentages to evaluate (0..1). If None, uses a default grid.
        baseline_pct (float): Baseline discount percentage used for comparison.
        aggressiveness (float): Decision aggressiveness parameter affecting coverage and weighting.
        return_debug (bool): If True, prints and returns debug information.

    Returns:
        Any: The return value from predict_discount_item(), which may include a debug DataFrame.
    """
    if train_if_missing and not artifacts_exist(ARTIFACT_PREFIX):
        train_and_save_artifacts(artifact_prefix=ARTIFACT_PREFIX, n_trials=n_trials)

    if pct_grid is None:
        pct_grid = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]

    if now_ts_unix is None:
        now_ts_unix = int(pd.Timestamp.utcnow().timestamp())

    if window_end_ts_unix is None:
        window_end_ts_unix = int((pd.Timestamp(now_ts_unix, unit="s", tz="UTC") + pd.Timedelta(hours=window_hours)).timestamp())

    out = predict_discount_item(
        amount_left=amount_left,
        expected_demand_for_remaining=expected_demand_for_remaining,
        now_ts_unix=now_ts_unix,
        window_end_ts_unix=window_end_ts_unix,
        place_id=place_id,
        item_id=item_id,
        num_items_targeted=num_items_targeted,
        pct_grid=pct_grid,
        baseline_pct=baseline_pct,
        aggressiveness=aggressiveness,
        return_debug=return_debug,
        artifact_prefix=ARTIFACT_PREFIX,
    )

    if return_debug:
        rec_item, dbg_item = out
        print(rec_item)
        print(
            dbg_item[
                [
                    "pct",
                    "pred_units_model",
                    "pred_units_eq",
                    "pred_units_per_hour",
                    "multiplier_vs_baseline",
                    "adjusted_expected_for_remaining",
                ]
            ].head(20)
        )
        return rec_item, dbg_item

    print(out)
    return out



if __name__ == "__main__":
    main()