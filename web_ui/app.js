let salesChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    checkHealth();
    renderChart(getParsedSales());
    
    document.getElementById('btn-forecast').addEventListener('click', () => handleAction('forecast'));
    document.getElementById('btn-anomalies').addEventListener('click', () => handleAction('anomalies'));
    document.getElementById('btn-analyze').addEventListener('click', () => handleAction('analyze'));
});

function getParsedSales() {
    const raw = document.getElementById('past-sales').value;
    return raw.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
}

function renderChart(dataArr) {
    if(!dataArr || dataArr.length === 0) return;
    
    const ctx = document.getElementById('salesChart').getContext('2d');
    const labels = dataArr.map((_, i) => `Day ${i+1}`);
    
    if(salesChartInstance) salesChartInstance.destroy();
    
    salesChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sales Output',
                data: dataArr,
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: '#3b82f6',
                pointRadius: 4
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
            scales: { x: { grid: { color: 'rgba(51, 65, 85, 0.5)' }, ticks: { color: '#94a3b8' } },
                      y: { grid: { color: 'rgba(51, 65, 85, 0.5)' }, ticks: { color: '#94a3b8' } } }
        }
    });
}

function setUIStatus(loading) {
    document.getElementById('btn-forecast').disabled = loading;
    document.getElementById('btn-anomalies').disabled = loading;
    document.getElementById('btn-analyze').disabled = loading;
    
    const loader = document.getElementById('loader');
    const results = document.getElementById('results-card');
    const errorBox = document.getElementById('error-box');
    
    errorBox.classList.add('hidden');
    if(loading) {
        loader.classList.remove('hidden');
        results.classList.add('hidden');
    } else { loader.classList.add('hidden'); }
}

function showError(msg) {
    const errorBox = document.getElementById('error-box');
    errorBox.innerHTML = `⚠️ ${msg}`;
    errorBox.classList.remove('hidden');
}

async function checkHealth() {
    const badge = document.getElementById('api-status');
    try {
        const res = await fetch('/health');
        if(!res.ok) throw new Error("Offline");
        const data = await res.json();
        badge.className = 'status-badge online';
        badge.innerText = `Online (${data.uptime_seconds}s)`;
    } catch(e) {
        badge.className = 'status-badge offline';
        badge.innerText = 'Offline';
    }
}

async function handleAction(type) {
    const productName = document.getElementById('product-name').value;
    const parsedSales = getParsedSales();
    
    if(parsedSales.length < 3) return showError("At least 3 valid sales numbers required.");
    if(type === 'forecast' && (parsedSales.length < 7 || parsedSales.length > 14)) return showError("Forecasting strictly requires 7-14 integers.");

    renderChart(parsedSales);
    setUIStatus(true);
    
    let path = '';
    let payload = {};
    
    if(type === 'forecast') {
        path = '/forecast-demand'; payload = { product_name: productName, past_sales: parsedSales };
    } else if(type === 'anomalies') {
        path = '/detect-anomalies'; payload = { product_name: productName, past_sales: parsedSales };
    } else if(type === 'analyze') {
        path = '/analyze';
        payload = { data: [{ product_id: 'p1', product_name: productName || 'Item', sales_volume: parsedSales.reduce((a,b)=>a+b, 0), revenue: parsedSales.reduce((a,b)=>a+b, 0) * 10 }] };
    }

    try {
        const res = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await res.json();
        if(!res.ok) throw new Error(data.detail || "API Error");
        populateResults(data, type);
    } catch(err) { showError(err.message); } finally { setUIStatus(false); }
}

function populateResults(data, type) {
    let intel = type === 'analyze' ? data.results[0] : data.intelligence;

    document.getElementById('res-insight').innerText = intel.insight;
    document.getElementById('res-confidence').innerText = intel.confidence + " Confidence";
    document.getElementById('res-action').innerText = intel.action;
    document.getElementById('res-reason').innerText = intel.reasoning;

    const grid = document.getElementById('metadata-grid'); grid.innerHTML = '';
    for(const key in data) {
        if(key === 'intelligence' || key === 'results') continue;
        const div = document.createElement('div'); div.className = 'meta-box'; 
        div.innerHTML = `<span>${key.replace('_', ' ')}</span><strong>${data[key]}</strong>`;
        grid.appendChild(div);
    }
    document.getElementById('results-card').classList.remove('hidden');
}
