import streamlit as st
import pymongo
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import requests
import time

# Page configuration
st.set_page_config(
    page_title="▶ Adaptive Market Strategy Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .strategy-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .stock-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 0.5rem;
    }
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# MongoDB connection
@st.cache_resource
def init_mongodb():
    try:
        MONGODB_URI = os.getenv('MONGODB_URI')
        if not MONGODB_URI:
            st.error("❌ MongoDB connection not configured. Please add MONGODB_URI to your environment variables.")
            st.stop()
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.adaptive_market_db
        client.admin.command('ping')
        return db, True
    except Exception as e:
        st.error(f"MongoDB connection failed: {e}")
        return None, False

# Sample data (same as your FastAPI app)
SAMPLE_STOCKS = {
    "momentum": [
        {"symbol": "GOOGL", "score": 17.93, "monthly_return": "12.17%", "volume_ratio": 1.35, "rsi": 68.2, "trend_strength": "Strong"},
        {"symbol": "MSFT", "score": 15.84, "monthly_return": "8.45%", "volume_ratio": 1.28, "rsi": 65.4, "trend_strength": "Strong"},
        {"symbol": "AAPL", "score": 14.72, "monthly_return": "6.23%", "volume_ratio": 1.22, "rsi": 62.8, "trend_strength": "Moderate"},
        {"symbol": "NVDA", "score": 13.58, "monthly_return": "9.87%", "volume_ratio": 1.45, "rsi": 71.3, "trend_strength": "Strong"},
        {"symbol": "AMZN", "score": 12.91, "monthly_return": "5.44%", "volume_ratio": 1.18, "rsi": 59.7, "trend_strength": "Moderate"},
        {"symbol": "META", "score": 11.76, "monthly_return": "7.92%", "volume_ratio": 1.31, "rsi": 66.1, "trend_strength": "Strong"},
        {"symbol": "TSLA", "score": 10.83, "monthly_return": "4.56%", "volume_ratio": 1.52, "rsi": 58.9, "trend_strength": "Moderate"},
        {"symbol": "NFLX", "score": 9.95, "monthly_return": "6.78%", "volume_ratio": 1.25, "rsi": 61.4, "trend_strength": "Moderate"}
    ],
    "mean_reversion": [
        {"symbol": "META", "score": 11.45, "oversold_level": "Extreme", "rsi": 28.4, "deviation_pct": "-8.2%", "support_level": "$485.20"},
        {"symbol": "PYPL", "score": 10.23, "oversold_level": "High", "rsi": 31.7, "deviation_pct": "-6.8%", "support_level": "$58.45"},
        {"symbol": "SNAP", "score": 9.67, "oversold_level": "Extreme", "rsi": 25.9, "deviation_pct": "-9.1%", "support_level": "$9.85"},
        {"symbol": "UBER", "score": 8.95, "oversold_level": "Moderate", "rsi": 33.2, "deviation_pct": "-5.4%", "support_level": "$68.90"},
        {"symbol": "ROKU", "score": 8.42, "oversold_level": "High", "rsi": 27.6, "deviation_pct": "-7.7%", "support_level": "$45.30"},
    ],
    "breakout": [
        {"symbol": "TSLA", "score": 10.23, "resistance_level": "$185.50", "distance_to_breakout": "1.2%", "volume_surge": "67%", "pattern": "Bull Flag"},
        {"symbol": "COIN", "score": 9.45, "resistance_level": "$95.80", "distance_to_breakout": "0.8%", "volume_surge": "84%", "pattern": "Ascending Triangle"},
        {"symbol": "PLTR", "score": 8.76, "resistance_level": "$18.45", "distance_to_breakout": "1.5%", "volume_surge": "52%", "pattern": "Rectangle"},
        {"symbol": "RIVN", "score": 8.12, "resistance_level": "$12.75", "distance_to_breakout": "2.1%", "volume_surge": "73%", "pattern": "Cup & Handle"},
    ],
    "value": [
        {"symbol": "JPM", "score": 18.67, "pe_ratio": 12.4, "pb_ratio": 1.3, "dividend_yield": "2.8%", "peg_ratio": 0.95},
        {"symbol": "BRK.B", "score": 17.23, "pe_ratio": 15.6, "pb_ratio": 1.4, "dividend_yield": "0.0%", "peg_ratio": 1.1},
        {"symbol": "WFC", "score": 16.45, "pe_ratio": 11.8, "pb_ratio": 1.1, "dividend_yield": "3.2%", "peg_ratio": 0.89},
        {"symbol": "BAC", "score": 15.89, "pe_ratio": 13.2, "pb_ratio": 1.2, "dividend_yield": "2.5%", "peg_ratio": 1.02},
        {"symbol": "XOM", "score": 15.34, "pe_ratio": 14.7, "pb_ratio": 1.8, "dividend_yield": "5.4%", "peg_ratio": 0.76},
    ]
}

