# -*- coding: utf-8 -*-
import datetime
from datetime import date, timedelta

from django.apps import apps
from django.db import models

from extra.validators import validar_archivo_subido
from django.db.models.aggregates import Sum
from django.views.generic.dates import timezone_today
from smart_selects.db_fields import ChainedForeignKey

from clientes.models import Cliente, Marca, Contacto
from compras.models import OrdenDeCompra, PapelOrdenDeCompra, PreprensaOrdenDeCompra, PosprensaServicioOrdenDeCompra, \
    PosprensaMaterialOrdenDeCompra, PosprensaOtroServicioOrdenDeCompra, DatosDeBolsaOrdenDeCompra, RevistaOrdenDeCompra, \
    CompuestoOrdenDeCompra, PlastificadoOrdenDeCompra, OtroGastoOrdenDeCompra
from materiales.models import Material
from extra.globals import separador_de_miles
from produccion.constants import TipoProceso, EstadoProceso


class CategoriaDeTrabajo(models.Model):
    class Meta:
        verbose_name = "categoría de trabajos"
        verbose_name_plural = "categorías de trabajos"

    nombre = models.CharField(max_length=100)

    def __str__(self):
        return str(self.nombre)


class SubcategoriaDeTrabajo(models.Model):
    class Meta:
        verbose_name = "subcategoría de trabajos"
        verbose_name_plural = "subcategorías de trabajos"

    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(CategoriaDeTrabajo, verbose_name="categoría")

    def __str__(self):
        return str(self.nombre)


ORIGINALES = (
    ("cliente", 'Cliente'),
    ("diseno", 'Diseño'),
)


