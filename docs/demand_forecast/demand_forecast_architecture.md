# Demand Forecast Model - Technical Architecture

## Overview

The demand forecast model is a modular, production-ready ML system for predicting item-level demand. It uses gradient boosting (XGBoost/LightGBM) with 40+ engineered features.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DemandForecastModel                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────┐  ┌───────────────┐            │
│  │ FeatureEngineer │  │ ModelTrainer│  │DemandPredictor│            │
│  │   (features)    │  │  (training) │  │ (inference)   │            │
│  └────────┬────────┘  └──────┬──────┘  └───────┬───────┘            │
│           │                  │                 │                     │
│           v                  v                 v                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      DataValidator                              ││
│  │               (validation.py - Data Quality)                    ││
│  └─────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

---

## Module Reference

### `model.py` - Main Orchestrator

The single entry point for all operations.

| Method | Description |
|--------|-------------|
| `train_pipeline()` | Runs full training: load data → create demand dataset → engineer features → train models |
| `predict_demand(item_id, place_id, date)` | Returns demand prediction for a specific item/place/date |
| `save(filepath)` / `load(filepath)` | Persist and restore model artifacts |
| `get_feature_importance()` | Returns DataFrame of feature importance scores |

---

### `feature_engineering.py` - Feature Creation

Creates 40+ features across 5 categories:

#### Temporal Features
| Feature | Description |
|---------|-------------|
| `year`, `month`, `day_of_month` | Basic date components |
| `day_of_week`, `week_of_year` | Day/week identifiers |
| `is_weekend` | Binary weekend flag |
| `is_month_start`, `is_month_end` | Month boundary flags |
| `quarter` | Fiscal quarter |
| `month_sin`, `month_cos` | Cyclical month encoding |
| `day_of_week_sin`, `day_of_week_cos` | Cyclical day encoding |

#### Lag Features
| Feature | Description |
|---------|-------------|
| `demand_lag_1..30` | Demand from 1, 2, 3, 7, 14, 30 days ago |
| `demand_same_dow` | Same day-of-week previous week |

#### Rolling Features
| Feature | Description |
|---------|-------------|
| `demand_rolling_mean_7/14/30` | 7/14/30-day rolling averages |
| `demand_rolling_std_7/14/30` | 7/14/30-day rolling std dev |
| `demand_ema_0.3/0.7` | Exponential moving averages |

#### Place Features
| Feature | Description |
|---------|-------------|
| `place_total_demand` | Total demand at place (prev day) |
| `place_unique_items` | Unique items sold at place |
| `place_demand_rolling_mean_7` | 7-day rolling place demand |
| `item_share_of_place` | Item's share of place demand |

#### Item Features
| Feature | Description |
|---------|-------------|
| `item_base_price` | Base price from items table |
| `menu_price`, `menu_status`, `menu_purchases` | Menu item metadata |

---

### `training.py` - Model Training

Trains and evaluates ML models.

#### Supported Models

| Model | Key | Notes |
|-------|-----|-------|
| XGBoost | `xgboost` | **Default** - Best accuracy |
| LightGBM | `lightgbm` | Fastest training |
| Random Forest | `random_forest` | Robust baseline |
| Ensemble | `ensemble` | Trains all 3, averages predictions |

#### Default Hyperparameters

```python
{
    'xgboost': {
        'n_estimators': 200,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8
    },
    'lightgbm': {
        'n_estimators': 200,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8
    },
    'random_forest': {
        'n_estimators': 100,
        'max_depth': 10
    }
}
```

#### Training Process

1. **Prepare Features**: Extract numeric/categorical columns, encode categoricals
2. **Time Series Split**: Uses `TimeSeriesSplit` to prevent data leakage
3. **Scale Features**: `StandardScaler` normalization
4. **Train Models**: Fits selected model(s)
5. **Calculate Metrics**: MAE, RMSE, MAPE, R²

---

### `prediction.py` - Inference

Handles prediction with ensemble support and cold start fallback.

#### Prediction Flow

