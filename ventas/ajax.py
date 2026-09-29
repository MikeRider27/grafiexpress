from django.shortcuts import get_object_or_404
import json

from datetime import datetime
from django.http.response import HttpResponse
from django.utils import timezone

from clientes.models import Cliente
from extra.globals import separador_de_miles

from ventas.models import *
from extra.globals import *


def get_detalle_de_remision(request):
    id_remisiones = request.GET.get('id_remisiones')
    response = []
    remisiones = id_remisiones.split(',')
    if id_remisiones == "":
        return HttpResponse(json.dumps(response), content_type='application/json')

    for remision in remisiones:
        detalles = DetalleDeRemision.objects.filter(remision_id=remision)

        for detalle in detalles:
            response.append({
                'id': str(detalle.orden_de_trabajo_id),
                'ot': str(detalle.orden_de_trabajo),
                'descripcion': str(detalle.orden_de_trabajo.nombre),
                #'iva': "IVA 10%",
                'cantidad': separador_de_miles(detalle.cantidad),
                'precio_unitario': separador_de_miles(detalle.orden_de_trabajo.precio_unitario),
                'subtotal': separador_de_miles(detalle.cantidad * detalle.orden_de_trabajo.precio_unitario),
                'orden_de_compra': str(detalle.orden_de_trabajo.orden_de_compra_del_cliente)
            })

    return HttpResponse(json.dumps(response), content_type='application/json')


def get_detalle2_de_remision(request):
    id_remisiones = request.GET.get('id_remisiones')
    response = []
    remisiones = id_remisiones.split(',')
    if id_remisiones == "":
        return HttpResponse(json.dumps(response), content_type='application/json')

    for remision in remisiones:
        detalles = DetalleDeRemision2.objects.filter(remision_id=remision)

        for detalle in detalles:
            response.append({
                'id': str(detalle.detalle_orden_de_trabajo_id),
                'dot': str(detalle.detalle_orden_de_trabajo),
                'descripcion': str(detalle.detalle_orden_de_trabajo.descripcion),
                #'iva': "IVA 10%",
                'cantidad': separador_de_miles(detalle.cantidad),
                'precio_unitario': separador_de_miles(detalle.detalle_orden_de_trabajo.get_precio_unitario()),
                'subtotal': separador_de_miles(detalle.detalle_orden_de_trabajo.get_subtotal()),
                'orden_de_compra': str(detalle.detalle_orden_de_trabajo.orden_de_trabajo.orden_de_compra_del_cliente)
            })

    return HttpResponse(json.dumps(response), content_type='application/json')


def get_venta(request):
    venta_id = (request.GET['ventaid']).replace(" ", "")

    result_set = []

    if venta_id == "":
        return HttpResponse(json.dumps(result_set),
                            content_type='application/json')

    venta = get_object_or_404(Venta, pk=venta_id)

    result_set.append({
        'total': separador_de_miles(venta.total),
        'pagado': separador_de_miles(venta.pagado),
        'saldo': separador_de_miles(venta.saldo)
    })

    return HttpResponse(json.dumps(result_set),
                        content_type='application/json')


def get_plazo_credito(request):
    cliente_id = request.GET.get('cliente_id', '')
    results = {}

    if cliente_id == "":
        return HttpResponse(json.dumps(results), content_type='application/json')

    cliente = get_object_or_404(Cliente, pk=cliente_id)
    import re
    plazo_credito = int((re.search(r'\d+', cliente.plazo_de_credito or '0')).group()) or 30
    fecha = timezone.now()
    fecha = fecha + datetime.timedelta(days=plazo_credito)
    results.update({
        'plazo_credito': int((re.search(r'\d+', cliente.plazo_de_credito or '0')).group()) or 30,
        'fecha_vencimiento_credito': fecha.strftime("%d/%m/%Y")
    })

    return HttpResponse(json.dumps(results), content_type='application/json')
