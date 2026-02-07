"""
File: decision.py
Description: Decision logic for recommending discount percentages using a blended model-based and rule-based approach.
Dependencies: typing, numpy, pandas
Author: SOFIDA Team

Notes:
- The recommendation routine evaluates a grid of discount percentages and selects a value based on sell-through targets.
- Category alignment is applied at inference time to prevent LightGBM categorical mismatch errors.
"""

from typing import Optional, Tuple, Union, Dict

import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype

from .feature_engineering import make_daypart


EQ_ALPHA = 1.5
EQ_BETA = 0.8
EQ_MAX_MULT = 3.0


def eq_units_per_hour(
    amount_left: float,
    expected_demand_for_remaining: float,
    pct: float,
    window_hours: float,
    max_boost_factor: float = 3.0,
) -> float:
    """
    Estimates units sold per hour using a simple hand-crafted response curve.

    The estimate is computed as:
    - base_rate = expected_demand_for_remaining / window_hours
    - lift = a capped linear function of the discount percentage
    - shortage_factor = optional multiplier that increases urgency when inventory is high relative to demand

    Args:
        amount_left (float): Remaining inventory amount to clear.
        expected_demand_for_remaining (float): Baseline expected demand in the remaining time window.
        pct (float): Candidate discount percentage as a fraction (0..1).
        window_hours (float): Remaining selling window length in hours.
        max_boost_factor (float): Maximum multiplier allowed for the discount lift effect.

    Returns:
        float: Estimated units sold per hour under the specified discount.
    """
    window_hours = max(window_hours, 1e-6)
    base_rate = expected_demand_for_remaining / window_hours

    lift = 1.0 + 4.5 * pct
    lift = float(np.clip(lift, 0.0, max_boost_factor))

    if expected_demand_for_remaining > 0:
        shortage_ratio = amount_left / expected_demand_for_remaining
        shortage_factor = float(np.clip(0.5 + 0.5 * shortage_ratio, 0.5, 2.0))
    else:
        shortage_factor = 1.0

    return base_rate * lift * shortage_factor


def map_aggressiveness(aggressiveness: float):
    """
    Maps an aggressiveness setting into blending weights and coverage requirements.

    Args:
        aggressiveness (float): User-provided aggressiveness value, expected in the range 0..10.

    Returns:
        Tuple[float, float, float]:
            - w_model: Weight applied to the ML model predictions.
            - w_eq: Weight applied to the rule-based curve predictions.
            - coverage_factor: Multiplier applied to required_units for clearance targeting.
    """
    aggr = float(np.clip(aggressiveness, 0.0, 10.0))
    w_eq = float(np.clip(0.2 + 0.06 * aggr, 0.2, 0.8))
    w_model = 1.0 - w_eq
    coverage_factor = 0.9 + 0.02 * aggr
    return w_model, w_eq, coverage_factor


def clamp_expm1(x, max_x: float = 10.0):
    """
    Applies expm1 to model outputs with clamping and non-negativity enforcement.

    Args:
        x: Input array-like values in log1p space.
        max_x (float): Maximum allowed value before applying expm1.

    Returns:
        np.ndarray: Non-negative values after clamping and expm1 transformation.
    """
    arr = np.asarray(x, dtype=float)
    arr = np.clip(arr, -20.0, max_x)
    y = np.expm1(arr)
    return np.maximum(y, 0.0)


def align_categories_for_inference(X: pd.DataFrame, X_ref: pd.DataFrame) -> pd.DataFrame:
    """
    Aligns categorical columns in an inference DataFrame to match a reference DataFrame.

    Args:
        X (pd.DataFrame): Inference feature matrix to align.
        X_ref (pd.DataFrame): Reference feature matrix containing the expected category sets.

    Returns:
        pd.DataFrame: A copy of X with categorical columns aligned to the reference categories.
    """
    X_out = X.copy()
    for c in X_ref.columns:
        if c in X_out.columns and isinstance(X_ref[c].dtype, CategoricalDtype):
            X_out[c] = pd.Categorical(X_out[c], categories=X_ref[c].cat.categories)
    return X_out


