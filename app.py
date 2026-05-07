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
    
    section[data-testid="stSidebar"] {{ 
        background-color: #252525 !important; 
        border-right: 1px solid rgba(128, 128, 128, 0.1); 
    }}

    /* ⭐ 關鍵：放寬整體寬度 */
    .block-container {{
        max-width: 1400px !important;
        padding-top: 1.5rem;
    }}

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
        min-width: min-content;
    }}
    </style>
""", unsafe_allow_html=True)

# --- DATA ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=60)
def fetch_data(p):
    data = yf.download(OFFICIAL_TICKERS + [INDEX_SYMBOL], period=p,
                       interval="1m" if p == "1d" else "1d",
                       progress=False, auto_adjust=True)
    if data.empty:
        return pd.DataFrame()
    df = data['Close']
    return df.ffill().dropna()

# --- UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

df = fetch_data(period_map[selected_label])

idx_series = df[INDEX_SYMBOL]
start, end = idx_series.iloc[0], idx_series.iloc[-1]
total_change = end - start

returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
row = (returns * total_change).sort_values()

# ⭐ 比例加大
col1, col2 = st.columns([1.7, 1], gap="large")

# --- 圖1 ---
fig_idx = go.Figure(go.Scatter(
    x=idx_series.index,
    y=idx_series.values,
    line=dict(color=COLORS['gold'], width=2),
    fill='tozeroy'
))

fig_idx.update_layout(
    template="none",
    height=620,  # ⭐ 放大
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

# --- 圖2 ---
fig_bar = go.Figure(go.Bar(
    y=row.index,
    x=row.values,
    orientation='h',
    marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values]
))

fig_bar.update_layout(
    template="none",
    height=620,  # ⭐ 放大
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

with col1:
    st.plotly_chart(fig_idx, use_container_width=True)

with col2:
    st.plotly_chart(fig_bar, use_container_width=True)
