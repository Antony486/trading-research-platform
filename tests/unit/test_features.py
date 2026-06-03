"""Unit tests for feature engineering"""
import pytest
import pandas as pd
import numpy as np
import sys

sys.path.append('/home/kobia/Desktop/trading-research-platform/trading-research-platform')
from services.ml_service.features.engineer import FeatureEngineer


def test_add_returns():
    df = pd.DataFrame({'close': [100, 102, 101, 103, 105]})
    engineer = FeatureEngineer()
    result = engineer.add_returns(df)
    
    assert 'returns' in result.columns
    assert result['returns'].iloc[0] == 0  # First row should be NaN or 0
    assert not result['returns'].isna().all()


def test_rsi_calculation():
    # Create trending data
    prices = [100 + i for i in range(50)]
    df = pd.DataFrame({'close': prices})
    engineer = FeatureEngineer()
    result = engineer.add_rsi(df, period=14)
    
    assert f'rsi_14' in result.columns
    # RSI should be between 0 and 100
    assert result[f'rsi_14'].between(0, 100).all()


def test_macd_calculation():
    df = pd.DataFrame({'close': np.random.randn(100).cumsum() + 100})
    engineer = FeatureEngineer()
    result = engineer.add_macd(df)
    
    assert 'macd' in result.columns
    assert 'macd_signal' in result.columns
    assert 'macd_histogram' in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
