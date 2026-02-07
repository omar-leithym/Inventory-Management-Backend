"""
Service layer for demand forecasting.

Encapsulates model loading, prediction, and training logic.
Follows the Singleton pattern to maintain model state across requests.
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

# Import the new modular model
from src.models.demand_forecast import DemandForecastModel

logger = logging.getLogger(__name__)


class DemandService:
    """
    Service for handling demand forecast operations.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DemandService, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.model_path = 'models/demand_forecast_xgboost.pkl'
            cls._instance.data_path = './data/Inventory Management'
        return cls._instance
    
    def load_model(self, model_path: str = None):
        """
        Load the model from disk.
        """
        path = model_path or self.model_path
        
        # Initialize new model instance
        self.model = DemandForecastModel(data_path=self.data_path)
        
        try:
            if os.path.exists(path):
                logger.info(f"Loading model from {path}")
                self.model.load(path)
            else:
                logger.warning(f"Model file {path} not found. Model must be trained.")
                self.model.is_trained = False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def predict(self, item_id: int, place_id: int, date: str, period: str = 'daily') -> Dict[str, Any]:
        """
        Make a demand prediction.
        """
        if self.model is None or not self.model.is_trained:
            # Try to load default model
            self.load_model()
            
            if not self.model.is_trained:
                raise ValueError("Model is not trained. Please train the model first.")
        
        try:
            result = self.model.predict_demand(
                item_id=int(item_id),
                place_id=int(place_id),
                date=date,
                period=period
            )
            return result
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
        
    def train(self, model_type: str = 'xgboost', period: str = 'daily') -> Dict[str, Any]:
        """
        Trigger model training.
        """
        logger.info(f"Starting training for {model_type} model ({period})")
        
        try:
            # Initialize fresh model
            self.model = DemandForecastModel(
                model_type=model_type,
                data_path=self.data_path,
                period=period
            )
            
            # Run pipeline
            metrics = self.model.train_pipeline()
            
            # Save
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
            
            return {
                "status": "success",
                "metrics": metrics,
                "model_path": self.model_path,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

    def get_info(self) -> Dict[str, Any]:
        """
        Get model status information.
        """
        if self.model is None:
            return {"status": "not_loaded"}
            
        return {
            "status": "loaded" if self.model.is_trained else "not_trained",
            "model_type": self.model.model_type,
            "period": self.model.period,
            "is_trained": self.model.is_trained
        }
