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

from depositos.models import Retiro, DetalleRetiro
from extra.globals import separador_de_miles

def reporte_retiro(request, retiro_id):
    response = HttpResponse(content_type='application/pdf')
    pdf_name = "Retiro_"+ datetime.now().strftime('%Y-%m-%d|%H:%M:%S') + '.pdf' 

    response['Content-Disposition'] = 'attachment; filename=%s' % pdf_name.replace(" ","_")
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
    header = Paragraph("Retiro", styles['Title'])
    reporte.append(header)

    retiro = Retiro.objects.get(pk=retiro_id)

    numero = Paragraph("Numero: %s" % separador_de_miles(retiro_id), styles['Normal'])
    reporte.append(numero)

    fecha = Paragraph("Fecha: %s" % retiro.fecha.strftime("%d/%m/%Y"), styles['Normal'])
    reporte.append(fecha)
  
    cliente = Paragraph("Funcionario: %s" % retiro.funcionario.get_full_name(), styles['Normal'])
    reporte.append(cliente)

    header = Paragraph("detalle", styles['Title'])
    reporte.append(header)


    detalles = DetalleRetiro.objects.filter(retiro_id = retiro_id)
    datos = [("OT", "Deposito", "Material" , "Cantidad")]

    for detalle in detalles:
        datos = datos + [(
							Paragraph( (separador_de_miles(detalle.orden_de_trabajo.id) if detalle.orden_de_trabajo != None else ''), styles['Normal']),
                            Paragraph( detalle.deposito.nombre, styles['Normal']),
                            Paragraph( detalle.material.__unicode__(), styles['Normal']),
							Paragraph( separador_de_miles(detalle.cantidad), styles['Normal']),
						)]

    t = Table(datos, colWidths=(30*mm, 30*mm, 105*mm, 30*mm))
    t.setStyle(TableStyle(
        [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            #('ALIGN',(1,1),(1,-1),'RIGHT'),
            #('ALIGN',(3,1),(3,-1),'RIGHT'),
            #('ALIGN',(4,1),(4,-1),'RIGHT'),
        ]
    ))
    reporte.append(t)

    doc.build(reporte)
    response.write(buff.getvalue())
    buff.close()
    return response


