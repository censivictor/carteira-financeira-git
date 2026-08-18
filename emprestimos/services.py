"""Lógica de negócio de empréstimos: geração da tabela de amortização
(Price e SAC) e registro de pagamento/amortização extra.

As parcelas nunca são editadas na mão — sempre recalculadas por essas
funções a partir das condições do `Emprestimo`, igual `Ativo._calcular_posicao`
reconstrói a posição a partir do ledger de transações em investimentos.
"""

import calendar
import math
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from financas.models import Despesa

from .models import AmortizacaoExtra, Emprestimo, ParcelaEmprestimo

DUAS_CASAS = Decimal('0.01')


class SemParcelasPendentesError(Exception):
    """O empréstimo já está quitado — não há parcela pendente pra abater."""


def _quantize(valor: Decimal) -> Decimal:
    return valor.quantize(DUAS_CASAS, rounding=ROUND_HALF_UP)


def _somar_meses(data: date, n: int) -> date:
    """Soma `n` meses a `data`, ajustando o dia se o mês de destino for mais
    curto (ex: 31/jan + 1 mês = 28/fev) — mesma ideia de
    `financas.services.gerar_despesas_recorrentes_do_mes`."""
    mes_total = data.month - 1 + n
    ano = data.year + mes_total // 12
    mes = mes_total % 12 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(data.day, ultimo_dia))


def taxa_mensal(emprestimo: Emprestimo) -> Decimal:
    """Taxa de juros mensal efetiva. Se contratada ao ano, converte pra
    mensal via juros compostos: (1 + anual)^(1/12) - 1 — Decimal não suporta
    expoente fracionário, então só essa conversão passa por float (o resto
    da tabela de amortização continua inteiro em Decimal)."""
    taxa = emprestimo.taxa_juros / Decimal('100')
    if emprestimo.periodo_taxa == Emprestimo.PeriodoTaxa.MENSAL:
        return taxa
    mensal = (1 + float(taxa)) ** (1 / 12) - 1
    return Decimal(str(mensal))


def _tabela_price(saldo: Decimal, n: int, i: Decimal, data_inicial: date) -> list:
    """Sistema Price: parcela fixa do início ao fim (PMT = PV·i / (1-(1+i)^-n)).
    A última parcela absorve a diferença de arredondamento acumulada, pra
    garantir que o saldo devedor feche exatamente em zero."""
    if i == 0:
        parcela = _quantize(saldo / n)
    else:
        fator = 1 - (1 + i) ** (-n)
        parcela = _quantize(saldo * i / fator)

    linhas = []
    restante = saldo
    for numero in range(1, n + 1):
        juros = _quantize(restante * i)
        if numero == n:
            amortizacao = restante
            valor_parcela = amortizacao + juros
        else:
            amortizacao = parcela - juros
            valor_parcela = parcela
        restante -= amortizacao
        linhas.append({
            'numero': numero,
            'data_vencimento': _somar_meses(data_inicial, numero - 1),
            'valor_parcela': valor_parcela,
            'valor_juros': juros,
            'valor_amortizacao': amortizacao,
            'saldo_devedor': max(restante, Decimal('0')),
        })
    return linhas


def _tabela_sac(saldo: Decimal, n: int, i: Decimal, data_inicial: date) -> list:
    """Sistema SAC: amortização fixa, parcela decrescente (juros incide
    sobre um saldo que cai sempre do mesmo jeito)."""
    amortizacao_fixa = _quantize(saldo / n)

    linhas = []
    restante = saldo
    for numero in range(1, n + 1):
        juros = _quantize(restante * i)
        amortizacao = restante if numero == n else amortizacao_fixa
        valor_parcela = amortizacao + juros
        restante -= amortizacao
        linhas.append({
            'numero': numero,
            'data_vencimento': _somar_meses(data_inicial, numero - 1),
            'valor_parcela': valor_parcela,
            'valor_juros': juros,
            'valor_amortizacao': amortizacao,
            'saldo_devedor': max(restante, Decimal('0')),
        })
    return linhas


def gerar_tabela_amortizacao(emprestimo: Emprestimo, saldo=None, n=None, data_inicial=None) -> list:
    """Monta a tabela de amortização (Price ou SAC, conforme
    `emprestimo.sistema_amortizacao`) — não salva nada, só calcula. Aceita
    `saldo`/`n`/`data_inicial` explícitos pra ser reaproveitada tanto na
    geração inicial quanto no recálculo após uma amortização extra."""
    saldo = emprestimo.valor_total if saldo is None else saldo
    n = emprestimo.numero_parcelas if n is None else n
    data_inicial = data_inicial or emprestimo.data_primeira_parcela
    i = taxa_mensal(emprestimo)

    if emprestimo.sistema_amortizacao == Emprestimo.Sistema.SAC:
        return _tabela_sac(saldo, n, i, data_inicial)
    return _tabela_price(saldo, n, i, data_inicial)


