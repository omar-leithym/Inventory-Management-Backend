"""
File: feature_engineering.py
Description: Feature engineering utilities for building a training dataset for discount-demand modeling.
Dependencies: re, dataclasses, typing, numpy, pandas
Author: SOFIDA Team

Notes:
- This module is import-safe and does not perform file I/O on import.
- Use build_feature_table() to load raw CSVs and produce train/valid/test splits and feature columns.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


RANDOM_SEED = 42


def parse_item_ids(item_ids_value) -> List[int]:
    """
    Parses a raw item_ids value into a list of integer item IDs.

    Args:
        item_ids_value: Raw value representing item IDs (may be NaN, string, or mixed types).

    Returns:
        List[int]: A de-duplicated list of item IDs in the original order.
    """
    if pd.isna(item_ids_value):
        return []
    s = str(item_ids_value).strip().strip('"').strip("'")
    if s == "" or s.lower() == "nan":
        return []
    parts = [p.strip() for p in s.split(",")]
    out: List[int] = []
    for p in parts:
        m = re.search(r"(\d+)", p)
        if m:
            out.append(int(m.group(1)))

    seen = set()
    dedup: List[int] = []
    for v in out:
        if v not in seen:
            dedup.append(v)
            seen.add(v)
    return dedup


def parse_discount(raw) -> Tuple[str, Optional[float], Optional[int], Optional[int], Optional[int]]:
    """
    Parses a raw discount representation into a structured discount description.

    Args:
        raw: Raw discount value (may be NaN, numeric, or string).

    Returns:
        Tuple[str, Optional[float], Optional[int], Optional[int], Optional[int]]:
            - discount_kind (str): One of 'pct', 'x_for_y', 'buy_x_get_y', 'bogo', or 'unknown'.
            - discount_pct (Optional[float]): Percent discount as a fraction (0..1) when kind is 'pct', otherwise NaN.
            - buy_qty (Optional[int]): Buy quantity for multi-buy formats, otherwise NaN.
            - pay_qty (Optional[int]): Pay quantity for 'x_for_y' format, otherwise NaN.
            - get_qty (Optional[int]): Get quantity for 'buy_x_get_y' format, otherwise NaN.
    """
    if pd.isna(raw):
        return ("unknown", np.nan, np.nan, np.nan, np.nan)

    s = str(raw).strip().lower()

    m = re.search(r"^\s*(\d+(\.\d+)?)\s*%?\s*$", s)
    if m:
        pct = float(m.group(1)) / 100.0
        return ("pct", pct, np.nan, np.nan, np.nan)

    m = re.search(r"(\d+)\s*for\s*(\d+)", s)
    if m:
        x = int(m.group(1))
        y = int(m.group(2))
        return ("x_for_y", np.nan, x, y, np.nan)

    m = re.search(r"buy\s*(\d+)\s*get\s*(\d+)", s)
    if m:
        buy = int(m.group(1))
        get = int(m.group(2))
        return ("buy_x_get_y", np.nan, buy, np.nan, get)

    if "bogo" in s or "buy one get one" in s or "2x1" in s:
        return ("bogo", np.nan, 2, 1, 1)

    return ("unknown", np.nan, np.nan, np.nan, np.nan)


def parse_discount_any(row) -> Tuple[str, Optional[float], Optional[int], Optional[int], Optional[int]]:
    """
    Parses a discount from a row using available fields.

    Args:
        row: A row-like object (e.g., pandas Series) expected to include 'discount_raw' and/or 'type'.

    Returns:
        Tuple[str, Optional[float], Optional[int], Optional[int], Optional[int]]: Parsed discount tuple.
    """
    d = row.get("discount_raw", np.nan)
    if not pd.isna(d):
        return parse_discount(d)
    return parse_discount(row.get("type", ""))


def safe_unix_to_dt(x) -> pd.Series:
    """
    Converts a Unix timestamp series to timezone-aware UTC datetimes.

    Args:
        x: Input values representing Unix timestamps in seconds.

    Returns:
        pd.Series: Datetime series in UTC with invalid values coerced to NaT.
    """
    s = pd.to_numeric(x, errors="coerce")
    return pd.to_datetime(s, unit="s", utc=True, errors="coerce")


def make_daypart(hour: float) -> str:
    """
    Maps an hour-of-day value to a coarse daypart category.

    Args:
        hour (float): Hour of day (0..23). Negative values map to 'unknown'.

    Returns:
        str: One of 'morning', 'afternoon', 'evening', 'night', or 'unknown'.
    """
    if hour < 0:
        return "unknown"
    h = int(hour)
    if 5 <= h <= 10:
        return "morning"
    if 11 <= h <= 15:
        return "afternoon"
    if 16 <= h <= 20:
        return "evening"
    return "night"


def effective_multiplier_from_parsed(kind: str, pct: float, buy: float, pay: float, get: float) -> float:
    """
    Computes an effective price multiplier from a parsed discount specification.

    Args:
        kind (str): Discount kind ('pct', 'x_for_y', 'buy_x_get_y', 'bogo', or 'unknown').
        pct (float): Discount percent as a fraction (0..1) when kind is 'pct'.
        buy (float): Buy quantity for multi-buy formats.
        pay (float): Pay quantity for 'x_for_y' format.
        get (float): Get quantity for 'buy_x_get_y' format.

    Returns:
        float: Effective price multiplier (0.05..1.0), where lower values indicate deeper discounts.
    """
    if kind == "pct" and np.isfinite(pct):
        return float(np.clip(1.0 - pct, 0.05, 1.0))
    if kind == "x_for_y" and np.isfinite(buy) and np.isfinite(pay) and buy > 0:
        return float(np.clip(pay / buy, 0.05, 1.0))
    if kind == "buy_x_get_y" and np.isfinite(buy) and np.isfinite(get) and (buy + get) > 0:
        return float(np.clip(buy / (buy + get), 0.05, 1.0))
    if kind == "bogo":
        return 0.5
    return 1.0


def ensure_categorical_slices(train_df, valid_df, test_df, cat_cols):
    """
    Aligns categorical columns across train/valid/test splits.

    This ensures all splits share identical pandas category sets, which prevents
    category mismatch errors during model training or inference.

    Args:
        train_df: Training DataFrame split.
        valid_df: Validation DataFrame split.
        test_df: Test DataFrame split.
        cat_cols: List of column names to treat as categorical.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            - aligned_train_df
            - aligned_valid_df
            - aligned_test_df
            - reference_df containing the categorical reference categories
    """
    ref = pd.concat([train_df[cat_cols], valid_df[cat_cols]], axis=0).copy()
    for c in cat_cols:
        ref[c] = ref[c].astype("category")

    def _align(df_):
        df_ = df_.copy()
        for c in cat_cols:
            df_[c] = pd.Categorical(df_[c], categories=ref[c].cat.categories)
        return df_

    return _align(train_df), _align(valid_df), _align(test_df), ref


@dataclass(frozen=True)
class FEPaths:
    """
    File path configuration for feature engineering inputs.

    Attributes:
        fct_campaigns_path (str): Path to the campaigns CSV.
        fct_order_items_path (str): Path to the order items CSV.
        most_ordered_path (Optional[str]): Optional path to item popularity CSV.
    """

    fct_campaigns_path: str
    fct_order_items_path: str
    most_ordered_path: Optional[str] = None


@dataclass
class FeatureEngineeringOutput:
    """
    Output container for engineered feature data and dataset splits.

    Attributes:
        df (pd.DataFrame): Full engineered dataset.
        feature_cols (List[str]): Feature column names used for training/inference.
        target_col (str): Target column name.
        time_col (str): Time column name used for time-based sorting/splitting.
        train_df (pd.DataFrame): Training split.
        valid_df (pd.DataFrame): Validation split.
        test_df (pd.DataFrame): Test split.
    """

    df: pd.DataFrame
    feature_cols: List[str]
    target_col: str
    time_col: str
    train_df: pd.DataFrame
    valid_df: pd.DataFrame
    test_df: pd.DataFrame


def build_feature_table(
    paths: FEPaths,
    random_seed: int = RANDOM_SEED,
    duration_cap_days: int = 30,
) -> FeatureEngineeringOutput:
    """
    Builds the feature table used for model training and evaluation.

    This function reads raw campaign and order item data, constructs discount and
    time features, creates an outcome signal, and returns a time-ordered split
    into train/validation/test sets.

    Args:
        paths (FEPaths): Input file paths for required and optional datasets.
        random_seed (int): Random seed for any stochastic operations.
        duration_cap_days (int): Maximum duration cap for campaign hours, expressed in days.

    Returns:
        FeatureEngineeringOutput: Engineered dataset, feature columns, target/time columns, and splits.

    Raises:
        Exception: Propagates file and parsing exceptions encountered during processing.
    """
    np.random.seed(random_seed)

    campaigns = pd.read_csv(paths.fct_campaigns_path)
    order_items = pd.read_csv(paths.fct_order_items_path, low_memory=False)

    most_ordered = None
    if paths.most_ordered_path:
        try:
            most_ordered = pd.read_csv(paths.most_ordered_path)
        except Exception:
            most_ordered = None

    if "id" in campaigns.columns and "campaign_id" not in campaigns.columns:
        campaigns = campaigns.rename(columns={"id": "campaign_id"})
    campaigns["campaign_id"] = pd.to_numeric(campaigns["campaign_id"], errors="coerce")

    campaigns["start_ts"] = pd.to_numeric(campaigns.get("start_date_time"), errors="coerce")
    campaigns["end_ts"] = pd.to_numeric(campaigns.get("end_date_time"), errors="coerce")
    campaigns["start_dt"] = safe_unix_to_dt(campaigns["start_ts"])
    campaigns["end_dt"] = safe_unix_to_dt(campaigns["end_ts"])

    campaigns["has_start_time"] = campaigns["start_dt"].notna().astype(int)
    campaigns["has_end_time"] = campaigns["end_dt"].notna().astype(int)
    campaigns["has_valid_time"] = (campaigns["has_start_time"] & campaigns["has_end_time"]).astype(int)

    campaigns["duration_hours"] = (campaigns["end_ts"] - campaigns["start_ts"]) / 3600.0
    campaigns["duration_is_valid"] = (campaigns["duration_hours"] > 0).astype(int)
    campaigns["duration_hours"] = campaigns["duration_hours"].fillna(0.0).clip(lower=0.0)
    campaigns["duration_hours_capped"] = campaigns["duration_hours"].clip(upper=24 * duration_cap_days)

    type_clean = campaigns.get("type", "").astype(str).str.strip().str.lower()
    seg = np.select(
        [
            type_clean.str.contains("total bill", na=False),
            type_clean.str.contains("specific menu items", na=False),
        ],
        ["bill_discount", "item_discount"],
        default="other",
    )
    campaigns["campaign_segment"] = pd.Categorical(seg, categories=["item_discount", "bill_discount", "other"])

    campaigns["discount_raw"] = campaigns.get("discount", np.nan)
    parsed = campaigns.apply(parse_discount_any, axis=1)

    campaigns["discount_kind"] = pd.Categorical(
        [t[0] for t in parsed],
        categories=["pct", "x_for_y", "buy_x_get_y", "bogo", "unknown"],
    )
    campaigns["discount_pct"] = pd.to_numeric([t[1] for t in parsed], errors="coerce")
    campaigns["buy_qty"] = pd.to_numeric([t[2] for t in parsed], errors="coerce")
    campaigns["pay_qty"] = pd.to_numeric([t[3] for t in parsed], errors="coerce")
    campaigns["get_qty"] = pd.to_numeric([t[4] for t in parsed], errors="coerce")

    campaigns["discount_is_pct"] = (campaigns["discount_kind"] == "pct").astype(int)
    campaigns["discount_is_multibuy"] = campaigns["discount_kind"].isin(["x_for_y", "buy_x_get_y", "bogo"]).astype(int)
    campaigns["discount_is_unknown"] = (campaigns["discount_kind"] == "unknown").astype(int)

    campaigns["effective_price_multiplier"] = [
        effective_multiplier_from_parsed(k, p, b, pay, g)
        for k, p, b, pay, g in zip(
            campaigns["discount_kind"].astype(str),
            campaigns["discount_pct"].values,
            campaigns["buy_qty"].values,
            campaigns["pay_qty"].values,
            campaigns["get_qty"].values,
        )
    ]
    campaigns["effective_price_multiplier"] = pd.to_numeric(campaigns["effective_price_multiplier"], errors="coerce").fillna(1.0)
    campaigns["effective_discount_depth"] = (1.0 - campaigns["effective_price_multiplier"]).clip(lower=0.0, upper=0.95)

    if "item_ids" in campaigns.columns:
        campaigns["item_id_list"] = campaigns["item_ids"].apply(parse_item_ids)
    else:
        campaigns["item_id_list"] = [[] for _ in range(len(campaigns))]
    campaigns["num_items_targeted"] = campaigns["item_id_list"].apply(len)

    item_seg = campaigns[campaigns["campaign_segment"] == "item_discount"].copy()
    bill_seg = campaigns[campaigns["campaign_segment"] == "bill_discount"].copy()
    other_seg = campaigns[campaigns["campaign_segment"] == "other"].copy()

    item_expl = item_seg.explode("item_id_list").rename(columns={"item_id_list": "item_id"})
    item_expl.loc[:, "item_id"] = pd.to_numeric(item_expl["item_id"], errors="coerce").fillna(-2).astype(int)

    bill_seg = bill_seg.copy()
    other_seg = other_seg.copy()
    bill_seg.loc[:, "item_id"] = -1
    other_seg.loc[:, "item_id"] = -3
    bill_seg.loc[:, "num_items_targeted"] = pd.to_numeric(bill_seg["num_items_targeted"], errors="coerce").fillna(0).astype(int)
    other_seg.loc[:, "num_items_targeted"] = pd.to_numeric(other_seg["num_items_targeted"], errors="coerce").fillna(0).astype(int)

    base = pd.concat([item_expl, bill_seg, other_seg], ignore_index=True)

    oi = order_items.copy()
    oi["campaign_id"] = pd.to_numeric(oi.get("campaign_id"), errors="coerce")
    oi = oi[oi["campaign_id"].notna()].copy()

    oi["created_ts"] = pd.to_numeric(oi.get("created"), errors="coerce")
    oi["item_id"] = pd.to_numeric(oi.get("item_id"), errors="coerce")
    oi["quantity"] = pd.to_numeric(oi.get("quantity"), errors="coerce").fillna(0.0)
    oi["price"] = pd.to_numeric(oi.get("price"), errors="coerce").fillna(0.0)
    oi["discount_amount"] = pd.to_numeric(oi.get("discount_amount"), errors="coerce").fillna(0.0)
    oi["gross_line"] = (oi["price"] * oi["quantity"]).astype(float)

    oi = oi.merge(
        campaigns[["campaign_id", "start_ts", "end_ts"]],
        on="campaign_id",
        how="left",
    )

    oi["in_window"] = (
        oi["created_ts"].notna()
        & oi["start_ts"].notna()
        & oi["end_ts"].notna()
        & (oi["created_ts"] >= oi["start_ts"])
        & (oi["created_ts"] <= oi["end_ts"])
    )
    oiw = oi[oi["in_window"]].copy()
    oiw_disc = oiw[oiw["discount_amount"] > 0].copy()

    agg_item_units = oiw.groupby(["campaign_id", "item_id"], as_index=False).agg(units_sold=("quantity", "sum"))

    agg_item_disc = oiw_disc.groupby(["campaign_id", "item_id"], as_index=False).agg(
        disc_gross=("gross_line", "sum"),
        disc_total=("discount_amount", "sum"),
    )
    agg_item_disc["effective_discount_pct_obs"] = np.where(
        agg_item_disc["disc_gross"] > 0,
        agg_item_disc["disc_total"] / agg_item_disc["disc_gross"],
        np.nan,
    ).clip(0.0, 0.95)

    agg_campaign_units = oiw.groupby("campaign_id", as_index=False).agg(campaign_units_sold=("quantity", "sum"))

    agg_campaign_disc = oiw_disc.groupby("campaign_id", as_index=False).agg(
        camp_disc_gross=("gross_line", "sum"),
        camp_disc_total=("discount_amount", "sum"),
    )
    agg_campaign_disc["campaign_effective_discount_pct_obs"] = np.where(
        agg_campaign_disc["camp_disc_gross"] > 0,
        agg_campaign_disc["camp_disc_total"] / agg_campaign_disc["camp_disc_gross"],
        np.nan,
    ).clip(0.0, 0.95)

    df = base.merge(agg_item_units, on=["campaign_id", "item_id"], how="left")
    df = df.merge(
        agg_item_disc[["campaign_id", "item_id", "effective_discount_pct_obs"]],
        on=["campaign_id", "item_id"],
        how="left",
    )
    df = df.merge(agg_campaign_units, on="campaign_id", how="left")
    df = df.merge(
        agg_campaign_disc[["campaign_id", "campaign_effective_discount_pct_obs"]],
        on="campaign_id",
        how="left",
    )

    df["units_sold"] = df["units_sold"].fillna(0.0)
    df["campaign_units_sold"] = df["campaign_units_sold"].fillna(0.0)

    df["label_units"] = np.where(
        (df["campaign_segment"].astype(str) == "item_discount") & (df["item_id"].astype(int) != -2),
        df["units_sold"],
        df["campaign_units_sold"],
    )

    df["discount_pct_final"] = df["discount_pct"].copy()
    mask = df["discount_pct_final"].isna()
    df.loc[mask, "discount_pct_final"] = np.where(
        df.loc[mask, "campaign_segment"].astype(str).eq("item_discount"),
        df.loc[mask, "effective_discount_pct_obs"],
        df.loc[mask, "campaign_effective_discount_pct_obs"],
    )

    df["discount_kind_final"] = df["discount_kind"].astype(str)
    df.loc[(df["discount_kind_final"] == "unknown") & (df["discount_pct_final"].notna()), "discount_kind_final"] = "pct"
    df["discount_kind_final"] = pd.Categorical(
        df["discount_kind_final"],
        categories=["pct", "x_for_y", "buy_x_get_y", "bogo", "unknown"],
    )

    df["effective_price_multiplier_final"] = [
        effective_multiplier_from_parsed(k, p, b, pay, g)
        for k, p, b, pay, g in zip(
            df["discount_kind_final"].astype(str),
            pd.to_numeric(df["discount_pct_final"], errors="coerce").values,
            pd.to_numeric(df["buy_qty"], errors="coerce").values,
            pd.to_numeric(df["pay_qty"], errors="coerce").values,
            pd.to_numeric(df["get_qty"], errors="coerce").values,
        )
    ]
    df["effective_price_multiplier_final"] = (
        pd.to_numeric(df["effective_price_multiplier_final"], errors="coerce").fillna(1.0).clip(0.05, 1.0)
    )
    df["effective_discount_depth_final"] = (1.0 - df["effective_price_multiplier_final"]).clip(0.0, 0.95)

    df["discount_is_pct"] = (df["discount_kind_final"] == "pct").astype(int)
    df["discount_is_multibuy"] = df["discount_kind_final"].isin(["x_for_y", "buy_x_get_y", "bogo"]).astype(int)
    df["discount_is_unknown"] = (df["discount_kind_final"] == "unknown").astype(int)

    start_dt = safe_unix_to_dt(df["start_ts"])
    df["hour_of_day_start"] = start_dt.dt.hour.fillna(-1).astype(int)
    df["day_of_week_start"] = start_dt.dt.dayofweek.fillna(-1).astype(int)
    df["is_weekend_start"] = ((df["day_of_week_start"] >= 5) & (df["day_of_week_start"] <= 6)).astype(int)
    df["month_start"] = start_dt.dt.month.fillna(-1).astype(int)

    df["daypart"] = df["hour_of_day_start"].apply(make_daypart)
    df["daypart"] = pd.Categorical(df["daypart"], categories=["morning", "afternoon", "evening", "night", "unknown"])

    df["order_count"] = 0.0
    df["place_total_order_count"] = 0.0

    if most_ordered is not None:
        mo = most_ordered.copy()
        mo["place_id"] = pd.to_numeric(mo.get("place_id"), errors="coerce")
        mo["item_id"] = pd.to_numeric(mo.get("item_id"), errors="coerce")

        if "order_count" not in mo.columns:
            for alt in ["orders", "count", "order_cnt", "num_orders"]:
                if alt in mo.columns:
                    mo["order_count"] = mo[alt]
                    break
        mo["order_count"] = pd.to_numeric(mo.get("order_count"), errors="coerce").fillna(0.0)

        pop_item = mo.groupby(["place_id", "item_id"], as_index=False).agg(order_count=("order_count", "sum"))
        pop_place = mo.groupby("place_id", as_index=False).agg(place_total_order_count=("order_count", "sum"))

        df = df.merge(pop_item, on=["place_id", "item_id"], how="left", suffixes=("", "_mo"))
        df = df.merge(pop_place, on="place_id", how="left", suffixes=("", "_mo"))

        if "order_count_mo" in df.columns:
            df["order_count"] = df["order_count_mo"]
            df = df.drop(columns=["order_count_mo"])
        if "place_total_order_count_mo" in df.columns:
            df["place_total_order_count"] = df["place_total_order_count_mo"]
            df = df.drop(columns=["place_total_order_count_mo"])

        df["order_count"] = pd.to_numeric(df["order_count"], errors="coerce").fillna(0.0)
        df["place_total_order_count"] = pd.to_numeric(df["place_total_order_count"], errors="coerce").fillna(0.0)

    duration_floor = 0.5
    df["y_units_per_hour"] = df["label_units"] / np.maximum(df["duration_hours"].values, duration_floor)
    df["y_log1p_units_per_hour"] = np.log1p(df["y_units_per_hour"].values)

    feature_cols = [
        "discount_kind_final",
        "discount_pct_final",
        "buy_qty",
        "pay_qty",
        "get_qty",
        "discount_is_pct",
        "discount_is_multibuy",
        "discount_is_unknown",
        "effective_price_multiplier_final",
        "effective_discount_depth_final",
        "duration_hours",
        "duration_hours_capped",
        "has_start_time",
        "has_end_time",
        "has_valid_time",
        "duration_is_valid",
        "hour_of_day_start",
        "day_of_week_start",
        "is_weekend_start",
        "month_start",
        "daypart",
        "num_items_targeted",
        "place_id",
        "item_id",
        "campaign_segment",
        "order_count",
        "place_total_order_count",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]

    for c in ["discount_kind_final", "daypart", "campaign_segment"]:
        if c in df.columns:
            df[c] = df[c].astype("category")

    for c in ["place_id", "item_id"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(-999).astype(int)

    df = df.sort_values("start_ts").reset_index(drop=True)
    place_cats = pd.Index(sorted(df["place_id"].unique().tolist()))
    item_cats = pd.Index(sorted(df["item_id"].unique().tolist()))
    df["place_id"] = pd.Categorical(df["place_id"], categories=place_cats)
    df["item_id"] = pd.Categorical(df["item_id"], categories=item_cats)

    target_col = "y_log1p_units_per_hour"
    time_col = "start_ts"
    df = df.sort_values(time_col).reset_index(drop=True)

    n = len(df)
    train_end = int(n * 0.70)
    valid_end = int(n * 0.85)

    train_df = df.iloc[:train_end].copy()
    valid_df = df.iloc[train_end:valid_end].copy()
    test_df = df.iloc[valid_end:].copy()

    return FeatureEngineeringOutput(
        df=df,
        feature_cols=feature_cols,
        target_col=target_col,
        time_col=time_col,
        train_df=train_df,
        valid_df=valid_df,
        test_df=test_df,
    )


def build_train_matrices(out: FeatureEngineeringOutput):
    """
    Builds train/validation/test matrices from a FeatureEngineeringOutput object.

    Args:
        out (FeatureEngineeringOutput): Feature engineering output containing splits and column names.

    Returns:
        Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
            (X_train, y_train, X_valid, y_valid, X_test, y_test)
    """
    X_train = out.train_df[out.feature_cols].copy()
    y_train = out.train_df[out.target_col].copy()
    X_valid = out.valid_df[out.feature_cols].copy()
    y_valid = out.valid_df[out.target_col].copy()
    X_test = out.test_df[out.feature_cols].copy()
    y_test = out.test_df[out.target_col].copy()
    return X_train, y_train, X_valid, y_valid, X_test, y_test
