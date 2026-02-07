# Demand Forecast Module

This package provides modular demand forecasting functionality.

## Structure

- `feature_engineering.py` - Feature creation and transformation logic
- `training.py` - Model training and evaluation
- `prediction.py` - Prediction and inference logic
- `validation.py` - Input validation and data quality checks
- `model.py` - Main orchestrator class (slim wrapper)

## Usage

```python
from src.models.demand_forecast import DemandForecastModel

model = DemandForecastModel(data_path="data/")
model.train_pipeline()
predictions = model.predict_demand(item_id=123, place_id=1, date="2024-01-15")
```