def gerar_parcelas(emprestimo: Emprestimo) -> None:
    """(Re)gera a tabela de amortização inteira do zero — só deve ser
    chamada na criação do empréstimo, ou numa edição sem nenhuma parcela
    paga ainda (garantido por `EmprestimoSerializer.validate`)."""
    emprestimo.parcelas.all().delete()
    linhas = gerar_tabela_amortizacao(emprestimo)
    ParcelaEmprestimo.objects.bulk_create(
        [ParcelaEmprestimo(emprestimo=emprestimo, **linha) for linha in linhas]
    )


def registrar_pagamento_parcela(parcela: ParcelaEmprestimo, data_pagamento: date) -> None:
    """Marca a parcela como paga e gera a Despesa correspondente — mesmo
    padrão de `DespesaRecorrente` → `Despesa`, cai direto no orçamento e nos
    gráficos que o dashboard já calcula."""
    emprestimo = parcela.emprestimo
    despesa = Despesa.objects.create(
        usuario=emprestimo.usuario,
        categoria=emprestimo.categoria,
        descricao=f'{emprestimo.descricao} — parcela {parcela.numero}/{emprestimo.numero_parcelas}',
        valor=parcela.valor_parcela,
        data=data_pagamento,
    )
    parcela.paga = True
    parcela.data_pagamento = data_pagamento
    parcela.despesa = despesa
    parcela.save(update_fields=['paga', 'data_pagamento', 'despesa'])


def _n_necessario_price(saldo: Decimal, i: Decimal, parcela_alvo: Decimal) -> int:
    """Quantas parcelas de valor ~`parcela_alvo` são necessárias pra quitar
    `saldo` à taxa `i` no sistema Price — usado no modo 'reduzir prazo'
    (resolve n na fórmula de PMT: n = -ln(1 - saldo·i/PMT) / ln(1+i))."""
    if i == 0:
        return max(1, math.ceil(float(saldo / parcela_alvo)))
    saldo_f, i_f, parcela_f = float(saldo), float(i), float(parcela_alvo)
    razao = 1 - (saldo_f * i_f) / parcela_f
    if razao <= 0:
        raise ValueError('Esse valor de parcela não cobre nem os juros do saldo restante.')
    n = -math.log(razao) / math.log(1 + i_f)
    return max(1, math.ceil(n))


def registrar_amortizacao_extra(emprestimo: Emprestimo, valor_extra: Decimal, modo: str) -> None:
    """Abate `valor_extra` do saldo devedor (gera uma Despesa avulsa) e
    recalcula as parcelas ainda não pagas a partir do novo saldo:

    - `modo='PRAZO'`: mantém o valor da parcela atual e diminui a
      quantidade de parcelas restantes (mais comum, economiza mais juros).
    - `modo='PARCELA'`: mantém a mesma quantidade de parcelas restantes e
      diminui o valor de cada uma.
    """
    pendentes = list(emprestimo.parcelas.filter(paga=False).order_by('numero'))
    if not pendentes:
        raise SemParcelasPendentesError

    primeira_pendente = pendentes[0]
    saldo_antes = emprestimo.saldo_devedor

    if valor_extra > saldo_antes:
        raise ValueError(f'O saldo devedor é R$ {saldo_antes} — não dá pra abater mais que isso.')

    despesa = Despesa.objects.create(
        usuario=emprestimo.usuario,
        categoria=emprestimo.categoria,
        descricao=f'{emprestimo.descricao} — amortização extra',
        valor=valor_extra,
        data=date.today(),
    )
    AmortizacaoExtra.objects.create(emprestimo=emprestimo, valor=valor_extra, data=date.today(), despesa=despesa)

    novo_saldo = saldo_antes - valor_extra
    numero_inicial = primeira_pendente.numero
    i = taxa_mensal(emprestimo)
    data_proxima = primeira_pendente.data_vencimento

    emprestimo.parcelas.filter(paga=False).delete()

    if novo_saldo <= 0:
        return  # quitado — não sobra nenhuma parcela pendente

    if emprestimo.sistema_amortizacao == Emprestimo.Sistema.SAC:
        if modo == 'PRAZO':
            amortizacao_fixa = primeira_pendente.valor_amortizacao
            n_restante = max(1, math.ceil(novo_saldo / amortizacao_fixa))
        else:
            n_restante = len(pendentes)
        linhas = _tabela_sac(novo_saldo, n_restante, i, data_proxima)
    else:
        if modo == 'PRAZO':
            n_restante = _n_necessario_price(novo_saldo, i, primeira_pendente.valor_parcela)
        else:
            n_restante = len(pendentes)
        linhas = _tabela_price(novo_saldo, n_restante, i, data_proxima)

    ParcelaEmprestimo.objects.bulk_create([
        ParcelaEmprestimo(emprestimo=emprestimo, **{**linha, 'numero': numero_inicial + idx})
        for idx, linha in enumerate(linhas)
    ])
