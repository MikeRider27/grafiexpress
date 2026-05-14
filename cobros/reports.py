# -*- coding: utf-8 -*-
import datetime
import time
from io import BytesIO

import xlwt
from django.http import HttpResponse
from django.utils.encoding import force_text
from django.utils.text import Truncator
# from geraldo.generators.pdf import PDFGenerator
from reportlab.lib.pagesizes import A4, A6
from reportlab.pdfgen import canvas

from cobros.models import DetallePresentacion, PresentacionCobros
from extra.globals import separador_de_miles

width, height = A6


def coord(x, y, unit=1):
    x, y = x * unit, height - y * unit
    return x, y


def rendicion_pdf(request, id):
    def contenido(canvas, rendicion):
        from reportlab.lib.colors import darkblue, black
        canvas.setFillColor(darkblue)
        canvas.setFillColor(black)
        canvas.setStrokeColor(black)
        canvas.setFont("Helvetica-Bold", 13)

        # DATOS DE LA RENDICION
        canvas.setFont("Helvetica", 14)
        canvas.drawString(30, 820, "Rendicion Nro. : %s" % force_text(rendicion.id or ''))
        canvas.drawString(220, 820, "Fecha: %s" % force_text(rendicion.fecha.strftime('%d/%m/%Y') or ''))
        canvas.drawString(30, 800, "Cobrador : %s" % force_text(rendicion.cobrador or ''))

        # DETALLES
        canvas.line(30, 785, 350, 785)
        canvas.line(30, 765, 350, 765)

        canvas.drawString(30, 770, "Recibo")
        canvas.drawString(90, 770, u"Cliente")
        canvas.drawString(290, 770, "Subtotal")

        row = 765
        canvas.setFont("Helvetica", 11)
        detalles = DetallePresentacion.objects.filter(presentacion=rendicion)
        total_rendicion = 0
        for d in detalles:
            row -= 15
            canvas.drawString(40, row, force_text(d.cobro.numero))
            canvas.drawString(90, row, force_text(Truncator(d.cobro.cliente).chars(30)))
            canvas.drawString(280, row, force_text(separador_de_miles(d.subtotal)).rjust(13, ' '))
            total_rendicion += d.subtotal

        row -= 10
        canvas.line(30, row, 350, row)

        canvas.setFont("Helvetica-Bold", 13)

        row -= 14
        canvas.drawString(230, row, "Total: %s Gs." % separador_de_miles(total_rendicion))

    rendicion = PresentacionCobros.objects.get(pk=id)
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % str(rendicion)

    buffer = BytesIO()

    # Create the PDF object, using the BytesIO object as its "file."
    p = canvas.Canvas(buffer)
    contenido(p, rendicion)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.

    # Close the PDF object cleanly.
    p.showPage()
    p.save()

    # Get the value of the BytesIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response