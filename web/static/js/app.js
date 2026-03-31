/**
 * Stock Dashboard — Frontend Application
 *
 * Gerencia a interface do dashboard: busca de cotações, watchlist,
 * gráficos interativos com Chart.js e armazenamento local.
 */

// ============================================================
// Estado global da aplicação
// ============================================================

const state = {
    watchlist: JSON.parse(localStorage.getItem('sd_watchlist') || '["AAPL","BTC","PETR4"]'),
    watchlistData: {},
    currentSymbol: null,
    currentHistory: null,
    currentPeriod: 30,
    chartInstance: null,
    volumeChartInstance: null,
    suggestions: [],
    isLoading: false,
};

const API_BASE = '';


// ============================================================
// Inicialização
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    loadSuggestions();
    initSearch();
    initQuickTags();
    loadWatchlist();
    loadSavedData();
});


// ============================================================
// Relógio
// ============================================================

function initClock() {
    const el = document.getElementById('headerTime');
    function update() {
        const now = new Date();
        const time = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const date = now.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
        el.innerHTML = `<span class="status-dot"></span>${date} · ${time}`;
    }
    update();
    setInterval(update, 1000);
}


// ============================================================
// Sugestões de busca
// ============================================================

async function loadSuggestions() {
    try {
        const res = await fetch(`${API_BASE}/api/watchlist/suggestions`);
        const data = await res.json();
        if (data.success) {
            state.suggestions = data.data;
        }
    } catch (e) {
        console.warn('Falha ao carregar sugestões:', e);
    }
}


// ============================================================
// Busca
// ============================================================

function initSearch() {
    const input = document.getElementById('searchInput');
    const suggestionsEl = document.getElementById('searchSuggestions');
    const btn = document.getElementById('searchBtn');

    input.addEventListener('input', () => {
        const query = input.value.trim().toLowerCase();
        if (query.length === 0) {
            suggestionsEl.classList.remove('active');
            return;
        }

        const filtered = state.suggestions.filter(s =>
            s.symbol.toLowerCase().includes(query) ||
            s.name.toLowerCase().includes(query)
        );

        if (filtered.length > 0) {
            renderSuggestions(filtered, suggestionsEl);
            suggestionsEl.classList.add('active');
        } else {
            suggestionsEl.classList.remove('active');
        }
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const symbol = input.value.trim().toUpperCase();
            if (symbol) {
                suggestionsEl.classList.remove('active');
                addToWatchlist(symbol);
                input.value = '';
            }
        }
        if (e.key === 'Escape') {
            suggestionsEl.classList.remove('active');
        }
    });

    btn.addEventListener('click', () => {
        const symbol = input.value.trim().toUpperCase();
        if (symbol) {
            suggestionsEl.classList.remove('active');
            addToWatchlist(symbol);
            input.value = '';
        }
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            suggestionsEl.classList.remove('active');
        }
    });
}

function renderSuggestions(items, container) {
    container.innerHTML = items.map(item => `
        <div class="suggestion-item" data-symbol="${item.symbol}">
            <div>
                <span class="suggestion-symbol">${item.symbol}</span>
                <span class="suggestion-name">${item.name}</span>
            </div>
            <span class="suggestion-type ${item.type}">${formatType(item.type)}</span>
        </div>
    `).join('');

    container.querySelectorAll('.suggestion-item').forEach(el => {
        el.addEventListener('click', () => {
            const symbol = el.dataset.symbol;
            container.classList.remove('active');
            document.getElementById('searchInput').value = '';
            addToWatchlist(symbol);
        });
    });
}


// ============================================================
// Quick Tags
// ============================================================

function initQuickTags() {
    document.querySelectorAll('.quick-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            const symbol = tag.dataset.symbol;
            addToWatchlist(symbol);
        });
    });
}


// ============================================================
// Watchlist
// ============================================================

function saveWatchlist() {
    localStorage.setItem('sd_watchlist', JSON.stringify(state.watchlist));
}

async function addToWatchlist(symbol) {
    symbol = symbol.toUpperCase().trim();
    if (!symbol) return;

    if (!state.watchlist.includes(symbol)) {
        state.watchlist.push(symbol);
        saveWatchlist();
    }

    await fetchQuote(symbol);
}

function removeFromWatchlist(symbol) {
    state.watchlist = state.watchlist.filter(s => s !== symbol);
    delete state.watchlistData[symbol];
    saveWatchlist();
    renderWatchlist();

    if (state.currentSymbol === symbol) {
        state.currentSymbol = null;
        state.currentHistory = null;
        renderChartEmpty();
    }

    showToast(`${symbol} removido da watchlist`, 'info');
}

async function loadWatchlist() {
    const grid = document.getElementById('watchlistGrid');
    grid.innerHTML = state.watchlist.map(() =>
        `<div class="skeleton skeleton-card"></div>`
    ).join('');

    for (const symbol of state.watchlist) {
        await fetchQuote(symbol);
    }
}

