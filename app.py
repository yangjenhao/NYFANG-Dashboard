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
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 10px; text-align: center; margin-bottom: 8px; border-radius: 4px; }}
    .metric-label {{ color: {COLORS['gold']}; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }}
    .metric-value {{ font-size: 1.4rem; font-weight: 600; line-height: 1.2; }}
    .performance-sub {{ font-size: 0.9rem; margin-top: 2px; opacity: 0.9; }}
    .logo-container {{ display: flex; align-items: center; gap: 10px; margin-bottom: 5px; padding: 5px; border-bottom: 1px solid #222; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=3600)
def get_logos():
    """獲取成分股 Logo URL"""
    logos = {}
    for t in OFFICIAL_TICKERS:
        try:
            # 優先使用 Clearbit 的 API，因為 yfinance info 有時較慢
            logos[t] = f"https://logo.clearbit.com/{t.lower()}.com"
        except:
            logos[t] = None
    return logos

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    if p == "1d":
        data = yf.download(all_symbols, period="1d", interval="1m", progress=False, auto_adjust=False)['Close']
        if data.index.tz is not None: data.index = data.index.tz_convert('America/New_York').tz_localize(None)
    elif p == "5d":
        raw = yf.download(all_symbols, period="1mo", interval="1d", progress=False, auto_adjust=False)['Close']
        data = raw.dropna(subset=[INDEX_SYMBOL]).tail(5)
    else:
        data = yf.download(all_symbols, period=p, interval="1d", progress=False, auto_adjust=False)['Close']
    return data.ffill().dropna()

# --- 3. SIDEBAR (LOGO DASHBOARD) ---
logo_urls = get_logos()
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus;'>CONSTITUENTS</h2>", unsafe_allow_html=True)
    for ticker in OFFICIAL_TICKERS:
        col_l, col_t = st.columns([1, 3])
        with col_l:
            st.image(logo_urls.get(ticker), width=25)
        with col_t:
            st.markdown(f"<p style='font-size:0.9rem; margin-top:2px;'>{ticker}</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<p style='font-size:0.7rem; color:{COLORS['muted']}; text-align:center;'>NYSE FANG+ TERMINAL v2.0</p>", unsafe_allow_html=True)

# --- 4. MAIN LAYOUT ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")
period_val = period_map[selected_label]

try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    start_v, end_v = df.iloc[0][INDEX_SYMBOL], df.iloc[-1][INDEX_SYMBOL]
    
    diff = end_v - start_v
    pct = (diff / start_v) * 100
    shift_col = COLORS['up'] if diff >= 0 else COLORS['down']

    # --- 行動端優化佈局 ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Value</div><div class="metric-value" style="color:{shift_col};">{end_v:,.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Performance ({selected_label})</div><div class="metric-value" style="color:{shift_col};">{diff:+.2f} <span style="font-size:0.9rem;">({pct:+.2f}%)</span></div></div>', unsafe_allow_html=True)

    # 歸因計算
    stock_returns = (df.iloc[-1][OFFICIAL_TICKERS] / df.iloc[0][OFFICIAL_TICKERS]) - 1
    total_raw = (stock_returns * 0.1).sum()
    cum_contrib = (stock_returns * 0.1 * (diff / total_raw)) if abs(total_raw) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)

    col1, col2 = st.columns([1, 1])
    
    with col1:
        y_min, y_max = idx_series.min(), idx_series.max()
        pad = (y_max - y_min) * (0.1 if len(selected_label) > 2 else 0.05)
        
        fig_idx = go.Figure(go.Scatter(
            x=df.index if (period_val == '1d' or len(selected_label) > 2) else df.index.strftime('%m/%d'), 
            y=idx_series, fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.03)', 
            line=dict(color=COLORS['gold'], width=2), hoverinfo="y"
        ))
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=5, r=5, t=10, b=5), height=300,
            xaxis=dict(showgrid=False, nticks=4), yaxis=dict(showgrid=True, gridcolor='#222', range=[y_min - pad, y_max + pad]),
            hovermode="x"
        )
        if period_val == '1d':
            fig_idx.update_xaxes(rangebreaks=[dict(bounds=[16, 9.5], pattern="hour"), dict(bounds=["sat", "mon"])])
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # 在圖表上方加入帶有 Logo 的標題區塊
        st.markdown(f"<p style='color:{COLORS['gold']}; font-size:0.8rem; margin-bottom:10px;'>CONTRIBUTION RANKING</p>", unsafe_allow_html=True)
        
        row = cum_contrib.sort_values(ascending=True)
        # Plotly 不支援在 y 軸直接插圖片，因此我們維持文字，但在側邊欄已補齊視覺引導
        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], 
            text=row.values.round(1), textposition='auto'
        ))
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=5, r=5, t=5, b=5), height=350, 
            yaxis=dict(fixedrange=True, side="right"), # 將標籤放右邊，更適合手機滑動
            xaxis=dict(fixedrange=True, showgrid=True, gridcolor='#222')
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"SYSTEM OFFLINE: {str(e)}")
