import datetime, calendar

from django.views import generic
from django.db.models import Q
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.generic.detail import DetailView

from extra.globals import separador_de_miles, listview_to_excel
from funcionarios.models import Funcionario
from .models import *


class PresupuestoListView(generic.ListView):
    model = Presupuesto
    template_name = 'comercial/presupuesto_list.html'
    paginate_by = 30

    def get_queryset(self):
        presupuestos = Presupuesto.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            presupuestos = presupuestos.filter(Q(id__istartswith=q) | Q(trabajo__icontains=q))

        cliente_id = self.request.GET.get('cliente_id', '')
        if cliente_id != '':
            presupuestos = presupuestos.filter(cliente__id=cliente_id)

        estado = self.request.GET.get('estado', 'TODOS')
        if estado == 'PENDIENTE':
            presupuestos = presupuestos.filter(estado=EstadoPresupuestos.PENDIENTE)
        elif estado == 'PRESUPUESTADO':
            presupuestos = presupuestos.filter(estado=EstadoPresupuestos.PRESUPUESTADO)
        elif estado == 'ENVIADO':
            presupuestos = presupuestos.filter(estado=EstadoPresupuestos.ENVIADO)
        else:
            presupuestos =  presupuestos.all()

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            presupuestos = presupuestos.filter(fecha_hora_creacion__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            presupuestos = presupuestos.filter(fecha_hora_creacion__lte=fecha)

        return presupuestos.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super(PresupuestoListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['clientes'] = Cliente.objects.all()
        context['cliente_id'] = int(self.request.GET.get('cliente_id', '')) if (self.request.GET.get('cliente_id', '') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['estado'] = self.request.GET.get('estado', 'TODOS')
        context['vendedores'] = Funcionario.objects.all()
        context['vendedor_id'] = int(self.request.GET.get('vendedor_id', '')) if (self.request.GET.get('vendedor_id', '') != '') else ''
        context['usuario_id'] = str(Funcionario.objects.filter(usuario=self.request.user).first().id) if Funcionario.objects.filter(usuario=self.request.user) else ''
        context['conteo_presupuestos'] = self.get_queryset().count()
        context['pendientes'] = self.get_queryset().filter(estado=EstadoPresupuestos.PENDIENTE).count()
        return context


def marcar_presupuesto_enviado(request, presupuesto_id):
    context = RequestContext(request)
    presupuesto = Presupuesto.objects.get(pk=presupuesto_id)
    if request.method == 'POST':
        presupuesto.estado = EstadoPresupuestos.ENVIADO
        presupuesto.save()
        return redirect('/admin/comercial/presupuesto/')

    mensaje = "Desea marcar como enviado el presupuesto " + separador_de_miles(presupuesto.id)
    return render_to_response('admin/confirm.html', {'mensaje': mensaje}, context)


class ActividadDetailView(DetailView):
    model = Actividad
    template_name = 'comercial/actividad_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ActividadDetailView, self).get_context_data(**kwargs)
        return context


class ActividadListView(generic.ListView):
    model = Actividad
    template_name = 'comercial/actividad_list.html'
    paginate_by = 30

    def get_queryset(self):
        actividades = Actividad.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            actividades = actividades.filter(Q(id__istartswith=q) | Q(presupuesto__trabajo__icontains=q))

        cliente_id = self.request.GET.get('cliente_id', '')
        if cliente_id != '':
            actividades = actividades.filter(cliente__id=cliente_id)

        vendedor = Funcionario.objects.filter(usuario=self.request.user).first()
        if not self.request.user.is_superuser and vendedor:
            vendedor_id = self.request.GET.get('vendedor_id', '')
            # Solo quien puede ver todas las OTs elige otro vendedor; el resto ve lo suyo
            if vendedor_id != '' and self.request.user.has_perm('produccion.view_all_ots'):
                actividades = actividades.filter(vendedor__id=vendedor_id)
            else:
                actividades = actividades.filter(vendedor__id=vendedor.id)
        else:
            vendedor_id = self.request.GET.get('vendedor_id', '')
            if vendedor_id != '':
                actividades = actividades.filter(vendedor__id=vendedor_id)

        canal_id = self.request.GET.get('canal_id', '')
        if canal_id != '':
            actividades = actividades.filter(canal__id=canal_id)

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            actividades = actividades.filter(fecha__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            actividades = actividades.filter(fecha__lte=fecha)

        return actividades.order_by("-id")

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''):

            lista_datos = []
            datos = self.get_queryset()
            for dato in datos:
                if dato.realizado:
                    estado = 'realizado'
                else:
                    estado = 'no realizado'

                if dato.vendedor:
                    vendedor = dato.vendedor.get_full_name()
                else:
                    vendedor = ' '
                lista_datos.append([
                    dato.fecha_creacion.strftime("%d/%m/%Y"),
                    dato.fecha.strftime("%d/%m/%Y"),
                    dato.cliente.razon_social,
                    dato.contacto.nombre,
                    dato.resumen,
                    vendedor,
                    estado
                ])
            titulos = ['Creacion', 'Fecha', 'Cliente', 'Contacto', 'Resumen', 'Vendedor', 'Estado']
            return listview_to_excel(lista_datos, 'actividades', titulos)

        return super(ActividadListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(ActividadListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['clientes'] = Cliente.objects.all()
        context['cliente_id'] = int(self.request.GET.get('cliente_id', '')) if (self.request.GET.get('cliente_id', '') != '') else ''
        context['vendedores'] = Funcionario.objects.all()
        context['vendedor_id'] = int(self.request.GET.get('vendedor_id', '')) if (
                    self.request.GET.get('vendedor_id', '') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['canales'] = Canal.objects.all()
        context['canal_id'] = int(self.request.GET.get('canal_id', '')) if (self.request.GET.get('canal_id', '') != '') else ''
        context['hoy'] = datetime.today().date()
        return context


class AgendaView(generic.ListView):
    model = Actividad
    template_name = 'comercial/agenda.html'
    queryset = Actividad.objects.all()

    def get_queryset(self):
        actividades = self.queryset
        mes_actual = datetime.today().month
        ano_actual = datetime.today().year
        mes = self.request.GET.get('mes', str(ano_actual) + '-' + str(mes_actual))

        if mes != '':
            inicio = mes + '-01'
            actividades = actividades.filter(fecha__gte=inicio)
            datetime_inicio = datetime.strptime(inicio, "%Y-%m-%d")
            rango_mes = calendar.monthrange(datetime_inicio.year, datetime_inicio.month)
            dia_final = calendar.monthrange(datetime_inicio.year, datetime_inicio.month)[1]
            final = mes + '-' + str(dia_final)
            actividades = actividades.filter(fecha__lte=final)

        vendedor = Funcionario.objects.filter(usuario=self.request.user).first()
        if not self.request.user.is_superuser and vendedor:
            vendedor_id = self.request.GET.get('vendedor_id', '')
            # Solo quien puede ver todas las OTs elige otro vendedor; el resto ve lo suyo
            if vendedor_id != '' and self.request.user.has_perm('produccion.view_all_ots'):
                actividades = actividades.filter(vendedor__id=vendedor_id)
            else:
                actividades = actividades.filter(vendedor__id=vendedor.id)
        else:
            vendedor_id = self.request.GET.get('vendedor_id', '')
            if vendedor_id != '':
                actividades = actividades.filter(vendedor__id=vendedor_id)

        actividades = actividades.filter(realizado=False)
        return actividades.order_by('id')

    def get_context_data(self, **kwargs):
        context = super(AgendaView, self).get_context_data(**kwargs)
        mes_actual = datetime.today().month
        ano_actual = datetime.today().year
        context['mes'] = self.request.GET.get('mes', str(ano_actual) + '-' + str(mes_actual))
        inicio = self.request.GET.get('mes', str(ano_actual) + '-' + str(mes_actual)) + '-01'
        datetime_inicio = datetime.strptime(inicio, "%Y-%m-%d")
        context['inicio'] = datetime_inicio.isoweekday()
        final = calendar.monthrange(datetime_inicio.year, datetime_inicio.month)
        context['final'] = final[1]
        context['clientes'] = Cliente.objects.all()
        context['vendedores'] = Funcionario.objects.all()
        context['vendedor_id'] = int(self.request.GET.get('vendedor_id', '')) if (
                    self.request.GET.get('vendedor_id', '') != '') else ''

        return context
