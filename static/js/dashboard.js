// Monta os gráficos do dashboard e faz polling periódico das cotações.

const CORES_PADRAO = [
    '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545',
    '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0',
];

function lerDadosJson(id) {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : null;
}

let chartAlocacao = null;

function montarChartAlocacao() {
    const dados = lerDadosJson('dados-alocacao');
    const canvas = document.getElementById('chart-alocacao');
    if (!dados || !canvas) return;

    chartAlocacao = new Chart(canvas, {
        type: 'pie',
        data: {
            labels: dados.map((a) => a.ticker),
            datasets: [{
                data: dados.map((a) => a.valor_atual),
                backgroundColor: dados.map((_, i) => CORES_PADRAO[i % CORES_PADRAO.length]),
            }],
        },
        options: { responsive: true, maintainAspectRatio: false },
    });
}

function montarChartGastos() {
    const dados = lerDadosJson('dados-gastos');
    const canvas = document.getElementById('chart-gastos');
    if (!dados || !canvas) return;

    new Chart(canvas, {
        type: 'pie',
        data: {
            labels: dados.map((c) => c.categoria__nome),
            datasets: [{
                data: dados.map((c) => c.total),
                backgroundColor: dados.map((c, i) => c.categoria__cor || CORES_PADRAO[i % CORES_PADRAO.length]),
            }],
        },
        options: { responsive: true, maintainAspectRatio: false },
    });
}

function montarChartEvolucao() {
    const canvas = document.getElementById('chart-evolucao');
    if (!canvas) return;

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: lerDadosJson('evolucao-labels'),
            datasets: [
                { label: 'Receita', data: lerDadosJson('evolucao-receitas'), backgroundColor: '#198754' },
                { label: 'Despesa', data: lerDadosJson('evolucao-despesas'), backgroundColor: '#dc3545' },
                {
                    label: 'Saldo',
                    data: lerDadosJson('evolucao-saldo'),
                    type: 'line',
                    borderColor: '#0d6efd',
                    backgroundColor: '#0d6efd',
                    tension: 0.3,
                },
            ],
        },
        options: { responsive: true, maintainAspectRatio: false },
    });
}

function montarChartComparacao() {
    const canvas = document.getElementById('chart-comparacao');
    if (!canvas) return;

    const valores = lerDadosJson('comparacao-valores');
    const cores = ['#198754', '#0d6efd', '#fd7e14'];

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: lerDadosJson('comparacao-labels'),
            datasets: [{
                data: valores,
                backgroundColor: cores,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: { x: { ticks: { callback: (v) => v + '%' } } },
        },
    });
}

function montarChartPatrimonio() {
    const canvas = document.getElementById('chart-patrimonio');
    if (!canvas) return;

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: lerDadosJson('patrimonio-labels'),
            datasets: [{
                label: 'Patrimônio',
                data: lerDadosJson('patrimonio-valores'),
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13,110,253,0.15)',
                fill: true,
                tension: 0.3,
            }],
        },
        options: { responsive: true, maintainAspectRatio: false },
    });
}

function formatarMoeda(valor) {
    return valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function atualizarCotacoes() {
    if (!window.COTACOES_JSON_URL) return;
    try {
        const resp = await fetch(window.COTACOES_JSON_URL, { headers: { Accept: 'application/json' } });
        if (!resp.ok) return;
        const dados = await resp.json();

        let patrimonio = 0;
        let algumIndisponivel = false;

        document.querySelectorAll('#tabela-ativos tr[data-ticker]').forEach((linha) => {
            const ticker = linha.dataset.ticker;
            const info = dados[ticker];
            if (!info) return;

            if (info.preco !== null && info.preco !== undefined) {
                linha.querySelector('.preco-atual').innerHTML = `R$ ${formatarMoeda(info.preco)}`;
                linha.querySelector('.valor-atual').textContent = `R$ ${formatarMoeda(info.valor_atual)}`;
                patrimonio += info.valor_atual;
            } else {
                algumIndisponivel = true;
                const valorAtualCel = linha.querySelector('.valor-atual');
                const valorAtual = parseFloat(valorAtualCel.textContent.replace(/[^\d,.-]/g, '').replace(',', '.'));
                if (!isNaN(valorAtual)) patrimonio += valorAtual;
            }
        });

        if (!algumIndisponivel && patrimonio > 0) {
            const card = document.getElementById('patrimonio-total');
            if (card) card.textContent = `R$ ${formatarMoeda(patrimonio)}`;
        }

        if (chartAlocacao) {
            chartAlocacao.data.datasets[0].data = chartAlocacao.data.labels.map((ticker) => {
                const info = dados[ticker];
                return info && info.valor_atual !== null ? info.valor_atual : chartAlocacao.data.datasets[0].data[0];
            });
            chartAlocacao.update();
        }
    } catch (err) {
        // API externa fora do ar ou rede instável — mantém os últimos valores exibidos.
        console.warn('Falha ao atualizar cotações:', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    montarChartAlocacao();
    montarChartGastos();
    montarChartEvolucao();
    montarChartPatrimonio();
    montarChartComparacao();
    setInterval(atualizarCotacoes, 60000);
});
