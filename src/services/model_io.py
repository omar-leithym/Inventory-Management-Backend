"""
File: model_io.py
Description: Model artifact save/load utilities for LightGBM models and inference-time category alignment.
Dependencies: dataclasses, typing, json, lightgbm, pandas
Author: SOFIDA Team

Notes:
- Artifacts are saved as a LightGBM model file (<prefix>.txt) and a metadata JSON (<prefix>.meta.json).
- Metadata includes feature columns, categorical feature names, and the category sets needed to align inference data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
import json
import lightgbm as lgb
import pandas as pd


@dataclass
class SavedArtifacts:
    """
    Container for saved artifact file paths.

    Attributes:
        model_path (str): Path to the saved LightGBM model file.
        meta_path (str): Path to the saved metadata JSON file.
    """

    model_path: str
    meta_path: str


def _serialize_categories(X_ref: pd.DataFrame) -> Dict[str, Any]:
    """
    Serializes pandas categorical column categories for storage in JSON.

    This function extracts category lists for each categorical column in the
    reference feature matrix. These stored categories are used later to align
    inference data and prevent LightGBM category mismatch errors.

    Args:
        X_ref (pd.DataFrame): Reference feature matrix containing categorical dtypes.

    Returns:
        Dict[str, Any]: Mapping of column name to a JSON-serializable list of categories.
    """
    cats = {}
    for c in X_ref.columns:
        if pd.api.types.is_categorical_dtype(X_ref[c]):
            cats[c] = [None if pd.isna(v) else v for v in X_ref[c].cat.categories.tolist()]
    return cats


def _apply_categories(X: pd.DataFrame, cats: Dict[str, Any]) -> pd.DataFrame:
    """
    Applies stored category sets to an input DataFrame.

    Args:
        X (pd.DataFrame): Input feature matrix to align.
        cats (Dict[str, Any]): Mapping of column name to category list.

    Returns:
        pd.DataFrame: A copy of X with categorical columns aligned to the stored categories.
    """
    Xo = X.copy()
    for c, cat_list in cats.items():
        if c in Xo.columns:
            Xo[c] = pd.Categorical(Xo[c], categories=cat_list)
    return Xo


def save_artifacts(
    model: lgb.Booster,
    feature_cols: List[str],
    categorical_features: List[str],
    X_ref_for_categories: pd.DataFrame,
    out_prefix: str = "artifacts/discount_lgbm",
) -> SavedArtifacts:
    """
    Saves a trained LightGBM model and its associated metadata to disk.

    The model is stored in LightGBM native format and metadata is stored as JSON.
    The metadata includes feature columns, categorical feature names, and category
    sets needed to align inference data.

    Args:
        model (lgb.Booster): Trained LightGBM model to save.
        feature_cols (List[str]): Feature column names expected by the model.
        categorical_features (List[str]): Names of categorical feature columns.
        X_ref_for_categories (pd.DataFrame): Reference feature matrix used to capture category sets.
        out_prefix (str): Output path prefix for artifacts (extensions are added automatically).

    Returns:
        SavedArtifacts: Paths to the saved model file and metadata JSON.
    """
    model_path = f"{out_prefix}.txt"
    meta_path  = f"{out_prefix}.meta.json"

    model.save_model(model_path)

    meta = {
        "feature_cols": feature_cols,
        "categorical_features": categorical_features,
        "categories": _serialize_categories(X_ref_for_categories),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f)

    return SavedArtifacts(model_path=model_path, meta_path=meta_path)


def load_artifacts(
    in_prefix: str = "artifacts/discount_lgbm",
):
    """
    Loads a LightGBM model and metadata from disk.

    This function also returns an alignment helper that applies stored categories
    to inference feature matrices.

    Args:
        in_prefix (str): Input path prefix for artifacts (extensions are added automatically).

    Returns:
        Tuple[lgb.Booster, List[str], List[str], Callable[[pd.DataFrame], pd.DataFrame]]:
            - model: Loaded LightGBM Booster.
            - feature_cols: Feature column names expected by the model.
            - categorical_features: Names of categorical feature columns.
            - align: Function that applies stored categories to an input DataFrame.
    """
    model_path = f"{in_prefix}.txt"
    meta_path  = f"{in_prefix}.meta.json"

    model = lgb.Booster(model_file=model_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    feature_cols = meta["feature_cols"]
    categorical_features = meta.get("categorical_features", [])
    categories = meta.get("categories", {})

    def align(X: pd.DataFrame) -> pd.DataFrame:
        return _apply_categories(X, categories)

    return model, feature_cols, categorical_features, align
