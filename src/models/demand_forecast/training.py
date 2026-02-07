"""
Model training for demand forecasting.

Handles model training, cross-validation, and hyperparameter optimization.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Optional imports
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False


class ModelTrainer:
    """
    Trains demand forecasting models.
    
    Supports XGBoost, LightGBM, Random Forest, and ensemble approaches.
    """
    
    # Default hyperparameters (can be overridden)
    DEFAULT_PARAMS = {
        'xgboost': {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1
        },
        'lightgbm': {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1,
            'verbose': -1
        },
        'random_forest': {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42,
            'n_jobs': -1
        }
    }
    
    def __init__(self, model_type: str = 'ensemble', 
                 custom_params: Dict = None):
        """
        Initialize trainer.
        
        Args:
            model_type: Type of model ('xgboost', 'lightgbm', 'random_forest', 'ensemble')
            custom_params: Custom hyperparameters to override defaults
        """
        self.model_type = model_type
        self.custom_params = custom_params or {}
        self.models: Dict = {}
        self.scaler = StandardScaler()
        self.label_encoders: Dict = {}
        self.feature_names: List[str] = []
        self.is_trained = False
        self.training_metrics: Dict = {}
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """
        Prepare features and target for training.
        
        Args:
            df: Dataset with engineered features
            
        Returns:
            Tuple of (features DataFrame, target Series, feature names list)
        """
        exclude_cols = ['date', 'item_id', 'place_id', 'target', 'demand', 'item_place_interaction']
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Get numeric and categorical columns
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df[feature_cols].select_dtypes(include=['object']).columns.tolist()
        
        # Encode categorical variables
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col].astype(str).fillna('unknown'))
            else:
                df[col] = self.label_encoders[col].transform(df[col].astype(str).fillna('unknown'))
        
        all_features = sorted(numeric_cols + categorical_cols)
        
        X = df[all_features].copy()
        for col in X.columns:
            if X[col].isna().any():
                median_val = X[col].median() if X[col].notna().any() else 0
                X[col] = X[col].fillna(median_val)
        
        y = df['target']
        
        self.feature_names = all_features
        
        logger.info(f"Prepared {len(all_features)} features for training")
        
        return X, y, all_features
    
    def train(self, X: pd.DataFrame, y: pd.Series, 
              validation_split: float = 0.2,
              use_time_series_split: bool = True) -> Dict[str, Dict]:
        """
        Train demand forecasting models.
        
        Args:
            X: Feature matrix
            y: Target variable
            validation_split: Fraction for validation
            use_time_series_split: Use proper time series CV (recommended)
            
        Returns:
            Dict of training metrics per model
        """
        logger.info(f"Training {self.model_type} model(s) on {len(X)} samples")
        
        # Split data
        if use_time_series_split:
            n_splits = max(2, int(1 / validation_split))
            tscv = TimeSeriesSplit(n_splits=n_splits)
            splits = list(tscv.split(X))
            train_idx, val_idx = splits[-1]
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        else:
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        metrics = {}
        
        # Train models based on type
        if self.model_type in ['xgboost', 'ensemble'] and XGBOOST_AVAILABLE:
            params = {**self.DEFAULT_PARAMS['xgboost'], **self.custom_params.get('xgboost', {})}
            xgb_model = xgb.XGBRegressor(**params)
            xgb_model.fit(X_train_scaled, y_train)
            self.models['xgboost'] = xgb_model
            
            y_pred = xgb_model.predict(X_val_scaled)
            metrics['xgboost'] = self._calculate_metrics(y_val, y_pred)
            logger.info(f"XGBoost - MAE: {metrics['xgboost']['mae']:.2f}, RMSE: {metrics['xgboost']['rmse']:.2f}")
        
        if self.model_type in ['lightgbm', 'ensemble'] and LIGHTGBM_AVAILABLE:
            params = {**self.DEFAULT_PARAMS['lightgbm'], **self.custom_params.get('lightgbm', {})}
            lgb_model = lgb.LGBMRegressor(**params)
            lgb_model.fit(X_train_scaled, y_train)
            self.models['lightgbm'] = lgb_model
            
            y_pred = lgb_model.predict(X_val_scaled)
            metrics['lightgbm'] = self._calculate_metrics(y_val, y_pred)
            logger.info(f"LightGBM - MAE: {metrics['lightgbm']['mae']:.2f}, RMSE: {metrics['lightgbm']['rmse']:.2f}")
        
        # Always train Random Forest as baseline
        params = {**self.DEFAULT_PARAMS['random_forest'], **self.custom_params.get('random_forest', {})}
        rf_model = RandomForestRegressor(**params)
        rf_model.fit(X_train_scaled, y_train)
        self.models['random_forest'] = rf_model
        
        y_pred = rf_model.predict(X_val_scaled)
        metrics['random_forest'] = self._calculate_metrics(y_val, y_pred)
        logger.info(f"Random Forest - MAE: {metrics['random_forest']['mae']:.2f}, RMSE: {metrics['random_forest']['rmse']:.2f}")
        
        self.is_trained = True
        self.training_metrics = metrics
        
        return metrics
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate evaluation metrics."""
        return {
            'mae': mean_absolute_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mape': mean_absolute_percentage_error(y_true, y_pred) * 100,
            'r2': r2_score(y_true, y_pred)
        }
    
    def get_feature_importance(self, model_name: str = None) -> pd.DataFrame:
        """
        Get feature importance from trained model.
        
        Args:
            model_name: Specific model to use, or None for best model
            
        Returns:
            DataFrame with feature names and importance scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")
        
        if model_name is None:
            # Use best model based on MAE
            best_model = min(self.training_metrics.items(), 
                           key=lambda x: x[1]['mae'])[0]
            model_name = best_model
        
        model = self.models.get(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not found")
        
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        else:
            raise ValueError(f"Model {model_name} does not support feature importance")
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def select_top_features(self, n_features: int = 30) -> List[str]:
        """
        Select top N most important features.
        
        Args:
            n_features: Number of features to keep
            
        Returns:
            List of top feature names
        """
        importance_df = self.get_feature_importance()
        top_features = importance_df.head(n_features)['feature'].tolist()
        
        logger.info(f"Selected top {n_features} features")
        
        return top_features
