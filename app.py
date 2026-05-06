import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. DESIGN TOKENS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

st.set_page_config(page_title="FANG+ TERMINAL", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ font-family: 'Marcellus', serif !important; color: {COLORS['gold']} !important; text-align: center; font-size: 1.5rem; margin: 5px 0; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 8px; text-align: center; margin-bottom: 5px; border-radius: 4px; }}
    .metric-label {{ color: {COLORS['gold']}; font-size: 0.6rem; text-transform: uppercase; }}
    .metric-value {{ font-size: 1.2rem; font-weight: 600; }}
    /* Logo 欄位緊湊化修正 */
    .logo-container {{ display: flex; flex-direction: column; align-items: center; padding-top: 25px; gap: 2.5px; }}
    .logo-img {{ border-radius: 50%; background: white; padding: 1px; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=3600)
def get_logo_urls():
    # 使用 Google Favicon API，穩定性較高
    return {t: f"https://www.google.com/s2/favicons?sz=64&domain={t.lower()}.com" for t in OFFICIAL_TICKERS}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, interval="1m" if p=="1d" else "1d", progress=False, auto_adjust=False)['Close']
    return data.ffill().dropna()

# --- 3. MAIN UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "1Y": "1y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    idx_series = df[INDEX_SYMBOL]
    start_v, end_v = idx_series.iloc[0], idx_series.iloc[-1]
    diff, pct = end_v - start_v, (end_v - start_v) / start_v * 100
    shift_col = COLORS['up'] if diff >= 0 else COLORS['down']

    # 頂部數據
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Value</div><div class="metric-value" style="color:{shift_col};">{end_v:,.2f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">{selected_label} Performance</div><div class="metric-value" style="color:{shift_col};">{pct:+.2f}%</div></div>', unsafe_allow_html=True)

    # 歸因排序
    stock_returns = (df.iloc[-1][OFFICIAL_TICKERS] / df.iloc[0][OFFICIAL_TICKERS]) - 1
    total_raw = (stock_returns * 0.1).sum()
    cum_contrib = (stock_returns * 0.1 * (diff / total_raw)) if abs(total_raw) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)
    sorted_contrib = cum_contrib.sort_values(ascending=True)

    # 圖表佈局
    col_rank = st.container()
    with col_rank:
        st.markdown(f"<p style='color:{COLORS['gold']}; font-size:0.7rem; margin-left:10px; margin-bottom:0px;'>RANKING</p>", unsafe_allow_html=True)
        
        # 建立 Logo 與 Bar Chart 的橫向佈局
        r_l, r_r = st.columns([0.12, 0.88])
        
        with r_l: # Logo 垂直欄位
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            logo_map = get_logo_urls()
            # 依據排行從下往上顯示 Logo
            for ticker in reversed(sorted_contrib.index):
                st.image(logo_map.get(ticker), width=18)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with r_r: # 排行圖表
            fig_bar = go.Figure(go.Bar(
                y=sorted_contrib.index, x=sorted_contrib.values, orientation='h',
                marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in sorted_contrib.values],
                text=sorted_contrib.values.round(1), textposition='outside',
                textfont=dict(size=10, color=COLORS['fg'])
            ))
            fig_bar.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=40, t=5, b=5), height=300, # 降低高度
                xaxis=dict(visible=False), 
                yaxis=dict(showgrid=False, tickfont=dict(size=11))
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

    # 底部趨勢圖
    fig_idx = go.Figure(go.Scatter(x=df.index, y=idx_series, line=dict(color=COLORS['gold'], width=1.5), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)'))
    fig_idx.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=5,r=5,t=0,b=0), height=180, xaxis=dict(showgrid=False, nticks=4), yaxis=dict(visible=False))
    st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"ERROR: {str(e)}")
