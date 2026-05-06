import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. DESIGN TOKENS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

# --- 2. THEMED CSS ---
st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    h1, .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; letter-spacing: 0.15em; color: {COLORS['gold']} !important; text-align: center; font-size: 1.8rem; }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 15px; text-align: center; margin-bottom: 10px; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOGIC (時區修正版) ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    # TODAY 模式抓 1m，其餘抓 1d
    fetch_p, interval = ("2d", "1m") if p == "1d" else (("10d", "1d") if p == "5d" else (p, "1d"))
    
    data = yf.download(all_symbols, period=fetch_p, interval=interval, progress=False, auto_adjust=False)['Close']
    
    # 【核心修正】強制轉換為美東時間並移除時區資訊以便顯示
    data.index = data.index.tz_convert('America/New_York').tz_localize(None)
    return data.ffill().dropna()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2>The Terminal</h2>", unsafe_allow_html=True)
    period_options = [('TODAY', '1d'), ('V DAYS', '5d'), ('I MONTH', '1mo'), ('III MONTHS', '3mo'), ('I YEAR', '1y'), ('II YEARS', '2y'), ('V YEARS', '5y'), ('YTD', 'ytd')]
    period_label, period_val = st.selectbox("TIMELINE", options=period_options, index=0)
    
    try:
        latest_market_date = fetch_data("1mo").index[-1].date()
    except:
        latest_market_date = datetime.now().date()
    target_date = st.date_input("DEPARTURE DATE", value=latest_market_date)

# --- 5. MAIN CONTENT ---
try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    target_dt = pd.to_datetime(target_date).date()
    day_data = idx_series[idx_series.index.date == target_dt]
    
    if not day_data.empty:
        plot_time = day_data.index[-1]
        loc_start = idx_series.index.get_loc(day_data.index[0])
        ref_val = idx_series.iloc[loc_start-1] if loc_start > 0 else day_data.iloc[0]
        
        # 即時累積計算
        current_idx_val = idx_series.loc[plot_time]
        total_pts_change = current_idx_val - ref_val
        
        stock_starts = df[OFFICIAL_TICKERS].iloc[loc_start-1] if loc_start > 0 else df[OFFICIAL_TICKERS].iloc[0]
        stock_returns = (df[OFFICIAL_TICKERS].loc[plot_time] / stock_starts) - 1
        
        raw_impacts = stock_returns * 0.1
        total_impact = raw_impacts.sum()
        cum_contrib = (raw_impacts * (total_pts_change / total_impact)) if abs(total_impact) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)

        # UI 顯示
        st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
        shift_col = COLORS['up'] if total_pts_change >= 0 else COLORS['down']
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><h3>{current_idx_val:,.2f}</h3></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><h3 style="color:{shift_col};">{total_pts_change:+.2f}</h3></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><h3 style="color:{shift_col};">{(total_pts_change/ref_val)*100:+.2f}%</h3></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            # 趨勢圖：確保顯示 09:30 開始
            show_df = day_data if period_val == '1d' else idx_series
            fig_idx = go.Figure(go.Scatter(x=show_df.index, y=show_df.values, line=dict(color=COLORS['gold'], width=2)))
            
            xaxis_cfg = dict(showgrid=False, color=COLORS['muted'], tickformat="%H:%M")
            if period_val == '1d':
                # 嚴格鎖定美東開收盤時間軸範圍
                start_range = plot_time.replace(hour=9, minute=30)
                end_range = plot_time.replace(hour=16, minute=0)
                xaxis_cfg['range'] = [start_range, end_range]
            
            fig_idx.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0), height=400, xaxis=xaxis_cfg)
            st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

        with col2:
            row = cum_contrib.sort_values(ascending=False)
            fig_bar = go.Figure(go.Bar(x=row.index, y=row.values, marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], text=row.values.round(2), textposition='auto'))
            fig_bar.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0), height=400, title=dict(text=f"REAL-TIME CONTRIBUTION ({plot_time.strftime('%H:%M')} EST)", font=dict(color=COLORS['gold'], size=14)))
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("NO DATA: CHECK IF MARKET IS OPEN (9:30 AM EST).")
except Exception as e:
    st.error(f"TERMINAL ERROR: {str(e)}")