async function fetchQuote(symbol) {
    try {
        const res = await fetch(`${API_BASE}/api/quote/${symbol}`);
        const json = await res.json();

        if (json.success) {
            state.watchlistData[symbol] = json.data;
            renderWatchlist();
            showToast(`${symbol} atualizado`, 'success');
        } else {
            showToast(`Erro: ${json.error}`, 'error');
        }
    } catch (e) {
        showToast(`Falha ao buscar ${symbol}`, 'error');
    }
}

function renderWatchlist() {
    const grid = document.getElementById('watchlistGrid');
    const badgeEl = document.getElementById('watchlistBadge');
    badgeEl.textContent = state.watchlist.length;

    if (state.watchlist.length === 0) {
        grid.innerHTML = `
            <div class="chart-empty" style="grid-column: 1/-1; height: 120px;">
                <div class="chart-empty-text">Nenhum ativo na watchlist</div>
                <div class="chart-empty-hint">Use a busca acima para adicionar ativos</div>
            </div>
        `;
        return;
    }

    grid.innerHTML = state.watchlist.map((symbol, i) => {
        const data = state.watchlistData[symbol];
        if (!data) {
            return `<div class="skeleton skeleton-card" style="animation-delay: ${i * 100}ms"></div>`;
        }

        const isPositive = data.change >= 0;
        const changeClass = isPositive ? 'positive' : 'negative';
        const arrow = isPositive ? '▲' : '▼';
        const typeLabel = formatType(data.asset_type);
        const typeClass = data.asset_type;

        return `
            <div class="price-card ${changeClass} card-enter" 
                 style="animation-delay: ${i * 80}ms"
                 data-symbol="${symbol}"
                 onclick="selectAsset('${symbol}')">
                <button class="price-card-remove" onclick="event.stopPropagation(); removeFromWatchlist('${symbol}')" title="Remover">✕</button>
                <div class="price-card-header">
                    <div>
                        <div class="price-card-symbol">${data.symbol}</div>
                        <div class="price-card-name">${data.name}</div>
                    </div>
                    <span class="price-card-type-badge suggestion-type ${typeClass}">${typeLabel}</span>
                </div>
                <div class="price-card-body">
                    <div class="price-card-price">${formatCurrency(data.price, data.currency)}</div>
                    <div class="price-card-change">
                        <div class="price-card-change-value ${changeClass}-text">${arrow} ${formatNumber(Math.abs(data.change))}</div>
                        <div class="price-card-change-pct ${changeClass}-text">${data.change_percent >= 0 ? '+' : ''}${data.change_percent.toFixed(2)}%</div>
                    </div>
                </div>
                <div class="price-card-mini-chart" id="mini-${symbol}"></div>
            </div>
        `;
    }).join('');

    // Carrega mini-charts
    state.watchlist.forEach(symbol => {
        if (state.watchlistData[symbol]) {
            loadMiniChart(symbol);
        }
    });
}


// ============================================================
// Mini Charts (sparklines)
// ============================================================

