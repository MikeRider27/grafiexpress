# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from extra.validators import validar_archivo_subido
from django.views.generic.dates import timezone_today

from clientes.models import Cliente
from comercial.constants import EstadoPresupuestos


def get_file_path(instance, filename):
    file_path = 'archivos/' + 'presupuesto_' + str(instance.id)
    return file_path


class Presupuesto(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT)
    contacto = models.ForeignKey('clientes.Contacto', on_delete=models.PROTECT)
    fecha_hora_creacion = models.DateField("Fecha de Creacion", null=True, blank=True, editable=False)
    estado = models.CharField(max_length=3, choices=EstadoPresupuestos.ESTADOS, default=EstadoPresupuestos.PENDIENTE)
    trabajo = models.CharField(max_length=200)
    repeticion = models.BooleanField(default=False)
    cambios = models.BooleanField(default=False)
    corte_final = models.CharField(max_length=200, blank=True)
    dimensiones_x = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="X")
    dimensiones_y = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Y")
    dimensiones_z = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Z")
    color_seleccion_frente = models.CharField(max_length=10, blank=True, null=True, verbose_name="frente")
    color_seleccion_dorso = models.CharField(max_length=10, blank=True, null=True, verbose_name="dorso")
    color_pantone_frente = models.CharField(max_length=10, blank=True, null=True, verbose_name="frente")
    color_pantone_dorso = models.CharField(max_length=10, blank=True, null=True, verbose_name="dorso")
    terminacion = models.CharField(max_length=200, blank=True)
    troquelado = models.BooleanField(default=False)
    hojalado = models.BooleanField(default=False)
    despuntado = models.BooleanField(default=False)
    plastificado = models.BooleanField(default=False)
    ambas_caras = models.BooleanField(default=False)
    rel_fuego = models.BooleanField(default=False)
    numerado = models.BooleanField(default=False)
    otros = models.CharField(max_length=200, help_text="especificar", blank=True)
    observaciones = models.TextField(max_length=400, blank=True, null=True)
    adjunto = models.FileField(upload_to=get_file_path, null=True, blank=True, validators=[validar_archivo_subido])

    class Meta:
        verbose_name_plural = "Presupuestos"

    def __str__(self):
        return str(str(self.id) + ": " + self.trabajo + '. -' + self.cliente.nombre)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.fecha_hora_creacion = datetime.now()

        if self.adjunto:
            self.estado = EstadoPresupuestos.PRESUPUESTADO

        super(Presupuesto, self).save(*args, **kwargs)


class CantidadPresupuesto(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()


class MaterialPresupuesto(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE)
    material = models.CharField('Material', max_length=80)
    precio = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)


class Canal(models.Model):
    nombre = models.CharField("Nombre", max_length=50)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name_plural = "Canales"


class Actividad(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT)
    contacto = models.ForeignKey('clientes.Contacto', on_delete=models.PROTECT)
    marca = models.ForeignKey('clientes.Marca', null=True, blank=True)
    presupuesto = models.ForeignKey(Presupuesto, null=True, blank=True)
    canal = models.ForeignKey(Canal, on_delete=models.PROTECT, null=True)
    fecha = models.DateField('Fecha', default=datetime.today)
    hora = models.TimeField('Hora', null=True, blank=True)
    titulo = models.CharField(max_length=150, null=True, blank=True)
    resumen = models.TextField(max_length=350)
    realizado = models.BooleanField(default=True, help_text="Desmarcar cuando es una actividad programada")
    documentos = models.FileField(upload_to=get_file_path, null=True, blank=True, validators=[validar_archivo_subido])
    vendedor = models.ForeignKey("funcionarios.Funcionario", null=True, blank=True)
    fecha_creacion = models.DateField("Fecha de Creacion", default=datetime.now, editable=False)

    def image_tag(self):
        return '<img src="%s" />' % self.documentos.url

    image_tag.short_description = "Documento"
    image_tag.allow_tags = True

    class Meta:
        verbose_name_plural = "CRM"

    def get_cliente_contacto(self):
        cliente = Cliente.objects.get(pk=self.contacto.cliente.pk)
        return cliente

    def get_self_path(self):
        return self.documentos.path

    def __str__(self):
        return str(str(self.id) + ': ' + self.cliente.nombre + ' - ')
