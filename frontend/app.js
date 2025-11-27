const API_URL = "http://localhost:8000/api";

const COLORS = {
    secondary: "#3498db",
    success: "#2ecc71",
    danger: "#e74c3c",
    warning: "#f39c12"
};

// Event listeners
document.getElementById("tickerSelect").addEventListener("change", updateAll);
document.querySelectorAll('input[name="priceFilter"]').forEach(r => r.addEventListener("change", updateAll));
document.querySelectorAll('input[name="volumeFilter"]').forEach(r => r.addEventListener("change", updateAll));
document.querySelectorAll('input[name="histoFilter"]').forEach(r => r.addEventListener("change", updateAll));

async function updateAll() {
    const ticker = document.getElementById("tickerSelect").value;
    const priceFilter = document.querySelector('input[name="priceFilter"]:checked').value;
    const volumeFilter = document.querySelector('input[name="volumeFilter"]:checked').value;
    const histoFilter = document.querySelector('input[name="histoFilter"]:checked').value;

    updatePrediction(ticker);
    updateCharts(ticker, priceFilter, volumeFilter, histoFilter);
    updateCorrelation(); // gọi luôn để cập nhật ma trận tương quan
}

async function updatePrediction(ticker) {
    try {
        const res = await fetch(`${API_URL}/prediction?symbols=${ticker}`);
        const json = await res.json();
        const pred = json.data?.[0] || {};
        
        const { next_price = "N/A", trend = "N/A", today_price = "N/A" } = pred;
        const trendColor = trend === "Tăng" ? COLORS.success : COLORS.danger;
        const trendIcon = trend === "Tăng" ? "📈" : "📉";

        const cards = [
            { title: "Mã CP", value: ticker, color: COLORS.secondary, icon: "💰" },
            { title: "Giá hôm nay", value: `${Number(today_price).toLocaleString()} VND`, color: COLORS.secondary, icon: "📊" },
            { title: "Dự báo ngày mai", value: `${Number(next_price).toLocaleString()} VND`, color: COLORS.warning, icon: "🔮" },
            { title: `Xu hướng ${trendIcon}`, value: trend, color: trendColor, icon: "🎯" }
        ];

        document.getElementById("prediction-box").innerHTML = cards.map(c => `
            <div class="pred-card" style="border-color: ${c.color}">
                <div class="pred-icon">${c.icon}</div>
                <div class="pred-title">${c.title}</div>
                <h3 class="pred-value" style="color: ${c.color}">${c.value}</h3>
            </div>
        `).join("");
    } catch (e) {
        console.error("Lỗi prediction:", e);
        document.getElementById("prediction-box").innerHTML = '<div style="color: red;">❌ Lỗi kết nối API</div>';
    }
}

