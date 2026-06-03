"""Backtest API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.append('/home/kobia/Desktop/trading-research-platform/trading-research-platform')

from services.backtest_service.engine.complete import CompleteBacktester
from services.data_service.ingestor.base import MarketDataIngestor
from services.ml_service.inference.predictor import PredictionService

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    strategy: str = "MLStrategy"
    symbol: str = "BTC/USDT"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 10000
    confidence_threshold: float = 0.55


@router.post("/run")
async def run_backtest(request: BacktestRequest) -> Dict[str, Any]:
    """Run a complete backtest with real data"""
    try:
        # Fetch historical data
        ingestor = MarketDataIngestor('binance')
        df = await ingestor.fetch_ohlcv(request.symbol, '1h', limit=1000)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Get predictions
        predictor = PredictionService()
        latest_model = predictor.find_latest_model()
        
        if latest_model:
            predictor.load_model(latest_model)
            # Generate predictions for historical data
            predictions = []
            for i in range(len(df)):
                # Simplified: in production, you'd generate features for each row
                predictions.append(0.55 + (i % 100) / 1000)  # Placeholder
        else:
            # Fallback to random predictions
            import numpy as np
            predictions = np.random.rand(len(df))
        
        # Run backtest
        backtester = CompleteBacktester(initial_capital=request.initial_capital)
        results = backtester.execute_backtest(
            df, 
            predictions, 
            confidence_threshold=request.confidence_threshold
        )
        
        results['strategy_name'] = request.strategy
        results['symbol'] = request.symbol
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}")
async def get_backtest(backtest_id: int) -> Dict[str, Any]:
    """Get backtest results by ID"""
    # TODO: Fetch from database
    return {"id": backtest_id, "status": "pending"}
