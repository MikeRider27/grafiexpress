# -*- coding: utf-8 -*-

from datetime import date
from django.apps import apps
from django.db import models

# Estados de Factura y Remision
PENDIENTE = 'P'
CONFIRMADO = 'C'
ANULADO = 'A'
ESTADOS = (
    (PENDIENTE, 'SIN IMPRIMIR'),
    (CONFIRMADO, 'IMPRESO'),
    (ANULADO, 'ANULADO'),
)


class Remision(models.Model):
    class Meta:
        permissions = (
            ("view_remision", "Puede ver la lista de remisiones"),
            ("print_remision", "Puede imprimir una remision"),
            ("cancel_remision", "Puede anular una remision"),
        )

        verbose_name = "Remision"
        verbose_name_plural = "Remisiones"
        unique_together = (('codigo_de_establecimiento', 'punto_de_expedicion', 'numero_de_remision', 'timbrado'))

    # datos de la empresa
    empresa = models.ForeignKey("empresas.Empresa")
    sucursal = models.ForeignKey("empresas.Sucursal", null=True)
    talonario = models.ForeignKey("empresas.Talonario", null=True)

    # datos de la remision
    codigo_de_establecimiento = models.CharField(max_length=3, null=True)
    punto_de_expedicion = models.CharField(max_length=3, null=True)
    numero_de_remision = models.CharField(max_length=10, null=True)
    timbrado = models.CharField(max_length=10, null=True)
    fecha_de_emision = models.DateField(default=date.today)

    # destinatario de la mercaderia
    cliente = models.ForeignKey("clientes.Cliente")

    # datos del traslado
    motivo_del_traslado = models.CharField(max_length=100, blank=True, null=True)
    comprobante_de_venta = models.CharField(max_length=100, blank=True, null=True)

    numero_de_comprobante_de_venta = models.CharField(max_length=100, blank=True, null=True)
    numero_de_timbrado = models.CharField(max_length=100, blank=True, null=True)

    fecha_de_expedicion = models.DateField(default=date.today, blank=True, null=True)

    fecha_de_inicio_del_traslado = models.DateField(default=date.today, blank=True, null=True)
    fecha_estimada_de_termino_del_traslado = models.DateField(default=date.today, blank=True, null=True)

    direccion_del_punto_de_partida = models.CharField(max_length=200, blank=True, null=True)

    ciudad_de_partida = models.CharField(max_length=100, blank=True, null=True)
    departamento_de_partida = models.CharField(max_length=100, blank=True, null=True)

    direccion_del_punto_de_llegada = models.CharField(max_length=200, blank=True, null=True)

    ciudad_de_llegada = models.CharField(max_length=100, blank=True, null=True)
    departamento_de_llegada = models.CharField(max_length=100, blank=True, null=True)

    kilometros_estimados_de_recorrido = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    cambio_de_fecha_de_termino_del_traslado_o_punto_de_llegada = models.CharField(max_length=100, blank=True, null=True)
    motivo = models.CharField(max_length=100, blank=True, null=True)

    # datos del vehiculo de transporte
    vehiculo = models.ForeignKey("automoviles.Automovil", null=True, blank=True)
    # marca_del_vehiculo = models.CharField(max_length=100, null=True, blank=True)
    # numero_de_registro_unico_del_automotor = models.CharField(max_length=100, blank=True, null=True)
    # numero_de_rua_de_remolquetracto_o_semiremolque = models.CharField(max_length=100, blank=True, null=True, verbose_name="numero de registro unico del automotor de remolquetracto o semiremolque")

    # datos del conductor del vehiculo
    chofer = models.ForeignKey("funcionarios.Funcionario", null=True, blank=True)
    # nombre = models.CharField("nombre y apellido o razon social",max_length=100, blank=True, null=True)
    # ruc = models.CharField("RUC/CI", max_length=100, blank=True, null=True)
    # domicilio = models.CharField(max_length=100, blank=True, null=True)

    estado = models.CharField(max_length=1, choices=ESTADOS, default=PENDIENTE, editable=False)

    def get_numero_de_remision(self):
        return "%s-%s-%s" % (self.codigo_de_establecimiento, self.punto_de_expedicion, self.numero_de_remision)

    def __unicode__(self):
        return unicode("Remision Nro.: " + str(self.get_numero_de_remision()))


