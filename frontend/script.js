const API_URL = "http://localhost:8000/api";

function updateCharts() {
    const symbol = document.getElementById('tickerSelect').value;
    document.getElementById('display-ticker').innerText = symbol;
    document.getElementById('pred-price').innerText = "...";
    
    loadPrediction(symbol);
    loadTrend(symbol);
    loadDistribution(symbol);
    loadHistogram(symbol);
}

window.onload = function() {
    loadCorrelation();
    loadClustering();
    updateCharts();
    setTimeout(() => document.getElementById('loading').classList.add('hidden'), 2000);
};

function loadPrediction(s) {
    fetch(`${API_URL}/prediction?symbol=${s}`).then(r=>r.json()).then(d => {
        if(d[0]) {
            document.getElementById('pred-price').innerText = new Intl.NumberFormat().format(d[0].next_price);
            const el = document.getElementById('pred-trend');
            el.innerText = d[0].trend;
            el.className = d[0].trend === 'Tăng' ? 'fw-bold trend-up' : 'fw-bold trend-down';
        } else {
            document.getElementById('pred-price').innerText = "N/A";
            document.getElementById('pred-trend').innerText = "N/A";
        }
    });
}

function loadTrend(s) {
    fetch(`${API_URL}/trend?symbol=${s}`).then(r=>r.json()).then(d => {
        if(d.length===0) return;
        const daily = d.filter(i=>i.type==='Daily');
        const weekly = d.filter(i=>i.type==='Weekly Trend');
        const monthly = d.filter(i=>i.type==='Monthly Seasonal');
        
        Plotly.newPlot('trendChart', [
            {x:daily.map(i=>i.time), y:daily.map(i=>i.close), name:'Ngày', line:{color:'#ccc', width:1}},
            {x:weekly.map(i=>i.time), y:weekly.map(i=>i.close), name:'Tuần', line:{color:'blue'}},
            {x:monthly.map(i=>i.time), y:monthly.map(i=>i.close), name:'Tháng', line:{color:'red', dash:'dot'}}
        ], {xaxis:{rangeslider:{visible:true}}, margin:{t:30, b:30, l:40, r:20}});
    });
}

function loadClustering() {
    fetch(`${API_URL}/clustering`).then(r=>r.json()).then(d => {
        Plotly.newPlot('clusterChart', [{
            x:d.map(i=>i.volatility), y:d.map(i=>i.returns), text:d.map(i=>i.ticker),
            mode:'markers+text', type:'scatter', marker:{size:12, color:d.map(i=>i.cluster), colorscale:'Viridis'}
        }], {xaxis:{title:'Rủi ro'}, yaxis:{title:'Lợi nhuận'}, margin:{t:30, b:30, l:40, r:20}});
    });
}

function loadCorrelation() {
    fetch(`${API_URL}/correlation`).then(r=>r.json()).then(d => {
        if(d.length === 0) return;
        const z = d.map(r=>Object.values(r).filter(v=>typeof v==='number'));
        const l = d.map(r=>r.ticker);
        
        Plotly.newPlot('corrChart', [{
            z:z, x:l, y:l, type:'heatmap', colorscale:'RdBu', zmin:-1, zmax:1
        }], {
            margin: {t: 20, b: 100, l: 100, r: 50}, 
            autosize: true 
        });
    });
}

function loadDistribution(s) {
    fetch(`${API_URL}/distribution?symbol=${s}`).then(r=>r.json()).then(d => {
        Plotly.newPlot('distChart', [{
            x:d.map(i=>i.volume), y:d.map(i=>i.close), mode:'markers', type:'scatter', marker:{opacity:0.5, color:'purple'}
        }], {xaxis:{title:'Volume'}, yaxis:{title:'Price'}, margin:{t:30, b:30, l:50, r:20}});
    });
}

function loadHistogram(s) {
    fetch(`${API_URL}/distribution?symbol=${s}`).then(r=>r.json()).then(d => {
        Plotly.newPlot('histoChart', [{
            x:d.map(i=>i.close), type:'histogram', marker:{color:'#17a2b8'}
        }], {xaxis:{title:'Giá (VND)'}, yaxis:{title:'Tần suất'}, margin:{t:30, b:30, l:50, r:20}});
    });
}