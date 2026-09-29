# -*- coding: utf-8 -*-
"""
Crea los grupos (roles) de usuario con sus permisos por módulo.

    python manage.py crear_roles               # crea los que no existen
    python manage.py crear_roles --actualizar  # además redefine los existentes

Django 1.8 no tiene permiso de "solo ver": el menú muestra un módulo si el
usuario tiene cualquier permiso de esa app. Por eso cada rol recibe
agregar/modificar (y los permisos especiales que se indiquen) en sus módulos,
pero NO borrar; borrar queda solo para el Administrador.

Para asignar un rol: Sistema > Usuarios > (usuario) > Grupos.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

APPS_DEL_SISTEMA = ['sistema', 'funcionarios', 'clientes', 'materiales', 'maquinaria', 'produccion',
                    'proveedores', 'compras', 'ventas', 'empresas', 'ciudades', 'depositos', 'automoviles',
                    'bancos', 'cheques', 'cobros', 'pagos', 'comercial']

# rol: (apps con agregar/modificar, permisos especiales "app.codename", descripción)
ROLES = {
    'Administrador': (
        None, [], 'Acceso total, incluida la gestión de usuarios y el borrado de registros.'),
    'Comercial': (
        ['clientes', 'comercial', 'ciudades'],
        ['produccion.add_ordendetrabajo', 'produccion.change_ordendetrabajo',
         'produccion.add_detalleordendetrabajo', 'produccion.change_detalleordendetrabajo',
         'produccion.add_archivoordendetrabajo', 'produccion.change_archivoordendetrabajo'],
        'Vendedores: clientes, presupuestos, agenda y carga de sus propias órdenes de trabajo.'),
    'Facturación': (
        ['ventas', 'clientes'],
        ['ventas.print_venta', 'ventas.cancel_venta', 'ventas.print_remision', 'ventas.cancel_remision',
         'ventas.view_venta', 'ventas.view_remision', 'produccion.view_all_ots',
         'automoviles.change_automovil', 'empresas.change_talonario'],
        'Emisión e impresión de facturas y notas de remisión.'),
    'Cobranzas': (
        ['cobros', 'cheques', 'bancos'],
        ['cobros.print_recibo', 'cobros.cancel_recibo', 'clientes.change_cliente'],
        'Recibos, cheques recibidos, rendiciones y estado de cuenta de clientes.'),
    'Compras y pagos': (
        ['proveedores', 'compras', 'pagos', 'cheques', 'bancos'],
        [],
        'Órdenes de compra, facturas de proveedores, pagos y cheques emitidos.'),
    'Producción': (
        ['produccion', 'maquinaria'],
        ['produccion.view_all_ots', 'produccion.view_fecha_solicitada', 'produccion.set_vendedor_ot',
         'materiales.change_material'],
        'Órdenes de trabajo de todos los vendedores, costos, procesos y programación de máquinas.'),
    'Depósito': (
        ['depositos', 'materiales'],
        ['produccion.view_all_ots'],
        'Stock, altas, bajas, retiros y devoluciones de materiales.'),
    'Gerencia': (
        APPS_DEL_SISTEMA,
        ['produccion.view_all_ots', 'produccion.view_fecha_solicitada', 'produccion.save_limite_credito',
         'produccion.set_vendedor_ot', 'ventas.view_venta', 'ventas.view_remision'],
        'Todos los módulos (sin borrar ni gestionar usuarios).'),
}


def permisos_de_apps(apps):
    """agregar/modificar + permisos propios (imprimir, anular...) de las apps; nunca borrar."""
    return Permission.objects.filter(content_type__app_label__in=apps).exclude(codename__startswith='delete_')


def permisos_puntuales(nombres):
    permisos = []
    for nombre in nombres:
        app, codename = nombre.split('.')
        permisos.append(Permission.objects.get(content_type__app_label=app, codename=codename))
    return permisos


class Command(BaseCommand):
    help = 'Crea los grupos de usuario (roles) con sus permisos por módulo.'

    def add_arguments(self, parser):
        parser.add_argument('--actualizar', action='store_true',
                            help='Redefinir también los permisos de los grupos que ya existen.')

    @transaction.atomic
    def handle(self, *args, **options):
        for nombre, (apps, extras, descripcion) in ROLES.items():
            grupo, creado = Group.objects.get_or_create(name=nombre)
            if not creado and not options['actualizar']:
                self.stdout.write('  = %s (ya existía, no se modifica)' % nombre)
                continue

            if apps is None:
                permisos = list(Permission.objects.filter(
                    content_type__app_label__in=APPS_DEL_SISTEMA + ['auth']))
            else:
                permisos = list(permisos_de_apps(apps)) + permisos_puntuales(extras)
            grupo.permissions = set(permisos)
            self.stdout.write('  %s %s: %d permisos. %s'
                              % ('+' if creado else '~', nombre, len(set(permisos)), descripcion))
        self.stdout.write('Roles listos. Asignalos en Sistema > Usuarios.')
