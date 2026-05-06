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

# CSS 修正：重點在於強制 Segmented Control 不換行與橫向捲動
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

    /* 修正問題 1：強制時間軸按鈕在一行，並在手機上可橫向滑動 */
    div[data-testid="stSegmentedControl"] > div {{
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        scrollbar-width: none; /* 隱藏捲軸 Firefox */
    }}
    div[data-testid="stSegmentedControl"] > div::-webkit-scrollbar {{
        display: none; /* 隱藏捲軸 Chrome/Safari */
    }}
    div[data-testid="stSegmentedControl"] button {{
        flex-shrink: 0 !important; /* 防止按鈕被擠壓 */
        min-width: 60px !important;
    }}
    
    section[data-testid="stSidebar"] {{ 
        background-color: #252525 !important; 
        border-right: 1px solid rgba(128, 128, 128, 0.1); 
    }}

    .block-container {{
        max-width: 1000px !important;
        padding-top: 1.5rem;
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
        st.stop()

    idx_series = df[INDEX_SYMBOL]
    start, end = idx_series.iloc[0], idx_series.iloc[-1]
    total_change = end - start
    val_color = COLORS['up'] if total_change >= 0 else COLORS['down']
    
    # 指標卡片 HTML (確保手機並排)
    st.markdown(f"""
    <div style="display: flex; flex-direction: row; justify-content: space-between; gap: 8px; width: 100%; margin-bottom: 20px;">
        <div style="flex: 1; background-color: rgba(128, 128, 128, 0.05); border: 1px solid {COLORS['gold']}22; padding: 12px 5px; text-align: center; border-radius: 6px;">
            <div style="color:{COLORS['gold']}; font-size:0.7rem; font-weight:600; margin-bottom:4px;">VALUE</div>
            <div style="font-size:1rem; font-weight:bold; color:white;">{end:,.2f}</div>
        </div>
        <div style="flex: 1; background-color: rgba(128, 128, 128, 0.05); border: 1px solid {COLORS['gold']}22; padding: 12px 5px; text-align: center; border-radius: 6px;">
            <div style="color:{COLORS['gold']}; font-size:0.7rem; font-weight:600; margin-bottom:4px;">SHIFT</div>
            <div style="font-size:1rem; font-weight:bold; color:{val_color};">{total_change:+.2f}</div>
        </div>
        <div style="flex: 1; background-color: rgba(128, 128, 128, 0.05); border: 1px solid {COLORS['gold']}22; padding: 12px 5px; text-align: center; border-radius: 6px;">
            <div style="color:{COLORS['gold']}; font-size:0.7rem; font-weight:600; margin-bottom:4px;">VAR %</div>
            <div style="font-size:1rem; font-weight:bold; color:{val_color};">{(total_change/start*100):+.2f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    # --- 圖一：趨勢圖 ---
    fig_idx = go.Figure(go.Scatter(
        x=idx_series.index, y=idx_series.values, 
        line=dict(color=COLORS['gold'], width=2, shape='spline'),
        fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)'
    ))
    fig_idx.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
        height=380, margin=dict(t=20, b=40, l=10, r=10),
        xaxis=dict(showgrid=False, tickfont=dict(color=COLORS['muted'], size=10)),
        yaxis=dict(gridcolor='rgba(128,128,128,0.1)', tickfont=dict(color=COLORS['muted'], size=10)),
        hovermode="x unified"
    )
    st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    # --- 圖二：貢獻度圖 (修正 Logo 重疊問題) ---
    # 修正重點 2：將 Logo 鎖定在標籤左側 (x=-0.08) 並向右對齊 (xanchor="right")
    logo_imgs = [dict(
        source=f"https://www.google.com/s2/favicons?sz=128&domain={DOMAIN_MAP.get(t, 'google.com')}",
        xref="paper", yref="y", 
        x=-0.08, # 固定在一個較遠的負座標
        y=i,
        sizex=0.035, sizey=0.45, 
        xanchor="right", # 向右對齊，確保不論圖表多寬，Logo 都會貼在文字左邊
        yanchor="middle", sizing="contain", layer="above"
    ) for i, t in enumerate(row.index)]

    ticker_labels = [dict(
        xref="paper", yref="y", 
        x=-0.07, # 標籤緊隨 Logo 之後
        y=i,
        text=f"<b>{t}</b>",
        showarrow=False, xanchor="left", yanchor="middle",
        font=dict(size=11, color=COLORS['muted'], family="Josefin Sans")
    ) for i, t in enumerate(row.index)]

    fig_bar = go.Figure(go.Bar(
        y=row.index, x=row.values, orientation='h',
        marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
        text=row.values.round(2), textposition='outside',
        textfont=dict(color=COLORS['muted'], size=10), cliponaxis=False 
    ))
    
    fig_bar.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=550, margin=dict(l=100, r=40, t=50, b=40),
        images=logo_imgs, annotations=ticker_labels,
        yaxis=dict(showticklabels=False, fixedrange=True),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.05)', fixedrange=True),
        title=dict(text=f"CONTRIBUTION ({selected_label})", x=0.5, font=dict(color=COLORS['gold'], size=16)),
        bargap=0.3 
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"系統錯誤: {e}")
