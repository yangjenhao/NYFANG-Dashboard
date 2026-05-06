import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. DESIGN TOKENS (修正適應性) ---
COLORS = {
    "accent": "#D4AF37", 
    "up": "#3da35d",      
    "down": "#e05e5e",    
    "muted": "rgba(128, 128, 128, 0.6)" 
}

# --- 2. CSS 修正 (支援 Light Mode) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap');
    .stApp {{ font-family: 'Josefin Sans', sans-serif; }}
    .main-title {{ 
        font-family: 'Marcellus', serif !important; 
        text-transform: uppercase; 
        color: {COLORS['accent']} !important; 
        text-align: center; font-size: 2.2rem; margin: 10px 0; 
    }}
    .metric-card {{ 
        background-color: rgba(128, 128, 128, 0.08); 
        border: 1px solid rgba(212, 175, 55, 0.2); 
        padding: 15px; text-align: center; border-radius: 4px; 
    }}
    section[data-testid="stSidebar"] {{ border-right: 1px solid rgba(128, 128, 128, 0.1); }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA FETCH (解決 KeyError) ---
@st.cache_data(ttl=60)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    interval = "1m" if p == "1d" else "1d"
    # 修正：確保只抓取 Close 欄位，並處理可能的 MultiIndex 錯誤
    raw_data = yf.download(all_symbols, period=p, interval=interval, progress=False, auto_adjust=True)
    
    if raw_data.empty:
        return pd.DataFrame()
    
    # yfinance 下載多個 ticker 會產生 MultiIndex，我們只取 Close
    if 'Close' in raw_data.columns:
        df = raw_data['Close']
    else:
        df = raw_data # 如果 auto_adjust=True 有時直接就是價格
        
    return df.ffill().dropna()

# --- 4. UI 邏輯與錯誤攔截 ---
try:
    df = fetch_data(period_map[selected_label])
    
    # 檢查關鍵欄位是否存在，防止 KeyError
    if INDEX_SYMBOL not in df.columns:
        st.error(f"目前抓不到 {INDEX_SYMBOL} 的資料，請稍後再試。")
    else:
        idx_series = df[INDEX_SYMBOL]
        # ... (後續計算邏輯保持不變)
        
        # Plotly 圖表修正：將 template 改為 "none" 讓它自動適應 Light/Dark Mode
        # fig_idx.update_layout(template="none", ...)
        # fig_bar.update_layout(template="none", ...)

# --- 3. SIDEBAR TERMINAL ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{COLORS['gold']}; font-family:Marcellus; letter-spacing:2px;'>TERMINAL</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='sidebar-content'>
            <p><b>AUTHOR:</b> Jen-Hao Yang</p>
            <p><b>SYSTEM:</b> NYSE FANG+ ENGINE</p>
            <hr style="border-color:{COLORS['gold']}22;">
            <p>STATUS: <span style="color:{COLORS['up']};">ONLINE</span></p>
            <p style="font-size:0.75rem; line-height:1.4;">Weekend Filter: ACTIVE.<br>Spike Guides: ENABLED.</p>
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
    with c1: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">VALUE</p><h2 style="color:{color}">{end:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">SHIFT</p><h2 style="color:{color}">{total_change:+.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p style="color:{COLORS["gold"]}; font-size:0.8rem;">VAR %</p><h2 style="color:{color}">{(total_change/start*100):+.2f}%</h2></div>', unsafe_allow_html=True)

    returns = (df[OFFICIAL_TICKERS].iloc[-1] / df[OFFICIAL_TICKERS].iloc[0]) - 1
    raw_impact = returns * 0.1
    impact_sum = raw_impact.sum()
    row = (raw_impact * (total_change / impact_sum) if abs(impact_sum) > 1e-9 else pd.Series(0, index=OFFICIAL_TICKERS)).sort_values(ascending=True)

    col1, col2 = st.columns([1.2, 1])
    
    with col1: # 指數走勢圖
        y_min, y_max = idx_series.min(), idx_series.max()
        padding = (y_max - y_min) * 0.15 if y_max != y_min else 10
        
        fig_idx = go.Figure(go.Scatter(
            x=idx_series.index, y=idx_series.values, 
            line=dict(color=COLORS['gold'], width=2, shape='spline'),
            fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.05)',
            hoverinfo="x+y"
        ))
        
        # 設定垂直虛線引導與隱藏週末
        fig_idx.update_xaxes(
            showgrid=False,
            fixedrange=True,
            showspikes=True, # 開啟虛線
            spikethickness=1,
            spikedash="dot",
            spikemode="across",
            spikecolor=COLORS['muted'],
            rangebreaks=[dict(bounds=["sat", "mon"])] if selected_label != "1D" else None # 隱藏週末
        )
        
        fig_idx.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=450, margin=dict(t=20, b=20),
            yaxis=dict(
                gridcolor='#333', 
                range=[y_min - padding, y_max + padding],
                fixedrange=True,
                tickformat=".0f"
            ),
            dragmode=False,
            hovermode="x unified" # 統一樣式以便讀取
        )
        st.plotly_chart(fig_idx, use_container_width=True, config={'displayModeBar': False})

    with col2:
            logo_imgs = []
            
            tickers = list(row.index)
            
            for i, ticker in enumerate(tickers):
                domain = DOMAIN_MAP.get(ticker, "google.com")
                
                # 主要 Logo - 保持原始透明度，無任何背景
                logo_imgs.append(dict(
                    source=f"https://www.google.com/s2/favicons?sz=128&domain={domain}",
                    xref="paper", yref="y", 
                    x=-0.12, y=i,
                    sizex=0.08, sizey=0.7, 
                    xanchor="center", 
                    yanchor="middle", 
                    sizing="contain", 
                    layer="above"
                ))
    
            # 針對 MU 調整 Ticker 文字顏色，確保在黑底上看得到
            tick_colors = [COLORS['fg'] if t != "MU" else "#FFFFFF" for t in row.index]
    
            fig_bar = go.Figure(go.Bar(
                y=row.index, x=row.values, orientation='h',
                marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
                text=row.values.round(2), textposition='outside',
                cliponaxis=False
            ))
            
            fig_bar.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=450, 
                margin=dict(l=140, r=60, t=50, b=20),
                images=logo_imgs,
                # 確保 shapes 是空的，徹底移除背景
                shapes=[], 
                yaxis=dict(
                    tickfont=dict(size=11, color=COLORS['fg']),
                    ticksuffix="      ", 
                    fixedrange=True
                ),
                xaxis=dict(showgrid=True, gridcolor='#333', zerolinecolor=COLORS['muted']),
                title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=14))
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Error: {e}")
