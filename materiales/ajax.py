from django.shortcuts import get_object_or_404
import json
from django.http import HttpResponse
from materiales.models import *
from extra.globals import *

def get_material(request):
    material_id = (request.GET['materialid']).replace(" ", "")

    result_set = []

    if material_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    material = get_object_or_404(Material, pk=material_id)

    result_set.append({
        'material': material.descripcion,
        'gramaje': material.gramaje.descripcion if material.gramaje != None else '',
        'resma':  material.resma.descripcion if material.resma != None else '',
        'marca': material.marca,
        'iva': material.iva,
        'precio': separador_de_miles(material.costo_actual) if material.costo_actual != None else '0'
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')

