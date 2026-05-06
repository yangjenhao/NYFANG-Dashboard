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
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['gold']} !important; text-align: center; font-size: clamp(1.4rem, 6vw, 2.2rem); margin: 10px 0; }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .sidebar-content {{ padding: 20px; font-size: 0.9rem; color: {COLORS['muted']}; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 12px; text-align: center; margin-bottom: 10px; }}
    div[data-testid="stHorizontalBlock"] {{ justify-content: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    
    if p == "5d":
        # 抓取 1 個月數據確保緩衝充足
        raw = yf.download(all_symbols, period="1mo", interval="1d", progress=False, auto_adjust=False)['Close']
        raw.index = pd.to_datetime(raw.index).normalize()
        # 排除所有 NaN 後取最後 5 個交易日
        data = raw.dropna(subset=[INDEX_SYMBOL]).tail(5)
    elif p == "1d":
        # 1D 模式抓取最近 2 天的分鐘線以獲取昨日收盤至今的走勢
        data = yf.download(all_symbols, period="2d", interval="1m", progress=False, auto_adjust=False)['Close']
        if data.index.tz is not None: 
            data.index = data.index.tz_convert('America/New_York').tz_localize(None)
        else: 
            data.index = data.index.tz_localize('UTC').tz_convert('America/New_York').tz_localize(None)
    else:
        data = yf.download(all_symbols, period=p, interval="1d", progress=False, auto_adjust=False)['Close']
        data.index = pd.to_datetime(data.index).normalize()
            
    return data.ffill().dropna()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='sidebar-content'>
            <p><b>AUTHOR:</b> Jen-Hao Yang</p>
            <p><b>SYSTEM:</b> NYSE FANG+ TERMINAL</p>
            <hr style="border-color:{COLORS['gold']}22;">
            <p style="font-size:0.8rem;">Current Date: {datetime.now().strftime('%Y-%m-%d')}<br>Live Session Sync: Enabled.</p>
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
    
    start_vals = df.iloc[0]
    end_vals = df.iloc[-1]
    
    total_pts_change = end_vals[INDEX_SYMBOL] - start_vals[INDEX_SYMBOL]
    variance = (total_pts_change / start_vals[INDEX_SYMBOL]) * 100
    shift_col = COLORS['up'] if total_pts_change >= 0 else COLORS['down']

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VALUE</p><h3 style="color:{shift_col};">{end_vals[INDEX_SYMBOL]:,.2f}</h3></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">SHIFT ({selected_label})</p><h3 style="color:{shift_col};">{total_pts_change:+.2f}</h3></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VAR %</p><h3 style="color:{shift_col};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

    # 歸因計算
    stock_returns = (end_vals[OFFICIAL_TICKERS] / start_vals[OFFICIAL_TICKERS]) - 1
    raw_impacts = stock_returns * 0.1
    total_impact_sum = raw_impacts.sum()
    cum_contrib = (raw_impacts * (total_pts_change / total_impact_sum)) if abs(total_impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)

    col1, col2 = st.columns([1, 1])
    
    with col1:
        y_min, y_max = idx_series.min(), idx_series.max()
        y_padding = (y_max - y_min) * 0.05 if (y_max - y_min) > 0 else 10
        
        x_axis_data = df.index.strftime('%m/%d') if period_val != '1d' else df.index

        fig_idx = go.Figure(go.Scatter(
            x=x_axis_data, y=df[INDEX_SYMBOL], 
            fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.03)', 
            line=dict(color=COLORS['gold'], width=2.5),
            hoverinfo="x+y"
        ))
        
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=10, r=10, t=20, b=10), height=380, 
            xaxis=dict(type='category' if period_val != '1d' else 'date', showgrid=False, color=COLORS['muted'], fixedrange=True, nticks=5),
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
            yaxis=dict(fixedrange=True), xaxis=dict(fixedrange=True, showgrid=True, gridcolor='#222'),
            title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=14))
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"TERMINAL ERROR: {str(e)}")
