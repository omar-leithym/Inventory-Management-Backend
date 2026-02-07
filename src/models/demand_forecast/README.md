# Demand Forecast Model

Modular, production-ready demand forecasting system using gradient boosting with 40+ engineered features.

## Features

- **Multiple Models**: XGBoost (default), LightGBM, Random Forest, Ensemble
- **40+ Features**: Temporal, lag, rolling statistics, place-level, item-level
- **Cold Start Handling**: Smart fallbacks using global averages for new items/places
- **Multi-Period Support**: Daily, weekly, monthly with native period aggregation
- **Data Leakage Prevention**: Proper temporal handling for all features
- **Input Validation**: Comprehensive data quality checks

## Quick Start

```python
from src.models.demand_forecast import DemandForecastModel

# Initialize
model = DemandForecastModel(
    model_type='xgboost',  # 'xgboost', 'lightgbm', 'random_forest', 'ensemble'
    data_path='./data/Inventory Management',
    period='daily'         # 'daily', 'weekly', 'monthly'
)

# Train
metrics = model.train_pipeline()
print(f"MAE: {metrics['xgboost']['mae']:.2f}")

# Predict
result = model.predict_demand(
    item_id=123,
    place_id=456,
    date='2024-03-01'
)
print(f"Predicted: {result['predicted_demand']:.1f} units")

# Save/Load
model.save('models/demand_forecast.pkl')
model.load('models/demand_forecast.pkl')
```

## Module Structure

| Module | Purpose |
|--------|---------|
| `model.py` | Main orchestrator - single entry point |
| `feature_engineering.py` | 40+ features: temporal, lag, rolling, place, item |
| `training.py` | Model training, hyperparameters, cross-validation |
| `prediction.py` | Inference, ensemble, period scaling |
| `validation.py` | Data quality checks, schema enforcement |

## Feature Categories

| Category | Examples |
|----------|----------|
| **Temporal** | day_of_week, is_weekend, month_sin/cos, quarter |
| **Lag** | demand_lag_1, demand_lag_7, demand_same_dow |
| **Rolling** | rolling_mean_7/14/30, rolling_std, EMA |
| **Place** | place_total_demand, place_unique_items, item_share |
| **Item** | base_price, menu_status, menu_purchases |

## Performance

| Model | MAE | R² | Best For |
|-------|-----|-----|----------|
| **XGBoost** | **2.60** | **0.684** | Production (best accuracy) |
| LightGBM | 2.64 | 0.648 | Fast training |
| Random Forest | 2.81 | 0.651 | Robust baseline |
| Ensemble | ~2.55 | ~0.69 | Highest accuracy |

## Period Handling

The model uses **native period aggregation** during training:

| Period | Training Data |
|--------|--------------|
| `daily` | Sum demand per day |
| `weekly` | Sum demand per week |
| `monthly` | Sum demand per month |

## API Integration

The model is exposed via Flask API on port 5001:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/demand/predict` | POST | Predict demand |
| `/api/demand/train` | POST | Train model |
| `/api/demand/info` | GET | Model status |

## Testing

```bash
# Run unit tests
pytest src/models/demand_forecast/tests/

# Full pipeline test
python test_model.py
```

## Detailed Documentation

For comprehensive documentation, see:
- [API Integration Guide](../../../docs/demand_forecast/demand_forecast_api_integration.md)
- [Technical Architecture](../../../docs/demand_forecast/demand_forecast_architecture.md)
