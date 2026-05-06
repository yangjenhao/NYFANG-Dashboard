import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. DESIGN TOKENS (移除硬編碼背景色) ---
COLORS = {
    "gold": "#D4AF37", 
    "up": "#3da35d", 
    "down": "#e05e5e",
    "muted": "#8d8680"
}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

# CSS 修正：讓背景隨系統切換，卡片使用 RGBA 透明度
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['gold']} !important; text-align: center; font-size: 2.2rem; margin: 10px 0; }}
    .metric-card {{ background-color: rgba(128, 128, 128, 0.1); border: 1px solid {COLORS['gold']}33; padding: 15px; text-align: center; border-radius: 4px; }}
    section[data-testid="stSidebar"] {{ border-right: 1px solid rgba(128, 128, 128, 0.2); }}
    .sidebar-content {{ padding: 10px; font-size: 0.85rem; opacity: 0.8; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC (加入安全檢查防止 KeyError) ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"
DOMAIN_MAP = {
    "META": "meta.com", "AAPL": "apple.com", "AMZN": "amazon.com", "NFLX": "netflix.com", 
    "MSFT": "microsoft.com", "GOOGL": "google.com", "MU": "micron.com", 
    "NVDA": "nvidia.com", "PLTR": "palantir.com", "AVGO": "broadcom.com"
}

@st.cache_data(ttl=60)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    interval = "1m" if p == "1d" else "1d"
    # 修正：確保抓取時處理 MultiIndex 結構
    data = yf.download(all_symbols, period=p, interval=interval, progress=False, auto_adjust=True)
    if data.empty: return pd.DataFrame()
    
    # 檢查 Close 欄位是否存在
    df = data['Close'] if 'Close' in data.columns else data
    
    if p == "1d" and df.index.tz is not None:
        df.index = df.index.tz_convert('America/New_York').tz_localize(None)
    return df.ffill().dropna()

# --- 3. SIDEBAR TERMINAL ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus; letter-spacing:2px;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='sidebar-content'>
            <p><b>AUTHOR:</b> Jen-Hao Yang</p>
            <p><b>SYSTEM:</b> NYSE FANG+ ENGINE</p>
            <hr style="opacity: 0.2;">
            <p>STATUS: <span style="color:{COLORS['up']};">ONLINE</span></p>
            <p style="font-size:0.75rem;">Theme: Adaptive Mode<br>Key Check: ACTIVE</p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. MAIN UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)
period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    
    # 安全檢查：若缺少欄位則停止執行，避免 KeyError
    if INDEX_SYMBOL not in df.columns:
        st.error(f"Missing data for {INDEX_SYMBOL}. Please refresh.")
        st.stop()

    idx_series = df[INDEX_SYMBOL]
    start, end = idx_series.iloc[0], idx_series.iloc[-1]
    total_change = end - start
    
    c1, c2, c3 = st.columns(3)
    val_color = COLORS['up'] if total_change >= 0 else COLORS['down']
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">VALUE</p><h2>{end:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">SHIFT</p><h2 style="color:{val_color}">{total_change:+.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">VAR %</p><h2 style="color:{val_color}">{(total_change/start*100):+.2f}%</h2></div>', unsafe_allow_html=True)

    returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    col1, col2 = st.columns([1.2, 1])
    
    with col1: # 趨勢圖 (移除 template="plotly_dark")
        fig_idx = go.Figure(go.Scatter(x=idx_series.index, y=idx_series.values, line=dict(color=COLORS['gold'], width=2, shape='spline'), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)'))
        fig_idx.update_layout(
            template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=450, margin=dict(t=20, b=20),
            xaxis=dict(showgrid=False, fixedrange=True, rangebreaks=[dict(bounds=["sat", "mon"])] if selected_label != "1D" else None),
            yaxis=dict(gridcolor='rgba(128,128,128,0.2)', fixedrange=True, tickformat=".0f"),
            hovermode="x unified"
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2: # 貢獻圖 (移除 template="plotly_dark")
        logo_imgs = [dict(source=f"https://www.google.com/s2/favicons?sz=128&domain={DOMAIN_MAP.get(t, 'google.com')}", xref="paper", yref="y", x=-0.12, y=i, sizex=0.08, sizey=0.7, xanchor="center", yanchor="middle", sizing="contain", layer="above") for i, t in enumerate(row.index)]
        fig_bar = go.Figure(go.Bar(y=row.index, x=row.values, orientation='h', marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], text=row.values.round(2), textposition='outside'))
        fig_bar.update_layout(
            template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, margin=dict(l=140, r=60, t=50, b=20),
            images=logo_imgs,
            yaxis=dict(ticksuffix="      ", fixedrange=True),
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=14))
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Application Error: {e}")
