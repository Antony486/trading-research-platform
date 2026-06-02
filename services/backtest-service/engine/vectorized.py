"""Vectorized Backtesting Engine"""
import pandas as pd
import numpy as np
from typing import Dict, Any

class VectorizedBacktester:
    """High-performance vectorized backtesting engine"""
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
    
    def run(self, data: pd.DataFrame, predictions: np.ndarray, threshold: float = 0.55) -> Dict[str, Any]:
        """Run backtest with predictions"""
        # Generate signals
        signals = np.where(predictions > threshold, 1, 0)
        
        # Calculate returns
        price_returns = data['close'].pct_change()
        strategy_returns = signals * price_returns
        
        # Apply commission
        trades = np.diff(signals, prepend=0)
        commission_cost = np.abs(trades) * self.commission
        strategy_returns = strategy_returns - commission_cost
        
        # Calculate equity curve
        equity = self.initial_capital * (1 + strategy_returns).cumprod()
        
        # Calculate metrics
        total_return = (equity.iloc[-1] - self.initial_capital) / self.initial_capital
        sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252) if strategy_returns.std() > 0 else 0
        win_rate = (strategy_returns[strategy_returns > 0].count() / strategy_returns[strategy_returns != 0].count()) if strategy_returns[strategy_returns != 0].count() > 0 else 0
        
        # Calculate max drawdown
        rolling_max = equity.expanding().max()
        drawdown = (equity - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        return {
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe),
            'win_rate': float(win_rate),
            'max_drawdown': float(max_drawdown),
            'final_equity': float(equity.iloc[-1]),
            'total_trades': int((trades != 0).sum())
        }

if __name__ == "__main__":
    # Test the backtester
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'close': 100 + np.cumsum(np.random.randn(100) * 2)
    }, index=dates)
    
    predictions = np.random.rand(100)
    
    backtester = VectorizedBacktester()
    results = backtester.run(data, predictions)
    
    print("Backtest Results:")
    for key, value in results.items():
        print(f"  {key}: {value:.4f}")
