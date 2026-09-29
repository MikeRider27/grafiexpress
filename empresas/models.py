# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from datetime import date


class Empresa(models.Model):
    nombre = models.CharField(max_length=100)
    ruc = models.CharField(max_length=15)
    direccion = models.CharField(max_length=200, null=True, blank=True, verbose_name="dirección")
    telefono = models.CharField(max_length=20, null=True, blank=True, verbose_name="teléfono")
    email = models.EmailField(max_length=100, null=True, blank=True, verbose_name="e-mail")

    def __str__(self):
        return str(self.nombre)


class Sucursal(models.Model):
    class Meta:
        verbose_name = "sucursal"
        verbose_name_plural = "sucursales"

    empresa = models.ForeignKey(Empresa)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, null=True, blank=True, verbose_name="dirección")
    telefono = models.CharField(max_length=20, null=True, blank=True, verbose_name="teléfono")
    email = models.CharField(max_length=100, null=True, blank=True, verbose_name="e-mail")

    def __str__(self):
        return (str(self.empresa.nombre) + u" - " + str(self.nombre))


class Timbrado(models.Model):
    numero = models.CharField(max_length=10)
    fecha_de_inicio = models.DateField(null=True)
    fecha_de_vencimiento = models.DateField(null=True)
    activo = models.BooleanField(default=True)
    empresa = models.ForeignKey(Empresa, null=True)

    def __str__(self):
        if self.empresa != None:
            return (str(self.empresa.nombre) + u" " + str(self.numero))
        return str(self.numero)


FACTURA = 0
REMISION = 1
RECIBO = 2
NOTA_CREDITO = 3
TIPO_DE_TALONARIO = (
    (FACTURA, "FACTURA"),
    (REMISION, "REMISION"),
    (RECIBO, "RECIBO"),
    (NOTA_CREDITO, "NOTA DE CREDITO"),
)


class Talonario(models.Model):
    nombre = models.CharField(max_length=100, null=True)
    descripcion = models.CharField(max_length=200, null=True)
    tipo_de_talonario = models.IntegerField(choices=TIPO_DE_TALONARIO, default=FACTURA)
    fecha_de_caducidad = models.DateField(null=True)
    fecha_de_creacion = models.DateField(default=date.today)
    numero_inicial = models.IntegerField()
    numero_final = models.IntegerField()
    ultimo_usado = models.IntegerField(null=True, blank=True)
    codigo_de_establecimiento = models.CharField(max_length=3, null=True, blank=True)
    punto_de_expedicion = models.CharField(max_length=3, null=True, blank=True)
    # usuario = models.ForeignKey(User, null=True, blank=True)
    sucursal = models.ForeignKey(Sucursal, null=True)
    agotado = models.BooleanField(default=False)
    timbrado = models.ForeignKey(Timbrado, null=True, blank=True)

    activo = models.BooleanField(default=False)

    def __str__(self):
        return (str(self.sucursal.empresa.nombre) + u" - " + str(self.nombre))

    def get_siguiente(self):
        if self.ultimo_usado == None:
            return self.numero_inicial
        return self.ultimo_usado + 1

    def set_siguiente(self):
        self.ultimo_usado = self.get_siguiente()
        self.save()

    def save(self, *args, **kwargs):
        if (self.tipo_de_talonario == RECIBO):
            self.descripcion = "%s %010d al %010d" % (
            self.get_tipo_de_talonario_display(), self.numero_inicial, self.numero_final)
        else:
            self.descripcion = "%s %s-%s-%07d al %s-%s-%07d" % (
                self.get_tipo_de_talonario_display(), self.codigo_de_establecimiento,
                self.punto_de_expedicion, self.numero_inicial, self.codigo_de_establecimiento,
                self.punto_de_expedicion, self.numero_final
            )

        self.agotado = True if self.ultimo_usado == self.numero_final else False

        if self.agotado == True:
            self.activo = False

        if self.activo == True:
            talonarios = Talonario.objects.filter(sucursal=self.sucursal, agotado=False,
                                                  tipo_de_talonario=self.tipo_de_talonario)
            for talonario in talonarios:
                talonario.activo = False
                talonario.save()

        super(Talonario, self).save(*args, **kwargs)