async function updateCharts(ticker, priceFilter, volumeFilter, histoFilter) {
    try {
        const distResp = await fetch(`${API_URL}/distribution?symbols=${ticker}`);
        const distData = await distResp.json();
        const data = distData.data || [];

        // Price Chart
        if (data.length) {
            const df = filterData(data, priceFilter);
            Plotly.newPlot("priceChart", [
                { x: df.map(d => d.time), y: df.map(d => d.close), type: "scatter", mode: "lines+markers", line: { color: COLORS.secondary, width: 3 } }
            ], { title: "", xaxis: { title: "Thời gian" }, yaxis: { title: "Giá (VND)" }, hovermode: "x unified" }, { responsive: true });
        }

        // Volume Chart
        const dfVol = filterData(data, volumeFilter);
        if (dfVol.length) {
            Plotly.newPlot("volumeChart", [
                { x: dfVol.map(d => d.time), y: dfVol.map(d => d.volume), type: "scatter", mode: "markers", marker: { size: 8, color: COLORS.secondary } }
            ], { title: "", xaxis: { title: "Thời gian" }, yaxis: { title: "Khối lượng GD" } }, { responsive: true });
        }

        // Histogram
        const dfHisto = filterData(data, histoFilter);
        if (dfHisto.length) {
            Plotly.newPlot("histoChart", [
                { x: dfHisto.map(d => d.time), y: dfHisto.map(d => d.close), type: "bar", marker: { color: COLORS.secondary } }
            ], { title: "", xaxis: { title: "Thời gian" }, yaxis: { title: "Giá (VND)" } }, { responsive: true });
        }

        // Trend Chart
        const trendResp = await fetch(`${API_URL}/trend?symbols=${ticker}`);
        const trendData = (await trendResp.json()).data || [];
        if (trendData.length) {
            Plotly.newPlot("trendChart", [
                { x: trendData.map(d => d.time), y: trendData.map(d => d.close), type: "scatter", mode: "lines+markers", line: { color: COLORS.success, width: 3 } }
            ], { title: "", xaxis: { title: "Tháng" }, yaxis: { title: "Giá trung bình (VND)" } }, { responsive: true });
        }

        // Seasonal Chart
        const seasResp = await fetch(`${API_URL}/seasonal?symbols=${ticker}`);
        const seasData = (await seasResp.json()).data || [];
        if (seasData.length) {
            const grouped = {};
            seasData.forEach(d => {
                const year = new Date(d.time).getFullYear();
                if (!grouped[year]) grouped[year] = [];
                grouped[year].push(d);
            });

            const traces = Object.entries(grouped).map(([year, items]) => ({
                x: items.map(d => new Date(d.time).getMonth() + 1),
                y: items.map(d => d.close),
                name: year,
                type: "scatter",
                mode: "lines+markers"
            }));
            Plotly.newPlot("seasonalChart", traces, { title: "", xaxis: { title: "Tháng" }, yaxis: { title: "Giá (VND)" } }, { responsive: true });
        }

        // Clustering Chart
        const clustResp = await fetch(`${API_URL}/clustering`);
        const clustJson = await clustResp.json();
        const clustData = clustJson.data || [];

        if (clustData.length) {
            const medianVol = clustData.map(d => d.volatility).sort((a, b) => a - b)[Math.floor(clustData.length / 2)];
            const medianRet = clustData.map(d => d.returns).sort((a, b) => a - b)[Math.floor(clustData.length / 2)];

            const colorMap = { "Ổn định": "#3498db", "Rủi ro cao": "#e74c3c", "Tiềm năng": "#2ecc71" };
            const grouped = { "Ổn định": [], "Rủi ro cao": [], "Tiềm năng": [] };

            clustData.forEach(d => {
                let clusterName;
                if (d.volatility > medianVol && d.returns < medianRet) clusterName = "Rủi ro cao";
                else if (d.returns > medianRet) clusterName = "Tiềm năng";
                else clusterName = "Ổn định";
                grouped[clusterName].push(d);
            });

            const traces = Object.entries(grouped).map(([name, items]) => ({
                x: items.map(d => d.volatility),
                y: items.map(d => d.returns),
                text: items.map(d => d.ticker),
                mode: "markers+text",
                type: "scatter",
                name,
                marker: { size: 10, color: colorMap[name], opacity: 0.8, line: { width: 1, color: "white" } },
                textposition: "top center",
                textfont: { size: 9, color: "#2c3e50" },
                hovertemplate: "<b>%{text}</b><br>Lợi suất: %{y:.2f}%<br>Biến động: %{x:.2f}%<extra></extra>"
            }));

            const layout = {
                title: "📊 Phân nhóm cổ phiếu theo Lợi suất & Biến động",
                xaxis: { title: "Độ biến động (%)", showgrid: true, gridwidth: 1, gridcolor: "#e0e0e0" },
                yaxis: { title: "Lợi suất trung bình năm (%)", showgrid: true, gridwidth: 1, gridcolor: "#e0e0e0", zeroline: true, zerolinewidth: 2, zerolinecolor: "#bdbdbd" },
                plot_bgcolor: "white",
                paper_bgcolor: "white",
                margin: { l: 70, r: 150, t: 80, b: 70 },
                legend: { title: { text: "Nhóm cổ phiếu" }, x: 1.02, y: 0.98, bgcolor: "rgba(255,255,255,0.9)", bordercolor: "#bdbdbd", borderwidth: 1 },
                hovermode: "closest"
            };

            Plotly.newPlot("clusterChart", traces, layout, { responsive: true });

            Plotly.relayout("clusterChart", {
                shapes: [
                    { type: "line", x0: medianVol, x1: medianVol, y0: Math.min(...clustData.map(d => d.returns)), y1: Math.max(...clustData.map(d => d.returns)), line: { dash: "dash", color: "#95a5a6", width: 1 } },
                    { type: "line", y0: medianRet, y1: medianRet, x0: Math.min(...clustData.map(d => d.volatility)), x1: Math.max(...clustData.map(d => d.volatility)), line: { dash: "dash", color: "#95a5a6", width: 1 } }
                ],
                annotations: [
                    { x: 0.95, y: 0.95, xref: "paper", yref: "paper", text: "🚀 Tiềm năng<br>Lợi suất cao", showarrow: false, bgcolor: "rgba(255,255,255,0.8)", bordercolor: "#bdc3c7", borderwidth: 1, borderpad: 4 },
                    { x: 0.05, y: 0.95, xref: "paper", yref: "paper", text: "⭐ Ổn định<br>Lợi suất trung bình, ít biến động", showarrow: false, bgcolor: "rgba(255,255,255,0.8)", bordercolor: "#bdc3c7", borderwidth: 1, borderpad: 4 },
                    { x: 0.05, y: 0.05, xref: "paper", yref: "paper", text: "💼 Bảo thủ<br>Ổn định nhưng lợi suất thấp", showarrow: false, bgcolor: "rgba(255,255,255,0.8)", bordercolor: "#bdc3c7", borderwidth: 1, borderpad: 4 },
                    { x: 0.95, y: 0.05, xref: "paper", yref: "paper", text: "⚠️ Rủi ro cao<br>Biến động cao, lợi suất thấp", showarrow: false, bgcolor: "rgba(255,255,255,0.8)", bordercolor: "#bdc3c7", borderwidth: 1, borderpad: 4 }
                ]
            });
        }

    } catch (e) {
        console.error("Lỗi update charts:", e);
    }
}