class OrdenDeTrabajo(models.Model):
    class Meta:
        verbose_name = "orden de trabajo"
        verbose_name_plural = "órdenes de trabajo"

        permissions = [
            ('view_all_ots', 'Ver Todas las OTs'),
            ('view_fecha_solicitada', 'Ver el campo Fecha Solicitada de la OT'),
            ('set_vendedor_ot', 'Puede cambiar el vendedor de una OT'),
            ('save_limite_credito', 'Puede guardar OT con limite de credito superado'),
        ]

    nombre = models.CharField(max_length=200, verbose_name="descripcion")
    presupuesto_numero = models.CharField(max_length=10, blank=True, null=True, verbose_name="número de presupuesto")
    presupuesto_item = models.CharField(max_length=10, blank=True, null=True, verbose_name="ítem")
    cliente = models.ForeignKey('clientes.Cliente')
    marca = ChainedForeignKey(Marca, chained_field="cliente", chained_model_field="cliente", auto_choose=True,
                              blank=True, null=True)
    contacto = ChainedForeignKey(Contacto, chained_field="cliente", chained_model_field="cliente", auto_choose=True,
                                 blank=True, null=True)
    fecha_de_ingreso = models.DateField(default=date.today)
    fecha_solicitada = models.DateField(null=True, blank=True)
    comentarios = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(CategoriaDeTrabajo, verbose_name="categoría")
    subcategoria = ChainedForeignKey(SubcategoriaDeTrabajo, chained_field="categoria", chained_model_field="categoria",
                                     auto_choose=True, blank=True, null=True, verbose_name="subcategoría")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    cambios = models.BooleanField(default=False)
    materiales_compuestos = models.BooleanField(default=False)
    originales = models.CharField(max_length=10, choices=ORIGINALES, default="cliente")
    prueba_de_color = models.BooleanField(default=False)
    muestra_de_color = models.BooleanField(default=False)
    prueba_de_producto = models.BooleanField(default=False)
    muestra_de_producto = models.BooleanField(default=False)
    repeticion = models.BooleanField(default=False, verbose_name="repetición")
    buscar_sobrante = models.BooleanField(default=False)
    estado = models.CharField(max_length=10, default="PENDIENTE", editable=False)

    vendedor = models.ForeignKey("funcionarios.Funcionario", null=True, blank=True)
    orden_de_compra_del_cliente = models.CharField(max_length=10, null=True, blank=True)

    entregado = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    restante = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)

    cantidad_facturada = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    cantidad_no_facturada = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)

    prueba_realizada = models.BooleanField(default=False, editable=False)

    anulada = models.BooleanField(default=False, editable=False)

    estado_produccion = models.CharField(max_length=12, choices=EstadoProceso.ESTADOS,
                                         default=EstadoProceso.NO_INICIADO)

    def __str__(self):
        return str("[" + str(self.id) + "] " + self.nombre)

    def get_total(self):
        return self.cantidad * self.precio_unitario

    def get_estado(self):
        detalles_todos = DetalleOrdenDeTrabajo.objects.filter(orden_de_trabajo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.detalle_orden_de_trabajo_id for i in Costo.objects.filter(estado='PROCESADO')])

        if detalles_procesados.count() != detalles_todos.count():
            return 'PENDIENTE'

        return 'PROCESADO'

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.entregado = 0
            self.restante = self.cantidad
            self.cantidad_facturada = 0
            self.cantidad_no_facturada = self.cantidad

        super(OrdenDeTrabajo, self).save(*args, **kwargs)

    def get_entregado_display(self):
        if self.entregado == 0:
            return "NO ENTEGADO"

        if self.restante == 0:
            return "ENTREGADO TOTALMENTE"

        return "ENTREGADO PARCIALMENTE"

    def actualizar_cantidades(self):
        if not self.cambios:
            detalles_remision = apps.get_model("ventas", "DetalleDeRemision").objects.filter(
                orden_de_trabajo_id=self.id).exclude(remision__estado='A')

            entregado = 0
            for detalle in detalles_remision:
                entregado = entregado + detalle.cantidad

            self.entregado = entregado
            self.restante = self.cantidad - entregado

        else:
            # actualizar cantidades de los detalles
            detalles_orden_de_trabajo = DetalleOrdenDeTrabajo.objects.filter(orden_de_trabajo_id=self.id)
            for detalle_orden_de_trabajo in detalles_orden_de_trabajo:

                detalles_remision = apps.get_model("ventas", "DetalleDeRemision2").objects.filter(
                    detalle_orden_de_trabajo_id=detalle_orden_de_trabajo.id).exclude(remision__estado='A')

                entregado = 0
                for detalle_remision in detalles_remision:
                    entregado = entregado + detalle_remision.cantidad

                detalle_orden_de_trabajo.entregado = entregado
                detalle_orden_de_trabajo.restante = detalle_orden_de_trabajo.cantidad - entregado

                detalle_orden_de_trabajo.save()

            # actualizar cantidades de la cabecera
            entregado = 0
            for detalle_orden_de_trabajo in detalles_orden_de_trabajo:
                entregado = entregado + detalle_orden_de_trabajo.entregado
            self.entregado = entregado
            self.restante = self.cantidad - entregado

        self.save()

    def actualizar_cantidades_facturadas(self):
        if not self.cambios:
            detalles_venta = apps.get_model("ventas", "DetalleDeVenta").objects.filter(
                orden_de_trabajo_id=self.id).exclude(venta__estado='A')
            cantidad_facturada = 0
            for detalle in detalles_venta:
                cantidad_facturada = cantidad_facturada + detalle.cantidad

            self.cantidad_facturada = cantidad_facturada
            self.cantidad_no_facturada = self.cantidad - cantidad_facturada

        else:
            detalles_orden_de_trabajo = DetalleOrdenDeTrabajo.objects.filter(orden_de_trabajo_id=self.id)
            for detalle_orden_de_trabajo in detalles_orden_de_trabajo:
                detalles_venta = apps.get_model("ventas", "DetalleDeVenta2").objects.filter(
                    detalle_orden_de_trabajo_id=detalle_orden_de_trabajo.id).exclude(venta__estado='A')
                cantidad_facturada = 0
                for detalle_venta in detalles_venta:
                    cantidad_facturada = cantidad_facturada + detalle_venta.cantidad

                detalle_orden_de_trabajo.cantidad_facturada = cantidad_facturada
                detalle_orden_de_trabajo.cantidad_no_facturada = detalle_orden_de_trabajo.cantidad - cantidad_facturada

                detalle_orden_de_trabajo.save()

            cantidad_facturada = 0

            for detalle_orden_de_trabajo in detalles_orden_de_trabajo:
                cantidad_facturada = cantidad_facturada + detalle_orden_de_trabajo.cantidad_facturada

            self.cantidad_facturada = cantidad_facturada
            self.cantidad_no_facturada = self.cantidad - cantidad_facturada

        self.save()

    def actualizar_estado_produccion(self):
        procesos = Proceso.objects.filter(orden_de_trabajo=self)
        for proceso in procesos:
            detalles = DetalleProceso.objects.filter(proceso=proceso)
            if detalles:
                self.estado_produccion = EstadoProceso.FINALIZADO
                for detalle in detalles:
                    if detalle.estado != EstadoProceso.FINALIZADO:
                        self.estado_produccion = EstadoProceso.EN_PROCESO
        self.save()


