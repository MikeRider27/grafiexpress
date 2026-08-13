# -*- coding: utf-8 -*-
from decimal import Decimal

from datetime import datetime
from django.db.models.aggregates import Sum

from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from common.jasper import reportes
from extra.globals import *
from ventas.models import *

from num2words import num2words

"""
    Bitacora del capitán, fecha espacial Miercoles 4 de enero de 2017.
    Nunca olvidar que en reportlab comienza a dibujar justo debajo del 
    punto en las coordenadas (X,Y)
"""


def imprimir_remision_grafiexpress(request, pk):
    # Crear el objeto HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=remision_grafiexpress.pdf'

    # Crear el objeto PDF, usando el objeto response
    p = canvas.Canvas(response)

    # Fijar tamaño de la hoja
    p.setPageSize((20.1*cm, 23.8*cm))

    # Fijar tipo y tamaño de letra
    p.setFont("Times-Roman", 7)


    ################ Escribir textos flotantes en coordenadas (X,Y) ################

    remision = Remision.objects.get(pk=pk)

    # fecha de emision
    p.drawString(4*cm,19.75*cm, remision.fecha_de_emision.strftime("%d/%m/%Y")) 

    # Nombre o razon social
    p.drawString(4*cm,18.95*cm, remision.cliente.razon_social)
    
    # RUC o CI
    p.drawString(15*cm,18.95*cm, remision.cliente.ruc)
    
    # Domicilio
    p.drawString(3*cm,18.55*cm, remision.cliente.direccion)

    # Motivo de traslado
    p.drawString(3.5*cm, 17.75*cm, remision.motivo_del_traslado)

    # Comprobante de Venta
    p.drawString(13.7*cm, 17.75*cm, remision.comprobante_de_venta)

    # Numero de Comprobante de Venta
    p.drawString(4*cm, 17.35*cm, remision.numero_de_comprobante_de_venta)

    # Nro de Timbrado
    p.drawString(13.1*cm, 17.35*cm, remision.numero_de_timbrado)

    # Fecha de expedicion
    p.drawString(3.4*cm, 16.95*cm, remision.fecha_de_expedicion.strftime('%d/%m/%Y'))

    # Fecha de Inicio de traslado
    p.drawString(4.2*cm, 16.55*cm, remision.fecha_de_inicio_del_traslado.strftime('%d/%m/%Y'))

    # Fecha estimada de termino de traslado
    p.drawString(15.4*cm, 16.55*cm, remision.fecha_estimada_de_termino_del_traslado.strftime('%d/%m/%Y'))

    # Direccion del punto de partida
    p.drawString(4.4*cm, 16.3*cm, remision.direccion_del_punto_de_partida)

    # Ciudad de partida
    p.drawString(2.2*cm, 16*cm, remision.ciudad_de_partida)

    # Departamento de partida
    p.drawString(13*cm, 16*cm, remision.departamento_de_partida)

    # Direccion del punto de llegada
    p.drawString(4.4*cm, 15.6*cm, remision.direccion_del_punto_de_llegada)

    # Ciudad de llegada
    p.drawString(2.2*cm, 15.3*cm, remision.ciudad_de_llegada)

    # Departamento de llegada
    p.drawString(13*cm, 15.3*cm, remision.departamento_de_llegada)

    # Kilometros estimados de recorrido
    p.drawString(4.9*cm, 15*cm, str(remision.kilometros_estimados_de_recorrido) if remision.kilometros_estimados_de_recorrido!=None else '')
    
    # Cambio de fecha de termino del traslado o punto de llegada
    p.drawString(7.5*cm, 14.6*cm, remision.cambio_de_fecha_de_termino_del_traslado_o_punto_de_llegada)
    
    # Motivo
    p.drawString(2.2*cm, 14.3*cm, remision.motivo)
    
    if (remision.vehiculo != None):
        # DATOS DEL VEHICULO DE TRANSPORTE
        # Marca
        p.drawString(3.3*cm, 13.4*cm, remision.vehiculo.marca)
        # Registro unico del automotor
        p.drawString(6.1*cm, 13.1*cm, remision.vehiculo.rua)
        # Registro unico del automotor del Remolque
        p.drawString(9.5*cm, 12.6*cm, remision.vehiculo.rua_remolque)

    if (remision.chofer != None):
        # DATOS DEL CONDUCTOR DEL VEHICULO
        #   Nombre y Apellidos
        nombre = remision.chofer.nombres + ' ' + remision.chofer.apellidos
        p.drawString(4.7*cm, 12*cm, nombre)
        # RUC o CIC
        p.drawString(14.4*cm, 12*cm, remision.chofer.ruc)
        # Domicilio
        p.drawString(2.3*cm, 11.6*cm, remision.chofer.direccion)


    linea = 0
    alto_de_celda = 0.5

    detalles = DetalleDeRemision.objects.filter(remision_id=remision.id)
    for detalle in detalles:
        p.drawString(1.2*cm, (10-(linea*alto_de_celda))*cm, separador_de_miles(detalle.cantidad))
        p.drawString(4*cm, (10-(linea*alto_de_celda))*cm, detalle.unidad_de_medida.simbolo if detalle.unidad_de_medida != None else "")
        p.drawString(5.5*cm, (10-(linea*alto_de_celda))*cm, detalle.descripcion)
        linea = linea + 1

    detalles2 = DetalleDeRemision2.objects.filter(remision_id=remision.id)
    for detalle in detalles2:
        p.drawString(1.2*cm, (10-(linea*alto_de_celda))*cm, separador_de_miles(detalle.cantidad))
        p.drawString(4*cm, (10-(linea*alto_de_celda))*cm, detalle.unidad_de_medida.simbolo if detalle.unidad_de_medida != None else "")
        p.drawString(5.5*cm, (10-(linea*alto_de_celda))*cm, detalle.descripcion)
        linea = linea + 1

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response


