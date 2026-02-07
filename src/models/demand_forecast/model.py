"""
Main DemandForecastModel orchestrator.

Provides a unified interface to the modular demand forecasting system.
This is a slim wrapper that delegates to specialized modules.
"""

import pandas as pd
import numpy as np
import pickle
import logging
from typing import Dict, Tuple, Optional

from .feature_engineering import FeatureEngineer
from .training import ModelTrainer
from .prediction import DemandPredictor
from .validation import DataValidator

logger = logging.getLogger(__name__)


class DemandForecastModel:
    """
    Unified demand forecasting model interface.
    
    Orchestrates feature engineering, training, validation, and prediction
    using specialized submodules for clean separation of concerns.
    
    Usage:
        model = DemandForecastModel(data_path="data/", period="daily")
        metrics = model.train_pipeline()
        prediction = model.predict_demand(item_id=123, place_id=1, date="2024-01-15")
    """
    
    def __init__(self, model_type: str = 'xgboost', 
                 data_path: str = None, 
                 period: str = 'daily'):
        """
        Initialize the demand forecast model.
        
        Args:
            model_type: Model type ('xgboost', 'lightgbm', 'random_forest', 'ensemble')
            data_path: Path to data directory
            period: Prediction period ('daily', 'weekly', 'monthly')
        """
        self.model_type = model_type
        self.data_path = data_path
        self.period = period
        
        # Initialize submodules
        self.feature_engineer = FeatureEngineer()
        self.trainer = ModelTrainer(model_type=model_type)
        self.predictor = DemandPredictor(self.trainer, self.feature_engineer)
        self.validator = DataValidator(strict=False)
        
        # State
        self.is_trained = False
        self._cached_data: Dict = {}
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load core datasets from data_path.
        
        Returns:
            Tuple of (orders, order_items, items, menu_items) DataFrames
        """
        if not self.data_path:
            raise ValueError("data_path must be set to load data")
        
        logger.info(f"Loading data from {self.data_path}")
        
        orders = pd.read_csv(f"{self.data_path}/fct_orders.csv")
        order_items = pd.read_csv(f"{self.data_path}/fct_order_items.csv")
        items = pd.read_csv(f"{self.data_path}/dim_items.csv")
        menu_items = pd.read_csv(f"{self.data_path}/dim_menu_items.csv")
        
        # Convert timestamps
        orders['created'] = pd.to_datetime(orders['created'], unit='s', errors='coerce')
        order_items['created'] = pd.to_datetime(order_items['created'], unit='s', errors='coerce')
        
        # Validate
        self.validator.validate_orders(orders)
        self.validator.validate_order_items(order_items)
        
        logger.info(f"Loaded {len(orders)} orders, {len(order_items)} order items")
        
        return orders, order_items, items, menu_items
    
    def train_pipeline(self, orders: pd.DataFrame = None,
                      order_items: pd.DataFrame = None,
                      items: pd.DataFrame = None,
                      menu_items: pd.DataFrame = None) -> Dict[str, Dict]:
        """
        Run full training pipeline.
        
        Args:
            orders: Orders DataFrame (loads from data_path if None)
            order_items: Order items DataFrame
            items: Items dimension table
            menu_items: Menu items dimension table
            
        Returns:
            Training metrics dict
        """
        # Load data if not provided
        if orders is None:
            orders, order_items, items, menu_items = self.load_data()
        
        # Create demand dataset
        logger.info(f"Creating {self.period} demand dataset")
        demand_df = self.feature_engineer.create_demand_dataset(
            orders, order_items, self.period
        )
        
        # Validate demand dataset
        self.validator.validate_demand_dataset(demand_df)
        
        # Engineer features
        logger.info("Engineering features")
        feature_df = self.feature_engineer.engineer_features(
            demand_df, items, menu_items
        )
        
        # Prepare for training
        X, y, feature_names = self.trainer.prepare_features(feature_df)
        
        # Train
        logger.info("Training models")
        metrics = self.trainer.train(X, y)
        
        # Set global stats for cold start
        self.predictor.set_global_stats(demand_df)
        self.predictor.set_period(self.period)
        
        # Cache data for predictions
        self._cached_data['demand'] = demand_df
        
        self.is_trained = True
        
        logger.info("Training complete")
        return metrics
    
    def predict_demand(self, item_id: int, place_id: int, date: str,
                      historical_data: pd.DataFrame = None,
                      period: str = None) -> Dict:
        """
        Predict demand for a specific item/place/date.
        
        Args:
            item_id: Item identifier
            place_id: Place identifier
            date: Date string 'YYYY-MM-DD'
            historical_data: Optional historical data (uses cached if None)
            period: Prediction period (uses model period if None)
            
        Returns:
            Prediction result dict
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        if historical_data is None:
            historical_data = self._cached_data.get('demand')
        
        return self.predictor.predict_demand(
            item_id, place_id, date, historical_data, period or self.period
        )
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from trained model."""
        return self.trainer.get_feature_importance()
    
    def save(self, filepath: str):
        """Save model to disk."""
        model_data = {
            'trainer': {
                'models': self.trainer.models,
                'scaler': self.trainer.scaler,
                'label_encoders': self.trainer.label_encoders,
                'feature_names': self.trainer.feature_names,
                'model_type': self.trainer.model_type,
                'is_trained': self.trainer.is_trained
            },
            'model_type': self.model_type,
            'period': self.period,
            'global_stats': self.predictor.global_stats,
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model from disk."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        # Restore trainer state
        self.trainer.models = model_data['trainer']['models']
        self.trainer.scaler = model_data['trainer']['scaler']
        self.trainer.label_encoders = model_data['trainer']['label_encoders']
        self.trainer.feature_names = model_data['trainer']['feature_names']
        self.trainer.model_type = model_data['trainer']['model_type']
        self.trainer.is_trained = model_data['trainer']['is_trained']
        
        # Restore model state
        self.model_type = model_data['model_type']
        self.period = model_data['period']
        self.predictor.global_stats = model_data['global_stats']
        self.predictor.set_period(self.period)
        self.is_trained = model_data['is_trained']
        
        logger.info(f"Model loaded from {filepath} (period: {self.period})")
