from decimal import Decimal

from django.db.models import Min, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from cartoes.models import FaturaCartao
from emprestimos.models import Emprestimo
from financas import services as financas_services
from financas.models import CategoriaDespesa, Despesa, Receita
from investimentos import services
from investimentos.models import AlocacaoAlvo, Ativo, PatrimonioSnapshot, Provento, TransacaoAtivo

MESES_PT = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
TIPOS_COTADOS_B3 = (Ativo.Tipo.ACAO, Ativo.Tipo.FII)


def _meses_recentes(n=12, referencia=None):
    """Lista de (ano, mes) dos últimos n meses, do mais antigo pro mais recente."""
    referencia = referencia or timezone.now().date().replace(day=1)
    ano, mes = referencia.year, referencia.month
    meses = []
    for _ in range(n):
        meses.append((ano, mes))
        mes -= 1
        if mes == 0:
            mes, ano = 12, ano - 1
    return list(reversed(meses))


def _variacao_pct(atual: Decimal, anterior: Decimal):
    """Retorna a variação percentual de `anterior` para `atual`, ou None se
    não há mês anterior pra comparar (evita divisão por zero)."""
    if not anterior:
        return None
    return float((atual - anterior) / anterior * 100)


def build_dashboard_data(usuario):
    """Monta todo o dict de dados do dashboard — agregação de investimentos,
    proventos, comparação com mercado, receitas/despesas, orçamento e
    evolução mensal — tudo restrito aos dados de `usuario`. Reaproveitada
    pela API DRF (`core/api_views.py::DashboardAPIView`)."""
    # --- Carteira de investimentos ---
    ativos = Ativo.objects.filter(usuario=usuario, ativo_flag=True)
    tickers = [a.ticker for a in ativos if a.tipo in TIPOS_COTADOS_B3]
    cripto_ids = [a.coingecko_id for a in ativos if a.tipo == Ativo.Tipo.CRIPTO and a.coingecko_id]

    cotacoes_acoes = services.get_cotacoes_acoes(tickers)
    cotacoes_cripto = services.get_cotacoes_cripto(cripto_ids)
    # Moedas de exibição != BRL realmente em uso — normalmente nenhuma, então
    # não gera chamada extra à API pra quem nunca mexeu nisso (ver
    # investimentos/models.py::Ativo.moeda).
    moedas_nativas = {a.moeda for a in ativos if a.tipo == Ativo.Tipo.CRIPTO and a.moeda != Ativo.Moeda.BRL}
    cotacoes_cripto_nativa = {
        moeda: services.get_cotacoes_cripto(cripto_ids, vs=moeda.lower()) for moeda in moedas_nativas
    }

    alocacao = []
    valor_investido_total = Decimal('0')
    valor_atual_total = Decimal('0')
    # Total atual por classe (Ação/FII/Cripto/Renda Fixa) — alimenta a
    # comparação com a alocação-alvo mais abaixo.
    valor_atual_por_tipo = {}
    # Subtotal só de Ação/FII/Cripto (exclui Renda Fixa) — usado na
    # comparação com CDI/Ibovespa mais abaixo, já que Renda Fixa não é
    # "risco de mercado" e comparar de novo contra CDI seria redundante.
    valor_investido_mercado = Decimal('0')
    valor_atual_mercado = Decimal('0')

    for ativo in ativos:
        # Ação/FII/Cripto sem nenhuma transação lançada ainda (posição
        # zerada) não fazem sentido na pizza/tabela do dashboard — mas
        # continuam normalmente em /investimentos/ pra lançar a 1ª compra.
        if ativo.tipo != Ativo.Tipo.RENDA_FIXA and not ativo.quantidade:
            continue

        valor_investido = ativo.valor_investido

        # Lógica de valoração (cotar + fallback pro preço médio/valor
        # aplicado quando a API está fora do ar) mora em services.avaliar_ativo
        # — reaproveitada também por MetaFinanceira.valor_atual (metas/models.py)
        # via services.avaliar_ativos, pra não duplicar essa regra em dois lugares.
        avaliacao = services.avaliar_ativo(ativo, cotacoes_acoes, cotacoes_cripto, cotacoes_cripto_nativa)
        valor_atual = avaliacao['valor_atual']
        cotacao_disponivel = avaliacao['cotacao_disponivel']

        if ativo.tipo == Ativo.Tipo.RENDA_FIXA:
            quantidade_exibicao = None
            preco_exibicao = None
        else:
            quantidade_exibicao = float(ativo.quantidade)
            preco_exibicao = float(avaliacao['preco_atual']) if avaliacao['preco_atual'] is not None else None
        preco_nativo_exibicao = (
            float(avaliacao['preco_atual_nativo']) if avaliacao['preco_atual_nativo'] is not None else None
        )

        valor_atual_total += valor_atual
        valor_investido_total += valor_investido
        valor_atual_por_tipo[ativo.tipo] = valor_atual_por_tipo.get(ativo.tipo, Decimal('0')) + valor_atual
        if ativo.tipo != Ativo.Tipo.RENDA_FIXA:
            valor_atual_mercado += valor_atual
            valor_investido_mercado += valor_investido

        alocacao.append({
            'ticker': ativo.ticker,
            'tipo': ativo.get_tipo_display(),
            'tipo_code': ativo.tipo,
            'quantidade': quantidade_exibicao,
            'preco_atual': preco_exibicao,
            'valor_atual': float(valor_atual),
            'valor_investido': float(valor_investido),
            'ganho_perda_pct': _variacao_pct(valor_atual, valor_investido) or 0,
            'cotacao_disponivel': cotacao_disponivel,
            # preco_atual/valor_atual acima são SEMPRE BRL (alimentam os
            # totais do patrimônio) — isso aqui é só a leitura adicional na
            # moeda de exibição escolhida pro ativo, quando != BRL.
            'moeda': ativo.moeda if ativo.tipo == Ativo.Tipo.CRIPTO else Ativo.Moeda.BRL,
            'preco_atual_nativo': preco_nativo_exibicao,
        })

    ganho_perda_total_pct = _variacao_pct(valor_atual_total, valor_investido_total) or 0

    # --- Alocação-alvo (comparação com a % desejada por classe) ---
    # Só entra na comparação a classe que tem alvo definido — sem nenhum
    # alvo cadastrado, a seção simplesmente não aparece no dashboard.
    percentuais_alvo = {a.tipo: a.percentual_alvo for a in AlocacaoAlvo.objects.filter(usuario=usuario)}
    alocacao_alvo = []
    for tipo_key, tipo_label in Ativo.Tipo.choices:
        if tipo_key not in percentuais_alvo:
            continue
        pct_alvo = percentuais_alvo[tipo_key]
        valor_tipo = valor_atual_por_tipo.get(tipo_key, Decimal('0'))
        pct_atual = float(valor_tipo / valor_atual_total * 100) if valor_atual_total else 0
        valor_alvo = valor_atual_total * pct_alvo / Decimal('100')
        alocacao_alvo.append({
            'tipo': tipo_key,
            'tipo_display': tipo_label,
            'valor_atual': float(valor_tipo),
            'pct_atual': pct_atual,
            'pct_alvo': float(pct_alvo),
            'desvio_pct': pct_atual - float(pct_alvo),
            # positivo = falta comprar pra chegar no alvo; negativo = tem sobra (considere vender/parar de aportar)
            'valor_para_ajustar': float(valor_alvo - valor_tipo),
        })

    # --- Empréstimos (saldo devedor total) ---
    # Poucos empréstimos pra uso pessoal — soma em Python (saldo_devedor é
    # uma property calculada a partir da tabela de parcelas, não uma coluna).
    divida_emprestimos = sum(
        (e.saldo_devedor for e in Emprestimo.objects.filter(usuario=usuario)), Decimal('0')
    )
    # Fatura de cartão só vira Despesa quando é paga — enquanto isso, o
    # valor em aberto é uma dívida "escondida" que ainda não apareceu nos
    # gastos do mês, então também precisa entrar no patrimônio líquido.
    divida_cartoes = FaturaCartao.objects.filter(cartao__usuario=usuario, paga=False).aggregate(
        s=Sum('parcelas__valor')
    )['s'] or Decimal('0')
    divida_total = divida_emprestimos + divida_cartoes
    patrimonio_liquido = valor_atual_total - divida_total

    # --- Renda e despesas do mês ---
    hoje = timezone.now().date()

    # --- Proventos (dividendos/JCP/rendimentos) ---
    # Poucos registros pra uso pessoal — soma em Python direto, sem agregação
    # SQL, já que valor_total é uma property calculada (quantidade na data-com).
    proventos_mes = Decimal('0')
    proventos_total = Decimal('0')
    for p in Provento.objects.filter(ativo__usuario=usuario).select_related('ativo'):
        valor = p.valor_total
        proventos_total += valor
        data_ref = p.data_pagamento or p.data_com
        if data_ref.year == hoje.year and data_ref.month == hoje.month:
            proventos_mes += valor
    ganho_com_proventos = valor_atual_total - valor_investido_total + proventos_total
    retorno_total_pct = (
        float(ganho_com_proventos / valor_investido_total * 100) if valor_investido_total else 0
    )

    # --- Comparação com CDI/Ibovespa ---
    # Desde a 1ª transação de Ação/FII/Cripto (Renda Fixa fica de fora, já é
    # resolvida contra CDI/Selic internamente). Sem transação nenhuma, a
    # seção simplesmente não aparece (data_inicio_investimentos = None).
    data_inicio_investimentos = TransacaoAtivo.objects.filter(
        ativo__usuario=usuario, ativo__ativo_flag=True
    ).aggregate(m=Min('data'))['m']

    retorno_mercado_pct = None
    variacao_cdi_pct = None
    comparacao_ibovespa = None
    if data_inicio_investimentos:
        ganho_mercado = valor_atual_mercado - valor_investido_mercado + proventos_total
        retorno_mercado_pct = (
            float(ganho_mercado / valor_investido_mercado * 100) if valor_investido_mercado else None
        )
        variacao_cdi = services.get_variacao_cdi(data_inicio_investimentos)
        variacao_cdi_pct = float(variacao_cdi) if variacao_cdi is not None else None
        comparacao_ibovespa = services.get_variacao_ibovespa(data_inicio_investimentos)

    variacao_ibovespa_pct = comparacao_ibovespa['variacao_pct'] if comparacao_ibovespa else None
    comparacao_labels = ['Sua carteira', 'CDI', 'Ibovespa']
    comparacao_valores = [retorno_mercado_pct, variacao_cdi_pct, variacao_ibovespa_pct]

    # --- Snapshot diário de patrimônio (alimenta o gráfico histórico) ---
    # update_or_create por data: reabrir o dashboard no mesmo dia só
    # atualiza o snapshot de hoje, nunca duplica.
    PatrimonioSnapshot.objects.update_or_create(
        usuario=usuario,
        data=hoje,
        defaults={
            'valor_total': valor_atual_total,
            'valor_investido_total': valor_investido_total,
        },
    )
    snapshots = PatrimonioSnapshot.objects.filter(usuario=usuario).order_by('data')
    patrimonio_historico_labels = [s.data.strftime('%d/%m/%y') for s in snapshots]
    patrimonio_historico_valores = [float(s.valor_total) for s in snapshots]

    # --- Despesas recorrentes do mês (aluguel, assinaturas...) ---
    # Idempotente: se já existe a despesa gerada desse mês, não duplica.
    financas_services.gerar_despesas_recorrentes_do_mes(usuario, referencia=hoje)

    # --- Evolução mensal (últimos 12 meses) ---
    # Calculado aqui (antes das seções que usam só "mês atual"/"mês
    # anterior") de propósito: esses totais são um subconjunto do que já
    # vem nesses dois dicts, então reaproveitar evita rodar 4 queries a mais
    # buscando o mesmo dado de novo. Cada query é uma ida-e-volta ao banco —
    # em produção (Render e Neon em regiões diferentes) isso pesa bem mais
    # no tempo de resposta do dashboard do que o volume de dados em si.
    meses = _meses_recentes(12, referencia=hoje.replace(day=1))

    receitas_por_mes = {
        (d['mes'].year, d['mes'].month): d['total']
        for d in Receita.objects.filter(usuario=usuario)
        .annotate(mes=TruncMonth('data')).values('mes').annotate(total=Sum('valor'))
    }
    despesas_por_mes = {
        (d['mes'].year, d['mes'].month): d['total']
        for d in Despesa.objects.filter(usuario=usuario)
        .annotate(mes=TruncMonth('data')).values('mes').annotate(total=Sum('valor'))
    }

    evolucao_labels = [f'{MESES_PT[m]}/{str(a)[2:]}' for a, m in meses]
    evolucao_receitas = [float(receitas_por_mes.get(chave, 0)) for chave in meses]
    evolucao_despesas = [float(despesas_por_mes.get(chave, 0)) for chave in meses]
    evolucao_saldo = [r - d for r, d in zip(evolucao_receitas, evolucao_despesas)]

    ano_atual, mes_atual = hoje.year, hoje.month
    ano_anterior, mes_anterior = _meses_recentes(2, referencia=hoje.replace(day=1))[0]

    receita_mes_atual = receitas_por_mes.get((ano_atual, mes_atual), Decimal('0'))
    despesa_mes_atual = despesas_por_mes.get((ano_atual, mes_atual), Decimal('0'))
    receita_mes_anterior = receitas_por_mes.get((ano_anterior, mes_anterior), Decimal('0'))
    despesa_mes_anterior = despesas_por_mes.get((ano_anterior, mes_anterior), Decimal('0'))

    saldo_mes_atual = receita_mes_atual - despesa_mes_atual
    variacao_receita_pct = _variacao_pct(receita_mes_atual, receita_mes_anterior)
    variacao_despesa_pct = _variacao_pct(despesa_mes_atual, despesa_mes_anterior)
    pct_gasto_da_renda = float(despesa_mes_atual / receita_mes_atual * 100) if receita_mes_atual else None

    # --- Gastos por categoria (mês atual) — pizza 2 ---
    gastos_por_categoria = list(
        Despesa.objects.filter(usuario=usuario, data__year=ano_atual, data__month=mes_atual)
        .values('categoria__nome', 'categoria__cor')
        .annotate(total=Sum('valor'))
        .order_by('-total')
    )

    # --- Orçamento por categoria (mês atual) ---
    # Mostra TODA categoria com orçamento definido, mesmo sem gasto ainda
    # esse mês (0%) — não só as que já têm despesa lançada. Reaproveita
    # gastos_por_categoria (mesmo agrupamento) em vez de buscar de novo só
    # sem a cor.
    totais_por_categoria = {g['categoria__nome']: g['total'] for g in gastos_por_categoria}
    orcamentos = []
    for cat in CategoriaDespesa.objects.filter(usuario=usuario, orcamento_mensal__isnull=False):
        total = totais_por_categoria.get(cat.nome, Decimal('0'))
        orcamentos.append({
            'categoria': cat.nome,
            'cor': cat.cor,
            'total': float(total),
            'orcamento': float(cat.orcamento_mensal),
            'pct': float(total / cat.orcamento_mensal * 100) if cat.orcamento_mensal else 0,
        })
    orcamentos.sort(key=lambda o: o['pct'], reverse=True)

    return {
        'patrimonio_total': float(valor_atual_total),
        'valor_investido_total': float(valor_investido_total),
        'divida_total': float(divida_total),
        'divida_emprestimos': float(divida_emprestimos),
        'divida_cartoes': float(divida_cartoes),
        'patrimonio_liquido': float(patrimonio_liquido),
        'ganho_perda_total_pct': ganho_perda_total_pct,
        'proventos_mes': float(proventos_mes),
        'proventos_total': float(proventos_total),
        'retorno_total_pct': retorno_total_pct,
        'alocacao': alocacao,
        'alocacao_alvo': alocacao_alvo,
        'receita_mes_atual': float(receita_mes_atual),
        'despesa_mes_atual': float(despesa_mes_atual),
        'saldo_mes_atual': float(saldo_mes_atual),
        'variacao_receita_pct': variacao_receita_pct,
        'variacao_despesa_pct': variacao_despesa_pct,
        'pct_gasto_da_renda': pct_gasto_da_renda,
        'gastos_por_categoria': gastos_por_categoria,
        'orcamentos': orcamentos,
        'evolucao_labels': evolucao_labels,
        'evolucao_receitas': evolucao_receitas,
        'evolucao_despesas': evolucao_despesas,
        'evolucao_saldo': evolucao_saldo,
        'tem_ativos': bool(alocacao),
        'patrimonio_historico_labels': patrimonio_historico_labels,
        'patrimonio_historico_valores': patrimonio_historico_valores,
        'data_inicio_investimentos': data_inicio_investimentos,
        'retorno_mercado_pct': retorno_mercado_pct,
        'variacao_cdi_pct': variacao_cdi_pct,
        'comparacao_ibovespa': comparacao_ibovespa,
        'comparacao_labels': comparacao_labels,
        'comparacao_valores': comparacao_valores,
    }
