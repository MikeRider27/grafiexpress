# -*- coding: utf-8 -*-
"""Base común de los tests: base cargada con los datos de demostración."""
import io
import re

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.urlresolvers import RegexURLResolver, get_resolver
from django.test import Client, TestCase

CLAVE = 'Clave-de-test-1'


class ConDatosDemo(TestCase):
    """Carga una vez por clase los datos de cargar_datos_demo y los roles."""

    @classmethod
    def setUpTestData(cls):
        call_command('cargar_datos_demo', stdout=io.StringIO())
        call_command('crear_roles', stdout=io.StringIO())
        cls.admin = User.objects.create_superuser('admin_test', 'a@test.py', CLAVE)

    def cliente_como(self, usuario):
        c = Client(HTTP_HOST='localhost')
        self.assertTrue(c.login(username=usuario.username, password=CLAVE))
        return c

    def usuario_con_rol(self, rol):
        u = User.objects.create_user('rol_%s' % re.sub(r'\W', '', rol.lower()), 'r@test.py', CLAVE)
        u.is_staff = True
        u.save()
        u.groups.add(Group.objects.get(name=rol))
        return u


def rutas_propias(con_parametros=True):
    """
    URLs de las vistas propias del sistema (no las del admin de Django), con
    los parámetros numéricos reemplazados por 1. Excluye las que modifican datos.
    """
    urls = set()

    def recorrer(patrones, prefijo):
        for p in patrones:
            rx = p.regex.pattern.lstrip('^').rstrip('$')
            if isinstance(p, RegexURLResolver):
                if p.namespace == 'admin' or 'admin.site' in repr(p.urlconf_name):
                    continue
                recorrer(p.url_patterns, prefijo + rx)
                continue
            url = prefijo + rx
            if '(?P' in url and not con_parametros:
                continue
            url = re.sub(r'\(\?P<[^>]+>[^)]*\)', '1', url).replace('\\', '')
            if '(' in url or re.search(r'delete|cancel|revert', url):
                continue
            urls.add('/' + url)

    recorrer(get_resolver(None).url_patterns, '')
    return sorted(urls)
