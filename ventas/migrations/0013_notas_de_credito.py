# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0007_cliente_activo'),
        ('empresas', '0005_auto_20170403_1525'),
        ('ventas', '0012_auto_20190930_0018'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetalleNotaDeCredito',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descripcion', models.CharField(max_length=200)),
                ('iva', models.IntegerField(default=10, choices=[(10, 'IVA 10%'), (5, 'IVA 5%'), (0, 'EXCENTA')])),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=15)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=15)),
                ('subtotal', models.DecimalField(editable=False, decimal_places=2, max_digits=15)),
            ],
            options={
                'verbose_name_plural': 'Detalles',
                'verbose_name': 'Detalle',
            },
        ),
        migrations.CreateModel(
            name='NotaDeCredito',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('codigo_de_establecimiento', models.CharField(editable=False, max_length=3)),
                ('punto_de_expedicion', models.CharField(editable=False, max_length=3)),
                ('numero', models.CharField(editable=False, max_length=10)),
                ('timbrado', models.CharField(editable=False, max_length=10)),
                ('fecha_de_emision', models.DateField(default=datetime.date.today)),
                ('motivo', models.CharField(default='DEV', max_length=3, choices=[('DEV', 'Devolución de mercaderías'), ('DES', 'Descuento'), ('BON', 'Bonificación'), ('AJU', 'Ajuste de precio'), ('OTR', 'Otro')])),
                ('observaciones', models.CharField(blank=True, max_length=300, default='')),
                ('total', models.DecimalField(editable=False, default=0, decimal_places=2, max_digits=15)),
                ('afecta_saldo', models.BooleanField(editable=False, help_text='Descuenta del saldo pendiente de la factura', default=False)),
                ('estado', models.CharField(editable=False, default='P', max_length=1, choices=[('P', 'SIN IMPRIMIR'), ('C', 'IMPRESO'), ('A', 'ANULADO')])),
                ('cliente', models.ForeignKey(to='clientes.Cliente')),
                ('empresa', models.ForeignKey(editable=False, to='empresas.Empresa')),
                ('sucursal', models.ForeignKey(editable=False, to='empresas.Sucursal', null=True)),
                ('talonario', models.ForeignKey(to='empresas.Talonario')),
            ],
            options={
                'verbose_name_plural': 'Notas de crédito',
                'verbose_name': 'Nota de crédito',
                'permissions': (('print_notadecredito', 'Puede imprimir una nota de crédito'), ('cancel_notadecredito', 'Puede anular una nota de crédito')),
            },
        ),
        migrations.AddField(
            model_name='notadecredito',
            name='venta',
            field=models.ForeignKey(verbose_name='factura', to='ventas.Venta'),
        ),
        migrations.AddField(
            model_name='detallenotadecredito',
            name='nota_de_credito',
            field=models.ForeignKey(to='ventas.NotaDeCredito'),
        ),
        migrations.AlterUniqueTogether(
            name='notadecredito',
            unique_together=set([('codigo_de_establecimiento', 'punto_de_expedicion', 'numero', 'timbrado')]),
        ),
    ]