def imprimir_venta_grafiexpress(request, pk):
    # Crear el objeto HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=venta_grafiexpress.pdf'

    # Crear el objeto PDF, usando el objeto response
    p = canvas.Canvas(response)

    # Fijar tamaño de la hoja
    p.setPageSize((20.5*cm, 28*cm))

    # Fijar tipo y tamaño de letra
    p.setFont("Times-Roman", 8)

    ################ Escribir textos flotantes en coordenadas (X,Y) ################

    venta = Venta.objects.get(pk=pk)

    # fecha
    p.drawString(2.5*cm, 22.45*cm, venta.fecha_de_emision.strftime("%d"))  # dia

    numero_del_mes = int(venta.fecha_de_emision.strftime("%m"))  # mes
    if (numero_del_mes == 1):
        p.drawString(4.5*cm, 22.45*cm, 'enero')
    elif (numero_del_mes == 2):
        p.drawString(4.5*cm, 22.45*cm, 'febrero')
    elif (numero_del_mes == 3):
        p.drawString(4.5*cm, 22.45*cm, 'marzo')
    elif (numero_del_mes == 4):
        p.drawString(4.5*cm, 22.45*cm, 'abril')
    elif (numero_del_mes == 5):
        p.drawString(4.5*cm, 22.45*cm, 'mayo')
    elif (numero_del_mes == 6):
        p.drawString(4.5*cm, 22.45*cm, 'junio')
    elif (numero_del_mes == 7):
        p.drawString(4.5*cm, 22.45*cm, 'julio')
    elif (numero_del_mes == 8):
        p.drawString(4.5*cm, 22.45*cm, 'agosto')
    elif (numero_del_mes == 9):
        p.drawString(4.5*cm, 22.45*cm, 'setiembre')
    elif (numero_del_mes == 10):
        p.drawString(4.5*cm, 22.45*cm, 'octubre')
    elif (numero_del_mes == 11):
        p.drawString(4.5*cm, 22.45*cm, 'noviembre')
    elif (numero_del_mes == 12):
        p.drawString(4.5*cm, 22.45*cm, 'diciembre')

    p.drawString(8.5*cm, 22.45*cm, venta.fecha_de_emision.strftime("%Y"))  # año

    # condicion de la venta
    if (venta.condicion == CONTADO):
        p.drawString(15*cm, 22.45*cm, 'X')  # contado
    else:
        p.drawString(17*cm, 22.45*cm, 'X')  # credito

    # clientesupplier_invoice_number
    p.drawString(2.5*cm, 21.95*cm, venta.cliente.razon_social)

    # condicion de pago
    # p.drawString(15.5*cm,21.95*cm, venta.condicion_de_pago)

    # Direccion
    p.drawString(2.5*cm, 21.25*cm, venta.cliente.direccion)

    # RUC o CI
    p.drawString(14.5*cm, 21.25*cm, venta.cliente.ruc)

    # Remisiones
    cadena_de_remisiones = ''
    for remision in venta.remision.all():
        cadena_de_remisiones = cadena_de_remisiones + remision.get_numero_de_remision()
    p.drawString(3*cm, 20.55*cm, cadena_de_remisiones)

    # Telefono
    p.drawString(13.5*cm, 20.55*cm, venta.cliente.telefono)

    # subtotal
    p.drawString(13*cm, 10.2*cm, separador_de_miles(venta.get_subtotal_exenta()))  # exentas
    p.drawString(15*cm, 10.2*cm, separador_de_miles(venta.get_subtotal_iva_5()))  # iva 5%
    p.drawString(16.5*cm, 10.2*cm, separador_de_miles(venta.get_subtotal_iva_10()))  # iva 10%

    # total
    p.drawString(16.5*cm, 9.5*cm, separador_de_miles(venta.total))

    # ivas
    p.drawString(3*cm, 8.7*cm, separador_de_miles(venta.get_iva_5()))  # total iva 5
    p.drawString(7*cm, 8.7*cm, separador_de_miles(venta.get_iva_10()))  # total iva 10
    p.drawString(13*cm, 8.7*cm, separador_de_miles(venta.get_total_iva()))  # total iva

    # total en letras
    p.drawString(5*cm, 8*cm, num2words(venta.total, lang='es'))

    linea = 0
    ancho_celda = 0.7

    detalles = DetalleDeVenta.objects.filter(venta_id=venta.id)
    for detalle in detalles:
        p.drawString(2.4*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.cantidad))
        p.drawString(3.9*cm, (19-(linea*ancho_celda))*cm, detalle.descripcion)
        p.drawString(11.3*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.precio_unitario))
        if detalle.iva == EXCENTA:
            p.drawString(13.3*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.subtotal))
        elif detalle.iva == IVA_5:
            p.drawString(15.1*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.subtotal))
        else:
            p.drawString(16.6*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.subtotal))

        linea = linea + 1

    detalles2 = DetalleDeVenta2.objects.filter(venta_id=venta.id)
    for detalle in detalles2:

        p.drawString(2.4*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.cantidad))
        p.drawString(3.9*cm, (19-(linea*ancho_celda))*cm, detalle.descripcion)
        p.drawString(11.3*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.precio_unitario))
        if detalle.iva == EXCENTA:
            p.drawString(13.3* cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.subtotal))
        elif detalle.iva == IVA_5:
            p.drawString(15.1*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.subtotal))
        else:
            p.drawString(16.6*cm, (19-(linea*ancho_celda))*cm, separador_de_miles(detalle.subtotal))

        linea = linea + 1

    detalles3 = DetalleVentaMateriales.objects.filter(venta_id=venta.id)
    for detalle in detalles3:

        p.drawString(2.4 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.cantidad))
        p.drawString(3.9 * cm, (19 - (linea * ancho_celda)) * cm, detalle.descripcion)
        p.drawString(11.3 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.precio_unitario))
        if detalle.iva == EXCENTA:
            p.drawString(13.3 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))
        elif detalle.iva == IVA_5:
            p.drawString(15.1 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))
        else:
            p.drawString(16.6 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))

        linea = linea + 1



    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response


