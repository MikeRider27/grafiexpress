# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import smart_selects.db_fields
import extra.validators
import produccion.models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0027_auto_20190930_0018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archivoordendetrabajo',
            name='archivo',
            field=models.FileField(validators=[extra.validators.validar_archivo_subido], upload_to=produccion.models.get_file_path),
        ),
    ]
