"""Integração com APIs externas de cotação (brapi.dev, CoinGecko, Banco Central).

Única camada do projeto que fala com o mundo externo — views nunca chamam
`requests` diretamente. Toda função de cotação/série segue o mesmo padrão:
  1. Faz UMA chamada em lote para todos os tickers/ids pedidos (nunca uma
     chamada por ativo, pra não estourar rate limit).
  2. Guarda o resultado em cache por um TTL curto.
  3. Se a chamada externa falhar (timeout, rede fora, API fora do ar), cai
     num cache "stale" de até 24h em vez de propagar exceção — o dashboard
     nunca deve quebrar por causa de API externa indisponível.

As funções de autocomplete (buscar_tickers_b3/buscar_cripto) não têm fallback
"stale" — se a API estiver fora do ar, simplesmente não há sugestões, o que
é uma degradação aceitável (o usuário ainda pode digitar manualmente).
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

TIMEOUT = 5
STALE_TTL = 60 * 60 * 24  # 24h
BUSCA_CACHE_TTL = 5 * 60  # 5min — autocomplete não precisa ser tão fresco quanto cotação


def get_cotacoes_acoes(tickers: list[str]) -> dict:
    """Retorna {ticker: {'preco': float|None, 'variacao_dia_pct': float|None}}.

    Fonte: brapi.dev (https://brapi.dev). O plano gratuito pode exigir um
    token (settings.BRAPI_TOKEN) e ter delay de alguns minutos — não é
    tempo real "de bolsa profissional", mas é o melhor disponível de graça.
    """
    if not tickers:
        return {}

    chave = f"brapi:{','.join(sorted(tickers))}"
    chave_stale = chave + ':stale'

    cached = cache.get(chave)
    if cached is not None:
        return cached

    try:
        params = {}
        if settings.BRAPI_TOKEN:
            params['token'] = settings.BRAPI_TOKEN
        resp = requests.get(
            f"https://brapi.dev/api/quote/{','.join(tickers)}",
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        resultado = {
            item['symbol']: {
                'preco': item.get('regularMarketPrice'),
                'variacao_dia_pct': item.get('regularMarketChangePercent'),
            }
            for item in data.get('results', [])
        }
        cache.set(chave, resultado, timeout=settings.COTACAO_CACHE_TTL)
        cache.set(chave_stale, resultado, timeout=STALE_TTL)
        return resultado
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning('Falha ao buscar cotações B3 (%s): %s', tickers, exc)
        return cache.get(chave_stale) or {}


def _coingecko_headers() -> dict:
    """Header de autenticação da CoinGecko (plano Demo gratuito). Sem chave
    configurada, a API ainda funciona — só com limite de requisições menor."""
    if settings.COINGECKO_API_KEY:
        return {'x-cg-demo-api-key': settings.COINGECKO_API_KEY}
    return {}


def get_cotacoes_cripto(coingecko_ids: list[str], vs: str = 'brl') -> dict:
    """Retorna {coingecko_id: {'preco': float|None, 'variacao_dia_pct': float|None}}.

    Fonte: CoinGecko, praticamente tempo real. Funciona sem chave; com
    settings.COINGECKO_API_KEY (plano Demo gratuito) ganha limite de
    requisições maior.
    """
    if not coingecko_ids:
        return {}

    chave = f"coingecko:{','.join(sorted(coingecko_ids))}:{vs}"
    chave_stale = chave + ':stale'

    cached = cache.get(chave)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={
                'ids': ','.join(coingecko_ids),
                'vs_currencies': vs,
                'include_24hr_change': 'true',
            },
            headers=_coingecko_headers(),
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        resultado = {
            cid: {
                'preco': info.get(vs),
                'variacao_dia_pct': info.get(f'{vs}_24h_change'),
            }
            for cid, info in data.items()
        }
        cache.set(chave, resultado, timeout=settings.COTACAO_CACHE_TTL)
        cache.set(chave_stale, resultado, timeout=STALE_TTL)
        return resultado
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning('Falha ao buscar cotações cripto (%s): %s', coingecko_ids, exc)
        return cache.get(chave_stale) or {}


def buscar_tickers_b3(query: str, tipo: str) -> list:
    """Autocomplete de tickers B3 (ação ou FII), busca no universo completo.

    `tipo` é 'ACAO' ou 'FII' — usado só pra mapear os filtros da brapi.
    Retorna [{'value': ticker, 'label': 'TICKER — Nome da empresa'}].
    Sem fallback "stale": se a API falhar, retorna lista vazia (autocomplete
    degrada pra digitação manual, sem quebrar a página).
    """
    query = (query or '').strip()
    if len(query) < 2:
        return []

    chave = f"brapi-busca:{tipo}:{query.lower()}"
    cached = cache.get(chave)
    if cached is not None:
        return cached

    params = {'search': query, 'limit': 10}
    if tipo == 'FII':
        params['type'] = 'fund'
        params['subType'] = 'fii'
    else:
        params['type'] = 'stock'
    if settings.BRAPI_TOKEN:
        params['token'] = settings.BRAPI_TOKEN

    try:
        resp = requests.get('https://brapi.dev/api/v2/tickers', params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        resultado = [
            {'value': item['symbol'], 'label': f"{item['symbol']} — {item.get('name', '')}"}
            for item in data.get('results', [])
        ]
        cache.set(chave, resultado, timeout=BUSCA_CACHE_TTL)
        return resultado
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning('Falha ao buscar tickers B3 (%s, %s): %s', tipo, query, exc)
        return []


def buscar_cripto(query: str) -> list:
    """Autocomplete de criptomoedas via busca do CoinGecko (todo o catálogo).

    Retorna [{'value': coingecko_id, 'label': 'Nome (SIMBOLO)'}].
    """
    query = (query or '').strip()
    if len(query) < 2:
        return []

    chave = f"coingecko-busca:{query.lower()}"
    cached = cache.get(chave)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            'https://api.coingecko.com/api/v3/search',
            params={'query': query},
            headers=_coingecko_headers(),
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        resultado = [
            {'value': c['id'], 'label': f"{c['name']} ({c['symbol'].upper()})"}
            for c in data.get('coins', [])[:10]
        ]
        cache.set(chave, resultado, timeout=BUSCA_CACHE_TTL)
        return resultado
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning('Falha ao buscar cripto (%s): %s', query, exc)
        return []


def get_serie_bcb(codigo_serie: int, data_inicial: date) -> dict:
    """Retorna {data: Decimal(taxa_do_dia_pct)} da série temporal do Banco
    Central (SGS) entre data_inicial e hoje. Série 12 = CDI diário, 11 = Selic
    diária — ambas públicas, sem chave.
    """
    hoje = date.today()
    chave = f"bcb:{codigo_serie}:{data_inicial.isoformat()}"
    chave_stale = chave + ':stale'

    cached = cache.get(chave)
    if cached is not None:
        return cached

    try:
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados"
        resp = requests.get(
            url,
            params={
                'formato': 'json',
                'dataInicial': data_inicial.strftime('%d/%m/%Y'),
                'dataFinal': hoje.strftime('%d/%m/%Y'),
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        resultado = {
            datetime.strptime(item['data'], '%d/%m/%Y').date(): Decimal(item['valor'])
            for item in data
        }
        cache.set(chave, resultado, timeout=6 * 60 * 60)  # taxa só muda 1x/dia
        cache.set(chave_stale, resultado, timeout=STALE_TTL)
        return resultado
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning('Falha ao buscar série BCB %s (desde %s): %s', codigo_serie, data_inicial, exc)
        return cache.get(chave_stale) or {}


def calcular_valor_atual_renda_fixa(ativo) -> Decimal | None:
    """Estima o valor atual de um ativo de renda fixa compondo a taxa
    histórica do indexador desde a data de aplicação.

    É uma ESTIMATIVA (convenção ACT/365, composição simplificada) — não
    substitui o extrato oficial do banco/corretora. Retorna None se não
    conseguir calcular (sem dados do BCB e sem cache stale), quem chama
    deve cair no fallback (mostrar valor_aplicado).
    """
    if not (ativo.data_aplicacao and ativo.taxa_contratada is not None and ativo.valor_aplicado is not None):
        return None

    hoje = date.today()

    if ativo.indexador in (ativo.Indexador.CDI, ativo.Indexador.SELIC):
        codigo_serie = 12 if ativo.indexador == ativo.Indexador.CDI else 11
        serie = get_serie_bcb(codigo_serie, ativo.data_aplicacao)
        if not serie:
            return None
        fator = 1.0
        for dia, taxa in serie.items():
            if ativo.data_aplicacao < dia <= hoje:
                fator *= 1 + float(taxa) / 100
        fator_ajustado = fator ** (float(ativo.taxa_contratada) / 100)
        return ativo.valor_aplicado * Decimal(str(fator_ajustado))

    if ativo.indexador == ativo.Indexador.PREFIXADO:
        dias_corridos = (hoje - ativo.data_aplicacao).days
        if dias_corridos <= 0:
            return ativo.valor_aplicado
        fator = (1 + float(ativo.taxa_contratada) / 100) ** (dias_corridos / 365)
        return ativo.valor_aplicado * Decimal(str(fator))

    return None


def get_variacao_cdi(data_inicial: date) -> Decimal | None:
    """Variação acumulada do CDI (100%, benchmark puro) entre data_inicial e
    hoje. Reaproveita get_serie_bcb (já cacheada), sem limite de período —
    o Banco Central não tem a restrição de plano que a brapi.dev tem."""
    serie = get_serie_bcb(12, data_inicial)
    if not serie:
        return None
    hoje = date.today()
    fator = 1.0
    for dia, taxa in serie.items():
        if data_inicial < dia <= hoje:
            fator *= 1 + float(taxa) / 100
    return Decimal(str((fator - 1) * 100))


def get_variacao_ibovespa(data_inicial: date) -> dict | None:
    """Variação do Ibovespa entre a data real usada e hoje.

    O plano gratuito da brapi.dev só libera `range` até '3mo' (testado e
    confirmado — 'range=2y' é rejeitado) — se `data_inicial` for mais antiga
    que isso, a função usa os 3 meses disponíveis mesmo assim e retorna
    `periodo_limitado=True` + `data_inicio_real` pra quem chama avisar o
    usuário, em vez de fingir que comparou o período todo.
    """
    chave = f"ibovespa-variacao:{data_inicial.isoformat()}"
    chave_stale = chave + ':stale'

    cached = cache.get(chave)
    if cached is not None:
        return cached

    try:
        params = {'range': '3mo', 'interval': '1d'}
        if settings.BRAPI_TOKEN:
            params['token'] = settings.BRAPI_TOKEN
        resp = requests.get('https://brapi.dev/api/quote/%5EBVSP', params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()['results'][0]
        preco_atual = data['regularMarketPrice']
        hist = data.get('historicalDataPrice', [])
        if not hist or preco_atual is None:
            return cache.get(chave_stale)

        preco_inicial = hist[0]['close']
        data_inicio_real = datetime.fromtimestamp(hist[0]['date']).date()
        resultado = {
            'variacao_pct': (preco_atual - preco_inicial) / preco_inicial * 100,
            'data_inicio_real': data_inicio_real,
            'periodo_limitado': data_inicio_real > data_inicial,
        }
        cache.set(chave, resultado, timeout=6 * 60 * 60)
        cache.set(chave_stale, resultado, timeout=STALE_TTL)
        return resultado
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        logger.warning('Falha ao buscar variação do Ibovespa (desde %s): %s', data_inicial, exc)
        return cache.get(chave_stale)
