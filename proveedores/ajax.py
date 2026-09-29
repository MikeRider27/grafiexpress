from django.shortcuts import get_object_or_404
import json

from django.http import HttpResponse

from proveedores.models import *
from extra.globals import separador_de_miles


def get_proveedor(request):
    proveedor_id = (request.GET['proveedorid']).replace(" ", "")

    result_set = []

    if proveedor_id == "":
        return HttpResponse(json.dumps(result_set),
                            content_type='application/json')

    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)

    result_set.append({
        'contacto': proveedor.contacto,
        'telefono': proveedor.telefono,
        'condicion': proveedor.condicion_de_compra,
    })

    return HttpResponse(json.dumps(result_set),
                        content_type='application/json')
