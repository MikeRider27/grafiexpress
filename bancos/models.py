from django.db import models


class Banco(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return str(self.nombre)


class CuentaBancaria(models.Model):
    numero_de_cuenta = models.CharField(max_length=100)
    banco = models.ForeignKey(Banco)

    def __str__(self):
        return str(self.numero_de_cuenta + " - " + self.banco.nombre)
