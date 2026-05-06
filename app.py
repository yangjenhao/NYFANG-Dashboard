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
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

DOMAIN_MAP = {
    "META": "meta.com", "AAPL": "apple.com", "AMZN": "amazon.com", 
    "NFLX": "netflix.com", "MSFT": "microsoft.com", "GOOGL": "google.com", 
    "MU": "micron.com", "NVDA": "nvidia.com", "PLTR": "palantir.com", "AVGO": "broadcom.com"
}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, interval="1d" if p != "1d" else "1m", progress=False, auto_adjust=False)['Close']
    if p == "1d" and data.index.tz is not None:
        data.index = data.index.tz_convert('America/New_York').tz_localize(None)
    return data.ffill().dropna()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='sidebar-content'><p><b>AUTHOR:</b> Jen-Hao Yang</p><p><b>SYSTEM:</b> NYSE FANG+ TERMINAL</p></div>", unsafe_allow_html=True)

# --- 4. MAIN LAYOUT ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")
period_val = period_map[selected_label]

try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    start_vals, end_vals = df.iloc[0], df.iloc[-1]
    
    total_pts_change = end_vals[INDEX_SYMBOL] - start_vals[INDEX_SYMBOL]
    variance = (total_pts_change / start_vals[INDEX_SYMBOL]) * 100
    shift_col = COLORS['up'] if total_pts_change >= 0 else COLORS['down']

    # Metrics
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VALUE</p><h3 style="color:{shift_col};">{end_vals[INDEX_SYMBOL]:,.2f}</h3></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">SHIFT</p><h3 style="color:{shift_col};">{total_pts_change:+.2f}</h3></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VAR %</p><h3 style="color:{shift_col};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

    # Attribution
    stock_returns = (end_vals[OFFICIAL_TICKERS] / start_vals[OFFICIAL_TICKERS]) - 1
    raw_impacts = stock_returns * 0.1
    cum_contrib = (raw_impacts * (total_pts_change / raw_impacts.sum())) if abs(raw_impacts.sum()) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        fig_idx = go.Figure(go.Scatter(x=df.index, y=df[INDEX_SYMBOL], line=dict(color=COLORS['gold'], width=2), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)'))
        fig_idx.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=20, b=10), height=400)
        st.plotly_chart(fig_idx, use_container_width=True)

    with col2:
        row = cum_contrib.sort_values(ascending=True)
        
        # 建立 Logo List
        logo_images = []
        for i, ticker in enumerate(row.index):
            domain = DOMAIN_MAP.get(ticker, "google.com")
            logo_images.append(dict(
                source=f"https://logo.clearbit.com/{domain}",
                xref="paper", yref="y",
                x=-0.15, y=i, # 將 Logo 放在文字更左邊
                sizex=0.07, sizey=0.7,
                xanchor="right", yanchor="middle"
            ))

        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2),
            textposition='outside', # 數字放在條狀圖外面，避免重疊
            cliponaxis=False
        ))

        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=100, r=40, t=40, b=20), # 左邊距加大至 100 確保 Logo 空間
            height=400,
            images=logo_images,
            title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'])),
            yaxis=dict(showgrid=False, fixedrange=True, tickfont=dict(size=12)),
            xaxis=dict(showgrid=True, gridcolor='#222', fixedrange=True)
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")
