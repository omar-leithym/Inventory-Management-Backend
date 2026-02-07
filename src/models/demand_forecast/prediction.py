"""
Prediction logic for demand forecasting.

Handles prediction, period scaling, and ensemble methods.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class DemandPredictor:
    """
    Handles demand predictions with ensemble support and period scaling.
    """
    
    def __init__(self, trainer, feature_engineer):
        """
        Initialize predictor.
        
        Args:
            trainer: Trained ModelTrainer instance
            feature_engineer: FeatureEngineer instance
        """
        self.trainer = trainer
        self.feature_engineer = feature_engineer
        self.period = 'daily'  # Default period
        self.global_stats: Dict = None
    
    def set_period(self, period: str):
        """Set the prediction period."""
        valid_periods = ['daily', 'weekly', 'monthly']
        if period not in valid_periods:
            raise ValueError(f"Period must be one of {valid_periods}")
        self.period = period
    
    def set_global_stats(self, historical_data: pd.DataFrame):
        """
        Calculate global statistics for cold start fallback.
        
        Args:
            historical_data: Historical demand data
        """
        if historical_data is not None and len(historical_data) > 0:
            self.global_stats = {
                'avg_demand': historical_data['demand'].mean(),
                'avg_price': historical_data.get('price', pd.Series([50.0])).mean(),
                'avg_place_demand': historical_data.groupby('place_id')['demand'].sum().mean()
            }
        else:
            self.global_stats = {
                'avg_demand': 5.0,
                'avg_price': 50.0,
                'avg_place_demand': 100.0
            }
        
        logger.info(f"Set global stats: avg_demand={self.global_stats['avg_demand']:.2f}")
    
    def predict(self, X: pd.DataFrame, 
                use_ensemble: bool = True,
                model_name: str = None) -> np.ndarray:
        """
        Predict demand for given features.
        
        Args:
            X: Feature matrix
            use_ensemble: If True, average predictions from all models
            model_name: Specific model to use (overrides ensemble)
            
        Returns:
            Predicted demand values
        """
        if not self.trainer.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Validate features
        missing = set(self.trainer.feature_names) - set(X.columns)
        if missing:
            raise ValueError(f"Missing features: {missing}")
        
        X_selected = X[self.trainer.feature_names].copy()
        
        # Fill missing values
        for col in X_selected.columns:
            if X_selected[col].isna().any():
                X_selected[col] = X_selected[col].fillna(0)
        
        # Scale features
        X_scaled = self.trainer.scaler.transform(X_selected)
        
        # Predict
        if use_ensemble and len(self.trainer.models) > 1:
            predictions_list = []
            for name, model in self.trainer.models.items():
                pred = model.predict(X_scaled)
                predictions_list.append(pred)
            predictions = np.mean(predictions_list, axis=0)
        elif model_name and model_name in self.trainer.models:
            predictions = self.trainer.models[model_name].predict(X_scaled)
        else:
            # Use best available model
            predictions = None
            for name in ['lightgbm', 'xgboost', 'random_forest']:
                if name in self.trainer.models:
                    predictions = self.trainer.models[name].predict(X_scaled)
                    break
            
            if predictions is None:
                raise ValueError("No trained model available for prediction")
        
        # Ensure non-negative predictions
        predictions = np.maximum(predictions, 0)
        
        return predictions
    
    def predict_demand(self, item_id: int, place_id: int, date: str,
                      historical_data: pd.DataFrame = None,
                      period: str = None) -> Dict[str, Union[float, Dict]]:
        """
        Predict demand for a specific item at a place and date.
        
        Args:
            item_id: Item identifier
            place_id: Place identifier
            date: Date string 'YYYY-MM-DD'
            historical_data: Optional historical demand data
            period: Prediction period (defaults to self.period)
            
        Returns:
            Dict with prediction and metadata
        """
        from .validation import DataValidator
        
        period = period or self.period
        pred_date = pd.to_datetime(date)
        
        # Validate inputs
        validator = DataValidator(strict=False)
        validation = validator.validate_prediction_inputs(item_id, place_id, date, period)
        
        if not validation['valid']:
            raise ValueError(f"Validation failed: {validation['errors']}")
        
        # Check for cold start
        is_cold_start = False
        if historical_data is not None:
            history_check = validator.validate_historical_data(
                historical_data, item_id, place_id
            )
            is_cold_start = 'cold start' in str(history_check.get('warnings', []))
        else:
            is_cold_start = True
        
        # Create features
        if is_cold_start:
            logger.warning(f"Cold start for item {item_id} at place {place_id}, using fallback")
            features = self.feature_engineer.get_cold_start_features(
                item_id, place_id, pred_date, self.global_stats
            )
        else:
            features = self._create_prediction_features(
                item_id, place_id, pred_date, historical_data
            )
        
        # Predict
        base_prediction = float(self.predict(features, use_ensemble=True)[0])
        
        # Scale if needed
        if period != self.period:
            scaled_prediction = self._scale_prediction(
                base_prediction, self.period, period, pred_date
            )
        else:
            scaled_prediction = base_prediction
        
        return {
            'item_id': item_id,
            'place_id': place_id,
            'date': date,
            'period': period,
            'predicted_demand': scaled_prediction,
            'is_cold_start': is_cold_start,
            'model_type': self.trainer.model_type,
            'units': f'total {period} demand'
        }
    
    def _create_prediction_features(self, item_id: int, place_id: int,
                                    date: pd.Timestamp, 
                                    historical_data: pd.DataFrame) -> pd.DataFrame:
        """Create features from historical data for prediction."""
        item_data = historical_data[
            (historical_data['item_id'] == item_id) &
            (historical_data['place_id'] == place_id)
        ].copy()
        
        if 'date' in item_data.columns:
            if not pd.api.types.is_datetime64_any_dtype(item_data['date']):
                item_data['date'] = pd.to_datetime(item_data['date'])
            item_data = item_data.sort_values('date')
        
        # Build feature dict
        features = {
            'year': date.year,
            'month': date.month,
            'day_of_month': date.day,
            'day_of_week': date.dayofweek,
            'week_of_year': date.isocalendar().week,
            'is_weekend': 1 if date.dayofweek >= 5 else 0,
            'quarter': date.quarter,
            'month_sin': np.sin(2 * np.pi * date.month / 12),
            'month_cos': np.cos(2 * np.pi * date.month / 12),
            'day_of_week_sin': np.sin(2 * np.pi * date.dayofweek / 7),
            'day_of_week_cos': np.cos(2 * np.pi * date.dayofweek / 7),
        }
        
        # Add lag features from historical data
        if len(item_data) > 0:
            demands = item_data['demand'].values
            for i, lag in enumerate(self.feature_engineer.LAG_PERIODS):
                if len(demands) >= lag:
                    features[f'demand_lag_{lag}'] = demands[-lag]
                else:
                    features[f'demand_lag_{lag}'] = demands[-1] if len(demands) > 0 else 0
            
            # Rolling stats
            for window in self.feature_engineer.ROLLING_WINDOWS:
                window_data = demands[-window:] if len(demands) >= window else demands
                features[f'demand_rolling_mean_{window}'] = np.mean(window_data)
                features[f'demand_rolling_std_{window}'] = np.std(window_data)
        
        # Fill any missing features with defaults
        for feature_name in self.trainer.feature_names:
            if feature_name not in features:
                features[feature_name] = 0
        
        return pd.DataFrame([features])
    
    def _scale_prediction(self, prediction: float, from_period: str,
                         to_period: str, date: pd.Timestamp) -> float:
        """Scale prediction between periods."""
        if from_period == to_period:
            return prediction
        
        # Days in month
        days_in_month = (date.replace(day=28) + pd.Timedelta(days=4)).replace(day=1) - pd.Timedelta(days=1)
        days_in_month = float(days_in_month.day)
        
        conversions = {
            ('daily', 'weekly'): 7.0,
            ('daily', 'monthly'): days_in_month,
            ('weekly', 'daily'): 1.0 / 7.0,
            ('weekly', 'monthly'): days_in_month / 7.0,
            ('monthly', 'daily'): 1.0 / days_in_month,
            ('monthly', 'weekly'): 7.0 / days_in_month,
        }
        
        scale = conversions.get((from_period, to_period), 1.0)
        return prediction * scale
