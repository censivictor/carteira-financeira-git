from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def atribuir_usuario_existente(apps, schema_editor):
    """Dados anteriores à separação por usuário viram todos do usuário
    'victor' (o único usuário do app até aqui) — ou o primeiro usuário
    existente, se por algum motivo esse username não existir."""
    User = apps.get_model('auth', 'User')
    Ativo = apps.get_model('investimentos', 'Ativo')
    PatrimonioSnapshot = apps.get_model('investimentos', 'PatrimonioSnapshot')

    usuario = User.objects.filter(username='victor').first() or User.objects.order_by('id').first()
    if usuario is None:
        return

    Ativo.objects.filter(usuario__isnull=True).update(usuario=usuario)
    PatrimonioSnapshot.objects.filter(usuario__isnull=True).update(usuario=usuario)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('investimentos', '0004_provento'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ativo',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='ativo',
            name='usuario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ativos', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patrimoniosnapshot',
            name='usuario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='patrimoniosnapshot',
            name='data',
            field=models.DateField(),
        ),
        migrations.RunPython(atribuir_usuario_existente, noop),
        migrations.AlterField(
            model_name='ativo',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ativos', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='patrimoniosnapshot',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='ativo',
            unique_together={('usuario', 'ticker', 'tipo')},
        ),
        migrations.AlterUniqueTogether(
            name='patrimoniosnapshot',
            unique_together={('usuario', 'data')},
        ),
    ]
