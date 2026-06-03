"""Database integration for predictions and backtests"""
import asyncpg
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Async database manager for PostgreSQL/TimescaleDB"""
    
    def __init__(self):
        self.pool = None
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://admin:trading123@localhost:5432/trading_research')
    
    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("Connected to database")
            await self.create_tables()
    
    async def create_tables(self):
        """Create necessary tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Predictions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    probability_up FLOAT,
                    probability_down FLOAT,
                    confidence FLOAT,
                    prediction TEXT,
                    current_price FLOAT,
                    model_version TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Backtest results table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id SERIAL PRIMARY KEY,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    start_date TIMESTAMPTZ,
                    end_date TIMESTAMPTZ,
                    metrics JSONB,
                    trades JSONB,
                    equity_curve JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Models table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trained_models (
                    id SERIAL PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    model_path TEXT,
                    metrics JSONB,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            logger.info("Tables created/verified")
    
    async def save_prediction(self, prediction: Dict[str, Any]) -> int:
        """Save a prediction to database"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO predictions (symbol, timestamp, probability_up, probability_down, 
                                        confidence, prediction, current_price)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, 
                prediction['symbol'],
                datetime.fromisoformat(prediction['timestamp']),
                prediction['probability_up'],
                prediction['probability_down'],
                prediction['confidence'],
                prediction['prediction'],
                prediction['current_price']
            )
            logger.info(f"Saved prediction {row['id']} for {prediction['symbol']}")
            return row['id']
    
    async def save_backtest(self, backtest_result: Dict[str, Any]) -> int:
        """Save backtest results to database"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO backtest_results (strategy_name, symbol, metrics, trades, equity_curve)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """,
                backtest_result.get('strategy_name', 'MLStrategy'),
                backtest_result.get('symbol', 'BTC/USDT'),
                json.dumps(backtest_result.get('metrics', {})),
                json.dumps(backtest_result.get('trades', [])),
                json.dumps(backtest_result.get('equity_curve', []))
            )
            logger.info(f"Saved backtest {row['id']}")
            return row['id']
    
    async def get_recent_predictions(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent predictions for a symbol"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM predictions 
                WHERE symbol = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            """, symbol, limit)
            return [dict(row) for row in rows]
    
    async def close(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")


# Global instance
db_manager = DatabaseManager()


async def init_db():
    """Initialize database connection"""
    await db_manager.connect()
    return db_manager