def _lookup_item_prior(
    pop_item: Optional[pd.DataFrame],
    place_id: int,
    item_id: int,
) -> float:
    """
    Looks up an item-level popularity prior for a given place and item.

    Args:
        pop_item (Optional[pd.DataFrame]): Popularity table indexed by place_id and item_id.
        place_id (int): Store or venue identifier.
        item_id (int): Item identifier.

    Returns:
        float: Total order count for the requested (place_id, item_id) pair, or 0.0 if not available.
    """
    if pop_item is None or pop_item.empty:
        return 0.0
    m = pop_item[(pop_item["place_id"] == place_id) & (pop_item["item_id"] == item_id)]
    if m.empty:
        return 0.0
    return float(pd.to_numeric(m["order_count"], errors="coerce").fillna(0.0).sum())


def _lookup_place_prior(
    pop_place: Optional[pd.DataFrame],
    place_id: int,
) -> float:
    """
    Looks up a place-level popularity prior for a given place.

    Args:
        pop_place (Optional[pd.DataFrame]): Popularity table indexed by place_id.
        place_id (int): Store or venue identifier.

    Returns:
        float: Total order count for the requested place_id, or 0.0 if not available.
    """
    if pop_place is None or pop_place.empty:
        return 0.0
    m = pop_place[pop_place["place_id"] == place_id]
    if m.empty:
        return 0.0
    return float(pd.to_numeric(m["place_total_order_count"], errors="coerce").fillna(0.0).sum())

