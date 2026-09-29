# -*- coding: utf-8 -*-

from django.db import models

# Create your models here.
class Maquina(models.Model):
    class Meta:
        verbose_name = "máquina"

    descripcion = models.CharField(max_length=150, verbose_name="descripción")
    precio = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return str(self.descripcion)