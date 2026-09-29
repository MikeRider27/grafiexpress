# -*- coding: utf-8 -*-
"""Descarga protegida de /media/ y validación de archivos subidos."""
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings

from extra.validators import validar_archivo_subido
from sistema.tests.base import CLAVE, ConDatosDemo


class MediaProtegidaTest(ConDatosDemo):

    def setUp(self):
        self.ruta = os.path.join(settings.MEDIA_ROOT, 'prueba_test_sec.txt')
        with open(self.ruta, 'w') as f:
            f.write('CONFIDENCIAL')

    def tearDown(self):
        if os.path.exists(self.ruta):
            os.remove(self.ruta)

    def test_anonimo_no_descarga_media(self):
        r = Client(HTTP_HOST='localhost').get('/media/prueba_test_sec.txt')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/admin/login/', r['Location'])

    @override_settings()
    def test_con_sesion_descarga_via_x_accel(self):
        os.environ['USAR_X_ACCEL'] = 'True'
        c = self.cliente_como(self.admin)
        r = c.get('/media/prueba_test_sec.txt')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['X-Accel-Redirect'], '/_media_protegido/prueba_test_sec.txt')

    def test_no_permite_salir_de_media(self):
        c = self.cliente_como(self.admin)
        self.assertEqual(c.get('/media/../settings.py').status_code, 404)
        self.assertEqual(c.get('/media/no_existe.pdf').status_code, 404)


class ValidacionArchivosTest(ConDatosDemo):

    def test_rechaza_ejecutables_y_html(self):
        for nombre in ['maldad.html', 'x.svg', 'shell.php', 'a.js', 'sin_extension']:
            with self.assertRaises(ValidationError, msg=nombre):
                validar_archivo_subido(SimpleUploadedFile(nombre, b'x'))

    def test_acepta_documentos(self):
        for nombre in ['recibo.pdf', 'foto.png', 'planilla.xlsx', 'nota.txt']:
            validar_archivo_subido(SimpleUploadedFile(nombre, b'x'))  # no lanza
