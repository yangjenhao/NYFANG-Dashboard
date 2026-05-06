import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

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

# --- 2. THEMED CSS INJECTION ---
st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    h1, .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; letter-spacing: 0.15em; color: {COLORS['gold']} !important; text-align: center; font-size: 1.8rem; }}
    @media (min-width: 768px) {{ section[data-testid="stSidebar"] {{ width: 350px !important; }} }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .stButton>button {{ width: 100%; border-radius: 0px !important; border: 1px solid {COLORS['gold']} !important; background-color: transparent !important; color: {COLORS['gold']} !important; font-size: 0.7rem !important; text-transform: uppercase; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 15px; text-align: center; margin-bottom: 10px; }}
    .sidebar-link {{ color: {COLORS['muted']} !important; text-decoration: none; font-size: 0.8rem; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    return yf.download(all_symbols, period=p, progress=False, auto_adjust=False)['Close']

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2>The Terminal</h2>", unsafe_allow_html=True)
    period_options = [('I MONTH', '1mo'), ('III MONTHS', '3mo'), ('VI MONTHS', '6mo'), ('I YEAR', '1y'), ('V YEARS', '5y'), ('YTD', 'ytd')]
    period_label, period_val = st.selectbox("TIMELINE", options=period_options, format_func=lambda x: x[0])
    
    try:
        latest_market_date = fetch_data("1mo").index[-1].date()
    except:
        latest_market_date = datetime.now().date()

    if 'target_date' not in st.session_state:
        st.session_state.target_date = latest_market_date
    
    st.session_state.target_date = st.date_input("DEPARTURE DATE", value=st.session_state.target_date, max_value=latest_market_date)
    
    c1, c2 = st.columns(2)
    if c1.button("GO TODAY"):
        st.session_state.target_date = latest_market_date
        st.rerun()
    if c2.button("REFRESH"): st.rerun()

    st.markdown(f"--- \n<p style='font-size: 0.8rem; color: {COLORS['muted']};'>© 2026 jen-hao.yang<br><a href='https://x.com/jenhaoyang' class='sidebar-link'>FOLLOW ON X</a></p>", unsafe_allow_html=True)

# --- 5. MAIN CONTENT ---
try:
    raw_data = fetch_data(period_val).ffill().bfill()
    idx_series = raw_data[INDEX_SYMBOL]
    stock_prices = raw_data[OFFICIAL_TICKERS]
    idx_diff = idx_series.diff()
    returns = stock_prices.pct_change()
    
    # 績效歸因計算
    point_contrib_df = pd.DataFrame(index=returns.index, columns=OFFICIAL_TICKERS)
    for date in returns.index:
        actual_pts, r = idx_diff.loc[date], returns.loc[date]
        raw_impact = r * 0.1
        impact_sum = raw_impact.sum()
        point_contrib_df.loc[date] = raw_impact * (actual_pts / impact_sum) if abs(impact_sum) > 1e-6 else 0

    target_ts = pd.to_datetime(st.session_state.target_date)
    valid_dates = point_contrib_df.index[point_contrib_df.index <= target_ts]
    plot_date = valid_dates[-1] if not valid_dates.empty else point_contrib_df.index[-1]

    # 頂部指標
    st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
    actual_idx_change = idx_diff.loc[plot_date]
    shift_color = COLORS['up'] if actual_idx_change >= 0 else COLORS['down']
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">INDEX VALUE</p><h3>{idx_series.loc[plot_date]:,.2f}</h3></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">POINT SHIFT</p><h3 style="color:{shift_color};">{actual_idx_change:+.2f}</h3></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VARIANCE</p><h3 style="color:{shift_color};">{((idx_series.loc[plot_date]/idx_series.shift(1).loc[plot_date])-1)*100:+.2f}%</h3></div>', unsafe_allow_html=True)

    # 圖表區塊
    col1, col2 = st.columns(2)
    
    with col1:
        # --- 互動式 Historical Trend ---
        fig_idx = go.Figure()
        fig_idx.add_trace(go.Scatter(
            x=idx_series.index, y=idx_series.values,
            line=dict(color=COLORS['gold'], width=2),
            hovertemplate="<b>Date: %{x}</b><br>Value: %{y:,.2f}<extra></extra>"
        ))
        fig_idx.add_vline(x=plot_date, line_width=1, line_dash="dash", line_color=COLORS['fg'])
        
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), height=400,
            hovermode="x unified", # 關鍵：滑鼠移動時自動顯示 X 軸對應數值
            xaxis=dict(showgrid=False, color=COLORS['muted']),
            yaxis=dict(showgrid=True, gridcolor='#333', color=COLORS['muted']),
            title=dict(text="HISTORICAL TREND", font=dict(color=COLORS['gold'], size=14))
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # --- 貢獻度長條圖 ---
        row = point_contrib_df.loc[plot_date].apply(pd.to_numeric).sort_values(ascending=False)
        fig_bar = go.Figure(go.Bar(
            x=row.index, y=row.values,
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2), textposition='auto'
        ))
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), height=400,
            xaxis=dict(color=COLORS['muted']), yaxis=dict(color=COLORS['muted']),
            title=dict(text=f"CONTRIBUTION ({plot_date.strftime('%Y-%m-%d')})", font=dict(color=COLORS['gold'], size=14))
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            
except Exception as e:
    st.error(f"TERMINAL OFFLINE: {e}")
