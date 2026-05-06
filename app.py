with col2: # 個股貢獻度
        logo_imgs = []
        for i, ticker in enumerate(row.index):
            domain = DOMAIN_MAP.get(ticker, "google.com")
            
            # 針對 MU (Micron) 加入純白底色塊，徹底解決深色 Logo 破圖或黑影問題
            if ticker == "MU":
                logo_imgs.append(dict(
                    source="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/square.svg", # 使用純色方形作為墊底
                    xref="paper", yref="y", x=-0.12, y=ticker,
                    sizex=0.06, sizey=0.6, 
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
            height=450, margin=dict(l=120, r=50, t=50, b=20),
            title=dict(text=f"CONTRIBUTION ({selected_label})", font=dict(color=COLORS['gold'], size=14)),
            images=logo_imgs,
            yaxis=dict(
                tickmode='array', tickvals=list(range(len(row))), ticktext=row.index,
                ticksuffix="      ", 
                fixedrange=True
            ),
            xaxis=dict(showgrid=True, gridcolor='#222')
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
