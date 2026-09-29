# -*- coding: utf-8 -*-
"""
Carga datos FALSOS de demostración en todos los módulos del sistema, para
probar pantallas, listados, saldos y reportes sin usar datos reales.

    python manage.py cargar_datos_demo            # falla si ya hay clientes cargados
    python manage.py cargar_datos_demo --forzar   # carga igual (suma datos)

Los registros se crean con los mismos save()/actualizar_*() que usa el admin,
así que stock, saldos de facturas/compras y cantidades de las OT quedan
consistentes. La generación es determinística (semilla fija).
"""
import os
import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from automoviles.models import Automovil
from bancos.models import Banco, CuentaBancaria
from cheques.models import ChequeEmitido, ChequeRecibido
from ciudades.models import Ciudad
from clientes.models import Cliente, Contacto, Marca
from cobros.models import DetalleDeRecibo, DetalleDeRecibo2, DetallePresentacion, PresentacionCobros, Recibo
from comercial.models import Actividad, CantidadPresupuesto, Canal, MaterialPresupuesto, Presupuesto
from compras.models import Compra, DetalleCompra, InsumoOrdenDeCompra, OrdenDeCompra
from depositos.models import (Alta, Baja, Deposito, DetalleAlta, DetalleBaja, DetalleDevolucion, DetalleRetiro,
                               Devolucion, Retiro)
from empresas.models import Empresa, Sucursal, Talonario, Timbrado
from funcionarios.models import Funcionario
from maquinaria.models import Maquina as MaquinaCosto
from materiales.models import CategoriaDeMaterial, Gramaje, Material, Resma, UnidadDeMedida
from pagos.models import DetalleDePago, DetalleDePago2, Pago
from produccion.models import (CategoriaDeTrabajo, Costo, DetalleOrdenDeTrabajo, DetalleProceso, Maquina,
                               OrdenDeTrabajo, PapelCosto, PreprensaCosto, Proceso, SubcategoriaDeTrabajo)
from proveedores.models import Proveedor
from ventas.models import DetalleDeRemision, DetalleDeVenta, Remision, Venta, VentaRemision

HOY = date.today()
D = Decimal

CIUDADES = ['Asunción', 'San Lorenzo', 'Luque', 'Fernando de la Mora', 'Lambaré', 'Capiatá',
            'Mariano Roque Alonso', 'Ciudad del Este', 'Encarnación', 'Villarrica']

CLIENTES = [
    ('Alimentos del Sur S.A.', 'Alisur'), ('Farmacéutica Guaraní S.R.L.', 'FarmaGuaraní'),
    ('Cervecería Río Paraná S.A.', 'Río Paraná'), ('Supermercados La Estrella S.A.', 'La Estrella'),
    ('Colegio San Martín', 'San Martín'), ('Lácteos Ybytyruzú S.A.', 'Ybytyruzú'),
    ('Yerbatera Tres Fronteras S.A.', 'Tres Fronteras'), ('Constructora Mbareté S.R.L.', 'Mbareté'),
    ('Clínica Santa Clara S.A.', 'Santa Clara'), ('Editorial Ñandutí', 'Ñandutí'),
    ('Café Tostado Chaco S.A.', 'Café Chaco'), ('Automotores del Este S.A.', 'AutoEste'),
    ('Universidad Tecnológica del Paraguay', 'UTP'), ('Panadería El Molino', 'El Molino'),
    ('Cosméticos Jazmín S.R.L.', 'Jazmín'),
]
NOMBRES = ['Ana', 'Carlos', 'María', 'José', 'Lucía', 'Diego', 'Sofía', 'Hugo', 'Laura', 'Pablo',
           'Rocío', 'Andrés', 'Gabriela', 'Rodrigo', 'Natalia', 'Óscar']
APELLIDOS = ['Benítez', 'González', 'Martínez', 'Giménez', 'Ramírez', 'Duarte', 'Acosta', 'Vera',
             'Ortiz', 'Cáceres', 'Villalba', 'Rojas', 'Sosa', 'Báez']

