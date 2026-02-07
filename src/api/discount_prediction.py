"""
File: discount_flask_api.py
Description: Flask API for serving the discount recommendation model via HTTP endpoints.
Dependencies: os, time, threading, typing, pandas, flask, pathlib
Author: DIH Hackathon Team

This module exposes two routes:
- GET /health: Readiness probe that reports whether model artifacts are loaded.
- POST /discount: Inference endpoint that evaluates discount candidates and returns a recommendation.

The API lazily loads LightGBM artifacts from disk and caches them in memory. Category alignment
is applied at inference time to prevent categorical mismatch issues with the trained model.
"""

import os
import time
import threading
from typing import Any, Dict, Optional

import pandas as pd
from flask import Flask, jsonify, request

from src.services.model_io import load_artifacts  # loads .txt + .meta.json and returns align()
from src.services.decision import recommend_discount_item  # main inference/decision logic

from pathlib import Path



DEFAULT_PCT_GRID = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]


def create_app() -> Flask:
    """
    Creates and configures the Flask application.

    The app loads model artifacts from a configured prefix path and caches the loaded
    model and metadata in memory. The artifact path can be overridden via the
    DISCOUNT_ARTIFACT_PREFIX environment variable.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    DEFAULT_PREFIX = (Path(__file__).resolve().parents[1] / "services" / "artifacts" / "discount_lgbm")
    artifact_prefix = os.getenv("DISCOUNT_ARTIFACT_PREFIX", str(DEFAULT_PREFIX))

    state: Dict[str, Any] = {
        "artifact_prefix": artifact_prefix,
        "model": None,
        "feature_cols": None,
        "X_ref_for_categories": None,
        "loaded_at_unix": None,
        "load_error": None,
    }
    lock = threading.Lock()

    def artifacts_exist(prefix: str) -> bool:
        """
        Checks whether both model and metadata files exist for a given artifact prefix.

        Args:
            prefix (str): Artifact prefix without file extensions.

        Returns:
            bool: True if <prefix>.txt and <prefix>.meta.json exist, otherwise False.
        """
        return os.path.exists(f"{prefix}.txt") and os.path.exists(f"{prefix}.meta.json")

    def load_model_if_needed(force: bool = False) -> None:
        """
        Loads model artifacts into memory if not already loaded or if forced.

        This function populates the shared state dict with:
        - model: LightGBM Booster
        - feature_cols: model feature column names
        - X_ref_for_categories: reference DataFrame used for categorical alignment
        - loaded_at_unix: unix timestamp of successful load
        - load_error: error details if loading fails

        Args:
            force (bool): If True, reload artifacts even if already loaded.

        Returns:
            None
        """
        with lock:
            if state["model"] is not None and not force:
                return

            prefix = state["artifact_prefix"]
            if not artifacts_exist(prefix):
                state["model"] = None
                state["feature_cols"] = None
                state["X_ref_for_categories"] = None
                state["loaded_at_unix"] = None
                state["load_error"] = (
                    f"Missing artifacts for prefix '{prefix}'. Expected:\n"
                    f"- {prefix}.txt\n"
                    f"- {prefix}.meta.json\n"
                    "Train + save artifacts first."
                )
                return

            try:
                model, feature_cols, _, align = load_artifacts(prefix)

                X_ref_for_categories = align(
                    pd.DataFrame({c: pd.Series([], dtype="object") for c in feature_cols})
                )

                state["model"] = model
                state["feature_cols"] = feature_cols
                state["X_ref_for_categories"] = X_ref_for_categories
                state["loaded_at_unix"] = int(time.time())
                state["load_error"] = None
            except Exception as e:
                state["model"] = None
                state["feature_cols"] = None
                state["X_ref_for_categories"] = None
                state["loaded_at_unix"] = None
                state["load_error"] = f"{type(e).__name__}: {e}"

    @app.get("/health")
    def health():
        """
        Health/readiness endpoint.

        This endpoint attempts a lazy load of model artifacts and reports readiness based
        on whether the model is available in memory.

        Returns:
            Response: JSON payload describing model readiness and artifact configuration.
        """
        load_model_if_needed(force=False)

        ok = state["model"] is not None
        return jsonify(
            {
                "status": "ok" if ok else "degraded",
                "model_loaded": ok,
                "artifact_prefix": state["artifact_prefix"],
                "loaded_at_unix": state["loaded_at_unix"],
                "error": state["load_error"],
            }
        ), (200 if ok else 503)

    @app.post("/discount")
    def discount():
        """
        Discount recommendation endpoint.

        Accepts a JSON payload describing inventory, expected demand, and optional tuning
        parameters. The endpoint evaluates candidate discount percentages and returns
        a recommended discount with supporting metrics.

        Required JSON fields:
            - amount_left
            - expected_demand_for_remaining
            - item_id

        Optional JSON fields:
            - place_id (defaults to 59897)
            - num_items_targeted (defaults to 1)
            - now_ts_unix (defaults to server current time)
            - window_end_ts_unix (if absent, computed from now_ts_unix + window_hours)
            - window_hours (defaults to 3.0 when window_end_ts_unix is absent)
            - pct_grid (defaults to DEFAULT_PCT_GRID)
            - baseline_pct (defaults to 0.0)
            - aggressiveness (defaults to 5.0)
            - return_debug (defaults to False)
            - debug_limit (defaults to 200)
            - reload (defaults to False)

        Returns:
            Response: JSON payload containing the recommendation result and optional debug details.
        """
        load_model_if_needed(force=False)
        if state["model"] is None:
            return jsonify(
                {
                    "error": "Model artifacts not loaded.",
                    "details": state["load_error"],
                    "hint": f"Make sure {state['artifact_prefix']}.txt and {state['artifact_prefix']}.meta.json exist.",
                }
            ), 503

        payload = request.get_json(silent=True) or {}

        if bool(payload.get("reload", False)):
            load_model_if_needed(force=True)
            if state["model"] is None:
                return jsonify({"error": "Reload failed.", "details": state["load_error"]}), 503

        missing = [k for k in ["amount_left", "expected_demand_for_remaining", "item_id"] if k not in payload]
        if missing:
            return jsonify({"error": "Missing required fields.", "missing": missing}), 400

        try:
            amount_left = float(payload["amount_left"])
            expected_demand_for_remaining = float(payload["expected_demand_for_remaining"])
            place_id = int(payload.get("place_id", 59897))
            item_id = int(payload["item_id"])
        except Exception as e:
            return jsonify({"error": "Bad types for required fields.", "details": f"{type(e).__name__}: {e}"}), 400

        num_items_targeted = int(payload.get("num_items_targeted", 1))

        now_ts_unix = payload.get("now_ts_unix", None)
        if now_ts_unix is None:
            now_ts_unix = int(time.time())
        else:
            now_ts_unix = int(now_ts_unix)

        window_end_ts_unix = payload.get("window_end_ts_unix", None)
        if window_end_ts_unix is None:
            window_hours = float(payload.get("window_hours", 3.0))
            window_end_ts_unix = int(now_ts_unix + window_hours * 3600.0)
        else:
            window_end_ts_unix = int(window_end_ts_unix)

        pct_grid = payload.get("pct_grid", DEFAULT_PCT_GRID)
        if not isinstance(pct_grid, list) or len(pct_grid) == 0:
            return jsonify({"error": "pct_grid must be a non-empty list of floats."}), 400
        pct_grid = [float(x) for x in pct_grid]

        baseline_pct = float(payload.get("baseline_pct", 0.0))
        aggressiveness = float(payload.get("aggressiveness", 5.0))
        return_debug = bool(payload.get("return_debug", False))
        debug_limit = int(payload.get("debug_limit", 200))

        try:
            out = recommend_discount_item(
                model=state["model"],
                feature_cols=state["feature_cols"],
                X_ref_for_categories=state["X_ref_for_categories"],
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
            if return_debug:
                result, dbg_df = out
                dbg_records = dbg_df.head(max(debug_limit, 0)).to_dict(orient="records")
                return jsonify({"result": result, "debug": dbg_records}), 200

            return jsonify({"result": out}), 200

        except Exception as e:
            return jsonify({"error": "Inference failed.", "details": f"{type(e).__name__}: {e}"}), 500

    load_model_if_needed(force=False)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)