def pdf_factura(request, pk):
    from decimal import Decimal
    
    factura = Venta.objects.filter(pk=pk)
    factura = factura.get()
    remisiones = ""
    for fact in factura.ventaremision_set.all():
        remisiones = remisiones + "; " + fact.remision.codigo_de_establecimiento + "-" +\
                     fact.remision.punto_de_expedicion + "-" + fact.remision.numero_de_remision

    if len(remisiones) > 0:
        remisiones = remisiones[2:]

    detalles1 = factura.detalledeventa_set.all()
    detalles2 = factura.detalledeventa2_set.all()
    detalles3 = factura.detalleventamateriales_set.all()

    sub_0 = detalles1.filter(iva=0).aggregate(subtotal_0=Sum('subtotal'))['subtotal_0'] or Decimal('0')
    sub_5 = detalles1.filter(iva=5).aggregate(subtotal_5=Sum('subtotal'))['subtotal_5'] or Decimal('0')
    sub_10 = detalles1.filter(iva=10).aggregate(subtotal_10=Sum('subtotal'))['subtotal_10'] or Decimal('0')

    sub_0 += detalles2.filter(iva=0).aggregate(subtotal_0=Sum('subtotal'))['subtotal_0'] or Decimal('0')
    sub_5 += detalles2.filter(iva=5).aggregate(subtotal_5=Sum('subtotal'))['subtotal_5'] or Decimal('0')
    sub_10 += detalles2.filter(iva=10).aggregate(subtotal_10=Sum('subtotal'))['subtotal_10'] or Decimal('0')

    sub_0 += detalles3.filter(iva=0).aggregate(subtotal_0=Sum('subtotal'))['subtotal_0'] or Decimal('0')
    sub_5 += detalles3.filter(iva=5).aggregate(subtotal_5=Sum('subtotal'))['subtotal_5'] or Decimal('0')
    sub_10 += detalles3.filter(iva=10).aggregate(subtotal_10=Sum('subtotal'))['subtotal_10'] or Decimal('0')

    # Convertir las divisiones a Decimal para mantener el tipo
    total_5 = sub_5 / Decimal('21')
    total_10 = sub_10 / Decimal('11')
    
    # Asegurar que total_iva sea Decimal
    total_iva = total_5 + total_10

    reporte = "factura_triplicado.jasper"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="factura_'+ factura.empresa.nombre +"_"+ str(
        pk) + '_' + datetime.datetime.now().strftime('%Y-%m-%d|%H:%M:%S') + '.pdf"'
    response.write(reportes.get_report(reporte, {
        "id": str(pk),
        "remisiones": str(remisiones),
        "sub_0": float(sub_0) if sub_0 else 0,  # Convertir a float si es necesario
        "sub_5": float(sub_5) if sub_5 else 0,
        "sub_10": float(sub_10) if sub_10 else 0,
        "total_5": float(total_5) if total_5 else 0,
        "total_10": float(total_10) if total_10 else 0,
        "total_iva": float(total_iva) if total_iva else 0
    }))
    return response