PROVEEDORES = ['Papelera Paraguaya S.A.', 'Tintas y Solventes S.R.L.', 'Importadora Gráfica del Plata',
               'Cartones del Paraná S.A.', 'Troqueles Asunción', 'Plastificados Express',
               'Distribuidora Offset S.A.', 'Insumos Industriales Capiatá']

# (descripción, unidad, categoría, costo, gramaje, resma)
MATERIALES = [
    ('Papel ilustración brillo', 'Hoja', 'Papel', 850, '150 g', '70x100'),
    ('Papel ilustración mate', 'Hoja', 'Papel', 820, '115 g', '70x100'),
    ('Papel obra', 'Hoja', 'Papel', 420, '80 g', '66x96'),
    ('Cartulina duplex', 'Hoja', 'Cartulina', 1900, '300 g', '70x100'),
    ('Cartulina triplex', 'Hoja', 'Cartulina', 2300, '350 g', '70x100'),
    ('Papel autoadhesivo', 'Hoja', 'Papel', 3100, None, '50x70'),
    ('Tinta cyan offset', 'Kilogramo', 'Tintas', 68000, None, None),
    ('Tinta magenta offset', 'Kilogramo', 'Tintas', 68000, None, None),
    ('Tinta amarilla offset', 'Kilogramo', 'Tintas', 64000, None, None),
    ('Tinta negra offset', 'Kilogramo', 'Tintas', 52000, None, None),
    ('Plancha CTP 745x605', 'Unidad', 'Preprensa', 45000, None, None),
    ('Film de plastificado brillo', 'Rollo', 'Terminación', 380000, None, None),
    ('Cola vinílica', 'Litro', 'Terminación', 21000, None, None),
    ('Caja corrugada para despacho', 'Unidad', 'Embalaje', 6500, None, None),
]

TRABAJOS = {
    'Packaging': ['Cajas plegadizas', 'Estuches', 'Bolsas'],
    'Editorial': ['Revistas', 'Libros', 'Catálogos'],
    'Comercial': ['Folletos', 'Tarjetas', 'Afiches', 'Talonarios'],
    'Etiquetas': ['Autoadhesivas', 'Colgantes'],
}
PRODUCTOS = ['Caja plegadiza {m}', 'Folleto promocional {m}', 'Etiqueta autoadhesiva {m}',
             'Catálogo anual {m}', 'Afiche campaña {m}', 'Estuche {m}', 'Revista institucional {m}',
             'Tarjetas personales {m}', 'Bolsa de papel {m}', 'Talonario de facturas {m}']


def dias_atras(n):
    return HOY - timedelta(days=n)


