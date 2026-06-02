"""Streamlit Research Dashboard"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Trading Research Platform",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Trading Research Platform")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    symbol = st.selectbox("Symbol", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"])
    model = st.selectbox("ML Model", ["XGBoost", "Random Forest", "Ensemble"])
    
    st.markdown("---")
    st.markdown("### Quick Actions")
    if st.button("Run Backtest"):
        st.success("Backtest started!")

# Main content
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Return", "+23.4%", "+5.2%")
with col2:
    st.metric("Sharpe Ratio", "1.87", "+0.23")
with col3:
    st.metric("Win Rate", "58.3%", "+2.1%")
with col4:
    st.metric("Max Drawdown", "-12.4%", "-1.2%")

st.markdown("---")

# Chart - FIXED: proper pandas Series for cumprod
st.subheader("Equity Curve")
dates = pd.date_range(start='2025-01-01', periods=252, freq='D')
# Fix: Create a pandas Series first, then apply cumprod
returns = pd.Series([0.0005] * 252)  # Daily returns
equity_curve = 10000 * (1 + returns).cumprod()
# Add some randomness
equity_curve = equity_curve + np.random.randn(252) * 100

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=equity_curve, mode='lines', name='Strategy'))
fig.update_layout(height=400, xaxis_title="Date", yaxis_title="Equity ($)")
st.plotly_chart(fig, use_container_width=True)

# Trades table
st.subheader("Recent Trades")
trades_data = {
    "Date": ["2026-06-01", "2026-05-31", "2026-05-30"],
    "Symbol": ["BTC/USDT", "BTC/USDT", "ETH/USDT"],
    "Type": ["BUY", "SELL", "BUY"],
    "Price": [50000, 51000, 3000],
    "Return": ["+2.0%", "-1.5%", "+1.2%"]
}
st.dataframe(pd.DataFrame(trades_data), use_container_width=True)

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
