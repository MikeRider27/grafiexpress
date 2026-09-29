# -*- coding: utf-8 -*-

from django.db import models
from django.apps import apps

# Condiciones de Compra
CONTADO = 'CO'
CREDITO = 'CR'
CONDICION = (
    (CONTADO, 'CONTADO'),
    (CREDITO, 'CREDITO'),
)


class Proveedor(models.Model):
    class Meta:
        verbose_name = 'proveedor'
        verbose_name_plural = 'proveedores'

    razon_social = models.CharField(max_length=100)
    ruc = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200, null=True, blank=True, verbose_name="dirección")
    telefono = models.CharField(max_length=50, null=True, blank=True, verbose_name="teléfono")
    celular = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True, verbose_name="e-mail")
    contacto = models.CharField(max_length=100, null=True, blank=True)
    condicion_de_compra = models.CharField(choices=CONDICION, default=CONTADO, max_length=2)
    plazo_de_credito = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.razon_social

    def get_total_deuda(self):
        facturas = apps.get_model("compras", "Compra").objects.filter(proveedor_id=self.id)
        suma = 0
        for factura in facturas:
            suma = suma + factura.saldo
        return suma
