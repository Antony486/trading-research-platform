"""Market Data Ingestion Service"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

import ccxt
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataIngestor:
    """Ingests market data from exchanges"""
    
    def __init__(self, exchange_id: str = 'binance'):
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            'rateLimit': 1200,
            'enableRateLimit': True,
        })
        logger.info(f"Initialized {exchange_id} ingestor")
    
    async def fetch_ohlcv(self, symbol: str = 'BTC/USDT', timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV candlestick data"""
        try:
            data = await asyncio.to_thread(
                self.exchange.fetch_ohlcv, symbol, timeframe, None, limit
            )
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            logger.info(f"Fetched {len(df)} candles for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    async def get_ticker(self, symbol: str = 'BTC/USDT') -> Dict[str, Any]:
        """Get current ticker price"""
        try:
            ticker = await asyncio.to_thread(self.exchange.fetch_ticker, symbol)
            return {
                'symbol': symbol,
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'last': ticker.get('last'),
                'volume': ticker.get('quoteVolume'),
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            return {}

async def main():
    """Main entry point"""
    ingestor = MarketDataIngestor('binance')
    
    # Fetch some data
    df = await ingestor.fetch_ohlcv('BTC/USDT', '1h', 100)
    print(f"Fetched {len(df)} candles")
    print(df.head())
    
    # Get current price
    ticker = await ingestor.get_ticker('BTC/USDT')
    print(f"Current BTC price: ${ticker.get('last', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
