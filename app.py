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
    h1, .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; letter-spacing: 0.25em; color: {COLORS['gold']} !important; text-align: center; }}
    section[data-testid="stSidebar"] {{ width: 350px !important; background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .stButton>button {{ width: 100%; border-radius: 0px !important; border: 1px solid {COLORS['gold']} !important; background-color: transparent !important; color: {COLORS['gold']} !important; font-size: 0.7rem !important; text-transform: uppercase; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 20px; text-align: center; }}
    .sidebar-link {{ color: {COLORS['muted']} !important; text-decoration: none; font-size: 0.8rem; transition: 0.3s; }}
    .sidebar-link:hover {{ color: {COLORS['gold']} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, progress=False, auto_adjust=False)['Close']
    return data

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2>The Terminal</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    period_options = [('I MONTH', '1mo'), ('III MONTHS', '3mo'), ('VI MONTHS', '6mo'), ('I YEAR', '1y'), ('V YEARS', '5y'), ('YTD', 'ytd')]
    period_label, period_val = st.selectbox("TIMELINE", options=period_options, format_func=lambda x: x[0], index=0)
    
    try:
        temp_data = fetch_data("1mo")
        latest_market_date = temp_data.index[-1].date()
    except:
        latest_market_date = datetime.now().date()

    if 'target_date' not in st.session_state:
        st.session_state.target_date = latest_market_date
    
    target_date = st.date_input("DEPARTURE DATE", value=st.session_state.target_date, max_value=latest_market_date)
    st.session_state.target_date = target_date
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("GO TODAY"):
            st.session_state.target_date = latest_market_date
            st.rerun()
    with btn_col2:
        if st.button("REFRESH"):
            st.rerun()

    st.markdown("---")
    st.markdown(f"<p style='font-size: 0.8rem; color: {COLORS['muted']};'>© 2026 jen-hao.yang<br><a href='https://x.com/jenhaoyang' target='_blank' class='sidebar-link'>FOLLOW ON X (TWITTER)</a></p>", unsafe_allow_html=True)

# --- 5. MAIN CONTENT ---
try:
    raw_data = fetch_data(period_val).ffill().bfill()
    idx_series = raw_data[INDEX_SYMBOL]
    stock_prices = raw_data[OFFICIAL_TICKERS]
    idx_diff = idx_series.diff()
    returns = stock_prices.pct_change()
    
    # 歸因計算
    point_contrib_df = pd.DataFrame(index=returns.index, columns=OFFICIAL_TICKERS)
    for date in returns.index:
        actual_total_pts = idx_diff.loc[date]
        r = returns.loc[date]
        raw_impact = r * 0.1
        impact_sum = raw_impact.sum()
        if abs(impact_sum) > 1e-6 and not pd.isna(actual_total_pts):
            point_contrib_df.loc[date] = raw_impact * (actual_total_pts / impact_sum)
        else:
            point_contrib_df.loc[date] = 0

    target_ts = pd.to_datetime(st.session_state.target_date)
    valid_dates = point_contrib_df.index[point_contrib_df.index <= target_ts]
    plot_date = valid_dates[-1] if not valid_dates.empty else point_contrib_df.index[-1]

    # 數據指標
    actual_idx_change = idx_diff.loc[plot_date]
    current_price = idx_series.loc[plot_date]
    prev_idx_loc = idx_series.index.get_loc(plot_date)
    prev_price = idx_series.iloc[prev_idx_loc - 1] if prev_idx_loc > 0 else current_price
    change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

    st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
    shift_color = COLORS['up'] if actual_idx_change >= 0 else COLORS['down']

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]};">INDEX VALUE</p><h2>{current_price:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]};">POINT SHIFT</p><h2 style="color:{shift_color};">{actual_idx_change:+.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]};">VARIANCE</p><h2 style="color:{shift_color};">{change_pct:+.2f}%</h2></div>', unsafe_allow_html=True)

    # --- 圖表區塊 ---
    col1, col2 = st.columns(2)
    
    with col1:
        # 使用 Plotly 製作互動式歷史曲線
        fig_idx = go.Figure()
        fig_idx.add_trace(go.Scatter(
            x=idx_series.index, y=idx_series.values,
            line=dict(color=COLORS['gold'], width=2),
            hoverinfo="x+y",
            name="Index"
        ))
        # 加入當前選取日期的垂直線
        fig_idx.add_vline(x=plot_date, line_width=1, line_dash="dash", line_color=COLORS['fg'])
        
        fig_idx.update_layout(
            title=dict(text="HISTORICAL TREND (CLICK TO SYNC)", font=dict(color=COLORS['gold'])),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0), height=400,
            xaxis=dict(showgrid=False, color=COLORS['muted']),
            yaxis=dict(showgrid=True, gridcolor='#333', color=COLORS['muted']),
            clickmode='event+select' # 啟用點擊事件
        )
        
        # 顯示圖表並捕捉點擊
        selected_points = st.plotly_chart(fig_idx, use_container_width=True, on_select="rerun")
        
        # 檢查是否有新的點擊
        if selected_points and "selection" in selected_points and selected_points["selection"]["points"]:
            clicked_date = selected_points["selection"]["points"][0]["x"]
            # 如果點擊的日期不同，更新並 rerun
            new_date = pd.to_datetime(clicked_date).date()
            if new_date != st.session_state.target_date:
                st.session_state.target_date = new_date
                st.rerun()

    with col2:
        # 貢獻度長條圖
        row = point_contrib_df.loc[plot_date].apply(pd.to_numeric).sort_values(ascending=False)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=row.index, y=row.values,
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2), textposition='auto'
        ))
        fig_bar.update_layout(
            title=dict(text=f"CONTRIBUTION ({plot_date.strftime('%Y-%m-%d')})", font=dict(color=COLORS['gold'])),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0), height=400,
            xaxis=dict(color=COLORS['muted']),
            yaxis=dict(showgrid=True, gridcolor='#333', color=COLORS['muted'])
        )
        st.plotly_chart(fig_bar, use_container_width=True)

except Exception as e:
    st.error(f"TERMINAL OFFLINE: {e}")
