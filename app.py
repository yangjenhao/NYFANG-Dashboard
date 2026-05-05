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

# --- 2. THEMED CSS INJECTION (Optimized for Mobile) ---
st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    
    /* 基礎樣式 */
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    h1, .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; letter-spacing: 0.15em; color: {COLORS['gold']} !important; text-align: center; font-size: 1.8rem; }}
    
    /* 側邊欄：僅在桌面版限制寬度 */
    @media (min-width: 768px) {{
        section[data-testid="stSidebar"] {{ width: 350px !important; }}
    }}
    
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    
    .stButton>button {{ width: 100%; border-radius: 0px !important; border: 1px solid {COLORS['gold']} !important; background-color: transparent !important; color: {COLORS['gold']} !important; font-size: 0.7rem !important; text-transform: uppercase; }}
    
    /* 指標卡片自適應 */
    .metric-card {{ 
        background-color: {COLORS['card_bg']}; 
        border: 1px solid {COLORS['gold']}33; 
        padding: 15px; 
        text-align: center; 
        margin-bottom: 10px;
    }}
    
    .sidebar-link {{ color: {COLORS['muted']} !important; text-decoration: none; font-size: 0.8rem; transition: 0.3s; }}
    .sidebar-link:hover {{ color: {COLORS['gold']} !important; }}

    /* 針對 Streamlit 內建 Column 的手機端間距調整 */
    div[data-testid="column"] {{
        margin-bottom: 1rem;
    }}
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
    
    input_date = st.date_input("DEPARTURE DATE", value=st.session_state.target_date, max_value=latest_market_date)
    st.session_state.target_date = input_date
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("GO TODAY"):
            st.session_state.target_date = latest_market_date
            st.rerun()
    with btn_col2:
        if st.button("REFRESH"):
            st.rerun()

    st.markdown("---")
    st.markdown(f"""
        <p style='font-size: 0.8rem; color: {COLORS['muted']};'>
        © 2026 jen-hao.yang<br>
        <a href="https://x.com/jenhaoyang" target="_blank" class="sidebar-link">FOLLOW ON X (TWITTER)</a>
        </p>
    """, unsafe_allow_html=True)

# --- 5. MAIN CONTENT ---
try:
    raw_data = fetch_data(period_val).ffill().bfill()
    idx_series = raw_data[INDEX_SYMBOL]
    stock_prices = raw_data[OFFICIAL_TICKERS]
    idx_diff = idx_series.diff()
    returns = stock_prices.pct_change()
    
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
    
    if not valid_dates.empty:
        plot_date = valid_dates[-1]
        actual_idx_change = idx_diff.loc[plot_date]
        current_price = idx_series.loc[plot_date]
        prev_idx_loc = idx_series.index.get_loc(plot_date)
        prev_price = idx_series.iloc[prev_idx_loc - 1] if prev_idx_loc > 0 else current_price
        change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

        st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
        shift_color = COLORS['up'] if actual_idx_change >= 0 else COLORS['down']

        # 在手機版，這些 columns 會自動堆疊
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem; margin:0;">INDEX VALUE</p><h3 style="margin:0;">{current_price:,.2f}</h3></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem; margin:0;">POINT SHIFT</p><h3 style="color:{shift_color}; margin:0;">{actual_idx_change:+.2f}</h3></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem; margin:0;">VARIANCE</p><h3 style="color:{shift_color}; margin:0;">{change_pct:+.2f}%</h3></div>', unsafe_allow_html=True)

        plt.rcParams.update({"text.color": COLORS['fg'], "axes.labelcolor": COLORS['muted'], "axes.edgecolor": COLORS['gold'], "xtick.color": COLORS['muted'], "ytick.color": COLORS['muted'], "axes.facecolor": COLORS['bg'], "figure.facecolor": COLORS['bg']})
        
        # 在手機版，col1 與 col2 會自動上下排列
        col1, col2 = st.columns([1, 1])
        with col1:
            fig1, ax1 = plt.subplots(figsize=(7, 4.5))
            ax1.plot(idx_series.index, idx_series.values, color=COLORS['gold'], lw=2)
            ax1.axvline(plot_date, color=COLORS['fg'], ls='--', lw=1)
            
            if period_val in ['1y', '5y']:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%y-%m'))
            else:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            
            ax1.xaxis.set_major_locator(mticker.MaxNLocator(5))
            ax1.set_title("HISTORICAL TREND", color=COLORS['gold'], pad=15, fontsize=10)
            st.pyplot(fig1, use_container_width=True)

        with col2:
            fig2, ax2 = plt.subplots(figsize=(7, 4.5))
            row = point_contrib_df.loc[plot_date].apply(pd.to_numeric).sort_values(ascending=False)
            chart_colors = [COLORS['up'] if x > 0 else COLORS['down'] for x in row]
            bars = ax2.bar(row.index, row.values, color=chart_colors, edgecolor=COLORS['gold'], lw=0.5)
            ax2.set_title(f"CONTRIBUTION ({plot_date.strftime('%Y-%m-%d')})", color=COLORS['gold'], pad=15, fontsize=10)
            ax2.axhline(0, color=COLORS['fg'], lw=0.5)
            ax2.tick_params(axis='x', rotation=45, labelsize=8)
            # 手機版簡化標籤顯示，只顯示絕對值較大的
            for bar in bars:
                height = bar.get_height()
                if abs(height) > (row.abs().max() * 0.1):
                    ax2.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height > 0 else -1.5), f'{height:+.1f}', ha='center', fontsize=7, color=COLORS['fg'])
            st.pyplot(fig2, use_container_width=True)
            
except Exception as e:
    st.error(f"TERMINAL OFFLINE: {e}")
