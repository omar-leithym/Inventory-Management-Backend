"""
File: train_demand_model.py
Description: Script to train the demand forecasting model.
Usage: python src/models/train_demand_model.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.demand_forecast_model import DemandForecastModel
import pandas as pd
import argparse


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description='Train demand forecasting model')
    parser.add_argument('--data-path', type=str, 
                       default='data/Inventory Management',
                       help='Path to data directory')
    parser.add_argument('--model-type', type=str, default='ensemble',
                       choices=['xgboost', 'lightgbm', 'random_forest', 'ensemble'],
                       help='Type of model to train')
    parser.add_argument('--period', type=str, default='daily',
                       choices=['daily', 'weekly', 'monthly'],
                       help='Prediction period')
    parser.add_argument('--output-dir', type=str, default='models',
                       help='Directory to save trained model')
    parser.add_argument('--sample-size', type=int, default=None,
                       help='Sample size for training (None = use all data)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Demand Forecasting Model Training")
    print("=" * 60)
    print(f"Data path: {args.data_path}")
    print(f"Model type: {args.model_type}")
    print(f"Period: {args.period}")
    print("=" * 60)
    
    # Initialize model
    model = DemandForecastModel(model_type=args.model_type, data_path=args.data_path)
    
    # Load data
    print("\n[1/5] Loading data...")
    orders, order_items, items, menu_items = model.load_data()
    
    # Create demand dataset
    print(f"\n[2/5] Creating {args.period} demand dataset...")
    demand_df = model.create_demand_dataset(orders, order_items, period=args.period)
    
    # Sample data if specified
    if args.sample_size and len(demand_df) > args.sample_size:
        print(f"Sampling {args.sample_size} records for faster training...")
        demand_df = demand_df.sample(n=args.sample_size, random_state=42)
    
    # Engineer features
    print("\n[3/5] Engineering features...")
    features_df = model.engineer_features(
        demand_df, orders, order_items, items, menu_items
    )
    
    # Prepare features and target
    print("\n[4/5] Preparing features for training...")
    X, y, feature_names = model.prepare_features(features_df)
    
    print(f"Training set size: {len(X)}")
    print(f"Number of features: {len(feature_names)}")
    print(f"Feature names: {feature_names[:10]}..." if len(feature_names) > 10 else f"Feature names: {feature_names}")
    
    # Train model
    print("\n[5/5] Training model...")
    metrics = model.train(X, y, validation_split=0.2)
    
    # Print results
    print("\n" + "=" * 60)
    print("Training Results")
    print("=" * 60)
    for model_name, model_metrics in metrics.items():
        print(f"\n{model_name.upper()}:")
        print(f"  MAE:  {model_metrics['mae']:.2f}")
        print(f"  RMSE: {model_metrics['rmse']:.2f}")
        print(f"  MAPE: {model_metrics['mape']:.2f}%")
        print(f"  R²:   {model_metrics['r2']:.4f}")
    
    # Save model
    os.makedirs(args.output_dir, exist_ok=True)
    model_filename = f"{args.output_dir}/demand_forecast_{args.period}_{args.model_type}.pkl"
    model.save(model_filename)
    
    print(f"\n✓ Model saved to: {model_filename}")
    print("\nTraining complete!")


if __name__ == '__main__':
    main()


