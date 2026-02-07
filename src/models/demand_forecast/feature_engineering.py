"""
Feature engineering for demand forecasting.

Handles all feature creation including temporal, historical, item, and place features.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Creates features for demand forecasting models.
    
    Responsible for:
    - Temporal features (day, week, month, seasonality)
    - Historical demand features (lags, rolling stats)
    - Item and place features
    - Interaction features
    """
    
    # Configuration for lag features - reduced from original for performance
    LAG_PERIODS = [1, 2, 3, 7, 14, 30]  # Reduced from 8 to 6 key lags
    ROLLING_WINDOWS = [7, 14, 30]  # Reduced from 7 to 3 key windows
    EMA_ALPHAS = [0.3, 0.7]  # Reduced from 5 to 2 key alphas
    
    def __init__(self, include_all_features: bool = True):
        """
        Initialize feature engineer.
        
        Args:
            include_all_features: If True, include all features.
                                 If False, use reduced feature set for performance.
        """
        self.include_all_features = include_all_features
        self.feature_names: List[str] = []
    
    def create_demand_dataset(self, orders: pd.DataFrame, 
                              order_items: pd.DataFrame,
                              period: str = 'daily') -> pd.DataFrame:
        """
        Create aggregated demand dataset from orders and order items.
        
        Args:
            orders: Orders DataFrame with columns [id, created, place_id, status, ...]
            order_items: Order items DataFrame with columns [order_id, item_id, quantity, price, ...]
            period: Aggregation period ('daily', 'weekly', 'monthly')
        
        Returns:
            Aggregated demand DataFrame with columns [date, item_id, place_id, demand, price, total_amount]
        """
        logger.info(f"Creating {period} demand dataset from {len(orders)} orders")
        
        # Merge order items with orders
        orders_subset = orders[['id', 'created', 'place_id', 'type', 'channel', 'status']].copy()
        
        merged = order_items.merge(
            orders_subset,
            left_on='order_id',
            right_on='id',
            how='inner',
            suffixes=('', '_order')
        )
        
        # Filter completed orders
        if 'status' in merged.columns:
            if merged['status'].dtype == 'object':
                completed_statuses = ['Closed', 'closed', 'Completed', 'completed', 'Paid', 'paid']
                merged = merged[merged['status'].isin(completed_statuses)]
        
        # Set date based on period
        merged['date'] = merged['created'].dt.date
        
        if period == 'weekly':
            merged['date'] = pd.to_datetime(merged['date']) - pd.to_timedelta(
                merged['created'].dt.dayofweek, unit='d'
            )
            merged['date'] = merged['date'].dt.date
        elif period == 'monthly':
            merged['date'] = pd.to_datetime(merged['date']).dt.to_period('M').dt.to_timestamp().dt.date
        
        # Calculate total amount if not present
        if 'total_amount' not in merged.columns:
            merged['total_amount'] = merged['quantity'] * merged['price']
        
        # Aggregate by date, item, place
        demand = merged.groupby(['date', 'item_id', 'place_id']).agg({
            'quantity': 'sum',
            'price': 'mean',
            'total_amount': 'sum'
        }).reset_index()
        
        demand.rename(columns={'quantity': 'demand'}, inplace=True)
        
        logger.info(f"Created {period} demand dataset: {len(demand)} records")
        
        return demand
    
    def engineer_features(self, demand_df: pd.DataFrame,
                         items: pd.DataFrame = None,
                         menu_items: pd.DataFrame = None) -> pd.DataFrame:
        """
        Engineer comprehensive features for demand forecasting.
        
        Args:
            demand_df: Base demand dataset with [date, item_id, place_id, demand]
            items: Optional items dimension table
            menu_items: Optional menu items dimension table
        
        Returns:
            Dataset with engineered features
        """
        logger.info(f"Engineering features for {len(demand_df)} records")
        
        df = demand_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # Add all feature groups
        df = self._add_temporal_features(df)
        df = self._add_lag_features(df)
        df = self._add_rolling_features(df)
        df = self._add_place_features(df)
        
        if items is not None:
            df = self._add_item_features(df, items)
        if menu_items is not None:
            df = self._add_menu_item_features(df, menu_items)
        
        # Add interaction features
        df['item_place_interaction'] = df['item_id'].astype(str) + '_' + df['place_id'].astype(str)
        
        # Create target variable (next period demand)
        df['target'] = df.groupby(['item_id', 'place_id'])['demand'].shift(-1)
        
        # Drop rows without target
        df = df.dropna(subset=['target'])
        
        # Fill remaining NaN values
        df = self._fill_missing_values(df)
        
        logger.info(f"Feature engineering complete: {len(df)} records, {len(df.columns)} features")
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal features."""
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_month'] = df['date'].dt.day
        df['day_of_week'] = df['date'].dt.dayofweek
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_month_start'] = (df['day_of_month'] <= 3).astype(int)
        df['is_month_end'] = (df['day_of_month'] >= 28).astype(int)
        df['quarter'] = df['date'].dt.quarter
        
        # Cyclical encoding
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        return df
    
    def _add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add lag features for historical demand."""
        df = df.sort_values(['item_id', 'place_id', 'date'])
        
        for lag in self.LAG_PERIODS:
            df[f'demand_lag_{lag}'] = df.groupby(['item_id', 'place_id'])['demand'].shift(lag)
        
        # Seasonal lags
        df['demand_same_dow'] = df.groupby(['item_id', 'place_id', 'day_of_week'])['demand'].shift(1)
        
        return df
    
    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling window statistics."""
        for window in self.ROLLING_WINDOWS:
            df[f'demand_rolling_mean_{window}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )
            df[f'demand_rolling_std_{window}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.rolling(window=window, min_periods=1).std().fillna(0)
            )
        
        # Exponential moving averages
        for alpha in self.EMA_ALPHAS:
            df[f'demand_ema_{alpha}'] = df.groupby(['item_id', 'place_id'])['demand'].transform(
                lambda x: x.ewm(alpha=alpha, adjust=False).mean()
            )
        
        return df
    
    def _add_place_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add place-level features (with leakage prevention)."""
        # Aggregate place stats from PREVIOUS day to avoid data leakage
        place_stats = df.groupby(['place_id', 'date']).agg({
            'demand': 'sum',
            'item_id': 'nunique'
        }).reset_index()
        place_stats.columns = ['place_id', 'date', 'place_total_demand', 'place_unique_items']
        
        # Shift date forward to use previous day's data
        place_stats['date'] = place_stats['date'] + pd.Timedelta(days=1)
        
        df = df.merge(place_stats, on=['place_id', 'date'], how='left')
        df['place_total_demand'] = df['place_total_demand'].fillna(0)
        df['place_unique_items'] = df['place_unique_items'].fillna(0)
        
        # Place-level rolling stats
        df['place_demand_rolling_mean_7'] = df.groupby('place_id')['place_total_demand'].transform(
            lambda x: x.rolling(7, min_periods=1).mean()
        )
        
        # Item share of place
        df['item_share_of_place'] = df['demand'] / (df['place_total_demand'] + 1e-6)
        
        return df
    
    def _add_item_features(self, df: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
        """Add item dimension features."""
        if 'id' in items.columns and 'price' in items.columns:
            item_features = items[['id', 'price']].copy()
            item_features.columns = ['item_id', 'item_base_price']
            df = df.merge(item_features, on='item_id', how='left')
        return df
    
    def _add_menu_item_features(self, df: pd.DataFrame, menu_items: pd.DataFrame) -> pd.DataFrame:
        """Add menu item dimension features."""
        if 'id' in menu_items.columns:
            menu_cols = ['id']
            for col in ['price', 'status', 'purchases']:
                if col in menu_items.columns:
                    menu_cols.append(col)
            
            menu_features = menu_items[menu_cols].copy()
            menu_features.columns = ['item_id'] + [f'menu_{c}' for c in menu_cols[1:]]
            df = df.merge(menu_features, on='item_id', how='left')
        return df
    
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values with appropriate defaults."""
        # Lag and rolling features - forward fill then 0
        lag_cols = [c for c in df.columns if 'lag' in c or 'rolling' in c or 'ema' in c]
        for col in lag_cols:
            df[col] = df.groupby(['item_id', 'place_id'])[col].ffill().fillna(0)
        
        # Other numeric - fill with median or 0
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['item_id', 'place_id', 'target', 'demand'] and df[col].isna().any():
                median_val = df[col].median() if df[col].notna().any() else 0
                df[col] = df[col].fillna(median_val)
        
        return df
    
    def get_cold_start_features(self, item_id: int, place_id: int, 
                                date: pd.Timestamp,
                                global_stats: Dict = None) -> pd.DataFrame:
        """
        Generate features for cold start (new item/place with no history).
        
        Uses global averages or reasonable defaults instead of zeros.
        
        Args:
            item_id: Item ID
            place_id: Place ID
            date: Prediction date
            global_stats: Optional dict with global averages
        
        Returns:
            Single-row DataFrame with features
        """
        if global_stats is None:
            global_stats = {
                'avg_demand': 5.0,
                'avg_price': 50.0,
                'avg_place_demand': 100.0
            }
        
        features = {
            'item_id': item_id,
            'place_id': place_id,
            'date': date,
            'year': date.year,
            'month': date.month,
            'day_of_month': date.day,
            'day_of_week': date.dayofweek,
            'week_of_year': date.isocalendar().week,
            'is_weekend': 1 if date.dayofweek >= 5 else 0,
            'is_month_start': 1 if date.day <= 3 else 0,
            'is_month_end': 1 if date.day >= 28 else 0,
            'quarter': date.quarter,
            # Cyclical encoding
            'month_sin': np.sin(2 * np.pi * date.month / 12),
            'month_cos': np.cos(2 * np.pi * date.month / 12),
            'day_of_week_sin': np.sin(2 * np.pi * date.dayofweek / 7),
            'day_of_week_cos': np.cos(2 * np.pi * date.dayofweek / 7),
        }
        
        # Use global averages for historical features
        for lag in self.LAG_PERIODS:
            features[f'demand_lag_{lag}'] = global_stats['avg_demand']
        
        for window in self.ROLLING_WINDOWS:
            features[f'demand_rolling_mean_{window}'] = global_stats['avg_demand']
            features[f'demand_rolling_std_{window}'] = global_stats['avg_demand'] * 0.3
        
        # Add EMA features (was missing)
        for alpha in self.EMA_ALPHAS:
            features[f'demand_ema_{alpha}'] = global_stats['avg_demand']
        
        # Add seasonal lag
        features['demand_same_dow'] = global_stats['avg_demand']
        
        features['place_total_demand'] = global_stats['avg_place_demand']
        features['place_unique_items'] = 5  # Default estimate
        features['place_total_demand'] = global_stats['avg_place_demand']
        features['place_unique_items'] = 5  # Default estimate
        features['place_demand_rolling_mean_7'] = global_stats['avg_place_demand']
        features['item_share_of_place'] = global_stats['avg_demand'] / (global_stats['avg_place_demand'] + 1e-6)
        
        # Add missing Item/Menu/Price features
        avg_price = global_stats.get('avg_price', 50.0)
        features['price'] = avg_price
        features['item_base_price'] = avg_price
        features['menu_price'] = avg_price
        features['total_amount'] = global_stats['avg_demand'] * avg_price
        features['menu_purchases'] = 0
        features['menu_status'] = 0  # Default encoded value for unknown status
        features['target'] = 0 # Dummy target
        
        return pd.DataFrame([features])
