# Inventory Management Backend

AI-powered inventory management system with demand forecasting and discount recommendations.

## Features

- **Demand Forecasting** - XGBoost-based ML model predicting item-level demand
- **Discount Recommendations** - LightGBM model for dynamic pricing to reduce waste
- **Real-time Inventory** - Track stock levels, orders, and menu items
- **User Authentication** - JWT-based auth with role management
- **RESTful APIs** - Node.js + Python Flask microservices

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│                         Port: 5173                              │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Node.js API (Express)                         │
│                         Port: 5000                              │
│  • Authentication   • Orders   • Inventory   • Menu Items       │
└──────────┬────────────────────────────────┬─────────────────────┘
           │                                │
           ▼                                ▼
┌────────────────────────┐    ┌────────────────────────────────────┐
│  Discount Prediction   │    │     Demand Forecast API            │
│   (Flask) Port: 8000   │    │      (Flask) Port: 5001            │
│   • LightGBM Model     │    │   • XGBoost/LightGBM/RF/Ensemble   │
└────────────────────────┘    └────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- MongoDB

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/your-repo/Inventory-Management-Backend.git
cd Inventory-Management-Backend

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Required variables:
# MONGO_URI=mongodb://localhost:27017/inventory
# JWT_SECRET=your-secret-key
# PORT=5000
```

### 3. Start Services

```bash
# Terminal 1: Start Node.js server (also spawns discount API)
node src/server.js

# Terminal 2: Start Demand Forecast API
python src/main.py

# Terminal 3: Start Frontend (optional)
cd Frontend && npm run dev
```

### 4. Verify

```bash
# Health checks
curl http://localhost:5000/api/health    # Node.js API
curl http://localhost:8000/health        # Discount API
curl http://localhost:5001/api/health    # Demand Forecast API
```

## API Endpoints

### Node.js API (Port 5000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User login |
| `/api/auth/register` | POST | User registration |
| `/api/orders` | GET/POST | Order management |
| `/api/inventory` | GET/POST | Inventory items |
| `/api/menu-items` | GET/POST | Menu management |

### Demand Forecast API (Port 5001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/demand/predict` | POST | Predict demand for item/place/date |
| `/api/demand/train` | POST | Train forecast model |
| `/api/demand/info` | GET | Model status |

### Discount API (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/discount` | POST | Get discount recommendation |
| `/health` | GET | API health check |

## Project Structure

```
├── src/
│   ├── server.js              # Node.js entry point
│   ├── main.py                # Python API entry point
│   ├── api/                   # Flask API routes
│   ├── controllers/           # Express controllers
│   ├── models/                # Data models & ML models
│   │   ├── demand_forecast/   # Demand prediction (XGBoost)
│   │   └── *.py               # Mongoose schemas
│   ├── routes/                # Express routes
│   └── services/              # Business logic
├── Frontend/                  # React + Vite app
├── docs/                      # Documentation
│   ├── demand_forecast/       # ML model docs
│   └── prediction_model/      # Discount model docs
├── tests/                     # Test suites
└── requirements.txt           # Python dependencies
```

## ML Models

### Demand Forecast

- **Algorithm**: XGBoost (default), LightGBM, Random Forest, Ensemble
- **Features**: 40+ (temporal, lag, rolling, place, item)
- **Metrics**: MAE 2.60, R² 0.684

[Detailed Documentation](docs/demand_forecast/demand_forecast_architecture.md)

### Discount Recommendation

- **Algorithm**: LightGBM
- **Output**: Recommended discount % to clear inventory
- **Inputs**: stock level, expected demand, time window

[API Documentation](docs/prediction_model/prediction_model_api_integration.md)

## Testing

```bash
# Python tests
pytest tests/

# API tests
python test_api.py

# Model tests
python test_model.py
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, Material UI, Recharts |
| **Node.js API** | Express 5, Mongoose, JWT |
| **Python APIs** | Flask, Pandas, Scikit-learn |
| **ML Models** | XGBoost, LightGBM |
| **Database** | MongoDB |

## License

ISC
