import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta, datetime

# 1. 基礎配置與標的 (2026 最新名單)
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

# 啟用寬螢幕模式
st.set_page_config(page_title="FANG+ Attribution", layout="wide")

# 2. 側邊欄控制 (縮減寬度)
st.sidebar.header("控制面板")
period_options = [
    ('1個月', '1mo'), ('3個月', '3mo'), ('6個月', '6mo'), 
    ('1年', '1y'), ('2年', '2y'), ('5年', '5y'), ('今年至今', 'ytd')
]
period_label, period_val = st.sidebar.selectbox(
    "選擇時間範圍", 
    options=period_options,
    format_func=lambda x: x[0],
    index=1
)

target_date = st.sidebar.date_input("選擇分析日期", value=datetime.now())

# 3. 數據抓取 (含快取機制)
@st.cache_data(ttl=3600)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, progress=False, auto_adjust=False)['Close']
    return data

try:
    raw_data = fetch_data(period_val)
    idx_series = raw_data[INDEX_SYMBOL].dropna()
    stock_prices = raw_data[OFFICIAL_TICKERS].dropna()

    # 4. 點數歸因邏輯計算
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

    # 5. 定位顯示日期
    target_ts = pd.to_datetime(target_date)
    valid_dates = point_contrib_df.index[point_contrib_df.index <= target_ts]

    if not valid_dates.empty:
        plot_date = valid_dates[-1]
        actual_idx_change = idx_diff.loc[plot_date]
        current_price = idx_series.loc[plot_date]
        prev_price = idx_series.shift(1).loc[plot_date]
        change_pct = (actual_idx_change / prev_price) * 100

        # --- 數據儀表板顯示 ---
        st.subheader(f"📊 NYSE FANG+ 歸因分析 ({plot_date.date()})")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("指數價位", f"{current_price:,.2f}")
        c2.metric("漲跌點數", f"{actual_idx_change:+.2f}")
        c3.metric("漲跌幅", f"{change_pct:+.2f}%")
        c4.metric("成分股", f"{len(OFFICIAL_TICKERS)} 檔")

        # --- 圖表繪製 (優化尺寸) ---
        # 縮小 figsize 使螢幕不需過度捲動
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7)) 
        
        # 上圖：指數歷史趨勢
        ax1.plot(idx_series, color='#1f77b4', lw=1.5, label='Index Price')
        ax1.axvline(plot_date, color='orange', ls='--', alpha=0.7)
        ax1.set_title("Index Trend", fontsize=10)
        ax1.tick_params(labelsize=8)
        ax1.grid(True, alpha=0.1)
        
        # 下圖：成分股點數貢獻
        row = point_contrib_df.loc[plot_date].sort_values(ascending=False)
        colors = ['#2ca02c' if x > 0 else '#d62728' for x in row]
        row.plot(kind='bar', ax=ax2, color=colors)
        ax2.set_title(f"Point Contribution (Total: {actual_idx_change:+.2f})", fontsize=10)
        ax2.axhline(0, color='black', lw=0.8)
        ax2.tick_params(axis='x', labelsize=9, rotation=0)
        ax2.tick_params(axis='y', labelsize=8)
        
        # 標註點數數值 (調小字體)
        for i, v in enumerate(row):
            ax2.text(i, v + (0.2 if v > 0 else -1.2), f"{v:+.2f}", ha='center', fontsize=8, fontweight='bold')
        
        plt.tight_layout() # 自動調整間距，避免重疊
        st.pyplot(fig, use_container_width=True) # 強制適應網頁寬度
    else:
        st.error("⚠️ 該日期無交易數據。")

except Exception as e:
    st.error(f"❌ 發生錯誤: {e}")
