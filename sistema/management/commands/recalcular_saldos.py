# -*- coding: utf-8 -*-
"""
Recalcula campos derivados que el sistema mantiene al guardar, por si
quedaron desfasados (datos migrados, ediciones directas en la base, etc.):

- Órdenes de trabajo: cantidades entregadas/restantes (según remisiones) y
  facturadas/no facturadas (según facturas).
- Facturas de venta: pagado y saldo (según recibos no anulados).

    python manage.py recalcular_saldos            # todo
    python manage.py recalcular_saldos --solo-ot
    python manage.py recalcular_saldos --solo-facturas

Reemplaza a los scripts sueltos fix_entregas_ot.py y set_ventas.py.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from produccion.models import OrdenDeTrabajo
from ventas.models import Venta


class Command(BaseCommand):
    help = 'Recalcula cantidades de las OT y saldos de las facturas de venta.'

    def add_arguments(self, parser):
        parser.add_argument('--solo-ot', action='store_true')
        parser.add_argument('--solo-facturas', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['solo_facturas']:
            n = 0
            for ot in OrdenDeTrabajo.objects.all().iterator():
                ot.actualizar_cantidades()
                ot.actualizar_cantidades_facturadas()
                n += 1
            self.stdout.write('Órdenes de trabajo recalculadas: %d' % n)

        if not options['solo_ot']:
            n = 0
            for venta in Venta.objects.all().iterator():
                # Venta.save() recalcula pagado/saldo (y fija saldo 0 en contado)
                venta.save()
                n += 1
            self.stdout.write('Facturas recalculadas: %d' % n)
