# -*- coding: utf-8 -*-

from django.db import models
from datetime import date


# Create your models here.
class Deposito(models.Model):
	nombre = models.CharField(max_length=100)

	def __str__(self):
		return self.nombre




class Alta(models.Model):
	deposito = models.ForeignKey(Deposito)
	fecha = models.DateField(default=date.today)
	funcionario = models.ForeignKey("funcionarios.Funcionario", null=True, blank=True)

	def __str__(self):
		return "[Nro.: " + str(self.id) + "] - fecha: " + self.fecha.strftime("%d/%m/%Y") 

class DetalleAlta(models.Model):
	alta = models.ForeignKey(Alta)
	material = models.ForeignKey("materiales.Material")
	cantidad = models.DecimalField(max_digits=15, decimal_places=2)
	motivo = models.CharField(max_length=500, null=True, blank=True)

	def __str__(self):
		return str(self.material)

	def save(self, *args, **kwargs):
		super(DetalleAlta, self).save(*args, **kwargs)
		self.material.actualizar_stock()

	def delete(self, *args, **kwargs):
		material = self.material
		alta = self.alta

		super(DetalleAlta, self).delete(*args, **kwargs)
		
		material.actualizar_stock()	
		detalles = DetalleAlta.objects.filter(alta_id=alta.id)
		if not detalles:
			alta.delete()

class Baja(models.Model):
	deposito = models.ForeignKey(Deposito)
	fecha = models.DateField(default=date.today)
	funcionario = models.ForeignKey("funcionarios.Funcionario", null=True, blank=True)

	def __str__(self):
		return "[Nro.: " + str(self.id) + "] - fecha: " + self.fecha.strftime("%d/%m/%Y") 

class DetalleBaja(models.Model):
	baja = models.ForeignKey(Baja)
	material = models.ForeignKey("materiales.Material")
	cantidad = models.DecimalField(max_digits=15, decimal_places=2)
	motivo = models.CharField(max_length=500, null=True, blank=True)

	def __str__(self):
		return str(self.material)

	def save(self, *args, **kwargs):
		super(DetalleBaja, self).save(*args, **kwargs)
		self.material.actualizar_stock()

	def delete(self, *args, **kwargs):
		material = self.material
		baja = self.baja

		super(DetalleBaja, self).delete(*args, **kwargs)
		
		material.actualizar_stock()	
		detalles = DetalleBaja.objects.filter(baja_id=baja.id)
		if not detalles:
			baja.delete()

class Retiro(models.Model):
	fecha = models.DateField(default=date.today)
	funcionario = models.ForeignKey("funcionarios.Funcionario", null=True, blank=True)

	def __str__(self):
		return "[Nro.: " + str(self.id) + "] - fecha: " + self.fecha.strftime("%d/%m/%Y") 

class DetalleRetiro(models.Model):
	retiro = models.ForeignKey(Retiro)
	orden_de_trabajo = models.ForeignKey("produccion.OrdenDeTrabajo", null=True, blank=True)
	factura = models.ForeignKey("ventas.Venta", null=True, blank=True)
	deposito = models.ForeignKey(Deposito)
	material = models.ForeignKey("materiales.Material")
	cantidad = models.DecimalField(max_digits=15, decimal_places=2)

	def __str__(self):
		return str(self.material)


	def save(self, *args, **kwargs):
		super(DetalleRetiro, self).save(*args, **kwargs)
		self.material.actualizar_stock()

	def delete(self, *args, **kwargs):
		material = self.material
		retiro = self.retiro

		super(DetalleRetiro, self).delete(*args, **kwargs)
		
		material.actualizar_stock()
		detalles = DetalleRetiro.objects.filter(retiro_id=retiro.id)
		if not detalles:
			retiro.delete()

class Devolucion(models.Model):
	fecha = models.DateField(default=date.today)
	funcionario = models.ForeignKey("funcionarios.Funcionario", null=True, blank=True)
	retiro = models.ForeignKey(Retiro, null=True, blank=False)

	def __str__(self):
		return "[Nro.: " + str(self.id) + "] - fecha: " + self.fecha.strftime("%d/%m/%Y") 

class DetalleDevolucion(models.Model):
	devolucion = models.ForeignKey(Devolucion)
	detalle_retiro = models.ForeignKey(DetalleRetiro, verbose_name="Material", null=True, blank=False)
	cantidad = models.DecimalField(max_digits=15, decimal_places=2)
	deposito = models.ForeignKey(Deposito)


	def __str__(self):
		return str(self.detalle_retiro.material)

	def save(self, *args, **kwargs):
		super(DetalleDevolucion, self).save(*args, **kwargs)
		self.detalle_retiro.material.actualizar_stock()

	def delete(self, *args, **kwargs):
		material = self.detalle_retiro.material
		devolucion = self.devolucion

		super(DetalleDevolucion, self).delete(*args, **kwargs)
		
		material.actualizar_stock()	
		detalles = DetalleDevolucion.objects.filter(devolucion_id=devolucion.id)
		if not detalles:
			devolucion.delete()