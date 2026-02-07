"""
File: demand_forecast_model.py
Description: ML model for predicting demand (daily, weekly, monthly) for inventory items.
Dependencies: pandas, numpy, scikit-learn, xgboost, lightgbm
Author: ML Team

This module implements a comprehensive demand forecasting system using multiple ML models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
import pickle
import os
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

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


class DemandForecastModel:
    """
    Advanced demand forecasting model using ensemble of ML algorithms.
    
    Supports daily, weekly, and monthly demand predictions with feature engineering
    including temporal patterns, item characteristics, and historical trends.
    
    Attributes:
        models (Dict): Dictionary of trained models
        scaler (StandardScaler): Feature scaler
        label_encoders (Dict): Label encoders for categorical features
        feature_names (List[str]): List of feature names
        model_type (str): Type of model ('xgboost', 'lightgbm', 'random_forest', 'ensemble')
    """
    
    def __init__(self, model_type: str = 'ensemble', data_path: str = None, period: str = 'daily'):
        """
        Initialize the DemandForecastModel.
        
        Args:
            model_type (str): Type of model to use ('xgboost', 'lightgbm', 'random_forest', 'ensemble')
            data_path (str): Path to data directory
            period (str): Period this model is trained for ('daily', 'weekly', 'monthly')
        """
        self.model_type = model_type
        self.data_path = data_path
        self.period = period  # Store the period this model was trained for
        self.models = {}
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.is_trained = False
        self.period_models = {}  # Store models for different periods
        
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load and prepare the core datasets for demand forecasting.
        
        Returns:
            Tuple of DataFrames: (orders, order_items, items, menu_items)
        """
        if not self.data_path:
            raise ValueError("data_path must be set to load data")
        
        # Load fact tables
        orders = pd.read_csv(f"{self.data_path}/fct_orders.csv")
        order_items = pd.read_csv(f"{self.data_path}/fct_order_items.csv")
        
        # Load dimension tables
        items = pd.read_csv(f"{self.data_path}/dim_items.csv")
        menu_items = pd.read_csv(f"{self.data_path}/dim_menu_items.csv")
        
        # Convert UNIX timestamps to datetime
        orders['created'] = pd.to_datetime(orders['created'], unit='s', errors='coerce')
        order_items['created'] = pd.to_datetime(order_items['created'], unit='s', errors='coerce')
        
        print(f"Loaded {len(orders)} orders and {len(order_items)} order items")
        
        return orders, order_items, items, menu_items
    
    def create_demand_dataset(self, orders: pd.DataFrame, order_items: pd.DataFrame, 
                             period: str = 'daily') -> pd.DataFrame:
        """
        Create aggregated demand dataset from orders and order items.
        
        Args:
            orders (pd.DataFrame): Orders dataframe
            order_items (pd.DataFrame): Order items dataframe
            period (str): Aggregation period ('daily', 'weekly', 'monthly')
        
        Returns:
            pd.DataFrame: Aggregated demand dataset with columns: date, item_id, quantity, place_id
        """
        # Merge order items with orders to get timestamps and place info
        # Select only needed columns from orders
        orders_subset = orders[['id', 'created', 'place_id', 'type', 'channel', 'status']].copy()
        
        merged = order_items.merge(
            orders_subset,
            left_on='order_id',
            right_on='id',
            how='inner',
            suffixes=('', '_order')
        )
        
        # Filter only completed orders (if status column exists)
        if 'status' in merged.columns:
            # Try different status values that might indicate completed orders
            if merged['status'].dtype == 'object':
                # Filter for closed/completed orders
                completed_statuses = ['Closed', 'closed', 'Completed', 'completed', 'Paid', 'paid']
                merged = merged[merged['status'].isin(completed_statuses)]
            else:
                # If status is numeric, might need different logic
                # For now, keep all orders if status format is unexpected
                pass
        
        # Set date column based on period
        merged['date'] = merged['created'].dt.date
        
        if period == 'weekly':
            merged['date'] = pd.to_datetime(merged['date']) - pd.to_timedelta(
                merged['created'].dt.dayofweek, unit='d'
            )
            merged['date'] = merged['date'].dt.date
        elif period == 'monthly':
            merged['date'] = pd.to_datetime(merged['date']).dt.to_period('M').dt.to_timestamp().dt.date
        
        # Aggregate demand by date, item_id, and place_id
        # Calculate total amount if not present
        if 'total_amount' not in merged.columns:
            merged['total_amount'] = merged['quantity'] * merged['price']
        
        demand = merged.groupby(['date', 'item_id', 'place_id']).agg({
            'quantity': 'sum',
            'price': 'mean',
            'total_amount': 'sum'
        }).reset_index()
        
        # Rename for clarity
        demand.rename(columns={'quantity': 'demand'}, inplace=True)
        
        print(f"Created {period} demand dataset: {len(demand)} records")
        
        return demand
    
    def engineer_features(self, demand_df: pd.DataFrame, orders: pd.DataFrame, 
                         order_items: pd.DataFrame, items: pd.DataFrame = None,
                         menu_items: pd.DataFrame = None) -> pd.DataFrame:
        """
        Engineer comprehensive features for demand forecasting.
        
        Args:
            demand_df (pd.DataFrame): Base demand dataset
            orders (pd.DataFrame): Orders dataframe
            order_items (pd.DataFrame): Order items dataframe
            items (pd.DataFrame): Items dimension table
            menu_items (pd.DataFrame): Menu items dimension table
        
        Returns:
            pd.DataFrame: Dataset with engineered features
        """
        df = demand_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # ========== TEMPORAL FEATURES ==========
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_month'] = df['date'].dt.day
        df['day_of_week'] = df['date'].dt.dayofweek
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_month_start'] = (df['day_of_month'] <= 3).astype(int)
        df['is_month_end'] = (df['day_of_month'] >= 28).astype(int)
        df['is_quarter_start'] = df['date'].dt.is_quarter_start.astype(int)
        df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)
        
        # Quarter and season
        df['quarter'] = df['date'].dt.quarter
        df['season'] = df['month'].apply(lambda x: 
            'Spring' if x in [3,4,5] else 
            'Summer' if x in [6,7,8] else 
            'Fall' if x in [9,10,11] else 'Winter'
        )
        
        # Cyclical encoding for temporal features (better for ML)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_month_sin'] = np.sin(2 * np.pi * df['day_of_month'] / 31)
        df['day_of_month_cos'] = np.cos(2 * np.pi * df['day_of_month'] / 31)
        df['week_of_year_sin'] = np.sin(2 * np.pi * df['week_of_year'] / 52)
        df['week_of_year_cos'] = np.cos(2 * np.pi * df['week_of_year'] / 52)
        
        # ========== HISTORICAL DEMAND FEATURES ==========
        # Sort by date and item/place
        df = df.sort_values(['item_id', 'place_id', 'date'])
        
        # Extended lag features (previous periods)
        for lag in [1, 2, 3, 7, 14, 21, 30, 60]:
            df[f'demand_lag_{lag}'] = df.groupby(['item_id', 'place_id'])['demand'].shift(lag)
        
        # Extended rolling statistics
        for window in [3, 7, 14, 21, 30, 60, 90]:
            df[f'demand_rolling_mean_{window}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )
            df[f'demand_rolling_std_{window}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.rolling(window=window, min_periods=1).std().fillna(0)
            )
            df[f'demand_rolling_min_{window}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.rolling(window=window, min_periods=1).min()
            )
            df[f'demand_rolling_max_{window}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.rolling(window=window, min_periods=1).max()
            )
        
        # Exponential moving average with more alphas
        for alpha in [0.1, 0.3, 0.5, 0.7, 0.9]:
            df[f'demand_ema_{alpha}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.ewm(alpha=alpha, adjust=False).mean()
            )
        
        # Trend features (multiple windows)
        for window in [7, 14, 30]:
            df[f'demand_trend_{window}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.rolling(window, min_periods=2).apply(
                    lambda y: np.polyfit(range(len(y)), y, 1)[0] if len(y) > 1 else 0
                )
            )
        
        # Seasonal patterns (same day of week, same day of month)
        df['demand_same_dow'] = df.groupby(['item_id', 'place_id', 'day_of_week'])['demand'].shift(1)
        df['demand_same_dom'] = df.groupby(['item_id', 'place_id', 'day_of_month'])['demand'].shift(1)
        
        # Growth rate (percentage change)
        df['demand_growth_7d'] = df.groupby(['item_id', 'place_id'])['demand'].pct_change(periods=7)
        df['demand_growth_30d'] = df.groupby(['item_id', 'place_id'])['demand'].pct_change(periods=30)
        
        # Volatility (coefficient of variation)
        df['demand_cv_7'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
            lambda x: (x.rolling(7, min_periods=2).std() / x.rolling(7, min_periods=2).mean()).fillna(0)
        )
        df['demand_cv_30'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
            lambda x: (x.rolling(30, min_periods=2).std() / x.rolling(30, min_periods=2).mean()).fillna(0)
        )
        
        # ========== ITEM FEATURES ==========
        if items is not None and 'item_id' in items.columns:
            item_features = items.set_index('id')[['title', 'price', 'status']].to_dict('index')
            # Add item features if available
            pass  # Can be expanded based on items schema
        
        if menu_items is not None and 'id' in menu_items.columns:
            # Merge menu item info
            menu_features = menu_items.set_index('id')
            if 'price' in menu_features.columns:
                df = df.merge(
                    menu_features[['price', 'status', 'purchases']].reset_index(),
                    left_on='item_id',
                    right_on='id',
                    how='left',
                    suffixes=('', '_menu')
                )
        
        # ========== PLACE/LOCATION FEATURES ==========
        # Aggregate place-level statistics
        place_stats = df.groupby(['place_id', 'date']).agg({
            'demand': 'sum',
            'item_id': 'nunique'
        }).reset_index()
        place_stats.columns = ['place_id', 'date', 'place_total_demand', 'place_unique_items']
        
        df = df.merge(place_stats, on=['place_id', 'date'], how='left')
        
        # Place-level lag features and rolling stats
        df['place_demand_lag_1'] = df.groupby('place_id')['place_total_demand'].shift(1)
        df['place_demand_lag_7'] = df.groupby('place_id')['place_total_demand'].shift(7)
        df['place_demand_rolling_mean_7'] = df.groupby('place_id')['place_total_demand'].transform(
            lambda x: x.rolling(7, min_periods=1).mean()
        )
        df['place_demand_rolling_mean_30'] = df.groupby('place_id')['place_total_demand'].transform(
            lambda x: x.rolling(30, min_periods=1).mean()
        )
        
        # Item's share of place demand
        df['item_share_of_place'] = df['demand'] / (df['place_total_demand'] + 1e-6)  # Avoid division by zero
        
        # ========== INTERACTION FEATURES ==========
        df['item_place_interaction'] = df['item_id'].astype(str) + '_' + df['place_id'].astype(str)
        
        # ========== TARGET VARIABLE ==========
        # Create target (next period demand) - will be used for training
        df['target'] = df.groupby(['item_id', 'place_id'])['demand'].shift(-1)
        
        # Drop rows with NaN in target (last period for each item/place)
        df = df.dropna(subset=['target'])
        
        # Fill NaN in lag features with forward-fill then 0 (better than just 0)
        lag_cols = [col for col in df.columns if 'lag' in col or 'rolling' in col or 'ema' in col or 'trend' in col or 'growth' in col or 'cv' in col]
        for col in lag_cols:
            # Forward fill within each item/place group, then fill remaining with 0
            df[col] = df.groupby(['item_id', 'place_id'])[col].ffill().fillna(0)
        
        # Fill other numeric features with median (more robust than mean)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['item_id', 'place_id', 'target', 'demand'] and df[col].isna().any():
                # Fill with group median if grouped, else global median
                if col in ['price', 'total_amount']:
                    df[col] = df.groupby('item_id')[col].transform(lambda x: x.fillna(x.median() if not x.isna().all() else 0))
                else:
                    df[col] = df[col].fillna(df[col].median() if df[col].notna().any() else 0)
        
        print(f"Feature engineering complete: {len(df)} records with {len(df.columns)} features")
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """
        Prepare features and target for model training.
        
        Args:
            df (pd.DataFrame): Dataset with engineered features
        
        Returns:
            Tuple of (features_df, target_series, feature_names)
        """
        # Select feature columns (exclude target and identifiers)
        exclude_cols = ['date', 'item_id', 'place_id', 'target', 'demand', 'item_place_interaction']
        
        # Get numeric and categorical columns
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Separate numeric and categorical
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df[feature_cols].select_dtypes(include=['object']).columns.tolist()
        
        # Encode categorical variables
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col].astype(str).fillna('unknown'))
            else:
                df[col] = self.label_encoders[col].transform(df[col].astype(str).fillna('unknown'))
        
        # Combine all features
        all_features = numeric_cols + categorical_cols
        
        # Ensure consistent feature order
        all_features = sorted(all_features)
        
        # Fill remaining NaN with appropriate defaults
        X = df[all_features].copy()
        for col in numeric_cols:
            if X[col].isna().any():
                X[col] = X[col].fillna(X[col].median() if X[col].notna().any() else 0)
        for col in categorical_cols:
            X[col] = X[col].fillna(0)  # Already encoded, 0 is safe default
        
        y = df['target']
        
        self.feature_names = all_features
        
        return X, y, all_features
    
    def train(self, X: pd.DataFrame, y: pd.Series, validation_split: float = 0.2, 
              use_time_series_split: bool = True) -> Dict[str, float]:
        """
        Train the demand forecasting model.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target variable
            validation_split (float): Fraction of data to use for validation
            use_time_series_split (bool): Use proper time series cross-validation
        
        Returns:
            Dict[str, float]: Training metrics
        """
        # Use proper time series split to respect temporal order
        if use_time_series_split:
            # Use TimeSeriesSplit for proper temporal validation
            # Need at least 2 splits, but we'll use the last split only
            n_splits = max(2, int(1 / validation_split))  # Ensure enough splits
            tscv = TimeSeriesSplit(n_splits=n_splits)
            # Get the last split (most recent data for validation)
            splits = list(tscv.split(X))
            train_idx, val_idx = splits[-1]
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        else:
            # Fallback to simple split (not recommended for time series)
            n_samples = len(X)
            split_idx = int(n_samples * (1 - validation_split))
            X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train models based on model_type
        metrics = {}
        
        if self.model_type == 'xgboost' or self.model_type == 'ensemble':
            if XGBOOST_AVAILABLE:
                xgb_model = xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1
                )
                xgb_model.fit(X_train_scaled, y_train)
                self.models['xgboost'] = xgb_model
                
                y_pred = xgb_model.predict(X_val_scaled)
                metrics['xgboost'] = self._calculate_metrics(y_val, y_pred)
                print(f"XGBoost - MAE: {metrics['xgboost']['mae']:.2f}, RMSE: {metrics['xgboost']['rmse']:.2f}")
        
        if self.model_type == 'lightgbm' or self.model_type == 'ensemble':
            if LIGHTGBM_AVAILABLE:
                lgb_model = lgb.LGBMRegressor(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                )
                lgb_model.fit(X_train_scaled, y_train)
                self.models['lightgbm'] = lgb_model
                
                y_pred = lgb_model.predict(X_val_scaled)
                metrics['lightgbm'] = self._calculate_metrics(y_val, y_pred)
                print(f"LightGBM - MAE: {metrics['lightgbm']['mae']:.2f}, RMSE: {metrics['lightgbm']['rmse']:.2f}")
        
        # Always train Random Forest as baseline
        from sklearn.ensemble import RandomForestRegressor
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)
        self.models['random_forest'] = rf_model
        
        y_pred = rf_model.predict(X_val_scaled)
        metrics['random_forest'] = self._calculate_metrics(y_val, y_pred)
        print(f"Random Forest - MAE: {metrics['random_forest']['mae']:.2f}, RMSE: {metrics['random_forest']['rmse']:.2f}")
        
        # Store scaled data for prediction
        self.X_train_scaled = X_train_scaled
        self.X_val_scaled = X_val_scaled
        
        self.is_trained = True
        
        return metrics
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate evaluation metrics."""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = mean_absolute_percentage_error(y_true, y_pred) * 100
        r2 = r2_score(y_true, y_pred)
        
        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2': r2
        }
    
    def predict(self, X: pd.DataFrame, model_name: Optional[str] = None, 
                use_ensemble: bool = True) -> np.ndarray:
        """
        Predict demand for given features.
        
        Args:
            X (pd.DataFrame): Feature matrix
            model_name (str, optional): Specific model to use. If None, uses ensemble or best model.
            use_ensemble (bool): If True and model_type is 'ensemble', average all model predictions.
        
        Returns:
            np.ndarray: Predicted demand values
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Validate input features match training features
        if not self.feature_names:
            raise ValueError("Model has no feature names. Ensure model was trained properly.")
        
        # Check if all required features are present
        missing_features = set(self.feature_names) - set(X.columns)
        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")
        
        # Select and order features to match training
        X_selected = X[self.feature_names].copy()
        
        # Fill missing values with same strategy as training
        for col in X_selected.columns:
            if X_selected[col].isna().any():
                if X_selected[col].dtype in [np.int64, np.float64]:
                    X_selected[col] = X_selected[col].fillna(0)  # Use 0 as default for numeric
                else:
                    X_selected[col] = X_selected[col].fillna(0)
        
        # Scale features
        X_scaled = self.scaler.transform(X_selected)
        
        # Use ensemble averaging if available and requested
        if use_ensemble and self.model_type == 'ensemble' and len(self.models) > 1:
            predictions_list = []
            for model_name, model in self.models.items():
                pred = model.predict(X_scaled)
                predictions_list.append(pred)
            
            # Average predictions from all models
            predictions = np.mean(predictions_list, axis=0)
        elif model_name and model_name in self.models:
            # Use specified model
            model = self.models[model_name]
            predictions = model.predict(X_scaled)
        elif 'lightgbm' in self.models:
            # Use best performing model (LightGBM typically best)
            model = self.models['lightgbm']
            predictions = model.predict(X_scaled)
        elif 'xgboost' in self.models:
            model = self.models['xgboost']
            predictions = model.predict(X_scaled)
        elif 'random_forest' in self.models:
            model = self.models['random_forest']
            predictions = model.predict(X_scaled)
        else:
            raise ValueError("No trained model available")
        
        # Ensure non-negative predictions
        predictions = np.maximum(predictions, 0)
        
        return predictions
    
    def predict_demand(self, item_id: int, place_id: int, date: str, 
                      historical_data: pd.DataFrame = None,
                      period: str = 'daily') -> Dict[str, Union[float, Dict]]:
        """
        Predict demand for a specific item at a specific place and date.
        
        Args:
            item_id (int): Item ID
            place_id (int): Place ID
            date (str): Date in 'YYYY-MM-DD' format
            historical_data (pd.DataFrame): Historical demand data with columns: date, item_id, place_id, demand
            period (str): Prediction period ('daily', 'weekly', 'monthly')
        
        Returns:
            Dict containing prediction and metadata
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not isinstance(item_id, (int, np.integer)):
            raise ValueError(f"item_id must be an integer, got {type(item_id)}")
        if not isinstance(place_id, (int, np.integer)):
            raise ValueError(f"place_id must be an integer, got {type(place_id)}")
        
        try:
            pred_date = pd.to_datetime(date)
        except Exception as e:
            raise ValueError(f"Invalid date format '{date}'. Expected 'YYYY-MM-DD': {e}")
        
        if historical_data is not None:
            required_cols = ['date', 'item_id', 'place_id', 'demand']
            missing_cols = set(required_cols) - set(historical_data.columns)
            if missing_cols:
                raise ValueError(f"historical_data missing required columns: {missing_cols}")
        
        # If historical data provided, use it to create features
        if historical_data is not None:
            # Create features from historical data using same pipeline as training
            features = self._create_prediction_features(item_id, place_id, pred_date, historical_data)
        else:
            # Use default/mean features (less accurate)
            features = self._create_default_features(item_id, place_id, pred_date)
        
        # Predict with ensemble averaging
        # Check if we have a model trained for the requested period
        if period in self.period_models:
            # Use period-specific model (best approach)
            period_model = self.period_models[period]
            prediction = period_model.predict(features, use_ensemble=(self.model_type == 'ensemble'))
            scaled_prediction = float(prediction[0])
            used_period_model = True
        elif self.period == period:
            # Current model matches requested period
            prediction = self.predict(features, use_ensemble=(self.model_type == 'ensemble'))
            scaled_prediction = float(prediction[0])
            used_period_model = True
        else:
            # Need to scale from current model's period to requested period
            base_prediction = self.predict(features, use_ensemble=(self.model_type == 'ensemble'))
            scaled_prediction = self._scale_prediction_by_period(
                float(base_prediction[0]), 
                from_period=self.period, 
                to_period=period,
                date=pred_date
            )
            used_period_model = False
        
        # Add validation and documentation
        prediction_info = {
            'item_id': item_id,
            'place_id': place_id,
            'date': date,
            'period': period,
            'predicted_demand': scaled_prediction,
            'model_period': self.period,
            'used_period_specific_model': used_period_model,
            'model_type': self.model_type,
            'used_ensemble': (self.model_type == 'ensemble' and len(self.models) > 1),
            'units': f'total {period} demand',  # Document what we're predicting
            'note': 'Prediction is total demand for the period, accounting for actual sales patterns'
        }
        
        # Add consistency check if we have daily prediction
        if period != 'daily' and not used_period_model and self.period == 'daily':
            # We scaled from daily, add expected range
            daily_base = float(base_prediction[0])
            if period == 'weekly':
                expected_min = daily_base * 5  # At least 5 days of sales
                expected_max = daily_base * 7  # At most 7 days
                prediction_info['expected_range'] = (expected_min, expected_max)
                prediction_info['consistency_check'] = 'within_expected_range' if expected_min <= scaled_prediction <= expected_max else 'outside_expected_range'
            elif period == 'monthly':
                expected_min = daily_base * 25  # At least 25 days of sales
                expected_max = daily_base * 31  # At most 31 days
                prediction_info['expected_range'] = (expected_min, expected_max)
                prediction_info['consistency_check'] = 'within_expected_range' if expected_min <= scaled_prediction <= expected_max else 'outside_expected_range'
        
        return prediction_info
    
    def _scale_prediction_by_period(self, prediction: float, from_period: str, 
                                    to_period: str, date: pd.Timestamp) -> float:
        """
        Intelligently scale predictions between periods.
        
        Args:
            prediction: Base prediction value
            from_period: Period the prediction is for
            to_period: Period we want to convert to
            date: Date for the prediction (used for smart scaling)
        
        Returns:
            Scaled prediction value
        """
        if from_period == to_period:
            return prediction
        
        # Conversion factors
        conversions = {
            ('daily', 'weekly'): self._daily_to_weekly_scale(date),
            ('daily', 'monthly'): self._daily_to_monthly_scale(date),
            ('weekly', 'daily'): 1.0 / self._daily_to_weekly_scale(date),
            ('weekly', 'monthly'): self._weekly_to_monthly_scale(date),
            ('monthly', 'daily'): 1.0 / self._daily_to_monthly_scale(date),
            ('monthly', 'weekly'): 1.0 / self._weekly_to_monthly_scale(date),
        }
        
        scale_factor = conversions.get((from_period, to_period), 1.0)
        return prediction * scale_factor
    
    def _daily_to_weekly_scale(self, date: pd.Timestamp) -> float:
        """
        Smart scaling from daily to weekly.
        Accounts for day-of-week patterns.
        """
        # Simple approach: 7 days
        # Could be enhanced to account for weekend vs weekday patterns
        # For now, use 7 but could weight by day-of-week demand patterns
        return 7.0
    
    def _daily_to_monthly_scale(self, date: pd.Timestamp) -> float:
        """
        Smart scaling from daily to monthly.
        Accounts for actual month length.
        """
        # Use actual days in the month
        days_in_month = (date.replace(day=28) + pd.Timedelta(days=4)).replace(day=1) - pd.Timedelta(days=1)
        return float(days_in_month.day)
    
    def _weekly_to_monthly_scale(self, date: pd.Timestamp) -> float:
        """Scale from weekly to monthly."""
        days_in_month = (date.replace(day=28) + pd.Timedelta(days=4)).replace(day=1) - pd.Timedelta(days=1)
        return days_in_month.day / 7.0
    
    def load_period_model(self, period: str, model_path: str):
        """
        Load a model trained for a specific period.
        
        Args:
            period: Period the model was trained for ('daily', 'weekly', 'monthly')
            model_path: Path to the model file
        """
        period_model = DemandForecastModel()
        period_model.load(model_path)
        self.period_models[period] = period_model
        print(f"Loaded {period} model from {model_path}")
    
    def save(self, filepath: str):
        """Save the trained model to disk."""
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'period': self.period,  # Save the period
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load a trained model from disk."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.models = model_data['models']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_names = model_data['feature_names']
        self.model_type = model_data['model_type']
        self.period = model_data.get('period', 'daily')  # Load period, default to daily
        self.is_trained = model_data['is_trained']
        
        print(f"Model loaded from {filepath} (trained for {self.period} period)")
    
    def _create_prediction_features(self, item_id: int, place_id: int, 
                                    date: pd.Timestamp, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        Create feature vector for prediction from historical data.
        Uses the same feature engineering logic as training to ensure consistency.
        """
        # Filter and sort historical data for this item/place
        item_data = historical_data[
            (historical_data['item_id'] == item_id) & 
            (historical_data['place_id'] == place_id)
        ].copy()
        
        if 'date' in item_data.columns:
            if not pd.api.types.is_datetime64_any_dtype(item_data['date']):
                item_data['date'] = pd.to_datetime(item_data['date'])
            item_data = item_data.sort_values('date')
        
        # Initialize features dictionary
        features_dict = {}
        
        # ========== TEMPORAL FEATURES (match training) ==========
        features_dict['year'] = date.year
        features_dict['month'] = date.month
        features_dict['day_of_month'] = date.day
        features_dict['day_of_week'] = date.dayofweek
        features_dict['week_of_year'] = date.isocalendar().week
        features_dict['is_weekend'] = 1 if date.dayofweek >= 5 else 0
        features_dict['is_month_start'] = 1 if date.day <= 3 else 0
        features_dict['is_month_end'] = 1 if date.day >= 28 else 0
        features_dict['is_quarter_start'] = 1 if date.is_quarter_start else 0
        features_dict['is_quarter_end'] = 1 if date.is_quarter_end else 0
        features_dict['quarter'] = date.quarter
        
        # Cyclical encoding
        features_dict['month_sin'] = np.sin(2 * np.pi * date.month / 12)
        features_dict['month_cos'] = np.cos(2 * np.pi * date.month / 12)
        features_dict['day_of_week_sin'] = np.sin(2 * np.pi * date.dayofweek / 7)
        features_dict['day_of_week_cos'] = np.cos(2 * np.pi * date.dayofweek / 7)
        features_dict['day_of_month_sin'] = np.sin(2 * np.pi * date.day / 31)
        features_dict['day_of_month_cos'] = np.cos(2 * np.pi * date.day / 31)
        features_dict['week_of_year_sin'] = np.sin(2 * np.pi * date.isocalendar().week / 52)
        features_dict['week_of_year_cos'] = np.cos(2 * np.pi * date.isocalendar().week / 52)
        
        # Season
        season_map = {3: 'Spring', 4: 'Spring', 5: 'Spring',
                      6: 'Summer', 7: 'Summer', 8: 'Summer',
                      9: 'Fall', 10: 'Fall', 11: 'Fall',
                      12: 'Winter', 1: 'Winter', 2: 'Winter'}
        features_dict['season'] = season_map.get(date.month, 'Unknown')
        
        # ========== HISTORICAL DEMAND FEATURES ==========
        if len(item_data) > 0 and 'demand' in item_data.columns:
            demand_series = item_data['demand']
            
            # Lag features
            for lag in [1, 2, 3, 7, 14, 21, 30, 60]:
                if len(demand_series) >= lag:
                    features_dict[f'demand_lag_{lag}'] = demand_series.iloc[-lag]
                else:
                    features_dict[f'demand_lag_{lag}'] = 0
            
            # Rolling statistics
            for window in [3, 7, 14, 21, 30, 60, 90]:
                window_data = demand_series.tail(window)
                if len(window_data) >= 2:
                    features_dict[f'demand_rolling_mean_{window}'] = window_data.mean()
                    features_dict[f'demand_rolling_std_{window}'] = window_data.std() if len(window_data) > 1 else 0
                    features_dict[f'demand_rolling_min_{window}'] = window_data.min()
                    features_dict[f'demand_rolling_max_{window}'] = window_data.max()
                else:
                    features_dict[f'demand_rolling_mean_{window}'] = demand_series.mean() if len(demand_series) > 0 else 0
                    features_dict[f'demand_rolling_std_{window}'] = 0
                    features_dict[f'demand_rolling_min_{window}'] = 0
                    features_dict[f'demand_rolling_max_{window}'] = 0
            
            # Exponential moving averages
            for alpha in [0.1, 0.3, 0.5, 0.7, 0.9]:
                if len(demand_series) > 0:
                    ema = demand_series.ewm(alpha=alpha, adjust=False).mean()
                    features_dict[f'demand_ema_{alpha}'] = ema.iloc[-1]
                else:
                    features_dict[f'demand_ema_{alpha}'] = 0
            
            # Trend features
            for window in [7, 14, 30]:
                window_data = demand_series.tail(window)
                if len(window_data) >= 2:
                    x = np.arange(len(window_data))
                    trend = np.polyfit(x, window_data.values, 1)[0]
                    features_dict[f'demand_trend_{window}'] = trend
                else:
                    features_dict[f'demand_trend_{window}'] = 0
            
            # Seasonal patterns
            if 'date' in item_data.columns:
                item_data['day_of_week'] = pd.to_datetime(item_data['date']).dt.dayofweek
                item_data['day_of_month'] = pd.to_datetime(item_data['date']).dt.day
                
                same_dow = item_data[item_data['day_of_week'] == date.dayofweek]['demand']
                same_dom = item_data[item_data['day_of_month'] == date.day]['demand']
                
                features_dict['demand_same_dow'] = same_dow.iloc[-1] if len(same_dow) > 0 else 0
                features_dict['demand_same_dom'] = same_dom.iloc[-1] if len(same_dom) > 0 else 0
            else:
                features_dict['demand_same_dow'] = 0
                features_dict['demand_same_dom'] = 0
            
            # Growth rate
            if len(demand_series) >= 7:
                features_dict['demand_growth_7d'] = demand_series.pct_change(periods=7).iloc[-1] if len(demand_series) >= 7 else 0
            else:
                features_dict['demand_growth_7d'] = 0
            
            if len(demand_series) >= 30:
                features_dict['demand_growth_30d'] = demand_series.pct_change(periods=30).iloc[-1] if len(demand_series) >= 30 else 0
            else:
                features_dict['demand_growth_30d'] = 0
            
            # Volatility (coefficient of variation)
            for window in [7, 30]:
                window_data = demand_series.tail(window)
                if len(window_data) >= 2 and window_data.mean() != 0:
                    features_dict[f'demand_cv_{window}'] = window_data.std() / window_data.mean()
                else:
                    features_dict[f'demand_cv_{window}'] = 0
        else:
            # Default values if no history
            for lag in [1, 2, 3, 7, 14, 21, 30, 60]:
                features_dict[f'demand_lag_{lag}'] = 0
            for window in [3, 7, 14, 21, 30, 60, 90]:
                features_dict[f'demand_rolling_mean_{window}'] = 0
                features_dict[f'demand_rolling_std_{window}'] = 0
                features_dict[f'demand_rolling_min_{window}'] = 0
                features_dict[f'demand_rolling_max_{window}'] = 0
            for alpha in [0.1, 0.3, 0.5, 0.7, 0.9]:
                features_dict[f'demand_ema_{alpha}'] = 0
            for window in [7, 14, 30]:
                features_dict[f'demand_trend_{window}'] = 0
            features_dict['demand_same_dow'] = 0
            features_dict['demand_same_dom'] = 0
            features_dict['demand_growth_7d'] = 0
            features_dict['demand_growth_30d'] = 0
            features_dict['demand_cv_7'] = 0
            features_dict['demand_cv_30'] = 0
        
        # ========== PLACE/LOCATION FEATURES ==========
        # Get place-level statistics from historical data
        place_data = historical_data[historical_data['place_id'] == place_id].copy()
        if len(place_data) > 0 and 'demand' in place_data.columns:
            if 'date' in place_data.columns:
                place_data = place_data.sort_values('date')
                place_demand = place_data.groupby('date')['demand'].sum()
                
                features_dict['place_total_demand'] = place_demand.iloc[-1] if len(place_demand) > 0 else 0
                features_dict['place_demand_lag_1'] = place_demand.iloc[-2] if len(place_demand) >= 2 else 0
                features_dict['place_demand_lag_7'] = place_demand.iloc[-8] if len(place_demand) >= 8 else 0
                
                features_dict['place_demand_rolling_mean_7'] = place_demand.tail(7).mean() if len(place_demand) >= 7 else 0
                features_dict['place_demand_rolling_mean_30'] = place_demand.tail(30).mean() if len(place_demand) >= 30 else 0
                
                features_dict['place_unique_items'] = place_data.groupby('date')['item_id'].nunique().iloc[-1] if len(place_data) > 0 else 0
            else:
                features_dict['place_total_demand'] = place_data['demand'].sum()
                features_dict['place_demand_lag_1'] = 0
                features_dict['place_demand_lag_7'] = 0
                features_dict['place_demand_rolling_mean_7'] = 0
                features_dict['place_demand_rolling_mean_30'] = 0
                features_dict['place_unique_items'] = place_data['item_id'].nunique()
        else:
            features_dict['place_total_demand'] = 0
            features_dict['place_demand_lag_1'] = 0
            features_dict['place_demand_lag_7'] = 0
            features_dict['place_demand_rolling_mean_7'] = 0
            features_dict['place_demand_rolling_mean_30'] = 0
            features_dict['place_unique_items'] = 0
        
        # Item's share of place demand
        if features_dict.get('place_total_demand', 0) > 0 and len(item_data) > 0:
            item_demand = item_data['demand'].iloc[-1] if len(item_data) > 0 else 0
            features_dict['item_share_of_place'] = item_demand / features_dict['place_total_demand']
        else:
            features_dict['item_share_of_place'] = 0
        
        # ========== ITEM FEATURES ==========
        # Price and other item features (if available in historical_data)
        if 'price' in item_data.columns:
            features_dict['price'] = item_data['price'].iloc[-1] if len(item_data) > 0 else 0
        else:
            features_dict['price'] = 0
        
        if 'total_amount' in item_data.columns:
            features_dict['total_amount'] = item_data['total_amount'].iloc[-1] if len(item_data) > 0 else 0
        else:
            features_dict['total_amount'] = 0
        
        # Create DataFrame
        features_df = pd.DataFrame([features_dict])
        
        # Encode categorical features if they exist
        if 'season' in features_df.columns and 'season' in self.label_encoders:
            features_df['season'] = self.label_encoders['season'].transform(
                features_df['season'].astype(str).fillna('unknown')
            )
        
        # Ensure all training features are present with correct types
        for feat in self.feature_names:
            if feat not in features_df.columns:
                # Determine type from training data if available
                features_df[feat] = 0
        
        # Reorder columns to match training exactly
        if self.feature_names:
            features_df = features_df[self.feature_names]
        
        return features_df
    
    def _create_default_features(self, item_id: int, place_id: int, 
                                date: pd.Timestamp) -> pd.DataFrame:
        """
        Create default feature vector when no historical data available.
        Uses same structure as _create_prediction_features but with zeros for historical features.
        """
        # Use same structure as prediction features but with empty historical data
        empty_historical = pd.DataFrame(columns=['date', 'item_id', 'place_id', 'demand'])
        return self._create_prediction_features(item_id, place_id, date, empty_historical)

