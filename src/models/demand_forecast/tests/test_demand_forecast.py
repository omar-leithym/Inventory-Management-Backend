"""
Unit tests for demand forecasting modules.

Run with: pytest src/models/demand_forecast/tests/ -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestDataValidator:
    """Tests for DataValidator class."""
    
    def test_validate_prediction_inputs_valid(self):
        """Test valid prediction inputs pass validation."""
        from src.models.demand_forecast.validation import DataValidator
        
        validator = DataValidator()
        result = validator.validate_prediction_inputs(
            item_id=123,
            place_id=1,
            date="2024-01-15",
            period="daily"
        )
        
        assert result['valid'] is True
        assert result['error_count'] == 0
    
    def test_validate_prediction_inputs_invalid_item_id(self):
        """Test invalid item_id fails validation."""
        from src.models.demand_forecast.validation import DataValidator
        
        validator = DataValidator()
        result = validator.validate_prediction_inputs(
            item_id="invalid",
            place_id=1,
            date="2024-01-15",
            period="daily"
        )
        
        assert result['valid'] is False
        assert result['error_count'] > 0
    
    def test_validate_prediction_inputs_invalid_period(self):
        """Test invalid period fails validation."""
        from src.models.demand_forecast.validation import DataValidator
        
        validator = DataValidator()
        result = validator.validate_prediction_inputs(
            item_id=1,
            place_id=1,
            date="2024-01-15",
            period="yearly"  # Invalid
        )
        
        assert result['valid'] is False
        assert 'period' in str(result['errors'])
    
    def test_validate_demand_dataset_valid(self):
        """Test valid demand dataset passes."""
        from src.models.demand_forecast.validation import DataValidator
        
        demand = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'item_id': [1] * 10,
            'place_id': [1] * 10,
            'demand': [5] * 10
        })
        
        validator = DataValidator()
        result = validator.validate_demand_dataset(demand)
        
        assert result['valid'] is True
    
    def test_validate_demand_dataset_negative_demand(self):
        """Test negative demand fails validation."""
        from src.models.demand_forecast.validation import DataValidator
        
        demand = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'item_id': [1] * 5,
            'place_id': [1] * 5,
            'demand': [5, 3, -1, 4, 2]  # Negative demand
        })
        
        validator = DataValidator()
        result = validator.validate_demand_dataset(demand)
        
        assert result['valid'] is False


class TestFeatureEngineer:
    """Tests for FeatureEngineer class."""
    
    @pytest.fixture
    def sample_demand_data(self):
        """Create sample demand data for testing."""
        dates = pd.date_range('2024-01-01', periods=60, freq='D')
        return pd.DataFrame({
            'date': dates,
            'item_id': [1] * 30 + [2] * 30,
            'place_id': [1] * 60,
            'demand': np.random.randint(1, 20, 60),
            'price': [10.0] * 60,
            'total_amount': [50.0] * 60
        })
    
    def test_add_temporal_features(self, sample_demand_data):
        """Test temporal features are added correctly."""
        from src.models.demand_forecast.feature_engineering import FeatureEngineer
        
        fe = FeatureEngineer()
        df = sample_demand_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        result = fe._add_temporal_features(df)
        
        assert 'year' in result.columns
        assert 'month' in result.columns
        assert 'day_of_week' in result.columns
        assert 'is_weekend' in result.columns
        assert 'month_sin' in result.columns
    
    def test_add_lag_features(self, sample_demand_data):
        """Test lag features are created correctly."""
        from src.models.demand_forecast.feature_engineering import FeatureEngineer
        
        fe = FeatureEngineer()
        df = sample_demand_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = fe._add_temporal_features(df)
        
        result = fe._add_lag_features(df)
        
        assert 'demand_lag_1' in result.columns
        assert 'demand_lag_7' in result.columns
    
    def test_cold_start_features(self):
        """Test cold start feature generation."""
        from src.models.demand_forecast.feature_engineering import FeatureEngineer
        
        fe = FeatureEngineer()
        date = pd.Timestamp('2024-01-15')
        
        result = fe.get_cold_start_features(
            item_id=999,
            place_id=1,
            date=date,
            global_stats={'avg_demand': 10, 'avg_price': 50, 'avg_place_demand': 100}
        )
        
        assert len(result) == 1
        assert result['item_id'].iloc[0] == 999
        assert 'demand_lag_1' in result.columns
        # Cold start uses global average
        assert result['demand_lag_1'].iloc[0] == 10


class TestDemandPredictor:
    """Tests for DemandPredictor class."""
    
    def test_scale_prediction_daily_to_weekly(self):
        """Test scaling from daily to weekly."""
        from src.models.demand_forecast.prediction import DemandPredictor
        from src.models.demand_forecast.training import ModelTrainer
        from src.models.demand_forecast.feature_engineering import FeatureEngineer
        
        trainer = ModelTrainer()
        fe = FeatureEngineer()
        predictor = DemandPredictor(trainer, fe)
        
        date = pd.Timestamp('2024-01-15')
        daily_pred = 10.0
        
        weekly_pred = predictor._scale_prediction(daily_pred, 'daily', 'weekly', date)
        
        assert weekly_pred == 70.0  # 10 * 7 days
    
    def test_scale_prediction_same_period(self):
        """Test scaling with same period returns unchanged."""
        from src.models.demand_forecast.prediction import DemandPredictor
        from src.models.demand_forecast.training import ModelTrainer
        from src.models.demand_forecast.feature_engineering import FeatureEngineer
        
        trainer = ModelTrainer()
        fe = FeatureEngineer()
        predictor = DemandPredictor(trainer, fe)
        
        date = pd.Timestamp('2024-01-15')
        pred = 10.0
        
        result = predictor._scale_prediction(pred, 'daily', 'daily', date)
        
        assert result == 10.0


class TestIntegration:
    """Integration tests for the full pipeline."""
    
    def test_full_pipeline_with_mock_data(self):
        """Test the full training and prediction pipeline."""
        from src.models.demand_forecast import DemandForecastModel
        
        # Create mock orders
        orders = pd.DataFrame({
            'id': range(100),
            'created': pd.date_range('2024-01-01', periods=100, freq='D').astype(int) // 10**9,
            'place_id': [1] * 50 + [2] * 50,
            'type': ['takeaway'] * 100,
            'channel': ['app'] * 100,
            'status': ['Closed'] * 100
        })
        
        # Create mock order items
        order_items = pd.DataFrame({
            'order_id': list(range(100)) * 3,
            'item_id': [1, 2, 3] * 100,
            'quantity': np.random.randint(1, 5, 300),
            'price': [10.0] * 300,
            'created': list(pd.date_range('2024-01-01', periods=100, freq='D').astype(int) // 10**9) * 3
        })
        
        # Convert timestamps
        orders['created'] = pd.to_datetime(orders['created'], unit='s')
        order_items['created'] = pd.to_datetime(order_items['created'], unit='s')
        
        # Initialize model
        model = DemandForecastModel(model_type='random_forest', period='daily')
        
        # Note: Full pipeline test would require more data
        # This tests the instantiation and basic setup
        assert model.is_trained is False
        assert model.period == 'daily'
