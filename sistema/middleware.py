# -*- coding: utf-8 -*-
"""
Exige usuario logueado (activo y staff, igual que el admin de Django) en
todas las vistas propias del sistema.

Las vistas de cada app están montadas bajo /admin/<app>/ pero son vistas
comunes (ListView, DetailView, AJAX, PDF...) y la mayoría no tenía ningún
control de acceso: se podían ver listados, estados de cuenta o descargar
facturas sin iniciar sesión.

Además, en esas vistas propias exige algún permiso sobre el módulo (mismo
criterio que el menú y la portada); las del admin de Django ya controlan
sus propios permisos.
"""
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import Resolver404, resolve
from django.http import HttpResponseForbidden
from django.shortcuts import render

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
        es_ajax = request.is_ajax() or 'autocomplete' in path or '/get' in path

        if not (user.is_authenticated() and user.is_active and user.is_staff):
            # Pedidos AJAX / autocompletados: 403 en vez de una redirección a HTML
            if es_ajax:
                return HttpResponseForbidden('Sesión requerida')
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

        # Autocompletados y consultas AJAX: los usan los formularios de otros
        # módulos (ej. buscar cliente al facturar), alcanza con estar logueado.
        if es_ajax or user.is_superuser:
            return None

        permiso = permiso_requerido(request.path_info)
        if permiso and not permiso(user):
            return render(request, '403.html', {'modulo': modulo_de(request.path_info)}, status=403)
        return None


# /admin/<segmento>/ -> app cuyos permisos habilitan ese módulo
MODULOS = {'auth': 'auth', 'sistema': 'auth'}

# Vistas propias que requieren un permiso puntual y no solo acceso al módulo
PERMISOS_PUNTUALES = {
    '/admin/auth/user/add/': 'auth.add_user',
}

# Vistas compartidas entre módulos: alcanza con permisos en cualquiera de ellos
# (el stock está bajo depósitos pero se enlaza también desde materiales)
MODULOS_COMPARTIDOS = {
    '/admin/depositos/stock/': ('depositos', 'materiales'),
}


def modulo_de(path):
    partes = path.strip('/').split('/')
    if len(partes) < 2 or partes[0] != 'admin':
        return None
    return MODULOS.get(partes[1], partes[1])


def permiso_requerido(path):
    """
    Para las vistas propias del sistema (ListView, DetailView, PDF... montadas
    bajo /admin/<app>/) devuelve la comprobación de permisos que corresponde:
    algún permiso sobre la app del módulo, como el menú. Las vistas del admin
    de Django (namespace "admin") ya controlan sus permisos: None.
    """
    try:
        match = resolve(path)
    except Resolver404:
        return None
    if match.namespace == 'admin':
        return None

    for prefijo, permiso in PERMISOS_PUNTUALES.items():
        if path.startswith(prefijo):
            return lambda user: user.has_perm(permiso)
    for prefijo, apps in MODULOS_COMPARTIDOS.items():
        if path.startswith(prefijo):
            return lambda user: any(user.has_module_perms(a) for a in apps)

    app = modulo_de(path)
    if not app:
        return None
    return lambda user: user.has_module_perms(app)
