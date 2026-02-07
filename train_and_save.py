"""Train and save the demand forecast model."""
import sys
sys.path.insert(0, '/Users/mohamedemara/Desktop/dih/DIH-X-AUC-Hackathon-main')

import warnings
warnings.filterwarnings('ignore')

from src.models.demand_forecast import DemandForecastModel

print("Training demand forecast model (XGBoost)...")
print("=" * 50)

# Initialize with XGBoost as default
model = DemandForecastModel(
    model_type='xgboost',
    data_path='./data/Inventory Management',
    period='daily'
)

# Run full pipeline (load, engineer, train)
metrics = model.train_pipeline()

print("=" * 50)
print(f"XGBoost MAE: {metrics['xgboost']['mae']:.2f}")
print(f"XGBoost R²: {metrics['xgboost']['r2']:.3f}")

# Save the trained model
model.save('models/demand_forecast_xgboost.pkl')
print("=" * 50)
print("Model saved to: models/demand_forecast_xgboost.pkl")
