from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def atribuir_usuario_existente(apps, schema_editor):
    """Dados anteriores à separação por usuário viram todos do usuário
    'victor' (o único usuário do app até aqui) — ou o primeiro usuário
    existente, se por algum motivo esse username não existir."""
    User = apps.get_model('auth', 'User')
    CategoriaDespesa = apps.get_model('financas', 'CategoriaDespesa')
    Despesa = apps.get_model('financas', 'Despesa')
    DespesaRecorrente = apps.get_model('financas', 'DespesaRecorrente')
    Receita = apps.get_model('financas', 'Receita')

    usuario = User.objects.filter(username='victor').first() or User.objects.order_by('id').first()
    if usuario is None:
        return

    CategoriaDespesa.objects.filter(usuario__isnull=True).update(usuario=usuario)
    Despesa.objects.filter(usuario__isnull=True).update(usuario=usuario)
    DespesaRecorrente.objects.filter(usuario__isnull=True).update(usuario=usuario)
    Receita.objects.filter(usuario__isnull=True).update(usuario=usuario)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('financas', '0002_categoriadespesa_orcamento_mensal_despesarecorrente_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='categoriadespesa',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='categoriadespesa',
            name='nome',
            field=models.CharField(max_length=50),
        ),
        migrations.AddField(
            model_name='categoriadespesa',
            name='usuario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categorias', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='despesa',
            name='usuario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='despesas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='despesarecorrente',
            name='usuario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recorrentes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='receita',
            name='usuario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receitas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(atribuir_usuario_existente, noop),
        migrations.AlterField(
            model_name='categoriadespesa',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categorias', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='despesa',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='despesas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='despesarecorrente',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recorrentes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='receita',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receitas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='categoriadespesa',
            unique_together={('usuario', 'nome')},
        ),
    ]
