import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

API_URL = "http://backend:8000/api"

TICKERS = [
    "ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG",
    "MBB","MSN","MWG","PLX","POW","SAB","SHB","SSB","SSI","STB",
    "TCB","TPB","VCB","VHM","VIB","VIC","VJC","VNM","VPB","VRE"
]

app = dash.Dash(__name__)
app.title = "Hệ thống Phân tích Chứng khoán"

# --- Styling ---
PRIMARY_COLOR = "#2c3e50"
SECONDARY_COLOR = "#3498db"
SUCCESS_COLOR = "#2ecc71"
DANGER_COLOR = "#e74c3c"
WARNING_COLOR = "#f39c12"
LIGHT_BG = "#f8f9fa"
CARD_BG = "white"

CARD_STYLE = {
    "padding": "20px",
    "backgroundColor": CARD_BG,
    "borderRadius": "12px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    "border": "1px solid #ecf0f1"
}

# --- Layout ---
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("📊 HỆ THỐNG PHÂN TÍCH CHỨNG KHOÁN VIỆT NAM", 
               style={"color": "white", "marginBottom": "10px", "textAlign": "center", "fontSize": "32px", "fontWeight": "bold"}),
        html.P("Phân tích xu hướng, dự báo giá và phân cụm cổ phiếu", 
              style={"color": "#ecf0f1", "textAlign": "center", "fontSize": "16px", "marginTop": "0"})
    ], style={"padding": "40px 30px", "backgroundColor": PRIMARY_COLOR, "marginBottom": "40px"}),

    # Main Container
    html.Div([
        # Controls
        html.Div([
            html.Label("🔎 Chọn mã chứng khoán:", style={"fontWeight": "bold", "color": PRIMARY_COLOR, "marginBottom": "12px", "display": "block", "fontSize": "16px"}),
            dcc.Dropdown(
                id="tickerSelect",
                options=[{"label": t, "value": t} for t in TICKERS],
                value="HPG",
                clearable=False,
                style={"width": "100%", "fontSize": "14px"}
            )
        ], style={**CARD_STYLE, "marginBottom": "30px"}),

        # Prediction Box
        html.Div(id="prediction-box", style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(250px, 1fr))", "gap": "15px", "marginBottom": "40px"}),

        # Row 1: Price Chart Full Width
        html.Div([
            html.H3("📈 Xu hướng Giá", style={"color": PRIMARY_COLOR, "marginTop": "0", "marginBottom": "15px", "fontSize": "22px"}),
            html.Div([
                html.Label("Lọc theo:", style={"fontWeight": "bold", "marginRight": "20px", "color": "#555", "fontSize": "14px"}),
                dcc.RadioItems(
                    id="priceFilter",
                    options=[
                        {"label": " 📅 Ngày", "value": "day"},
                        {"label": " 📊 Tháng", "value": "month"},
                        {"label": " 📆 Năm", "value": "year"}
                    ],
                    value="day",
                    inline=True,
                    style={"display": "flex", "gap": "25px"}
                )
            ], style={"marginBottom": "20px"}),
            # FIX CSS: Đổi minHeight thành height để cố định chiều cao
            dcc.Graph(id="priceChart", style={"height": "450px"}) 
        ], style={**CARD_STYLE, "marginBottom": "40px"}),

        # Row 2: Volume + Histogram
        html.Div([
            html.Div([
                html.H3("📊 Khối lượng giao dịch", style={"color": PRIMARY_COLOR, "marginTop": "0", "marginBottom": "15px", "fontSize": "22px"}),
                html.Div([
                    html.Label("Lọc theo:", style={"fontWeight": "bold", "marginRight": "20px", "color": "#555", "fontSize": "14px"}),
                    dcc.RadioItems(
                        id="volumeFilter",
                        options=[
                            {"label": " 📅 Ngày", "value": "day"},
                            {"label": " 📊 Tháng", "value": "month"},
                            {"label": " 📆 Năm", "value": "year"}
                        ],
                        value="day",
                        inline=True,
                        style={"display": "flex", "gap": "25px"}
                    )
                ], style={"marginBottom": "20px"}),
                # FIX CSS
                dcc.Graph(id="volumeChart", style={"height": "450px"})
            ], style={**CARD_STYLE, "marginBottom": "40px"}),
            
            html.Div([
                html.H3("📉 Phân phối Giá & Thời gian", style={"color": PRIMARY_COLOR, "marginTop": "0", "marginBottom": "15px", "fontSize": "22px"}),
                html.Div([
                    html.Label("Lọc theo:", style={"fontWeight": "bold", "marginRight": "20px", "color": "#555", "fontSize": "14px"}),
                    dcc.RadioItems(
                        id="histoFilter",
                        options=[
                            {"label": " 📅 Ngày", "value": "day"},
                            {"label": " 📊 Tháng", "value": "month"},
                            {"label": " 📆 Năm", "value": "year"}
                        ],
                        value="day",
                        inline=True,
                        style={"display": "flex", "gap": "25px"}
                    )
                ], style={"marginBottom": "20px"}),
                # FIX CSS
                dcc.Graph(id="histoChart", style={"height": "450px"})
            ], style={**CARD_STYLE, "marginBottom": "40px"})
        ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "25px", "marginBottom": "40px"}),

        # Row 3: Trend + Seasonal
        html.Div([
            html.Div([
                html.H3("📈 Xu hướng Tháng", style={"color": PRIMARY_COLOR, "marginTop": "0", "marginBottom": "15px", "fontSize": "22px"}),
                # FIX CSS
                dcc.Graph(id="trendChart", style={"height": "450px"})
            ], style={**CARD_STYLE}),
            
            html.Div([
                html.H3("🔄 Mô hình Theo mùa", style={"color": PRIMARY_COLOR, "marginTop": "0", "marginBottom": "15px", "fontSize": "22px"}),
                # FIX CSS
                dcc.Graph(id="seasonalChart", style={"height": "450px"})
            ], style={**CARD_STYLE})
        ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "25px", "marginBottom": "40px"}),

        # Row 4: Clustering + Correlation
        html.Div([
            html.Div([
                html.H3("🎯 Phân cụm Cổ phiếu", style={"color": PRIMARY_COLOR, "marginTop": "0", "marginBottom": "15px", "fontSize": "22px"}),
                # FIX CSS
                dcc.Graph(id="clusterChart", style={"height": "500px"})
            ], style={**CARD_STYLE}),
            
            html.Div([
                html.H3("🔗 Ma trận Tương quan", style={"color": PRIMARY_COLOR, "marginTop": "0", "marginBottom": "15px", "fontSize": "22px"}),
                # FIX CSS
                dcc.Graph(id="corrChart", style={"height": "500px"})
            ], style={**CARD_STYLE})
        ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "25px"})

    ], style={"maxWidth": "1600px", "margin": "0 auto", "padding": "0 30px", "paddingBottom": "60px"})

], style={"fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif", "backgroundColor": LIGHT_BG, "minHeight": "100vh"})


