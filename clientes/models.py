# -*- coding: utf-8 -*-

from django.db import models
from django.apps import apps

# Create your models here.
# Condiciones de Venta
CONTADO = 'CO'
CREDITO = 'CR'
CONDICION = (
    (CONTADO, 'CONTADO'),
    (CREDITO, 'CREDITO'),
)


class Cliente(models.Model):
    razon_social = models.CharField(max_length=100, verbose_name="razón social")
    nombre = models.CharField(max_length=100, null=True, blank=True)
    ruc = models.CharField(max_length=20, verbose_name="RUC", unique=True)
    direccion = models.CharField(max_length=200, null=True, verbose_name="dirección")
    telefono = models.CharField(max_length=50, null=True, verbose_name="teléfono")
    email = models.CharField(max_length=100, null=True, blank=True, verbose_name="e-mail")
    vendedor = models.ForeignKey('funcionarios.Funcionario', null=True, blank=True)

    condicion_de_venta = models.CharField(choices=CONDICION, default=CONTADO, max_length=2)
    plazo_de_credito = models.CharField(max_length=100, null=True, blank=True, help_text="agregar palabra  días.")
    limite_de_credito = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=2000000.00)

    ciudad = models.ForeignKey("ciudades.Ciudad", null=True, blank=True)

    libre_de_impuesto = models.BooleanField(default=False, verbose_name="¿Es excento de impuesto?")

    requiere_orden_de_compra_del_proveedor = models.BooleanField(default=False)
    requiere_orden_de_trabajo = models.BooleanField(default=False)
    requiere_numero_de_recepcion = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return str(self.razon_social)

    def get_total_deuda(self):
        facturas = apps.get_model("ventas", "Venta").objects.filter(cliente_id=self.id).exclude(estado='A')
        suma = 0
        for factura in facturas:
            suma = suma + factura.saldo
        return suma


class Marca(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, blank=False, null=False)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return str(self.nombre)


class Contacto(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, blank=False, null=False)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="teléfono")

    def __str__(self):
        return (str(self.nombre) + u" " + str(self.apellido))

    def get_cliente(self):
        return self.cliente.nombre
