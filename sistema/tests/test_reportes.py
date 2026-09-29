# -*- coding: utf-8 -*-
"""Facturas/remisiones en PDF vía el servicio Jasper (simulado)."""
import io
import urllib.error
import urllib.parse
from unittest import mock

from common.jasper import conector
from sistema.tests.base import ConDatosDemo
from ventas.models import Remision, Venta


class RespuestaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ReportesJasperTest(ConDatosDemo):

    def setUp(self):
        self.c = self.cliente_como(self.admin)

    def test_factura_envia_parametros_y_devuelve_el_pdf(self):
        with mock.patch('urllib.request.urlopen', return_value=RespuestaFalsa(b'%PDF-falso')) as urlopen:
            venta = Venta.objects.filter(remision__isnull=False).first()
            r = self.c.get('/admin/ventas/venta/%d/grafiexpress_report/' % venta.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertEqual(r.content, b'%PDF-falso')

        pedido = urlopen.call_args[0][0]
        self.assertTrue(pedido.full_url.endswith('/report/factura_triplicado.jasper'))
        params = dict(urllib.parse.parse_qsl(pedido.data.decode()))
        self.assertEqual(params['id'], str(venta.pk))
        self.assertIn('001-001-', params['remisiones'])   # la remisión vinculada a la factura

    def test_remision(self):
        with mock.patch('urllib.request.urlopen', return_value=RespuestaFalsa(b'%PDF-rem')) as urlopen:
            r = self.c.get('/admin/ventas/remision/%d/gesa_report/' % Remision.objects.first().pk)
        self.assertEqual(r.content, b'%PDF-rem')
        self.assertTrue(urlopen.call_args[0][0].full_url.endswith('/report/remision_triplicado.jasper'))

    def test_servicio_caido_da_error_claro(self):
        with mock.patch('urllib.request.urlopen', side_effect=urllib.error.URLError('Connection refused')):
            with self.assertRaisesRegex(conector.JasperError, 'No se pudo conectar'):
                conector.generar_pdf('factura_triplicado.jasper', {'id': 1})
