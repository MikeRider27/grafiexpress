#!/usr/bin/python
# -*- coding: utf-8 -*-
from empresas.models import *
from datetime import date

def set_vencimiento_timbrado():
	timbrados = Timbrado.objects.filter(fecha_de_vencimiento__lte=date.today(), activo=True)
	for timbrado in timbrados:
		timbrado.activo=False
		timbrado.save()

	print ('hola mundo schedule')