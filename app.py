import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta, datetime

# --- 1. DESIGN TOKENS (Art Deco System) ---
COLORS = {
    "bg": "#0A0A0A",
    "card_bg": "#141414",
    "fg": "#F2F0E4",
    "gold": "#D4AF37",
    "muted": "#888888",
}

# --- 2. THEMED CSS INJECTION ---
st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');

    .stApp {{
        background-color: {COLORS['bg']};
        color: {COLORS['fg']};
        font-family: 'Josefin Sans', sans-serif;
    }}

    h1, h2, h3, .main-title {{
        font-family: 'Marcellus', serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.25em !important;
        color: {COLORS['gold']} !important;
        text-align: center;
    }}

    [data-testid="stMetric"] {{
        background-color: {COLORS['card_bg']};
        border: 1px solid {COLORS['gold']}33;
        padding: 15px;
        text-align: center;
    }}
    
    [data-testid="stMetricLabel"] {{
        font-family: 'Marcellus', serif;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: {COLORS['gold']} !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {COLORS['card_bg']};
        border-right: 1px solid {COLORS['gold']}44;
    }}
    
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: repeating-linear-gradient(45deg, {COLORS['gold']}05 0px, {COLORS['gold']}05 1px, transparent 1px, transparent 10px);
        pointer-events: none;
        z-index: 0;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=3600)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, progress=False, auto_adjust=False)['Close']
    return data

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2 style='font-size: 1.5rem;'>The Terminal</h2>", unsafe_allow_html=True)
    period_options = [
        ('I MONTH', '1mo'), ('III MONTHS', '3mo'), ('VI MONTHS', '6mo'), 
        ('I YEAR', '1y'), ('II YEARS', '2y'), ('V YEARS', '5y'), ('YTD', 'ytd')
    ]
    period_label, period_val = st.selectbox("TIMELINE", options=period_options, format_func=lambda x: x[0], index=1)
    target_date = st.date_input("DEPARTURE DATE", value=datetime.now())
    
    st.markdown("---")
    st.caption("© 2026 jen-hao.yang")
    st.caption("ARCHITECTURAL TRADING INTERFACE")

# --- 5. MAIN CONTENT ---
try:
    raw_data = fetch_data(period_val)
    idx_series = raw_data[INDEX_SYMBOL].dropna()
    stock_prices = raw_data[OFFICIAL_TICKERS].dropna()

    idx_diff = idx_series.diff()
    returns = stock_prices.pct_change().dropna()
    point_contrib_list = []
    for date in returns.index:
        if date in idx_diff.index:
            actual_total_pts = idx_diff.loc[date]
            r = returns.loc[date]
            raw_impact = r * 0.1
            impact_sum = raw_impact.sum()
            point_contrib = raw_impact * (actual_total_pts / impact_sum) if abs(impact_sum) > 0 else raw_impact * 0
            point_contrib_list.append(point_contrib)
    point_contrib_df = pd.DataFrame(point_contrib_list, index=returns.index)

    target_ts = pd.to_datetime(target_date)
    valid_dates = point_contrib_df.index[point_contrib_df.index <= target_ts]

    if not valid_dates.empty:
        plot_date = valid_dates[-1]
        actual_idx_change = idx_diff.loc[plot_date]
        current_price = idx_series.loc[plot_date]
        prev_price = idx_series.shift(1).loc[plot_date]
        change_pct = (actual_idx_change / prev_price) * 100

        st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; margin-bottom:20px; font-size:0.8rem; color:{COLORS['gold']};'>CONSTITUENTS: {', '.join(OFFICIAL_TICKERS)}</div>", unsafe_allow_html=True)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("INDEX VALUE", f"{current_price:,.2f}")
        m2.metric("POINT SHIFT", f"{actual_idx_change:+.2f}")
        m3.metric("VARIANCE %", f"{change_pct:+.2f}%")
        m4.metric("ASSETS", "X STOCKS")

        # --- 6. ART DECO CHARTS (FIXED) ---
        plt.rcParams.update({
            "text.color": COLORS['fg'],
            "axes.labelcolor": COLORS['muted'],
            "axes.edgecolor": COLORS['gold'],
            "xtick.color": COLORS['muted'],
            "ytick.color": COLORS['muted'],
            "axes.facecolor": COLORS['bg'],
            "figure.facecolor": COLORS['bg']
        })

        col1, col2 = st.columns(2)

        with col1:
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ax1.plot(idx_series, color=COLORS['gold'], lw=1.5)
            ax1.fill_between(idx_series.index, idx_series, color=COLORS['gold'], alpha=0.05)
            ax1.axvline(plot_date, color=COLORS['fg'], ls='--', lw=0.8)
            ax1.set_title("HISTORICAL TREND", color=COLORS['gold'], fontsize=10)
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig1)

        with col2:
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            row = point_contrib_df.loc[plot_date].sort_values(ascending=False)
            colors = [COLORS['gold'] if x > 0 else '#1E3D59' for x in row]
            bars = ax2.bar(row.index, row.values, color=colors, edgecolor=COLORS['gold'], linewidth=0.5)
            ax2.set_title(f"CONTRIBUTION: {actual_idx_change:+.2f} PTS", color=COLORS['gold'], fontsize=10)
            ax2.axhline(0, color=COLORS['fg'], lw=0.5)
            
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + (0.5 if height > 0 else -1.5),
                        f'{height:+.2f}', ha='center', va='bottom', fontsize=7, color=COLORS['fg'], fontweight='bold')
            
            plt.tight_layout()
            st.pyplot(fig2)
            
    else:
        st.error("NO DATA FOUND FOR THE CHOSEN ERA.")

except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")
