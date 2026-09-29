from django.db import models
from datetime import date, datetime

PENDIENTE = 0
PROCESADO = 1
ANULADO = 2
ESTADO_RECIBO = (
    (PENDIENTE, "NO IMPRESO"),
    (PROCESADO, "IMPRESO"),
    (ANULADO, "ANULADO")
)


class Recibo(models.Model):
    class Meta:
        permissions = (
            ("print_recibo", "Puede imprimir un recibo"),
            ("cancel_recibo", "Puede anular un recibo"),
        )

    talonario = models.ForeignKey('empresas.Talonario')
    numero = models.CharField(max_length=10)
    fecha = models.DateField(default=date.today)
    hora = models.TimeField(default=datetime.now, null=True, blank=True, editable=False)
    cliente = models.ForeignKey('clientes.Cliente')
    monto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    estado = models.IntegerField(choices=ESTADO_RECIBO, editable=False, default=PENDIENTE)
    presentado = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return str("Recibo Nro.:" + self.numero + " - " + self.cliente.razon_social)

    def get_total_facturas(self):
        detalles = DetalleDeRecibo.objects.filter(recibo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.monto
        return total

    def get_total_medios_de_pago(self):
        detalles = DetalleDeRecibo2.objects.filter(recibo_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.monto
        return total

    def marcar_presentado(self):
        recibo = Recibo.objects.filter(pk=self.id).first()
        if recibo:
            self.presentado = True

        else:
            self.presentado = False
        super(Recibo, self).save()


MEDIOS_DE_PAGO = (
    (0, 'Efectivo'),
    (1, 'Transferencia bancaria'),
    (2, 'Giros'),
    (3, 'Cheque'),
    (4, 'Nota de credito'),
    (5, 'Retencion'),
    (6, 'Tarjeta de debito'),
    (7, 'Tarjeta de credito'),
    (8, 'Anticipo'),
    (9, 'Otros'),
)


class DetalleDeRecibo(models.Model):
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"

    recibo = models.ForeignKey(Recibo)
    factura = models.ForeignKey('ventas.Venta', null=True, blank=True)
    monto = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.factura:
            factura = self.factura
            super(DetalleDeRecibo, self).save(*args, **kwargs)
            factura.pagado = factura.get_pagado()
            factura.saldo = factura.get_saldo()
            factura.save()

    def delete(self, *args, **kwargs):
        if self.factura:
            factura = self.factura
            super(DetalleDeRecibo, self).delete(*args, **kwargs)
            factura.pagado = factura.get_pagado()
            factura.saldo = factura.get_saldo()
            factura.save()


class DetalleDeRecibo2(models.Model):
    class Meta:
        verbose_name = "Medio de pago"
        verbose_name_plural = "Medios de pago"

    recibo = models.ForeignKey(Recibo)
    medio_de_pago = models.IntegerField(choices=MEDIOS_DE_PAGO, default=0)
    numero_de_comprobante = models.CharField(max_length=100, null=True, blank=True)
    cheque = models.ForeignKey('cheques.ChequeRecibido', null=True, blank=True)
    cuenta_bancaria = models.ForeignKey('bancos.CuentaBancaria', null=True, blank=True)
    monto = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("Pago segun recibo Nro.: " + self.recibo.numero)

    def save(self, *args, **kwargs):
        if self.monto is None:
            self.monto = 0

        super(DetalleDeRecibo2, self).save(*args, **kwargs)


class PresentacionCobros(models.Model):
    class Meta:
        verbose_name = 'Rendicion de cobros'
        verbose_name_plural = 'Rendiciones de cobros'

    fecha = models.DateField(default=date.today)
    cobrador = models.ForeignKey('funcionarios.Funcionario')
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return str(str(self.fecha))

    def get_total(self):
        detalles = DetallePresentacion.objects.filter(presentacion=self)
        total = 0
        for detalle in detalles:
            total += detalle.subtotal
        return total

    def save(self, *args, **kwargs):
        super(PresentacionCobros, self).save(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.total = self.get_total()
        super(PresentacionCobros, self).update(*args, **kwargs)


class DetallePresentacion(models.Model):
    class Meta:
        verbose_name = 'Cobro de presentacion'
        verbose_name_plural = 'Cobros de presentacion'

    presentacion = models.ForeignKey(PresentacionCobros)
    cobro = models.ForeignKey('cobros.Recibo')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        recibo = Recibo.objects.filter(id=self.cobro.pk).first()
        recibo.marcar_presentado()
        presentacion = PresentacionCobros.objects.filter(id=self.presentacion_id).first()
        presentacion.save()
        super(DetallePresentacion, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        presentacion = PresentacionCobros.objects.filter(id=self.presentacion_id).first()
        super(DetallePresentacion, self).delete(*args, **kwargs)
        presentacion.save()
