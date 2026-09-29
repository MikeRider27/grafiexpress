# -*- coding: utf-8 -*-
"""
Exige usuario logueado (activo y staff, igual que el admin de Django) en
todas las vistas propias del sistema.

Las vistas de cada app están montadas bajo /admin/<app>/ pero son vistas
comunes (ListView, DetailView, AJAX, PDF...) y la mayoría no tenía ningún
control de acceso: se podían ver listados, estados de cuenta o descargar
facturas sin iniciar sesión.
"""
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden

PREFIJOS_PROTEGIDOS = ('/admin/', '/chaining/')

# Rutas del admin que tienen que funcionar sin sesión
RUTAS_PUBLICAS = (
    '/admin/login/',
    '/admin/logout/',
    '/admin/password_reset/',
    '/admin/reset/',
    '/admin/jsi18n/',
)


class RequiereLoginMiddleware(object):

    def process_request(self, request):
        path = request.path if request.path.endswith('/') else request.path + '/'
        if not path.startswith(PREFIJOS_PROTEGIDOS) or path.startswith(RUTAS_PUBLICAS):
            return None

        user = request.user
        if user.is_authenticated() and user.is_active and user.is_staff:
            return None

        # Pedidos AJAX / autocompletados: 403 en vez de una redirección a HTML
        if request.is_ajax() or 'autocomplete' in path or '/get' in path:
            return HttpResponseForbidden('Sesión requerida')

        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