// --- Correlation Matrix ---
async function updateCorrelation() {
    try {
        const resp = await fetch(`${API_URL}/correlation`);
        const json = await resp.json();
        const data = json.data || {};

        const tickers = Object.keys(data).sort();
        const zData = tickers.map(t1 => tickers.map(t2 => data[t1][t2] ?? 0));

        Plotly.newPlot("corrChart", [{
            z: zData,
            x: tickers,
            y: tickers,
            type: "heatmap",
            colorscale: "RdBu",
            zmin: -1,
            zmax: 1,
            text: zData.map(row => row.map(val => val.toFixed(2))),
            texttemplate: "%{text}",
            textfont: { size: 6 },
            hovertemplate: "%{y} - %{x}: %{z:.2f}<extra></extra>",
            xgap: 0.2, // tăng ô theo chiều ngang
            ygap: 0.2  // tăng ô theo chiều dọc
        }], {
            xaxis: { title: "Mã CK", tickangle: -45 },
            yaxis: { title: "Mã CK", autorange: "reversed" },
            margin: { b: 70, l: 70 },
            plot_bgcolor: "white",
            paper_bgcolor: "white"
        }, { responsive: true });

    } catch (e) {
        console.error("Lỗi correlation:", e);
        document.getElementById("corrChart").innerHTML = '<div style="color:red;">❌ Lỗi tải dữ liệu</div>';
    }
}

function filterData(data, type) {
    if (type === "day") return data;
    if (type === "month") {
        const grouped = {};
        data.forEach(d => {
            const month = new Date(d.time).toISOString().slice(0, 7);
            if (!grouped[month]) grouped[month] = [];
            grouped[month].push(d);
        });
        return Object.entries(grouped).map(([month, items]) => ({
            time: month,
            close: items.reduce((a, b) => a + b.close, 0) / items.length,
            volume: items.reduce((a, b) => a + (b.volume || 0), 0) / items.length
        }));
    }
    if (type === "year") {
        const grouped = {};
        data.forEach(d => {
            const year = new Date(d.time).getFullYear();
            if (!grouped[year]) grouped[year] = [];
            grouped[year].push(d);
        });
        return Object.entries(grouped).map(([year, items]) => ({
            time: year,
            close: items.reduce((a, b) => a + b.close, 0) / items.length,
            volume: items.reduce((a, b) => a + (b.volume || 0), 0) / items.length
        }));
    }
}

// Init
updateAll();