class DetalleOrdenDeTrabajo(models.Model):
    class Meta:
        verbose_name = "detalle"
        verbose_name_plural = "detalles"

    orden_de_trabajo = models.ForeignKey(OrdenDeTrabajo)
    descripcion = models.CharField(max_length=200, verbose_name="descripción")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    dimensiones_x = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="X")
    dimensiones_y = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Y")
    dimensiones_z = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Z")
    material = models.ForeignKey(Material)
    color_seleccion_frente = models.CharField(max_length=10, blank=True, null=True, verbose_name="frente")
    color_seleccion_dorso = models.CharField(max_length=10, blank=True, null=True, verbose_name="dorso")
    color_pantone_frente = models.CharField(max_length=10, blank=True, null=True, verbose_name="frente")
    color_pantone_dorso = models.CharField(max_length=10, blank=True, null=True, verbose_name="dorso")
    observaciones = models.TextField(max_length=300, blank=True, null=True)

    entregado = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    restante = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    cantidad_facturada = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    cantidad_no_facturada = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)

    def __str__(self):
        return str("[" + str(self.orden_de_trabajo.id) + "] - " + self.descripcion)

    def get_precio_unitario(self):
        return self.material.costo_actual

    def get_subtotal(self):
        return self.cantidad * self.material.costo_actual

    def get_dimension(self):
        dimension = separador_de_miles(self.dimensiones_x) if self.dimensiones_x != None else ''
        dimension = dimension + (('x' + separador_de_miles(self.dimensiones_y)) if self.dimensiones_y != None else '')
        dimension = dimension + (('x' + separador_de_miles(self.dimensiones_z)) if self.dimensiones_z != None else '')
        return dimension

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.entregado = 0
            self.restante = self.cantidad

        super(DetalleOrdenDeTrabajo, self).save(*args, **kwargs)


def get_file_path(instance, filename):
    d = str(timezone_today()).split("-")
    fecha = d[0] + "_" + d[1] + "_" + d[2]
    file_path = 'archivos/' + fecha + "/" + str(instance.orden_de_trabajo.id).replace(" ", "_") + "/" + filename
    return file_path


class ArchivoOrdenDeTrabajo(models.Model):
    class Meta:
        verbose_name = "archivo"
        verbose_name_plural = "archivos"

    orden_de_trabajo = models.ForeignKey(OrdenDeTrabajo)
    archivo = models.FileField(upload_to=get_file_path, validators=[validar_archivo_subido])

    def __str__(self):
        return str(self.archivo)


