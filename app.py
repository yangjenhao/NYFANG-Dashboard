import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. DESIGN TOKENS ---
COLORS = {"bg": "#0A0A0A", "card_bg": "#141414", "fg": "#F2F0E4", "gold": "#D4AF37", "muted": "#888888", "up": "#00FF00", "down": "#FF0000"}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['gold']} !important; text-align: center; font-size: 2.2rem; margin: 10px 0; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 15px; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"
DOMAIN_MAP = {"META": "meta.com", "AAPL": "apple.com", "AMZN": "amazon.com", "NFLX": "netflix.com", "MSFT": "microsoft.com", "GOOGL": "google.com", "MU": "micron.com", "NVDA": "nvidia.com", "PLTR": "palantir.com", "AVGO": "broadcom.com"}

@st.cache_data(ttl=60)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, interval="1d" if p != "1d" else "1m", progress=False)['Close']
    return data.ffill().dropna()

# --- 3. UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)
period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    start, end = df.iloc[0], df.iloc[-1]
    total_change = end[INDEX_SYMBOL] - start[INDEX_SYMBOL]
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    color = COLORS['up'] if total_change >= 0 else COLORS['down']
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}">VALUE</p><h2 style="color:{color}">{end[INDEX_SYMBOL]:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}">SHIFT</p><h2 style="color:{color}">{total_change:+.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}">VAR %</p><h2 style="color:{color}">{(total_change/start[INDEX_SYMBOL]*100):+.2f}%</h2></div>', unsafe_allow_html=True)

    # Contribution Calculation
    returns = (end[OFFICIAL_TICKERS] / start[OFFICIAL_TICKERS]) - 1
    row = (returns * 0.1 * (total_change / (returns * 0.1).sum())).sort_values(ascending=True)

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        fig_idx = go.Figure(go.Scatter(x=df.index, y=df[INDEX_SYMBOL], line=dict(color=COLORS['gold'], width=2)))
        fig_idx.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=450, margin=dict(t=20))
        st.plotly_chart(fig_idx, use_container_width=True)

    with col2:
        # 構建 Logo 列表
        logo_imgs = []
        for i, ticker in enumerate(row.index):
            domain = DOMAIN_MAP[ticker]
            logo_imgs.append(dict(
                source=f"https://www.google.com/s2/favicons?sz=64&domain={domain}",
                xref="paper", yref="y", x=-0.12, y=i,
                sizex=0.08, sizey=0.8, xanchor="right", yanchor="middle"
            ))

        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2), textposition='outside', # 數字放外面
            cliponaxis=False
        ))
        
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, margin=dict(l=120, r=50, t=50, b=20), # 加大左邊距給 Logo
            title=f"CONTRIBUTION ({selected_label})",
            images=logo_imgs,
            yaxis=dict(
                tickmode='array', tickvals=list(range(len(row))), ticktext=row.index,
                ticksuffix="      ", # 在名稱後加空格，防止與數字/圖表擠壓
                fixedrange=True
            ),
            xaxis=dict(showgrid=True, gridcolor='#222')
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Error: {e}")
