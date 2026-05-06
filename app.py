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

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    # 為確保有前一收盤價可計算，1d 抓 2d，5d 抓 8d (避開週末)
    fetch_p = "2d" if p == "1d" else ("8d" if p == "5d" else p)
    # TODAY 模式使用 1m 間隔以獲得精細線條
    interval = "1m" if p == "1d" else "1h" if p == "5d" else "1d"
    
    data = yf.download(all_symbols, period=fetch_p, interval=interval, progress=False, auto_adjust=False)['Close']
    data.index = data.index.tz_localize(None) 
    return data.ffill().dropna()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2>The Terminal</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    period_options = [('TODAY', '1d'), ('V DAYS', '5d'), ('I MONTH', '1mo'), ('III MONTHS', '3mo'), ('I YEAR', '1y'), ('YTD', 'ytd')]
    period_label, period_val = st.selectbox("TIMELINE", options=period_options, format_func=lambda x: x[0], index=0)
    
    try:
        init_data = fetch_data("1mo")
        latest_market_date = init_data.index[-1].date()
    except:
        latest_market_date = datetime.now().date()

    if 'target_date' not in st.session_state:
        st.session_state.target_date = latest_market_date
    
    selected_date = st.date_input("DEPARTURE DATE", value=st.session_state.target_date, max_value=latest_market_date)
    st.session_state.target_date = selected_date
    
    if st.button("GO TODAY"):
        st.session_state.target_date = latest_market_date
        st.rerun()

    st.markdown(f"--- \n<p style='font-size: 0.8rem; color: {COLORS['muted']};'>© 2026 jen-hao.yang<br><a href='https://x.com/jenhaoyang' class='sidebar-link' target='_blank'>FOLLOW ON X</a></p>", unsafe_allow_html=True)

# --- 5. MAIN CONTENT ---
try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    idx_diff = idx_series.diff()
    returns = df[OFFICIAL_TICKERS].pct_change()
    
    # 計算歸因
    contrib_df = pd.DataFrame(index=returns.index, columns=OFFICIAL_TICKERS)
    for t in returns.index:
        actual_pts = idx_diff.loc[t]
        r = returns.loc[t]
        raw_impact = r * 0.1
        impact_sum = raw_impact.sum()
        contrib_df.loc[t] = raw_impact * (actual_pts / impact_sum) if abs(impact_sum) > 1e-6 else 0

    target_dt = pd.to_datetime(st.session_state.target_date).date()
    available_data = contrib_df[contrib_df.index.date <= target_dt]
    
    if not available_data.empty:
        plot_time = available_data.index[-1]
        current_val = idx_series.loc[plot_time]
        
        # 抓取前一有效交易點 (確保 Variance 準確)
        loc = idx_series.index.get_loc(plot_time)
        prev_val = idx_series.iloc[loc-1] if loc > 0 else current_val
        actual_shift = current_val - prev_val
        variance = ((current_val / prev_val) - 1) * 100 if prev_val != 0 else 0

        st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
        shift_col = COLORS['up'] if actual_shift >= 0 else COLORS['down']
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">INDEX VALUE</p><h3>{current_val:,.2f}</h3></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">POINT SHIFT</p><h3 style="color:{shift_col};">{actual_shift:+.2f}</h3></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VARIANCE</p><h3 style="color:{shift_col};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            # 趨勢圖：隱藏假日與非交易時段
            fig_idx = go.Figure()
            show_df = idx_series[idx_series.index.date == plot_time.date()] if period_val == '1d' else idx_series
            
            fig_idx.add_trace(go.Scatter(
                x=show_df.index, y=show_df.values,
                line=dict(color=COLORS['gold'], width=2),
                hovertemplate="<b>%{x}</b><br>Value: %{y:,.2f}<extra></extra>"
            ))
            
            fig_idx.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0), height=400, hovermode="x unified",
                title=dict(text="HISTORICAL TREND", font=dict(color=COLORS['gold'], size=14)),
                xaxis=dict(
                    showgrid=False, color=COLORS['muted'],
                    # 【關鍵】：隱藏週末與非交易時段 (美股 16:00 到隔日 09:30)
                    rangebreaks=[
                        dict(bounds=["sat", "mon"]), # 隱藏週六至週一 (週末)
                        dict(bounds=[16, 9.5], pattern="hour") # 隱藏下午4點到隔日早上9點半
                    ]
                ),
                yaxis=dict(showgrid=True, gridcolor='#333', color=COLORS['muted'])
            )
            st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

        with col2:
            # 歸因圖
            row = contrib_df.loc[plot_time].apply(pd.to_numeric).sort_values(ascending=False)
            fig_bar = go.Figure(go.Bar(
                x=row.index, y=row.values,
                marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
                text=row.values.round(2), textposition='auto'
            ))
            fig_bar.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0), height=400,
                xaxis=dict(color=COLORS['muted']), yaxis=dict(color=COLORS['muted']),
                title=dict(text=f"CONTRIBUTION ({plot_time.strftime('%m-%d %H:%M')})", font=dict(color=COLORS['gold'], size=14))
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("THE SELECTED DATE IS A HOLIDAY OR NO DATA AVAILABLE.")
            
except Exception as e:
    st.error(f"TERMINAL OFFLINE: {e}")
