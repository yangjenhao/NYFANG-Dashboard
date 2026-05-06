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
    
    .metric-card {{ 
        background-color: rgba(128, 128, 128, 0.05); 
        border: 1px solid {COLORS['gold']}22; 
        padding: 15px; 
        text-align: center; 
        border-radius: 4px; 
        margin-bottom: 10px;
    }}
    
    section[data-testid="stSidebar"] {{ 
        background-color: #252525 !important; 
        border-right: 1px solid rgba(128, 128, 128, 0.1); 
    }}

    /* 優化手機端欄位間距 */
    @media (max-width: 768px) {{
        [data-testid="column"] {{
            margin-bottom: 20px;
        }}
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
    st.markdown(f"""
        <div style='padding:10px; font-size:0.85rem; opacity:0.8;'>
            <p><b>AUTHOR:</b> Jen-Hao Yang</p>
            <p><b>SYSTEM:</b> NYSE FANG+ ENGINE</p>
            <hr style="opacity: 0.2;">
            <p>STATUS: <span style="color:{COLORS['up']};">ONLINE</span></p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. MAIN UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    if INDEX_SYMBOL not in df.columns:
        st.error(f"數據缺失：找不到 {INDEX_SYMBOL}")
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

    # 建立兩欄佈局
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        y_min, y_max = idx_series.min(), idx_series.max()
        padding = (y_max - y_min) * 0.15 if y_max != y_min else 10
        
        fig_idx = go.Figure(go.Scatter(
            x=idx_series.index, y=idx_series.values, 
            line=dict(color=COLORS['gold'], width=2, shape='spline'),
            fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)',
            hoverinfo="x+y"
        ))
        
        fig_idx.update_layout(
            template="none", 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=400, # 微調高度適合手機垂直堆疊
            margin=dict(t=20, b=40, l=10, r=10),
            hoverlabel=dict(bgcolor="#FF3333", font_color="#FFFFFF"),
            xaxis=dict(
                showgrid=False, fixedrange=True, showspikes=True,
                spikecolor="#FF3333", spikethickness=1,
                tickformat="%H:%M" if selected_label == "1d" else "%m-%d",
                tickfont=dict(color=COLORS['muted'], size=10),
                rangebreaks=[dict(bounds=["sat", "mon"])] if selected_label != "1d" else None
            ),
            yaxis=dict(
                gridcolor='rgba(128,128,128,0.1)',
                range=[y_min - padding, y_max + padding],
                fixedrange=True, tickformat=".0f",
                tickfont=dict(color=COLORS['muted'], size=10)
            ),
            hovermode="x unified"
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # 1. 調整 Logo 位置：x 座標縮小至 -0.12 ~ -0.15 之間，防止寬螢幕時噴掉
        logo_imgs = [dict(
            source=f"https://www.google.com/s2/favicons?sz=128&domain={DOMAIN_MAP.get(t, 'google.com')}",
            xref="paper", yref="y", 
            x=-0.14,          # 修正重點：縮短與圖表邊界的距離
            y=i,
            sizex=0.045, sizey=0.45, 
            xanchor="left", yanchor="middle", sizing="contain", layer="above"
        ) for i, t in enumerate(row.index)]

        # 2. 調整 Ticker 文字位置：x 緊貼 Logo
        ticker_labels = [dict(
            xref="paper", yref="y",
            x=-0.09,          # 修正重點：讓文字靠近 y 軸邊界
            y=i,
            text=f"<b>{t}</b>",
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(size=11, color=COLORS['muted'], family="Josefin Sans")
        ) for i, t in enumerate(row.index)]

        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2), textposition='outside',
            textfont=dict(color=COLORS['muted'], size=10),
            cliponaxis=False 
        ))
        
        fig_bar.update_layout(
            template="none",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, 
            # 3. 邊距修正：電腦版 l=100 即可提供充足空間，不至於讓圖表太瘦
            margin=dict(l=100, r=50, t=50, b=20), 
            images=logo_imgs,
            annotations=ticker_labels,
            yaxis=dict(showticklabels=False, fixedrange=True),
            xaxis=dict(
                showgrid=True, 
                gridcolor='rgba(128,128,128,0.05)', 
                fixedrange=True,
                side="bottom"
            ),
            title=dict(
                text=f"CONTRIBUTION ({selected_label})", 
                font=dict(color=COLORS['gold'], size=14, family="Josefin Sans"),
                x=0.5, xanchor="center"
            ),
            bargap=0.35 
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"系統錯誤: {e}")
