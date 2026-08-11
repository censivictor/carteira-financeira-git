from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class CategoriaDespesa(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=50)
    cor = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text='Cor hex usada na legenda do gráfico de pizza (ex: #6c757d).',
    )
    orcamento_mensal = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        help_text='Limite de gasto mensal nessa categoria, em R$. Deixe em branco pra não definir orçamento.',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        unique_together = ('usuario', 'nome')
        verbose_name = 'Categoria de despesa'
        verbose_name_plural = 'Categorias de despesa'

    def __str__(self):
        return self.nome


class DespesaRecorrente(models.Model):
    """Uma despesa fixa que se repete todo mês (aluguel, assinaturas...).

    Não gera as `Despesa`s diretamente — quem faz isso é
    `financas.services.gerar_despesas_recorrentes_do_mes`, chamado a cada
    carregamento do dashboard (sem cron/Celery no projeto).
    """

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recorrentes')
    categoria = models.ForeignKey(CategoriaDespesa, on_delete=models.PROTECT, related_name='recorrentes')
    descricao = models.CharField(max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    dia_do_mes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Dia do mês em que a despesa é lançada (ex: 5). Meses mais curtos usam o último dia disponível.',
    )
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dia_do_mes', 'descricao']
        verbose_name = 'Despesa recorrente'
        verbose_name_plural = 'Despesas recorrentes'

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor} (dia {self.dia_do_mes})'


class Despesa(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='despesas')
    categoria = models.ForeignKey(
        CategoriaDespesa, on_delete=models.PROTECT, related_name='despesas'
    )
    descricao = models.CharField(max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField(default=timezone.now)
    recorrente = models.ForeignKey(
        DespesaRecorrente, on_delete=models.SET_NULL, null=True, blank=True, related_name='despesas_geradas',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-criado_em']
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor}'


class Receita(models.Model):
    class Tipo(models.TextChoices):
        SALARIO = 'SALARIO', 'Salário'
        FREELA = 'FREELA', 'Freelance'
        RENDIMENTO = 'RENDIMENTO', 'Rendimento'
        OUTRO = 'OUTRO', 'Outro'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receitas')
    descricao = models.CharField(max_length=150)
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.SALARIO)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField(default=timezone.now)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-criado_em']
        verbose_name = 'Receita'
        verbose_name_plural = 'Receitas'

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor}'
