import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta, datetime

# 1. 基礎配置
OFFICIAL_TICKERS = ["META", "AAPL", "AMZN", "NFLX", "MSFT", "GOOGL", "MU", "NVDA", "PLTR", "AVGO"]
INDEX_SYMBOL = "^NYFANG"

st.set_page_config(page_title="FANG+ Dashboard", layout="wide")

# 2. 側邊欄與版權資訊
with st.sidebar:
    st.header("控制面板")
    period_options = [
        ('1個月', '1mo'), ('3個月', '3mo'), ('6個月', '6mo'), 
        ('1年', '1y'), ('2年', '2y'), ('5年', '5y'), ('今年至今', 'ytd')
    ]
    period_label, period_val = st.selectbox(
        "選擇時間範圍", options=period_options, format_func=lambda x: x[0], index=1
    )
    target_date = st.date_input("選擇分析日期", value=datetime.now())
    
    st.markdown("---")
    # 加入版權資訊
    st.caption("© 2026 jen-hao.yang")

# 3. 數據抓取
@st.cache_data(ttl=3600)
def fetch_data(p):
    all_symbols = OFFICIAL_TICKERS + [INDEX_SYMBOL]
    data = yf.download(all_symbols, period=p, progress=False, auto_adjust=False)['Close']
    return data

try:
    raw_data = fetch_data(period_val)
    idx_series = raw_data[INDEX_SYMBOL].dropna()
    stock_prices = raw_data[OFFICIAL_TICKERS].dropna()

    # 4. 點數歸因邏輯
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

    # 5. 定位日期
    target_ts = pd.to_datetime(target_date)
    valid_dates = point_contrib_df.index[point_contrib_df.index <= target_ts]

    if not valid_dates.empty:
        plot_date = valid_dates[-1]
        actual_idx_change = idx_diff.loc[plot_date]
        current_price = idx_series.loc[plot_date]
        prev_price = idx_series.shift(1).loc[plot_date]
        change_pct = (actual_idx_change / prev_price) * 100

        # --- 標題與數值 ---
        st.subheader(f"📊 NYFANG+ 歸因分析 ({plot_date.date()})")
        
        # 顯示成分股清單
        st.write(f"**當前追蹤成分股：** {', '.join(OFFICIAL_TICKERS)}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("指數價位", f"{current_price:,.2f}")
        c2.metric("漲跌點數", f"{actual_idx_change:+.2f}")
        c3.metric("漲跌幅", f"{change_pct:+.2f}%")
        c4.metric("成分股數", "10 檔")

        # --- 左右並排佈局 ---
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ax1.plot(idx_series, color='#1f77b4', lw=2)
            ax1.axvline(plot_date, color='orange', ls='--')
            ax1.set_title("Index Trend", fontsize=12)
            ax1.tick_params(labelsize=8)
            plt.tight_layout()
            st.pyplot(fig1)

        with chart_col2:
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            row = point_contrib_df.loc[plot_date].sort_values(ascending=False)
            colors = ['#2ca02c' if x > 0 else '#d62728' for x in row]
            row.plot(kind='bar', ax=ax2, color=colors)
            ax2.set_title(f"Contribution: {actual_idx_change:+.2f} pts", fontsize=12)
            ax2.axhline(0, color='black', lw=0.8)
            ax2.tick_params(labelsize=9)
            for i, v in enumerate(row):
                ax2.text(i, v + (0.1 if v > 0 else -1.5), f"{v:+.2f}", ha='center', fontsize=8, fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig2)
            
    else:
        st.error("⚠️ 該日期無交易數據。")

except Exception as e:
    st.error(f"❌ 錯誤: {e}")
