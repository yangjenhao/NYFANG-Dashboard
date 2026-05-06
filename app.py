with col2:
        # 標題
        st.markdown(f"<p style='color:{COLORS['gold']}; font-size:14px; margin-bottom:10px;'>CONTRIBUTION ({selected_label})</p>", unsafe_allow_html=True)
        
        row = cum_contrib.sort_values(ascending=True)
        
        # 建立兩欄：左側放 Logo，右側放圖表
        logo_col, chart_col = st.columns([0.1, 0.9])
        
        with logo_col:
            # 為了對齊圖表的高度，這裡加入一點間距 (根據實際視覺調整)
            st.write("") 
            for ticker in reversed(row.index):
                domain = DOMAIN_MAP.get(ticker, "google.com")
                # 使用 Clearbit API 獲取 Logo 並固定寬度
                st.image(f"https://logo.clearbit.com/{domain}", width=20)
                st.write("") # 增加間距以對齊橫條圖

        with chart_col:
            fig_bar = go.Figure(go.Bar(
                y=row.index, x=row.values, orientation='h',
                marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values], 
                text=row.values.round(2), textposition='auto',
                showlegend=False
            ))

            fig_bar.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                margin=dict(l=0, r=10, t=0, b=10), # 將左邊距設為 0
                height=400, 
                yaxis=dict(showticklabels=True, fixedrange=True), # 保持文字標籤
                xaxis=dict(fixedrange=True, showgrid=True, gridcolor='#222'),
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
