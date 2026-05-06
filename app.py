import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. DESIGN TOKENS ---
COLORS = {
    "gold": "#D4AF37", 
    "up": "#3da35d", 
    "down": "#e05e5e",
    "muted": "#8d8680"
}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

# CSS 優化：時間軸深度縮小、指標卡響應式對齊
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    
    .stApp {{ 
        background-color: #1E1E1E !important; 
        font-family: 'Josefin Sans', sans-serif; 
    }}
    
    .main-title {{ 
        font-family: 'Marcellus', serif !important; 
        text-transform: uppercase; 
        color: {COLORS['gold']} !important; 
        text-align: center; 
        font-size: 2.2rem; 
        margin: 10px 0; 
    }}
    
    /* --- 指標卡響應式佈局 --- */
    .metrics-container {{
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        gap: 12px;
        width: 100%;
        margin-bottom: 20px;
    }}
    
    .metric-card {{
        flex: 1;
        background-color: rgba(128, 128, 128, 0.05);
        border: 1px solid {COLORS['gold']}22;
        padding: 16px 5px;
        text-align: center;
        border-radius: 6px;
    }}

    /* 當螢幕較窄時自動垂直堆疊指標卡 */
    @media (max-width: 768px) {{
        .metrics-container {{
            flex-direction: column !important;
        }}
        .metric-card {{
            width: 100%;
        }}
    }}

    /* --- 時間軸 (Timeline) 深度縮小與防換行控制 --- */
    div[data-testid="stSegmentedControl"] {{
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none; 
    }}
    div[data-testid="stSegmentedControl"]::-webkit-scrollbar {{
        display: none; 
    }}
    div[data-testid="stSegmentedControl"] > div {{
        flex-wrap: nowrap !important;
        gap: 2px !important; /* 縮小按鈕之間的間距 */
    }}
    div[data-testid="stSegmentedControl"] span {{
        font-size: 0.75rem !important; /* 強制縮小字體 */
    }}
    div[data-testid="stSegmentedControl"] label {{
        padding: 2px 8px !important; /* 減少按鈕內距 */
        min-height: 30px !important; /* 降低按鈕高度 */
    }}
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
    interval = "1m" if p == "1d" else "1d"
    data = yf.download(all_symbols, period=p, interval=interval, progress=False, auto_adjust=True)
    if data.empty: return pd.DataFrame()
    df = data['Close'] if 'Close' in data.columns else data
    if p == "1d" and df.index.tz is not None:
        df.index = df.index.tz_convert('America/New_York').tz_localize(None)
    return df.ffill().dropna()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus; letter-spacing:2px;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.write("---")
    st.caption("AUTHOR: Jen-Hao Yang")

# --- 4. MAIN UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

# 依照要求：移除 YTD, 將 5Y 改為 2Y
period_map = {
    "1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", 
    "1Y": "1y", "2Y": "2y", "MAX": "max"
}

# 使用 st.columns 限制時間軸在電腦版的最大寬度，使其保持小巧
col_tl, col_fill = st.columns([6, 4])
with col_tl:
    selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    if INDEX_SYMBOL not in df.columns:
        st.stop()

    idx_series = df[INDEX_SYMBOL]
    start, end = idx_series.iloc[0], idx_series.iloc[-1]
    total_change = end - start
    val_color = COLORS['up'] if total_change >= 0 else COLORS['down']
    
    # 渲染響應式指標卡
    metrics_html = f"""
    <div class="metrics-container">
        <div class="metric-card">
            <div style="color:{COLORS['gold']}; font-size:0.75rem; font-weight:600; margin-bottom:6px;">VALUE</div>
            <div style="font-size:1.2rem; font-weight:bold; color:white;">{end:,.2f}</div>
        </div>
        <div class="metric-card">
            <div style="color:{COLORS['gold']}; font-size:0.75rem; font-weight:600; margin-bottom:6px;">SHIFT</div>
            <div style="font-size:1.2rem; font-weight:bold; color:{val_color};">{total_change:+.2f}</div>
        </div>
        <div class="metric-card">
            <div style="color:{COLORS['gold']}; font-size:0.75rem; font-weight:600; margin-bottom:6px;">VAR %</div>
            <div style="font-size:1.2rem; font-weight:bold; color:{val_color};">{(total_change/start*100):+.2f}%</div>
        </div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)

    returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    # --- 圖一：趨勢圖 ---
    y_min, y_max = idx_series.min(), idx_series.max()
    padding = (y_max - y_min) * 0.15 if y_max != y_min else 10
    
    fig_idx = go.Figure(go.Scatter(
        x=idx_series.index, y=idx_series.values, 
        line=dict(color=COLORS['gold'], width=2, shape='spline'),
        fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)', hoverinfo="x+y"
    ))
    fig_idx.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
        height=380, margin=dict(t=20, b=40, l=50, r=10),
        xaxis=dict(showgrid=False, tickformat="%H:%M" if selected_label == "1d" else "%m-%d", tickfont=dict(color=COLORS['muted'], size=10)),
        yaxis=dict(gridcolor='rgba(128,128,128,0.1)', range=[y_min - padding, y_max + padding], tickformat=".0f", tickfont=dict(color=COLORS['muted'], size=10)),
        hovermode="x unified"
    )
    st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    # --- 圖二：貢獻度圖 (僅保留 Logo) ---
    val_min, val_max = row.min(), row.max()
    val_range = val_max - val_min if val_max != val_min else 10
    dynamic_x_min = val_min - (val_range * 0.25)
    dynamic_x_max = val_max + (val_range * 0.25)

    logo_imgs = [dict(
        source=f"https://www.google.com/s2/favicons?sz=128&domain={DOMAIN_MAP.get(t, 'google.com')}",
        xref="paper", yref="y", 
        x=-0.015, 
        y=i,
        sizex=0.045, sizey=0.45, 
        xanchor="right", yanchor="middle", sizing="contain", layer="above"
    ) for i, t in enumerate(row.index)]

    fig_bar = go.Figure(go.Bar(
        y=row.index, x=row.values, orientation='h',
        marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
        text=row.values.round(2), textposition='outside',
        textfont=dict(color=COLORS['muted'], size=10), cliponaxis=False 
    ))
    
    fig_bar.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=550, 
        margin=dict(l=60, r=60, t=50, b=40), 
        images=logo_imgs,
        yaxis=dict(showticklabels=False, fixedrange=True), 
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.05)', fixedrange=True, range=[dynamic_x_min, dynamic_x_max]),
        title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=16), x=0.5, xanchor="center"),
        bargap=0.3 
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"系統錯誤: {e}")
