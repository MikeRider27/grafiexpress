from django.db import models

# Create your models here.
class Automovil(models.Model):
    marca = models.CharField(max_length=100)
    rua = models.CharField(max_length=100, verbose_name="numero de registro unico del automotor")
    rua_remolque = models.CharField(max_length=100, blank=True, null=True, verbose_name="numero de registro unico del automotor de remolquetracto o semiremolque")

    def __str__(self):
        return str(self.marca + ' - ' + self.rua)
