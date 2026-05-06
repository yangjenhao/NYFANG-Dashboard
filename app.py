import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. DESIGN TOKENS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['gold']} !important; text-align: center; font-size: clamp(1.4rem, 6vw, 2.2rem); margin: 10px 0; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 12px; text-align: center; margin-bottom: 10px; }}
    /* 強制 Logo 垂直居中與間距 */
    .logo-container {{ display: flex; flex-direction: column; justify-content: space-around; height: 350px; padding-top: 45px; }}
    .logo-item {{ height: 32px; display: flex; align-items: center; justify-content: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"
DOMAIN_MAP = {"META": "meta.com", "AAPL": "apple.com", "AMZN": "amazon.com", "NFLX": "netflix.com", "MSFT": "microsoft.com", "GOOGL": "google.com", "MU": "micron.com", "NVDA": "nvidia.com", "PLTR": "palantir.com", "AVGO": "broadcom.com"}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, interval="1d" if p != "1d" else "1m", progress=False)['Close']
    return data.ffill().dropna()

# --- 3. MAIN LAYOUT ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")
period_val = period_map[selected_label]

try:
    df = fetch_data(period_val)
    start_vals, end_vals = df.iloc[0], df.iloc[-1]
    total_pts_change = end_vals[INDEX_SYMBOL] - start_vals[INDEX_SYMBOL]
    shift_col = COLORS['up'] if total_pts_change >= 0 else COLORS['down']

    # Metrics
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VALUE</p><h3 style="color:{shift_col};">{end_vals[INDEX_SYMBOL]:,.2f}</h3></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">SHIFT</p><h3 style="color:{shift_col};">{total_pts_change:+.2f}</h3></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VAR %</p><h3 style="color:{shift_col};">{(total_pts_change/start_vals[INDEX_SYMBOL]*100):+.2f}%</h3></div>', unsafe_allow_html=True)

    # Attribution Logic
    stock_returns = (end_vals[OFFICIAL_TICKERS] / start_vals[OFFICIAL_TICKERS]) - 1
    raw_impacts = stock_returns * 0.1
    row = (raw_impacts * (total_pts_change / raw_impacts.sum())).sort_values(ascending=True)

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        fig_idx = go.Figure(go.Scatter(x=df.index, y=df[INDEX_SYMBOL], line=dict(color=COLORS['gold'], width=2), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)'))
        fig_idx.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=20, b=10), height=400)
        st.plotly_chart(fig_idx, use_container_width=True)

    with col2:
        st.markdown(f"<p style='color:{COLORS['gold']}; font-weight:600; margin-bottom:10px;'>CONTRIBUTION ({selected_label})</p>", unsafe_allow_html=True)
        
        # 使用更穩定的 Column 佈局來排版 Logo 與 圖表
        inner_logo, inner_chart = st.columns([0.15, 0.85])
        
        with inner_logo:
            # 這裡使用 CSS 控制 Logo 垂直分布，避開 Plotly 內部渲染問題
            logo_html = "".join([f'<div class="logo-item"><img src="https://logo.clearbit.com/{DOMAIN_MAP[t]}" width="22"></div>' for t in row.index[::-1]])
            st.markdown(f'<div class="logo-container">{logo_html}</div>', unsafe_allow_html=True)

        with inner_chart:
            fig_bar = go.Figure(go.Bar(
                y=row.index, x=row.values, orientation='h',
                marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
                text=row.values.round(2),
                textposition='outside', # 確保數字在條形圖外，不與名稱重疊
                cliponaxis=False
            ))
            fig_bar.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=40, t=10, b=10), # 左邊距設為 0 因為 Logo 已獨立
                height=400,
                showlegend=False,
                xaxis=dict(showgrid=True, gridcolor='#222', fixedrange=True),
                yaxis=dict(fixedrange=True, tickfont=dict(size=12, color=COLORS['fg']))
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")