# --- Helper Functions ---
def filter_data_by_type(df, filter_type):
    """Lọc dữ liệu theo ngày, tháng, hoặc năm - Đã sửa lỗi logic index"""
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])
    
    if filter_type == "day":
        return df.sort_values("time")
    
    elif filter_type == "month":
        df["month"] = df["time"].dt.to_period("M")
        # FIX: Thêm reset_index để không mất cột month
        df_agg = df.groupby("month").agg({
            "close": "mean",
            "volume": "mean" if "volume" in df.columns else None,
            "ticker": "first"
        }).reset_index() 
        df_agg["time"] = df_agg["month"].dt.to_timestamp()
        df_agg = df_agg.drop("month", axis=1)
        return df_agg.sort_values("time")
        
    elif filter_type == "year":
        df["year"] = df["time"].dt.to_period("Y")
        # FIX: Thêm reset_index
        df_agg = df.groupby("year").agg({
            "close": "mean",
            "volume": "mean" if "volume" in df.columns else None,
            "ticker": "first"
        }).reset_index()
        df_agg["time"] = df_agg["year"].dt.to_timestamp()
        df_agg = df_agg.drop("year", axis=1)
        return df_agg.sort_values("time")

# --- Callbacks ---
@app.callback(
    Output("prediction-box", "children"),
    Input("tickerSelect", "value")
)
def update_prediction(ticker):
    try:
        pred_resp = requests.get(f"{API_URL}/prediction", params={"symbols": ticker}).json()
        pred_data = pred_resp.get("data", [])
        if pred_data:
            pred = pred_data[0]
            next_price = pred.get("next_price", "N/A")
            trend = pred.get("trend", "N/A")
            today_price = pred.get("today_price", "N/A")
            trend_color = SUCCESS_COLOR if trend == "Tăng" else DANGER_COLOR
            trend_icon = "📈" if trend == "Tăng" else "📉"
        else:
            next_price, trend, today_price = "N/A", "N/A", "N/A"
            trend_color = "#95a5a6"
            trend_icon = "➖"

        cards = [
            ("Mã CP", ticker, SECONDARY_COLOR, "💰"),
            ("Giá hôm nay", f"{today_price:,.0f} VND", SECONDARY_COLOR, "📊"),
            ("Dự báo ngày mai", f"{next_price:,.0f} VND", WARNING_COLOR, "🔮"),
            (f"Xu hướng {trend_icon}", trend, trend_color, "🎯")
        ]

        return [
            html.Div([
                html.Div(icon, style={"fontSize": "32px", "marginBottom": "10px"}),
                html.H5(title, style={"color": "#7f8c8d", "marginBottom": "8px", "fontSize": "13px", "fontWeight": "600"}),
                html.H3(value, style={"color": color, "marginTop": "0", "fontSize": "22px", "fontWeight": "bold"})
            ], style={
                "padding": "25px",
                "backgroundColor": CARD_BG,
                "borderRadius": "12px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                "border": f"2px solid {color}",
                "textAlign": "center"
            })
            for title, value, color, icon in cards
        ]
    except Exception as e:
        print(f"Lỗi prediction: {e}")
        return html.Div("❌ Lỗi kết nối API", style={"color": DANGER_COLOR})


