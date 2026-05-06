import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. DESIGN TOKENS (Anthropic Style: Shell & Off-white) ---
COLORS = {
    "bg": "#1d1916",      # Anthropic 深色背景 (Shell)
    "card_bg": "#2a2622", # 稍淺的深褐灰
    "fg": "#f9f6f1",      # Anthropic 暖白文字
    "gold": "#d97757",    # 磚紅/土橘色 (類似其品牌點綴色)
    "muted": "#8d8680",   # 灰褐色
    "up": "#3da35d",      # 莫蘭迪綠
    "down": "#e05e5e"     # 莫蘭迪紅
}

st.set_page_config(page_title="FANG+ GATSBY TERMINAL", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['bg']}; color: {COLORS['fg']}; font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ font-family: 'Marcellus', serif !important; text-transform: uppercase; color: {COLORS['fg']} !important; text-align: center; font-size: 2.2rem; margin: 10px 0; letter-spacing: 3px; }}
    .metric-card {{ background-color: {COLORS['card_bg']}; border: 1px solid {COLORS['muted']}33; padding: 15px; text-align: center; border-radius: 8px; }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['card_bg']}; border-right: 1px solid {COLORS['muted']}44; }}
    .sidebar-content {{ padding: 15px; font-size: 0.85rem; color: {COLORS['muted']}; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOGIC (修正 5D 抓取) ---
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
    # 修正：10d 採樣確保包含今日 (5/6)
    fetch_p = "10d" if p == "5d" else p
    interval = "1m" if p == "1d" else "1d"
    data = yf.download(all_symbols, period=fetch_p, interval=interval, progress=False, auto_adjust=False)['Close']
    
    if p == "5d":
        data = data.ffill().dropna().tail(5)
    if p == "1d" and data.index.tz is not None:
        data.index = data.index.tz_convert('America/New_York').tz_localize(None)
    return data.ffill().dropna()

# --- 3. SIDEBAR TERMINAL ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['fg']}; font-family:Marcellus; letter-spacing:2px;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='sidebar-content'>
            <p><b>AUTHOR:</b> Jen-Hao Yang</p>
            <p><b>SYSTEM:</b> NYSE FANG+ ENGINE</p>
            <hr style="border-color:{COLORS['muted']}44;">
            <p>STATUS: <span style="color:{COLORS['up']};">CONNECTED</span></p>
            <p style="font-size:0.75rem; line-height:1.4;">Theme: Anthropic Shell<br>Date Sync: Active (5/6 Incl.)</p>
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
    
    c1, c2, c3 = st.columns(3)
    color = COLORS['up'] if total_change >= 0 else COLORS['down']
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["muted"]}; font-size:0.8rem;">VALUE</p><h2 style="color:{COLORS["fg"]}">{end:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["muted"]}; font-size:0.8rem;">SHIFT</p><h2 style="color:{color}">{total_change:+.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["muted"]}; font-size:0.8rem;">VAR %</p><h2 style="color:{color}">{(total_change/start*100):+.2f}%</h2></div>', unsafe_allow_html=True)

    returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    col1, col2 = st.columns([1.2, 1])
    
    with col1: # 指數走勢圖 - 修正 5/6 顯示問題
        y_min, y_max = idx_series.min(), idx_series.max()
        padding = (y_max - y_min) * 0.15 if y_max != y_min else 10
        
        # 修正：5D 使用類別軸確保最後一天 (5/6) 強制出現
        if selected_label == "5D":
            x_plot = idx_series.index.strftime('%m/%d')
            x_type = 'category'
        else:
            x_plot = idx_series.index
            x_type = 'date'
        
        fig_idx = go.Figure(go.Scatter(
            x=x_plot, y=idx_series.values, 
            line=dict(color=COLORS['gold'], width=2.5),
            fill='tozeroy', fillcolor='rgba(217, 119, 87, 0.05)',
            hoverinfo="x+y"
        ))
        
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=450, margin=dict(t=20, b=20),
            xaxis=dict(
                type=x_type,
                showgrid=False,
                fixedrange=True,
                tickmode='linear' if selected_label == "5D" else 'auto',
                rangebreaks=[dict(bounds=["sat", "mon"])] if x_type == 'date' else None
            ),
            yaxis=dict(gridcolor='#333', range=[y_min - padding, y_max + padding], fixedrange=True, tickformat=".0f"),
            hovermode="x unified"
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2: # 貢獻度圖表
        logo_imgs = []
        for i, ticker in enumerate(row.index):
            logo_imgs.append(dict(
                source=f"https://www.google.com/s2/favicons?sz=128&domain={DOMAIN_MAP[ticker]}",
                xref="paper", yref="y", x=-0.12, y=i,
                sizex=0.08, sizey=0.7, xanchor="center", yanchor="middle", sizing="contain", layer="above"
            ))

        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2), textposition='outside', cliponaxis=False
        ))
        
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, margin=dict(l=140, r=60, t=50, b=20),
            images=logo_imgs,
            yaxis=dict(tickfont=dict(size=11, color=COLORS['fg']), ticksuffix="      ", fixedrange=True),
            xaxis=dict(showgrid=True, gridcolor='#333', zerolinecolor=COLORS['muted']),
            title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['fg'], size=14))
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Error: {e}")
