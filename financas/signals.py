"""Categorias padrão pra usuário novo — sem isso, quem acaba de se cadastrar
não consegue lançar despesa (categoria é FK obrigatória) até criar uma na
mão. Mesmos nomes/cores do seed original do app."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CategoriaDespesa

CATEGORIAS_PADRAO = [
    ('Alimentação', '#fd7e14'),
    ('Educação', '#0dcaf0'),
    ('Lazer', '#20c997'),
    ('Moradia', '#0d6efd'),
    ('Outros', '#6c757d'),
    ('Saúde', '#dc3545'),
    ('Transporte', '#6f42c1'),
]


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_categorias_padrao(sender, instance, created, **kwargs):
    if not created:
        return
    CategoriaDespesa.objects.bulk_create([
        CategoriaDespesa(usuario=instance, nome=nome, cor=cor)
        for nome, cor in CATEGORIAS_PADRAO
    ])