SAMPLE_MARKET_DATA = [
    {"symbol": "SPY", "price": 563.45, "change_percent": 0.85, "volume": 45230000, "rsi": 61.2, "trend": "up"},
    {"symbol": "QQQ", "price": 485.67, "change_percent": 1.25, "volume": 32180000, "rsi": 64.8, "trend": "up"},
    {"symbol": "IWM", "price": 225.89, "change_percent": -0.45, "volume": 28450000, "rsi": 48.3, "trend": "down"},
    {"symbol": "DIA", "price": 442.12, "change_percent": 0.65, "volume": 15670000, "rsi": 58.7, "trend": "up"}
]

SAMPLE_NEWS = [
    {"title": "Markets Show Momentum as Tech Stocks Rally", "impact": "High", "sentiment": "Positive", "time": "2 hours ago"},
    {"title": "Fed Officials Signal Dovish Stance on Interest Rates", "impact": "High", "sentiment": "Positive", "time": "4 hours ago"},
    {"title": "Earnings Season Drives Selective Trading Opportunities", "impact": "Medium", "sentiment": "Neutral", "time": "6 hours ago"},
    {"title": "Technical Analysis Points to Range-Bound Trading", "impact": "Medium", "sentiment": "Neutral", "time": "8 hours ago"}
]

