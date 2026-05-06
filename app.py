import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. DESIGN TOKENS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['gold']} !important; text-align: center; font-size: clamp(1.4rem, 6vw, 2.2rem); margin: 10px 0; }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .sidebar-content {{ padding: 20px; font-size: 0.9rem; color: {COLORS['muted']}; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 12px; text-align: center; margin-bottom: 10px; }}
    div[data-testid="stHorizontalBlock"] {{ justify-content: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    
    if p == "1d":
        data = yf.download(all_symbols, period="1d", interval="1m", progress=False, auto_adjust=False)['Close']
        if data.index.tz is not None: data.index = data.index.tz_convert('America/New_York').tz_localize(None)
    elif p == "5d":
        raw = yf.download(all_symbols, period="1mo", interval="1d", progress=False, auto_adjust=False)['Close']
        raw.index = pd.to_datetime(raw.index).normalize()
        data = raw.dropna(subset=[INDEX_SYMBOL]).tail(5)
    else:
        # 針對 1Y, 5Y, MAX 使用日線
        data = yf.download(all_symbols, period=p, interval="1d", progress=False, auto_adjust=False)['Close']
        data.index = pd.to_datetime(data.index).normalize()
            
    return data.ffill().dropna()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='sidebar-content'>
            <p><b>AUTHOR:</b> Jen-Hao Yang</p>
            <p><b>SYSTEM:</b> NYSE FANG+ TERMINAL</p>
            <hr style="border-color:{COLORS['gold']}22;">
            <p style="font-size:0.8rem;">Historical Depth: MAX.<br>Dynamic Range Scaling: OPTIMIZED.</p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. MAIN LAYOUT ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

# 更新時間軸選項，加入 MAX
period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")
period_val = period_map[selected_label]

try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    
    start_vals = df.iloc[0]
    end_vals = df.iloc[-1]
    
    total_pts_change = end_vals[INDEX_SYMBOL] - start_vals[INDEX_SYMBOL]
    variance = (total_pts_change / start_vals[INDEX_SYMBOL]) * 100
    shift_col = COLORS['up'] if total_pts_change >= 0 else COLORS['down']

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VALUE</p><h3 style="color:{shift_col};">{end_vals[INDEX_SYMBOL]:,.2f}</h3></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">SHIFT ({selected_label})</p><h3 style="color:{shift_col};">{total_pts_change:+.2f}</h3></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VAR %</p><h3 style="color:{shift_col};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

    # 歸因計算
    stock_returns = (end_vals[OFFICIAL_TICKERS] / start_vals[OFFICIAL_TICKERS]) - 1
    raw_impacts = stock_returns * 0.1
    total_impact_sum = raw_impacts.sum()
    cum_contrib = (raw_impacts * (total_pts_change / total_impact_sum)) if abs(total_impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)

    col1, col2 = st.columns([1, 1])
    
    with col1:
        y_min, y_max = idx_series.min(), idx_series.max()
        # 長線（1Y以上）增加緩衝區至 10%，短線維持 5%
        pad_factor = 0.10 if selected_label in ["1Y", "5Y", "MAX"] else 0.05
        y_padding = (y_max - y_min) * pad_factor if (y_max - y_min) > 0 else 10
        
        # 軸線類型：1D 用日期，5D 用類別（去週末），長線用日期（顯示年分）
        is_long_term = selected_label in ["1M", "6M", "YTD", "1Y", "5Y", "MAX"]
        x_axis_data = df.index if (period_val == '1d' or is_long_term) else df.index.strftime('%m/%d')

        fig_idx = go.Figure(go.Scatter(
            x=x_axis_data, y=df[INDEX_SYMBOL], 
            fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.03)', 
            line=dict(color=COLORS['gold'], width=2.5 if not is_long_term else 1.8),
            hoverinfo="x+y"
        ))
        
        xaxis_params = dict(
            type='date' if (period_val == '1d' or is_long_term) else 'category',
            showgrid=False, color=COLORS['muted'], fixedrange=True, nticks=6
        )
        
        if period_val == '1d':
            fig_idx.update_xaxes(rangebreaks=[dict(bounds=[16, 9.5], pattern="hour"), dict(bounds=["sat", "mon"])])

        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=10, r=10, t=20, b=10), height=380, 
            xaxis=xaxis_params,
            yaxis=dict(fixedrange=True, showgrid=True, gridcolor='#222', nticks=6, range=[y_min - y_padding, y_max + y_padding]),
            hovermode="x"
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2:
        row = cum_contrib.sort_values(ascending=True)
        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], 
            text=row.values.round(2), textposition='auto'
        ))
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=10, r=10, t=20, b=10), height=400, 
            yaxis=dict(fixedrange=True), xaxis=dict(fixedrange=True, showgrid=True, gridcolor='#222'),
            title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=14))
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"TERMINAL ERROR: {str(e)}")
