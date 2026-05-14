import json
from django.http import HttpResponse, JsonResponse
from produccion.models import *
from extra.globals import separador_de_miles


def get_ordendetrabajo(request):
    orden_de_trabajo_id = (request.GET['otid']).replace(" ","")

    result_set = []

    if orden_de_trabajo_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    orden_de_trabajo = OrdenDeTrabajo.objects.get(pk = orden_de_trabajo_id)

    result_set.append({
        'ot': orden_de_trabajo.id,
        'nombre': orden_de_trabajo.nombre,
        'cantidad': separador_de_miles(orden_de_trabajo.cantidad),
        'cantidad_no_facturada': separador_de_miles(orden_de_trabajo.cantidad_no_facturada),
        'presupuesto': orden_de_trabajo.presupuesto_numero,
        'cliente': orden_de_trabajo.cliente.nombre,
        'fecha': orden_de_trabajo.fecha_de_ingreso.strftime("%d/%m/%Y"),
        'precio': separador_de_miles(orden_de_trabajo.precio_unitario),
        'orden_de_compra': orden_de_trabajo.orden_de_compra_del_cliente,
        'entregado': separador_de_miles(orden_de_trabajo.entregado),
        'restante': separador_de_miles(orden_de_trabajo.restante),
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_detalleordendetrabajo(request):
    detalle_orden_de_trabajo_id = (request.GET['dotid']).replace(" ","")

    result_set = []

    if detalle_orden_de_trabajo_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    detalle_orden_de_trabajo = DetalleOrdenDeTrabajo.objects.get(pk = detalle_orden_de_trabajo_id)

    result_set.append({
        #cabecera
        'ot': detalle_orden_de_trabajo.orden_de_trabajo.id,
        'cantidad': separador_de_miles(detalle_orden_de_trabajo.orden_de_trabajo.cantidad),
        'presupuesto': detalle_orden_de_trabajo.orden_de_trabajo.presupuesto_numero,
        'cliente': detalle_orden_de_trabajo.orden_de_trabajo.cliente.razon_social,
        'vendedor': str(detalle_orden_de_trabajo.orden_de_trabajo.cliente.vendedor_id) if detalle_orden_de_trabajo.orden_de_trabajo.cliente.vendedor_id !=None else '',
        'fecha': detalle_orden_de_trabajo.orden_de_trabajo.fecha_de_ingreso.strftime("%d/%m/%Y"),
        'precio': separador_de_miles(detalle_orden_de_trabajo.orden_de_trabajo.precio_unitario),
        'orden_de_compra': detalle_orden_de_trabajo.orden_de_trabajo.orden_de_compra_del_cliente,
        #detalle papel
        'detallecantidad': separador_de_miles(detalle_orden_de_trabajo.cantidad),
        'descripcion': detalle_orden_de_trabajo.material.descripcion,
        'gramaje': detalle_orden_de_trabajo.material.gramaje.descripcion if detalle_orden_de_trabajo.material.gramaje != None else '',
        'resma': detalle_orden_de_trabajo.material.resma.descripcion if detalle_orden_de_trabajo.material.resma != None else '',
        # 'precio': separador_de_miles(detalle_orden_de_trabajo.material.costo_actual),
        #detalle del item
        'nombre': detalle_orden_de_trabajo.descripcion,
        'detalleentregado': separador_de_miles(detalle_orden_de_trabajo.entregado),
        'detallerestante': separador_de_miles(detalle_orden_de_trabajo.restante),
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_papelcosto(request):
    papelcosto_id = (request.GET['id']).replace(" ","")
    print ("ajax papelcosto_id (%s)" % papelcosto_id)

    result_set = []

    if papelcosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    papelcosto = PapelCosto.objects.get(pk = papelcosto_id)

    result_set.append({
        'cantidad': separador_de_miles(papelcosto.cantidad - papelcosto.cantidad_en_oc),
        'precio': separador_de_miles(papelcosto.precio_unitario),
        'subtotal': separador_de_miles(papelcosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_preprensacosto(request):
    preprensacosto_id = (request.GET['id']).replace(" ","")
    print ("ajax preprensacosto_id (%s)" % preprensacosto_id)

    result_set = []

    if preprensacosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    preprensacosto = PreprensaCosto.objects.get(pk = preprensacosto_id)

    result_set.append({
        'cantidad':separador_de_miles(preprensacosto.cantidad - preprensacosto.cantidad_en_oc),
        'precio':separador_de_miles(preprensacosto.precio_unitario),
        'subtotal':separador_de_miles(preprensacosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_troquelcosto(request):
    troquelcosto_id = (request.GET['id']).replace(" ","")
    print ("ajax troquelcosto_id (%s)" % troquelcosto_id)

    result_set = []

    if troquelcosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    troquelcosto = TroquelCosto.objects.get(pk = troquelcosto_id)

    result_set.append({
        'cantidad':separador_de_miles(1),
        'precio':separador_de_miles(troquelcosto.precio),
        'subtotal':separador_de_miles(troquelcosto.precio)
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_posprensaserviciocosto(request):
    posprensaserviciocosto_id = (request.GET['id']).replace(" ","")
    print ("ajax posprensaserviciocosto_id (%s)" % posprensaserviciocosto_id)

    result_set = []

    if posprensaserviciocosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    posprensaserviciocosto = PosprensaServicioCosto.objects.get(pk = posprensaserviciocosto_id)

    result_set.append({
        'cantidad':separador_de_miles(posprensaserviciocosto.cantidad - posprensaserviciocosto.cantidad_en_oc),
        'precio':separador_de_miles(posprensaserviciocosto.precio_unitario),
        'subtotal':separador_de_miles(posprensaserviciocosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_posprensamaterialcosto(request):
    posprensamaterialcosto_id = (request.GET['id']).replace(" ","")
    print ("ajax posprensamaterialcosto_id (%s)" % posprensamaterialcosto_id)

    result_set = []

    if posprensamaterialcosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    posprensamaterialcosto = PosprensaMaterialCosto.objects.get(pk = posprensamaterialcosto_id)

    result_set.append({
        'cantidad':separador_de_miles(posprensamaterialcosto.cantidad - posprensamaterialcosto.cantidad_en_oc),
        'precio':separador_de_miles(posprensamaterialcosto.precio_unitario),
        'subtotal':separador_de_miles(posprensamaterialcosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_posprensaotroserviciocosto(request):
    posprensaotroserviciocosto_id = (request.GET['id']).replace(" ","")
    print ("ajax posprensaotroserviciocosto_id (%s)" % posprensaotroserviciocosto_id)

    result_set = []

    if posprensaotroserviciocosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    posprensaotroserviciocosto = PosprensaOtroServicioCosto.objects.get(pk = posprensaotroserviciocosto_id)

    result_set.append({
        'cantidad':separador_de_miles(posprensaotroserviciocosto.cantidad - posprensaotroserviciocosto.cantidad_en_oc),
        'precio':separador_de_miles(posprensaotroserviciocosto.precio_unitario),
        'subtotal':separador_de_miles(posprensaotroserviciocosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_datosdebolsacosto(request):
    datosdebolsacosto_id = (request.GET['id']).replace(" ","")
    print ("ajax datosdebolsacosto_id (%s)" % datosdebolsacosto_id)

    result_set = []

    if datosdebolsacosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    datosdebolsacosto = DatosDeBolsaCosto.objects.get(pk = datosdebolsacosto_id)

    result_set.append({
        'cantidad':separador_de_miles(datosdebolsacosto.cantidad - datosdebolsacosto.cantidad_en_oc),
        'precio':separador_de_miles(datosdebolsacosto.precio_unitario),
        'subtotal':separador_de_miles(datosdebolsacosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_revistacosto(request):
    revistacosto_id = (request.GET['id']).replace(" ","")
    print ("ajax revistacosto_id (%s)" % revistacosto_id)

    result_set = []

    if revistacosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    revistacosto = RevistaCosto.objects.get(pk = revistacosto_id)

    result_set.append({
        'cantidad':separador_de_miles(revistacosto.cantidad - revistacosto.cantidad_en_oc),
        'precio':separador_de_miles(revistacosto.precio_unitario),
        'subtotal':separador_de_miles(revistacosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_compuestocosto(request):
    compuestocosto_id = (request.GET['id']).replace(" ","")
    print ("ajax compuestocosto_id (%s)" % compuestocosto_id)

    result_set = []

    if compuestocosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    compuestocosto = CompuestoCosto.objects.get(pk = compuestocosto_id)

    result_set.append({
        'cantidad':separador_de_miles(compuestocosto.cantidad - compuestocosto.cantidad_en_oc),
        'precio':separador_de_miles(compuestocosto.precio_unitario),
        'subtotal':separador_de_miles(compuestocosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_plastificadocosto(request):
    plastificadocosto_id = (request.GET['id']).replace(" ","")
    print ("ajax plastificadocosto_id (%s)" % plastificadocosto_id)

    result_set = []

    if plastificadocosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    plastificadocosto = PlastificadoCosto.objects.get(pk = plastificadocosto_id)

    result_set.append({
        'cantidad':separador_de_miles(plastificadocosto.cantidad - plastificadocosto.cantidad_en_oc),
        'precio':separador_de_miles(plastificadocosto.precio_unitario),
        'subtotal':separador_de_miles(plastificadocosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_otrogastocosto(request):
    otrogastocosto_id = (request.GET['id']).replace(" ","")
    print ("ajax otrogastocosto_id (%s)" % otrogastocosto_id)

    result_set = []

    if otrogastocosto_id == "":
        return HttpResponse(json.dumps(result_set), 
                            content_type='application/json')

    otrogastocosto = OtroGastoCosto.objects.get(pk = otrogastocosto_id)

    result_set.append({
        'cantidad':separador_de_miles(otrogastocosto.cantidad - otrogastocosto.cantidad_en_oc),
        'precio':separador_de_miles(otrogastocosto.precio_unitario),
        'subtotal':separador_de_miles(otrogastocosto.get_subtotal())
    })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')


def get_maquina(request):
    maquina_id = (request.GET['maquina_id']).replace(" ", "")
    datos = {}

    if maquina_id == "":
        return JsonResponse(datos)

    maquina = Maquina.objects.get(pk=maquina_id)
    if maquina.tercerizado:
        tercerizado = 1
    else:
        tercerizado = 0
    fecha, hora = maquina.get_disponibilidad()

    hora_disponible = str(hora) + ':00'
    datos.update({'fecha_disponible': fecha.strftime('%d/%m/%Y'), 'hora_disponible': hora_disponible,
                  'pasadas_por_hora': int(maquina.pasadas_por_hora), 'tercerizado': tercerizado})

    return JsonResponse(datos)


def get_detalle_proceso(request):
    detalle_proceso_id = (request.GET['detalle_proceso_id']).replace(" ", "")
    datos = {}

    if detalle_proceso_id == "":
        return JsonResponse(datos)

    detalle_proceso = DetalleProceso.objects.get(pk=detalle_proceso_id)
    fecha_de_inicio = detalle_proceso.fecha_de_inicio
    hora_de_inicio = detalle_proceso.hora_de_inicio
    fecha_de_finalizacion = detalle_proceso.fecha_de_finalizacion
    hora_de_finalizacion = detalle_proceso.hora_de_finalizacion
    pliegos = detalle_proceso.pliegos_a_realizar
    maquina = detalle_proceso.maquina
    datos.update({'fecha_de_inicio': fecha_de_inicio.strftime('%d/%m/%Y'), 'hora_de_inicio': hora_de_inicio,
                  'fecha_de_finalizacion': fecha_de_finalizacion.strftime('%d/%m/%Y'), 'hora_de_finalizacion': hora_de_finalizacion,
                  'pliegos': pliegos, 'fecha_disponible_maquina': maquina.fecha_disponible, 'hora_disponible_maquina': maquina.hora_disponible})

    return JsonResponse(datos)


def get_detalle_programacion(request):
    detalle_programacion_id = (request.GET['detalle_programacion_id']).replace(" ", "")
    datos = {}

    if detalle_programacion_id == "":
        return JsonResponse(datos)

    detalle_programacion = DetalleProgramacion.objects.get(pk=detalle_programacion_id)
    fecha_de_inicio = detalle_programacion.fecha_de_inicio
    hora_de_inicio = detalle_programacion.hora_de_inicio
    fecha_de_finalizacion = detalle_programacion.fecha_de_finalizacion
    hora_de_finalizacion = detalle_programacion.hora_de_finalizacion

    datos.update({'fecha_de_inicio': fecha_de_inicio.strftime('%d/%m/%Y'), 'hora_de_inicio': hora_de_inicio,
                  'fecha_de_finalizacion': fecha_de_finalizacion.strftime('%d/%m/%Y'),
                  'hora_de_finalizacion': hora_de_finalizacion})

    return JsonResponse(datos)
