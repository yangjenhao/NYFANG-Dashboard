import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

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

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

# 注入自定義 CSS
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['gold']} !important; text-align: center; font-size: 2.2rem; margin: 10px 0; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['gold']}33; padding: 15px; text-align: center; border-radius: 4px; }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['gold']}44; }}
    .sidebar-content {{ padding: 10px; font-size: 0.85rem; color: {COLORS['muted']}; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC ---
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"
DOMAIN_MAP = {
    "META": "meta.com", "AAPL": "apple.com", "AMZN": "amazon.com", "NFLX": "netflix.com", 
    "MSFT": "microsoft.com", "GOOGL": "google.com", "MU": "micron.com", 
    "NVDA": "nvidia.com", "PLTR": "palantir.com", "AVGO": "broadcom.com"
}

@st.cache_data(ttl=60)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    interval = "1m" if p == "1d" else "1d"
    data = yf.download(all_symbols, period=p, interval=interval, progress=False, auto_adjust=False)['Close']
    if p == "1d" and data.index.tz is not None:
        data.index = data.index.tz_convert('America/New_York').tz_localize(None)
    return data.ffill().dropna()

# --- 3. SIDEBAR TERMINAL ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus; letter-spacing:2px;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='sidebar-content'>
            <p><b>AUTHOR:</b> Jen-Hao Yang</p>
            <p><b>SYSTEM:</b> NYSE FANG+ ENGINE</p>
            <hr style="border-color:{COLORS['gold']}22;">
            <p>STATUS: <span style="color:{COLORS['up']};">ONLINE</span></p>
            <p style="font-size:0.75rem; line-height:1.4;">
                UI: Dynamic Scaling & Logo Masking Active.
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. MAIN UI ---
st.markdown("<h1 class='main-title'>NYSE FANG+ INDEX</h1>", unsafe_allow_html=True)

period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y", "MAX": "max"}
selected_label = st.segmented_control("TIMELINE", options=list(period_map.keys()), default="1D", label_visibility="collapsed")

try:
    df = fetch_data(period_map[selected_label])
    idx_series = df[INDEX_SYMBOL]
    start, end = idx_series.iloc[0], idx_series.iloc[-1]
    total_change = end - start
    
    # 頂部數據指標
    c1, c2, c3 = st.columns(3)
    color = COLORS['up'] if total_change >= 0 else COLORS['down']
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">VALUE</p><h2 style="color:{color}">{end:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">SHIFT</p><h2 style="color:{color}">{total_change:+.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">VAR %</p><h2 style="color:{color}">{(total_change/start*100):+.2f}%</h2></div>', unsafe_allow_html=True)

    # 貢獻度計算
    returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    col1, col2 = st.columns([1.2, 1])
    
    with col1: # 左側：指數走勢圖（動態 Y 軸）
        y_min, y_max = idx_series.min(), idx_series.max()
        padding = (y_max - y_min) * 0.15 if y_max != y_min else 10
        
        fig_idx = go.Figure(go.Scatter(
            x=idx_series.index, y=idx_series.values, 
            line=dict(color=COLORS['gold'], width=2, shape='spline'),
            fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)'
        ))
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=450, margin=dict(t=20, b=20),
            xaxis=dict(showgrid=False),
            yaxis=dict(
                gridcolor='#222', 
                range=[y_min - padding, y_max + padding], # 動態縮放，不從 0 開始
                fixedrange=True,
                tickformat=".0f"
            )
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2: # 右側：個股貢獻度（含 Logo 優化）
        logo_imgs = []
        for ticker in row.index:
            domain = DOMAIN_MAP.get(ticker, "google.com")
            
            # 針對 MU 加入純白圓形襯底，避免黑色背景隱身或黑影
            if ticker == "MU":
                logo_imgs.append(dict(
                    source="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/circle.svg", 
                    xref="paper", yref="y", x=-0.12, y=ticker,
                    sizex=0.055, sizey=0.55, 
                    xanchor="right", yanchor="middle", 
                    sizing="contain", opacity=1.0, layer="below"
                ))

            logo_imgs.append(dict(
                source=f"https://www.google.com/s2/favicons?sz=64&domain={domain}",
                xref="paper", yref="y", x=-0.12, y=ticker,
                sizex=0.08, sizey=0.8, 
                xanchor="right", yanchor="middle", 
                sizing="contain", layer="above"
            ))

        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2), textposition='outside',
            cliponaxis=False
        ))
        
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, margin=dict(l=120, r=60, t=50, b=20),
            title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=14)),
            images=logo_imgs,
            yaxis=dict(
                tickfont=dict(size=11),
                ticksuffix="      ", 
                fixedrange=True
            ),
            xaxis=dict(showgrid=True, gridcolor='#222', zerolinecolor=COLORS['muted'])
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Error: {e}")
