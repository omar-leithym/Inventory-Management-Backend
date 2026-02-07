# Demand Forecast Model

Modular, production-ready demand forecasting system.

## 🚀 Features

- **XGBoost (Default)**, **LightGBM**, **Random Forest** model support
- **Ensemble** mode available (averages predictions from all 3 models)
- **Data Leakage Prevention**: Correctly handles historical data for place-level features
- **Cold Start Handling**: Smart fallbacks for new items/places using global averages
- **Multi-Period Support**: Daily, Weekly, and Monthly predictions with automatic scaling
- **Input Validation**: Strict checks for data quality and business rules

## 📦 Architecture

The system is split into focused modules for maintainability:

- `model.py`: **Main Orchestrator**. The single entry point.
- `feature_engineering.py`: Feature creation, lag generation, window statistics.
- `training.py`: Model training, hyperparameter management, cross-validation.
- `prediction.py`: Inference logic, period scaling, ensemble aggregation.
- `validation.py`: Data quality checks and schema enforcement.

## 🛠️ Usage

### Basic Usage

```python
from src.models.demand_forecast import DemandForecastModel

# 1. Initialize
model = DemandForecastModel(
    model_type='xgboost',  # or 'ensemble', 'lightgbm', 'random_forest'
    data_path='./data',
    period='daily'         # 'daily', 'weekly', 'monthly'
)

# 2. Train
# Automatically loads data, creates demand dataset, engineers features, and trains
metrics = model.train_pipeline()
print(f"MAE: {metrics['xgboost']['mae']}")

# 3. Predict
result = model.predict_demand(
    item_id=123,
    place_id=456,
    date='2024-03-01'
)
print(f"Predicted Demand: {result['predicted_demand']}")
```

### Advanced Usage (Custom Data)

```python
# Load your own dataframes
orders, order_items, items, menu_items = load_custom_data()

# Run pipeline with custom data
model.train_pipeline(orders, order_items, items, menu_items)

# Get feature importance
importance_df = model.get_feature_importance()
print(importance_df.head(10))

# Save/Load
model.save('models/my_model.pkl')
loaded_model = DemandForecastModel()
loaded_model.load('models/my_model.pkl')
```

## Key Metrics

For daily demand forecasting on the inventory dataset:

| Model | MAE | R² | Use Case |
|-------|-----|----|----------|
| **XGBoost** | **2.60** | **0.684** | **Best All-Rounder** |
| LightGBM | 2.64 | 0.648 | Fast Training |
| Random Forest | 2.81 | 0.651 | Robust Baseline |


## Testing

Run the included test scripts:

```bash
# Full pipeline test with metrics
python test_model.py

# Train and save a production model
python train_and_save.py
```