def recommend_discount_item(
    model,
    feature_cols,
    X_ref_for_categories: pd.DataFrame,
    amount_left: float,
    expected_demand_for_remaining: float,
    now_ts_unix: int,
    window_end_ts_unix: int,
    place_id: int,
    item_id: int,
    num_items_targeted: int,
    pct_grid,
    baseline_pct: float = 0.0,
    aggressiveness: float = 5.0,
    pop_item: Optional[pd.DataFrame] = None,
    pop_place: Optional[pd.DataFrame] = None,
    return_debug: bool = False,
):
    """
        Recommends an item-level discount percentage by scoring a grid of candidate discounts.

        This function builds feature rows for each candidate discount in pct_grid, obtains
        model predictions, blends model predictions with a rule-based estimate, and selects
        a discount based on whether adjusted expected demand can meet a required clearance target.

        Args:
            model: Trained model object supporting predict(X).
            feature_cols: Feature column names expected by the model.
            X_ref_for_categories (pd.DataFrame): Reference frame used for categorical alignment.
            amount_left (float): Remaining inventory amount to clear.
            expected_demand_for_remaining (float): Baseline expected demand in the remaining time window.
            now_ts_unix (int): Current Unix timestamp (seconds).
            window_end_ts_unix (int): Unix timestamp (seconds) marking the end of the selling window.
            place_id (int): Store or venue identifier.
            item_id (int): Item identifier.
            num_items_targeted (int): Number of items targeted by the campaign.
            pct_grid: Iterable of candidate discount percentages (0..1).
            baseline_pct (float): Baseline discount percentage used for comparison.
            aggressiveness (float): Decision aggressiveness affecting blending weights and coverage.
            pop_item (Optional[pd.DataFrame]): Optional item-level popularity prior table.
            pop_place (Optional[pd.DataFrame]): Optional place-level popularity prior table.
            return_debug (bool): If True, returns an additional debug DataFrame.

        Returns:
            Union[Dict, Tuple[Dict, pd.DataFrame]]:
                - If return_debug is False: result dictionary containing the chosen discount and key metrics.
                - If return_debug is True: (result dictionary, debug DataFrame with per-candidate details).
        """
    pct_grid = list(sorted(pct_grid))
    window_hours = max((window_end_ts_unix - now_ts_unix) / 3600.0, 1e-6)

    w_model, w_eq, coverage_factor = map_aggressiveness(aggressiveness)

    place_id_int = int(place_id)
    item_id_int = int(item_id)
    item_prior = _lookup_item_prior(pop_item, place_id_int, item_id_int)
    place_prior = _lookup_place_prior(pop_place, place_id_int)

    dt_now = pd.to_datetime(now_ts_unix, unit="s", utc=True)
    hour = int(dt_now.hour)
    dow = int(dt_now.dayofweek)
    month = int(dt_now.month)
    is_weekend = int(dow >= 5)
    daypart_val = make_daypart(hour)

    rows = []
    for p in pct_grid:
        row = {}
        row["discount_kind_final"] = "pct"
        row["discount_pct_final"] = float(p)
        row["buy_qty"] = 0.0
        row["pay_qty"] = 0.0
        row["get_qty"] = 0.0

        row["discount_is_pct"] = 1
        row["discount_is_multibuy"] = 0
        row["discount_is_unknown"] = 0

        eff_mult = float(np.clip(1.0 - p, 0.05, 1.0))
        row["effective_price_multiplier_final"] = eff_mult
        row["effective_discount_depth_final"] = float(np.clip(1.0 - eff_mult, 0.0, 0.95))

        row["duration_hours"] = window_hours
        row["duration_hours_capped"] = min(window_hours, 24 * 30)

        row["has_start_time"] = 1
        row["has_end_time"] = 1
        row["has_valid_time"] = 1
        row["duration_is_valid"] = 1

        row["hour_of_day_start"] = hour
        row["day_of_week_start"] = dow
        row["is_weekend_start"] = is_weekend
        row["month_start"] = month
        row["daypart"] = daypart_val

        row["num_items_targeted"] = int(num_items_targeted)
        row["place_id"] = place_id_int
        row["item_id"] = item_id_int
        row["campaign_segment"] = "item_discount"

        row["order_count"] = item_prior
        row["place_total_order_count"] = place_prior

        rows.append(row)

    X = pd.DataFrame(rows)
    X = X[[c for c in feature_cols if c in X.columns]].copy()
    X = align_categories_for_inference(X, X_ref_for_categories)

    pred_log = model.predict(X)
    pred_units_model = clamp_expm1(pred_log)

    pred_units_eq = np.array([
        eq_units_per_hour(
            amount_left=amount_left,
            expected_demand_for_remaining=expected_demand_for_remaining,
            pct=p,
            window_hours=window_hours,
        )
        for p in pct_grid
    ])

    pred_units_per_hour = w_model * pred_units_model + w_eq * pred_units_eq

    baseline_idx = pct_grid.index(baseline_pct) if baseline_pct in pct_grid else 0
    baseline_units_per_hour = pred_units_per_hour[baseline_idx]

    multiplier_vs_baseline = pred_units_per_hour / max(baseline_units_per_hour, 1e-6)
    adjusted_expected = expected_demand_for_remaining * multiplier_vs_baseline

    aggr = float(np.clip(aggressiveness, 0.0, 10.0))
    relief_max_frac = 0.60 - 0.05 * aggr
    relief_units_per_hour = 2.0 - 0.18 * aggr
    slack_units = min(amount_left * relief_max_frac, relief_units_per_hour * window_hours)

    required_units = max(amount_left - slack_units, 0.0) * coverage_factor

    best_idx = next((i for i, _ in enumerate(pct_grid) if adjusted_expected[i] >= required_units), None)

    if best_idx is None:
        chosen_idx = int(np.argmax(adjusted_expected))
        best_pct = pct_grid[chosen_idx]
        status = "cannot_clear_choose_best_sellthrough"
    else:
        best_pct = pct_grid[best_idx]
        status = "can_clear_inventory"
        chosen_idx = best_idx

    result = {
        "recommended_pct": float(best_pct),
        "pred_units_per_hour": float(pred_units_per_hour[chosen_idx]),
        "baseline_units_per_hour": float(baseline_units_per_hour),
        "multiplier_vs_baseline": float(multiplier_vs_baseline[chosen_idx]),
        "adjusted_expected_for_remaining": float(adjusted_expected[chosen_idx]),
        "amount_left": float(amount_left),
        "expected_demand_for_remaining": float(expected_demand_for_remaining),
        "window_hours": float(window_hours),
        "coverage_factor": float(coverage_factor),
        "w_model": float(w_model),
        "w_eq": float(w_eq),
        "place_id": place_id_int,
        "item_id": item_id_int,
        "campaign_segment": "item_discount",
        "num_items_targeted": int(num_items_targeted),
        "status": status,
        "aggressiveness": float(aggressiveness),
        "required_units": float(required_units),
        "slack_units": float(slack_units),
        "relief_max_frac": float(relief_max_frac),
        "relief_units_per_hour": float(relief_units_per_hour),
    }

    if not return_debug:
        return result

    dbg = X.copy()
    dbg.insert(0, "pct", pct_grid)
    dbg["pred_units_model"] = pred_units_model
    dbg["pred_units_eq"] = pred_units_eq
    dbg["pred_units_per_hour"] = pred_units_per_hour
    dbg["multiplier_vs_baseline"] = multiplier_vs_baseline
    dbg["adjusted_expected_for_remaining"] = adjusted_expected
    dbg["required_units"] = required_units
    dbg["slack_units"] = slack_units
    dbg["chosen"] = dbg["pct"].eq(best_pct)

    return result, dbg


