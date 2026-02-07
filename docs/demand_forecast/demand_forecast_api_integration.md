# Demand Forecast Model - API Integration Guide

This service predicts **item-level demand** based on historical sales data, temporal patterns, and item/place characteristics.

---

## Base URL

| Environment | URL |
|-------------|-----|
| Local (Flask) | `http://127.0.0.1:5001` |
| Node.js Proxy | `http://127.0.0.1:5000/api` |

---

## Endpoints

### `GET /api/demand/info`

Returns the current model status.

**Response (200 OK)**
```json
{
  "status": "loaded",
  "model_type": "xgboost",
  "period": "daily",
  "is_trained": true
}
```

---

### `POST /api/demand/predict`

Predicts demand for a specific item at a given place and date.

**Content-Type:** `application/json`

#### Required JSON Fields

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | integer | Item identifier |
| `place_id` | integer | Store/venue identifier |
| `date` | string | Date in `YYYY-MM-DD` format |

#### Optional JSON Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `period` | string | `"daily"` | Prediction period: `"daily"`, `"weekly"`, `"monthly"` |

#### Example Request (curl)
```bash
curl -X POST http://127.0.0.1:5001/api/demand/predict \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": 123,
    "place_id": 456,
    "date": "2024-03-01",
    "period": "daily"
  }'
```

#### Success Response (200 OK)
```json
{
  "item_id": 123,
  "place_id": 456,
  "date": "2024-03-01",
  "period": "daily",
  "predicted_demand": 15.5,
  "is_cold_start": false,
  "model_type": "xgboost",
  "units": "total daily demand"
}
```

---

### `POST /api/demand/train`

Triggers model training with the configured dataset.

#### Optional JSON Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model_type` | string | `"xgboost"` | Model to train: `"xgboost"`, `"lightgbm"`, `"random_forest"`, `"ensemble"` |
| `period` | string | `"daily"` | Aggregation period |

#### Example Request
```bash
curl -X POST http://127.0.0.1:5001/api/demand/train \
  -H "Content-Type: application/json" \
  -d '{"model_type": "xgboost", "period": "daily"}'
```

#### Success Response (200 OK)
```json
{
  "status": "success",
  "metrics": {
    "xgboost": {
      "mae": 2.60,
      "rmse": 4.12,
      "mape": 18.5,
      "r2": 0.684
    }
  },
  "model_path": "models/demand_forecast_xgboost.pkl",
  "timestamp": "2024-03-01T12:34:56.789Z"
}
```

---

## Response Fields Explained

### Prediction Response

| Field | Description |
|-------|-------------|
| `predicted_demand` | Forecasted demand (units) for the specified period |
| `is_cold_start` | `true` if no historical data exists for this item/place combo (uses fallback) |
| `model_type` | Which model made the prediction |
| `units` | Human-readable description of the prediction units |

### Training Metrics

| Metric | Description |
|--------|-------------|
| `mae` | Mean Absolute Error (lower = better) |
| `rmse` | Root Mean Square Error (penalizes large errors) |
| `mape` | Mean Absolute Percentage Error (%) |
| `r2` | R² score (1.0 = perfect, 0.0 = baseline) |

---

## Model Performance Benchmarks

| Model | MAE | R² | Best For |
|-------|-----|-----|----------|
| **XGBoost** | **2.60** | **0.684** | Production (best accuracy) |
| LightGBM | 2.64 | 0.648 | Fast training |
| Random Forest | 2.81 | 0.651 | Robust baseline |
| Ensemble | ~2.55 | ~0.69 | Highest accuracy (slower) |

---

## Error Handling

### 400 Bad Request
```json
{
  "error": "Missing required fields: ['item_id', 'place_id', 'date']"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error: Model is not trained. Please train the model first."
}
```

---


---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5001` | Flask API port |
| Data path | `./data/Inventory Management` | Location of CSV files |
| Model path | `models/demand_forecast_xgboost.pkl` | Saved model location |

### Starting the API

```bash
# From project root
python -m src.main

# Or directly
python src/main.py
```

---

## Data Requirements

The model requires these CSV files in the data directory:

| File | Required Columns |
|------|------------------|
| `fct_orders.csv` | `id`, `created` (unix timestamp), `place_id`, `status` |
| `fct_order_items.csv` | `order_id`, `item_id`, `quantity`, `price` |
| `dim_items.csv` | `id`, `price` (optional) |
| `dim_menu_items.csv` | `id`, `price`, `status`, `purchases` (optional) |

---

## Production Notes

- Model artifacts are ~5-10MB per trained model
- Cold start uses global averages (no training data needed for prediction)