```
Input (item_id, place_id, date)
          │
          v
   ┌──────────────┐
   │ Validate     │ → Check inputs are valid
   │ Inputs       │
   └──────┬───────┘
          │
          v
   ┌──────────────┐
   │ Check        │ → Does historical data exist?
   │ Cold Start   │
   └──────┬───────┘
          │
    ┌─────┴─────┐
    │           │
    v           v
 Historical  Cold Start
  Features    Features
    │           │
    └─────┬─────┘
          │
          v
   ┌──────────────┐
   │ Scale +      │ → Apply StandardScaler
   │ Predict      │ → Model inference
   └──────┬───────┘
          │
          v
   ┌──────────────┐
   │ Scale to     │ → daily → weekly → monthly
   │ Period       │
   └──────┬───────┘
          │
          v
    Return Result
```

#### Period Handling (Robust Approach)

The model uses **native period aggregation during training**, not simple linear scaling:

**Training-Time Aggregation:**
```python
# When period='weekly', the model:
# 1. Rolls dates back to start of week
# 2. Sums all demand within each week
# 3. Trains on weekly aggregated data

# When period='monthly', the model:
# 1. Rolls dates to start of month  
# 2. Sums all demand within each month
# 3. Trains on monthly aggregated data
```

| Training Period | What the Model Learns |
|-----------------|----------------------|
| `daily` | Predicts daily demand directly |
| `weekly` | Predicts weekly totals (sum of 7 days) |
| `monthly` | Predicts monthly totals (sum of month) |



---

### `validation.py` - Data Quality

Validates data at multiple stages.

#### Validation Methods

| Method | Checks |
|--------|--------|
| `validate_orders()` | Required columns, timestamps, null place_ids |
| `validate_order_items()` | Required columns, positive quantities, non-negative prices |
| `validate_demand_dataset()` | No future dates, no duplicates, non-negative demand |
| `validate_prediction_inputs()` | Types, date format, valid period |
| `validate_historical_data()` | Cold start detection, minimum history check |

#### Strict Mode

```python
# Raises ValidationError on any error
validator = DataValidator(strict=True)

# Logs warnings, returns report dict
validator = DataValidator(strict=False)
```

---

## Cold Start Handling

For new items/places with no history, the model uses global averages:

```python
global_stats = {
    'avg_demand': 5.0,      # Global average daily demand
    'avg_price': 50.0,      # Global average price
    'avg_place_demand': 100.0  # Global average place demand
}
```

All lag and rolling features are set to global averages instead of zeros.

---

## Data Leakage Prevention

The model correctly handles place-level features to prevent data leakage:

1. **Place stats use previous day's data** (shifted by 1 day)
2. **Target is next-period demand** (shifted by -1)
3. **Time series split for validation** (no random shuffle)

---

## File Structure

```
src/models/demand_forecast/
├── __init__.py          # Package exports
├── model.py             # Main orchestrator (216 lines)
├── feature_engineering.py  # Feature creation (339 lines)
├── training.py          # Model training (262 lines)
├── prediction.py        # Inference logic (262 lines)
├── validation.py        # Data validation (233 lines)
├── README.md            # Quick start guide
└── tests/               # Unit tests
```

---

## Usage Examples

### Basic Training + Prediction

```python
from src.models.demand_forecast import DemandForecastModel

# Initialize
model = DemandForecastModel(
    model_type='xgboost',
    data_path='./data/Inventory Management',
    period='daily'
)

# Train (loads data automatically)
metrics = model.train_pipeline()
print(f"MAE: {metrics['xgboost']['mae']:.2f}")

# Predict
result = model.predict_demand(
    item_id=123,
    place_id=456,
    date='2024-03-01'
)
print(f"Predicted: {result['predicted_demand']:.1f} units")
```

### Save/Load Model

```python
# Save
model.save('models/demand_forecast_xgboost.pkl')

# Load
loaded_model = DemandForecastModel()
loaded_model.load('models/demand_forecast_xgboost.pkl')

# Predict with loaded model
result = loaded_model.predict_demand(123, 456, '2024-03-01')
```

### Custom Hyperparameters

```python
from src.models.demand_forecast import ModelTrainer

trainer = ModelTrainer(
    model_type='xgboost',
    custom_params={
        'xgboost': {
            'n_estimators': 500,
            'max_depth': 8,
            'learning_rate': 0.05
        }
    }
)
```

### Ensemble Mode

```python
model = DemandForecastModel(model_type='ensemble')
metrics = model.train_pipeline()

# metrics contains results for all 3 models:
# metrics['xgboost'], metrics['lightgbm'], metrics['random_forest']
```

---



## Dependencies

```
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
xgboost>=1.5.0
lightgbm>=3.3.0  # Optional
```
