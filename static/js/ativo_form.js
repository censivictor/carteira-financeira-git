// Formulário de ativo: mostra/esconde campos conforme o Tipo escolhido e
// oferece autocomplete real (B3 via brapi.dev, cripto via CoinGecko) nos
// campos de ticker e ID do CoinGecko.

function tipoAtual() {
    const select = document.getElementById('id_tipo');
    return select ? select.value : '';
}

function atualizarVisibilidadeCampos() {
    const tipo = tipoAtual();
    document.querySelectorAll('[data-tipo-show]').forEach((wrapper) => {
        const tipos = wrapper.dataset.tipoShow.split(',');
        wrapper.style.display = (tipos.includes('SEMPRE') || tipos.includes(tipo)) ? '' : 'none';
    });
}

function debounce(fn, ms) {
    let timer = null;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
}

function montarAutocomplete({ inputId, containerId, tipoParam, ativoPara, onSelect }) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(containerId);
    if (!input || !container) return;

    let controller = null;

    const buscar = debounce(async (q) => {
        if (q.length < 2 || (ativoPara && !ativoPara.includes(tipoAtual()))) {
            container.style.display = 'none';
            container.innerHTML = '';
            return;
        }
        if (controller) controller.abort();
        controller = new AbortController();

        const tipo = typeof tipoParam === 'function' ? tipoParam() : tipoParam;
        const url = `${window.BUSCAR_ATIVOS_URL}?tipo=${encodeURIComponent(tipo)}&q=${encodeURIComponent(q)}`;

        try {
            const resp = await fetch(url, { signal: controller.signal, headers: { Accept: 'application/json' } });
            if (!resp.ok) return;
            const dados = await resp.json();
            renderizarSugestoes(dados.results || []);
        } catch (err) {
            if (err.name !== 'AbortError') console.warn('Falha na busca de ativos:', err);
        }
    }, 300);

    function renderizarSugestoes(results) {
        container.innerHTML = '';
        if (!results.length) {
            container.style.display = 'none';
            return;
        }
        results.forEach((item) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'list-group-item list-group-item-action';
            btn.textContent = item.label;
            btn.addEventListener('click', () => {
                onSelect(item);
                container.style.display = 'none';
                container.innerHTML = '';
            });
            container.appendChild(btn);
        });
        container.style.display = 'block';
    }

    input.addEventListener('input', () => buscar(input.value.trim()));
    document.addEventListener('click', (ev) => {
        if (!container.contains(ev.target) && ev.target !== input) {
            container.style.display = 'none';
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    atualizarVisibilidadeCampos();

    const selectTipo = document.getElementById('id_tipo');
    if (selectTipo) {
        selectTipo.addEventListener('change', atualizarVisibilidadeCampos);
    }

    // Autocomplete de ticker (Ação/FII) — busca no universo completo da B3.
    montarAutocomplete({
        inputId: 'id_ticker',
        containerId: 'ticker-suggestions',
        tipoParam: () => (tipoAtual() === 'FII' ? 'FII' : 'ACAO'),
        ativoPara: ['ACAO', 'FII'],
        onSelect: (item) => {
            document.getElementById('id_ticker').value = item.value;
            const label = item.label.split(' — ');
            if (label.length > 1) {
                const nomeField = document.getElementById('id_nome');
                if (nomeField && !nomeField.value) nomeField.value = label[1];
            }
        },
    });

    // Autocomplete de criptomoeda — busca por nome, preenche o ID do CoinGecko.
    montarAutocomplete({
        inputId: 'id_coingecko_id',
        containerId: 'coingecko-suggestions',
        tipoParam: 'CRIPTO',
        onSelect: (item) => {
            document.getElementById('id_coingecko_id').value = item.value;
            const match = item.label.match(/^(.*) \(([A-Z0-9]+)\)$/);
            if (match) {
                const nomeField = document.getElementById('id_nome');
                const tickerField = document.getElementById('id_ticker');
                if (nomeField && !nomeField.value) nomeField.value = match[1];
                if (tickerField && !tickerField.value) tickerField.value = match[2];
            }
        },
    });
});
