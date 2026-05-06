import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
    # 【關鍵修復】：如果選 TODAY (1d)，改抓 2d 以獲得基準點
    fetch_p = "2d" if p == "1d" else p
    data = yf.download(all_symbols, period=fetch_p, progress=False, auto_adjust=False)['Close']
    return data

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2>The Terminal</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    period_options = [('TODAY', '1d'), ('V DAYS', '5d'), ('I MONTH', '1mo'), ('III MONTHS', '3mo'), ('VI MONTHS', '6mo'), ('I YEAR', '1y'), ('V YEARS', '5y'), ('YTD', 'ytd')]
    period_label, period_val = st.selectbox("TIMELINE", options=period_options, format_func=lambda x: x[0], index=2)
    
    try:
        # 始終以較長週期決定最新交易日
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
    
    # 績效歸因計算
    idx_diff = idx_series.diff()
    returns = stock_prices.pct_change()
    
    point_contrib_df = pd.DataFrame(index=returns.index, columns=OFFICIAL_TICKERS)
    for date in returns.index:
        actual_pts = idx_diff.loc[date]
        r = returns.loc[date]
        raw_impact = r * 0.1
        impact_sum = raw_impact.sum()
        point_contrib_df.loc[date] = raw_impact * (actual_pts / impact_sum) if abs(impact_sum) > 1e-6 else 0
    
    # 【關鍵修復】：移除因計算產生的首行 NaN
    point_contrib_df = point_contrib_df.dropna()
    idx_diff = idx_diff.dropna()

    # 處理時間比對 (針對 1d/5d 的 Timestamp 與 Departure Date 比對)
    target_dt = pd.to_datetime(st.session_state.target_date)
    
    # 找出所有小於等於選定日期的資料列
    # 如果是 1d 資料，時間戳會帶有時分秒，我們取日期部分比對
    mask = point_contrib_df.index.date <= target_dt.date()
    valid_data = point_contrib_df[mask]
    
    if not valid_data.empty:
        plot_date = valid_data.index[-1]
        actual_idx_change = idx_diff.loc[plot_date]
        current_val = idx_series.loc[plot_date]
        
        # 取得前一筆有效數據計算 Variance
        prev_idx_loc = idx_series.index.get_loc(plot_date)
        prev_val = idx_series.iloc[prev_idx_loc - 1] if prev_idx_loc > 0 else current_val
        variance = ((current_val / prev_val) - 1) * 100 if prev_val != 0 else 0

        # UI 呈現
        st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
        shift_color = COLORS['up'] if actual_idx_change >= 0 else COLORS['down']
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">INDEX VALUE</p><h3>{current_val:,.2f}</h3></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">POINT SHIFT</p><h3 style="color:{shift_color};">{actual_idx_change:+.2f}</h3></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VARIANCE</p><h3 style="color:{shift_color};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            fig_idx = go.Figure()
            # TODAY 模式下只顯示今日的線條，不顯示背景參考的那一天
            display_series = idx_series[idx_series.index.date == plot_date.date()] if period_val == "1d" else idx_series
            
            fig_idx.add_trace(go.Scatter(
                x=display_series.index, y=display_series.values,
                line=dict(color=COLORS['gold'], width=2),
                hovertemplate="<b>%{x}</b><br>Value: %{y:,.2f}<extra></extra>"
            ))
            fig_idx.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0), height=400,
                hovermode="x unified",
                xaxis=dict(showgrid=False, color=COLORS['muted']),
                yaxis=dict(showgrid=True, gridcolor='#333', color=COLORS['muted']),
                title=dict(text="HISTORICAL TREND", font=dict(color=COLORS['gold'], size=14))
            )
            st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

        with col2:
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
                title=dict(text=f"CONTRIBUTION ({plot_date.strftime('%Y-%m-%d %H:%M')})", font=dict(color=COLORS['gold'], size=14))
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("NO DATA AVAILABLE FOR THE SELECTED DATE.")
            
except Exception as e:
    st.error(f"TERMINAL OFFLINE: {e}")
