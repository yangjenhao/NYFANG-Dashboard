with col2: # 個股貢獻度 - 修正 MU Logo 隱身問題
        logo_imgs = []
        for ticker in row.index:
            domain = DOMAIN_MAP.get(ticker, "google.com")
            
            # 針對 MU 強化白色圓形襯底
            if ticker == "MU":
                logo_imgs.append(dict(
                    source="https://upload.wikimedia.org/wikipedia/commons/f/f1/White_dot.svg", 
                    xref="paper", yref="y", 
                    x=-0.12, y=ticker,
                    sizex=0.07, sizey=0.7, # 稍微加大襯底
                    xanchor="right", yanchor="middle", 
                    sizing="contain", 
                    opacity=1.0, 
                    layer="below" # 確保在 Logo 下方
                ))

            # 主要 Logo
            logo_imgs.append(dict(
                source=f"https://www.google.com/s2/favicons?sz=64&domain={domain}",
                xref="paper", yref="y", 
                x=-0.12, y=ticker,
                sizex=0.08, sizey=0.8, 
                xanchor="right", yanchor="middle", 
                sizing="contain", 
                layer="above" # 確保在白色襯底上方
            ))

        fig_bar = go.Figure(go.Bar(
            y=row.index, x=row.values, orientation='h',
            marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
            text=row.values.round(2), textposition='outside',
            cliponaxis=False
        ))
        
        fig_bar.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, 
            margin=dict(l=140, r=60, t=50, b=20), # 增加左側邊距 (l=140) 避免 Logo 被切到
            images=logo_imgs,
            yaxis=dict(
                tickfont=dict(size=11, color=COLORS['fg']),
                ticksuffix="      ", 
                fixedrange=True,
                automargin=True # 自動調整邊距
            ),
            xaxis=dict(showgrid=True, gridcolor='#333')
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
