"""Feature Engineering Pipeline"""
import pandas as pd
import numpy as np
from typing import Tuple

class FeatureEngineer:
    """Feature engineering for trading data"""
    
    @staticmethod
    def add_returns(df: pd.DataFrame) -> pd.DataFrame:
        """Add return features"""
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['returns_lag_1'] = df['returns'].shift(1)
        df['returns_lag_2'] = df['returns'].shift(2)
        df['returns_lag_3'] = df['returns'].shift(3)
        return df
    
    @staticmethod
    def add_volatility(df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility features"""
        df['volatility_10'] = df['returns'].rolling(10).std()
        df['volatility_20'] = df['returns'].rolling(20).std()
        df['volatility_50'] = df['returns'].rolling(50).std()
        return df
    
    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add RSI indicator"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        return df
    
    @staticmethod
    def add_macd(df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD indicator"""
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        return df
    
    @staticmethod
    def add_target(df: pd.DataFrame, periods_ahead: int = 5) -> pd.DataFrame:
        """Add binary classification target"""
        future_price = df['close'].shift(-periods_ahead)
        df['target'] = (future_price > df['close']).astype(int)
        return df.dropna()
    
    def create_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Create complete feature set"""
        df = self.add_returns(df)
        df = self.add_volatility(df)
        df = self.add_rsi(df)
        df = self.add_macd(df)
        
        # Drop NaN values
        df = df.dropna()
        
        # Separate features and target
        feature_cols = [col for col in df.columns if col not in ['target', 'timestamp']]
        X = df[feature_cols]
        y = df['target'] if 'target' in df.columns else None
        
        return X, y

if __name__ == "__main__":
    # Test the feature engineer
    import yfinance as yf
    df = yf.download('BTC-USD', period='1mo', interval='1h')
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    
    engineer = FeatureEngineer()
    df = engineer.add_returns(df)
    df = engineer.add_volatility(df)
    df = engineer.add_rsi(df)
    df = engineer.add_macd(df)
    
    print("Feature engineering test:")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
