"""
File: inventory_service.py
Description: Business logic for inventory management and demand forecasting.
Dependencies: pandas, numpy, sklearn
Author: ML Team

This service integrates the ML demand forecasting model for accurate predictions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from models.demand_forecast_model import DemandForecastModel
    ML_MODEL_AVAILABLE = True
except ImportError:
    ML_MODEL_AVAILABLE = False
    print("Warning: DemandForecastModel not available. Using fallback methods.")


class InventoryService:
    """
    Handles inventory management operations and demand forecasting.
    
    This service provides methods for analyzing inventory levels, predicting demand,
    and generating recommendations for stock optimization using ML models.
    
    Attributes:
        inventory_data (pd.DataFrame): Current inventory dataset.
        sales_data (pd.DataFrame): Historical sales dataset.
        demand_model (DemandForecastModel): Trained ML model for demand forecasting.
        model_loaded (bool): Whether ML model is loaded and ready.
    """
    
    def __init__(self, inventory_data: pd.DataFrame = None, sales_data: pd.DataFrame = None,
                 model_path: Optional[str] = None, data_path: Optional[str] = None):
        """
        Initialize the InventoryService.
        
        Args:
            inventory_data (pd.DataFrame, optional): Current inventory dataset.
            sales_data (pd.DataFrame, optional): Historical sales dataset.
            model_path (str, optional): Path to saved ML model file.
            data_path (str, optional): Path to data directory for model initialization.
        """
        self.inventory_data = inventory_data
        self.sales_data = sales_data
        self.demand_model = None
        self.model_loaded = False
        self.data_path = data_path
        self.period_models = {}  # Store models for different periods
        
        # Try to load ML model if path provided
        if model_path and ML_MODEL_AVAILABLE and os.path.exists(model_path):
            try:
                self.demand_model = DemandForecastModel()
                self.demand_model.load(model_path)
                self.model_loaded = True
                print(f"Loaded ML model from {model_path}")
                
                # Try to load period-specific models if available
                model_dir = os.path.dirname(model_path) or 'models'
                for period in ['daily', 'weekly', 'monthly']:
                    period_model_path = os.path.join(model_dir, f'demand_forecast_{period}_ensemble.pkl')
                    if os.path.exists(period_model_path):
                        try:
                            self.demand_model.load_period_model(period, period_model_path)
                            print(f"Loaded {period} period model")
                        except Exception as e:
                            print(f"Could not load {period} model: {e}")
            except Exception as e:
                print(f"Warning: Could not load ML model: {e}. Using fallback methods.")
        elif data_path and ML_MODEL_AVAILABLE:
            # Initialize model with data path for training
            self.demand_model = DemandForecastModel(data_path=data_path)
    
    def predict_demand(self, item_id: str, period: str = 'daily', 
                      place_id: Optional[int] = None, 
                      date: Optional[str] = None) -> float:
        """
        Predicts demand for a specific item using ML model or fallback method.
        
        Args:
            item_id (str): The unique identifier of the item.
            period (str): Time period for prediction ('daily', 'weekly', 'monthly').
            place_id (int, optional): Place/location ID for more accurate predictions.
            date (str, optional): Date in 'YYYY-MM-DD' format. Defaults to tomorrow.
        
        Returns:
            float: Predicted demand quantity.
        
        Raises:
            ValueError: If item_id not found in sales data and ML model unavailable.
        """
        # Use ML model if available and loaded
        if self.model_loaded and self.demand_model:
            try:
                # Use provided date or default to tomorrow
                if not date:
                    from datetime import datetime, timedelta
                    date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                
                # Use provided place_id or default to first available
                if not place_id and self.sales_data is not None:
                    item_sales = self.sales_data[self.sales_data['item_id'] == int(item_id)]
                    if not item_sales.empty:
                        place_id = item_sales['place_id'].iloc[0]
                    else:
                        place_id = 1  # Default fallback
                elif not place_id:
                    place_id = 1  # Default fallback
                
                # Prepare historical data if available
                historical_data = None
                if self.sales_data is not None:
                    item_sales = self.sales_data[self.sales_data['item_id'] == int(item_id)].copy()
                    if period == 'weekly':
                        # Aggregate demand by week
                        item_sales['week'] = pd.to_datetime(item_sales['date']).dt.isocalendar().week
                        item_sales['year'] = pd.to_datetime(item_sales['date']).dt.year
                        weekly = item_sales.groupby(['year', 'week', 'item_id', 'place_id']).agg({'demand': 'sum'}).reset_index()
                        # Use only relevant place
                        historical_data = weekly[weekly['place_id'] == int(place_id)]
                    elif period == 'monthly':
                        # Aggregate demand by month
                        item_sales['month'] = pd.to_datetime(item_sales['date']).dt.month
                        item_sales['year'] = pd.to_datetime(item_sales['date']).dt.year
                        monthly = item_sales.groupby(['year', 'month', 'item_id', 'place_id']).agg({'demand': 'sum'}).reset_index()
                        historical_data = monthly[monthly['place_id'] == int(place_id)]
                    else:
                        # Daily
                        historical_data = item_sales[item_sales['place_id'] == int(place_id)]
                
                prediction = self.demand_model.predict_demand(
                    item_id=int(item_id),
                    place_id=int(place_id),
                    date=date,
                    historical_data=historical_data,
                    period=period
                )
                return round(prediction['predicted_demand'], 2)
                
            except Exception as e:
                print(f"ML model prediction failed: {e}. Falling back to statistical method.")
        
        # Fallback to statistical method
        if self.sales_data is None:
            raise ValueError("No sales data available for prediction")
        
        # Filter sales data for the specific item
        item_sales = self.sales_data[self.sales_data['item_id'] == int(item_id)]
        
        if item_sales.empty:
            raise ValueError(f"No sales data found for item: {item_id}")
        
        # Simple moving average (last 7 days for daily, etc.)
        window = 7 if period == 'daily' else 4 if period == 'weekly' else 3
        avg_demand = item_sales['quantity'].tail(window).mean()
        
        return round(avg_demand, 2)
    
    def calculate_reorder_point(self, item_id: str, lead_time_days: int = 3,
                                place_id: Optional[int] = None) -> int:
        """
        Calculates the optimal reorder point for an item using ML predictions.
        
        Reorder Point = (Average Daily Demand × Lead Time) + Safety Stock
        
        Args:
            item_id (str): The unique identifier of the item.
            lead_time_days (int): Number of days for supplier delivery.
            place_id (int, optional): Place ID for location-specific predictions.
        
        Returns:
            int: Recommended reorder point quantity.
        """
        # Use ML model for more accurate daily demand prediction
        daily_demand = self.predict_demand(item_id, 'daily', place_id=place_id)
        
        # Calculate demand variability for safety stock
        if self.sales_data is not None:
            item_sales = self.sales_data[self.sales_data['item_id'] == int(item_id)]
            if len(item_sales) > 7:
                # Use standard deviation for safety stock calculation
                demand_std = item_sales['quantity'].tail(30).std()
                # Safety stock = Z-score (1.65 for 95% service level) × std × sqrt(lead_time)
                safety_stock = 1.65 * demand_std * np.sqrt(lead_time_days)
            else:
                # Fallback: 50% of lead time demand
                safety_stock = (daily_demand * lead_time_days) * 0.5
        else:
            # Default safety stock
            safety_stock = (daily_demand * lead_time_days) * 0.5
        
        reorder_point = (daily_demand * lead_time_days) + safety_stock
        
        return int(np.ceil(max(reorder_point, 0)))
    
    def identify_expiring_items(self, days_threshold: int = 7) -> pd.DataFrame:
        """
        Identifies items that are approaching expiration.
        
        Args:
            days_threshold (int): Number of days before expiration to flag items.
        
        Returns:
            pd.DataFrame: DataFrame containing items near expiration with recommendations.
        """
        # This is a placeholder - students should implement actual expiration logic
        expiring = self.inventory_data[
            self.inventory_data['days_until_expiration'] <= days_threshold
        ]
        
        return expiring.sort_values('days_until_expiration')
    
    def generate_recommendations(self, item_id: str, place_id: Optional[int] = None) -> Dict[str, any]:
        """
        Generates comprehensive inventory recommendations for an item using ML predictions.
        
        Args:
            item_id (str): The unique identifier of the item.
            place_id (int, optional): Place ID for location-specific recommendations.
        
        Returns:
            Dict[str, any]: Dictionary containing recommendations and metrics.
        """
        try:
            # Get predictions for all periods
            daily_demand = self.predict_demand(item_id, 'daily', place_id=place_id)
            weekly_demand = self.predict_demand(item_id, 'weekly', place_id=place_id)
            monthly_demand = self.predict_demand(item_id, 'monthly', place_id=place_id)
            
            # Calculate reorder point
            reorder_point = self.calculate_reorder_point(item_id, place_id=place_id)
            
            # Determine status based on current inventory (if available)
            status = 'optimal'
            action = 'monitor'
            
            if self.inventory_data is not None:
                item_inventory = self.inventory_data[
                    self.inventory_data.get('item_id', pd.Series()) == int(item_id)
                ]
                
                if not item_inventory.empty:
                    current_stock = item_inventory.iloc[0].get('quantity_on_hand', 0)
                    
                    if current_stock < reorder_point * 0.5:
                        status = 'critical'
                        action = 'reorder_urgent'
                    elif current_stock < reorder_point:
                        status = 'low'
                        action = 'reorder'
                    elif current_stock > reorder_point * 3:
                        status = 'overstocked'
                        action = 'reduce_order'
            
            recommendations = {
                'item_id': item_id,
                'place_id': place_id,
                'predicted_daily_demand': daily_demand,
                'predicted_weekly_demand': weekly_demand,
                'predicted_monthly_demand': monthly_demand,
                'reorder_point': reorder_point,
                'status': status,
                'action': action,
                'model_type': 'ml' if self.model_loaded else 'statistical'
            }
            
        except Exception as e:
            # Fallback recommendations
            recommendations = {
                'item_id': item_id,
                'place_id': place_id,
                'predicted_daily_demand': 0,
                'predicted_weekly_demand': 0,
                'predicted_monthly_demand': 0,
                'reorder_point': 0,
                'status': 'unknown',
                'action': 'investigate',
                'error': str(e),
                'model_type': 'fallback'
            }
        
        return recommendations
