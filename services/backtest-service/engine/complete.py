"""Complete Production Backtesting Engine"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Single trade record"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_size: float
    direction: str  # 'LONG' or 'SHORT'
    pnl: float
    pnl_percent: float
    exit_reason: str


class CompleteBacktester:
    """Production-grade backtesting engine with realistic modeling"""
    
    def __init__(
        self,
        initial_capital: float = 10000,
        commission: float = 0.001,
        slippage: float = 0.0005,
        risk_per_trade: float = 0.02  # 2% risk per trade
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.risk_per_trade = risk_per_trade
        
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        
    def calculate_position_size(self, capital: float, stop_loss_pct: float) -> float:
        """Calculate position size based on risk management"""
        risk_amount = capital * self.risk_per_trade
        position_size = risk_amount / stop_loss_pct
        return min(position_size, capital)  # Don't exceed available capital
    
    def execute_backtest(
        self,
        data: pd.DataFrame,
        predictions: np.ndarray,
        confidence_threshold: float = 0.55,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04
    ) -> Dict[str, Any]:
        """Execute complete backtest with realistic conditions"""
        
        capital = self.initial_capital
        self.trades = []
        self.equity_curve = [capital]
        
        in_position = False
        entry_price = 0
        entry_time = None
        position_size = 0
        direction = None
        
        for i in range(len(data)):
            current_price = data.iloc[i]['close']
            current_time = data.index[i] if isinstance(data.index, pd.DatetimeIndex) else i
            
            # Generate signal
            signal = predictions[i] if i < len(predictions) else 0.5
            should_buy = signal > confidence_threshold
            
            # Exit conditions if in position
            if in_position:
                pnl_pct = (current_price - entry_price) / entry_price
                if direction == 'SHORT':
                    pnl_pct = (entry_price - current_price) / entry_price
                
                exit_trade = False
                exit_reason = ""
                
                # Stop loss
                if pnl_pct <= -stop_loss_pct:
                    exit_trade = True
                    exit_reason = "stop_loss"
                # Take profit
                elif pnl_pct >= take_profit_pct:
                    exit_trade = True
                    exit_reason = "take_profit"
                # Exit on opposite signal
                elif not should_buy:
                    exit_trade = True
                    exit_reason = "signal_reverse"
                
                if exit_trade:
                    # Close position
                    exit_price = current_price
                    pnl = position_size * pnl_pct
                    capital += pnl
                    
                    self.trades.append(Trade(
                        entry_time=entry_time,
                        exit_time=current_time,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position_size=position_size,
                        direction=direction,
                        pnl=pnl,
                        pnl_percent=pnl_pct,
                        exit_reason=exit_reason
                    ))
                    
                    in_position = False
                    logger.debug(f"Closed {direction} position: PnL={pnl:.2f} ({pnl_pct:.2%}) - {exit_reason}")
            
            # Enter new position
            if not in_position and should_buy:
                direction = 'LONG'
                entry_price = current_price * (1 + self.slippage)  # Apply slippage
                entry_time = current_time
                position_size = self.calculate_position_size(capital, stop_loss_pct)
                in_position = True
                logger.debug(f"Opened LONG position at {entry_price:.2f} with size {position_size:.2f}")
            
            # Update equity curve
            if in_position:
                unrealized_pnl = position_size * ((current_price - entry_price) / entry_price)
                current_equity = capital + unrealized_pnl
            else:
                current_equity = capital
            
            self.equity_curve.append(current_equity)
        
        # Close any open position at the end
        if in_position:
            final_price = data.iloc[-1]['close']
            pnl = position_size * ((final_price - entry_price) / entry_price)
            capital += pnl
            self.trades.append(Trade(
                entry_time=entry_time,
                exit_time=data.index[-1],
                entry_price=entry_price,
                exit_price=final_price,
                position_size=position_size,
                direction=direction,
                pnl=pnl,
                pnl_percent=(final_price - entry_price) / entry_price,
                exit_reason="end_of_period"
            ))
        
        # Calculate metrics
        metrics = self.calculate_metrics(capital)
        
        return {
            'metrics': metrics,
            'trades': [asdict(t) for t in self.trades],
            'equity_curve': self.equity_curve,
            'final_capital': capital,
            'total_return': (capital - self.initial_capital) / self.initial_capital,
            'num_trades': len(self.trades)
        }
    
    def calculate_metrics(self, final_capital: float) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return {}
        
        # Trade statistics
        returns = [t.pnl_percent for t in self.trades]
        winning_trades = [r for r in returns if r > 0]
        losing_trades = [r for r in returns if r < 0]
        
        # Calculate metrics
        equity_series = pd.Series(self.equity_curve)
        daily_returns = equity_series.pct_change().dropna()
        
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        profit_factor = abs(sum(winning_trades) / sum(losing_trades)) if sum(losing_trades) != 0 else 0
        
        # Risk metrics
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
        
        # Max drawdown
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Calmar ratio
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': (1 + total_return) ** (252 / len(self.equity_curve)) - 1,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'num_trades': len(self.trades),
            'avg_holding_period': np.mean([(t.exit_time - t.entry_time).days for t in self.trades]) if self.trades else 0
        }


# Test the backtester
if __name__ == "__main__":
    # Generate sample data
    dates = pd.date_range('2024-01-01', periods=1000, freq='H')
    prices = 50000 + np.cumsum(np.random.randn(1000) * 100)
    data = pd.DataFrame({'close': prices}, index=dates)
    
    # Generate random predictions
    predictions = np.random.rand(1000)
    
    backtester = CompleteBacktester()
    results = backtester.execute_backtest(data, predictions)
    
    print("\n=== BACKTEST RESULTS ===")
    for key, value in results['metrics'].items():
        print(f"{key}: {value:.4f}")
    print(f"Total trades: {results['num_trades']}")
    print(f"Final capital: ${results['final_capital']:.2f}")
