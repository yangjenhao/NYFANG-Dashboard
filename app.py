import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. DESIGN TOKENS ---
COLORS = {
    "bg": "#0A0A0A", 
    "card_bg": "#141414", 
    "fg": "#F2F0E4", 
    "gold": "#D4AF37", 
    "muted": "#888888", 
    "up": "#00FF00", 
    "down": "#FF0000"
}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

# 強制注入 CSS 優化介面
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['gold']} !important; text-align: center; font-size: 2.2rem; margin: 10px 0; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 15px; text-align: center; border-radius: 4px; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
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
    # 1D 使用 1m 間隔，其餘使用 1d
    interval = "1m" if p == "1d" else "1d"
    data = yf.download(all_symbols, period=p, interval=interval, progress=False, auto_adjust=False)['Close']
    if p == "1d" and data.index.tz is not None:
        data.index = data.index.tz_convert('America/New_York').tz_localize(None)
    return data.ffill().dropna()

# --- 3. UI LAYOUT ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    start, end = df.iloc[0], df.iloc[-1]
    total_change = end[INDEX_SYMBOL] - start[INDEX_SYMBOL]
    
    # 1. 核心數據指標 (Metrics)
    c1, c2, c3 = st.columns(3)
    color = COLORS['up'] if total_change >= 0 else COLORS['down']
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}">VALUE</p><h2 style="color:{color}">{end[INDEX_SYMBOL]:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}">SHIFT</p><h2 style="color:{color}">{total_change:+.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}">VAR %</p><h2 style="color:{color}">{(total_change/start[INDEX_SYMBOL]*100):+.2f}%</h2></div>', unsafe_allow_html=True)

    # 2. 貢獻度計算
    # 權重各佔 10%，計算各股對指數點數變動的實際貢獻
    returns = (end[OFFICIAL_TICKERS] / start[OFFICIAL_TICKERS]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    # 根據指數實際跳動點數按比例回推貢獻
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    # 3. 圖表展示
    col1, col2 = st.columns([1.2, 1])
    
    with col1: # 左側：指數走勢圖
        fig_idx = go.Figure(go.Scatter(
            x=df.index, y=df[INDEX_SYMBOL], 
            line=dict(color=COLORS['gold'], width=2),
            fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)'
        ))
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=480, margin=dict(t=30, b=20),
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#222')
        )
        st.plotly_chart(fig_idx, use_container_width=True)

    with col2: # 右側：個股貢獻度 (含 Logo)
        logo_imgs = []
        for ticker in row.index:
            domain = DOMAIN_MAP.get(ticker, "google.com")
            logo_imgs.append(dict(
                source=f"https://www.google.com/s2/favicons?sz=64&domain={domain}",
                xref="paper", yref="y",
                x=-0.08, y=ticker, # 直接綁定 y 軸名稱
                sizex=0.07, sizey=0.7,
                xanchor="right", yanchor="middle",
                sizing="contain"
            ))

        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2), textposition='outside',
            cliponaxis=False
        ))
        
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=480, margin=dict(l=120, r=60, t=50, b=20),
            title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=16)),
            images=logo_imgs,
            yaxis=dict(
                tickfont=dict(size=12),
                tickprefix="      ", # 增加前綴空白，為 Logo 留出視覺緩衝空間
                fixedrange=True
            ),
            xaxis=dict(showgrid=True, gridcolor='#222', zerolinecolor=COLORS['muted'])
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"SYSTEM OFFLINE: {e}")
