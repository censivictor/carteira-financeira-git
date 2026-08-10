"""Integração com APIs externas de cotação (brapi.dev e CoinGecko).

Única camada do projeto que fala com o mundo externo — views nunca chamam
`requests` diretamente. Toda função aqui:
  1. Faz UMA chamada em lote para todos os tickers/ids pedidos (nunca uma
     chamada por ativo, pra não estourar rate limit).
  2. Guarda o resultado em cache por COTACAO_CACHE_TTL segundos.
  3. Se a chamada externa falhar (timeout, rede fora, API fora do ar), cai
     num cache "stale" de até 24h em vez de propagar exceção — o dashboard
     nunca deve quebrar por causa de API externa indisponível.
"""

import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

TIMEOUT = 5
STALE_TTL = 60 * 60 * 24  # 24h


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


def get_cotacoes_cripto(coingecko_ids: list[str], vs: str = 'brl') -> dict:
    """Retorna {coingecko_id: {'preco': float|None, 'variacao_dia_pct': float|None}}.

    Fonte: CoinGecko, endpoint público sem chave, praticamente tempo real.
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
