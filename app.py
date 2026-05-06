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

# CSS 修正：1. 高度統一 2. 指標橫列置中 3. 時間軸不換行
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

    /* 修正 2：強制指標卡片在手機版維持一橫列並置中 */
    .metric-row {{
        display: flex;
        justify-content: center;
        gap: 8px;
        margin: 15px auto;
        max-width: 1000px;
    }}
    
    .metric-card {{ 
        flex: 1;
        background-color: rgba(128, 128, 128, 0.05); 
        border: 1px solid {COLORS['gold']}22; 
        padding: 12px 5px; 
        text-align: center; 
        border-radius: 4px;
        min-width: 0;
    }}
    
    .metric-card h2 {{ font-size: 1.1rem !important; margin: 0; }}
    .metric-card p {{ margin: 0; font-size: 0.7rem; }}

    /* 修正 3：強制時間軸按鈕不換行且置中 */
    div[data-testid="stSegmentedControl"] {{
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }}
    div[data-testid="stSegmentedControl"] > div {{
        flex-wrap: nowrap !important;
        overflow-x: auto;
        justify-content: center;
        gap: 4px;
    }}

    .block-container {{
        max-width: 1100px !important;
        padding-top: 2rem;
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

# --- 3. MAIN UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

# 時間軸按鈕
period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    if INDEX_SYMBOL not in df.columns: st.stop()

    idx_series = df[INDEX_SYMBOL]
    start, end = idx_series.iloc[0], idx_series.iloc[-1]
    total_change = end - start
    val_color = COLORS['up'] if total_change >= 0 else COLORS['down']

    # 修正 2：改用 HTML Flex 結構確保橫排置中
    st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <p style="color:{COLORS["gold"]};">VALUE</p>
                <h2>{end:,.2f}</h2>
            </div>
            <div class="metric-card">
                <p style="color:{COLORS["gold"]};">SHIFT</p>
                <h2 style="color:{val_color}">{total_change:+.2f}</h2>
            </div>
            <div class="metric-card">
                <p style="color:{COLORS["gold"]};">VAR %</p>
                <h2 style="color:{val_color}">{(total_change/start*100):+.2f}%</h2>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 數據計算
    returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    # 修正 1：統一圖表高度與佈局參數
    CHART_HEIGHT = 480
    
    # --- 圖一：趨勢圖 ---
    y_min, y_max = idx_series.min(), idx_series.max()
    padding = (y_max - y_min) * 0.15 if y_max != y_min else 10
    
    fig_idx = go.Figure(go.Scatter(
        x=idx_series.index, y=idx_series.values, 
        line=dict(color=COLORS['gold'], width=2, shape='spline'),
        fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)'
    ))
    fig_idx.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
        height=CHART_HEIGHT, margin=dict(t=30, b=40, l=50, r=30),
        xaxis=dict(showgrid=False, tickfont=dict(color=COLORS['muted'], size=10)),
        yaxis=dict(gridcolor='rgba(128,128,128,0.05)', range=[y_min-padding, y_max+padding]),
        hovermode="x unified"
    )
    st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    # --- 圖二：貢獻度圖 ---
    logo_imgs = [dict(
        source=f"https://www.google.com/s2/favicons?sz=128&domain={DOMAIN_MAP.get(t, 'google.com')}",
        xref="paper", yref="y", x=-0.15, y=i,
        sizex=0.04, sizey=0.5, xanchor="left", yanchor="middle", sizing="contain", layer="above"
    ) for i, t in enumerate(row.index)]

    ticker_labels = [dict(
        xref="paper", yref="y", x=-0.10, y=i, text=f"<b>{t}</b>",
        showarrow=False, xanchor="left", yanchor="middle",
        font=dict(size=12, color=COLORS['muted'], family="Josefin Sans")
    ) for i, t in enumerate(row.index)]

    fig_bar = go.Figure(go.Bar(
        y=row.index, x=row.values, orientation='h',
        marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
        text=row.values.round(2), textposition='outside',
        textfont=dict(color=COLORS['muted'], size=10), cliponaxis=False 
    ))
    
    fig_bar.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=CHART_HEIGHT, margin=dict(l=140, r=40, t=50, b=40), 
        images=logo_imgs, annotations=ticker_labels,
        yaxis=dict(showticklabels=False, fixedrange=True),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.05)'),
        title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=16), x=0.5),
        bargap=0.35 
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"系統錯誤: {e}")
