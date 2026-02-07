"""
Test script for demand forecasting model.
Runs training and prediction, outputs metrics.
"""
import sys
sys.path.insert(0, '/Users/mohamedemara/Desktop/dih/DIH-X-AUC-Hackathon-main')

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Use the original model
from src.models.demand_forecast_model import DemandForecastModel

print("=" * 70)
print("DEMAND FORECAST MODEL - TRAINING & PREDICTION TEST")
print("=" * 70)

# Initialize model
data_path = "./data/Inventory Management"
model = DemandForecastModel(model_type='xgboost', data_path=data_path, period='daily')

print("\n1. LOADING DATA...")
try:
    orders, order_items, items, menu_items = model.load_data()
    print(f"   Orders: {len(orders):,} rows")
    print(f"   Order Items: {len(order_items):,} rows")
    print(f"   Items: {len(items):,} rows")
    print(f"   Menu Items: {len(menu_items):,} rows")
except Exception as e:
    print(f"   Error loading data: {e}")
    sys.exit(1)

print("\n2. CREATING DEMAND DATASET...")
try:
    demand_df = model.create_demand_dataset(orders, order_items, period='daily')
    print(f"   Demand dataset: {len(demand_df):,} records")
    print(f"   Date range: {demand_df['date'].min()} to {demand_df['date'].max()}")
    print(f"   Unique items: {demand_df['item_id'].nunique()}")
    print(f"   Unique places: {demand_df['place_id'].nunique()}")
except Exception as e:
    print(f"   Error creating demand dataset: {e}")
    sys.exit(1)

print("\n3. ENGINEERING FEATURES...")
try:
    feature_df = model.engineer_features(demand_df, orders, order_items, items, menu_items)
    print(f"   Feature dataset: {len(feature_df):,} records")
    print(f"   Number of features: {len(feature_df.columns)}")
except Exception as e:
    print(f"   Error engineering features: {e}")
    sys.exit(1)

print("\n4. PREPARING FEATURES FOR TRAINING...")
try:
    X, y, feature_names = model.prepare_features(feature_df)
    print(f"   Training samples: {len(X):,}")
    print(f"   Feature count: {len(feature_names)}")
except Exception as e:
    print(f"   Error preparing features: {e}")
    sys.exit(1)

print("\n5. TRAINING MODELS...")
print("-" * 70)
try:
    metrics = model.train(X, y)
    print("-" * 70)
except Exception as e:
    print(f"   Error training: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n6. MODEL METRICS")
print("=" * 70)
print(f"{'Model':<20} {'MAE':>10} {'RMSE':>10} {'MAPE (%)':>10} {'R2':>10}")
print("-" * 70)
for model_name, model_metrics in metrics.items():
    print(f"{model_name:<20} {model_metrics['mae']:>10.2f} {model_metrics['rmse']:>10.2f} {model_metrics['mape']:>10.1f} {model_metrics['r2']:>10.3f}")
print("=" * 70)

# Find best model
best_model = min(metrics.items(), key=lambda x: x[1]['mae'])
print(f"\nBest model (by MAE): {best_model[0]} with MAE = {best_model[1]['mae']:.2f}")

print("\n7. SAMPLE PREDICTIONS...")
print("-" * 70)
# Get a sample item and place for prediction
sample_items = demand_df['item_id'].unique()[:3]
sample_place = demand_df['place_id'].iloc[0]
sample_date = "2024-01-15"

for item_id in sample_items:
    try:
        prediction = model.predict_demand(
            item_id=int(item_id), 
            place_id=int(sample_place), 
            date=sample_date,
            historical_data=demand_df,
            period='daily'
        )
        print(f"Item {item_id} at Place {sample_place}: {prediction['predicted_demand']:.1f} units/day")
    except Exception as e:
        print(f"Item {item_id}: Error - {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
