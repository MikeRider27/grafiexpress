# -*- coding: utf-8 -*-
"""
Desactiva los timbrados vencidos (fecha_de_vencimiento <= hoy).
Lo ejecuta el servicio "tareas" todos los días; reemplaza al CRONJOB de
django_crontab (empresas.cron.set_vencimiento_timbrado), que en Docker no corría.
"""
from datetime import date

from django.core.management.base import BaseCommand

from empresas.models import Timbrado


class Command(BaseCommand):
    help = 'Desactiva los timbrados cuya fecha de vencimiento ya pasó.'

    def handle(self, *args, **options):
        vencidos = Timbrado.objects.filter(fecha_de_vencimiento__lte=date.today(), activo=True)
        numeros = list(vencidos.values_list('numero', flat=True))
        for timbrado in vencidos:
            timbrado.activo = False
            timbrado.save()
        self.stdout.write('Timbrados desactivados: %d %s' % (len(numeros), ', '.join(numeros)))
