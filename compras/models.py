from django.contrib.auth.models import User
from django.db import models
from datetime import date

from django.http import request

from pagos.models import DetalleDePago
from sistema import apps

CONTADO = "CO"
CREDITO = "CR"
CONDICION = (
    (CONTADO, 'CONTADO'),
    (CREDITO, 'CREDITO')
)


class OrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "orden de compra"
        verbose_name_plural = "ordenes de compra"

    fecha = models.DateField(default=date.today, verbose_name="fecha de emision")
    proveedor = models.ForeignKey("proveedores.Proveedor", verbose_name="proveedor")
    contacto = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    forma_de_pago = models.CharField(max_length=50, null=True, blank=True)
    condicion = models.CharField(max_length=10, choices=CONDICION, default=CONTADO)
    cheque_diferido = models.CharField(max_length=50, null=True, blank=True)
    plazo = models.CharField(max_length=50, null=True, blank=True)
    departamento_solicitante = models.CharField(max_length=50, null=True, blank=True)
    categoria_de_gastos = models.CharField(max_length=50, null=True, blank=True)
    responsable = models.CharField(max_length=50, null=True, blank=True)
    creado_por = models.ForeignKey(User, blank=True, null=True)

    def __str__(self):
        return str("Orden de compra Nro.: " + str(self.id))

    def get_total(self):
        total = 0
        detalles = PapelOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = PreprensaOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = TroquelOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = PosprensaMaterialOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = PosprensaServicioOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = DatosDeBolsaOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = RevistaOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = CompuestoOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = PlastificadoOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = OtroGastoOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        detalles = InsumoOrdenDeCompra.objects.filter(orden_de_compra_id=self.id)
        for detalle in detalles:
            total = total + detalle.get_subtotal()
        return total

    def delete(self, *args, **kwargs):
        detalles_papel = PapelOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_papel in detalles_papel:
            detalle_papel.delete()

        detalles_preprensa = PreprensaOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_preprensa in detalles_preprensa:
            detalle_preprensa.delete()

        detalles_troquel = TroquelOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_troquel in detalles_troquel:
            detalle_troquel.delete()

        detalles_posprensa_servicio = PosprensaServicioOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_posprensa_servicio in detalles_posprensa_servicio:
            detalle_posprensa_servicio.delete()

        detalles_posprensa_material = PosprensaMaterialOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalles_posprensa_material in detalles_posprensa_material:
            detalles_posprensa_material.delete()

        detalles_posprensa_otro_servicio = PosprensaOtroServicioOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_posprensa_otro_servicio in detalles_posprensa_otro_servicio:
            detalle_posprensa_otro_servicio.delete()

        detalles_bolsa = DatosDeBolsaOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_bolsa in detalles_bolsa:
            detalle_bolsa.delete()

        detalles_revista = RevistaOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_revista in detalles_revista:
            detalle_revista.delete()

        detalles_compuesto = CompuestoOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_compuesto in detalles_compuesto:
            detalle_compuesto.delete()

        detalles_plastificado = PlastificadoOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalles_plastificado in detalles_plastificado:
            detalles_plastificado.delete()

        detalles_otro = OtroGastoOrdenDeCompra.objects.filter(orden_de_compra=self)
        for detalle_otro in detalles_otro:
            detalle_otro.delete()


class PapelOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Papel"
        verbose_name_plural = "Papeles"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.PapelCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        papel_costo = self.descripcion
        super(PapelOrdenDeCompra, self).save(*args, **kwargs)
        papel_costo.save()

    def delete(self, *args, **kwargs):
        papel_costo = self.descripcion
        super(PapelOrdenDeCompra, self).delete(*args, **kwargs)
        papel_costo.save()


class PreprensaOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Pre-Prensa"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.PreprensaCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        preprensa_costo = self.descripcion
        super(PreprensaOrdenDeCompra, self).save(*args, **kwargs)
        preprensa_costo.save()

    def delete(self, *args, **kwargs):
        preprensa_costo = self.descripcion
        super(PreprensaOrdenDeCompra, self).delete(*args, **kwargs)
        preprensa_costo.save()


class TroquelOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Troquel"
        verbose_name_plural = "Troqueles"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.TroquelCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        troquel_costo = self.descripcion
        super(TroquelOrdenDeCompra, self).save(*args, **kwargs)
        troquel_costo.save()

    def delete(self, *args, **kwargs):
        troquel_costo = self.descripcion
        super(TroquelOrdenDeCompra, self).delete(*args, **kwargs)
        troquel_costo.save()


class PosprensaServicioOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.PosprensaServicioCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        posprensa_costo = self.descripcion
        super(PosprensaServicioOrdenDeCompra, self).save(*args, **kwargs)
        posprensa_costo.save()

    def delete(self, *args, **kwargs):
        posprensa_costo = self.descripcion
        super(PosprensaServicioOrdenDeCompra, self).delete(*args, **kwargs)
        posprensa_costo.save()


class PosprensaMaterialOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.PosprensaMaterialCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        posprensa_costo = self.descripcion
        super(PosprensaMaterialOrdenDeCompra, self).save(*args, **kwargs)
        posprensa_costo.save()

    def delete(self, *args, **kwargs):
        posprensa_costo = self.descripcion
        super(PosprensaMaterialOrdenDeCompra, self).delete(*args, **kwargs)
        posprensa_costo.save()


class PosprensaOtroServicioOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Otro servicio"
        verbose_name_plural = "Otros servicios"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.PosprensaOtroServicioCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        posprensa_costo = self.descripcion
        super(PosprensaOtroServicioOrdenDeCompra, self).save(*args, **kwargs)
        posprensa_costo.save()

    def delete(self, *args, **kwargs):
        posprensa_costo = self.descripcion
        super(PosprensaOtroServicioOrdenDeCompra, self).delete(*args, **kwargs)
        posprensa_costo.save()


class DatosDeBolsaOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Dato de bolsa"
        verbose_name_plural = "Datos de bolsa"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.DatosDeBolsaCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        datos_costo = self.descripcion
        super(DatosDeBolsaOrdenDeCompra, self).save(*args, **kwargs)
        datos_costo.save()

    def delete(self, *args, **kwargs):
        datos_costo = self.descripcion
        super(DatosDeBolsaOrdenDeCompra, self).delete(*args, **kwargs)
        datos_costo.save()


class RevistaOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Revista"
        verbose_name_plural = "Revistas"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.RevistaCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        revista_costo = self.descripcion
        super(RevistaOrdenDeCompra, self).save(*args, **kwargs)
        revista_costo.save()

    def delete(self, *args, **kwargs):
        revista_costo = self.descripcion
        super(RevistaOrdenDeCompra, self).delete(*args, **kwargs)
        revista_costo.save()


class CompuestoOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Compuesto"
        verbose_name_plural = "Compuestos"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.CompuestoCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        compuesto_costo = self.descripcion
        super(CompuestoOrdenDeCompra, self).save(*args, **kwargs)
        compuesto_costo.save()

    def delete(self, *args, **kwargs):
        compuesto_costo = self.descripcion
        super(CompuestoOrdenDeCompra, self).delete(*args, **kwargs)
        compuesto_costo.save()


class PlastificadoOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Plastificado"
        verbose_name_plural = "Plastificados"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.PlastificadoCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        pastificado_costo = self.descripcion
        super(PlastificadoOrdenDeCompra, self).save(*args, **kwargs)
        pastificado_costo.save()

    def delete(self, *args, **kwargs):
        plastificado_costo = self.descripcion
        super(PlastificadoOrdenDeCompra, self).delete(*args, **kwargs)
        plastificado_costo.save()


class OtroGastoOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Otro gasto"
        verbose_name_plural = "Otros gastos"

    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    descripcion = models.ForeignKey("produccion.OtroGastoCosto")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario

    def save(self, *args, **kwargs):
        otro_costo = self.descripcion
        super(OtroGastoOrdenDeCompra, self).save(*args, **kwargs)
        otro_costo.save()

    def delete(self, *args, **kwargs):
        otro_costo = self.descripcion
        super(OtroGastoOrdenDeCompra, self).delete(*args, **kwargs)
        otro_costo.save()


class InsumoOrdenDeCompra(models.Model):
    class Meta:
        verbose_name = "Compra de insumo"
        verbose_name_plural = "Compras de insumos"

    orden_de_compra = models.ForeignKey(OrdenDeCompra)
    descripcion = models.ForeignKey("materiales.Material")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    def get_subtotal(self):
        return self.cantidad*self.precio_unitario


class Compra(models.Model):
    empresa = models.ForeignKey("empresas.Empresa")
    sucursal = models.ForeignKey("empresas.Sucursal")

    codigo_de_establecimiento = models.CharField(max_length=3, editable=False)
    punto_de_expedicion = models.CharField(max_length=3, editable=False)
    numero_de_factura = models.CharField(max_length=10, editable=False)
    # timbrado = models.CharField(max_length=10, null=True)

    proveedor = models.ForeignKey("proveedores.Proveedor")

    condicion = models.CharField(choices=CONDICION, default=CREDITO, max_length=2)

    orden_de_compra = models.ManyToManyField(OrdenDeCompra, blank=True)
    fecha = models.DateField(default=date.today, verbose_name="fecha de emision")
    fecha_de_vencimiento = models.DateField(default=date.today, null=True)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    pagado = models.DecimalField(max_digits=15, decimal_places=2, editable=False, null=True)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, editable=False, null=True)
    creado_por = models.ForeignKey(User, blank=True, null=True)

    def get_numero_de_factura(self):
        return "%s-%s-%s" % (self.codigo_de_establecimiento, self.punto_de_expedicion, self.numero_de_factura)

    def get_pagado(self):
        detalles = DetalleDePago.objects.filter(compra_id=self.id)  # .exclude(pago__estado=2) #excluir pagos anulados
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

        super(Compra, self).save(*args, **kwargs)

    def __str__(self):
        if self.condicion == CONTADO:
            return "Factura Contado Nro.: " + self.get_numero_de_factura()
        return "Factura Credito Nro.: " + self.get_numero_de_factura()


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra)
    material = models.ForeignKey("materiales.Material")
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)


class DetalleCompra2(models.Model):
    class Meta:
        verbose_name = "Insumo compra"
        verbose_name_plural = "Insumos compra"

    compra = models.ForeignKey(Compra)
    articulo = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