def pdf_remision(request, pk):
    remision = Remision.objects.filter(pk=pk)
    if remision:
        remision = remision.get()

    reporte = "remision_triplicado.jasper"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="remision_'+ remision.empresa.nombre +"_"+ str(
        pk) + '_' + datetime.datetime.now().strftime('%Y-%m-%d|%H:%M:%S') + '.pdf"'
    response.write(reportes.get_report(reporte, {
        "id": str(pk),
    }))
    return response


def imprimir_remision_gesa(request, pk):
    # Crear el objeto HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=remision_gesa.pdf'

    # Crear el objeto PDF, usando el objeto response
    p = canvas.Canvas(response)

    # Fijar tamaño de la hoja
    p.setPageSize((19.7 * cm, 23.5 * cm))

    # Fijar tipo y tamaño de letra
    p.setFont("Times-Roman", 7)

    # color = colors.blue
    # p.setFillColor(color)


    ################ Escribir textos flotantes en coordenadas (X,Y) ################

    remision = Remision.objects.get(pk=pk)

    # fecha de emision
    p.drawString(3.5 * cm, 19.5 * cm, remision.fecha_de_emision.strftime("%d/%m/%Y"))

    # Nombre o razon social
    p.drawString(3.9 * cm, 18.8 * cm, remision.cliente.razon_social)

    # RUC o CI
    p.drawString(14.8 * cm, 18.8 * cm, remision.cliente.ruc)

    # Domicilio
    p.drawString(2.2 * cm, 18.4 * cm, remision.cliente.direccion)

    # Motivo de traslado
    p.drawString( 3.4 * cm, 17.8 * cm, remision.motivo_del_traslado)

    # Comprobante de Venta
    p.drawString(13.2 * cm, 17.8 * cm, remision.comprobante_de_venta)

    # Numero de Comprobante de Venta
    p.drawString(4.2 * cm, 17.4 * cm, remision.numero_de_comprobante_de_venta)

    # Nro de Timbrado
    p.drawString(12.9 * cm, 17.4 * cm, remision.numero_de_timbrado)

    # Fecha de expedicion
    p.drawString(3.6 * cm, 17.0 * cm, remision.fecha_de_expedicion.strftime('%d/%m/%Y'))

    # Fecha de Inicio de traslado
    p.drawString(4.4 * cm, 16.7 * cm, remision.fecha_de_inicio_del_traslado.strftime('%d/%m/%Y'))

    # Fecha estimada de termino de traslado
    p.drawString(15.6 * cm, 16.7 * cm, remision.fecha_estimada_de_termino_del_traslado.strftime('%d/%m/%Y'))

    # Direccion del punto de partida
    p.drawString(4.6 * cm, 16.3 * cm, remision.direccion_del_punto_de_partida)

    # Ciudad de partida
    p.drawString(2.2 * cm, 16 * cm, remision.ciudad_de_partida)

    # Departamento de partida
    p.drawString(12.7 * cm, 16 * cm, remision.departamento_de_partida)

    # Direccion del punto de llegada
    p.drawString(4.6 * cm, 15.6 * cm, remision.direccion_del_punto_de_llegada)

    # Ciudad de llegada
    p.drawString(2.2 * cm, 15.3 * cm, remision.ciudad_de_llegada)

    # Departamento de llegada
    p.drawString(12.7 * cm, 15.3 * cm, remision.departamento_de_llegada)

    # Kilometros estimados de recorrido
    p.drawString(5.1 * cm, 14.8 * cm, str(
        remision.kilometros_estimados_de_recorrido) if remision.kilometros_estimados_de_recorrido != None else '')

    # Cambio de fecha de termino del traslado o punto de llegada
    p.drawString(8.2 * cm, 14.5 * cm, remision.cambio_de_fecha_de_termino_del_traslado_o_punto_de_llegada)

    # Motivo
    p.drawString(2.2 * cm, 14.1 * cm, remision.motivo)

    if (remision.vehiculo != None):
        # DATOS DEL VEHICULO DE TRANSPORTE
        # Marca
        p.drawString(3.4 * cm, 13.3 * cm, remision.vehiculo.marca)
        # Registro unico del automotor
        p.drawString(6.6 * cm, 13. * cm, remision.vehiculo.rua)
        # Registro unico del automotor del Remolque
        p.drawString(10.5 * cm, 12.6 * cm, remision.vehiculo.rua_remolque)

    if (remision.chofer != None):
        # DATOS DEL CONDUCTOR DEL VEHICULO
        #   Nombre y Apellidos
        nombre = remision.chofer.nombres + ' ' + remision.chofer.apellidos
        p.drawString(5.1 * cm, 11.9 * cm, nombre)
        # RUC o CIC
        p.drawString(14.42* cm, 11.9 * cm, remision.chofer.ruc)
        # Domicilio
        p.drawString(2.3 * cm, 11.5 * cm, remision.chofer.direccion)

    linea = 0
    alto_de_celda = 0.5

    detalles = DetalleDeRemision.objects.filter(remision_id=remision.id)
    for detalle in detalles:
        p.drawString(1.2 * cm, (10 - (linea * alto_de_celda)) * cm, separador_de_miles(detalle.cantidad))
        p.drawString(2.9 * cm, (10 - (linea * alto_de_celda)) * cm,
                     detalle.unidad_de_medida.simbolo if detalle.unidad_de_medida != None else "")
        p.drawString(4.6 * cm, (10 - (linea * alto_de_celda)) * cm, detalle.descripcion)
        linea = linea + 1

    detalles2 = DetalleDeRemision2.objects.filter(remision_id=remision.id)
    for detalle in detalles2:
        p.drawString(1.2 * cm, (10 - (linea * alto_de_celda)) * cm, separador_de_miles(detalle.cantidad))
        p.drawString(2.9 * cm, (10 - (linea * alto_de_celda)) * cm,
                     detalle.unidad_de_medida.simbolo if detalle.unidad_de_medida != None else "")
        p.drawString(4.6 * cm, (10 - (linea * alto_de_celda)) * cm, detalle.descripcion)
        linea = linea + 1

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response


