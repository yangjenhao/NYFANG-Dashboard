import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. DESIGN TOKENS & RESPONSIVE CSS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

# 加入手機端專用的 CSS 調整
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    
    /* 響應式標題 */
    h1, .main-title {{ 
        font-family: 'Marcellus', serif !important; 
        text-transform: uppercase; 
        letter-spacing: 0.1em; 
        color: {COLORS['gold']} !important; 
        text-align: center; 
        font-size: clamp(1.2rem, 5vw, 1.8rem); 
        padding: 10px 0;
    }}
    
    /* 指標卡片手機優化 */
    .metric-card {{ 
        background-color: {COLORS['card_bg']}; 
        border: 1px solid {COLORS['gold']}33; 
        padding: 12px; 
        text-align: center; 
        margin-bottom: 8px; 
    }}
    .metric-card h3 {{ font-size: 1.4rem; margin: 0; }}
    .metric-card p {{ margin-bottom: 4px; }}

    /* 隱藏手機端不必要的邊距 */
    @media (max-width: 640px) {{
        .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    is_intraday = (p == "1d")
    fetch_p, interval = ("2d", "1m") if is_intraday else (p, "1d")
    data = yf.download(all_symbols, period=fetch_p, interval=interval, progress=False, auto_adjust=False)['Close']
    if is_intraday:
        if data.index.tz is not None: data.index = data.index.tz_convert('America/New_York').tz_localize(None)
        else: data.index = data.index.tz_localize('UTC').tz_convert('America/New_York').tz_localize(None)
    else: data.index = pd.to_datetime(data.index).normalize()
    return data.ffill().dropna()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}'>TERMINAL</h2>", unsafe_allow_html=True)
    period_options = [('TODAY', '1d'), ('V DAYS', '5d'), ('I MONTH', '1mo'), ('III MONTHS', '3mo'), ('I YEAR', '1y'), ('II YEARS', '2y'), ('V YEARS', '5y'), ('YTD', 'ytd')]
    selected_period = st.selectbox("TIMELINE", options=period_options, format_func=lambda x: x[0], index=0)
    period_val = selected_period[1]
    
    try:
        latest_market_date = fetch_data("1mo").index[-1].date()
    except:
        latest_market_date = datetime.now().date()
    target_date = st.date_input("DEPARTURE DATE", value=latest_market_date)

# --- 4. MAIN CONTENT ---
try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    target_dt = pd.to_datetime(target_date).date()
    available_df = df[df.index.date <= target_dt]
    
    if not available_df.empty:
        start_vals = available_df.iloc[0]
        end_vals = available_df.iloc[-1]
        plot_time = available_df.index[-1]
        
        total_pts_change = end_vals[INDEX_SYMBOL] - start_vals[INDEX_SYMBOL]
        variance = (total_pts_change / start_vals[INDEX_SYMBOL]) * 100
        shift_col = COLORS['up'] if total_pts_change >= 0 else COLORS['down']

        # 歸因計算
        stock_returns = (end_vals[OFFICIAL_TICKERS] / start_vals[OFFICIAL_TICKERS]) - 1
        raw_impacts = stock_returns * 0.1
        total_impact_sum = raw_impacts.sum()
        cum_contrib = (raw_impacts * (total_pts_change / total_impact_sum)) if abs(total_impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)

        st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
        
        # 指標卡：手機端會自動換列
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VALUE</p><h3 style="color:{shift_col};">{end_vals[INDEX_SYMBOL]:,.2f}</h3></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">SHIFT</p><h3 style="color:{shift_col};">{total_pts_change:+.2f}</h3></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VAR %</p><h3 style="color:{shift_col};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

        # 圖表區域
        # st.columns 在手機端預設會變成 100% 寬度堆疊，非常適合響應式
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig_idx = go.Figure(go.Scatter(x=available_df.index, y=available_df[INDEX_SYMBOL], line=dict(color=COLORS['gold'], width=2), hoverinfo="x+y"))
            xaxis_cfg = dict(
                showgrid=False, color=COLORS['muted'], fixedrange=True,
                showspikes=True, spikemode='across', spikesnap='cursor', spikedash='dash', spikecolor=COLORS['muted'],
                nticks=5 # 【手機優化】限制刻度數量，避免文字重疊
            )
            if period_val == '1d':
                xaxis_cfg['tickformat'] = "%H:%M"
                xaxis_cfg['range'] = [plot_time.replace(hour=9, minute=30), plot_time.replace(hour=16, minute=0)]
            
            fig_idx.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                margin=dict(l=10, r=10, t=30, b=10), height=350, 
                xaxis=xaxis_cfg, yaxis=dict(fixedrange=True, showgrid=True, gridcolor='#333', nticks=5),
                hovermode="x"
            )
            st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

        with col2:
            row = cum_contrib.sort_values(ascending=True) # 手機端從下往上看更直觀
            fig_bar = go.Figure(go.Bar(
                y=row.index, x=row.values, # 【手機優化】改為橫向長條圖，方便讀取成份股名稱
                orientation='h',
                marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], 
                text=row.values.round(2), textposition='auto'
            ))
            fig_bar.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                margin=dict(l=10, r=10, t=30, b=10), height=400, 
                yaxis=dict(fixedrange=True), xaxis=dict(fixedrange=True, showgrid=True, gridcolor='#333'),
                title=dict(text=f"CUMULATIVE CONTRIBUTION", font=dict(color=COLORS['gold'], size=14))
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("NO DATA FOUND.")
except Exception as e:
    st.error(f"TERMINAL ERROR: {str(e)}")
