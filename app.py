import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. DESIGN TOKENS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

# --- 2. THEMED CSS ---
st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    h1, .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; letter-spacing: 0.15em; color: {COLORS['gold']} !important; text-align: center; font-size: 1.8rem; }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 15px; text-align: center; margin-bottom: 10px; }}
    .stButton>button {{ width: 100%; border-radius: 0px !important; border: 1px solid {COLORS['gold']} !important; background-color: transparent !important; color: {COLORS['gold']} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    # TODAY 模式抓 1m 數據，其餘天數抓 1d 數據
    if p == "1d":
        fetch_p, interval = "2d", "1m"
    elif p == "5d":
        fetch_p, interval = "10d", "1d"
    else:
        fetch_p, interval = p, "1d"
    
    data = yf.download(all_symbols, period=fetch_p, interval=interval, progress=False, auto_adjust=False)['Close']
    data.index = data.index.tz_localize(None) 
    return data.ffill().dropna()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2>The Terminal</h2>", unsafe_allow_html=True)
    period_options = [
        ('TODAY', '1d'), ('V DAYS', '5d'), ('I MONTH', '1mo'), 
        ('III MONTHS', '3mo'), ('I YEAR', '1y'), ('II YEARS', '2y'), 
        ('V YEARS', '5y'), ('YTD', 'ytd')
    ]
    period_label, period_val = st.selectbox("TIMELINE", options=period_options, format_func=lambda x: x[0], index=0)
    
    try:
        latest_market_date = fetch_data("1mo").index[-1].date()
    except:
        latest_market_date = datetime.now().date()

    target_date = st.date_input("DEPARTURE DATE", value=latest_market_date, max_value=latest_market_date)
    if st.button("GO TODAY"): st.rerun()

# --- 5. MAIN CONTENT ---
try:
    df = fetch_data(period_val)
    idx_series = df[INDEX_SYMBOL]
    
    # 核心計算
    idx_diff = idx_series.diff()
    returns = df[OFFICIAL_TICKERS].pct_change()
    contrib_df = pd.DataFrame(index=returns.index, columns=OFFICIAL_TICKERS)
    
    for t in returns.index:
        pts = idx_diff.loc[t]
        r = returns.loc[t]
        impact = r * 0.1
        total_impact = impact.sum()
        # 修正 Contribution 消失問題：若當下變化極小，仍分配權重
        contrib_df.loc[t] = impact * (pts / total_impact) if abs(total_impact) > 1e-9 else 0

    target_dt = pd.to_datetime(target_date).date()
    # 過濾出選定日期的數據
    day_data = idx_series[idx_series.index.date == target_dt]
    
    if not day_data.empty:
        plot_time = day_data.index[-1]
        current_val = idx_series.loc[plot_time]
        
        # 基準價：TODAY 模式取前一天收盤價
        loc = idx_series.index.get_loc(day_data.index[0])
        ref_val = idx_series.iloc[loc-1] if loc > 0 else day_data.iloc[0]
        
        actual_shift = current_val - ref_val
        variance = ((current_val / ref_val) - 1) * 100

        st.markdown(f"<h1 class='main-title'>NYSE FANG+ ATTRIBUTION</h1>", unsafe_allow_html=True)
        shift_col = COLORS['up'] if actual_shift >= 0 else COLORS['down']
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">INDEX VALUE</p><h3>{current_val:,.2f}</h3></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">POINT SHIFT</p><h3 style="color:{shift_col};">{actual_shift:+.2f}</h3></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.7rem;">VARIANCE</p><h3 style="color:{shift_col};">{variance:+.2f}%</h3></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            # TODAY 模式顯示分時圖，限定開盤時段
            show_df = day_data if period_val == '1d' else idx_series
            fig_idx = go.Figure(go.Scatter(x=show_df.index, y=show_df.values, line=dict(color=COLORS['gold'], width=2), connectgaps=True, hovertemplate="Value: %{y:,.2f}<extra></extra>"))
            
            # 設定美股交易時段過濾 (09:30 - 16:00)
            xaxis_config = dict(showgrid=False, color=COLORS['muted'], type='date')
            if period_val == '1d':
                xaxis_config['rangebreaks'] = [dict(bounds=[16, 9.5], pattern="hour"), dict(bounds=["sat", "mon"])]
            
            fig_idx.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0), height=400,
                xaxis=xaxis_config, yaxis=dict(showgrid=True, gridcolor='#333', color=COLORS['muted']),
                title=dict(text="HISTORICAL TREND", font=dict(color=COLORS['gold'], size=14))
            )
            st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

        with col2:
            # 獲取該時間點的所有貢獻
            row = contrib_df.loc[plot_time].apply(pd.to_numeric).sort_values(ascending=False)
            fig_bar = go.Figure(go.Bar(x=row.index, y=row.values, marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], text=row.values.round(2), textposition='auto'))
            fig_bar.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0), height=400,
                title=dict(text=f"CONTRIBUTION ({plot_time.strftime('%H:%M')})", font=dict(color=COLORS['gold'], size=14))
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("WAITING FOR MARKET OPEN OR NO DATA AVAILABLE.")
except Exception as e:
    st.error(f"TERMINAL OFFLINE: {str(e)}")
