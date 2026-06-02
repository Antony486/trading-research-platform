# Trading Research Platform

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://docker.com)

## 🚀 Features
- Real-time market data from 60+ exchanges
- ML predictions (XGBoost, Random Forest, LSTM)
- High-performance backtesting engine
- Interactive Streamlit dashboard
- RESTful API with automatic docs

## Quick Start
```bash
git clone https://github.com/Antony486/trading-research-platform
cd trading-research-platform
docker-compose up -d
streamlit run services/dashboard/app.py
\```

## 📊 Access
- Dashboard: http://localhost:8501
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Built with Python, FastAPI, Streamlit, TimescaleDB, Docker
