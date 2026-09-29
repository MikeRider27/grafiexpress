# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import comercial.models
import datetime
import extra.validators


class Migration(migrations.Migration):

    dependencies = [
        ('comercial', '0010_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actividad',
            name='documentos',
            field=models.FileField(validators=[extra.validators.validar_archivo_subido], upload_to=comercial.models.get_file_path, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='presupuesto',
            name='adjunto',
            field=models.FileField(validators=[extra.validators.validar_archivo_subido], upload_to=comercial.models.get_file_path, null=True, blank=True),
        ),
    ]
