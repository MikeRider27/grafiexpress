from django.db import models
from datetime import date
from bancos.models import *
from extra.globals import separador_de_miles


class ChequeRecibido(models.Model):
    numero = models.CharField(max_length=100)
    banco = models.ForeignKey('bancos.Banco')
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    es_diferido = models.BooleanField(default=False)
    fecha_de_emision = models.DateField(default=date.today)
    fecha_de_cobro = models.DateField(null=True, blank=True)

    def __str__(self):
        return str("Cheque " + self.numero + " | Gs." + separador_de_miles(self.monto))


class ChequeEmitido(models.Model):
    numero = models.CharField(max_length=100)
    banco = models.ForeignKey('bancos.Banco')
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    es_diferido = models.BooleanField(default=False)
    fecha_de_emision = models.DateField(default=date.today)
    fecha_de_cobro = models.DateField(null=True, blank=True)

    def __str__(self):
        return str("Cheque " + self.numero + " | Gs." + separador_de_miles(self.monto))