async function loadMiniChart(symbol) {
    const container = document.getElementById(`mini-${symbol}`);
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/api/history/${symbol}?days=7`);
        const json = await res.json();

        if (json.success && json.data.length > 0) {
            const closes = json.data.map(d => d.Close);
            const isPositive = closes[closes.length - 1] >= closes[0];
            const color = isPositive ? '#10b981' : '#ef4444';

            const canvas = document.createElement('canvas');
            canvas.width = container.offsetWidth || 240;
            canvas.height = 40;
            container.innerHTML = '';
            container.appendChild(canvas);

            const ctx = canvas.getContext('2d');
            drawSparkline(ctx, closes, canvas.width, canvas.height, color);
        }
    } catch (e) {
        // Silently fail for mini chart
    }
}

function drawSparkline(ctx, data, width, height, color) {
    if (data.length < 2) return;

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const padding = 2;

    ctx.clearRect(0, 0, width, height);

    // Draw gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, color + '20');
    gradient.addColorStop(1, color + '00');

    ctx.beginPath();
    data.forEach((val, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - padding - ((val - min) / range) * (height - padding * 2);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    // Fill
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    data.forEach((val, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - padding - ((val - min) / range) * (height - padding * 2);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
}


// ============================================================
// Seleção de ativo e gráfico principal
// ============================================================

async function selectAsset(symbol) {
    state.currentSymbol = symbol;

    // Highlight card
    document.querySelectorAll('.price-card').forEach(card => {
        card.style.borderColor = card.dataset.symbol === symbol
            ? 'var(--accent-primary)'
            : '';
    });

    await loadChart(symbol, state.currentPeriod);

    // Scroll to chart
    document.getElementById('chartSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function loadChart(symbol, days) {
    const wrapper = document.getElementById('chartCanvasWrapper');
    const statsEl = document.getElementById('chartStats');

    // Show loading
    wrapper.innerHTML = `
        <div class="chart-loading">
            <div class="chart-loading-icon">⟳</div>
            <div>Carregando dados de ${symbol}...</div>
        </div>
    `;
    statsEl.innerHTML = '';

    // Update header
    updateChartHeader(symbol);

    try {
        const res = await fetch(`${API_BASE}/api/history/${symbol}?days=${days}`);
        const json = await res.json();

        if (!json.success) {
            wrapper.innerHTML = `
                <div class="chart-empty">
                    <div class="chart-empty-icon">⚠️</div>
                    <div class="chart-empty-text">${json.error}</div>
                </div>
            `;
            return;
        }

        state.currentHistory = json.data;
        state.currentPeriod = days;

        renderMainChart(symbol, json.data);
        renderChartStats(json.data);
        loadSavedData();
    } catch (e) {
        wrapper.innerHTML = `
            <div class="chart-empty">
                <div class="chart-empty-icon">🌐</div>
                <div class="chart-empty-text">Erro de conexão</div>
                <div class="chart-empty-hint">Verifique sua internet e tente novamente</div>
            </div>
        `;
    }
}

function updateChartHeader(symbol) {
    const data = state.watchlistData[symbol];
    const symbolEl = document.getElementById('chartSymbol');
    const priceEl = document.getElementById('chartPriceLive');
    const changeEl = document.getElementById('chartChangeLive');

    symbolEl.textContent = symbol;

    if (data) {
        priceEl.textContent = formatCurrency(data.price, data.currency);
        const isPositive = data.change >= 0;
        changeEl.textContent = `${isPositive ? '+' : ''}${data.change_percent.toFixed(2)}%`;
        changeEl.className = `chart-change-live ${isPositive ? 'positive' : 'negative'}`;
    } else {
        priceEl.textContent = '—';
        changeEl.textContent = '';
        changeEl.className = 'chart-change-live';
    }
}

function renderMainChart(symbol, data) {
    const wrapper = document.getElementById('chartCanvasWrapper');
    wrapper.innerHTML = '<canvas id="mainChart"></canvas>';

    const canvas = document.getElementById('mainChart');
    const ctx = canvas.getContext('2d');

    const labels = data.map(d => d.Date);
    const closes = data.map(d => d.Close);
    const opens = data.map(d => d.Open);

    const isPositive = closes[closes.length - 1] >= closes[0];
    const lineColor = isPositive ? '#10b981' : '#ef4444';

    // Gradient fill
    const gradientFill = ctx.createLinearGradient(0, 0, 0, 380);
    gradientFill.addColorStop(0, lineColor + '25');
    gradientFill.addColorStop(0.5, lineColor + '08');
    gradientFill.addColorStop(1, lineColor + '00');

    if (state.chartInstance) {
        state.chartInstance.destroy();
    }

    state.chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Fechamento',
                    data: closes,
                    borderColor: lineColor,
                    backgroundColor: gradientFill,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: lineColor,
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2,
                },
                {
                    label: 'Abertura',
                    data: opens,
                    borderColor: '#6366f180',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.35,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    pointHoverBackgroundColor: '#6366f1',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        color: '#94a3b8',
                        font: { family: "'Inter', sans-serif", size: 12, weight: 500 },
                        boxWidth: 12,
                        boxHeight: 2,
                        borderRadius: 1,
                        useBorderRadius: true,
                        padding: 16,
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    titleFont: { family: "'Inter', sans-serif", size: 13, weight: 600 },
                    bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
                    displayColors: true,
                    boxWidth: 8,
                    boxHeight: 8,
                    boxPadding: 4,
                    callbacks: {
                        label: (ctx) => ` ${ctx.dataset.label}: ${formatNumber(ctx.parsed.y)}`,
                    },
                },
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.03)',
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#64748b',
                        font: { family: "'Inter', sans-serif", size: 11 },
                        maxTicksLimit: 8,
                        maxRotation: 0,
                    },
                    border: { display: false },
                },
                y: {
                    position: 'right',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.03)',
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#64748b',
                        font: { family: "'JetBrains Mono', monospace", size: 11 },
                        callback: (val) => formatNumber(val),
                    },
                    border: { display: false },
                },
            },
        },
    });

    // Render volume chart
    renderVolumeChart(data, lineColor);
}

function renderVolumeChart(data, color) {
    const wrapper = document.getElementById('volumeChartWrapper');
    if (!wrapper) return;

    wrapper.innerHTML = '<canvas id="volumeChart"></canvas>';
    const ctx = document.getElementById('volumeChart').getContext('2d');

    const labels = data.map(d => d.Date);
    const volumes = data.map(d => d.Volume || 0);

    if (state.volumeChartInstance) {
        state.volumeChartInstance.destroy();
    }

    state.volumeChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: color + '30',
                borderColor: color + '60',
                borderWidth: 1,
                borderRadius: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
                    callbacks: {
                        label: (ctx) => ` Volume: ${ctx.parsed.y.toLocaleString('pt-BR')}`,
                    },
                },
            },
            scales: {
                x: {
                    display: false,
                },
                y: {
                    display: false,
                },
            },
        },
    });
}

function renderChartStats(data) {
    const statsEl = document.getElementById('chartStats');

    const closes = data.map(d => d.Close);
    const volumes = data.map(d => d.Volume || 0);

    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const avg = closes.reduce((a, b) => a + b, 0) / closes.length;
    const first = closes[0];
    const last = closes[closes.length - 1];
    const variation = ((last - first) / first * 100);
    const totalVolume = volumes.reduce((a, b) => a + b, 0);

    const variationColor = variation >= 0 ? 'positive-text' : 'negative-text';

    statsEl.innerHTML = `
        <div class="chart-stat">
            <div class="chart-stat-label">Mínima</div>
            <div class="chart-stat-value">${formatNumber(min)}</div>
        </div>
        <div class="chart-stat">
            <div class="chart-stat-label">Máxima</div>
            <div class="chart-stat-value">${formatNumber(max)}</div>
        </div>
        <div class="chart-stat">
            <div class="chart-stat-label">Média</div>
            <div class="chart-stat-value">${formatNumber(avg)}</div>
        </div>
        <div class="chart-stat">
            <div class="chart-stat-label">Variação</div>
            <div class="chart-stat-value ${variationColor}">${variation >= 0 ? '+' : ''}${variation.toFixed(2)}%</div>
        </div>
        <div class="chart-stat">
            <div class="chart-stat-label">Volume Total</div>
            <div class="chart-stat-value">${abbreviateNumber(totalVolume)}</div>
        </div>
        <div class="chart-stat">
            <div class="chart-stat-label">Dias</div>
            <div class="chart-stat-value">${data.length}</div>
        </div>
    `;
}

function renderChartEmpty() {
    const wrapper = document.getElementById('chartCanvasWrapper');
    const statsEl = document.getElementById('chartStats');

    document.getElementById('chartSymbol').textContent = '—';
    document.getElementById('chartPriceLive').textContent = '';
    document.getElementById('chartChangeLive').textContent = '';

    wrapper.innerHTML = `
        <div class="chart-empty">
            <div class="chart-empty-icon">📊</div>
            <div class="chart-empty-text">Selecione um ativo</div>
            <div class="chart-empty-hint">Clique em um card da watchlist para ver o gráfico</div>
        </div>
    `;
    statsEl.innerHTML = '';

    const volumeWrapper = document.getElementById('volumeChartWrapper');
    if (volumeWrapper) volumeWrapper.innerHTML = '';
}


// ============================================================
// Period tabs
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.chart-period-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            if (!state.currentSymbol) return;

            document.querySelectorAll('.chart-period-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const days = parseInt(tab.dataset.days);
            loadChart(state.currentSymbol, days);
        });
    });
});


// ============================================================
// Saved data table
// ============================================================

async function loadSavedData() {
    try {
        const res = await fetch(`${API_BASE}/api/saved`);
        const json = await res.json();

        if (json.success) {
            renderSavedTable(json.data);
        }
    } catch (e) {
        console.warn('Falha ao carregar dados salvos:', e);
    }
}

function renderSavedTable(assets) {
    const tbody = document.getElementById('savedTableBody');

    if (!assets || assets.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td class="table-empty" colspan="5">
                    Nenhum dado salvo localmente. Visualize gráficos para salvar automaticamente.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = assets.map(asset => `
        <tr class="fade-in">
            <td class="symbol-cell">${asset.symbol}</td>
            <td>${asset.file}</td>
            <td class="mono">${asset.records}</td>
            <td class="mono">${asset.size_kb} KB</td>
            <td class="muted">${asset.last_modified}</td>
        </tr>
    `).join('');
}


// ============================================================
// Toasts
// ============================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');

    const icons = { success: '✓', error: '✕', info: 'ℹ' };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ'}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}


// ============================================================
// Utilidades de formatação
// ============================================================

function formatCurrency(value, currency = 'USD') {
    if (value >= 1000) {
        return `${currency} ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `${currency} ${value.toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })}`;
}

function formatNumber(value) {
    if (value >= 1000) {
        return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return value.toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
}

function abbreviateNumber(num) {
    if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toLocaleString('pt-BR');
}

function formatType(type) {
    const map = { us_stock: 'US', br_stock: 'BR', crypto: 'CRYPTO' };
    return map[type] || type;
}
