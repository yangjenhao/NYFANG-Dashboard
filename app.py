import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. DESIGN TOKENS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

# CSS 優化：頂部導航與手機端顯示
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    
    h1, .main-title {{ 
        font-family: 'Marcellus', serif !important; 
        text-transform: uppercase; 
        color: {COLORS['gold']} !important; 
        text-align: center; 
        font-size: clamp(1.4rem, 6vw, 2rem); 
        margin-bottom: 0px;
    }}
    
    .metric-card {{ 
        background-color: {COLORS['card_bg']}; 
        border: 1px solid {COLORS['gold']}33; 
        padding: 10px; 
        text-align: center; 
        margin-bottom: 5px; 
    }}
    
    /* 讓 Streamlit 的按鈕組在手機上置中且美觀 */
    .stHorizontal {{ justify-content: center !important; }}
    div[data-testid="stHorizontalBlock"] {{ gap: 0.5rem; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    is_intraday = (p == "1d")
    fetch_p, interval = ("2d", "1m") if is_intraday else (p, "1d")
    data = yf.download(all_symbols, period=fetch_p, interval=interval, progress=False, auto_adjust=False)['Close']
    if is_intraday:
        if data.index.tz is not None: data.index = data.index.tz_convert('America/New_York').tz_localize(None)
        else: data.index = data.index.tz_localize('UTC').tz_convert('America/New_York').tz_localize(None)
    else: data.index = pd.to_datetime(data.index).normalize()
    return data.ffill().dropna()

# --- 3. TOP NAVIGATION (取代原本的 Sidebar) ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

# 橫向時間軸切換
period_map = {
    "1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y"
}
# 使用 segmented_control 達成類似附圖的橫向切換效果
selected_label = st.segmented_control(
    "TIMELINE", 
    options=list(period_map.keys()), 
    default="1D", 
    label_visibility="collapsed"
)
period_val = period_map[selected_label]

# --- 4. MAIN CONTENT ---
try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    
    # 始終顯示最新數據點
    start_vals = df.iloc[0]
    end_vals = df.iloc[-1]
    plot_time = df.index[-1]
    
    total_pts_change = end_vals[INDEX_SYMBOL] - start_vals[INDEX_SYMBOL]
    variance = (total_pts_change / start_vals[INDEX_SYMBOL]) * 100
    shift_col = COLORS['up'] if total_pts_change >= 0 else COLORS['down']

    # 指標顯示
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VALUE</p><h3 style="color:{shift_col};">{end_vals[INDEX_SYMBOL]:,.2f}</h3></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">SHIFT</p><h3 style="color:{shift_col};">{total_pts_change:+.2f}</h3></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VAR %</p><h3 style="color:{shift_col};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

    # 歸因計算
    stock_returns = (end_vals[OFFICIAL_TICKERS] / start_vals[OFFICIAL_TICKERS]) - 1
    raw_impacts = stock_returns * 0.1
    total_impact_sum = raw_impacts.sum()
    cum_contrib = (raw_impacts * (total_pts_change / total_impact_sum)) if abs(total_impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)

    # 圖表佈局 (手機端自動堆疊)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        fig_idx = go.Figure(go.Scatter(
            x=df.index, y=df[INDEX_SYMBOL], 
            fill='tozeroy', # 加上陰影面積，更像附圖
            fillcolor='rgba(212, 175, 55, 0.1)',
            line=dict(color=COLORS['gold'], width=2),
            hoverinfo="x+y"
        ))
        
        xaxis_cfg = dict(
            showgrid=False, color=COLORS['muted'], fixedrange=True,
            showspikes=True, spikemode='across', spikesnap='cursor', spikedash='dash', spikecolor=COLORS['muted'],
            nticks=5
        )
        if period_val == '1d':
            xaxis_cfg['tickformat'] = "%H:%M"
            xaxis_cfg['range'] = [plot_time.replace(hour=9, minute=30), plot_time.replace(hour=16, minute=0)]
        
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=10, r=10, t=20, b=10), height=350, 
            xaxis=xaxis_cfg, yaxis=dict(fixedrange=True, showgrid=True, gridcolor='#333', nticks=5),
            hovermode="x"
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2:
        row = cum_contrib.sort_values(ascending=True)
        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, 
            orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], 
            text=row.values.round(2), textposition='auto'
        ))
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=10, r=10, t=20, b=10), height=400, 
            yaxis=dict(fixedrange=True), xaxis=dict(fixedrange=True, showgrid=True, gridcolor='#333', nticks=5),
            title=dict(text="CUMULATIVE CONTRIBUTION", font=dict(color=COLORS['gold'], size=14))
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"TERMINAL ERROR: {str(e)}")
