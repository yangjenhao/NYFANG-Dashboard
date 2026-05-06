import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. DESIGN TOKENS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ 
        font-family: 'Marcellus', serif !important; 
        text-transform: uppercase; 
        color: {COLORS['gold']} !important; 
        text-align: center; 
        font-size: clamp(1.4rem, 6vw, 2.2rem); 
        margin: 10px 0;
    }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .sidebar-content {{ padding: 20px; font-size: 0.9rem; color: {COLORS['muted']}; }}
    .metric-card {{ 
        background-color: {COLORS['card_bg']}; 
        border: 1px solid {COLORS['gold']}33; 
        padding: 12px; 
        text-align: center; 
        margin-bottom: 10px; 
    }}
    div[data-testid="stHorizontalBlock"] {{ justify-content: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    
    # 邏輯修正：5D 模式下抓取 14 天數據以應對假日與週末，確保能湊滿 5 個開盤日
    fetch_p = "14d" if p == "5d" else p
    interval = "1m" if p == "1d" else "1d"
    
    data = yf.download(all_symbols, period=fetch_p, interval=interval, progress=False, auto_adjust=False)['Close']
    
    if p == "1d":
        if data.index.tz is not None: data.index = data.index.tz_convert('America/New_York').tz_localize(None)
        else: data.index = data.index.tz_localize('UTC').tz_convert('America/New_York').tz_localize(None)
    else:
        data.index = pd.to_datetime(data.index).normalize()
        # 強制過濾並僅保留最近的 5 個開盤日（4/29, 4/30 等）
        if p == "5d":
            data = data.tail(5)
            
    return data.ffill().dropna()

# --- 3. SIDEBAR (TERMINAL) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='sidebar-content'>
            <p><b>AUTHOR:</b> Jen-Hao Yang</p>
            <p><b>SYSTEM:</b> NYSE FANG+ TERMINAL</p>
            <hr style="border-color:{COLORS['gold']}22;">
            <p style="font-size:0.8rem;">Session Alignment: Enabled. <br>Fetching 5-day trading window including late April sessions.</p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. MAIN LAYOUT ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")
period_val = period_map[selected_label]

try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    
    # 點位定義
    start_vals = df.iloc[0]
    end_vals = df.iloc[-1]
    plot_time = df.index[-1]
    
    total_pts_change = end_vals[INDEX_SYMBOL] - start_vals[INDEX_SYMBOL]
    variance = (total_pts_change / start_vals[INDEX_SYMBOL]) * 100
    shift_col = COLORS['up'] if total_pts_change >= 0 else COLORS['down']

    # 指標顯示
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VALUE</p><h3 style="color:{shift_col};">{end_vals[INDEX_SYMBOL]:,.2f}</h3></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">SHIFT ({selected_label})</p><h3 style="color:{shift_col};">{total_pts_change:+.2f}</h3></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VAR %</p><h3 style="color:{shift_col};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

    # 歸因計算 (對齊交易日)
    stock_returns = (end_vals[OFFICIAL_TICKERS] / start_vals[OFFICIAL_TICKERS]) - 1
    raw_impacts = stock_returns * 0.1
    total_impact_sum = raw_impacts.sum()
    cum_contrib = (raw_impacts * (total_pts_change / total_impact_sum)) if abs(total_impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)

    # 圖表佈局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 強化的 Y 軸縮放
        y_min, y_max = idx_series.min(), idx_series.max()
        y_range = y_max - y_min
        y_padding = y_range * 0.05 if y_range > 0 else 10

        fig_idx = go.Figure(go.Scatter(
            x=df.index, y=df[INDEX_SYMBOL], 
            fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.03)', 
            line=dict(color=COLORS['gold'], width=2.5),
            hoverinfo="x+y"
        ))
        
        xaxis_cfg = dict(showgrid=False, color=COLORS['muted'], fixedrange=True, showspikes=True, spikemode='across', nticks=5)
        
        if period_val == '1d':
            xaxis_cfg['tickformat'] = "%H:%M"
            xaxis_cfg['range'] = [plot_time.replace(hour=9, minute=30), plot_time.replace(hour=16, minute=0)]
        else:
            xaxis_cfg['tickformat'] = "%m/%d" # 確保 5D 顯示日期如 04/29, 04/30
        
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=10, r=10, t=20, b=10), height=380, 
            xaxis=xaxis_cfg, 
            yaxis=dict(fixedrange=True, showgrid=True, gridcolor='#222', nticks=6, range=[y_min - y_padding, y_max + y_padding]),
            hovermode="x"
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2:
        row = cum_contrib.sort_values(ascending=True)
        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], 
            text=row.values.round(2), textposition='auto'
        ))
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=10, r=10, t=20, b=10), height=400, 
            yaxis=dict(fixedrange=True), xaxis=dict(fixedrange=True, showgrid=True, gridcolor='#222', nticks=5),
            title=dict(text=f"CUMULATIVE CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=14))
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"TERMINAL OFFLINE: {str(e)}")
