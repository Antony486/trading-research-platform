"""Real-time Prediction Service"""
import asyncio
import pickle
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent to path
import sys
sys.path.append('/home/kobia/Desktop/trading-research-platform/trading-research-platform')
from services.ml_service.features.engineer import FeatureEngineer
from services.data_service.ingestor.base import MarketDataIngestor


class PredictionService:
    """Real-time prediction service with model management"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.model_path = model_path
        self.feature_columns = None
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str):
        """Load trained model from disk"""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info(f"Model loaded from {model_path}")
        
        # Infer feature columns from model if available
        if hasattr(self.model, 'feature_names_in_'):
            self.feature_columns = list(self.model.feature_names_in_)
    
    def find_latest_model(self, model_type: str = 'xgboost') -> Optional[str]:
        """Find the latest trained model"""
        models_dir = Path(__file__).parent.parent / "models"
        models = list(models_dir.glob(f"{model_type}_*.pkl"))
        
        if not models:
            logger.warning("No models found")
            return None
        
        latest = max(models, key=lambda p: p.stat().st_ctime)
        logger.info(f"Found latest model: {latest}")
        return str(latest)
    
    async def predict_from_live_data(self, symbol: str = 'BTC/USDT') -> Dict[str, Any]:
        """Make prediction using live market data"""
        if self.model is None:
            latest_model = self.find_latest_model()
            if latest_model:
                self.load_model(latest_model)
            else:
                raise ValueError("No model available for prediction")
        
        # Fetch latest data
        ingestor = MarketDataIngestor('binance')
        df = await ingestor.fetch_ohlcv(symbol, '1h', limit=100)
        
        if df.empty:
            return {'error': 'No data available'}
        
        # Engineer features
        df = self.feature_engineer.add_returns(df)
        df = self.feature_engineer.add_volatility(df)
        df = self.feature_engineer.add_rsi(df)
        df = self.feature_engineer.add_macd(df)
        
        # Get latest row for prediction
        latest_features = df.iloc[-1:].copy()
        
        # Align with model's expected features
        if self.feature_columns:
            missing_cols = set(self.feature_columns) - set(latest_features.columns)
            for col in missing_cols:
                latest_features[col] = 0
            latest_features = latest_features[self.feature_columns]
        
        # Make prediction
        proba = self.model.predict_proba(latest_features)[0, 1]
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'probability_up': float(proba),
            'probability_down': 1 - float(proba),
            'confidence': abs(proba - 0.5) * 2,  # Scale confidence from 0-1
            'prediction': 'UP' if proba > 0.5 else 'DOWN',
            'current_price': float(df.iloc[-1]['close'])
        }


async def main():
    """Test prediction service"""
    service = PredictionService()
    
    # Find and load latest model
    latest = service.find_latest_model()
    if latest:
        service.load_model(latest)
        
        # Make prediction
        result = await service.predict_from_live_data('BTC/USDT')
        print("\n=== PREDICTION RESULT ===")
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print("No model found. Run training first:")
        print("  python services/ml-service/training/trainer.py --symbol BTC/USDT --days 180")


if __name__ == "__main__":
    asyncio.run(main())
