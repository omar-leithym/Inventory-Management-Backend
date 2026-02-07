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

<img width="1112" height="849" alt="image" src="https://github.com/user-attachments/assets/98a9cd1c-7620-4ff7-a779-2a81ba2b464a" />


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
curl http://localhost:8000/health        # Promotion API
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

##**Business Value** (Dan)
Value to Business:
The model provides data based demand forecasting for items historically used by the establishment, aiding in more efficient decision making and inventory management by the owner. The system accounts for any margins of error and minimises risk by incorporating the use of MAPE ( Mean Absolute Percentage Error), that reflects as a confidence metric allowing for a cushioning strategy. This ensures that inventory levels are always optimal and directly improves profitability by tracking reduced waste and avoiding inventory holding cost and spoilage.
The system operates based on an automated perpetual stock counting system that creates an accurate and timely log of on hand stock and deducts any sold/ used items. It also updates stock count in real time, eliminating manual counting that reduces the average time spent on planning inventory management.Overall, relying on the model reduces operational costs and increases efficiency. By timely tracking the usage of items, the owner gains timely insight and reports on sale trends, increased demand on a specifc item/ set of items, their performance, and adjusted units forecasted to be ordered, to fit changing demand. This results in faster and more proactive decision making, and maximising operational control and profitability.
The model is dynamic, flexible and user friendly with options on forecasting ranging from daily , weekly , to monthly to allow for both short term operational adjustments and long term strategic planning. To keep the user timely informed, the system uses alerts categorised into “medium” “high” and “critical” to signify inventory depletion, acting as a ROP and lead time tracker that satisfies the users input baseline. This reduces the risk of stockouts and lost sales. As the model is intuitive and adaptable, it is fit to aid establishments in all sizes and is able to adjust to scaled operations and expansion, ensuring continued, long term value to the user.

## Key Solutions

**How do we accurately predict daily, weekly, and monthly demand?**
> The system utilizes advanced **XGBoost and Ensemble models** trained on 40+ engineered features (temporal patterns, lag features, rolling statistics) to forecast demand with high accuracy (R² ~0.68), supporting native daily, weekly, and monthly aggregation.

**What prep quantities should kitchens prepare to minimize waste?**
> By providing precise **item-level demand forecasts**, the system informs exact prep quantities to facilitate "just-in-time" preparation. It also calculates error margins to help kitchens find the optimal balance between product availability and waste reduction.

**How can we prioritize inventory based on expiration dates?**
> The system tracks real-time stock levels and leverages the **Discount Prediction Model**, which takes "window hours" (remaining shelf life) as a key input to identify and prioritize items that need to be sold urgently.

**What promotions or bundles can move near-expired items profitably?**
> The **LightGBM-based Discount Recommendation Model** dynamically calculates the optimal discount percentage required to clear specific inventory within a set time window, maximizing revenue recovery while ensuring items are sold before expiration.

**How do external factors (weather, holidays, weekends) impact sales?**
> The demand model incorporates robust **temporal feature engineering**, including day-of-week, month, weekend flags, and holiday indicators, to automatically adjust forecasts for cyclical trends and special events.

## Team

- **Omar Leithy** - Full Stack Developer
  - Implemented secure user authentication, database design, and comprehensive sale/restock logging systems.
  - Developed critical backend infrastructure and handled seamless frontend integration.

- **Samar Ashraf** - Full Stack Developer
  - Engineered core business calculations for predictions, error margins, and alert systems.
  - led frontend-backend integration and rigorous API testing to ensure robust functionality.

- **Ahmed Abdeen** - Frontend Engineer & UI/UX Designer
  - Designed the complete user interface and user experience flow.
  - Built the responsive frontend application using modern React practices.

- **Ahmed Fawzy** - ML Engineer (Discount Prediction)
  - Developed the LightGBM-based discount prediction model for dynamic pricing.
  - Implemented the Flask API routes to serve model inference in real-time.

- **Islam Abdeen** - ML Engineer (Demand Forecast)
  - Architected the demand forecasting models using XGBoost and ensemble techniques.
  - Created the API infrastructure for demand prediction and model training.

- **Dan** - Product Manager & Designer
  - Provided strategic business direction and product design oversight.
  - Managed the project lifecycle as business consultant and product lead.

  
## License

ISC
