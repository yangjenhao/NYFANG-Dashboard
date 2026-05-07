import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. LINEAR DESIGN TOKENS ---
COLORS = {
    "bg_base": "#050506",
    "bg_elevated": "#0a0a0c",
    "accent": "#5E6AD2",
    "accent_glow": "rgba(94, 106, 210, 0.15)",
    "text_main": "#EDEDEF",
    "text_muted": "#8A8F98",
    "border": "rgba(255, 255, 255, 0.08)",
    "up": "#4ADE80",
    "down": "#F87171"
}

st.set_page_config(page_title="FANG+ LINEAR TERMINAL", layout="wide")

# --- 2. CSS ENGINE (LINEAR SPEC) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* 背景：放射狀漸層 + 雜訊紋理 */
    .stApp {{ 
        background-color: {COLORS['bg_base']} !important; 
        font-family: 'Inter', sans-serif;
        background-image: 
            radial-gradient(circle at 50% -20%, #1e1e2d 0%, {COLORS['bg_base']} 80%),
            url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.02'/%3E%3C/svg%3E");
    }}
    
    /* 標題：Linear 招牌消散型漸層 */
    .main-title {{ 
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.04em !important;
        background: linear-gradient(to bottom, #ffffff 0%, rgba(255,255,255,0.7) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; 
        font-size: 3rem; 
        margin: 20px 0; 
    }}
    
    /* 側邊欄：磨砂玻璃效果 */
    section[data-testid="stSidebar"] {{ 
        background-color: rgba(10, 10, 12, 0.7) !important; 
        backdrop-filter: blur(12px);
        border-right: 1px solid {COLORS['border']}; 
    }}

    .block-container {{
        max-width: 1100px !important;
        padding-top: 2rem;
    }}

    /* 現代化指標卡 */
    .metric-card {{
        flex: 1;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid {COLORS['border']};
        border-top: 1px solid rgba(255, 255, 255, 0.15); /* 頂部亮邊線 */
        padding: 20px;
        text-align: center;
        border-radius: 12px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    }}

    /* 時間選擇器樣式 */
    div[data-testid="stSegmentedControl"] {{
        background: rgba(255, 255, 255, 0.03);
        padding: 4px;
        border-radius: 8px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"
DOMAIN_MAP = {t: f"{t.lower()}.com" for t in OFFICIAL_TICKERS} # 簡化映射

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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<div style='color:{COLORS['accent']}; font-weight:600; letter-spacing:1px; font-size:0.9rem;'>SYSTEM TERMINAL</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='margin-top:20px; font-size:0.8rem; color:{COLORS['text_muted']};'>
            <p>CORE: <span style="color:white;">NYSE FANG+</span></p>
            <p>STATUS: <span style="color:{COLORS['up']};">OPERATIONAL</span></p>
            <hr style="opacity: 0.1;">
            <p style="font-size:0.7rem;">PRECISION TRADING INTERFACE v2.0</p>
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    idx_series = df[INDEX_SYMBOL]
    start, end = idx_series.iloc[0], idx_series.iloc[-1]
    total_change = end - start
    val_color = COLORS['up'] if total_change >= 0 else COLORS['down']
    
    # 指標卡布局
    st.markdown(f"""
    <div style="display: flex; gap: 16px; margin-bottom: 25px;">
        <div class="metric-card">
            <div style="color:{COLORS['text_muted']}; font-size:0.7rem; font-weight:600; margin-bottom:8px; letter-spacing:1px;">MARKET VALUE</div>
            <div style="font-size:1.5rem; font-weight:600; color:{COLORS['text_main']};">{end:,.2f}</div>
        </div>
        <div class="metric-card">
            <div style="color:{COLORS['text_muted']}; font-size:0.7rem; font-weight:600; margin-bottom:8px; letter-spacing:1px;">PERIOD SHIFT</div>
            <div style="font-size:1.5rem; font-weight:600; color:{val_color};">{total_change:+.2f}</div>
        </div>
        <div class="metric-card">
            <div style="color:{COLORS['text_muted']}; font-size:0.7rem; font-weight:600; margin-bottom:8px; letter-spacing:1px;">VARIANCE %</div>
            <div style="font-size:1.5rem; font-weight:600; color:{val_color};">{(total_change/start*100):+.2f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 圖一：趨勢圖 (Linear Glow Style) ---
    y_min, y_max = idx_series.min(), idx_series.max()
    padding = (y_max - y_min) * 0.1
    
    fig_idx = go.Figure(go.Scatter(
        x=idx_series.index, y=idx_series.values, 
        line=dict(color=COLORS['accent'], width=2.5),
        fill='tozeroy', fillcolor='rgba(94, 106, 210, 0.05)', 
        hoverinfo="x+y"
    ))
    
    fig_idx.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
        height=400, margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(
            showgrid=False, tickfont=dict(color=COLORS['text_muted'], size=10),
            tickformat=( "%H:%M" if selected_label == "1D" else "%Y-%m-%d" if selected_label in ["1Y", "2Y", "MAX"] else "%m-%d"),
            rangebreaks=[dict(bounds=["sat", "mon"])] if selected_label != "1D" else None
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.03)', range=[y_min - padding, y_max + padding],
            tickfont=dict(color=COLORS['text_muted'], size=10), side="right"
        ),
        hovermode="x unified"
    )
    st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    # --- 圖二：貢獻度圖 (Technical Bar) ---
    returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    fig_bar = go.Figure(go.Bar(
        y=row.index, x=row.values, orientation='h',
        marker=dict(
            color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            line=dict(width=0)
        ),
        text=row.values.round(2), textposition='outside',
        textfont=dict(color=COLORS['text_muted'], size=11)
    ))
    
    fig_bar.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=500, margin=dict(l=80, r=80, t=50, b=40),
        title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['text_main'], size=14), x=0.5),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)', tickfont=dict(color=COLORS['text_muted'])),
        yaxis=dict(tickfont=dict(color=COLORS['text_main'], size=12), fixedrange=True),
        bargap=0.4
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")
