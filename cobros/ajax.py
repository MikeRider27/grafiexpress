from django.shortcuts import get_object_or_404
from django.http.response import JsonResponse

from cobros.models import Recibo


def get_recibo(request):
    recibo_id = (request.GET['reciboid']).replace(" ", "")
    datos = {}

    if recibo_id == "":
        return JsonResponse(datos)

    recibo = get_object_or_404(Recibo, pk=recibo_id)
    datos.update({'subtotal': int(recibo.monto)})

    return JsonResponse(datos)