class Command(BaseCommand):
    help = 'Carga datos falsos de demostración en todos los módulos.'

    def add_arguments(self, parser):
        parser.add_argument('--forzar', action='store_true',
                            help='Cargar aunque ya existan clientes en la base.')

    def log(self, msg):
        self.stdout.write('  - ' + msg)

    def handle(self, *args, **options):
        if Cliente.objects.exists() and not options['forzar']:
            raise CommandError('La base ya tiene clientes. Usá --forzar para cargar igual.')

        random.seed(2024)
        self.stdout.write('Cargando datos de demostración...')
        with transaction.atomic():
            self.maestros()
            self.empresa()
            self.terceros()
            self.inventario()
            self.produccion()
            self.ventas()
            self.cobros()
            self.compras_y_pagos()
            self.comercial()
        self.stdout.write('Datos de demostración cargados.')

    # ------------------------------------------------------------------ maestros
    def maestros(self):
        self.ciudades = [Ciudad.objects.create(nombre=n) for n in CIUDADES]

        def funcionario(nombre, apellido, usuario=None):
            return Funcionario.objects.create(
                nombres=nombre, apellidos=apellido, ruc='%d-%d' % (random.randint(1000000, 5999999), random.randint(0, 9)),
                direccion='Calle %s %d' % (random.choice(APELLIDOS), random.randint(100, 3000)),
                email='%s.%s@grafiexpress.test' % (nombre.lower(), apellido.lower()),
                fecha_de_ingreso=dias_atras(random.randint(200, 2500)), usuario=usuario)

        # Usuarios de prueba (no superusuarios, rol Comercial) asociados a vendedores
        self.usuarios = []
        for nombre, apellido in [('Marta', 'Vera'), ('Julio', 'Ortiz')]:
            username = 'vendedor_' + nombre.lower()
            user = User.objects.filter(username=username).first() or User.objects.create_user(
                username, '%s@grafiexpress.test' % username, 'demo1234',
                first_name=nombre, last_name=apellido)
            user.is_staff = True
            user.save()
            call_command('crear_roles', stdout=open(os.devnull, 'w'))
            user.groups.add(Group.objects.get(name='Comercial'))
            self.usuarios.append(user)

        self.vendedores = [funcionario('Marta', 'Vera', self.usuarios[0]),
                           funcionario('Julio', 'Ortiz', self.usuarios[1]),
                           funcionario('Carla', 'Sosa')]
        self.chofer = funcionario('Ramón', 'Báez')
        self.cobrador = funcionario('Elena', 'Rojas')
        self.deposito_resp = funcionario('Víctor', 'Cáceres')

        self.bancos = [Banco.objects.create(nombre=n) for n in
                       ['Banco Continental', 'Banco Itaú', 'Banco Basa', 'Visión Banco', 'Banco GNB']]
        self.cuentas = [CuentaBancaria.objects.create(numero_de_cuenta='%010d' % random.randint(10 ** 8, 10 ** 10 - 1),
                                                      banco=b) for b in self.bancos[:3]]
        self.vehiculos = [Automovil.objects.create(marca='Toyota Hilux', rua='AAKX 482'),
                          Automovil.objects.create(marca='Hyundai HD65', rua='BCDF 915', rua_remolque='RMQ 120')]
        self.log('ciudades, funcionarios, bancos y vehículos')

    # ------------------------------------------------------------------ empresa
    def empresa(self):
        self.empresa = Empresa.objects.create(nombre='GRAFIEXPRESS', ruc='80012345-6',
                                              direccion='Av. Artigas 1234, Asunción',
                                              telefono='(021) 555-100', email='info@grafiexpress.test')
        self.sucursal = Sucursal.objects.create(empresa=self.empresa, nombre='Casa Matriz',
                                                direccion=self.empresa.direccion, telefono=self.empresa.telefono)
        self.timbrado = Timbrado.objects.create(numero='15482736', empresa=self.empresa, activo=True,
                                                fecha_de_inicio=dias_atras(200),
                                                fecha_de_vencimiento=HOY + timedelta(days=165))

        def talonario(nombre, tipo, inicial, final):
            return Talonario.objects.create(
                nombre=nombre, tipo_de_talonario=tipo, numero_inicial=inicial, numero_final=final,
                codigo_de_establecimiento='001', punto_de_expedicion='001', sucursal=self.sucursal,
                timbrado=self.timbrado, fecha_de_caducidad=self.timbrado.fecha_de_vencimiento, activo=True)

        self.tal_factura = talonario('Facturas 001-001', 0, 1, 5000)
        self.tal_remision = talonario('Remisiones 001-001', 1, 1, 5000)
        self.tal_recibo = talonario('Recibos', 2, 1, 5000)
        self.log('empresa, sucursal, timbrado y talonarios')

    # ------------------------------------------------------------------ clientes / proveedores
    def terceros(self):
        self.clientes = []
        for i, (razon, fantasia) in enumerate(CLIENTES):
            credito = i % 3 != 0
            cliente = Cliente.objects.create(
                razon_social=razon, nombre=fantasia, ruc='80%06d-%d' % (100000 + i * 731, i % 10),
                direccion='Av. %s %d' % (random.choice(APELLIDOS), random.randint(100, 5000)),
                telefono='(021) %03d-%03d' % (random.randint(200, 999), random.randint(0, 999)),
                email='compras@%s.test' % fantasia.lower().replace(' ', ''),
                vendedor=self.vendedores[i % len(self.vendedores)],
                condicion_de_venta='CR' if credito else 'CO',
                plazo_de_credito='30 días' if credito else None,
                limite_de_credito=D(random.choice([5, 10, 20, 50]) * 1000000) if credito else None,
                ciudad=random.choice(self.ciudades),
                requiere_orden_de_compra_del_proveedor=(i % 4 == 0),
                activo=(i != len(CLIENTES) - 1))
            cliente.marcas_demo = [Marca.objects.create(cliente=cliente, nombre='%s %s' % (fantasia, s))
                                   for s in random.sample(['Clásica', 'Premium', 'Light', 'Kids', 'Pro'], 2)]
            cliente.contactos_demo = [Contacto.objects.create(
                cliente=cliente, nombre=random.choice(NOMBRES), apellido=random.choice(APELLIDOS),
                telefono='09%02d %03d %03d' % (random.randint(71, 99), random.randint(0, 999), random.randint(0, 999)))
                for _ in range(2)]
            self.clientes.append(cliente)

        self.proveedores = []
        for i, razon in enumerate(PROVEEDORES):
            self.proveedores.append(Proveedor.objects.create(
                razon_social=razon, ruc='80%06d-%d' % (500000 + i * 977, (i * 3) % 10),
                direccion='Ruta %d km %d' % (random.randint(1, 3), random.randint(5, 30)),
                telefono='(021) %03d-%03d' % (random.randint(200, 999), random.randint(0, 999)),
                email='ventas@proveedor%d.test' % (i + 1),
                contacto='%s %s' % (random.choice(NOMBRES), random.choice(APELLIDOS)),
                condicion_de_compra='CR' if i % 2 == 0 else 'CO',
                plazo_de_credito='30 días' if i % 2 == 0 else 'Contado'))
        self.log('%d clientes (con marcas y contactos) y %d proveedores' % (len(self.clientes), len(self.proveedores)))

    # ------------------------------------------------------------------ materiales / depósitos
    def inventario(self):
        unidades, categorias, gramajes, resmas = {}, {}, {}, {}
        simbolos = {'Hoja': 'hj', 'Kilogramo': 'kg', 'Unidad': 'u', 'Rollo': 'rl', 'Litro': 'l'}
        self.materiales = []
        for i, (desc, unidad, cat, costo, gram, resma) in enumerate(MATERIALES):
            if unidad not in unidades:
                unidades[unidad] = UnidadDeMedida.objects.create(nombre=unidad, simbolo=simbolos[unidad])
            if cat not in categorias:
                categorias[cat] = CategoriaDeMaterial.objects.create(nombre=cat)
            if gram and gram not in gramajes:
                gramajes[gram] = Gramaje.objects.create(descripcion=gram)
            if resma and resma not in resmas:
                resmas[resma] = Resma.objects.create(descripcion=resma)
            self.materiales.append(Material.objects.create(
                descripcion=desc, codigo='MAT%03d' % (i + 1), unidad_de_medida=unidades[unidad],
                categoria=categorias[cat], costo_actual=D(costo), iva=10,
                gramaje=gramajes.get(gram), resma=resmas.get(resma), retiro_ot=True))
        self.unidad = unidades['Unidad']

        self.depositos = [Deposito.objects.create(nombre=n) for n in ['Depósito Central', 'Depósito Planta 2']]

        # Altas iniciales de stock (el stock se recalcula en DetalleAlta.save)
        for n, deposito in enumerate(self.depositos):
            alta = Alta.objects.create(deposito=deposito, fecha=dias_atras(120 - n), funcionario=self.deposito_resp)
            for material in self.materiales:
                cantidad = random.randint(4000, 9000) if material.unidad_de_medida.nombre == 'Hoja' else random.randint(10, 80)
                DetalleAlta.objects.create(alta=alta, material=material, cantidad=D(cantidad), motivo='Stock inicial')

        baja = Baja.objects.create(deposito=self.depositos[0], fecha=dias_atras(40), funcionario=self.deposito_resp)
        for material in random.sample(self.materiales[:6], 2):
            DetalleBaja.objects.create(baja=baja, material=material, cantidad=D(random.randint(5, 30)),
                                       motivo='Papel dañado por humedad')
        self.log('%d materiales, 2 depósitos, altas y bajas de stock' % len(self.materiales))

    # ------------------------------------------------------------------ producción
    def produccion(self):
        categorias = {}
        for cat, subs in TRABAJOS.items():
            c = CategoriaDeTrabajo.objects.create(nombre=cat)
            categorias[c] = [SubcategoriaDeTrabajo.objects.create(nombre=s, categoria=c) for s in subs]

        for nombre, precio in [('Heidelberg SM 74', 350000), ('Guillotina Polar 115', 80000),
                               ('Troqueladora Bobst', 220000), ('Plastificadora Komfi', 120000)]:
            MaquinaCosto.objects.create(descripcion=nombre, precio=D(precio))
        self.maquinas_costo = list(MaquinaCosto.objects.all())

        maquinas = [('Heidelberg SM 74', 'impresion', 5000), ('Heidelberg GTO 52', 'impresion', 3500),
                    ('Plastificadora Komfi', 'plastificado', 2500), ('Troqueladora Bobst', 'toquelado', 3000),
                    ('Guillotina Polar 115', 'terminacion', 4000), ('Encuadernación externa', 'tercerizado', 1000)]
        self.maquinas = {tipo: Maquina.objects.create(nombre=n, tipo=tipo, pasadas_por_hora=pph,
                                                      tercerizado=(tipo == 'tercerizado'),
                                                      fecha_disponible=dias_atras(90))
                         for n, tipo, pph in maquinas}

        papeles = [m for m in self.materiales if m.unidad_de_medida.nombre == 'Hoja']
        self.ots = []
        for i in range(30):
            cliente = self.clientes[i % len(self.clientes)]
            categoria = random.choice(list(categorias))
            marca = random.choice(cliente.marcas_demo)
            cantidad = random.choice([500, 1000, 2000, 3000, 5000, 10000])
            ingreso = dias_atras(110 - i * 3)
            ot = OrdenDeTrabajo.objects.create(
                nombre=random.choice(PRODUCTOS).format(m=marca.nombre), cliente=cliente, marca=marca,
                contacto=random.choice(cliente.contactos_demo), categoria=categoria,
                subcategoria=random.choice(categorias[categoria]),
                fecha_de_ingreso=ingreso, fecha_solicitada=ingreso + timedelta(days=random.randint(7, 20)),
                cantidad=D(cantidad), precio_unitario=D(random.choice([150, 350, 800, 1200, 2500, 4500])),
                vendedor=cliente.vendedor, originales=random.choice(['cliente', 'diseno']),
                repeticion=(i % 5 == 0), prueba_de_color=(i % 3 == 0),
                orden_de_compra_del_cliente=('OC-%05d' % (4000 + i)) if cliente.requiere_orden_de_compra_del_proveedor else None,
                comentarios='Trabajo de prueba generado automáticamente.',
                anulada=(i == 29))

            papel = random.choice(papeles)
            detalle = DetalleOrdenDeTrabajo.objects.create(
                orden_de_trabajo=ot, descripcion='Impresión 4/0 sobre %s' % papel.descripcion.lower(),
                cantidad=D(cantidad), material=papel, dimensiones_x=D(random.choice([10, 21, 30, 50])),
                dimensiones_y=D(random.choice([15, 29.7, 40, 70])), color_seleccion_frente='4', color_seleccion_dorso='0')

            # Costeo en la mitad de las OT
            if i % 2 == 0:
                costo = Costo.objects.create(detalle_orden_de_trabajo=detalle, vendedor=cliente.vendedor)
                pliegos = D(cantidad) / 4
                PapelCosto.objects.create(costo=costo, tipo=papel.descripcion, gramaje=str(papel.gramaje or ''),
                                          resma=str(papel.resma or ''), color='Blanco', cantidad=pliegos,
                                          precio_unitario=papel.costo_actual)
                PreprensaCosto.objects.create(costo=costo, maquina=self.maquinas_costo[0], cantidad=D(4),
                                              precio_unitario=D(45000))

            # Proceso productivo en las primeras 12 OT (crea la programación de máquinas)
            if i < 12:
                proceso = Proceso.objects.create(orden_de_trabajo=ot, pliegos=int(cantidad / 4),
                                                 fecha_de_creacion=ingreso,
                                                 fecha_de_entrega=ot.fecha_solicitada, urgente=(i % 4 == 0))
                inicio = ingreso + timedelta(days=2)
                for tipo in ['impresion', 'terminacion']:
                    DetalleProceso.objects.create(
                        proceso=proceso, tipo=tipo, maquina=self.maquinas[tipo], fecha_de_inicio=inicio,
                        hora_de_inicio=time(8, 0), fecha_de_finalizacion=inicio + timedelta(days=1),
                        hora_de_finalizacion=time(17, 0), pliegos_a_realizar=int(cantidad / 4),
                        estado='finalizado' if i < 8 else 'en_proceso')
                    inicio += timedelta(days=2)
                ot.actualizar_estado_produccion()

            self.ots.append(ot)

        # Retiros de material del depósito para OT
        for ot in self.ots[:10]:
            retiro = Retiro.objects.create(fecha=ot.fecha_de_ingreso + timedelta(days=1), funcionario=self.deposito_resp)
            detalle_ot = ot.detalleordendetrabajo_set.first()
            # Pliegos: 4 piezas por hoja, sin superar el stock disponible
            cantidad = min(detalle_ot.cantidad / 4, detalle_ot.material.stock_actual / 3).quantize(D('1'))
            DetalleRetiro.objects.create(retiro=retiro, orden_de_trabajo=ot, deposito=self.depositos[0],
                                         material=detalle_ot.material, cantidad=cantidad)
            detalle_ot.material.actualizar_stock()

        # Devolución parcial del sobrante de los dos primeros retiros
        for retiro in Retiro.objects.order_by('id')[:2]:
            devolucion = Devolucion.objects.create(fecha=retiro.fecha + timedelta(days=3), funcionario=self.deposito_resp,
                                                   retiro=retiro)
            for detalle in retiro.detalleretiro_set.all():
                DetalleDevolucion.objects.create(devolucion=devolucion, detalle_retiro=detalle,
                                                 cantidad=(detalle.cantidad / 10).quantize(D('1')), deposito=detalle.deposito)
                detalle.material.actualizar_stock()
        self.log('%d órdenes de trabajo, costeos, procesos productivos, retiros y devoluciones de material' % len(self.ots))

    # ------------------------------------------------------------------ remisiones / facturas
    def ventas(self):
        self.ventas_credito = []
        n_rem = n_fac = 0
        for i, ot in enumerate(self.ots[:22]):
            if ot.anulada:
                continue
            fecha = ot.fecha_solicitada
            parcial = (i % 6 == 5)
            entregar = (ot.cantidad / 2) if parcial else ot.cantidad

            # Remisión de entrega
            numero = self.tal_remision.get_siguiente()
            remision = Remision.objects.create(
                empresa=self.empresa, sucursal=self.sucursal, talonario=self.tal_remision,
                codigo_de_establecimiento='001', punto_de_expedicion='001', numero_de_remision='%07d' % numero,
                timbrado=self.timbrado.numero, fecha_de_emision=fecha, cliente=ot.cliente,
                motivo_del_traslado='Venta', fecha_de_inicio_del_traslado=fecha,
                fecha_estimada_de_termino_del_traslado=fecha,
                direccion_del_punto_de_partida=self.empresa.direccion, ciudad_de_partida='Asunción',
                direccion_del_punto_de_llegada=ot.cliente.direccion,
                ciudad_de_llegada=str(ot.cliente.ciudad.nombre), kilometros_estimados_de_recorrido=D(random.randint(5, 40)),
                vehiculo=random.choice(self.vehiculos), chofer=self.chofer, estado='C' if i < 18 else 'P')
            self.tal_remision.set_siguiente()
            DetalleDeRemision.objects.create(remision=remision, orden_de_trabajo=ot, descripcion=ot.nombre,
                                             cantidad=entregar, unidad_de_medida=self.unidad)
            ot.actualizar_cantidades()
            n_rem += 1

            # Factura (las primeras 18 OT entregadas)
            if i >= 18:
                continue
            credito = ot.cliente.condicion_de_venta == 'CR'
            subtotal = entregar * ot.precio_unitario
            numero = self.tal_factura.get_siguiente()
            venta = Venta.objects.create(
                cliente=ot.cliente, empresa=self.empresa, sucursal=self.sucursal, talonario=self.tal_factura,
                codigo_de_establecimiento='001', punto_de_expedicion='001', numero_de_factura='%07d' % numero,
                timbrado=self.timbrado.numero, condicion='CR' if credito else 'CO', fecha_de_emision=fecha,
                fecha_de_vencimiento=fecha + timedelta(days=30 if credito else 0), total=subtotal,
                estado='C' if i < 15 else 'P')
            self.tal_factura.set_siguiente()
            VentaRemision.objects.create(venta=venta, remision=remision)
            DetalleDeVenta.objects.create(venta=venta, orden_de_trabajo=ot, descripcion=ot.nombre, descripcion_extra='', iva=10,
                                          cantidad=entregar, precio_unitario=ot.precio_unitario, subtotal=subtotal)
            ot.actualizar_cantidades_facturadas()
            if credito:
                self.ventas_credito.append(venta)
            n_fac += 1
        self.log('%d remisiones y %d facturas (%d a crédito)' % (n_rem, n_fac, len(self.ventas_credito)))

    # ------------------------------------------------------------------ cobros
    def cobros(self):
        recibos = []
        # Se cobra ~2/3 de las facturas a crédito: algunas completas, otras parciales
        for i, venta in enumerate(self.ventas_credito):
            if i % 3 == 2:
                continue
            monto = venta.total if i % 3 == 0 else (venta.total / 2).quantize(D('1'))
            numero = self.tal_recibo.get_siguiente()
            recibo = Recibo.objects.create(talonario=self.tal_recibo, numero='%07d' % numero,
                                           fecha=venta.fecha_de_emision + timedelta(days=20),
                                           cliente=venta.cliente, monto=monto, estado=1)
            self.tal_recibo.set_siguiente()
            DetalleDeRecibo.objects.create(recibo=recibo, factura=venta, monto=monto)

            if i % 2 == 0:
                cheque = ChequeRecibido.objects.create(
                    numero='%08d' % random.randint(10 ** 7, 10 ** 8 - 1), banco=random.choice(self.bancos),
                    monto=monto, es_diferido=(i % 4 == 0), fecha_de_emision=recibo.fecha,
                    fecha_de_cobro=recibo.fecha + timedelta(days=30 if i % 4 == 0 else 0))
                DetalleDeRecibo2.objects.create(recibo=recibo, medio_de_pago=3, cheque=cheque, monto=monto)
            else:
                DetalleDeRecibo2.objects.create(recibo=recibo, medio_de_pago=1, cuenta_bancaria=random.choice(self.cuentas),
                                                numero_de_comprobante='TRF-%06d' % random.randint(0, 999999), monto=monto)
            recibos.append(recibo)

        # Rendición de los primeros recibos por el cobrador
        if recibos:
            presentacion = PresentacionCobros.objects.create(fecha=recibos[2].fecha, cobrador=self.cobrador)
            for recibo in recibos[:3]:
                DetallePresentacion.objects.create(presentacion=presentacion, cobro=recibo, subtotal=recibo.monto)
            presentacion.total = presentacion.get_total()
            presentacion.save()
        self.log('%d recibos de cobro (cheques y transferencias) y 1 rendición' % len(recibos))

    # ------------------------------------------------------------------ compras / pagos
    def compras_y_pagos(self):
        admin = User.objects.filter(is_superuser=True).first()
        insumos = self.materiales
        compras = []
        for i in range(10):
            proveedor = self.proveedores[i % len(self.proveedores)]
            fecha = dias_atras(100 - i * 9)
            oc = OrdenDeCompra.objects.create(
                fecha=fecha, proveedor=proveedor, contacto=proveedor.contacto, telefono=proveedor.telefono,
                forma_de_pago='Transferencia', condicion=proveedor.condicion_de_compra,
                departamento_solicitante='Producción', categoria_de_gastos='Insumos',
                responsable='Víctor Cáceres', creado_por=admin)
            items = random.sample(insumos, 2)
            total = D(0)
            for material in items:
                cantidad = D(random.randint(5, 50) if material.costo_actual > 10000 else random.randint(500, 3000))
                InsumoOrdenDeCompra.objects.create(orden_de_compra=oc, descripcion=material, cantidad=cantidad,
                                                   precio_unitario=material.costo_actual)
                total += cantidad * material.costo_actual

            if i < 8:  # 8 de las 10 OC ya tienen factura del proveedor
                compra = Compra.objects.create(
                    empresa=self.empresa, sucursal=self.sucursal, codigo_de_establecimiento='001',
                    punto_de_expedicion='%03d' % (i + 1), numero_de_factura='%07d' % random.randint(1000, 90000),
                    proveedor=proveedor, condicion=proveedor.condicion_de_compra, fecha=fecha + timedelta(days=3),
                    fecha_de_vencimiento=fecha + timedelta(days=33), total=total, creado_por=admin)
                compra.orden_de_compra.add(oc)
                for item in oc.insumoordendecompra_set.all():
                    DetalleCompra.objects.create(compra=compra, material=item.descripcion, cantidad=item.cantidad,
                                                 precio_unitario=item.precio_unitario,
                                                 subtotal=item.cantidad * item.precio_unitario)
                compras.append(compra)

        n_pagos = 0
        for i, compra in enumerate(compras[:6]):
            monto = compra.total if i % 2 == 0 else (compra.total / 2).quantize(D('1'))
            pago = Pago.objects.create(proveedor=compra.proveedor, fecha=compra.fecha + timedelta(days=25), monto=monto)
            DetalleDePago.objects.create(pago=pago, compra=compra, monto=monto)
            if i % 2 == 0:
                cheque = ChequeEmitido.objects.create(
                    numero='%08d' % random.randint(10 ** 7, 10 ** 8 - 1), banco=self.cuentas[0].banco, monto=monto,
                    fecha_de_emision=pago.fecha, fecha_de_cobro=pago.fecha + timedelta(days=15), es_diferido=True)
                DetalleDePago2.objects.create(pago=pago, medio_de_pago=3, cheque=cheque, monto=monto)
            else:
                DetalleDePago2.objects.create(pago=pago, medio_de_pago=1, cuenta_bancaria=self.cuentas[1],
                                              numero_de_comprobante='TRF-%06d' % random.randint(0, 999999), monto=monto)
            n_pagos += 1
        self.log('10 órdenes de compra, %d facturas de proveedores y %d pagos' % (len(compras), n_pagos))

    # ------------------------------------------------------------------ comercial
    def comercial(self):
        canales = [Canal.objects.create(nombre=n, activo=True) for n in
                   ['Visita', 'Llamada', 'WhatsApp', 'E-mail', 'Reunión virtual']]
        presupuestos = []
        for i, cliente in enumerate(self.clientes[:10]):
            p = Presupuesto.objects.create(
                cliente=cliente, contacto=cliente.contactos_demo[0], estado=['pen', 'pre', 'env'][i % 3],
                trabajo=random.choice(PRODUCTOS).format(m=cliente.nombre), dimensiones_x=D(21), dimensiones_y=D(29.7),
                color_seleccion_frente='4', color_seleccion_dorso=random.choice(['0', '1', '4']),
                terminacion='Corte recto', plastificado=(i % 2 == 0), troquelado=(i % 3 == 0),
                observaciones='Presupuesto de prueba.')
            for cantidad in [1000, 3000, 5000]:
                CantidadPresupuesto.objects.create(presupuesto=p, cantidad=cantidad)
            MaterialPresupuesto.objects.create(presupuesto=p, material='Ilustración 150 g', precio=D(850))
            presupuestos.append(p)

        for i in range(25):
            cliente = self.clientes[i % len(self.clientes)]
            realizado = i < 18
            Actividad.objects.create(
                cliente=cliente, contacto=random.choice(cliente.contactos_demo), marca=random.choice(cliente.marcas_demo),
                presupuesto=presupuestos[i % len(presupuestos)] if i % 2 == 0 and i < 20 else None,
                canal=random.choice(canales),
                fecha=dias_atras(60 - i * 3) if realizado else HOY + timedelta(days=i - 17),
                hora=time(9 + i % 8, 0), titulo=random.choice(['Seguimiento de presupuesto', 'Presentación de muestras',
                                                               'Reclamo de entrega', 'Visita comercial', 'Cobranza']),
                resumen='Actividad comercial de prueba con %s.' % cliente.nombre,
                realizado=realizado, vendedor=cliente.vendedor)
        self.log('%d presupuestos y 25 actividades comerciales' % len(presupuestos))
