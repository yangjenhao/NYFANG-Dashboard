# --- 5. MAIN CONTENT (ENHANCED WITH DATA BACKFILLING) ---
try:
    raw_data = fetch_data(period_val)
    
    # 確保數據不為空且執行 Forward Fill 處理休市日
    if raw_data.empty:
        st.warning("YAHOO FINANCE RETURNED NO DATA. PLEASE REFRESH.")
        st.stop()
        
    raw_data = raw_data.ffill()
    idx_series = raw_data[INDEX_SYMBOL].dropna()
    stock_prices = raw_data[OFFICIAL_TICKERS].dropna()

    idx_diff = idx_series.diff()
    returns = stock_prices.pct_change().dropna()
    
    point_contrib_df = pd.DataFrame(index=returns.index, columns=OFFICIAL_TICKERS)
    for date in returns.index:
        if date in idx_diff.index:
            actual_total_pts = idx_diff.loc[date]
            r = returns.loc[date]
            raw_impact = r * 0.1
            impact_sum = raw_impact.sum()
            point_contrib_df.loc[date] = raw_impact * (actual_total_pts / impact_sum) if abs(impact_sum) > 0 else 0

    target_ts = pd.to_datetime(target_date)
    
    # 【關鍵修復】：尋找小於等於選擇日期的最新有效交易日
    valid_dates = point_contrib_df.index[point_contrib_df.index <= target_ts]

    if not valid_dates.empty:
        plot_date = valid_dates[-1]  # 自動鎖定最近的一個交易日
        
        # 如果用戶選的是今天，但美股還沒開盤，這會自動抓到昨天（或上週五）的資料
        actual_idx_change = idx_diff.loc[plot_date]
        current_price = idx_series.loc[plot_date]
        
        # 取得前一天的價格計算漲跌幅
        prev_idx = idx_series.shift(1).loc[plot_date]
        change_pct = (actual_idx_change / prev_idx) * 100 if prev_idx != 0 else 0

        # ... (後續繪圖代碼保持不變)
