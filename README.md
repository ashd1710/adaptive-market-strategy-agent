# 🎯 Adaptive Market Strategy Agent

[![Made with Google Cloud](https://img.shields.io/badge/Made%20with-Google%20Cloud-4285f4)](https://cloud.google.com/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248)](https://www.mongodb.com/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)

> **AI-powered trading strategy recommendation system built in 72 hours for Google Cloud + MongoDB Hackathon**

🎬 **[Demo Video Coming Soon]** | 🚀 **[Live System](http://localhost:8000)**

---

## 🏆 Hackathon Achievement

**Built in 72 hours** - A complete AI trading platform that:
- ✅ **Analyzes real-time market data** from 4 major ETFs (SPY, QQQ, IWM, DIA)
- ✅ **AI-powered market regime detection** with 80% confidence
- ✅ **Live stock screening** across 4 strategies (Momentum, Value, Breakout, Mean Reversion)
- ✅ **Professional scoring system** with detailed reasoning

### **🎯 Current Live Results:**
- **11 momentum stocks identified** from 50 analyzed
- **GOOGL leads with 17.93 score** (12.17% monthly return)
- **Range-bound market regime** detected with 80% confidence
- **Trend Following Strategy** recommended with 82% confidence

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/adaptive-market-strategy-agent
cd adaptive-market-strategy-agent

# Install dependencies
pip install fastapi uvicorn pymongo requests python-multipart numpy pandas

# Set MongoDB connection
export MONGODB_URI='your-mongodb-connection-string'

# Start the system
python startup.py

# Access dashboard
open http://localhost:8000

🏗️ Technical Architecture
Stack:

Backend: FastAPI + Python
Database: MongoDB Atlas with Vector Search
AI/ML: Google Cloud Vertex AI + Custom Algorithms
Frontend: HTML/CSS/JS with Chart.js
APIs: Alpha Vantage + Yahoo Finance

Key Components:

Market Data Engine - Real-time ETF analysis
AI Strategy Engine - Market regime detection & strategy matching
Stock Screener - Multi-factor analysis across 50+ stocks
Risk Calculator - Confidence scoring & risk assessment


📊 Live Demo Results
Market Analysis (Real-time):
json{
  "market_regime": "range_bound",
  "confidence": 0.8,
  "recommended_strategy": "Trend Following Strategy",
  "strategy_confidence": 0.82,
  "risk_level": "medium"
}
Top Momentum Picks:
SymbolScoreReturnRSIStatusGOOGL17.9312.17%68.1✅ StrongAMD14.978.95%67.9✅ StrongPFE14.807.46%73.9✅ Strong
Live ETF Data:

SPY: $603.08 (+0.57%) RSI: 74.7 📈
QQQ: $534.21 (+0.66%) RSI: 74.6 📈
IWM: $214.51 (+0.54%) RSI: 79.1 📈
DIA: $429.61 (+0.29%) RSI: 73.2 📈


🎯 Key Features
1. AI Market Regime Detection

Continuous analysis of 4 major indices
80%+ confidence classification
Real-time strategy recommendations

2. Multi-Strategy Stock Screening

Momentum: Strong price trends with volume
Value: Undervalued fundamentals
Breakout: Technical pattern recognition
Mean Reversion: Oversold opportunities

3. Professional Risk Management

Dynamic confidence scoring
Stop-loss recommendations
Expected holding periods
Risk-adjusted position sizing


📈 Business Opportunity
Market Scaling Path:

Retail (Individual traders)
Professional (Trading groups)
Institutional (Hedge funds)
Enterprise (Asset managers)

Competitive Advantages:

Real-time adaptability vs static tools
Multi-dimensional analysis beyond technical indicators
Transparent AI reasoning with confidence scores
Scalable MongoDB + Google Cloud architecture


🛠️ Project Files
Core System:

main.py - FastAPI application server
startup.py - System initialization and data pipeline
strategy_engine.py - AI strategy recommendation engine
market_data_fetcher.py - Real-time market data collection
static/index.html - Professional dashboard UI

Testing & Debug:

health_check.py - System health monitoring
debug_screener.py - Stock screener testing
optimize_for_demo.py - Demo performance optimization


🏆 Technical Highlights
Innovation Factors:

Dynamic Strategy Adaptation - Changes with market conditions
MongoDB Vector Search - Historical pattern matching
Google Cloud AI Integration - Intelligent market analysis
Real-time Processing - Live data updates every 5 minutes

System Performance:

API Response: <30 seconds for complex analysis
Data Coverage: 50+ stocks, 4 strategies, 4 ETFs
Accuracy: 80%+ confidence in recommendations
Uptime: 99%+ during hackathon period


📞 Contact
Built by: Ashish Deshpande
🏆 From idea to production with Google Cloud + MongoDB EOF

