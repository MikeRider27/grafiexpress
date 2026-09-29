from django.shortcuts import get_object_or_404
import time
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import _user_has_perm
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.db.models import Q, F
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas

from extra.globals import *

from datetime import date

from grafiexpress.globales import separar
from produccion.models import *
from funcionarios.models import *
from produccion.reports import calendario_por_maquina
from ventas.models import DetalleDeVenta, DetalleDeVenta2, Remision, DetalleDeRemision, DetalleDeRemision2, Venta


class OrdenDeTrabajoDetailView(DetailView):
    model = OrdenDeTrabajo
    template_name = "ordendetrabajo_detail.html"

    def get_context_data(self, **kwargs):
        context = super(OrdenDeTrabajoDetailView, self).get_context_data(**kwargs)
        context['detalles'] = DetalleOrdenDeTrabajo.objects.filter(orden_de_trabajo=self.object)
        context['remisiones'] = Remision.objects.filter(Q(pk__in=[i.remision_id for i in DetalleDeRemision.objects.filter(orden_de_trabajo=self.object)]) | Q(pk__in=[j.remision_id for j in DetalleDeRemision2.objects.filter(detalle_orden_de_trabajo__orden_de_trabajo=self.object)])).exclude(estado='A')
        context['detalles_de_remisiones'] = DetalleDeRemision.objects.filter(orden_de_trabajo=self.object).exclude(remision__estado='A')
        context['detalles_de_remisiones2'] = DetalleDeRemision2.objects.filter(detalle_orden_de_trabajo__orden_de_trabajo=self.object).exclude(remision__estado='A')
        context['ventas'] = Venta.objects.filter(Q(pk__in=[i.venta_id for i in DetalleDeVenta.objects.filter(orden_de_trabajo=self.object)]) | Q(pk__in=[j.venta_id for j in DetalleDeVenta2.objects.filter(detalle_orden_de_trabajo__orden_de_trabajo=self.object)])).exclude(estado='A')
        context['detalles_de_ventas'] = DetalleDeVenta.objects.filter(orden_de_trabajo=self.object).exclude(
            venta__estado='A')
        context['detalles_de_ventas2'] = DetalleDeVenta2.objects.filter(
            detalle_orden_de_trabajo__orden_de_trabajo=self.object).exclude(venta__estado='A')
        return context


