"""Complete ML Training Pipeline"""
import asyncio
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import mlflow
import mlflow.sklearn
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to path
import sys
sys.path.append('/home/kobia/Desktop/trading-research-platform/trading-research-platform')
from services.ml_service.features.engineer import FeatureEngineer
from services.data_service.ingestor.base import MarketDataIngestor


class ModelTrainer:
    """Complete model training pipeline with versioning"""
    
    def __init__(self, model_type: str = 'xgboost'):
        self.model_type = model_type
        self.models_dir = Path(__file__).parent.parent / "models"
        self.models_dir.mkdir(exist_ok=True)
        self.feature_engineer = FeatureEngineer()
        
        # Configure MLflow
        mlflow.set_tracking_uri("file://" + str(Path(__file__).parent.parent / "mlruns"))
        mlflow.set_experiment("trading-research")
        
    async def fetch_training_data(
        self, 
        symbol: str = 'BTC/USDT', 
        timeframe: str = '1h', 
        days: int = 180
    ) -> pd.DataFrame:
        """Fetch historical data for training"""
        ingestor = MarketDataIngestor('binance')
        
        # Calculate number of candles needed
        hours_per_day = 24 if timeframe == '1h' else 6 if timeframe == '4h' else 1
        limit = days * hours_per_day
        
        df = await ingestor.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        if df.empty:
            logger.error(f"No data fetched for {symbol}")
            raise ValueError("No data available")
        
        logger.info(f"Fetched {len(df)} candles for training")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for training"""
        # Add features
        df = self.feature_engineer.add_returns(df)
        df = self.feature_engineer.add_volatility(df)
        df = self.feature_engineer.add_rsi(df)
        df = self.feature_engineer.add_macd(df)
        df = self.feature_engineer.add_target(df, periods_ahead=5)
        
        # Drop NaN values
        df = df.dropna()
        
        # Define feature columns
        feature_cols = [col for col in df.columns if col not in ['target', 'timestamp', 'symbol', 'timeframe']]
        feature_cols = [col for col in feature_cols if df[col].dtype in ['float64', 'int64']]
        
        X = df[feature_cols]
        y = df['target']
        
        logger.info(f"Features shape: {X.shape}, Target shape: {y.shape}")
        logger.info(f"Feature columns: {feature_cols[:10]}...")
        logger.info(f"Target distribution:\n{y.value_counts(normalize=True)}")
        
        return X, y
    
    def train_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series) -> XGBClassifier:
        """Train XGBoost model with hyperparameter tuning"""
        logger.info("Training XGBoost model...")
        
        # Define hyperparameter grid
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [4, 6, 8],
            'learning_rate': [0.01, 0.05, 0.1],
            'subsample': [0.7, 0.8, 0.9],
            'colsample_bytree': [0.7, 0.8, 0.9]
        }
        
        # Use time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        base_model = XGBClassifier(
            objective='binary:logistic',
            eval_metric='logloss',
            random_state=42,
            n_jobs=-1
        )
        
        # Grid search with limited params for speed (or full for production)
        grid_search = GridSearchCV(
            base_model, 
            param_grid, 
            cv=tscv, 
            scoring='roc_auc',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best CV score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def train_random_forest(self, X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
        """Train Random Forest model"""
        logger.info("Training Random Forest model...")
        
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [6, 8, 10],
            'min_samples_split': [5, 10],
            'min_samples_leaf': [2, 4]
        }
        
        tscv = TimeSeriesSplit(n_splits=3)
        
        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
        
        grid_search = GridSearchCV(
            base_model, 
            param_grid, 
            cv=tscv, 
            scoring='roc_auc',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best CV score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def evaluate_model(
        self, 
        model, 
        X_test: pd.DataFrame, 
        y_test: pd.Series
    ) -> Dict[str, float]:
        """Comprehensive model evaluation"""
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
        }
        
        logger.info("Model Evaluation:")
        for name, value in metrics.items():
            logger.info(f"  {name}: {value:.4f}")
        
        return metrics
    
    def save_model(self, model, metrics: Dict[str, float], symbol: str) -> str:
        """Save model with MLflow tracking"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = self.models_dir / f"{self.model_type}_{symbol}_{timestamp}.pkl"
        
        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Log with MLflow
        with mlflow.start_run() as run:
            mlflow.log_params(model.get_params())
            mlflow.log_metrics(metrics)
            mlflow.log_artifact(str(model_path))
            mlflow.set_tag("model_type", self.model_type)
            mlflow.set_tag("symbol", symbol)
            
            model_uri = f"runs:/{run.info.run_id}/model"
            mlflow.sklearn.log_model(model, "model")
        
        logger.info(f"Model saved to: {model_path}")
        logger.info(f"MLflow run ID: {run.info.run_id}")
        
        return str(model_path)
    
    async def run_full_training(
        self, 
        symbol: str = 'BTC/USDT',
        timeframe: str = '1h',
        days: int = 180,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """Run complete training pipeline"""
        logger.info(f"Starting full training pipeline for {symbol}")
        
        # 1. Fetch data
        df = await self.fetch_training_data(symbol, timeframe, days)
        
        # 2. Prepare features
        X, y = self.prepare_features(df)
        
        # 3. Split data (time-based)
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # 4. Train model
        if self.model_type == 'xgboost':
            model = self.train_xgboost(X_train, y_train)
        elif self.model_type == 'random_forest':
            model = self.train_random_forest(X_train, y_train)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # 5. Evaluate model
        metrics = self.evaluate_model(model, X_test, y_test)
        
        # 6. Save model
        model_path = self.save_model(model, metrics, symbol)
        
        return {
            'model_path': model_path,
            'metrics': metrics,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'model_type': self.model_type,
            'symbol': symbol,
            'timeframe': timeframe,
            'feature_columns': list(X.columns)
        }


async def main():
    """Run training from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ML model')
    parser.add_argument('--model', type=str, default='xgboost', choices=['xgboost', 'random_forest'])
    parser.add_argument('--symbol', type=str, default='BTC/USDT')
    parser.add_argument('--timeframe', type=str, default='1h')
    parser.add_argument('--days', type=int, default=180)
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(model_type=args.model)
    result = await trainer.run_full_training(
        symbol=args.symbol,
        timeframe=args.timeframe,
        days=args.days
    )
    
    print("\n" + "="*50)
    print("TRAINING COMPLETE!")
    print("="*50)
    print(f"Model: {result['model_path']}")
    print(f"Metrics: {result['metrics']}")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
