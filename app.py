import streamlit as st
import ccxt
import pandas as pd
import numpy as np

# --- 1. PRO CONFIGURATION ---
st.set_page_config(page_title="Diamond Master Radar v2", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Mobile Optimization & High-Contrast Trading
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #00ffcc !important; }
    .card { border: 1px solid #333; padding: 12px; border-radius: 8px; background: #111; margin-bottom: 10px; }
    .elite { border-left: 5px solid #bc13fe; }
    .high { border-left: 5px solid #00ff00; }
    </style>
""", unsafe_with_html=True)

# --- 2. MULTI-EXCHANGE DATA ENGINE (STEP 5) ---
@st.cache_data(ttl=10)
def fetch_radar_data(symbol, timeframe='15m'):
    exchanges = [ccxt.okx(), ccxt.binance(), ccxt.bybit()]
    for ex in exchanges:
        try:
            ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=150)
            df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            # Indicators (STEP 6)
            df['sma20'] = df['close'].rolling(20).mean()
            df['sma100'] = df['close'].rolling(100).mean()
            df['vol_ma'] = df['vol'].rolling(20).mean()
            return df, ex.name
        except: continue
    return pd.DataFrame(), "OFFLINE"

# --- 3. THE 7-SETUP "BRAIN" ---
def analyze_setups(df):
    if df.empty or len(df) < 100: return None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Surgical Metrics
    spread = abs(last['sma20'] - last['sma100']) / last['sma100'] * 100
    dist_100 = abs(last['close'] - last['sma100']) / last['sma100'] * 100
    
    # Liquidity Engine (BSL/SSL)
    h20 = df['high'].rolling(20).max().iloc[-2]
    l20 = df['low'].rolling(20).min().iloc[-2]
    
    # 7-Setup Mapping
    res = {"setup": "🔎 SCANNING", "tier": "C", "strat": "Wait", "color": "#888"}

    # #7: SURGICAL SQUEEZE (0.09% Precision)
    if spread <= 0.09:
        res = {"setup": "🟣 0.09% ELITE SQZ", "tier": "A+", "strat": "Breakout", "color": "#bc13fe"}
    
    # #5: LIQUIDITY SWEEP (Floor/Ceiling Rejection)
    elif last['low'] < l20 and last['close'] > l20:
        res = {"setup": "🟢 BULL SWEEP (SSL)", "tier": "A+", "strat": "Reversion", "color": "#00ff00"}
    elif last['high'] > h20 and last['close'] < h20:
        res = {"setup": "🔴 BEAR SWEEP (BSL)", "tier": "A+", "strat": "Reversion", "color": "#ff4b4b"}

    # #6: THE KISS (SMA 100 Reversion)
    elif dist_100 <= 0.06 and spread > 0.30:
        res = {"setup": "💋 THE KISS", "tier": "A", "strat": "Shadowing", "color": "#ff007f"}

    # #1 & #2: MOMENTUM TRAPS
    elif last['close'] > last['sma20'] and last['sma20'] < last['sma100']:
        res = {"setup": "🔥 SHORT TRAP", "tier": "B", "strat": "Basis", "color": "#ffa500"}
    
    # #3 & #4: EXPANSION / TREND
    elif last['sma20'] > last['sma100'] and last['close'] > last['sma20']:
        res = {"setup": "🌊 EXPANSION", "tier": "B", "strat": "Shadowing", "color": "#00aaff"}

    return res

# --- 4. THE RADAR INTERFACE ---
st.title("💎 Diamond Master Radar")

# BTC Global Context (1H)
btc_df, source = fetch_radar_data('BTC/USDT', '1h')
if not btc_df.empty:
    s = analyze_setups(btc_df)
    c1, c2, c3 = st.columns(3)
    c1.metric("BTC PRICE", f"${btc_df['close'].iloc[-1]:,.0f}")
    c2.metric("CONVICTION", s['tier'])
    c3.metric("SET-UP", s['setup'])
    
    if s['tier'] == "A+":
        st.warning(f"⚠️ HIGH CONVICTION ALERT: {s['setup']} on BTC (1H)")

st.divider()

# Multi-Pair Watchlist (15m)
watchlist = ["PEPE/USDT", "DOGE/USDT", "SOL/USDT", "WIF/USDT", "BONK/USDT", "SHIB/USDT"]
cols = st.columns(2) # Mobile optimized grid

for i, pair in enumerate(watchlist):
    df, _ = fetch_radar_data(pair, '15m')
    if not df.empty:
        setup = analyze_setups(df)
        border_class = "elite" if setup['tier'] == "A+" else "high" if setup['tier'] == "A" else ""
        with cols[i % 2]:
            st.markdown(f"""
                <div class="card {border_class}">
                    <h3 style="margin:0; color:{setup['color']};">{pair.split('/')[0]}</h3>
                    <p style="margin:5px 0;"><b>{setup['setup']}</b></p>
                    <p style="margin:0; font-size:0.8rem; color:#888;">Tier: {setup['tier']} | Strat: {setup['strat']}</p>
                </div>
            """, unsafe_with_html=True)
