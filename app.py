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
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['gold']} !important; text-align: center; font-size: clamp(1.2rem, 5vw, 2.2rem); margin: 10px 0; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 10px; text-align: center; margin-bottom: 8px; border-radius: 4px; }}
    .metric-label {{ color: {COLORS['gold']}; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }}
    .metric-value {{ font-size: 1.4rem; font-weight: 600; }}
    /* Logo 垂直排列對齊微調 */
    .logo-sidebar {{ display: flex; flex-direction: column; align-items: center; padding-top: 35px; gap: 11px; }}
    .logo-item {{ height: 24px; width: 24px; object-fit: contain; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=3600)
def get_logos():
    return {t: f"https://logo.clearbit.com/{t.lower()}.com" for t in OFFICIAL_TICKERS}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, interval="1m" if p=="1d" else "1d", progress=False, auto_adjust=False)['Close']
    if p == "1d" and data.index.tz is not None:
        data.index = data.index.tz_convert('America/New_York').tz_localize(None)
    return data.ffill().dropna()

# --- 3. MAIN UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    idx_series = df[INDEX_SYMBOL]
    start_v, end_v = idx_series.iloc[0], idx_series.iloc[-1]
    diff, pct = end_v - start_v, (end_v - start_v) / start_v * 100
    shift_col = COLORS['up'] if diff >= 0 else COLORS['down']

    # 頂部數據卡片
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Value</div><div class="metric-value" style="color:{shift_col};">{end_v:,.2f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">Shift ({selected_label})</div><div class="metric-value" style="color:{shift_col};">{diff:+.2f} ({pct:+.2f}%)</div></div>', unsafe_allow_html=True)

    # 歸因計算
    stock_returns = (df.iloc[-1][OFFICIAL_TICKERS] / df.iloc[0][OFFICIAL_TICKERS]) - 1
    total_raw = (stock_returns * 0.1).sum()
    cum_contrib = (stock_returns * 0.1 * (diff / total_raw)) if abs(total_raw) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)
    sorted_contrib = cum_contrib.sort_values(ascending=True)

    # 圖表區塊
    col_chart, col_rank = st.columns([1, 1])
    
    with col_chart:
        y_min, y_max = idx_series.min(), idx_series.max()
        pad = (y_max - y_min) * 0.05
        fig_idx = go.Figure(go.Scatter(x=df.index, y=idx_series, line=dict(color=COLORS['gold'], width=2), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.03)'))
        fig_idx.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=5,r=5,t=10,b=5), height=350, yaxis=dict(range=[y_min-pad, y_max+pad], showgrid=True, gridcolor='#222'))
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col_rank:
        st.markdown(f"<p style='color:{COLORS['gold']}; font-size:0.8rem; margin-left:45px;'>CONTRIBUTION RANKING</p>", unsafe_allow_html=True)
        
        # 關鍵修正：將 Logo 與圖表並排
        rank_l, rank_r = st.columns([0.15, 0.85])
        
        with rank_l: # Logo 欄位
            logo_urls = get_logos()
            st.markdown('<div class="logo-sidebar">', unsafe_allow_html=True)
            # 依照排序從下往上顯示 Logo (因為 Plotly 橫向圖底部是第一個)
            for ticker in reversed(sorted_contrib.index):
                st.image(logo_urls.get(ticker), width=22)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with rank_r: # 長條圖欄位
            fig_bar = go.Figure(go.Bar(
                y=sorted_contrib.index, x=sorted_contrib.values, orientation='h',
                marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in sorted_contrib.values],
                text=sorted_contrib.values.round(1), textposition='outside'
            ))
            fig_bar.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=40, t=0, b=0), height=380,
                xaxis=dict(visible=False), 
                yaxis=dict(showgrid=False, tickfont=dict(size=12, family="Josefin Sans"))
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"SYSTEM OFFLINE: {str(e)}")
