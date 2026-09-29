from django.shortcuts import get_object_or_404
import json
from django.http.response import JsonResponse
from django.http import HttpResponse

from clientes.models import *
from extra.globals import separador_de_miles


def get_cliente(request):
    cliente_id = (request.GET['clienteid']).replace(" ", "")
    result_set = []

    if cliente_id == "":
        return HttpResponse(json.dumps(result_set),
                            content_type='application/json')

    cliente = get_object_or_404(Cliente, pk=cliente_id)

    result_set.append({
        'limitedecredito': separador_de_miles(cliente.limite_de_credito) if cliente.limite_de_credito else '',

        'vendedor': cliente.vendedor_id if cliente.vendedor != None else '',
        'nombrevendedor': cliente.vendedor.get_full_name() if cliente.vendedor != None else '',
        'libredeimpuesto': '0' if cliente.libre_de_impuesto == True else '10',
        'condicion': str(cliente.condicion_de_venta),
        'total_deuda': str(cliente.get_total_deuda())
    })

    return HttpResponse(json.dumps(result_set),
                        content_type='application/json')


def get_clientedecontacto(request):
    contacto_id = request.GET.get('contacto_id', '')
    results = {}
    if contacto_id == "":
        return JsonResponse(results)

    contacto = get_object_or_404(Contacto, pk=contacto_id)
    cliente = Cliente.objects.get(pk=contacto.cliente_id)
    results.update({'cliente': str(cliente), 'cliente_id': contacto.cliente_id})

    return JsonResponse(results)
