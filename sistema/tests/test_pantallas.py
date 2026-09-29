# -*- coding: utf-8 -*-
"""Todas las pantallas cargan (sin errores 500) con datos cargados."""
import re

from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import Group

from sistema.tests.base import ConDatosDemo, rutas_propias

APPS_DEL_SISTEMA = ['funcionarios', 'clientes', 'materiales', 'maquinaria', 'produccion', 'proveedores',
                    'compras', 'ventas', 'empresas', 'ciudades', 'depositos', 'automoviles', 'bancos',
                    'cheques', 'cobros', 'pagos', 'comercial']

# Respuestas esperadas que no son 200/302: factura/remisión ya impresas no se editan
PERMITIDAS = {403: re.compile(r'^/admin/ventas/(venta|ventaantiguo|remision|remisionantiguo)/\d+/$')}

# Endpoints AJAX que exigen parámetros, PDF que dependen de Jasper y rutas internas
NO_PROBAR = re.compile(r'autocomplete|/get|ajax|grafiexpress_report|gesa_report|^/chaining/')


class PantallasTest(ConDatosDemo):

    def setUp(self):
        self.c = self.cliente_como(self.admin)

    def assertCarga(self, url, acepta_404=False):
        r = self.c.get(url)
        esperado = r.status_code in (200, 302) or (acepta_404 and r.status_code == 404) or (
            r.status_code in PERMITIDAS and PERMITIDAS[r.status_code].match(url))
        self.assertTrue(esperado, '%s -> %s' % (url, r.status_code))
        return r

    def test_listados_altas_y_edicion_del_admin(self):
        for model in admin.site._registry:
            base = '/admin/%s/%s/' % (model._meta.app_label, model._meta.model_name)
            self.assertCarga(base)
            self.assertCarga(base + 'add/')
            obj = model.objects.order_by('pk').first()
            if obj is not None:
                self.assertCarga('%s%s/' % (base, obj.pk))

    def test_vistas_propias_y_reportes(self):
        # Los parámetros se reemplazan por 1, que puede no existir: 404 es
        # válido, lo que no puede haber es un error 500.
        for url in rutas_propias():
            if not NO_PROBAR.search(url):
                self.assertCarga(url, acepta_404=True)

    def test_registro_inexistente_da_404_y_no_500(self):
        for url in ['/admin/ventas/venta/999999/grafiexpress_report/', '/admin/ventas/remision/999999/gesa_report/',
                    '/admin/compras/ordendecompra/999999/print/', '/admin/cobros/recibo/999999/print/',
                    '/admin/depositos/retiro/999999/detail/']:
            self.assertEqual(self.c.get(url).status_code, 404, url)

    def test_pdf_propios_generan_pdf(self):
        from compras.models import OrdenDeCompra
        from cobros.models import PresentacionCobros
        from depositos.models import Retiro
        from produccion.models import OrdenDeTrabajo
        for url in ['/admin/compras/ordendecompra/%d/print/' % OrdenDeCompra.objects.first().pk,
                    '/admin/depositos/retiro/%d/print/' % Retiro.objects.first().pk,
                    '/admin/produccion/ordendetrabajo/%d/print/' % OrdenDeTrabajo.objects.first().pk,
                    '/admin/cobros/generar_rendicion/%d/' % PresentacionCobros.objects.first().pk]:
            r = self.assertCarga(url)
            self.assertEqual(r['Content-Type'], 'application/pdf', url)

    def test_detalle_de_movimientos_de_deposito(self):
        from depositos.models import Alta, Baja, Devolucion, Retiro
        for tipo, modelo in [('alta', Alta), ('baja', Baja), ('retiro', Retiro), ('devolucion', Devolucion)]:
            r = self.assertCarga('/admin/depositos/%s/%d/detail/' % (tipo, modelo.objects.first().pk))
            self.assertContains(r, 'Materiales')


class MenuPorRolTest(ConDatosDemo):
    """Cada rol recorre todo lo que se le muestra sin toparse con accesos bloqueados."""

    OMITIR = re.compile(r'delete|cancel|revert|anular|logout|print|report|export|excel|xls|generar|'
                        r'/media/|/static/|autocomplete|/get')

    def recorrer(self, c):
        vistos, cola, claves, bloqueados = set(), ['/admin/'], {'/admin/'}, []
        while cola and len(vistos) < 400:
            url = cola.pop(0)
            if url in vistos:
                continue
            vistos.add(url)
            r = c.get(url)
            if r.status_code >= 400:
                bloqueados.append((url, r.status_code))
                continue
            if r.status_code != 200 or 'html' not in r.get('Content-Type', ''):
                continue
            html = re.sub(r'<!--.*?-->', '', r.content.decode('utf-8', 'replace'), flags=re.S)
            for h in re.findall(r"""(?:href=|location\.href=)["']([^"'{}]+)["']""", html):
                h = re.sub(r'[?#].*', '', h)
                if not h.startswith('/') or self.OMITIR.search(h):
                    continue
                h = h if h.endswith('/') else h + '/'
                clave = re.sub(r'/\d+/', '/N/', h)
                if clave not in claves:
                    claves.add(clave)
                    cola.append(h)
        return vistos, [b for b in bloqueados
                        if not (b[1] in PERMITIDAS and PERMITIDAS[b[1]].match(b[0]))]

    def test_ningun_rol_ve_enlaces_que_no_puede_usar(self):
        for grupo in Group.objects.all():
            vistos, bloqueados = self.recorrer(self.cliente_como(self.usuario_con_rol(grupo.name)))
            self.assertGreater(len(vistos), 3, grupo.name)
            self.assertEqual(bloqueados, [], grupo.name)


class RepresentacionTest(ConDatosDemo):

    def test_modelos_principales_no_se_muestran_como_object(self):
        genericos = []
        for app in APPS_DEL_SISTEMA:
            for model in apps.get_app_config(app).get_models():
                if model._meta.model_name.startswith(('detalle', 'ventaremision', 'cantidad', 'materialpresupuesto',
                                                      'insumoordendecompra')):
                    continue  # líneas de detalle: nunca tuvieron nombre propio
                obj = model.objects.first()
                if obj is not None and str(obj).endswith(' object'):
                    genericos.append(model.__name__)
        self.assertEqual(genericos, [])