# Fetch real news function
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_real_news():
    api_key = os.getenv('NEWS_API_KEY', 'demo')
    if api_key == 'demo':
        return SAMPLE_NEWS
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': 'stock market OR finance OR trading',
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 4,
            'from': (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = []
            for article in data.get('articles', [])[:4]:
                if article.get('title'):
                    articles.append({
                        "title": article['title'][:80] + "..." if len(article['title']) > 80 else article['title'],
                        "impact": "High" if any(word in article['title'].lower() for word in ['surge', 'crash', 'rally']) else "Medium",
                        "sentiment": "Positive" if any(word in article['title'].lower() for word in ['rise', 'gain', 'bull']) else "Neutral",
                        "time": "Live"
                    })
            return articles if articles else SAMPLE_NEWS
    except:
        pass
    
    return SAMPLE_NEWS

# Initialize MongoDB
db, mongodb_connected = init_mongodb()

# Main App
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>▶ Adaptive Market Strategy Agent</h1>
        <p>AI-Powered Trading Strategy Recommendations Based on Real-Time Market Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for controls
    with st.sidebar:
        st.title("🎛️ Controls")
        auto_refresh = st.checkbox("Auto-refresh data", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 30, 300, 60)
        
        st.markdown("---")
        st.markdown("### 🔗 System Status")
        st.success(f"MongoDB: {'✅ Connected' if mongodb_connected else '❌ Disconnected'}")
        st.info(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        if st.button("🔄 Refresh Now"):
            st.cache_data.clear()
            st.rerun()
    
    # Main content in columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Market Regime Analysis
        st.markdown("### 📊 Market Regime Analysis")
        regime_container = st.container()
        with regime_container:
            st.markdown("""
            <div class="metric-card">
                <h4>🎯 RANGE-BOUND MARKET</h4>
                <p><span class="confidence-high">Confidence: 75%</span></p>
                <p><small>Markets moving sideways, no clear direction. Good for mean reversion and range trading strategies.</small></p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # AI Strategy Recommendation
        st.markdown("### 🤖 AI Strategy Recommendation")
        strategy_container = st.container()
        with strategy_container:
            st.markdown("""
            <div class="strategy-card">
                <h4>🎯 Trend Following Strategy</h4>
                <p><strong>Confidence: 74%</strong></p>
                <p><em>"Follow market direction with momentum"</em></p>
                <p>Risk Level: Medium | Timeframe: 2-4 weeks</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Live Market Data
    st.markdown("### 📈 Live Market Data")
    market_cols = st.columns(4)
    
    for i, data in enumerate(SAMPLE_MARKET_DATA):
        with market_cols[i]:
            change_color = "🟢" if data["change_percent"] >= 0 else "🔴"
            st.metric(
                label=f"{change_color} {data['symbol']}",
                value=f"${data['price']:.2f}",
                delta=f"{data['change_percent']:+.2f}%"
            )
            st.caption(f"RSI: {data['rsi']:.1f} | Trend: {data['trend'].upper()}")
    
    # Charts and News
    chart_col, news_col = st.columns([2, 1])
    
    with chart_col:
        st.markdown("### 📊 Market Trends")
        # Create sample chart data
        dates = pd.date_range(start='2024-06-01', periods=30, freq='D')
        prices = [560 + i*0.5 + (i%7)*2 for i in range(30)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name='Market Trend', line=dict(color='#007bff', width=3)))
        fig.update_layout(
            title="30-Day Market Trend",
            xaxis_title="Date",
            yaxis_title="Price",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with news_col:
        st.markdown("### 📰 Recent Market Events")
        news_data = fetch_real_news()
        
        for news in news_data:
            impact_color = "🔴" if news["impact"] == "High" else "🟡"
            sentiment_emoji = "📈" if news["sentiment"] == "Positive" else "📊"
            
            st.markdown(f"""
            <div class="stock-card">
                <strong>{impact_color} {news['title']}</strong><br>
                <small>{sentiment_emoji} {news['sentiment']} | {news['time']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Stock Screener
    st.markdown("### 🔍 Strategy-Based Stock Screener")
    
    # Strategy selection tabs
    strategy_tabs = st.tabs(["📈 Momentum", "↩️ Mean Reversion", "📊 Breakout", "💰 Value"])
    
    with strategy_tabs[0]:  # Momentum
        display_stocks("momentum", "Momentum Strategy")
    
    with strategy_tabs[1]:  # Mean Reversion
        display_stocks("mean_reversion", "Mean Reversion Strategy")
    
    with strategy_tabs[2]:  # Breakout
        display_stocks("breakout", "Breakout Strategy")
    
    with strategy_tabs[3]:  # Value
        display_stocks("value", "Value Strategy")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

def display_stocks(strategy_type, strategy_name):
    """Display stocks for a specific strategy"""
    st.subheader(f"{strategy_name} - Top Picks")
    
    stocks = SAMPLE_STOCKS.get(strategy_type, [])
    
    if stocks:
        # Create columns for stock cards
        cols = st.columns(3)
        
        for i, stock in enumerate(stocks[:9]):  # Show top 9 stocks
            with cols[i % 3]:
                # Create stock card
                metrics_html = ""
                for key, value in stock.items():
                    if key not in ['symbol', 'score']:
                        metrics_html += f"<strong>{key.replace('_', ' ').title()}:</strong> {value}<br>"
                
                st.markdown(f"""
                <div class="stock-card">
                    <h4>{stock['symbol']} <span style="float: right; color: #007bff;">{stock['score']:.2f}</span></h4>
                    {metrics_html}
                </div>
                """, unsafe_allow_html=True)
        
        st.info(f"📊 Showing {len(stocks)} {strategy_name.lower()} stocks (Demo Mode)")
    else:
        st.warning(f"No {strategy_name.lower()} opportunities detected at this time.")

if __name__ == "__main__":
    main()
