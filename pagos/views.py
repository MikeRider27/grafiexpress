from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.db.models import Sum

import datetime

from proveedores.models import Proveedor
from empresas.models import Empresa
from compras.models import *
from pagos.models import *
from proveedores.views import ProveedorListView

from extra.globals import separador_de_miles, listview_to_excel


class PagoDetailView(DetailView):
    model = Pago
    template_name = "pago_detail.html"

    def get_context_data(self, **kwargs):
        context = super(PagoDetailView, self).get_context_data(**kwargs)
        context['detalles'] = DetalleDePago.objects.filter(pago=self.object)
        context['detalles2'] = DetalleDePago2.objects.filter(pago=self.object)
        return context


class PagoListView(ListView):
    model = Pago
    template_name = "pago_list.html"
    paginate_by = 30

    def get_queryset(self):
        pagos = Pago.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            pagos = pagos.filter(id=q)

        nro_factura = self.request.GET.get('factura_id', '')
        if nro_factura != '':
            pagos = pagos.filter(detalledepago__compra__numero_de_factura__icontains=nro_factura)

        proveedor_id = self.request.GET.get('proveedor_id', '')
        if proveedor_id != '':
            pagos = pagos.filter(proveedor__id=proveedor_id)

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            pagos = pagos.filter(fecha__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            pagos = pagos.filter(fecha__lte=fecha)

        return pagos.order_by('-id')

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''):
            lista_pagos = []
            pagos = self.get_queryset()
            total_pagos = 0

            for pago in pagos:
                compras = DetalleDePago.objects.filter(pago=pago)
                facturas_de_compra = ''
                for compra in compras:
                    facturas_de_compra += compra.compra.get_numero_de_factura() + ' - '

                lista_pagos.append([
                    pago.id,
                    pago.fecha.strftime("%d/%m/%Y"),
                    pago.proveedor.razon_social,
                    facturas_de_compra,
                    separador_de_miles(pago.monto),
                ])
                total_pagos += pago.monto
            lista_pagos.append(['', '', '', 'TOTAL PAGADO:', separador_de_miles(total_pagos)])
            titulos = ['ID', 'Fecha', 'Proveedor', 'Facturas de compra', 'Monto']
            return listview_to_excel(lista_pagos, 'pagos_a_proveedores', titulos)
        return super(PagoListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(PagoListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['proveedores'] = Proveedor.objects.all()
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['proveedor_id'] = int(self.request.GET.get('proveedor_id', '')) if (
                    self.request.GET.get('proveedor_id', '') != '') else ''
        context['factura_id'] = self.request.GET.get('factura_id', '') if (
                self.request.GET.get('factura_id', '') != '') else ''
        return context


def pagos_presentacion(request):
    context = RequestContext(request)
    titulo = "PAGO"
    descripcion = "."
    return render_to_response('admin/presentacion.html', {'titulo': titulo, 'descripcion': descripcion}, context)


class EstadoDeCuentaProveedorListView(ListView):
    model = Compra
    template_name = "estadodecuentaproveedor_list.html"
    paginate_by = 30

    def get_queryset(self):
        compras = Compra.objects.filter(proveedor_id=self.kwargs['proveedorid'])

        q = self.request.GET.get('q', '')
        if q != '':
            vector = q.split("-")
            codigo_de_establecimiento = vector[0]
            punto_de_expedicion = vector[1]
            numero_de_factura = vector[2]
            compras = compras.filter(Q(codigo_de_establecimiento__contains=codigo_de_establecimiento) &
                                     Q(punto_de_expedicion__contains=punto_de_expedicion) &
                                     Q(numero_de_factura__contains=numero_de_factura))

        return compras.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super(EstadoDeCuentaProveedorListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['proveedor'] = get_object_or_404(Proveedor, pk=self.kwargs['proveedorid'])
        return context


class PagosPendientesListView(ListView):
    model = Compra
    template_name = "pagos_pendientes_list.html"
    paginate_by = 30

    def get_queryset(self):
        compras = Compra.objects.exclude(saldo=0).order_by('fecha_de_vencimiento').reverse()
        q = self.request.GET.get('q', '')
        if q != '':
            compras = compras.filter(numero_de_factura__icontains=q)

        proveedor_id = self.request.GET.get('proveedor_id', '')
        if proveedor_id != '':
            compras = compras.filter(proveedor__id=proveedor_id)

        fecha_de_emision_desde = self.request.GET.get('fecha_de_emision_desde', '')
        if fecha_de_emision_desde != '':
            vector = fecha_de_emision_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            compras = compras.filter(fecha__gte=fecha)

        fecha_de_emision_hasta = self.request.GET.get('fecha_de_emision_hasta', '')
        if fecha_de_emision_hasta != '':
            vector = fecha_de_emision_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            compras = compras.filter(fecha__lte=fecha)

        fecha_de_vencimiento_desde = self.request.GET.get('fecha_de_vencimiento_desde', '')
        if fecha_de_vencimiento_desde != '':
            vector = fecha_de_vencimiento_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            compras = compras.filter(fecha_de_vencimiento__gte=fecha)

        fecha_de_vencimiento_hasta = self.request.GET.get('fecha_de_vencimiento_hasta', '')
        if fecha_de_vencimiento_hasta != '':
            vector = fecha_de_vencimiento_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            compras = compras.filter(fecha_de_vencimiento__lte=fecha)

        return compras

    def get_context_data(self, **kwargs):
        context = super(PagosPendientesListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['proveedores'] = Proveedor.objects.all()
        context['proveedor_id'] = int(self.request.GET.get('proveedor_id', '')) if (
                    self.request.GET.get('proveedor_id', '') != '') else ''
        context['fecha_de_emision_desde'] = self.request.GET.get('fecha_de_emision_desde', '')
        context['fecha_de_emision_hasta'] = self.request.GET.get('fecha_de_emision_hasta', '')
        context['fecha_de_vencimiento_desde'] = self.request.GET.get('fecha_de_vencimiento_desde', '')
        context['fecha_de_vencimiento_hasta'] = self.request.GET.get('fecha_de_vencimiento_hasta', '')
        context['total_general'] = self.get_queryset().aggregate(total_general=Sum('total')).get('total_general')
        return context

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''):
            lista_datos = []
            datos = self.get_queryset()
            for dato in datos:
                if dato.saldo != 0:
                    lista_datos.append([
                        dato.get_numero_de_factura(),
                        dato.proveedor.razon_social,
                        dato.fecha.strftime("%d/%m/%Y"),
                        dato.fecha_de_vencimiento.strftime("%d/%m/%Y"),
                        separador_de_miles(dato.total),
                        separador_de_miles(dato.saldo),
                    ])

            titulos = ['Factura', 'Proveedor', 'Emision', 'Vencimiento', 'Monto', 'Saldo']
            return listview_to_excel(lista_datos, 'Compras', titulos)
        return super(PagosPendientesListView, self).render_to_response(context, **response_kwargs)