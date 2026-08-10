from django.db import models
from django.utils import timezone


class CategoriaDespesa(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    cor = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text='Cor hex usada na legenda do gráfico de pizza (ex: #6c757d).',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Categoria de despesa'
        verbose_name_plural = 'Categorias de despesa'

    def __str__(self):
        return self.nome


class Despesa(models.Model):
    categoria = models.ForeignKey(
        CategoriaDespesa, on_delete=models.PROTECT, related_name='despesas'
    )
    descricao = models.CharField(max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField(default=timezone.now)
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
