# Demand Forecast API

This module provides a REST API for the demand forecasting system.

## Endpoints

### 1. Predict Demand

Get a demand forecast for a specific item at a specific place and date.

- **URL**: `/api/demand/predict`
- **Method**: `POST`
- **Auth**: None (for now)

#### Request Body
```json
{
    "item_id": 123,       // Required: Item ID (integer)
    "place_id": 456,      // Required: Place ID (integer)
    "date": "2024-03-01", // Required: Date (YYYY-MM-DD)
    "period": "daily"     // Optional: 'daily', 'weekly', 'monthly' (default: 'daily')
}
```

#### Success Response (200 OK)
```json
{
    "date": "2024-03-01",
    "is_cold_start": true,
    "item_id": 123,
    "model_type": "xgboost",
    "period": "daily",
    "place_id": 456,
    "predicted_demand": 6.02,
    "units": "total daily demand"
}
```

#### Error Response (400 Bad Request)
```json
{
    "error": "Missing required fields: ['place_id']"
}
```

---

### 2. Trigger Training

Trigger the model training pipeline.

- **URL**: `/api/demand/train`
- **Method**: `POST`

#### Request Body (Optional)
```json
{
    "model_type": "xgboost", // Default: 'xgboost'
    "period": "daily"        // Default: 'daily'
}
```

#### Success Response (200 OK)
```json
{
    "status": "success",
    "metrics": {
        "xgboost": {
            "mae": 2.63,
            "r2": 0.646
        }
    },
    "model_path": "models/demand_forecast_xgboost.pkl",
    "timestamp": "2024-02-07T15:30:00"
}
```

---

### 3. Model Info

Get current model status.

- **URL**: `/api/demand/info`
- **Method**: `GET`

#### Success Response (200 OK)
```json
{
    "status": "loaded",
    "model_type": "xgboost",
    "period": "daily",
    "is_trained": true
}
```

## Running the Server

```bash
python src/main.py
```