class DetalleDeRemision(models.Model):
    class Meta:
        verbose_name = "Detalle de la remision (OT sin cambio)"
        verbose_name_plural = "Detalles de la remision (OT sin cambio)"

    remision = models.ForeignKey(Remision)
    orden_de_trabajo = models.ForeignKey("produccion.OrdenDeTrabajo")
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    unidad_de_medida = models.ForeignKey("materiales.UnidadDeMedida", blank=True, null=True)


class DetalleDeRemision2(models.Model):
    class Meta:
        verbose_name = "Detalle de la remision (OT con cambio)"
        verbose_name_plural = "Detalles de la remision (OT con cambio)"

    remision = models.ForeignKey(Remision)
    detalle_orden_de_trabajo = models.ForeignKey("produccion.DetalleOrdenDeTrabajo")
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    unidad_de_medida = models.ForeignKey("materiales.UnidadDeMedida", blank=True, null=True)


# Condiciones de Venta
CONTADO = 'CO'
CREDITO = 'CR'
CONDICION = (
    (CONTADO, 'CONTADO'),
    (CREDITO, 'CREDITO'),
)

# tipos de IVA
IVA_10 = 10
IVA_5 = 5
EXCENTA = 0
IVA = (
    (IVA_10, 'IVA 10%'),
    (IVA_5, 'IVA 5%'),
    (EXCENTA, 'EXCENTA')
)


