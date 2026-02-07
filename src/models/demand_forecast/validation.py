"""
Data validation for demand forecasting inputs.

Provides validators for data quality, temporal consistency, and business rules.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class DataValidator:
    """
    Validates input data for demand forecasting.
    
    Checks data quality, temporal consistency, and business rule constraints.
    """
    
    def __init__(self, strict: bool = False):
        """
        Initialize validator.
        
        Args:
            strict: If True, raise exceptions on validation failures.
                   If False, log warnings and return validation report.
        """
        self.strict = strict
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_orders(self, orders: pd.DataFrame) -> Dict[str, any]:
        """
        Validate orders DataFrame.
        
        Args:
            orders: Orders DataFrame
            
        Returns:
            Validation report dict
        """
        self._reset_errors()
        
        # Required columns
        required_cols = ['id', 'created', 'place_id', 'status']
        self._check_required_columns(orders, required_cols, 'orders')
        
        # Data type checks
        if 'created' in orders.columns:
            self._check_timestamps(orders, 'created', 'orders')
        
        # Business rules
        if 'place_id' in orders.columns:
            null_places = orders['place_id'].isna().sum()
            if null_places > 0:
                self._add_warning(f"orders: {null_places} rows have null place_id")
        
        return self._get_report()
    
    def validate_order_items(self, order_items: pd.DataFrame) -> Dict[str, any]:
        """Validate order_items DataFrame."""
        self._reset_errors()
        
        required_cols = ['order_id', 'item_id', 'quantity', 'price']
        self._check_required_columns(order_items, required_cols, 'order_items')
        
        # Quantity must be positive
        if 'quantity' in order_items.columns:
            invalid_qty = (order_items['quantity'] <= 0).sum()
            if invalid_qty > 0:
                self._add_error(f"order_items: {invalid_qty} rows have non-positive quantity")
        
        # Price should be non-negative
        if 'price' in order_items.columns:
            negative_price = (order_items['price'] < 0).sum()
            if negative_price > 0:
                self._add_warning(f"order_items: {negative_price} rows have negative price")
        
        return self._get_report()
    
    def validate_demand_dataset(self, demand: pd.DataFrame) -> Dict[str, any]:
        """Validate aggregated demand dataset."""
        self._reset_errors()
        
        required_cols = ['date', 'item_id', 'place_id', 'demand']
        self._check_required_columns(demand, required_cols, 'demand')
        
        # Check for future dates
        if 'date' in demand.columns:
            demand_dates = pd.to_datetime(demand['date'])
            future_dates = (demand_dates > pd.Timestamp.now()).sum()
            if future_dates > 0:
                self._add_error(f"demand: {future_dates} rows have future dates (data leakage risk)")
        
        # Check for duplicate entries
        if all(col in demand.columns for col in ['date', 'item_id', 'place_id']):
            duplicates = demand.duplicated(subset=['date', 'item_id', 'place_id']).sum()
            if duplicates > 0:
                self._add_error(f"demand: {duplicates} duplicate (date, item_id, place_id) entries")
        
        # Demand should be non-negative
        if 'demand' in demand.columns:
            negative_demand = (demand['demand'] < 0).sum()
            if negative_demand > 0:
                self._add_error(f"demand: {negative_demand} rows have negative demand")
        
        return self._get_report()
    
    def validate_prediction_inputs(self, item_id: int, place_id: int, 
                                   date: str, period: str) -> Dict[str, any]:
        """
        Validate prediction request inputs.
        
        Args:
            item_id: Item identifier
            place_id: Place identifier  
            date: Date string in 'YYYY-MM-DD' format
            period: Prediction period ('daily', 'weekly', 'monthly')
        """
        self._reset_errors()
        
        # Type checks
        if not isinstance(item_id, (int, np.integer)):
            self._add_error(f"item_id must be integer, got {type(item_id).__name__}")
        
        if not isinstance(place_id, (int, np.integer)):
            self._add_error(f"place_id must be integer, got {type(place_id).__name__}")
        
        # Date format
        try:
            parsed_date = pd.to_datetime(date)
            if parsed_date > pd.Timestamp.now() + pd.Timedelta(days=365):
                self._add_warning("Prediction date is more than 1 year in the future")
        except Exception as e:
            self._add_error(f"Invalid date format '{date}': {e}")
        
        # Valid periods
        valid_periods = ['daily', 'weekly', 'monthly']
        if period not in valid_periods:
            self._add_error(f"period must be one of {valid_periods}, got '{period}'")
        
        return self._get_report()
    
    def validate_historical_data(self, historical: pd.DataFrame, 
                                 item_id: int, place_id: int,
                                 min_history_days: int = 7) -> Dict[str, any]:
        """
        Validate historical data for a specific item/place.
        
        Args:
            historical: Historical demand data
            item_id: Item to check
            place_id: Place to check
            min_history_days: Minimum days of history required
        """
        self._reset_errors()
        
        if historical is None or len(historical) == 0:
            self._add_warning("No historical data provided - using cold start fallback")
            return self._get_report()
        
        # Filter for item/place
        item_data = historical[
            (historical['item_id'] == item_id) & 
            (historical['place_id'] == place_id)
        ]
        
        if len(item_data) == 0:
            self._add_warning(f"No history for item {item_id} at place {place_id} - cold start")
        elif len(item_data) < min_history_days:
            self._add_warning(
                f"Only {len(item_data)} days of history for item {item_id} "
                f"(recommended: {min_history_days}+)"
            )
        
        return self._get_report()
    
    def _check_required_columns(self, df: pd.DataFrame, 
                                required: List[str], table_name: str):
        """Check that required columns exist."""
        missing = set(required) - set(df.columns)
        if missing:
            self._add_error(f"{table_name}: missing required columns {missing}")
    
    def _check_timestamps(self, df: pd.DataFrame, col: str, table_name: str):
        """Check timestamp column validity."""
        try:
            if df[col].dtype in ['int64', 'float64']:
                # Unix timestamp - check reasonable range
                min_ts = df[col].min()
                max_ts = df[col].max()
                if min_ts < 0:
                    self._add_error(f"{table_name}.{col}: negative timestamps found")
                if max_ts > 2e10:  # Year 2603+
                    self._add_warning(f"{table_name}.{col}: very large timestamps (milliseconds?)")
        except Exception as e:
            self._add_warning(f"{table_name}.{col}: timestamp check failed - {e}")
    
    def _add_error(self, msg: str):
        """Add validation error."""
        self.validation_errors.append(msg)
        logger.error(f"Validation error: {msg}")
        if self.strict:
            raise ValidationError(msg)
    
    def _add_warning(self, msg: str):
        """Add validation warning."""
        self.validation_warnings.append(msg)
        logger.warning(f"Validation warning: {msg}")
    
    def _reset_errors(self):
        """Reset error lists."""
        self.validation_errors = []
        self.validation_warnings = []
    
    def _get_report(self) -> Dict[str, any]:
        """Get validation report."""
        return {
            'valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors.copy(),
            'warnings': self.validation_warnings.copy(),
            'error_count': len(self.validation_errors),
            'warning_count': len(self.validation_warnings)
        }
