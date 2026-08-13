from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from django.utils.encoding import force_text
from reportlab.pdfgen import canvas
#from reportlab.lib.pagesizes import letter, LEGAL, landscape
from reportlab.lib.pagesizes import A4, landscape
import time

from reportlab.platypus import Table
from io import BytesIO
from reportlab.lib.units import mm

from django.http.response import HttpResponse

from grafiexpress.globales import separar
from produccion.models import *
from extra.globals import separador_de_miles


def reporte_orden_de_trabajo(request, orden_de_trabajo_id):
    response = HttpResponse(content_type='application/pdf')
    pdf_name = "orden_de_trabajo_" + time.strftime('%Y-%m-%d|%H:%M:%S') + '.pdf'

    response['Content-Disposition'] = 'attachment; filename=%s' % pdf_name.replace(" ", "_")
    buff = BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=(A4),
                            rightMargin=40,
                            leftMargin=40,
                            topMargin=60,
                            bottomMargin=18,
                            )

    orden_de_trabajo = OrdenDeTrabajo.objects.get(pk=orden_de_trabajo_id)

    reporte = []
    styles = getSampleStyleSheet()

    #tabla cabecera con numero y fechas de la OT
    datos = []
    elementos = []

    # Tabla con datos de la cabecera Nro. OT y Nro. Presupuesto
    nro_ot = Paragraph("Nro. de OT: %s" % separador_de_miles(orden_de_trabajo.id), styles['Heading2'])
    nro_presupuesto = Paragraph("Nro. de presupuesto: %s" % orden_de_trabajo.presupuesto_numero, styles['Heading2'])
    elementos.append(nro_presupuesto)
    elementos.append(nro_ot)

    t_header = Table([elementos], colWidths=(125*mm, 70*mm))
    reporte.append(t_header)

    #Tabla con datos de la OT
    datos += [("Nombre: %s" % orden_de_trabajo.nombre, "Fecha de ingreso: %s" % orden_de_trabajo.fecha_de_ingreso.strftime("%d/%m/%Y") )]
    #if request.user.has_perm('produccion.view_fecha_solicitada'):
    fecha_solicitada = orden_de_trabajo.fecha_solicitada.strftime("%d/%m/%Y") if (orden_de_trabajo.fecha_solicitada != None) else ''
    datos += [("Cliente: %s" % orden_de_trabajo.cliente.razon_social, "Fecha de presentacion: %s" % fecha_solicitada )]
    datos += [("Vendedor: %s" % orden_de_trabajo.vendedor.get_full_name(), "")]
    datos += [("Comentarios: %s" % orden_de_trabajo.comentarios, "")]

    t = Table(datos, colWidths=(125*mm, 70*mm))
    reporte.append(t)

    linea = Paragraph("", styles['Title'])
    reporte.append(linea)

    t = Table([("Opciones",)], colWidths=(195*mm))
    t.setStyle(TableStyle(
        [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            #('ALIGN',(3,1),(3,-1),'RIGHT'),
            #('ALIGN',(2,1),(2,-1),'RIGHT'),
            #('ALIGN',(4,1),(4,-1),'RIGHT'),
        ]
    ))

    reporte.append(t)

    datos = [("Prueba de color:", ("Si" if orden_de_trabajo.prueba_de_color == True else "No"), "Prueba del producto:", ("Si" if orden_de_trabajo.prueba_de_producto == True else "No"))]
    datos = datos + [("Muestra de color:", ("Si" if orden_de_trabajo.muestra_de_color == True else "No"), "Muestra del producto:", ("Si" if orden_de_trabajo.muestra_de_producto == True else "No"))]
    datos = datos + [("Repeticion:", ("Si" if orden_de_trabajo.repeticion == True else "No"), "Buscar sobrante:", ("Si" if orden_de_trabajo.buscar_sobrante == True else "No"))]
    t = Table(datos, colWidths=(48*mm,48*mm,48*mm,48*mm))
    reporte.append(t)



    t = Table([("Detalle",)], colWidths=(195*mm))
    t.setStyle(TableStyle(
        [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN',(0,0),(-1,0),'CENTER'),
            #('ALIGN',(2,1),(2,-1),'RIGHT'),
            #('ALIGN',(4,1),(4,-1),'RIGHT'),
        ]
    ))

    reporte.append(t)

    datos = [(
        "Categoria:", Paragraph((orden_de_trabajo.categoria.nombre if orden_de_trabajo.categoria != None else ''), styles['Normal']),
        "Subcategoria:", Paragraph((orden_de_trabajo.subcategoria.nombre if orden_de_trabajo.subcategoria != None else ''), styles['Normal']), 
        "Cantidad:", separador_de_miles(orden_de_trabajo.cantidad), 
    )] 


    t = Table(datos, colWidths=(25*mm, 45*mm, 35*mm, 45*mm, 20*mm, 25*mm))
    reporte.append(t)

    datos = [( "Precio unitario:", separador_de_miles(orden_de_trabajo.precio_unitario, gs=True), "Total:", separador_de_miles(orden_de_trabajo.get_total(), gs=True ) )] + [("Cambios:", ("Si" if orden_de_trabajo.cambios == True else "No"), "Materiales compuestos", ("Si" if orden_de_trabajo.materiales_compuestos == True else "No"))]
    t = Table(datos, colWidths=(25*mm, 45*mm, 45*mm, 80*mm))
    reporte.append(t)

    contador = 1
    detalles = DetalleOrdenDeTrabajo.objects.filter(orden_de_trabajo_id = orden_de_trabajo_id)
    for detalle in detalles:

        datos = [( ("#"+str(contador)+" Descripcion:"), Paragraph(detalle.descripcion, styles['Normal']),"Cantidad:", Paragraph(separador_de_miles(detalle.cantidad), styles['Normal']) )]
        datos = datos + [(
            "Material:",  Paragraph(str(detalle.material), styles['Normal']),
            "Dimensiones:", Paragraph(detalle.get_dimension(), styles['Normal']) 
        )]

        t = Table(datos, colWidths=(30*mm, 115*mm, 25*mm, 25*mm))

        t.setStyle(TableStyle(
            [
                ("LINEABOVE", (0,0), (-1,0), 1, colors.black),

                #('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                #('GRID', (0, 0), (-1, -1), 1, colors.black),
                #('ALIGN',(3,1),(3,-1),'RIGHT'),
                #('ALIGN',(2,1),(2,-1),'RIGHT'),
                #('ALIGN',(4,1),(4,-1),'RIGHT'),
            ]
        ))

        reporte.append(t)



        datos = [("Color", "", "")]
        datos = datos + [("", "Frente", "Dorso")]
        datos = datos + [("Seleccion", detalle.color_seleccion_frente, detalle.color_seleccion_dorso)]
        datos = datos + [("Pantone", detalle.color_pantone_frente, detalle.color_pantone_dorso)]
        t = Table(datos, colWidths=(20*mm, 45*mm, 45*mm))

        t.setStyle(TableStyle(
            [
                ('SPAN', (0,0), (-1,0)),
                #('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN',(0,0),(-1,1),'CENTER'),
                #('ALIGN',(2,1),(2,-1),'RIGHT'),
                #('ALIGN',(4,1),(4,-1),'RIGHT'),
            ]
        ))

        reporte.append(t)



        datos = [("Observaciones:", Paragraph(detalle.observaciones, styles['Normal']) )]
        t = Table(datos, colWidths=(30*mm, 165*mm))

        t.setStyle(TableStyle(
            [
                #('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                #('GRID', (0, 0), (-1, -1), 1, colors.black),
                #('ALIGN',(3,1),(3,-1),'RIGHT'),
                #('ALIGN',(2,1),(2,-1),'RIGHT'),
                #('ALIGN',(4,1),(4,-1),'RIGHT'),
            ]
        ))

        reporte.append(t)
        linea = Paragraph("", styles['Title'])
        reporte.append(linea)
        contador = contador + 1

    doc.build(reporte)
    response.write(buff.getvalue())
    buff.close()
    return response