def imprimir_venta_gesa(request, pk):
    # Crear el objeto HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=venta_gesa.pdf'

    # Crear el objeto PDF, usando el objeto response
    p = canvas.Canvas(response)

    # Fijar tamaño de la hoja
    p.setPageSize((20.4 * cm, 27 * cm))

    # Fijar tipo y tamaño de letra
    p.setFont("Times-Roman", 8)

    ################ Escribir textos flotantes en coordenadas (X,Y) ################

    venta = Venta.objects.get(pk=pk)

    # fecha
    p.drawString(2.5 * cm, 22.2 * cm, venta.fecha_de_emision.strftime("%d"))  # dia

    numero_del_mes = int(venta.fecha_de_emision.strftime("%m"))  # mes
    if (numero_del_mes == 1):
        p.drawString(4.7 * cm, 22.2 * cm, 'enero')
    elif (numero_del_mes == 2):
        p.drawString(4.7 * cm, 22.2 * cm, 'febrero')
    elif (numero_del_mes == 3):
        p.drawString(4.7 * cm, 22.2 * cm, 'marzo')
    elif (numero_del_mes == 4):
        p.drawString(4.7 * cm, 22.2 * cm, 'abril')
    elif (numero_del_mes == 5):
        p.drawString(4.7 * cm, 22.2 * cm, 'mayo')
    elif (numero_del_mes == 6):
        p.drawString(4.7 * cm, 22.2 * cm, 'junio')
    elif (numero_del_mes == 7):
        p.drawString(4.7 * cm, 22.2 * cm, 'julio')
    elif (numero_del_mes == 8):
        p.drawString(4.7 * cm, 22.2 * cm, 'agosto')
    elif (numero_del_mes == 9):
        p.drawString(4.7 * cm, 22.2 * cm, 'setiembre')
    elif (numero_del_mes == 10):
        p.drawString(4.7 * cm, 22.2 * cm, 'octubre')
    elif (numero_del_mes == 11):
        p.drawString(4.7 * cm, 22.2 * cm, 'noviembre')
    elif (numero_del_mes == 12):
        p.drawString(4.7 * cm, 22.2 * cm, 'diciembre')

    p.drawString(8 * cm, 22.2 * cm, venta.fecha_de_emision.strftime("%Y"))  # año

    # condicion de la venta
    if (venta.condicion == CONTADO):
        p.drawString(15.5 * cm, 22.2 * cm, 'X')  # contado
    else:
        p.drawString(17.2 * cm, 22.2 * cm, 'X')  # credito

    # cliente
    p.drawString(2.5 * cm, 21.75 * cm, venta.cliente.razon_social)

    # condicion de pago
    #p.drawString(15.5*cm,21.75*cm, venta.condicion_de_pago)

    # Direccion
    p.drawString(2.5 * cm, 21.15 * cm, venta.cliente.direccion)

    # RUC o CI
    p.drawString(14 * cm, 21.15 * cm, venta.cliente.ruc)

    # Remisiones
    cadena_de_remisiones = ''
    for remision in venta.remision.all():
        cadena_de_remisiones = cadena_de_remisiones + remision.get_numero_de_remision()
    p.drawString(3 * cm, 20.45 * cm, cadena_de_remisiones)

    # Telefono
    p.drawString(14.4 * cm, 20.45 * cm, venta.cliente.telefono)

    # subtotal
    p.drawString(11 * cm, 9.2 * cm, separador_de_miles(venta.get_subtotal_exenta()))  # exentas
    p.drawString(13.6 * cm, 9.2 * cm, separador_de_miles(venta.get_subtotal_iva_5()))  # iva 5%
    p.drawString(16.5 * cm, 9.2 * cm, separador_de_miles(venta.get_subtotal_iva_10()))  # iva 10%

    # total
    p.drawString(16.5 * cm, 8.5 * cm, separador_de_miles(venta.total))

    # ivas
    p.drawString(2.5 * cm, 7.8 * cm, separador_de_miles(venta.get_iva_5()))  # total iva 5
    p.drawString(8 * cm, 7.8 * cm, separador_de_miles(venta.get_iva_10()))  # total iva 10
    p.drawString(14.2 * cm, 7.8 * cm, separador_de_miles(venta.get_total_iva()))  # total iva

    # total en letras
    p.drawString(5 * cm, 7.1 * cm, num2words(venta.total, lang='es'))

    linea = 0
    ancho_celda = 0.7

    detalles = DetalleDeVenta.objects.filter(venta_id=venta.id)
    for detalle in detalles:
        p.drawString(2.6 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.cantidad))
        p.drawString(3.8 * cm, (19 - (linea * ancho_celda)) * cm, detalle.descripcion)
        p.drawString(9.4 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.precio_unitario))
        if detalle.iva == EXCENTA:
            p.drawString(11.1 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))
        elif detalle.iva == IVA_5:
            p.drawString(13.7 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))
        else:
            p.drawString(16.6 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))

        linea = linea + 1

    detalles2 = DetalleDeVenta2.objects.filter(venta_id=venta.id)
    for detalle in detalles2:

        p.drawString(2.6 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.cantidad))
        p.drawString(3.8 * cm, (19 - (linea * ancho_celda)) * cm, detalle.descripcion)
        p.drawString(9.4 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.precio_unitario))
        if detalle.iva == EXCENTA:
            p.drawString(11.1 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))
        elif detalle.iva == IVA_5:
            p.drawString(13.7 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))
        else:
            p.drawString(16.6 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))

        linea = linea + 1

    detalles3 = DetalleVentaMateriales.objects.filter(venta_id=venta.id)

    for detalle in detalles3:
        p.drawString(2.6 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.cantidad))
        p.drawString(3.8 * cm, (19 - (linea * ancho_celda)) * cm, detalle.descripcion)
        p.drawString(9.4 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.precio_unitario))
        if detalle.iva == EXCENTA:
            p.drawString(11.1 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))
        elif detalle.iva == IVA_5:
            p.drawString(13.7 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))
        else:
            p.drawString(16.6 * cm, (19 - (linea * ancho_celda)) * cm, separador_de_miles(detalle.subtotal))

        linea = linea + 1

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response