@app.callback(
    Output("priceChart", "figure"),
    Output("volumeChart", "figure"),
    Output("histoChart", "figure"),
    Output("trendChart", "figure"),
    Output("seasonalChart", "figure"),
    Output("clusterChart", "figure"),
    Output("corrChart", "figure"),
    [Input("tickerSelect", "value"), Input("priceFilter", "value"), Input("volumeFilter", "value"), Input("histoFilter", "value")]
)
def update_charts(ticker, price_filter, volume_filter, histo_filter):
    
    # --- Price Line Chart ---
    fig_price = go.Figure()
    try:
        resp = requests.get(f"{API_URL}/distribution", params={"symbols": ticker}).json()
        data = resp.get("data", [])
        if data:
            df = pd.DataFrame(data)
            df = filter_data_by_type(df, price_filter)
            
            if not df.empty:
                fig_price = px.line(df, x="time", y="close", title="",
                                   markers=True, line_shape="linear")
                fig_price.update_xaxes(title_text="Thời gian", showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
                fig_price.update_yaxes(title_text="Giá (VND)", showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
                fig_price.update_traces(line=dict(color=SECONDARY_COLOR, width=3), marker=dict(size=6))
                fig_price.update_layout(hovermode="x unified", plot_bgcolor="#fafafa", paper_bgcolor="white", margin=dict(l=60, r=20, t=30, b=60))
    except Exception as e:
        print(f"Lỗi price chart: {e}")

    # --- Volume Scatter Chart ---
    fig_volume = go.Figure()
    try:
        resp = requests.get(f"{API_URL}/distribution", params={"symbols": ticker}).json()
        data = resp.get("data", [])
        if data:
            df = pd.DataFrame(data)
            df = filter_data_by_type(df, volume_filter)
            
            if not df.empty:
                fig_volume = px.scatter(df, x="time", y="volume", title="",
                                       size="close", color="close", hover_data=["close"],
                                       color_continuous_scale="Viridis")
                fig_volume.update_xaxes(title_text="Thời gian", showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
                fig_volume.update_yaxes(title_text="Khối lượng GD", showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
                fig_volume.update_layout(hovermode="Giá", plot_bgcolor="#fafafa", paper_bgcolor="white", margin=dict(l=60, r=20, t=30, b=60))
    except Exception as e:
        print(f"Lỗi volume chart: {e}")

        # --- Histogram/Bar Chart (Modified) ---
    fig_histo = go.Figure()
    try:
        resp = requests.get(f"{API_URL}/distribution", params={"symbols": ticker}).json()
        data = resp.get("data", [])
        if data:
            df = pd.DataFrame(data)
            
            # 1. Bật lại cái lọc này để nút Radio (Ngày/Tháng/Năm) nó hoạt động
            df = filter_data_by_type(df, histo_filter)
            
            if not df.empty:
                df["time"] = pd.to_datetime(df["time"])
                
                # 2. QUAN TRỌNG: Đổi px.histogram thành px.bar
                # px.bar sẽ vẽ chính xác từng cột cho từng mốc thời gian, không tự động gom nhóm
                fig_histo = px.bar(df, x="time", y="close", 
                                   title="", 
                                   color_discrete_sequence=[SECONDARY_COLOR]) 
                
                fig_histo.update_xaxes(title_text="Thời gian", showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
                fig_histo.update_yaxes(title_text="Giá (VND)", showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
                
                # Giữ nguyên height để không bị lỗi layout
                fig_histo.update_layout(height=450, plot_bgcolor="#fafafa", paper_bgcolor="white", margin=dict(l=60, r=20, t=30, b=60))
                
                # Tooltip hiển thị
                fig_histo.update_traces(hovertemplate="Thời gian: %{x}<br>Giá: %{y:,.0f} VND")
    except Exception as e:
        print(f"Lỗi histogram: {e}")


    # --- Trend Chart (Monthly) ---
    fig_trend = go.Figure()
    try:
        resp = requests.get(f"{API_URL}/trend", params={"symbols": ticker})
        resp.raise_for_status()  # chắc chắn request thành công
        data = resp.json().get("data", [])

        if data:
            df = pd.DataFrame(data)
            if not df.empty:
                df["time"] = pd.to_datetime(df["time"])
                df = df.sort_values("time")

                fig_trend = px.line(
                    df, x="time", y="close",
                    markers=True, line_shape="linear",
                    title=""
                )
                fig_trend.update_xaxes(title_text="Tháng", showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
                fig_trend.update_yaxes(title_text="Giá trung bình (VND)", showgrid=True, gridwidth=1, gridcolor='#ecf0f1')
                fig_trend.update_traces(line=dict(color=SUCCESS_COLOR, width=3), marker=dict(size=7))
                fig_trend.update_layout(
                    hovermode="x unified",
                    plot_bgcolor="#fafafa",
                    paper_bgcolor="white",
                    margin=dict(l=60, r=20, t=30, b=60)
                )
            else:
                fig_trend.add_annotation(text="Không có dữ liệu trend", showarrow=False)
        else:
            fig_trend.add_annotation(text="Không có dữ liệu trend", showarrow=False)

    except Exception as e:
        print(f"Lỗi trend chart: {e}")
        fig_trend.add_annotation(text=f"Lỗi: {str(e)}", showarrow=False)


    # --- Seasonal Chart (Monthly by Year) ---
    fig_seasonal = go.Figure()
    try:
        resp = requests.get(f"{API_URL}/seasonal", params={"symbols": ticker})
        resp.raise_for_status()
        data = resp.json().get("data", [])

        if data:
            df = pd.DataFrame(data)
            df["time"] = pd.to_datetime(df["time"])
            df["year"] = df["time"].dt.year
            df["month"] = df["time"].dt.month

            if not df.empty:
                # Vẽ line theo từng year
                fig_seasonal = px.line(
                    df,
                    x="month",
                    y="close",
                    color="year",
                    markers=True,
                    line_shape="spline",
                    title="Seasonal Chart theo từng năm"
                )

                fig_seasonal.update_xaxes(
                    title_text="Tháng",
                    tickmode="linear",
                    tick0=1,
                    dtick=1,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="#ecf0f1"
                )
                fig_seasonal.update_yaxes(
                    title_text="Giá trung bình (VND)",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="#ecf0f1"
                )
                fig_seasonal.update_traces(marker=dict(size=7))
                fig_seasonal.update_layout(
                    hovermode="x unified",
                    plot_bgcolor="#fafafa",
                    paper_bgcolor="white",
                    margin=dict(l=60, r=20, t=30, b=60)
                )
            else:
                fig_seasonal.add_annotation(text="Không có dữ liệu seasonal", showarrow=False)
        else:
            fig_seasonal.add_annotation(text="Không có dữ liệu seasonal", showarrow=False)

    except Exception as e:
        print(f"Lỗi seasonal chart: {e}")
        fig_seasonal.add_annotation(text=f"Lỗi: {str(e)}", showarrow=False)


    # --- Clustering Chart ---
    fig_cluster = px.scatter()

    try:
        # Lấy dữ liệu clustering từ API
        resp = requests.get(f"{API_URL}/clustering").json()
        data = resp.get("data", [])

        if data:
            df = pd.DataFrame(data)
            df["returns_abs"] = df["returns"].abs()  # size luôn dương
            
            # Màu sắc cluster theo theme chuyên nghiệp
            cluster_colors = {
                0: "#3498db",  # Xanh dương - Ổn định
                1: "#e74c3c",  # Đỏ - Rủi ro cao
                2: "#2ecc71"   # Xanh lá - Tiềm năng
            }
            
            # Tên cluster dễ hiểu
            cluster_names = {
                0: "Ổn định",
                1: "Rủi ro cao", 
                2: "Tiềm năng"
            }
            df["cluster_name"] = df["cluster"].map(cluster_names)

            fig_cluster = px.scatter(
                df,
                x="volatility",
                y="returns",
                text="ticker",
                color="cluster_name",
                size="returns_abs",
                size_max=25,
                color_discrete_map={
                    "Ổn định": "#3498db",
                    "Rủi ro cao": "#e74c3c",
                    "Tiềm năng": "#2ecc71"
                },
                title="📊 Phân nhóm cổ phiếu theo Lợi suất & Biến động"
            )

            # Layout nâng cao
            fig_cluster.update_xaxes(
                title="Độ biến động (%)",
                showgrid=True,
                gridwidth=1,
                gridcolor='#e0e0e0'
            )
            fig_cluster.update_yaxes(
                title="Lợi suất trung bình năm (%)",
                showgrid=True,
                gridwidth=1,
                gridcolor='#e0e0e0',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#bdbdbd'
            )
            
            fig_cluster.update_traces(
                textposition='top center',
                textfont=dict(size=9, color='#2c3e50'),
                marker=dict(
                    line=dict(width=1.5, color='white'),
                    opacity=0.8
                ),
                hovertemplate='<b>%{text}</b><br>Lợi suất: %{y:.2f}%<br>Biến động: %{x:.2f}%<extra></extra>'
            )
            
            fig_cluster.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=70, r=150, t=80, b=70),
                legend=dict(
                    title="Nhóm cổ phiếu",
                    orientation="v",
                    yanchor="top",
                    y=0.98,
                    xanchor="left",
                    x=1.02,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#bdbdbd",
                    borderwidth=1
                ),
                font=dict(family="Arial, sans-serif", size=12),
                hovermode='closest'
            )

            # --- Thêm vùng phân chia quadrant ---
            # Tính median để vẽ đường phân chia
            median_vol = df["volatility"].median()
            median_ret = df["returns"].median()
            
            # Đường phân chia dọc
            fig_cluster.add_vline(
                x=median_vol, 
                line_dash="dash", 
                line_color="#95a5a6",
                opacity=0.4,
                annotation_text="",
            )
            
            # Đường phân chia ngang
            fig_cluster.add_hline(
                y=median_ret,
                line_dash="dash",
                line_color="#95a5a6", 
                opacity=0.4,
                annotation_text="",
            )
            
            # --- Annotation giải thích tại các góc ---
            # Góc trên phải (High return, High volatility)
            fig_cluster.add_annotation(
                x=0.95, y=0.95,
                text="🚀 Tiềm năng cao<br>Rủi ro cao",
                showarrow=False,
                xref="paper", yref="paper",
                font=dict(size=10, color="#7f8c8d"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#bdc3c7",
                borderwidth=1,
                borderpad=4,
                align="center"
            )
            
            # Góc trên trái (High return, Low volatility) 
            fig_cluster.add_annotation(
                x=0.05, y=0.95,
                text="⭐ Lý tưởng<br>Lợi suất tốt, ít biến động",
                showarrow=False,
                xref="paper", yref="paper",
                font=dict(size=10, color="#27ae60"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#bdc3c7",
                borderwidth=1,
                borderpad=4,
                align="center"
            )
            
            # Góc dưới trái (Low return, Low volatility)
            fig_cluster.add_annotation(
                x=0.05, y=0.05,
                text="💼 Bảo thủ<br>Ổn định nhưng lợi suất thấp",
                showarrow=False,
                xref="paper", yref="paper",
                font=dict(size=10, color="#3498db"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#bdc3c7",
                borderwidth=1,
                borderpad=4,
                align="center"
            )
            
            # Góc dưới phải (Low return, High volatility)
            fig_cluster.add_annotation(
                x=0.95, y=0.05,
                text="⚠️ Cảnh báo<br>Biến động cao, lợi suất thấp",
                showarrow=False,
                xref="paper", yref="paper",
                font=dict(size=10, color="#e74c3c"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#bdc3c7",
                borderwidth=1,
                borderpad=4,
                align="center"
            )

    except Exception as e:
        print(f"Lỗi clustering: {e}")

    # --- Correlation Matrix ---
    resp = requests.get(f"{API_URL}/correlation").json()
    data = resp.get("data", [])

    if data:
        # Nếu data dạng list of dict
        if isinstance(data, list) and "ticker1" in data[0]:
            df = pd.DataFrame(data)
            tickers = sorted(set(df["ticker1"].tolist() + df["ticker2"].tolist()))
            corr_matrix = df.pivot(index="ticker1", columns="ticker2", values="correlation")
            corr_matrix = corr_matrix.reindex(index=tickers, columns=tickers, fill_value=1.0)
        else:  # nếu data dạng dict vuông
            corr_matrix = pd.DataFrame(data)

        fig_corr = go.Figure(data=go.Heatmap(
            z=corr_matrix.fillna(0).values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmin=-1, zmax=1,
            text=corr_matrix.fillna(0).values,
            texttemplate='%{text:.2f}'
        ))

        fig_corr.update_xaxes(tickangle=-45)
        fig_corr.update_yaxes(autorange="reversed")


        
    return fig_price, fig_volume, fig_histo, fig_trend, fig_seasonal, fig_cluster, fig_corr


# --- Run server ---
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)