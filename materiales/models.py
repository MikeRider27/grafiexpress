# -*- coding: utf-8 -*-

from django.apps import apps
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from ventas.models import IVA, IVA_10


@python_2_unicode_compatible
class UnidadDeMedida(models.Model):
    class Meta:
        verbose_name = "unidad de medida"
        verbose_name_plural = "unidades de medida"

    nombre = models.CharField(max_length=100)
    simbolo = models.CharField(max_length=10, blank=True, null=True, verbose_name="Símbolo")

    def __str__(self):
        return self.nombre


@python_2_unicode_compatible
class CategoriaDeMaterial(models.Model):
    class Meta:
        verbose_name = "categoría de materiales"
        verbose_name_plural = "categorías de materiales"

    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


@python_2_unicode_compatible
class Gramaje(models.Model):
    descripcion = models.CharField(max_length=10)

    def __str__(self):
        return self.descripcion


@python_2_unicode_compatible
class Resma(models.Model):
    descripcion = models.CharField(max_length=10)

    def __str__(self):
        return self.descripcion


@python_2_unicode_compatible
class Material(models.Model):
    class Meta:
        verbose_name_plural = "materiales"

    descripcion = models.CharField(max_length=150, verbose_name="descripción")
    codigo = models.CharField(max_length=10, blank=True, null=True, verbose_name="código")
    unidad_de_medida = models.ForeignKey(UnidadDeMedida)
    categoria = models.ForeignKey(CategoriaDeMaterial, verbose_name="categoría")
    stock_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    iva = models.IntegerField(choices=IVA, default=IVA_10)
    costo_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    retiro_ot = models.BooleanField(default=True, verbose_name="retiro en OT")
    retiro_factura = models.BooleanField(default=False, verbose_name="retiro en Factura")
    gramaje = models.ForeignKey(Gramaje, null=True, blank=True)
    resma = models.ForeignKey(Resma, null=True, blank=True)

    marca = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        resultado = self.descripcion
        if self.gramaje:
            resultado += ' - ' + str(self.gramaje)
        if self.resma:
            resultado += ' - ' + str(self.resma)
        return resultado

    def actualizar_stock(self):
        cantidad = 0

        detalles_altas = apps.get_model("depositos", "DetalleAlta").objects.filter(material_id=self.id)
        for detalle in detalles_altas:
            cantidad = cantidad + detalle.cantidad

        detalles_bajas = apps.get_model("depositos", "DetalleBaja").objects.filter(material_id=self.id)
        for detalle in detalles_bajas:
            cantidad -= detalle.cantidad

        detalles_retiros = apps.get_model("depositos", "DetalleRetiro").objects.filter(material_id=self.id)
        for detalle in detalles_retiros:
            cantidad = cantidad - detalle.cantidad

        detalles_devoluciones = apps.get_model("depositos", "DetalleDevolucion").objects.filter(
            detalle_retiro__material__id=self.id)
        for detalle in detalles_devoluciones:
            cantidad = cantidad + detalle.cantidad

        self.stock_actual = cantidad
        self.save()

    def get_stock_deposito(self, deposito_id):
        cantidad = 0

        detalles_altas = apps.get_model("depositos", "DetalleAlta").objects.filter(material_id=self.id,
                                                                                   alta__deposito=deposito_id)
        for detalle in detalles_altas:
            cantidad = cantidad + detalle.cantidad

        detalles_bajas = apps.get_model("depositos", "DetalleBaja").objects.filter(material_id=self.id,
                                                                                   baja__deposito=deposito_id)
        for detalle in detalles_bajas:
            cantidad = cantidad - detalle.cantidad

        detalles_retiros = apps.get_model("depositos", "DetalleRetiro").objects.filter(material_id=self.id,
                                                                                       deposito=deposito_id)
        for detalle in detalles_retiros:
            cantidad = cantidad - detalle.cantidad

        detalles_devoluciones = apps.get_model("depositos", "DetalleDevolucion").objects.filter(
            detalle_retiro__material__id=self.id, deposito=deposito_id)
        for detalle in detalles_devoluciones:
            cantidad = cantidad + detalle.cantidad

        return cantidad