# -*- coding: utf-8 -*-
"""Reglas de negocio: saldos, stock, cantidades de OT, talonarios y timbrados."""
import io
from datetime import date, timedelta
from decimal import Decimal

from django.core.management import call_command

from cobros.models import DetalleDeRecibo, Recibo
from depositos.models import Alta, Baja, DetalleAlta, DetalleBaja
from empresas.models import Talonario, Timbrado
from materiales.models import Material
from produccion.models import OrdenDeTrabajo
from sistema.tests.base import ConDatosDemo
from ventas.models import DetalleDeRemision, Remision, Venta


class DatosDemoConsistentesTest(ConDatosDemo):

    def test_saldo_de_facturas_es_total_menos_cobrado(self):
        for v in Venta.objects.all():
            if v.condicion == 'CO':
                self.assertEqual(v.saldo, 0, v)
            else:
                self.assertEqual(v.saldo, v.total - v.get_pagado() - v.get_total_notas_de_credito(), v)

    def test_no_hay_stock_negativo(self):
        self.assertFalse(Material.objects.filter(stock_actual__lt=0).exists())

    def test_cantidades_de_ot_cuadran(self):
        for ot in OrdenDeTrabajo.objects.all():
            self.assertEqual(ot.entregado + ot.restante, ot.cantidad, ot.id)
            self.assertEqual(ot.cantidad_facturada + ot.cantidad_no_facturada, ot.cantidad, ot.id)


class SaldosTest(ConDatosDemo):

    def test_recibo_descuenta_saldo_y_anularlo_lo_devuelve(self):
        venta = Venta.objects.filter(condicion='CR', saldo__gt=0).first()
        saldo = venta.saldo
        talonario = Talonario.objects.get(tipo_de_talonario=2)
        recibo = Recibo.objects.create(talonario=talonario, numero='9999999', cliente=venta.cliente, monto=100)
        DetalleDeRecibo.objects.create(recibo=recibo, factura=venta, monto=Decimal('100'))
        venta.refresh_from_db()
        self.assertEqual(venta.saldo, saldo - 100)

        recibo.estado = 2  # anulado
        recibo.save()
        venta.save()
        venta.refresh_from_db()
        self.assertEqual(venta.saldo, saldo)

    def test_recalcular_saldos_repara_datos_desfasados(self):
        venta = Venta.objects.filter(condicion='CR').first()
        ot = OrdenDeTrabajo.objects.filter(entregado__gt=0).first()
        correctos = (venta.saldo, venta.pagado, ot.entregado, ot.restante)
        Venta.objects.filter(pk=venta.pk).update(saldo=123, pagado=0)
        OrdenDeTrabajo.objects.filter(pk=ot.pk).update(entregado=0, restante=ot.cantidad)

        call_command('recalcular_saldos', stdout=io.StringIO())
        venta.refresh_from_db()
        ot.refresh_from_db()
        self.assertEqual((venta.saldo, venta.pagado, ot.entregado, ot.restante), correctos)


class StockTest(ConDatosDemo):

    def test_altas_y_bajas_actualizan_el_stock(self):
        material = Material.objects.first()
        stock = material.stock_actual
        deposito = Alta.objects.first().deposito
        alta = Alta.objects.create(deposito=deposito)
        DetalleAlta.objects.create(alta=alta, material=material, cantidad=Decimal('50'))
        material.refresh_from_db()
        self.assertEqual(material.stock_actual, stock + 50)

        baja = Baja.objects.create(deposito=deposito)
        detalle = DetalleBaja.objects.create(baja=baja, material=material, cantidad=Decimal('20'))
        material.refresh_from_db()
        self.assertEqual(material.stock_actual, stock + 30)

        detalle.delete()
        material.refresh_from_db()
        self.assertEqual(material.stock_actual, stock + 50)


class OrdenDeTrabajoTest(ConDatosDemo):

    def test_remision_actualiza_entregado_y_anularla_lo_revierte(self):
        ot = OrdenDeTrabajo.objects.filter(restante__gt=0, anulada=False, cambios=False).first()
        remision = Remision.objects.filter(cliente=ot.cliente).first()
        restante = ot.restante
        DetalleDeRemision.objects.create(remision=remision, orden_de_trabajo=ot, descripcion='x', cantidad=Decimal('1'))
        ot.actualizar_cantidades()
        self.assertEqual(ot.restante, restante - 1)

        # Anular la remisión: sus entregas dejan de contar
        Remision.objects.filter(pk=remision.pk).update(estado='A')
        ot.actualizar_cantidades()
        self.assertEqual(ot.restante, ot.cantidad - sum(
            d.cantidad for d in DetalleDeRemision.objects.filter(orden_de_trabajo=ot).exclude(remision__estado='A')))
        self.assertGreater(ot.restante, restante - 1)


class TalonariosYTimbradosTest(ConDatosDemo):

    def test_numeracion_del_talonario_y_agotado(self):
        t = Talonario.objects.get(tipo_de_talonario=0)
        usado = t.ultimo_usado
        self.assertEqual(t.get_siguiente(), usado + 1)
        t.set_siguiente()
        self.assertEqual(t.ultimo_usado, usado + 1)
        self.assertFalse(t.agotado)
        t.numero_final = t.ultimo_usado
        t.save()
        self.assertTrue(t.agotado)

    def test_vencer_timbrados_solo_desactiva_los_vencidos(self):
        vigente = Timbrado.objects.get(activo=True)
        vencido = Timbrado.objects.create(numero='99999999', empresa=vigente.empresa, activo=True,
                                          fecha_de_inicio=date.today() - timedelta(days=400),
                                          fecha_de_vencimiento=date.today() - timedelta(days=1))
        call_command('vencer_timbrados', stdout=io.StringIO())
        vencido.refresh_from_db()
        vigente.refresh_from_db()
        self.assertFalse(vencido.activo)
        self.assertTrue(vigente.activo)
