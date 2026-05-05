import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
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
    
    # 預抓資料取得今日有效交易日
    try:
        temp_data = fetch_data("1mo")
        latest_market_date = temp_data.index[-1].date()
    except:
        latest_market_date = datetime.now().date()

    # 初始化與同步日期
    if 'target_date' not in st.session_state:
        st.session_state.target_date = latest_market_date
    
    # 關鍵：使用 key='target_date' 與 session_state 雙向綁定
    target_date = st.date_input(
        "DEPARTURE DATE", 
        key="target_date",
        max_value=latest_market_date
    )
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("GO TODAY"):
            st.session_state.target_date = latest_market_date
            st.rerun()
    with btn_col2:
        if st.button("REFRESH"):
            st.rerun()

    st.markdown("---")
    st.caption("© 2026 jen-hao.yang")

# --- 5. MAIN CONTENT ---
try:
    raw_data = fetch_data(period_val)
    raw_data = raw_data.ffill().bfill()
    
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

    target_ts = pd.to_datetime(target_date)
    valid_dates = point_contrib_df.index[point_contrib_df.index <= target_ts]
    
    if not valid_dates.empty:
        plot_date = valid_dates[-1]
        actual_idx_change = idx_diff.loc[plot_date]
        current_price = idx_series.loc[plot_date]
        prev_idx_loc = idx_series.index.get_loc(plot_date)
        prev_price = idx_series.iloc[prev_idx_loc - 1] if prev_idx_loc > 0 else current_price
        change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

        st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
        
        shift_color = COLORS['up'] if actual_idx_change >= 0 else COLORS['down']

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem; margin:0;">INDEX VALUE</p><h2 style="color:{COLORS["fg"]}; margin:0; font-family:Marcellus;">{current_price:,.2f}</h2></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem; margin:0;">POINT SHIFT</p><h2 style="color:{shift_color}; margin:0; font-family:Marcellus;">{actual_idx_change:+.2f}</h2></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem; margin:0;">VARIANCE</p><h2 style="color:{shift_color}; margin:0; font-family:Marcellus;">{change_pct:+.2f}%</h2></div>', unsafe_allow_html=True)

        plt.rcParams.update({"text.color": COLORS['fg'], "axes.labelcolor": COLORS['muted'], "axes.edgecolor": COLORS['gold'], "xtick.color": COLORS['muted'], "ytick.color": COLORS['muted'], "axes.facecolor": COLORS['bg'], "figure.facecolor": COLORS['bg']})
        
        col1, col2 = st.columns(2)
        with col1:
            fig1, ax1 = plt.subplots(figsize=(7, 4.5))
            ax1.plot(idx_series.index, idx_series.values, color=COLORS['gold'], lw=2)
            ax1.axvline(plot_date, color=COLORS['fg'], ls='--', lw=1)
            
            # --- 動態修正 X 軸年份 ---
            if period_val in ['1y', '5y']:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            else:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            
            ax1.xaxis.set_major_locator(mticker.MaxNLocator(6))
            ax1.set_title("HISTORICAL TREND", color=COLORS['gold'], pad=20)
            st.pyplot(fig1)

        with col2:
            fig2, ax2 = plt.subplots(figsize=(7, 4.5))
            row = point_contrib_df.loc[plot_date].apply(pd.to_numeric).sort_values(ascending=False)
            chart_colors = [COLORS['up'] if x > 0 else COLORS['down'] for x in row]
            bars = ax2.bar(row.index, row.values, color=chart_colors, edgecolor=COLORS['gold'], lw=0.5)
            ax2.set_title(f"CONTRIBUTION ({plot_date.strftime('%Y-%m-%d')})", color=COLORS['gold'], pad=20)
            ax2.axhline(0, color=COLORS['fg'], lw=0.5)
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height > 0 else -1.5), f'{height:+.2f}', ha='center', fontsize=8, color=COLORS['fg'], fontweight='bold')
            st.pyplot(fig2)
            
except Exception as e:
    st.error(f"SYSTEM RECOVERY: {e}")
