from django.db import models
from datetime import date


class Pago(models.Model):
    proveedor = models.ForeignKey("proveedores.Proveedor")
    fecha = models.DateField(default=date.today)
    monto = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return str("Pago a proveedor " + self.proveedor.razon_social)

    def get_total_facturas(self):
        detalles = DetalleDePago.objects.filter(pago_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.monto
        return total

    def get_total_medios_de_pago(self):
        detalles = DetalleDePago2.objects.filter(pago_id=self.id)
        total = 0
        for detalle in detalles:
            total = total + detalle.monto
        return total


MEDIOS_DE_PAGO = (
    (0, 'Efectivo'),
    (1, 'Transferencia bancaria'),
    (2, 'Giros'),
    (3, 'Cheque'),
    (4, 'Nota de credito'),
    (5, 'Retencion'),
    (6, 'Tarjeta de debito'),
    (7, 'Tarjeta de credito'),
)


class DetalleDePago(models.Model):
    class Meta:
        verbose_name = "Detalle de factura"
        verbose_name_plural = "Detalle de facturas"

    pago = models.ForeignKey(Pago)
    compra = models.ForeignKey("compras.Compra", verbose_name="factura", null=True)
    monto = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        factura = self.compra
        super(DetalleDePago, self).save(*args, **kwargs)
        factura.pagado = factura.get_pagado()
        factura.saldo = factura.get_saldo()
        factura.save()

    def delete(self, *args, **kwargs):
        factura = self.compra
        super(DetalleDePago, self).delete(*args, **kwargs)
        factura.pagado = factura.get_pagado()
        factura.saldo = factura.get_saldo()
        factura.save()


class DetalleDePago2(models.Model):
    class Meta:
        verbose_name = "Detalle de medio de pago"
        verbose_name_plural = "Detalle de medios de pago"

    pago = models.ForeignKey(Pago)
    medio_de_pago = models.IntegerField(choices=MEDIOS_DE_PAGO, default=0)
    numero_de_comprobante = models.CharField(max_length=100, null=True, blank=True)
    cheque = models.ForeignKey('cheques.ChequeEmitido', null=True, blank=True)
    cuenta_bancaria = models.ForeignKey('bancos.CuentaBancaria', null=True, blank=True)
    monto = models.DecimalField(max_digits=15, decimal_places=2)
