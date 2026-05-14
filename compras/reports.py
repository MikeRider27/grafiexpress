from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
#from reportlab.lib.pagesizes import letter, LEGAL, landscape
from reportlab.lib.pagesizes import A4

from reportlab.platypus import Table
from io import BytesIO
from reportlab.lib.units import mm

from django.http.response import HttpResponse
from datetime import datetime
from extra.globals import separador_de_miles
from compras.models import *
from num2words import num2words

def reporte_orden_de_compra(request, orden_de_compra_id):
    response = HttpResponse(content_type='application/pdf')
    pdf_name = "orden_de_compra_"+ datetime.now().strftime('%Y-%m-%d|%H:%M:%S') + '.pdf' 
    print (pdf_name)
    response['Content-Disposition'] = 'attachment; filename=%s' % pdf_name.replace(" ", "_")
    buff = BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=(A4),
                            rightMargin=40,
                            leftMargin=40,
                            topMargin=60,
                            bottomMargin=18,
                            )
    reporte = []
    styles = getSampleStyleSheet()
    orden_de_compra = OrdenDeCompra.objects.get(pk=orden_de_compra_id)

    numero = "Numero: " + str(orden_de_compra.id)
    # reporte.append(numero)
    header = Table([[" ", Paragraph("Orden de compra", styles['Title']), numero], ], colWidths=(65*mm, 65*mm, 65*mm))
    header.setStyle(TableStyle(
        [
            ('ALIGN', (2, 0), (2, 0), 'RIGHT')
        ]
    ))
    reporte.append(header)



    fecha = Paragraph("Fecha: %s" % orden_de_compra.fecha.strftime("%d/%m/%Y"), styles['Normal'])
    # reporte.append(fecha)

    proveedor = Paragraph("Proveedor: %s" % orden_de_compra.proveedor.razon_social, styles['Normal'])
    # reporte.append(proveedor)

    contacto = Paragraph("Contacto: %s" % orden_de_compra.contacto, styles['Normal'])
    # reporte.append(contacto)

    telefono = Paragraph("Telefono: %s" % orden_de_compra.telefono, styles['Normal'])
    # reporte.append(telefono)

    forma_de_pago = Paragraph("Forma de pago: %s" % orden_de_compra.forma_de_pago, styles['Normal'])
    # reporte.append(forma_de_pago)

    condicion = Paragraph("Condicion: %s" % orden_de_compra.condicion, styles['Normal'])
    # reporte.append(condicion)

    cheque_diferido = Paragraph("Cheque diferido: %s" % orden_de_compra.cheque_diferido, styles['Normal'])
    # reporte.append(cheque_diferido)

    plazo = Paragraph("Plazo: %s" % orden_de_compra.plazo, styles['Normal'])
    # reporte.append(plazo)

    cabecera = [
        [fecha, forma_de_pago],
        [proveedor, condicion],
        [contacto, cheque_diferido],
        [telefono, plazo],
    ]

    headerbox = Table(cabecera, colWidths=(80*mm, 115*mm))
    headerbox.setStyle(TableStyle(
        [
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBEFORE', (0, 0), (-1, -1), 1, colors.black)
        ]
    ))
    reporte.append(headerbox)

    departamento_solicitante = Paragraph("Departamento solicitante: %s" % orden_de_compra.departamento_solicitante, styles['Normal'])
    # reporte.append(departamento_solicitante)

    categoria_de_gastos = Paragraph("Categoria de gastos: %s" % orden_de_compra.categoria_de_gastos, styles['Normal'])
    # reporte.append(categoria_de_gastos)

    responsable = Paragraph("Responsable: %s" % orden_de_compra.responsable, styles['Normal'])
    # reporte.append(responsable)

    cabecera2 = [
        [departamento_solicitante],
        [categoria_de_gastos],
        [responsable],
    ]
    headerbox2 = Table(cabecera2, 195*mm)
    headerbox2.setStyle(TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]
    ))
    reporte.append(headerbox2)
    #total = Paragraph("Total: Gs. %s" % separador_de_miles(orden_de_compra.total), styles['Normal'])
    #reporte.append(total)

    datos = [("OT", "Descripcion", "Cantidad", "Precio Unitario", "Subtotal")]


    detalles = PapelOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
							detalle.descripcion.__unicode__(), 
							separador_de_miles(detalle.cantidad), 
							separador_de_miles(detalle.precio_unitario),
							separador_de_miles(detalle.get_subtotal())
						)]

    detalles = PreprensaOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = TroquelOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = PosprensaServicioOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = PosprensaMaterialOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = PosprensaOtroServicioOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = DatosDeBolsaOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = RevistaOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = CompuestoOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = PlastificadoOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = OtroGastoOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            separador_de_miles(detalle.descripcion.costo.detalle_orden_de_trabajo.orden_de_trabajo.id),
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    detalles = InsumoOrdenDeCompra.objects.filter(orden_de_compra_id = orden_de_compra_id)

    for detalle in detalles:
        datos = datos + [(
                            '',
                            detalle.descripcion.__unicode__(), 
                            separador_de_miles(detalle.cantidad), 
                            separador_de_miles(detalle.precio_unitario),
                            separador_de_miles(detalle.get_subtotal())
                        )]

    t = Table(datos, colWidths=(20*mm,100*mm,25*mm, 25*mm, 25*mm))
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

    totalapagar = orden_de_compra.get_total()
    valorletras = "Valor en Letras          " + num2words(totalapagar, lang='es')

    footer1 = Table([['Total a Pagar', separador_de_miles(totalapagar), ]],
                   colWidths=(170*mm, 25*mm))
    footer1.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, 0), 1, colors.black),
        ('BOX', (0, 1), (-1, 1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT')
        ]
    ))

    footer2 = Table([[valorletras, ], ], 195*mm)
    footer2.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT')
    ]
    ))

    reporte.append(footer1)
    reporte.append(footer2)

    doc.build(reporte)
    response.write(buff.getvalue())
    buff.close()
    return response