def calendario_por_maquina(request, id):
    def contenido(canvas, obj):
        from reportlab.lib.colors import darkblue, black
        canvas.setFillColor(darkblue)
        canvas.setFillColor(black)
        canvas.setStrokeColor(black)
        canvas.setPageSize(landscape(A4))

        canvas.setFont("Helvetica", 12)
        canvas.drawString(30, 570, "Fecha de inicio:")
        canvas.setFont("Helvetica", 13)
        canvas.drawString(140, 570, obj.fecha_de_inicio.strftime('%d/%m/%Y'))

        canvas.setFont("Helvetica", 12)
        canvas.drawString(30, 550, "Fecha de entrega:")
        canvas.setFont("Helvetica", 13)
        canvas.drawString(140, 550, obj.fecha_de_entrega.strftime('%d/%m/%Y'))

        canvas.setFont("Helvetica", 12)
        canvas.drawString(30, 530, "Maquina:")
        canvas.setFont("Helvetica", 13)
        canvas.drawString(140, 530, str(obj.maquina))

        canvas.setFont("Helvetica", 13)
        canvas.drawString(480, 530, "Programado")

        canvas.setFont("Helvetica", 13)
        canvas.drawString(570, 530, "Realizado")

        # LINEA HORIZONTAL QUE SEPARA LA CABECERA DEL RESTO
        canvas.line(20, 520, 820, 520)

        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(40, 505, "O.T")
        canvas.drawString(260, 505, "Cliente")
        canvas.drawString(375, 505, "Tiradas")
        canvas.drawString(430, 505, "Pasadas")
        canvas.drawString(490, 505, "Inicio")
        canvas.drawString(530, 505, "Fin")
        canvas.drawString(570, 505, "Inicio")
        canvas.drawString(610, 505, "Fin")
        canvas.drawString(648, 505, "Tirada Fin")
        canvas.drawString(728, 505, "Responsable")
        canvas.line(20, 500, 820, 500)

        row = 500
        canvas.setFont("Helvetica", 11)
        programaciones = DetalleProgramacion.objects.filter(programacion=obj)
        for programacion in programaciones:
            row -= 20
            canvas.drawString(40, row, force_text(programacion.detalle_proceso.proceso.orden_de_trabajo)[:38])
            canvas.line(255, row - 5, 255, row + 40)
            canvas.drawString(260, row, force_text(programacion.detalle_proceso.proceso.orden_de_trabajo.cliente.razon_social[:15]))
            canvas.line(373, row - 5, 373, row + 40)
            canvas.drawString(370, row, separar(int(round(programacion.pliegos))).rjust(15))
            canvas.line(430, row - 5, 430, row + 40)
            canvas.drawString(430, row, separar(int(round(programacion.detalle_proceso.pasadas_por_pliego))).rjust(15))
            canvas.line(485, row - 5, 485, row + 40)
            canvas.drawString(490, row, programacion.hora_de_inicio.strftime('%H:%M'))
            canvas.line(525, row - 5, 525, row + 40)
            canvas.drawString(530, row, programacion.hora_de_finalizacion.strftime('%H:%M'))
            canvas.line(565, row - 5, 565, row + 40)
            canvas.line(605, row - 5, 605, row + 40)
            canvas.line(645, row - 5, 645, row + 40)
            canvas.line(720, row - 5, 720, row + 40)
            canvas.line(20, row-5, 820, row-5)

        canvas.line(20, 520, 20, row-5)
        canvas.line(820, 520, 820, row - 5)

        row -= 30
        canvas.setFont("Helvetica", 10)
        canvas.drawString(30, 20, "Fecha: %s" % time.strftime("%Y/%m/%d"))
        canvas.drawString(200, 20, "Hora: %s" % time.strftime("%X"))
        canvas.drawString(350, 20, "Impreso por: %s" % request.user)

    obj = Programacion.objects.get(pk=id)
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="calendario_por_maquina.pdf"'
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    contenido(p, obj)
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response