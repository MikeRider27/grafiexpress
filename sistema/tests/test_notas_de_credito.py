# -*- coding: utf-8 -*-
"""Notas de crédito: alta desde el admin, validaciones, saldo, impresión y anulación."""
from decimal import Decimal

from empresas.models import Talonario
from sistema.tests.base import ConDatosDemo
from ventas.models import NotaDeCredito, Venta


class NotasDeCreditoTest(ConDatosDemo):

    def setUp(self):
        self.c = self.cliente_como(self.admin)
        self.talonario = Talonario.objects.get(tipo_de_talonario=3)
        self.credito = Venta.objects.filter(condicion='CR', saldo__gt=0).exclude(estado='A').order_by('-id').first()

    def emitir(self, venta, montos, cliente=None, **extra):
        datos = {
            'talonario': self.talonario.pk, 'fecha_de_emision': venta.fecha_de_emision.strftime('%d/%m/%Y'),
            'cliente': (cliente or venta.cliente).pk, 'venta': venta.pk, 'motivo': 'DEV', 'observaciones': '',
            'detallenotadecredito_set-TOTAL_FORMS': str(len(montos)),
            'detallenotadecredito_set-INITIAL_FORMS': '0',
            'detallenotadecredito_set-MIN_NUM_FORMS': '0',
            'detallenotadecredito_set-MAX_NUM_FORMS': '1000',
        }
        for i, monto in enumerate(montos):
            datos.update({'detallenotadecredito_set-%d-descripcion' % i: 'Item %d' % i,
                          'detallenotadecredito_set-%d-iva' % i: '10',
                          'detallenotadecredito_set-%d-cantidad' % i: '1',
                          'detallenotadecredito_set-%d-precio_unitario' % i: str(monto)})
        datos.update(extra)
        return self.c.post('/admin/ventas/notadecredito/add/', datos)

    def test_emitir_descuenta_saldo_y_numera_del_talonario(self):
        saldo = self.credito.saldo
        siguiente = self.talonario.get_siguiente()
        r = self.emitir(self.credito, [1000, 500])
        self.assertEqual(r.status_code, 302, r.content[:3000])

        nota = NotaDeCredito.objects.latest('id')
        self.assertEqual(nota.numero, '%07d' % siguiente)
        self.assertEqual(nota.timbrado, self.talonario.timbrado.numero)
        self.assertEqual(nota.total, Decimal('1500'))
        self.assertTrue(nota.afecta_saldo)
        self.credito.refresh_from_db()
        self.assertEqual(self.credito.saldo, saldo - 1500)
        self.talonario.refresh_from_db()
        self.assertEqual(self.talonario.ultimo_usado, siguiente)

    def test_no_puede_superar_el_saldo_pendiente(self):
        r = self.emitir(self.credito, [self.credito.saldo + 1])
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'supera el saldo pendiente')
        self.assertFalse(NotaDeCredito.objects.filter(venta=self.credito, total__gt=self.credito.saldo).exists())

    def test_factura_de_otro_cliente_o_anulada_se_rechaza(self):
        otro = Venta.objects.exclude(cliente=self.credito.cliente).first().cliente
        r = self.emitir(self.credito, [100], cliente=otro)
        self.assertContains(r, 'La factura no es de este cliente')

        anulada = Venta.objects.exclude(pk=self.credito.pk).filter(condicion='CR').first()
        Venta.objects.filter(pk=anulada.pk).update(estado='A')
        r = self.emitir(Venta.objects.get(pk=anulada.pk), [100])
        self.assertEqual(r.status_code, 200)
        self.assertFalse(NotaDeCredito.objects.filter(venta=anulada).exclude(total=0).filter(estado='P').exists())

    def test_sin_detalles_se_rechaza(self):
        r = self.emitir(self.credito, [])
        self.assertContains(r, 'al menos un detalle')

    def test_factura_contado_no_modifica_saldo_pero_respeta_el_total(self):
        contado = Venta.objects.filter(condicion='CO').exclude(estado='A').order_by('-id').first()
        self.assertEqual(self.emitir(contado, [100]).status_code, 302)
        contado.refresh_from_db()
        self.assertEqual(contado.saldo, 0)
        self.assertFalse(NotaDeCredito.objects.latest('id').afecta_saldo)

        r = self.emitir(contado, [contado.total])  # con la anterior supera el total
        self.assertContains(r, 'supera el total de la factura')

    def test_imprimir_anular_y_pdf(self):
        saldo = self.credito.saldo
        self.emitir(self.credito, [2000])
        nota = NotaDeCredito.objects.latest('id')

        self.c.post('/admin/ventas/notadecredito/%d/print/' % nota.pk)
        nota.refresh_from_db()
        self.assertEqual(nota.estado, 'C')
        # impresa: ya no se modifica, abrirla muestra el documento
        r = self.c.get('/admin/ventas/notadecredito/%d/' % nota.pk)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r['Location'].endswith('/admin/ventas/notadecredito/%d/pdf/' % nota.pk))

        r = self.c.get('/admin/ventas/notadecredito/%d/grafiexpress_report/' % nota.pk)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))

        self.c.post('/admin/ventas/notadecredito/%d/cancel/' % nota.pk)
        nota.refresh_from_db()
        self.credito.refresh_from_db()
        self.assertEqual(nota.estado, 'A')
        self.assertEqual(self.credito.saldo, saldo)  # la factura recupera el saldo

    def test_permisos(self):
        comercial = self.cliente_como(self.usuario_con_rol('Comercial'))
        self.assertEqual(comercial.get('/admin/ventas/notadecredito/').status_code, 403)
        facturacion = self.cliente_como(self.usuario_con_rol('Facturación'))
        self.assertEqual(facturacion.get('/admin/ventas/notadecredito/').status_code, 200)
        self.assertEqual(facturacion.get('/admin/ventas/notadecredito/add/').status_code, 200)