def recommend_discount_bill(
    model,
    feature_cols,
    X_ref_for_categories: pd.DataFrame,
    amount_left: float,
    expected_demand_for_remaining: float,
    now_ts_unix: int,
    window_end_ts_unix: int,
    place_id: int,
    pct_grid,
    baseline_pct: float = 0.0,
    aggressiveness: float = 5.0,
    pop_place: Optional[pd.DataFrame] = None,
    return_debug: bool = False,
):
    """
    Recommends a bill-level discount using the same scoring logic as item-level discounts.

    This is a thin wrapper around recommend_discount_item() that forces item_id to -1
    and num_items_targeted to 0 to represent a bill-level campaign.

    Args:
        model: Trained model object supporting predict(X).
        feature_cols: Feature column names expected by the model.
        X_ref_for_categories (pd.DataFrame): Reference frame used for categorical alignment.
        amount_left (float): Remaining inventory amount to clear.
        expected_demand_for_remaining (float): Baseline expected demand in the remaining time window.
        now_ts_unix (int): Current Unix timestamp (seconds).
        window_end_ts_unix (int): Unix timestamp (seconds) marking the end of the selling window.
        place_id (int): Store or venue identifier.
        pct_grid: Iterable of candidate discount percentages (0..1).
        baseline_pct (float): Baseline discount percentage used for comparison.
        aggressiveness (float): Decision aggressiveness affecting blending weights and coverage.
        pop_place (Optional[pd.DataFrame]): Optional place-level popularity prior table.
        return_debug (bool): If True, returns an additional debug DataFrame.

    Returns:
        Union[Dict, Tuple[Dict, pd.DataFrame]]:
            - If return_debug is False: result dictionary containing the chosen discount and key metrics.
            - If return_debug is True: (result dictionary, debug DataFrame with per-candidate details).
    """
    return recommend_discount_item(
        model=model,
        feature_cols=feature_cols,
        X_ref_for_categories=X_ref_for_categories,
        amount_left=amount_left,
        expected_demand_for_remaining=expected_demand_for_remaining,
        now_ts_unix=now_ts_unix,
        window_end_ts_unix=window_end_ts_unix,
        place_id=int(place_id),
        item_id=-1,
        num_items_targeted=0,
        pct_grid=pct_grid,
        baseline_pct=baseline_pct,
        aggressiveness=aggressiveness,
        pop_item=None,
        pop_place=pop_place,
        return_debug=return_debug,
    )