class Costo(models.Model):
    class Meta:
        verbose_name = "costo"

    detalle_orden_de_trabajo = models.ForeignKey(DetalleOrdenDeTrabajo)
    vendedor = models.ForeignKey('funcionarios.Funcionario', null=True, blank=True)
    estado = models.CharField(max_length=10, default="PENDIENTE")

    def __str__(self):
        return str(
            str(self.detalle_orden_de_trabajo.orden_de_trabajo) + " - " + self.detalle_orden_de_trabajo.descripcion)

    def get_estado(self):
        detalles_todos = PapelCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.descripcion_id for i in apps.get_model("compras", "PapelOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = PreprensaCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.descripcion_id for i in apps.get_model("compras", "PreprensaOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = TroquelCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.descripcion_id for i in apps.get_model("compras", "TroquelOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = PosprensaServicioCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(pk__in=[i.descripcion_id for i in apps.get_model("compras",
                                                                                                     "PosprensaServicioOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = PosprensaMaterialCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(pk__in=[i.descripcion_id for i in apps.get_model("compras",
                                                                                                     "PosprensaMaterialOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = PosprensaOtroServicioCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(pk__in=[i.descripcion_id for i in apps.get_model("compras",
                                                                                                     "PosprensaOtroServicioOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = DatosDeBolsaCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.descripcion_id for i in apps.get_model("compras", "DatosDeBolsaOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = RevistaCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.descripcion_id for i in apps.get_model("compras", "RevistaOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = CompuestoCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.descripcion_id for i in apps.get_model("compras", "CompuestoOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = PlastificadoCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.descripcion_id for i in apps.get_model("compras", "PlastificadoOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        detalles_todos = OtroGastoCosto.objects.filter(costo_id=self.id)
        detalles_procesados = detalles_todos.filter(
            pk__in=[i.descripcion_id for i in apps.get_model("compras", "OtroGastoOrdenDeCompra").objects.all()])

        if (detalles_todos.count() != detalles_procesados.count()):
            return 'PENDIENTE'

        return 'PROCESADO'

    def save(self, *args, **kwargs):
        orden_de_trabajo = self.detalle_orden_de_trabajo.orden_de_trabajo
        super(Costo, self).save(*args, **kwargs)
        orden_de_trabajo.estado = orden_de_trabajo.get_estado()
        orden_de_trabajo.save()

    def delete(self, *args, **kwargs):
        orden_de_trabajo = self.detalle_orden_de_trabajo.orden_de_trabajo
        super(Costo, self).delete(*args, **kwargs)
        orden_de_trabajo.estado = orden_de_trabajo.get_estado()
        orden_de_trabajo.save()

    def get_orden_de_trabajo_unicode(self):
        return str(self.detalle_orden_de_trabajo.orden_de_trabajo)

    def get_total_papel(self):
        detalles = PapelCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_preprensa(self):
        detalles = PreprensaCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_troquel(self):
        detalles = TroquelCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_posprensaservicio(self):
        detalles = PosprensaServicioCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_posprensamaterial(self):
        detalles = PosprensaMaterialCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_posprensaotroservicio(self):
        detalles = PosprensaOtroServicioCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_datosdebolsa(self):
        detalles = DatosDeBolsaCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_revista(self):
        detalles = RevistaCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_compuesto(self):
        detalles = CompuestoCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_plastificado(self):
        detalles = PlastificadoCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_otrogasto(self):
        detalles = OtroGastoCosto.objects.filter(costo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def get_total_general(self):
        return (self.get_total_papel() + self.get_total_preprensa() + self.get_total_troquel() \
                + self.get_total_posprensaservicio() + self.get_total_posprensamaterial() \
                + self.get_total_posprensaotroservicio() + self.get_total_datosdebolsa() \
                + self.get_total_revista() + self.get_total_compuesto() \
                + self.get_total_plastificado() + self.get_total_otrogasto()
                )


class PapelCosto(models.Model):
    class Meta:
        verbose_name = "Papel"
        verbose_name_plural = "Papeles"

    costo = models.ForeignKey(Costo)
    tipo = models.CharField(max_length=50)
    gramaje = models.CharField(max_length=10, null=True, blank=True)
    resma = models.CharField(max_length=10, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(
            self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.tipo + " - " + self.gramaje + " - " + self.resma)

    def get_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(PapelCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = PapelOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class PreprensaCosto(models.Model):
    class Meta:
        verbose_name = "Pre-Prensa"

    costo = models.ForeignKey(Costo)
    maquina = models.ForeignKey('maquinaria.Maquina', blank=True, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str(
            "[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.maquina.descripcion)

    def get_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(PreprensaCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = PreprensaOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class TroquelCosto(models.Model):
    class Meta:
        verbose_name = "Troquel"
        verbose_name_plural = "Troqueles"

    costo = models.ForeignKey(Costo)
    existente = models.BooleanField(default=False)
    precio = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        if self.existente == True:
            return str("[" + str(
                self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + "Troquel existente - " + str(
                self.precio))

        return str(
            "[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + "Troquel no existente - " + str(
                self.precio))


class PosprensaServicioCosto(models.Model):
    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    costo = models.ForeignKey(Costo)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.descripcion)

    def get_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(PosprensaServicioCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = PosprensaServicioOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class PosprensaMaterialCosto(models.Model):
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"

    costo = models.ForeignKey(Costo)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.descripcion)

    def get_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(PosprensaMaterialCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = PosprensaMaterialOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class PosprensaOtroServicioCosto(models.Model):
    class Meta:
        verbose_name = "Otro servicio"
        verbose_name_plural = "Otros servicios"

    costo = models.ForeignKey(Costo)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.descripcion)

    def get_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(PosprensaOtroServicioCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = PosprensaOtroServicioOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class DatosDeBolsaCosto(models.Model):
    class Meta:
        verbose_name = "Dato de bolsa"
        verbose_name_plural = "Datos de bolsa"

    costo = models.ForeignKey(Costo)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.descripcion)

    def get_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(DatosDeBolsaCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = DatosDeBolsaOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class RevistaCosto(models.Model):
    class Meta:
        verbose_name = "Revista"
        verbose_name_plural = "Revistas"

    costo = models.ForeignKey(Costo)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.descripcion)

    def get_subtotal(self):
        return (self.cantidad * self.precio_unitario)

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(RevistaCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = RevistaOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class CompuestoCosto(models.Model):
    class Meta:
        verbose_name = "Compuesto"
        verbose_name_plural = "Compuestos"

    costo = models.ForeignKey(Costo)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.descripcion)

    def get_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(CompuestoCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = CompuestoOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class PlastificadoCosto(models.Model):
    class Meta:
        verbose_name = "Plastificado"
        verbose_name_plural = "Plastificados"

    costo = models.ForeignKey(Costo)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="cantidad (cm²)")
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.descripcion)

    def get_subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(PlastificadoCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = PlastificadoOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class OtroGastoCosto(models.Model):
    class Meta:
        verbose_name = "Otro gasto"
        verbose_name_plural = "Otros gastos"

    costo = models.ForeignKey(Costo)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_en_oc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    oc_incompletas = models.BooleanField(default=True)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("[" + str(self.costo.detalle_orden_de_trabajo.orden_de_trabajo.id) + "] " + self.descripcion)

    def get_subtotal(self):
        return (self.cantidad * self.precio_unitario)

    def save(self, *args, **kwargs):
        self.cantidad_en_oc = self.get_cantidad_en_oc()
        self.oc_incompletas = self.get_estado_oc()
        if self.pk is None:
            self.cantidad_en_oc = 0
        super(OtroGastoCosto, self).save(*args, **kwargs)

    def get_cantidad_en_oc(self):
        ordenes_de_compra = OtroGastoOrdenDeCompra.objects.filter(descripcion_id=self.id)
        cantidad_en_oc = 0
        for orden_de_compra in ordenes_de_compra:
            cantidad_en_oc += orden_de_compra.cantidad
        return cantidad_en_oc

    def get_estado_oc(self):
        if self.cantidad_en_oc >= self.cantidad:
            return False
        else:
            return True


class Maquina(models.Model):
    class Meta:
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"

    nombre = models.CharField(max_length=100)
    pasadas_por_hora = models.IntegerField(default=1)
    tipo = models.CharField(max_length=20, choices=TipoProceso.TIPOS)
    fecha_disponible = models.DateField(default=date.today)
    hora_disponible = models.TimeField(default=datetime.time(8, 0))
    activa = models.BooleanField(default=True)
    tercerizado = models.BooleanField(default=False)

    def __str__(self):
        return str(self.nombre)

    def actualizar_disponibilidad(self, fecha, hora, borrado):
        if not borrado:
            self.fecha_disponible = fecha
            self.hora_disponible = hora
        else:
            ultimo_detalle = DetalleProceso.objects.filter(maquina=self).last()
            if ultimo_detalle:
                self.fecha_disponible = ultimo_detalle.fecha_de_finalizacion
                self.hora_disponible = ultimo_detalle.hora_de_finalizacion
        self.save()

    def save(self, *args, **kwargs):
        super(Maquina, self).save(*args, **kwargs)

    def get_disponibilidad(self):
        if self.fecha_disponible < datetime.date.today():
            numero_de_dia = int(datetime.date.today().strftime("%w"))
            if 1 < numero_de_dia < 5:
                return datetime.date.today() + timedelta(days=1), 8
            elif numero_de_dia == 6:
                return datetime.date.today() + timedelta(days=2), 8
        else:
            return self.fecha_disponible, int(self.hora_disponible.hour)


class Proceso(models.Model):
    orden_de_trabajo = models.ForeignKey(OrdenDeTrabajo)
    pliegos = models.IntegerField(default=1)
    fecha_de_creacion = models.DateField(default=date.today)
    fecha_de_entrega = models.DateField(blank=True, null=True)
    urgente = models.BooleanField(default=False)

    def __str__(self):
        return str(str(self.fecha_de_creacion.strftime('%d/%m/%Y')) + ' - ' + str(self.orden_de_trabajo))

    def estado_ot(self):
        return self.orden_de_trabajo.estado_produccion

    estado_ot.short_description = 'Estado de produccion'

    def save(self, *args, **kwargs):
        if self.pk:
            orden_de_trabajo = self.orden_de_trabajo
            orden_de_trabajo.actualizar_estado_produccion()

        super(Proceso, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        detalles = DetalleProceso.objects.filter(proceso=self)
        for detalle in detalles:
            detalle.delete()
        super(Proceso, self).delete(*args, **kwargs)

    def get_procesos_realizados(self):
        detalles = DetalleProceso.objects.filter(proceso=self)
        total_procesos = 0
        detalles_realizados = 0
        if detalles:
            total_procesos = detalles.count()
            detalles_realizados = detalles.filter(estado=EstadoProceso.FINALIZADO).count()
        return str(detalles_realizados) + ' de ' + str(total_procesos)

    get_procesos_realizados.short_description = 'Procesos realizados'


class DetalleProceso(models.Model):
    proceso = models.ForeignKey(Proceso)
    tipo = models.CharField(max_length=20, choices=TipoProceso.TIPOS)
    maquina = models.ForeignKey(Maquina, on_delete=models.PROTECT)
    pasadas_por_pliego = models.IntegerField(default=1)
    horas_por_dia = models.IntegerField(default=8)
    fecha_de_inicio = models.DateField(default=date.today)
    hora_de_inicio = models.TimeField(null=True, blank=True)
    fecha_de_finalizacion = models.DateField(null=True, blank=True)
    hora_de_finalizacion = models.TimeField(null=True, blank=True)
    pliegos_a_realizar = models.IntegerField(default=0)
    pliegos_realizados = models.IntegerField(default=0, editable=False)
    estado = models.CharField(max_length=15, choices=EstadoProceso.ESTADOS, editable=False)

    def save(self, *args, **kwargs):
        if self.pk:
            crear_programacion = False
        else:
            crear_programacion = True

        super(DetalleProceso, self).save(*args, **kwargs)
        maquina = self.maquina
        maquina.actualizar_disponibilidad(self.fecha_de_finalizacion, self.hora_de_finalizacion, False)

        orden_de_trabajo = self.proceso.orden_de_trabajo
        orden_de_trabajo.actualizar_estado_produccion()

        if crear_programacion:
            programacion = Programacion.objects.exclude(fecha_de_inicio__lt=self.fecha_de_inicio).filter(
                maquina=self.maquina).order_by('fecha_de_inicio').first()
            if programacion:
                DetalleProgramacion.objects.create(programacion=programacion, detalle_proceso=self,
                                                   fecha_de_inicio=self.fecha_de_inicio,
                                                   hora_de_inicio=self.hora_de_inicio,
                                                   fecha_de_finalizacion=self.fecha_de_finalizacion,
                                                   hora_de_finalizacion=self.hora_de_finalizacion,
                                                   pliegos=self.pliegos_a_realizar)

            else:
                Programacion.objects.create(maquina=self.maquina, fecha_de_inicio=self.fecha_de_inicio)
                programacion = Programacion.objects.filter(maquina=self.maquina).last()
                DetalleProgramacion.objects.create(programacion=programacion, detalle_proceso=self,
                                                   fecha_de_inicio=self.fecha_de_inicio,
                                                   hora_de_inicio=self.hora_de_inicio,
                                                   fecha_de_finalizacion=self.fecha_de_finalizacion,
                                                   hora_de_finalizacion=self.hora_de_finalizacion,
                                                   pliegos=self.pliegos_a_realizar)

    def actualizar_pliegos_realizados(self):
        detalles_produccion = DetalleProduccion.objects.filter(detalle_programacion__detalle_proceso=self)
        if detalles_produccion:
            for detalle in detalles_produccion:
                self.pliegos_realizados += detalle.pliegos_realizados
        if self.pliegos_realizados >= self.pliegos_a_realizar:
            self.estado = EstadoProceso.FINALIZADO
        self.save()

    def delete(self, *args, **kwargs):
        maquina = self.maquina
        super(DetalleProceso, self).delete(*args, **kwargs)
        maquina.actualizar_disponibilidad(date.today, date.today, True)

    def __str__(self):
        return str(str(self.proceso) + " - " + str(self.pliegos_a_realizar) + " pliegos")

    def get_duracion(self):
        total_pasadas = self.pliegos_a_realizar * self.pasadas_por_pliego
        duracion = total_pasadas / self.maquina.pasadas_por_hora

        return duracion

    @property
    def fecha_hora_inicio(self):
        return datetime.datetime.combine(self.fecha_de_inicio, self.hora_de_inicio)

    @property
    def fecha_hora_finalizacion(self):
        return datetime.datetime.combine(self.fecha_de_finalizacion, self.hora_de_finalizacion)

    def get_diferencia_con_anterior(self):
        detalles = DetalleProceso.objects.filter(maquina=self.maquina).filter(
            fecha_de_finalizacion__lte=self.fecha_de_inicio).exclude(id=self.id)

        if detalles:
            for detalle in detalles:
                if detalle.fecha_de_inicio == self.fecha_de_inicio:
                    if self.fecha_hora_inicio - detalle.fecha_hora_inicio < timedelta(0):
                        detalles = detalles.exclude(id=detalle.id)
            detalles_ordenados = sorted(detalles, key=lambda t: t.fecha_hora_inicio, reverse=True)
            if detalles_ordenados.__len__() > 0:
                diferencia = self.fecha_hora_inicio - detalles_ordenados.__getitem__(0).fecha_hora_finalizacion
                return diferencia
            elif detalles_ordenados.__len__() == 0:
                return None

        else:
            return None


class Programacion(models.Model):
    maquina = models.ForeignKey(Maquina)
    fecha_de_inicio = models.DateField(default=date.today)
    fecha_de_entrega = models.DateField(null=True, blank=True)
    realizada = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return str(
            str(self.id) + " - " + str(self.maquina) + ' - ' + str(self.fecha_de_inicio.strftime('%d/%m/%Y')))

    def actualizar_fecha_de_entrega(self):
        ultimo_detalle = DetalleProgramacion.objects.filter(programacion=self).last()
        self.fecha_de_entrega = ultimo_detalle.fecha_de_finalizacion
        self.save()

    def save(self, *args, **kwargs):
        produccion = Produccion.objects.filter(programacion=self)
        if produccion:
            self.realizada = True
        super(Programacion, self).save(*args, **kwargs)


class DetalleProgramacion(models.Model):
    class Meta:
        verbose_name = 'Trabajo'
        verbose_name_plural = 'Trabajos'

    programacion = models.ForeignKey(Programacion)
    detalle_proceso = models.ForeignKey(DetalleProceso)
    fecha_de_inicio = models.DateField(default=date.today)
    hora_de_inicio = models.TimeField(default=datetime.time(8, 00))
    fecha_de_finalizacion = models.DateField(null=True, blank=True)
    hora_de_finalizacion = models.TimeField(null=True, blank=True)
    pliegos = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        super(DetalleProgramacion, self).save(*args, **kwargs)
        programacion = self.programacion
        programacion.actualizar_fecha_de_entrega()
        detalle_proceso = self.detalle_proceso

        detalle_proceso.maquina.fecha_disponible = self.fecha_de_finalizacion
        detalle_proceso.maquina.hora_disponible = self.hora_de_finalizacion
        detalle_proceso.maquina.save()

    def __str__(self):
        return str(str(self.programacion) + ' - ' + str(self.detalle_proceso))


class Produccion(models.Model):
    programacion = models.ForeignKey(Programacion)
    fecha_de_creacion = models.DateField(default=date.today, editable=False)

    def save(self, *args, **kwargs):
        super(Produccion, self).save(*args, **kwargs)
        self.programacion.save()


class DetalleProduccion(models.Model):
    produccion = models.ForeignKey(Produccion)
    detalle_programacion = models.ForeignKey(DetalleProgramacion)
    fecha_de_inicio = models.DateField(default=date.today)
    hora_de_inicio = models.TimeField(default=datetime.time(8, 00))
    fecha_de_finalizacion = models.DateField(null=True, blank=True)
    hora_de_finalizacion = models.TimeField(null=True, blank=True)
    pliegos_realizados = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        super(DetalleProduccion, self).save(*args, **kwargs)
        detalle_proceso = DetalleProceso.objects.get(pk=self.detalle_programacion.detalle_proceso.id)
        detalle_proceso.actualizar_pliegos_realizados()