class OrdenDeTrabajoListView(ListView):
    model = OrdenDeTrabajo
    template_name = "ordendetrabajo_list.html"
    paginate_by = 30

    def get_queryset(self):
        ordenes_de_trabajo = OrdenDeTrabajo.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            ordenes_de_trabajo = ordenes_de_trabajo.filter(Q(id__istartswith=q) | Q(nombre__icontains=q))

        cliente_id = self.request.GET.get('cliente_id', '')
        if cliente_id != '':
            ordenes_de_trabajo = ordenes_de_trabajo.filter(cliente__id=cliente_id)

        vendedor = Funcionario.objects.filter(usuario=self.request.user).first()
        if not self.request.user.is_superuser and vendedor:
            vendedor_id = self.request.GET.get('vendedor_id', '')
            # Solo quien puede ver todas las OTs elige otro vendedor; el resto ve lo suyo
            if vendedor_id != '' and self.request.user.has_perm('produccion.view_all_ots'):
                ordenes_de_trabajo = ordenes_de_trabajo.filter(vendedor__id=vendedor_id)
            else:
                ordenes_de_trabajo = ordenes_de_trabajo.filter(vendedor__id=vendedor.id)
        else:
            vendedor_id = self.request.GET.get('vendedor_id', '')
            if vendedor_id != '':
                ordenes_de_trabajo = ordenes_de_trabajo.filter(vendedor__id=vendedor_id)

        estado = self.request.GET.get('estado', 'TODOS')
        if estado != 'TODOS':
            ordenes_de_trabajo = ordenes_de_trabajo.filter(estado=estado)

        anulada = self.request.GET.get('anulada', 'NO')
        if anulada != 'TODOS':
            if anulada == 'SI':
                ordenes_de_trabajo = ordenes_de_trabajo.filter(anulada=True)
            else:
                ordenes_de_trabajo = ordenes_de_trabajo.filter(anulada=False)

        entregado = self.request.GET.get('entregado', 'TODOS')
        if entregado != 'TODOS':
            if entregado == 'ENTREGADO TOTALMENTE':
                ordenes_de_trabajo = ordenes_de_trabajo.filter(restante=0)

            elif entregado == 'ENTREGADO PARCIALMENTE':
                ordenes_de_trabajo = ordenes_de_trabajo.exclude(entregado=0).exclude(restante=0)

            elif entregado == 'NO ENTREGADO':
                ordenes_de_trabajo = ordenes_de_trabajo.filter(entregado=0)
            else:
                pass

        fecha_de_ingreso_desde = self.request.GET.get('fecha_de_ingreso_desde', '')
        if fecha_de_ingreso_desde != '':
            vector = fecha_de_ingreso_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            ordenes_de_trabajo = ordenes_de_trabajo.filter(fecha_de_ingreso__gte=fecha)

        fecha_de_ingreso_hasta = self.request.GET.get('fecha_de_ingreso_hasta', '')
        if fecha_de_ingreso_hasta != '':
            vector = fecha_de_ingreso_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            ordenes_de_trabajo = ordenes_de_trabajo.filter(fecha_de_ingreso__lte=fecha)

        fecha_solicitada_desde = self.request.GET.get('fecha_solicitada_desde', '')
        if fecha_solicitada_desde != '':
            vector = fecha_solicitada_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            ordenes_de_trabajo = ordenes_de_trabajo.filter(fecha_solicitada__gte=fecha)

        fecha_solicitada_hasta = self.request.GET.get('fecha_solicitada_hasta', '')
        if fecha_solicitada_hasta != '':
            vector = fecha_solicitada_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            ordenes_de_trabajo = ordenes_de_trabajo.filter(fecha_solicitada__lte=fecha)

        facturado = self.request.GET.get('facturado', 'TODOS')
        if facturado != 'TODOS':
            if facturado == 'FACTURADO':
                ordenes_de_trabajo = ordenes_de_trabajo.filter(cantidad_no_facturada=0)
            elif facturado == 'PARCIALMENTE':
                ordenes_de_trabajo = ordenes_de_trabajo.filter(cantidad_no_facturada__gte=1).filter(cantidad_facturada__gte=1)
            else:
                ordenes_de_trabajo = ordenes_de_trabajo.filter(cantidad_facturada=0)

        cliente_requiere_oc = self.request.GET.get('cliente_requiere_oc', 'TODOS')
        if cliente_requiere_oc != 'TODOS':
            if cliente_requiere_oc == 'SI':
                ordenes_de_trabajo = ordenes_de_trabajo.filter(cliente__requiere_orden_de_compra_del_proveedor=True)
            else:
                ordenes_de_trabajo = ordenes_de_trabajo.exclude(cliente__requiere_orden_de_compra_del_proveedor=True)

        return ordenes_de_trabajo.order_by("-id")

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''): 

            lista_datos = []
            datos = self.get_queryset()
            total_general = 0
            total_sin_facturar = 0
            for dato in datos:
                total = dato.get_total()
                sin_facturar = dato.precio_unitario*dato.cantidad_no_facturada
                lista_datos.append([
                    dato.id,
                    dato.nombre,
                    dato.cliente.razon_social,
                    dato.fecha_de_ingreso.strftime("%d/%m/%Y"),
                    separador_de_miles(dato.cantidad),
                    separador_de_miles(dato.precio_unitario),
                    separador_de_miles(dato.entregado),
                    separador_de_miles(dato.restante),
                    separador_de_miles(dato.cantidad_no_facturada),
                    separador_de_miles(sin_facturar),
                    separador_de_miles(total)
                ])
                total_general = total_general + total
                total_sin_facturar = total_sin_facturar + sin_facturar

            lista_datos.append(['', '', '', '', '', '', '', '', 'TOTALES', separador_de_miles(total_sin_facturar), separador_de_miles(total_general)])

            titulos = ['OT', 'Descripcion', 'Cliente', 'Fecha', 'Cantidad', 'Precio Unit', 'Cant. entregada',
                       'Cant. restante', 'Sin facturar', 'Pendiente de facturacion', 'Total de factura']
            return listview_to_excel(lista_datos, 'ordenes_trabajo', titulos)
        
        return super(OrdenDeTrabajoListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrdenDeTrabajoListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['clientes'] = Cliente.objects.all()
        context['cliente_id'] = int(self.request.GET.get('cliente_id', '')) if (self.request.GET.get('cliente_id', '') != '') else ''
        context['cliente_requiere_oc'] = self.request.GET.get('cliente_requiere_oc', 'TODOS') if (self.request.GET.get('cliente_requiere_oc', 'TODOS') != 'TODOS') else 'TODOS'
        context['estado'] = self.request.GET.get('estado', 'TODOS')
        context['fecha_de_ingreso_desde'] = self.request.GET.get('fecha_de_ingreso_desde', '')
        context['fecha_de_ingreso_hasta'] = self.request.GET.get('fecha_de_ingreso_hasta', '')
        context['fecha_solicitada_desde'] = self.request.GET.get('fecha_solicitada_desde', '')
        context['fecha_solicitada_hasta'] = self.request.GET.get('fecha_solicitada_hasta', '')
        context['entregado'] = self.request.GET.get('entregado', 'TODOS')
        context['vendedores'] = Funcionario.objects.all()
        context['vendedor_id'] = int(self.request.GET.get('vendedor_id', '')) if (self.request.GET.get('vendedor_id', '') != '') else ''
        context['facturado'] = self.request.GET.get('facturado', 'TODOS')
        context['anulada'] = self.request.GET.get('anulada', 'NO')
        context['usuario_id'] = str(Funcionario.objects.filter(usuario=self.request.user).first().id) if Funcionario.objects.filter(usuario=self.request.user) else ''
        context['conteo_ots'] = self.get_queryset().count()
        context['total_sin_facturar'] = self.get_queryset().aggregate(total_sin_facturar=Sum(F('precio_unitario') * F('cantidad_no_facturada'))).get('total_sin_facturar')
        return context


#@permission_required('orden_de_trabajo.cancel_orden_de_trabajo')
def marcar_orden_de_trabajo_aprobada(request, orden_de_trabajo_id):
    context = RequestContext(request)
    orden_de_trabajo = get_object_or_404(OrdenDeTrabajo, pk=orden_de_trabajo_id)
    if request.method == 'POST':
        orden_de_trabajo.prueba_realizada = True  
        orden_de_trabajo.save()
        return redirect('/admin/produccion/ordendetrabajo/')

    mensaje = "Desea marcar como aprobada la orden de trabajo " + separador_de_miles(orden_de_trabajo.id)
    return render_to_response('admin/confirm.html', {'mensaje': mensaje}, context)


def marcar_orden_de_trabajo_desaprobada(request, orden_de_trabajo_id):
    context = RequestContext(request)
    orden_de_trabajo = get_object_or_404(OrdenDeTrabajo, pk=orden_de_trabajo_id)
    if request.method == 'POST':
        orden_de_trabajo.prueba_realizada = False  
        orden_de_trabajo.save()
        return redirect('/admin/produccion/ordendetrabajo/')

    mensaje = "Desea marcar como no aprobada la orden de trabajo " + separador_de_miles(orden_de_trabajo.id)
    return render_to_response('admin/confirm.html', {'mensaje': mensaje}, context)


#@permission_required('orden_de_trabajo.cancel_orden_de_trabajo')
def anular_orden_de_trabajo(request, orden_de_trabajo_id):
    context = RequestContext(request)
    orden_de_trabajo = get_object_or_404(OrdenDeTrabajo, pk=orden_de_trabajo_id)
    if request.method == 'POST':
        orden_de_trabajo.anulada = True  
        orden_de_trabajo.save()
        return redirect('/admin/produccion/ordendetrabajo/')

    mensaje = "Desea anular la orden de trabajo " + separador_de_miles(orden_de_trabajo.id) + " ?"
    return render_to_response('admin/confirm.html', {'mensaje': mensaje}, context)


def desanular_orden_de_trabajo(request, orden_de_trabajo_id):
    context = RequestContext(request)
    orden_de_trabajo = get_object_or_404(OrdenDeTrabajo, pk=orden_de_trabajo_id)
    if request.method == 'POST':
        orden_de_trabajo.anulada = False  
        orden_de_trabajo.save()
        return redirect('/admin/produccion/ordendetrabajo/')

    mensaje = "Desea revertir la anulacion de la orden de trabajo " + separador_de_miles(orden_de_trabajo.id) + " ?"
    return render_to_response('admin/confirm.html', {'mensaje': mensaje}, context)

class CategoriaDeTrabajoListView(ListView):
    model = CategoriaDeTrabajo
    template_name = 'categoriadetrabajo_list.html'
    paginate_by = 30

    def get_queryset(self):
        categorias = CategoriaDeTrabajo.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            categorias = categorias.filter(nombre__startswith=q)
        return categorias


class CategoriaDeTrabajoDetailView(DetailView):
    model = CategoriaDeTrabajo
    template_name = 'categoriadetrabajo_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CategoriaDeTrabajoDetailView, self).get_context_data(**kwargs)
        context['subcategorias'] = SubcategoriaDeTrabajo.objects.filter(categoria=self.object)
        return context

    def get_context_data(self, **kwargs):
        context = super(CategoriaDeTrabajoDetailView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class CostoListView(ListView):
    model = Costo
    template_name = "costo_list.html"
    paginate_by = 30

    def get_queryset(self):
        costos = Costo.objects.all().order_by("-id")

        q = self.request.GET.get('q', '')
        if q != '':
            costos = costos.filter(Q(detalle_orden_de_trabajo__orden_de_trabajo__id__istartswith=q) | Q(
                detalle_orden_de_trabajo__descripcion__icontains=q) | Q(id__istartswith=q))

        cliente_id = self.request.GET.get('cliente_id', '')
        if cliente_id != '':
            costos = costos.filter(detalle_orden_de_trabajo__orden_de_trabajo__cliente__id=cliente_id)

        return costos

    def get_context_data(self, **kwargs):
        context = super(CostoListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['clientes'] = Cliente.objects.all()
        context['cliente_id'] = int(self.request.GET.get('cliente_id', '')) if (self.request.GET.get('cliente_id', '') != '') else ''
        return context


class CostoDetailView(DetailView):
    model = Costo
    template_name = "costo_detail.html"

    def get_context_data(self, **kwargs):
        context = super(CostoDetailView, self).get_context_data(**kwargs)
        context['papeles'] = PapelCosto.objects.filter(costo=self.object)
        context['preprensas'] = PreprensaCosto.objects.filter(costo=self.object)
        context['troqueles'] = TroquelCosto.objects.filter(costo=self.object)
        context['posprensaservicios'] = PosprensaServicioCosto.objects.filter(costo=self.object)
        context['posprensamateriales'] = PosprensaMaterialCosto.objects.filter(costo=self.object)
        context['posprensaotroservicios'] = PosprensaOtroServicioCosto.objects.filter(costo=self.object)
        context['datosdebolsas'] = DatosDeBolsaCosto.objects.filter(costo=self.object)
        context['revistas'] = RevistaCosto.objects.filter(costo=self.object)
        context['compuestos'] = CompuestoCosto.objects.filter(costo=self.object)
        context['plastificados'] = PlastificadoCosto.objects.filter(costo=self.object)
        context['otrosgastos'] = OtroGastoCosto.objects.filter(costo=self.object)    
        return context


def produccion_presentacion(request):
    context = RequestContext(request)
    titulo = "PRODUCCION"
    descripcion = "."
    return render_to_response('admin/presentacion.html', {'titulo': titulo, 'descripcion': descripcion}, context)


class ProcesoListView(ListView):
    model = Proceso
    template_name = "proceso_list.html"
    paginate_by = 30

    def get_queryset(self):
        procesos = Proceso.objects.all().order_by("-id")

        q = self.request.GET.get('q', '')
        if q != '':
            procesos = procesos.filter(Q(orden_de_trabajo_id=q) | Q(id__istartswith=q))

        estado = self.request.GET.get('estado', 'TODOS')
        if estado != 'TODOS':
            procesos = procesos.filter(orden_de_trabajo__estado_produccion=estado)

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            procesos = procesos.filter(fecha_de_creacion__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            procesos = procesos.filter(fecha_de_creacion__lte=fecha)

        return procesos

    def get_context_data(self, **kwargs):
        context = super(ProcesoListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', 'TODOS')
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        return context


class ProgramacionListView(ListView):
    model = Programacion
    template_name = "programacion_list.html"
    paginate_by = 30

    def get_queryset(self):
        programaciones = Programacion.objects.all().order_by("-id")

        q = self.request.GET.get('q', '')
        if q != '':
            programaciones = programaciones.filter(id__istartswith=q)

        maquina_id = self.request.GET.get('maquina_id', '')
        if maquina_id != '':
            programaciones = programaciones.filter(maquina_id=maquina_id)

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            programaciones = programaciones.filter(fecha_de_inicio__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            programaciones = programaciones.filter(fecha_de_inicio__lte=fecha)

        return programaciones

    def render_to_response(self, context, **response_kwargs):
        if 'imprimir' in self.request.GET.get('imprimir', ''):
            def contenido(canvas, datos):
                from reportlab.lib.colors import darkblue, black
                canvas.setFillColor(darkblue)
                canvas.setFillColor(black)
                canvas.setStrokeColor(black)
                canvas.setPageSize(landscape(A4))

                for dato in datos:
                    canvas.setFont("Helvetica", 12)
                    canvas.drawString(30, 570, "Fecha de inicio:")
                    canvas.setFont("Helvetica", 13)
                    canvas.drawString(140, 570, dato.fecha_de_inicio.strftime('%d/%m/%Y'))

                    canvas.setFont("Helvetica", 12)
                    canvas.drawString(30, 550, "Fecha de entrega:")
                    canvas.setFont("Helvetica", 13)
                    canvas.drawString(140, 550, dato.fecha_de_entrega.strftime('%d/%m/%Y'))

                    canvas.setFont("Helvetica", 12)
                    canvas.drawString(30, 530, "Maquina:")
                    canvas.setFont("Helvetica", 13)
                    canvas.drawString(140, 530, str(dato.maquina))

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
                    programaciones = DetalleProgramacion.objects.filter(programacion=dato)
                    for programacion in programaciones:
                        row -= 20
                        canvas.drawString(40, row,
                                          force_text(programacion.detalle_proceso.proceso.orden_de_trabajo)[:38])
                        canvas.line(255, row - 5, 255, row + 40)
                        canvas.drawString(260, row, force_text(
                            programacion.detalle_proceso.proceso.orden_de_trabajo.cliente.razon_social[:15]))
                        canvas.line(373, row - 5, 373, row + 40)
                        canvas.drawString(370, row, separar(int(round(programacion.pliegos))).rjust(15))
                        canvas.line(430, row - 5, 430, row + 40)
                        canvas.drawString(430, row,
                                          separar(int(round(programacion.detalle_proceso.pasadas_por_pliego))).rjust(
                                              15))
                        canvas.line(485, row - 5, 485, row + 40)
                        canvas.drawString(490, row, programacion.hora_de_inicio.strftime('%H:%M'))
                        canvas.line(525, row - 5, 525, row + 40)
                        canvas.drawString(530, row, programacion.hora_de_finalizacion.strftime('%H:%M'))
                        canvas.line(565, row - 5, 565, row + 40)
                        canvas.line(605, row - 5, 605, row + 40)
                        canvas.line(645, row - 5, 645, row + 40)
                        canvas.line(720, row - 5, 720, row + 40)
                        canvas.line(20, row - 5, 820, row - 5)

                    canvas.line(20, 520, 20, row - 5)
                    canvas.line(820, 520, 820, row - 5)

                    row -= 30
                    canvas.setFont("Helvetica", 10)
                    canvas.drawString(30, 20, "Fecha: %s" % time.strftime("%Y/%m/%d"))
                    canvas.drawString(200, 20, "Hora: %s" % time.strftime("%X"))
                    canvas.showPage()

            datos = self.get_queryset()
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="calendario_lista.pdf"'
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            contenido(p, datos)
            p.save()
            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response

        return super(ProgramacionListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProgramacionListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['maquinas'] = Maquina.objects.exclude(activa=False)
        context['maquina_id'] = int(self.request.GET.get('maquina_id', '')) if (self.request.GET.get('maquina_id', '') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        return context


class ProduccionListView(ListView):
    model = Produccion
    template_name = "produccion_list.html"
    paginate_by = 30

    def get_queryset(self):
        producciones = Produccion.objects.all().order_by("-id")

        q = self.request.GET.get('q', '')
        if q != '':
            producciones = producciones.filter(id__istartswith=q)

        maquina_id = self.request.GET.get('maquina_id', '')
        if maquina_id != '':
            producciones = producciones.filter(programacion__maquina_id=maquina_id)

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            producciones = producciones.filter(fecha_de_creacion__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            producciones = producciones.filter(fecha_de_creacion__lte=fecha)

        return producciones

    def get_context_data(self, **kwargs):
        context = super(ProduccionListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['maquinas'] = Maquina.objects.exclude(activa=False)
        context['maquina_id'] = int(self.request.GET.get('maquina_id', '')) if (
                    self.request.GET.get('maquina_id', '') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        return context


class AgendaMaquinaDetailView(DetailView):
    model = Maquina
    template_name = "agenda_maquina.html"

    def get_context_data(self, **kwargs):
        context = super(AgendaMaquinaDetailView, self).get_context_data(**kwargs)
        context['detalles'] = sorted(DetalleProceso.objects.filter(maquina=self.object), key=lambda t: t.fecha_hora_inicio, reverse=True)
        context['total'] = DetalleProceso.objects.filter(maquina=self.object).count()

        return context
