from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from financas.models import Despesa, Receita
from investimentos import services
from investimentos.models import Ativo, PatrimonioSnapshot

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


@login_required
def dashboard(request):
    # --- Carteira de investimentos ---
    ativos = Ativo.objects.filter(ativo_flag=True)
    tickers = [a.ticker for a in ativos if a.tipo in TIPOS_COTADOS_B3]
    cripto_ids = [a.coingecko_id for a in ativos if a.tipo == Ativo.Tipo.CRIPTO and a.coingecko_id]

    cotacoes_acoes = services.get_cotacoes_acoes(tickers)
    cotacoes_cripto = services.get_cotacoes_cripto(cripto_ids)

    alocacao = []
    valor_investido_total = Decimal('0')
    valor_atual_total = Decimal('0')

    for ativo in ativos:
        # Ação/FII/Cripto sem nenhuma transação lançada ainda (posição
        # zerada) não fazem sentido na pizza/tabela do dashboard — mas
        # continuam normalmente em /investimentos/ pra lançar a 1ª compra.
        if ativo.tipo != Ativo.Tipo.RENDA_FIXA and not ativo.quantidade:
            continue

        valor_investido = ativo.valor_investido

        if ativo.tipo in TIPOS_COTADOS_B3:
            info = cotacoes_acoes.get(ativo.ticker, {})
            preco = info.get('preco')
            cotacao_disponivel = preco is not None
            # sem cotação disponível (API fora do ar), usa o preço médio de
            # compra como fallback só pra não zerar o card de patrimônio
            preco_decimal = Decimal(str(preco)) if cotacao_disponivel else ativo.preco_medio_compra
            valor_atual = ativo.quantidade * preco_decimal
            quantidade_exibicao = float(ativo.quantidade)
            preco_exibicao = float(preco_decimal)

        elif ativo.tipo == Ativo.Tipo.CRIPTO:
            info = cotacoes_cripto.get(ativo.coingecko_id, {})
            preco = info.get('preco')
            cotacao_disponivel = preco is not None
            preco_decimal = Decimal(str(preco)) if cotacao_disponivel else ativo.preco_medio_compra
            valor_atual = ativo.quantidade * preco_decimal
            quantidade_exibicao = float(ativo.quantidade)
            preco_exibicao = float(preco_decimal)

        else:  # RENDA_FIXA — sem cotação de mercado, valor estimado via taxa do BCB
            valor_calculado = services.calcular_valor_atual_renda_fixa(ativo)
            cotacao_disponivel = valor_calculado is not None
            valor_atual = valor_calculado if cotacao_disponivel else ativo.valor_aplicado
            quantidade_exibicao = None
            preco_exibicao = None

        valor_atual_total += valor_atual
        valor_investido_total += valor_investido

        alocacao.append({
            'ticker': ativo.ticker,
            'tipo': ativo.get_tipo_display(),
            'quantidade': quantidade_exibicao,
            'preco_atual': preco_exibicao,
            'valor_atual': float(valor_atual),
            'valor_investido': float(valor_investido),
            'ganho_perda_pct': _variacao_pct(valor_atual, valor_investido) or 0,
            'cotacao_disponivel': cotacao_disponivel,
        })

    ganho_perda_total_pct = _variacao_pct(valor_atual_total, valor_investido_total) or 0

    # --- Renda e despesas do mês ---
    hoje = timezone.now().date()

    # --- Snapshot diário de patrimônio (alimenta o gráfico histórico) ---
    # update_or_create por data: reabrir o dashboard no mesmo dia só
    # atualiza o snapshot de hoje, nunca duplica.
    PatrimonioSnapshot.objects.update_or_create(
        data=hoje,
        defaults={
            'valor_total': valor_atual_total,
            'valor_investido_total': valor_investido_total,
        },
    )
    snapshots = PatrimonioSnapshot.objects.order_by('data')
    patrimonio_historico_labels = [s.data.strftime('%d/%m/%y') for s in snapshots]
    patrimonio_historico_valores = [float(s.valor_total) for s in snapshots]

    ano_atual, mes_atual = hoje.year, hoje.month
    ano_anterior, mes_anterior = _meses_recentes(2, referencia=hoje.replace(day=1))[0]

    def total_mes(model, ano, mes):
        return model.objects.filter(data__year=ano, data__month=mes).aggregate(t=Sum('valor'))['t'] or Decimal('0')

    receita_mes_atual = total_mes(Receita, ano_atual, mes_atual)
    despesa_mes_atual = total_mes(Despesa, ano_atual, mes_atual)
    receita_mes_anterior = total_mes(Receita, ano_anterior, mes_anterior)
    despesa_mes_anterior = total_mes(Despesa, ano_anterior, mes_anterior)

    saldo_mes_atual = receita_mes_atual - despesa_mes_atual
    variacao_receita_pct = _variacao_pct(receita_mes_atual, receita_mes_anterior)
    variacao_despesa_pct = _variacao_pct(despesa_mes_atual, despesa_mes_anterior)
    pct_gasto_da_renda = float(despesa_mes_atual / receita_mes_atual * 100) if receita_mes_atual else None

    # --- Gastos por categoria (mês atual) — pizza 2 ---
    gastos_por_categoria = list(
        Despesa.objects.filter(data__year=ano_atual, data__month=mes_atual)
        .values('categoria__nome', 'categoria__cor')
        .annotate(total=Sum('valor'))
        .order_by('-total')
    )

    # --- Evolução mensal (últimos 12 meses) ---
    meses = _meses_recentes(12, referencia=hoje.replace(day=1))

    receitas_por_mes = {
        (d['mes'].year, d['mes'].month): d['total']
        for d in Receita.objects.annotate(mes=TruncMonth('data')).values('mes').annotate(total=Sum('valor'))
    }
    despesas_por_mes = {
        (d['mes'].year, d['mes'].month): d['total']
        for d in Despesa.objects.annotate(mes=TruncMonth('data')).values('mes').annotate(total=Sum('valor'))
    }

    evolucao_labels = [f'{MESES_PT[m]}/{str(a)[2:]}' for a, m in meses]
    evolucao_receitas = [float(receitas_por_mes.get(chave, 0)) for chave in meses]
    evolucao_despesas = [float(despesas_por_mes.get(chave, 0)) for chave in meses]
    evolucao_saldo = [r - d for r, d in zip(evolucao_receitas, evolucao_despesas)]

    context = {
        'patrimonio_total': float(valor_atual_total),
        'valor_investido_total': float(valor_investido_total),
        'ganho_perda_total_pct': ganho_perda_total_pct,
        'alocacao': alocacao,
        'receita_mes_atual': float(receita_mes_atual),
        'despesa_mes_atual': float(despesa_mes_atual),
        'saldo_mes_atual': float(saldo_mes_atual),
        'variacao_receita_pct': variacao_receita_pct,
        'variacao_despesa_pct': variacao_despesa_pct,
        'pct_gasto_da_renda': pct_gasto_da_renda,
        'gastos_por_categoria': gastos_por_categoria,
        'evolucao_labels': evolucao_labels,
        'evolucao_receitas': evolucao_receitas,
        'evolucao_despesas': evolucao_despesas,
        'evolucao_saldo': evolucao_saldo,
        'tem_ativos': bool(alocacao),
        'patrimonio_historico_labels': patrimonio_historico_labels,
        'patrimonio_historico_valores': patrimonio_historico_valores,
    }
    return render(request, 'core/dashboard.html', context)
