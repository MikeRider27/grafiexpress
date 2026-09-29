from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

import datetime

from clientes.models import Cliente
from cobros.models import *
from empresas.models import Empresa
from funcionarios.models import Funcionario
from ventas.models import *

from extra.globals import separador_de_miles, listview_to_excel


class ReciboDetailView(DetailView):
    model = Recibo
    template_name = "recibo_detail.html"

    def get_context_data(self, **kwargs):
        context = super(ReciboDetailView, self).get_context_data(**kwargs)
        context['detalles'] = DetalleDeRecibo.objects.filter(recibo=self.object)
        context['detalles2'] = DetalleDeRecibo2.objects.filter(recibo=self.object)
        return context


class ReciboListView(ListView):
    model = Recibo
    template_name = "recibo_list.html"
    paginate_by = 30

    def get_queryset(self):
        recibos = Recibo.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            recibos = recibos.filter(numero=q)

        cliente_id = self.request.GET.get('cliente_id', '')
        if cliente_id != '':
            recibos = recibos.filter(cliente__id=cliente_id)

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            recibos = recibos.filter(fecha__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            recibos = recibos.filter(fecha__lte=fecha)

        estado = self.request.GET.get('estado', '0')
        if estado != 'TODOS':
            recibos = recibos.filter(estado=estado)

        presentado = self.request.GET.get('presentado', '')
        if presentado != 'TODOS':
            if presentado == 'SI':
                recibos = recibos.filter(presentado=True)
            else:
                recibos = recibos.exclude(presentado=True)

        nro_factura = self.request.GET.get('factura_id', '')
        if nro_factura != '':
            recibos = recibos.filter(detallederecibo__factura__numero_de_factura__icontains=nro_factura)

        return recibos.order_by('-id')

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''):
            lista_recibos = []
            recibos = self.get_queryset()
            total_anticipos = 0
            total_retenciones = 0
            total_efectivo = 0
            total_cheques = 0
            total_transferencias = 0
            total_giros = 0
            total_notas_de_credito = 0
            total_tarjetas_de_credito = 0
            total_tarjetas_de_debito = 0
            total_otros = 0
            total_del_dia = 0

            for recibo in recibos:
                facturas_del_recibo = DetalleDeRecibo.objects.filter(recibo=recibo)
                facturas = ' '
                for factura in facturas_del_recibo:
                    facturas += factura.factura.get_numero_de_factura() + ' - '

                pagos_del_recibo = DetalleDeRecibo2.objects.filter(recibo=recibo)
                anticipo = 0
                retencion = 0
                efectivo = 0
                cheque = 0
                transferencia = 0
                giro = 0
                tarjeta_de_credito = 0
                tarjeta_de_debito = 0
                otro = 0
                nota_de_credito = 0
                banco = ' '
                cheque_nro = ''
                for pago in pagos_del_recibo:
                    if pago.medio_de_pago == 8:
                        anticipo = pago.monto
                    if pago.medio_de_pago == 5:
                        retencion = pago.monto
                    if pago.medio_de_pago == 0:
                        efectivo = pago.monto
                    if pago.medio_de_pago == 1:
                        transferencia = pago.monto
                    if pago.medio_de_pago == 2:
                        giro = pago.monto
                    if pago.medio_de_pago == 7:
                        tarjeta_de_credito = pago.monto
                    if pago.medio_de_pago == 6:
                        tarjeta_de_debito = pago.monto
                    if pago.medio_de_pago == 9:
                        otro = pago.monto
                    if pago.medio_de_pago == 4:
                        nota_de_credito = pago.monto
                    if pago.medio_de_pago == 3:
                        cheque = pago.monto
                        if pago.cheque:
                            banco = pago.cheque.banco.nombre
                            cheque_nro = pago.cheque.numero

                if recibo.estado != 'A':
                    lista_recibos.append([
                        recibo.numero,
                        recibo.fecha.strftime("%d/%m/%Y"),
                        recibo.cliente.nombre,
                        facturas,
                        separador_de_miles(anticipo),
                        separador_de_miles(retencion),
                        separador_de_miles(efectivo),
                        separador_de_miles(transferencia),
                        separador_de_miles(giro),
                        separador_de_miles(tarjeta_de_credito),
                        separador_de_miles(tarjeta_de_debito),
                        separador_de_miles(otro),
                        separador_de_miles(nota_de_credito),
                        separador_de_miles(cheque),
                        banco,
                        cheque_nro,
                    ])
                    total_anticipos += anticipo
                    total_retenciones += retencion
                    total_efectivo += efectivo
                    total_transferencias += transferencia
                    total_giros += giro
                    total_notas_de_credito += nota_de_credito
                    total_tarjetas_de_credito += tarjeta_de_credito
                    total_tarjetas_de_debito += tarjeta_de_debito
                    total_otros += otro
                    total_cheques += cheque
            total_del_dia = total_anticipos + total_retenciones + total_efectivo + total_cheques + \
                            total_transferencias + total_giros + total_notas_de_credito + \
                            total_tarjetas_de_credito + total_tarjetas_de_debito + total_otros

            lista_recibos.append([])
            lista_recibos.append(['', '', '', 'TOTALES:', separador_de_miles(total_anticipos),
                                  separador_de_miles(total_retenciones), separador_de_miles(total_efectivo),
                                  separador_de_miles(total_transferencias), separador_de_miles(total_giros),
                                  separador_de_miles(total_tarjetas_de_credito),
                                  separador_de_miles(total_tarjetas_de_debito),
                                  separador_de_miles(total_otros), separador_de_miles(total_notas_de_credito),
                                  separador_de_miles(total_cheques)])
            lista_recibos.append(['', '', 'TOTAL DEL DIA:', separador_de_miles(total_del_dia)])
            titulos = ['Nro de Recibo', 'Fecha', 'Cliente', 'Facturas', 'Anticipo', 'Retencion', 'Efectivo',
                       'Transferencias', 'Giros', 'Tarjetas de credito', 'Tarjetas de debito', 'Otros',
                       'Notas de credito', 'Cheque', 'Banco', 'Nro de cheque']
            return listview_to_excel(lista_recibos, 'recibos_emitidos', titulos)

        return super(ReciboListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReciboListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['clientes'] = Cliente.objects.all()
        context['cliente_id'] = int(self.request.GET.get('cliente_id', '')) if (
                self.request.GET.get('cliente_id', '') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['factura_id'] = self.request.GET.get('factura_id', '') if (
                self.request.GET.get('factura_id', '') != '') else ''
        context['estado'] = self.request.GET.get('estado', '0')
        context['presentado'] = self.request.GET.get('presentado', 'TODOS') if (
                    self.request.GET.get('presentado', 'TODOS') != 'TODOS') else 'TODOS'

        return context


# @permission_required('recibo.print_recibo')
def imprimir_recibo(request, pk):
    context = RequestContext(request)
    recibo = get_object_or_404(Recibo, pk=pk)
    if request.method == 'POST':
        recibo.estado = 1  # PROCESADO
        recibo.save()
        return redirect('/admin/cobros/recibo')

    mensaje = "Esta seguro que desea imprimir el Recibo " + recibo.numero
    return render_to_response('recibo_confirm.html', {'mensaje': mensaje}, context)


# @permission_required('recibo.cancel_recibo')
def anular_recibo(request, pk):
    context = RequestContext(request)
    recibo = get_object_or_404(Recibo, pk=pk)
    if request.method == 'POST':
        recibo.estado = 2  # ANULADO
        recibo.save()

        detalles = DetalleDeRecibo.objects.filter(recibo_id=recibo.id)
        for detalle in detalles:
            factura = detalle.factura
            factura.pagado = factura.get_pagado()
            factura.saldo = factura.get_saldo()
            factura.save()

        return redirect('/admin/cobros/recibo/')

    mensaje = "Esta seguro que desea anular el Recibo " + recibo.numero
    return render_to_response('recibo_confirm.html', {'mensaje': mensaje}, context)


# @permission_required('recibo.cancel_recibo')
def cancelar_anular_recibo(request, pk):
    context = RequestContext(request)
    recibo = get_object_or_404(Recibo, pk=pk)
    if request.method == 'POST':
        recibo.estado = 1  # PROCESADO
        recibo.save()

        detalles = DetalleDeRecibo.objects.filter(recibo_id=recibo.id)
        for detalle in detalles:
            factura = detalle.factura
            factura.pagado = factura.get_pagado()
            factura.saldo = factura.get_saldo()
            factura.save()

        return redirect('/admin/cobros/recibo/')

    mensaje = "Esta seguro que desea cancelar la anulacion del Recibo " + recibo.numero
    return render_to_response('recibo_confirm.html', {'mensaje': mensaje}, context)


def cobros_presentacion(request):
    context = RequestContext(request)
    titulo = "COBROS"
    descripcion = "."
    return render_to_response('admin/presentacion.html', {'titulo': titulo, 'descripcion': descripcion}, context)


class EstadoDeCuentaListView(ListView):
    model = Venta
    template_name = "estadodecuenta_list.html"
    paginate_by = 30

    def get_queryset(self):
        ventas = Venta.objects.filter(cliente_id=self.kwargs['clienteid']).exclude(estado='A')

        q_numero_de_factura = self.request.GET.get('q_numero_de_factura', '')
        q_fecha_de_emision_desde = self.request.GET.get('q_fecha_de_emision_desde', '')
        q_fecha_de_emision_hasta = self.request.GET.get('q_fecha_de_emision_hasta', '')
        q_fecha_de_vencimiento_desde = self.request.GET.get('q_fecha_de_vencimiento_desde', '')
        q_fecha_de_vencimiento_hasta = self.request.GET.get('q_fecha_de_vencimiento_hasta', '')

        if q_numero_de_factura != "":
            ventas = ventas.filter(Q(codigo_de_establecimiento__contains=q_numero_de_factura) |
                                   Q(punto_de_expedicion__contains=q_numero_de_factura) |
                                   Q(numero_de_factura__contains=q_numero_de_factura)
                                   )

        if q_fecha_de_emision_desde != "":
            q_fecha_de_emision_desde = datetime.datetime.strptime(q_fecha_de_emision_desde, '%d/%m/%Y').strftime(
                '%Y-%m-%d')
            ventas = ventas.filter(fecha_de_emision__gte=q_fecha_de_emision_desde)

        if q_fecha_de_emision_hasta != "":
            q_fecha_de_emision_hasta = datetime.datetime.strptime(q_fecha_de_emision_hasta, '%d/%m/%Y').strftime(
                '%Y-%m-%d')
            ventas = ventas.filter(fecha_de_emision__lte=q_fecha_de_emision_hasta)

        if q_fecha_de_vencimiento_desde != "":
            q_fecha_de_vencimiento_desde = datetime.datetime.strptime(q_fecha_de_vencimiento_desde,
                                                                      '%d/%m/%Y').strftime('%Y-%m-%d')
            ventas = ventas.filter(fecha_de_vencimiento__gte=q_fecha_de_vencimiento_desde)

        if q_fecha_de_vencimiento_hasta != "":
            q_fecha_de_vencimiento_hasta = datetime.datetime.strptime(q_fecha_de_vencimiento_hasta,
                                                                      '%d/%m/%Y').strftime('%Y-%m-%d')
            ventas = ventas.filter(fecha_de_vencimiento__gte=q_fecha_de_vencimiento_hasta)

        return ventas.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super(EstadoDeCuentaListView, self).get_context_data(**kwargs)
        context['q_numero_de_factura'] = self.request.GET.get('q_numero_de_factura', '')
        context['q_fecha_de_emision_desde'] = self.request.GET.get('q_fecha_de_emision_desde', '')
        context['q_fecha_de_emision_desde'] = self.request.GET.get('q_fecha_de_emision_desde', '')
        context['q_fecha_de_vencimiento_desde'] = self.request.GET.get('q_fecha_de_vencimiento_desde', '')
        context['q_fecha_de_vencimiento_hasta'] = self.request.GET.get('q_fecha_de_vencimiento_hasta', '')
        context['cliente'] = get_object_or_404(Cliente, pk=self.kwargs['clienteid'])
        return context

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''):
            lista_datos = []
            datos = self.get_queryset()
            total_total = 0
            total_pagado = 0
            total_saldo = 0
            for dato in datos:
                lista_datos.append([
                    dato.get_numero_de_factura(),
                    dato.fecha_de_emision.strftime("%d/%m/%Y"),
                    dato.fecha_de_vencimiento.strftime("%d/%m/%Y"),
                    separador_de_miles(dato.total),
                    separador_de_miles(dato.pagado),
                    separador_de_miles(dato.saldo),
                ])
                total_total += dato.total
                total_pagado += dato.pagado
                total_saldo += dato.saldo

            lista_datos.append(['Totales', '', '',
                                separador_de_miles(total_total),
                                separador_de_miles(total_pagado),
                                separador_de_miles(total_saldo)])

            titulos = ['Nro. Factura', 'Fecha Emision', 'Fecha Vencimiento', 'Total', 'Pagado', 'Saldo']

            filename = "cobros_%s" % dato.cliente.nombre
            return listview_to_excel(lista_datos, filename, titulos)

        return super(EstadoDeCuentaListView, self).render_to_response(context, **response_kwargs)


class CobroListView(ListView):
    model = Venta
    template_name = "cobro_list.html"
    paginate_by = 30

    def get_queryset(self):
        ventas = Venta.objects.exclude(Q(estado='A') | Q(saldo=0)).order_by('fecha_de_vencimiento').reverse()
        q = self.request.GET.get('q', '')
        if q != '':
            ventas = ventas.filter(numero_de_factura__icontains=q)

        orden_de_trabajo = self.request.GET.get('orden_de_trabajo', '')
        if orden_de_trabajo != '':
            ventas = ventas.filter(
                Q(pk__in=[i.venta_id for i in DetalleDeVenta.objects.filter(orden_de_trabajo=orden_de_trabajo)]) | Q(
                    pk__in=[j.venta_id for j in DetalleDeVenta2.objects.filter(
                        detalle_orden_de_trabajo__orden_de_trabajo=orden_de_trabajo)])
            )

        cliente_id = self.request.GET.get('cliente_id', '')
        if cliente_id != '':
            ventas = ventas.filter(cliente_id=cliente_id)

        empresa_id = self.request.GET.get('empresa_id', '')
        if empresa_id != '':
            ventas = ventas.filter(empresa_id=empresa_id)

        estado = self.request.GET.get('estado', '')
        if estado != 'TODOS':
            ventas = ventas.filter(estado=estado)

        fecha_de_emision_desde = self.request.GET.get('fecha_de_emision_desde', '')
        if fecha_de_emision_desde != '':
            vector = fecha_de_emision_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            ventas = ventas.filter(fecha_de_emision__gte=fecha)

        fecha_de_emision_hasta = self.request.GET.get('fecha_de_emision_hasta', '')
        if fecha_de_emision_hasta != '':
            vector = fecha_de_emision_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            ventas = ventas.filter(fecha_de_emision__lte=fecha)

        fecha_de_vencimiento_desde = self.request.GET.get('fecha_de_vencimiento_desde', '')
        if fecha_de_vencimiento_desde != '':
            vector = fecha_de_vencimiento_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            ventas = ventas.filter(fecha_de_vencimiento__gte=fecha)

        fecha_de_vencimiento_hasta = self.request.GET.get('fecha_de_vencimiento_hasta', '')
        if fecha_de_vencimiento_hasta != '':
            vector = fecha_de_vencimiento_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            ventas = ventas.filter(fecha_de_vencimiento__lte=fecha)

        vendedor_id = self.request.GET.get('vendedor_id', '')
        if vendedor_id != '':
            ventas = ventas.filter(cliente__vendedor__id=vendedor_id)
            # ventas = ventas.filter(
            #    Q(pk__in=[i.venta_id for i in DetalleDeVenta.filter(orden_de_trabajo.vendedor_id=vendedor_id)]) | Q(pk__in=[i.venta_id for i in DetalleDeVenta2.filter(detalle_orden_de_trabajo.orden_de_trabajo.vendedor_id=vendedor_id)])
            # )

        return ventas.order_by('-id')

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''):
            lista_datos = []
            datos = self.get_queryset()
            for dato in datos:
                if dato.estado != 'A' and dato.saldo != 0:
                    lista_datos.append([
                        dato.get_numero_de_factura(),
                        dato.cliente.razon_social,
                        dato.fecha_de_emision.strftime("%d/%m/%Y"),
                        dato.fecha_de_vencimiento.strftime("%d/%m/%Y"),
                        separador_de_miles(dato.total),
                        separador_de_miles(dato.saldo),
                    ])

            titulos = ['Factura', 'Cliente', 'Emision', 'Vencimiento', 'Monto', 'Saldo']
            return listview_to_excel(lista_datos, 'facturas_vencidas', titulos)

        return super(CobroListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(CobroListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['clientes'] = Cliente.objects.all()
        context['cliente_id'] = int(self.request.GET.get('cliente_id', '')) if (self.request.GET.get('cliente_id', '') != '') else ''
        context['estado'] = self.request.GET.get('estado', '')
        context['empresas'] = Empresa.objects.all()
        context['empresa_id'] = int(self.request.GET.get('empresa_id', '')) if (self.request.GET.get('empresa_id', '') != '') else ''
        context['orden_de_trabajo'] = self.request.GET.get('orden_de_trabajo', '')
        context['fecha_de_emision_desde'] = self.request.GET.get('fecha_de_emision_desde', '')
        context['fecha_de_emision_hasta'] = self.request.GET.get('fecha_de_emision_hasta', '')
        context['fecha_de_vencimiento_desde'] = self.request.GET.get('fecha_de_vencimiento_desde', '')
        context['fecha_de_vencimiento_hasta'] = self.request.GET.get('fecha_de_vencimiento_hasta', '')
        context['vendedores'] = Funcionario.objects.all()
        context['vendedor_id'] = int(self.request.GET.get('vendedor_id', '')) if (self.request.GET.get('vendedor_id', '') != '') else ''
        return context


# @permission_required('venta.print_venta')
def imprimir_venta(request, pk):
    context = RequestContext(request)
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.estado = 'C'  # CONFIRMADO
        venta.save()
        return redirect('/admin/ventas/venta')

    mensaje = "Esta seguro que desea imprimir la Factura " + venta.get_numero_de_factura()

    return render_to_response("print_confirm.html", {'mensaje': mensaje, 'object': venta, }, context)


# @permission_required('venta.cancel_venta')
def anular_venta(request, pk):
    context = RequestContext(request)
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.estado = 'A'  # ANULADO
        # venta.fecha_de_anulacion = date.today

        venta.pagado = 0
        venta.saldo = venta.total
        venta.save()

        for detalle in venta.detallederecibo_set.all():
            detalle.cantidad = 0
            detalle.precio_unitario = 0
            detalle.subtotal = 0
            detalle.save()

        return redirect('/admin/ventas/venta/')

    mensaje = "Esta seguro que desea anular la Factura " + venta.get_numero_de_factura() + "? ADVERTENCIA: Se borraran todos los pagos efectuados de la factura y ya no se podran revertir"
    return render_to_response('venta_confirm.html', {'mensaje': mensaje}, context)


# @permission_required('venta.cancel_venta')
def cancelar_anular_venta(request, pk):
    context = RequestContext(request)
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.estado = 'C'  # CONFIRMADO
        venta.save()
        return redirect('/admin/ventas/venta/')

    mensaje = "Esta seguro que desea cancelar la anulacion de la Factura " + venta.get_numero_de_factura()
    return render_to_response('venta_confirm.html', {'mensaje': mensaje}, context)


def ventas_presentacion(request):
    context = RequestContext(request)
    titulo = "VENTAS"
    descripcion = "."
    return render_to_response('admin/presentacion.html', {'titulo': titulo, 'descripcion': descripcion}, context)


class RendicionListView(ListView):
    model = PresentacionCobros
    template_name = "rendicion_list.html"
    paginate_by = 30

    def get_queryset(self):
        rendiciones = PresentacionCobros.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            rendiciones = rendiciones.filter(id=q)

        cobrador_id = self.request.GET.get('cobrador_id', '')
        if cobrador_id != '':
            rendiciones = rendiciones.filter(cobrador__id=cobrador_id)

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            rendiciones = rendiciones.filter(fecha__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            rendiciones = rendiciones.filter(fecha__lte=fecha)

        nro_recibo = self.request.GET.get('recibo_id', '')
        if nro_recibo != '':
            rendiciones = rendiciones.filter(detallepresentacion__cobro__numero__icontains=nro_recibo)

        return rendiciones.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super(RendicionListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['cobradores'] = Funcionario.objects.all()
        context['cobrador_id'] = int(self.request.GET.get('cobrador_id', '')) if (
                self.request.GET.get('cobrador_id', '') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['recibo_id'] = self.request.GET.get('recibo_id', '') if (
                self.request.GET.get('recibo_id', '') != '') else ''

        return context