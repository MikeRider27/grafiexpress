from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.db.models import Sum

from clientes.models import Cliente
from empresas.models import Empresa
from produccion.models import OrdenDeTrabajo
from ventas.forms import SearchRemisionOTForm
from ventas.models import *
from funcionarios.models import Funcionario
from extra.globals import separador_de_miles, listview_to_excel


class RemisionDetailView(DetailView):
    model = Remision
    template_name = "remision_detail.html"

    def get_context_data(self, **kwargs):
        context = super(RemisionDetailView, self).get_context_data(**kwargs)
        context['detalles'] = DetalleDeRemision.objects.filter(remision=self.object)
        context['detalles2'] = DetalleDeRemision2.objects.filter(remision=self.object)
        return context


class RemisionListView(ListView):
    model = Remision
    template_name = "remision_list.html"
    paginate_by = 30

    def get_queryset(self):
        remisiones = Remision.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            vector = q.split("-")
            codigo_de_establecimiento = vector[0]
            punto_de_expedicion = vector[1]
            numero_de_remision = vector[2]
            remisiones = remisiones.filter(Q(codigo_de_establecimiento__contains=codigo_de_establecimiento) &
                                   Q(punto_de_expedicion__contains=punto_de_expedicion) &
                                   Q(numero_de_remision__contains=numero_de_remision))

        orden_de_trabajo = self.request.GET.get('orden_de_trabajo', '')
        if orden_de_trabajo != '':
            remisiones = remisiones.filter(
                Q(pk__in=[i.remision_id for i in DetalleDeRemision.objects.filter(orden_de_trabajo=orden_de_trabajo) ]) | Q(pk__in=[j.remision_id for j in DetalleDeRemision2.objects.filter(detalle_orden_de_trabajo__orden_de_trabajo=orden_de_trabajo) ])
            )

        cliente_id = self.request.GET.get('cliente_id', '')
        if cliente_id != '':
            remisiones = remisiones.filter(cliente__id=cliente_id)

        estado = self.request.GET.get('estado', 'P')
        if estado != 'TODOS':
            remisiones = remisiones.filter(estado=estado)

        empresa_id = self.request.GET.get('empresa_id', '')
        if empresa_id != '':
            remisiones = remisiones.filter(empresa_id=empresa_id)

        fecha_de_emision_desde = self.request.GET.get('fecha_de_emision_desde', '')
        if fecha_de_emision_desde != '':
            vector = fecha_de_emision_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            remisiones = remisiones.filter(fecha_de_emision__gte=fecha)

        fecha_de_emision_hasta = self.request.GET.get('fecha_de_emision_hasta', '')
        if fecha_de_emision_hasta != '':
            vector = fecha_de_emision_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            remisiones = remisiones.filter(fecha_de_emision__lte=fecha)

        estado = self.request.GET.get('estado', 'P')
        if estado != 'TODOS':
            remisiones = remisiones.filter(estado=estado)

        facturado = self.request.GET.get('facturado', 'NO')
        if facturado != 'TODOS':
            if facturado == 'SI':
                remisiones = remisiones.filter(pk__in=[i.remision_id for i in VentaRemision.objects.exclude(venta__estado='A')])
            else: #facturado == NO
                remisiones = remisiones.exclude(pk__in=[i.remision_id for i in VentaRemision.objects.exclude(venta__estado='A')])

        es_administrador = False
        grupos = self.request.user.groups.values_list('name', flat=True)
        for grupo in grupos:
            if grupo == 'administracion':
                es_administrador = True
                pass

        if not (self.request.user.is_superuser or es_administrador):
            vendedor = Funcionario.objects.filter(usuario_id=self.request.user.pk)
            remisiones = remisiones.filter(cliente__vendedor=vendedor)
        else:
            vendedor_id = self.request.GET.get('vendedor_id', '')
            if vendedor_id != '':
                remisiones = remisiones.filter(cliente__vendedor__id=vendedor_id)
                
        return remisiones.order_by('-id')

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''):
            lista_datos = []
            datos = self.get_queryset().exclude(estado=ANULADO)
            for dato in datos:
                ots = DetalleDeRemision.objects.filter(remision=dato)
                otsConCambios = DetalleDeRemision2.objects.filter(remision=dato)
                ordenes = ' '
                for ot in ots:
                    ordenes += '[' + str(ot.orden_de_trabajo_id) + '] ' + ot.descripcion + ', '

                for otConCambio in otsConCambios:
                    ordenes += '[' + str(
                        otConCambio.detalle_orden_de_trabajo.orden_de_trabajo_id) + '] ' + otConCambio.descripcion + '; '

                if dato.estado != 'A':
                    lista_datos.append([
                        dato.get_numero_de_remision(),
                        dato.cliente.razon_social,
                        dato.fecha_de_expedicion.strftime("%d/%m/%Y"),
                        dato.empresa.nombre,
                        ordenes
                    ])

            titulos = ['Remision', 'Cliente', 'Fecha Expedicion', 'Empresa', 'Ordenes de trabajo']
            return listview_to_excel(lista_datos, 'Remisiones', titulos)

        return super(RemisionListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(RemisionListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        es_administrador = False
        grupos = self.request.user.groups.values_list('name', flat=True)
        for grupo in grupos:
            if grupo == 'administracion':
                es_administrador = True
                pass

        if self.request.user.is_superuser or es_administrador:
            context['clientes'] = Cliente.objects.all()
        else:
            vendedor = Funcionario.objects.filter(usuario_id=self.request.user.pk)
            context['clientes'] = Cliente.objects.filter(vendedor=vendedor)
        context['cliente_id'] = int(self.request.GET.get('cliente_id', '')) if (self.request.GET.get('cliente_id', '') != '') else ''
        context['estado'] = self.request.GET.get('estado', 'P')
        context['orden_de_trabajo'] = self.request.GET.get('orden_de_trabajo', '')
        context['empresas'] = Empresa.objects.all()
        context['empresa_id'] = int(self.request.GET.get('empresa_id', '')) if (self.request.GET.get('empresa_id', '') != '') else ''
        context['fecha_de_emision_desde'] = self.request.GET.get('fecha_de_emision_desde', '')
        context['fecha_de_emision_hasta'] = self.request.GET.get('fecha_de_emision_hasta', '')
        context['facturado'] = self.request.GET.get('facturado', 'NO')
        context['vendedores'] = Funcionario.objects.all()
        context['vendedor_id'] = int(self.request.GET.get('vendedor_id', '')) if \
            (self.request.GET.get('vendedor_id', '') != '') else ''
        return context

#@permission_required('venta.print_remision')
def imprimir_remision(request, pk):
    context = RequestContext(request)
    remision = get_object_or_404(Remision, pk=pk)
    if request.method == 'POST':
        remision.estado = 'C'  # CONFIRMADO
        remision.save()
        return redirect('/admin/ventas/remision')

    mensaje = "Esta seguro que desea imprimir la Nota de Remision " + remision.get_numero_de_remision()
    return render_to_response('print_confirm.html', {'mensaje': mensaje, 'object':remision}, context)

#@permission_required('venta.cancel_remision')
def anular_remision(request, pk):
    context = RequestContext(request)
    remision = get_object_or_404(Remision, pk=pk)
    if request.method == 'POST':
        remision.estado = 'A'  # ANULADO
        remision.save()

        detalles = DetalleDeRemision.objects.filter(remision_id=remision.id)
        for detalle in detalles:
            orden_de_trabajo = detalle.orden_de_trabajo
            orden_de_trabajo.actualizar_cantidades()

        detalles = DetalleDeRemision2.objects.filter(remision_id=remision.id)
        for detalle in detalles:
            orden_de_trabajo = detalle.detalle_orden_de_trabajo.orden_de_trabajo
            orden_de_trabajo.actualizar_cantidades()

        return redirect('/admin/ventas/remision/')

    mensaje = "Esta seguro que desea anular la Remision " + remision.get_numero_de_remision()
    return render_to_response('venta_confirm.html', {'mensaje': mensaje}, context)


#@permission_required('venta.cancel_remision')
def cancelar_anular_remision(request, pk):
    context = RequestContext(request)
    remision = get_object_or_404(Remision, pk=pk)
    if request.method == 'POST':
        remision.estado = 'C'  # CONFIRMADO
        remision.save()

        detalles = DetalleDeRemision.objects.filter(remision_id=remision.id)
        for detalle in detalles:
            orden_de_trabajo = detalle.orden_de_trabajo
            orden_de_trabajo.actualizar_cantidades()

        detalles = DetalleDeRemision2.objects.filter(remision_id=remision.id)
        for detalle in detalles:
            orden_de_trabajo = detalle.detalle_orden_de_trabajo.orden_de_trabajo
            orden_de_trabajo.actualizar_cantidades()

        return redirect('/admin/ventas/remision/')

    mensaje = "Esta seguro que desea cancelar la anulacion de la Remision " + remision.get_numero_de_remision()
    return render_to_response('venta_confirm.html', {'mensaje': mensaje}, context)


class VentaDetailView(DetailView):
    model = Venta
    template_name = "venta_detail.html"

    def get_context_data(self, **kwargs):
        context = super(VentaDetailView, self).get_context_data(**kwargs)
        context['detalles'] = DetalleDeVenta.objects.filter(venta_id=self.object.id)
        context['detalles2'] = DetalleDeVenta2.objects.filter(venta_id=self.object.id)
        return context


class VentaListView(ListView):
    model = Venta
    template_name = "venta_list.html"
    paginate_by = 30

    def get_queryset(self):
        ventas = Venta.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            ventas = ventas.filter(numero_de_factura__icontains=q)

        orden_de_trabajo = self.request.GET.get('orden_de_trabajo', '')
        if orden_de_trabajo != '':
            ventas = ventas.filter(
                Q(pk__in=[i.venta_id for i in DetalleDeVenta.objects.filter(orden_de_trabajo=orden_de_trabajo)])
                | Q(pk__in=[j.venta_id for j in DetalleDeVenta2.objects.filter(detalle_orden_de_trabajo__orden_de_trabajo=orden_de_trabajo)])
            )

        cliente_id = self.request.GET.get('cliente_id', '')
        if cliente_id != '':
            ventas = ventas.filter(cliente_id=cliente_id)

        empresa_id = self.request.GET.get('empresa_id', '')
        if empresa_id != '':
            ventas = ventas.filter(empresa_id=empresa_id)

        estado = self.request.GET.get('estado', 'P')
        if estado != 'TODOS':
            if estado == 'NN':
                ventas = ventas.exclude(estado='A')
            else:
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

        es_administrador = False
        grupos = self.request.user.groups.values_list('name', flat=True)
        for grupo in grupos:
            if grupo == 'administracion' or grupo == 'gerencia_ventas':
                es_administrador = True
                pass

        if not (self.request.user.is_superuser or es_administrador):
            vendedor = Funcionario.objects.filter(usuario_id=self.request.user.pk)
            ventas = ventas.filter(cliente__vendedor=vendedor)
        else:
            vendedor_id = self.request.GET.get('vendedor_id', '')
            if vendedor_id != '':
                ventas = ventas.filter(cliente__vendedor__id=vendedor_id)

        return ventas.order_by('-id')

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''): 
            lista_datos=[]
            datos = self.get_queryset().exclude(estado=ANULADO)
            for dato in datos:
                ots = DetalleDeVenta.objects.filter(venta=dato)
                otsConCambios = DetalleDeVenta2.objects.filter(venta=dato)
                ordenes = ' '
                for ot in ots:
                    ordenes += '[' + str(ot.orden_de_trabajo_id) + '] ' + ot.descripcion + ', '

                for otConCambio in otsConCambios:
                    ordenes += '[' + str(otConCambio.detalle_orden_de_trabajo.orden_de_trabajo_id) + '] ' + otConCambio.descripcion + '; '

                if dato.estado != 'A':
                    lista_datos.append([
                        dato.get_numero_de_factura(),
                        dato.cliente.razon_social,
                        dato.fecha_de_emision.strftime("%d/%m/%Y"),
                        dato.fecha_de_vencimiento.strftime("%d/%m/%Y"),
                        separador_de_miles(dato.total),
                        separador_de_miles(dato.saldo),
                        dato.estado,
                        ordenes
                    ])

            titulos = ['Factura', 'Cliente', 'Emision', 'Vencimiento', 'Monto', 'Saldo', 'Estado', 'Ordenes de trabajo']
            return listview_to_excel(lista_datos, 'Ventas', titulos)
        
        return super(VentaListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(VentaListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        es_administrador = False
        grupos = self.request.user.groups.values_list('name', flat=True)
        for grupo in grupos:
            if grupo == 'administracion' or grupo == 'gerencia_ventas':
                es_administrador = True
                pass

        if self.request.user.is_superuser or es_administrador:
            context['clientes'] = Cliente.objects.all()
        else:
            vendedor = Funcionario.objects.filter(usuario_id=self.request.user.pk)
            context['clientes'] = Cliente.objects.filter(vendedor=vendedor)

        context['cliente_id'] = int(self.request.GET.get('cliente_id', '')) if (self.request.GET.get('cliente_id', '') != '') else ''
        context['estado'] = self.request.GET.get('estado', 'P')
        context['empresas'] = Empresa.objects.all()
        context['empresa_id'] = int(self.request.GET.get('empresa_id', '')) if (self.request.GET.get('empresa_id', '') != '') else ''
        context['orden_de_trabajo'] = self.request.GET.get('orden_de_trabajo', '')
        context['fecha_de_emision_desde'] = self.request.GET.get('fecha_de_emision_desde', '')
        context['fecha_de_emision_hasta'] = self.request.GET.get('fecha_de_emision_hasta', '')
        context['fecha_de_vencimiento_desde'] = self.request.GET.get('fecha_de_vencimiento_desde', '')
        context['fecha_de_vencimiento_hasta'] = self.request.GET.get('fecha_de_vencimiento_hasta', '')
        context['total_general'] = self.get_queryset().aggregate(total_general=Sum('total')).get('total_general')
        context['vendedores'] = Funcionario.objects.all()
        context['vendedor_id'] = int(self.request.GET.get('vendedor_id', '')) if (self.request.GET.get('vendedor_id', '') != '') else ''
        return context


#@permission_required('venta.print_venta')
def imprimir_venta(request, pk):
    context = RequestContext(request)
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.estado = 'C'  # CONFIRMADO
        venta.save()
        return redirect('/admin/ventas/venta')

    mensaje = "Esta seguro que desea imprimir la Factura " + venta.get_numero_de_factura()

    return render_to_response("print_confirm.html", {'mensaje': mensaje, 'object':venta,}, context)


#@permission_required('venta.cancel_venta')
def anular_venta(request, pk):
    context = RequestContext(request)
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.estado = 'A'  # ANULADO
        # venta.fecha_de_anulacion = date.today
        venta.total = 0
        venta.pagado = 0
        venta.saldo = venta.total
        
        venta.save() 

        for detalle in venta.detallederecibo_set.all():
            detalle.cantidad = 0
            detalle.precio_unitario = 0
            detalle.subtotal = 0
            detalle.save()

        detalles = DetalleDeVenta.objects.filter(venta_id=venta.id)
        for detalle in detalles:
            orden_de_trabajo = detalle.orden_de_trabajo
            orden_de_trabajo.actualizar_cantidades_facturadas()

        detalles = DetalleDeVenta2.objects.filter(venta_id=venta.id)
        for detalle in detalles:
            orden_de_trabajo = detalle.detalle_orden_de_trabajo.orden_de_trabajo
            orden_de_trabajo.actualizar_cantidades_facturadas()

        return redirect('/admin/ventas/venta/')

    mensaje = "Esta seguro que desea anular la Factura " + venta.get_numero_de_factura() + "? ADVERTENCIA: Se borraran todos los pagos efectuados de la factura y ya no se podran revertir"
    return render_to_response('venta_confirm.html', {'mensaje': mensaje}, context)


#@permission_required('venta.cancel_venta')
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


class VentaRemisionesView(DetailView):
    model = Venta
    template_name = "venta_remisiones_form.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        form = SearchRemisionOTForm(request.GET)
        rem_ids = []
        if form.is_valid():
            ot_queryset = OrdenDeTrabajo.objects.filter(detallederemision__remision__venta=self.object)
            if form.cleaned_data['nombre']:
               ot_queryset = ot_queryset.filter(nombre__icontains=form.cleaned_data['nombre'])

            if form.cleaned_data['numero']:
                ot_queryset = ot_queryset.filter(pk__icontains=form.cleaned_data['numero'])

            for o in ot_queryset:
                for d in o.detallederemision_set.all():
                    rem_ids.append(d.remision_id)

        context['remisiones'] = Remision.objects.filter(venta=self.object,pk__in=rem_ids).distinct('id')
        context['form'] = form
        return self.render_to_response(context)


# ---------------------------------------------------------------------------
# Notas de crédito: imprimir (marca como impresa) y anular
# ---------------------------------------------------------------------------
from django.contrib.auth.decorators import permission_required


@permission_required('ventas.print_notadecredito', raise_exception=True)
def imprimir_nota_de_credito(request, pk):
    context = RequestContext(request)
    nota = get_object_or_404(NotaDeCredito, pk=pk)
    if nota.estado == ANULADO:
        return redirect('/admin/ventas/notadecredito/')
    if request.method == 'POST':
        nota.estado = CONFIRMADO
        nota.save()
        return redirect('/admin/ventas/notadecredito/')

    mensaje = "¿Imprimir la Nota de crédito " + nota.get_numero() + "?"
    return render_to_response("print_confirm.html", {'mensaje': mensaje, 'object': nota}, context)


@permission_required('ventas.cancel_notadecredito', raise_exception=True)
def anular_nota_de_credito(request, pk):
    context = RequestContext(request)
    nota = get_object_or_404(NotaDeCredito, pk=pk)
    if request.method == 'POST' and nota.estado != ANULADO:
        nota.estado = ANULADO
        nota.save()  # la factura recupera el saldo en NotaDeCredito.save()
        return redirect('/admin/ventas/notadecredito/')

    mensaje = ("¿Anular la Nota de crédito " + nota.get_numero() + "? " +
               ("La factura " + nota.venta.get_numero_de_factura() + " recupera el saldo acreditado. "
                if nota.afecta_saldo else "") + "La anulación no se puede revertir.")
    return render_to_response('venta_confirm.html', {'mensaje': mensaje}, context)