class Venta(models.Model):
    class Meta:
        permissions = (
            ("view_venta", "Puede ver la lista de facturas"),
            ("print_venta", "Puede imprimir una factura"),
            ("cancel_venta", "Puede anular una factura"),
        )

        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        unique_together = (('codigo_de_establecimiento', 'punto_de_expedicion', 'numero_de_factura', 'timbrado'))

    cliente = models.ForeignKey("clientes.Cliente")

    empresa = models.ForeignKey("empresas.Empresa")
    sucursal = models.ForeignKey("empresas.Sucursal", null=True)
    talonario = models.ForeignKey("empresas.Talonario", null=True)

    remision = models.ManyToManyField(Remision, blank=True)

    codigo_de_establecimiento = models.CharField(max_length=3, editable=False)
    punto_de_expedicion = models.CharField(max_length=3, editable=False)
    numero_de_factura = models.CharField(max_length=10, editable=False)
    timbrado = models.CharField(max_length=10, null=True)

    condicion = models.CharField(choices=CONDICION, default=CREDITO, max_length=2)
    cantidad_de_cuotas = models.IntegerField(default=0)
    fecha_de_emision = models.DateField(default=date.today)
    fecha_de_vencimiento = models.DateField(default=date.today, null=True)
    fecha_de_anulacion = models.DateField(null=True, blank=True, editable=False)
    estado = models.CharField(choices=ESTADOS, default=PENDIENTE, max_length=10, editable=False)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    pagado = models.DecimalField(max_digits=15, decimal_places=2, editable=False, null=True)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, editable=False, null=True)

    def get_numero_de_factura(self):
        return "%s-%s-%s" % (self.codigo_de_establecimiento, self.punto_de_expedicion, self.numero_de_factura)

    def get_pagado(self):
        detalles = apps.get_model("cobros.DetalleDeRecibo").objects.filter(factura_id=self.id).exclude(
            recibo__estado=2)  # excluir recibos anulados
        suma = 0
        for detalle in detalles:
            suma = suma + detalle.monto
        return suma

    def get_saldo(self):
        return (self.total - self.pagado)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.pagado = 0
            self.saldo = self.total
        else:
            self.pagado = self.get_pagado()
            self.saldo = self.get_saldo()

        if self.condicion == CREDITO:
            self.cantidad_de_cuotas = 1
        elif self.condicion == CONTADO:
            self.pagado = self.total
            self.saldo = 0

        super(Venta, self).save(*args, **kwargs)

    def __unicode__(self):
        if self.condicion == CONTADO:
            return "Factura Contado Nro.: " + self.get_numero_de_factura()
        return "Factura Credito Nro.: " + self.get_numero_de_factura()

    def get_subtotal_exenta(self):
        suma = 0

        detalles = DetalleDeVenta.objects.filter(venta_id=self.id, iva=EXCENTA)
        for detalle in detalles:
            suma = suma + detalle.subtotal

        detalles = DetalleDeVenta2.objects.filter(venta_id=self.id, iva=EXCENTA)
        for detalle in detalles:
            suma = suma + detalle.subtotal

        return suma

    def get_subtotal_iva_5(self):
        suma = 0

        detalles = DetalleDeVenta.objects.filter(venta_id=self.id, iva=IVA_5)
        for detalle in detalles:
            suma = suma + detalle.subtotal

        detalles = DetalleDeVenta2.objects.filter(venta_id=self.id, iva=IVA_5)
        for detalle in detalles:
            suma = suma + detalle.subtotal

        return suma

    def get_iva_5(self):
        return (self.get_subtotal_iva_5() / 21)

    def get_subtotal_iva_10(self):
        suma = 0

        detalles = DetalleDeVenta.objects.filter(venta_id=self.id, iva=IVA_10)
        for detalle in detalles:
            suma = suma + detalle.subtotal

        detalles = DetalleDeVenta2.objects.filter(venta_id=self.id, iva=IVA_10)
        for detalle in detalles:
            suma = suma + detalle.subtotal

        return suma

    def get_iva_10(self):
        return (self.get_subtotal_iva_10() / 11)

    def get_total_iva(self):
        return (self.get_iva_5() + self.get_iva_10())


class DetalleDeVenta(models.Model):
    class Meta:
        verbose_name = "Detalle de la venta"
        verbose_name_plural = "Detalles de la venta (Sin cambios)"

    venta = models.ForeignKey(Venta)
    orden_de_trabajo = models.ForeignKey("produccion.OrdenDeTrabajo")
    descripcion = models.CharField(max_length=200)
    descripcion_extra = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nº de oc/recepcion")
    iva = models.IntegerField(choices=IVA, default=IVA_10)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)


class DetalleDeVenta2(models.Model):
    class Meta:
        verbose_name = "Detalle de la venta"
        verbose_name_plural = "Detalles de la venta (Con cambios)"

    venta = models.ForeignKey(Venta)
    detalle_orden_de_trabajo = models.ForeignKey("produccion.DetalleOrdenDeTrabajo")
    descripcion = models.CharField(max_length=200)
    descripcion_extra = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nº de oc/recepcion")
    iva = models.IntegerField(choices=IVA, default=IVA_10)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)


class DetalleVentaMateriales(models.Model):
    class Meta:
        verbose_name = "Detalle de Venta - Materiales"
        verbose_name_plural = "Detalles de Venta - Materiales"

    venta = models.ForeignKey(Venta)
    material = models.ForeignKey('materiales.Material')
    descripcion = models.CharField(max_length=200)
    iva = models.IntegerField(choices=IVA, default=IVA_10)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)


class VentaRemision(models.Model):
    class Meta:
        db_table = 'ventas_venta_remision'
        managed = False

    venta = models.ForeignKey(Venta)
    remision = models.ForeignKey(Remision)


class RemisionAntiguo(Remision):
    class Meta:
        proxy = True


class VentaAntiguo(Venta):
    class Meta:
        proxy = True
