# -*- coding: utf-8 -*-
"""Control de acceso: login obligatorio y permisos por módulo/rol."""
from django.contrib.auth.models import Group, User
from django.test import Client

from produccion.models import OrdenDeTrabajo
from funcionarios.models import Funcionario
from sistema.tests.base import CLAVE, ConDatosDemo, rutas_propias


class LoginObligatorioTest(ConDatosDemo):

    def test_ninguna_vista_propia_responde_sin_sesion(self):
        c = Client(HTTP_HOST='localhost')
        expuestas = []
        for url in rutas_propias():
            if url == '/':
                continue
            r = c.get(url)
            bloqueada = r.status_code == 403 or (r.status_code == 302 and '/admin/login/' in r['Location'])
            if not bloqueada:
                expuestas.append((url, r.status_code))
        self.assertEqual(expuestas, [], 'Rutas accesibles sin iniciar sesión')

    def test_alta_de_usuarios_sin_sesion_no_crea_nada(self):
        antes = User.objects.count()
        Client(HTTP_HOST='localhost').post('/admin/auth/user/add/', {
            'username': 'intruso', 'password1': 'Xx-123456789', 'password2': 'Xx-123456789'})
        self.assertEqual(User.objects.count(), antes)

    def test_login_y_paginas_publicas(self):
        c = Client(HTTP_HOST='localhost')
        self.assertEqual(c.get('/admin/login/').status_code, 200)
        self.assertEqual(c.get('/admin/login').status_code, 301)  # sin bucle de redirecciones

    def test_usuario_no_staff_no_entra(self):
        User.objects.create_user('no_staff', 'n@test.py', CLAVE)
        c = Client(HTTP_HOST='localhost')
        c.login(username='no_staff', password=CLAVE)
        self.assertEqual(c.get('/admin/ventas/venta/').status_code, 302)


class PermisosPorModuloTest(ConDatosDemo):

    def test_vendedor_no_abre_otros_modulos_escribiendo_la_url(self):
        c = self.cliente_como(self.usuario_con_rol('Comercial'))
        for url in ['/admin/ventas/venta/', '/admin/ventas/venta/1/grafiexpress_report/',
                    '/admin/cobros/estadodecuenta/1/detail/', '/admin/pagos/pago/',
                    '/admin/compras/compra/1/detail/', '/admin/auth/user/add/']:
            r = c.get(url)
            self.assertEqual(r.status_code, 403, url)
            self.assertContains(r, 'Acceso restringido', status_code=403)

    def test_vendedor_usa_sus_modulos_y_autocompletados(self):
        c = self.cliente_como(self.usuario_con_rol('Comercial'))
        for url in ['/admin/clientes/cliente/', '/admin/comercial/actividad/',
                    '/admin/produccion/ordendetrabajo/', '/admin/clientes/clienteautocomplete/']:
            self.assertEqual(c.get(url).status_code, 200, url)

    def test_stock_visible_desde_materiales(self):
        c = self.cliente_como(self.usuario_con_rol('Producción'))
        self.assertEqual(c.get('/admin/depositos/stock/').status_code, 200)

    def test_vendedor_no_ve_ots_de_otro_cambiando_el_parametro(self):
        marta = Funcionario.objects.get(usuario__username='vendedor_marta')
        julio = Funcionario.objects.get(usuario__username='vendedor_julio')
        usuario = marta.usuario
        usuario.set_password(CLAVE)
        usuario.save()
        c = self.cliente_como(usuario)
        r = c.get('/admin/produccion/ordendetrabajo/?vendedor_id=%d' % julio.id)
        ids = [int(i) for i in set(__import__('re').findall(r'/admin/produccion/ordendetrabajo/(\d+)/', r.content.decode()))]
        self.assertTrue(ids)
        self.assertEqual(set(OrdenDeTrabajo.objects.filter(id__in=ids).values_list('vendedor', flat=True)), {marta.id})


class RolesTest(ConDatosDemo):

    def test_se_crean_los_ocho_roles(self):
        self.assertEqual(set(Group.objects.values_list('name', flat=True)), {
            'Administrador', 'Gerencia', 'Comercial', 'Facturación', 'Cobranzas',
            'Compras y pagos', 'Producción', 'Depósito'})

    def test_solo_administrador_puede_borrar(self):
        for g in Group.objects.exclude(name='Administrador'):
            self.assertFalse(g.permissions.filter(codename__startswith='delete_').exists(), g.name)

    def test_no_pisa_grupos_existentes_sin_actualizar(self):
        import io
        from django.core.management import call_command
        g = Group.objects.get(name='Comercial')
        g.permissions.clear()
        call_command('crear_roles', stdout=io.StringIO())
        self.assertEqual(g.permissions.count(), 0)
        call_command('crear_roles', '--actualizar', stdout=io.StringIO())
        self.assertGreater(g.permissions.count(), 0)
