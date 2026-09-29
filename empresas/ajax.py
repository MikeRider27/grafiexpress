from django.shortcuts import get_object_or_404
import json
from django.http import HttpResponse
from empresas.models import *

def get_empresa(request):
    empresa_id = (request.GET['empresaid']).replace(" ","")

    result_set = []

    if empresa_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    empresa = get_object_or_404(Empresa, pk=empresa_id)

    result_set.append({
        'timbrado': empresa.timbrado
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_talonario(request):
    talonario_id = (request.GET['talonarioid']).replace(" ","")

    result_set = []

    if talonario_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    talonario = get_object_or_404(Talonario, pk=talonario_id)

    result_set.append({
        'timbrado': talonario.timbrado.numero if talonario.tipo_de_talonario != RECIBO else '',
        'empresa': talonario.sucursal.empresa.nombre,
        'sucursal': talonario.sucursal.nombre,
        'numero': "%s-%s-%07d" % (talonario.codigo_de_establecimiento, talonario.punto_de_expedicion, talonario.get_siguiente()) if talonario.tipo_de_talonario != RECIBO else str(talonario.get_siguiente())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')
