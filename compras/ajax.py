from django.shortcuts import get_object_or_404
import json

from django.http.response import HttpResponse
from extra.globals import separador_de_miles

from compras.models import *
from extra.globals import *
from proveedores.models import Proveedor
from django.utils import timezone


def get_compra(request):
    compra_id = (request.GET['compraid']).replace(" ", "")

    result_set = []

    if compra_id == "":
        return HttpResponse(json.dumps(result_set),
                            content_type='application/json')

    compra = get_object_or_404(Compra, pk=compra_id)

    result_set.append({
        'total': separador_de_miles(compra.total),
        'pagado': separador_de_miles(compra.pagado),
        'saldo': separador_de_miles(compra.saldo)
    })

    return HttpResponse(json.dumps(result_set),
                        content_type='application/json')


def get_plazo_credito(request):
    proveedor_id = request.GET.get('proveedor_id', '')
    results = {}

    if proveedor_id == "":
        return HttpResponse(json.dumps(results), content_type='application/json')

    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    import re
    plazo_credito = int((re.search(r'\d+', proveedor.plazo_de_credito or '0')).group()) or 30
    fecha = timezone.now()
    fecha = fecha + datetime.timedelta(days=plazo_credito)
    results.update({
        'plazo_credito': int((re.search(r'\d+', proveedor.plazo_de_credito or '0')).group()) or 30,
        'fecha_vencimiento_credito': fecha.strftime("%d/%m/%Y")
    })

    return HttpResponse(json.dumps(results), content_type='application/json')
