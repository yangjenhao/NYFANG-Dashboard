# --- 圖二：貢獻度圖 ---
    
    # 移除 ticker_labels 變數，僅保留 logo_imgs
    logo_imgs = [dict(
        source=f"https://www.google.com/s2/favicons?sz=128&domain={DOMAIN_MAP.get(t, 'google.com')}",
        xref="paper", yref="y", 
        x=-0.01,          # 稍微離開軸線
        y=i,
        sizex=0.045, sizey=0.45, 
        xanchor="right", yanchor="middle", sizing="contain", layer="above"
    ) for i, t in enumerate(row.index)]

    fig_bar = go.Figure(go.Bar(
        y=row.index, x=row.values, orientation='h',
        marker_color=[COLORS['up'] if x > 0 else COLORS['down'] for x in row.values],
        text=row.values.round(2), textposition='outside',
        textfont=dict(color=COLORS['muted'], size=10), cliponaxis=False 
    ))
    
    fig_bar.update_layout(
        template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=550, 
        margin=dict(l=60, r=40, t=50, b=40), # 左側邊界縮小至 60，因不再需要容納文字
        images=logo_imgs,
        annotations=[],                       # 清空 annotations，隱藏公司名稱文字
        yaxis=dict(showticklabels=False, fixedrange=True), 
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.05)', fixedrange=True),
        title=dict(
            text=f"CONTRIBUTION ({selected_label})", 
            font=dict(color=COLORS['gold'], size=16, family="Josefin Sans"),
            x=0.5, xanchor="center"
        ),
        bargap=0.3 
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
