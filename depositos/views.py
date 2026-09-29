from django.shortcuts import render, render_to_response
from django.template.context import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView

from django.views.generic.list import ListView
from django.db.models import Q

from django.contrib.auth.models import User

from depositos.models import *
from funcionarios.models import *

from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from django.apps import apps

from extra.globals import *
from materiales.views import MaterialListView



class StockListView (MaterialListView):
    template_name = "stock_list.html"

    def get_context_data(self, **kwargs):
        context = super(StockListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q','')
        context['depositos'] = apps.get_model("depositos", "Deposito").objects.all()
        context['categorias'] = apps.get_model("materiales", "CategoriaDeMaterial").objects.all()
        context['categoria_id'] = int(self.request.GET.get('categoria_id','')) if (self.request.GET.get('categoria_id','') != '') else ''
        return context

class DepositoListView(ListView):
    model = Deposito
    template_name = "deposito_list.html"

    def get_queryset(self):
        depositos = Deposito.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            depositos = depositos.filter( nombre__icontains=q )

        return depositos

    def get_context_data(self, **kwargs):
        context = super(DepositoListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(DepositoListView, self).dispatch(*args, **kwargs)


class AltaListView(ListView):
    model = DetalleAlta
    template_name = "alta_list.html"
    paginate_by = 30

    def get_queryset(self):
        altas = DetalleAlta.objects.all().order_by('-id')

        funcionario_id = self.request.GET.get('funcionario_id', '')
        if funcionario_id != '':
            altas = altas.filter(alta__funcionario_id=funcionario_id)

        deposito_id = self.request.GET.get('deposito_id', '')
        if deposito_id != '':
            altas = altas.filter(alta__deposito_id=deposito_id)

        q = self.request.GET.get('q', '')
        if q != '':
            altas = altas.filter( Q(material__descripcion__icontains=q) | Q(material__id__istartswith=q) )


        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            altas = altas.filter(alta__fecha__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            altas = altas.filter(alta__fecha__lte=fecha)

        return altas

    def get_context_data(self, **kwargs):
        context = super(AltaListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q','')
        context['funcionarios'] = Funcionario.objects.all()
        context['funcionario_id'] = int(self.request.GET.get('funcionario_id','')) if (self.request.GET.get('funcionario_id','') != '') else ''
        context['depositos'] = Deposito.objects.all()
        context['deposito_id'] = int(self.request.GET.get('deposito_id','')) if (self.request.GET.get('deposito_id','') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''): 

            lista_datos=[]
            datos = self.get_queryset()
            for dato in datos:
                lista_datos.append([
                    dato.alta.fecha.strftime('%d/%m/%Y'),
                    dato.alta.deposito.nombre,
                    str(dato.material),
                    separador_de_miles(dato.cantidad),
                    dato.motivo,
                    dato.alta.funcionario.get_full_name()
                ])

            titulos=[ 'Fecha', 'Deposito', 'Material', 'Cantidad', 'Motivo','Funcionario' ]
            return listview_to_excel(lista_datos,'Altas',titulos)
        
        return super(AltaListView, self).render_to_response(context, **response_kwargs)


    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(AltaListView, self).dispatch(*args, **kwargs)

class BajaListView(ListView):
    model = DetalleBaja
    template_name = "baja_list.html"
    paginate_by = 30

    def get_queryset(self):
        bajas = DetalleBaja.objects.all().order_by('-id')

        funcionario_id = self.request.GET.get('funcionario_id', '')
        if funcionario_id != '':
            bajas = bajas.filter(baja__funcionario_id=funcionario_id)

        deposito_id = self.request.GET.get('deposito_id', '')
        if deposito_id != '':
            bajas = bajas.filter(baja__deposito_id=deposito_id)

        q = self.request.GET.get('q', '')
        if q != '':
            bajas = bajas.filter( Q(material__descripcion__icontains=q) | Q(material__id__istartswith=q) )


        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            bajas = bajas.filter(baja__fecha__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            bajas = bajas.filter(baja__fecha__lte=fecha)


        return bajas

    def get_context_data(self, **kwargs):
        context = super(BajaListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q','')
        context['funcionarios'] = Funcionario.objects.all()
        context['funcionario_id'] = int(self.request.GET.get('funcionario_id','')) if (self.request.GET.get('funcionario_id','') != '') else ''
        context['depositos'] = Deposito.objects.all()
        context['deposito_id'] = int(self.request.GET.get('deposito_id','')) if (self.request.GET.get('deposito_id','') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''): 

            lista_datos=[]
            datos = self.get_queryset()
            for dato in datos:
                lista_datos.append([
                    dato.baja.fecha.strftime('%d/%m/%Y'),
                    dato.baja.deposito.nombre,
                    str(dato.material),
                    separador_de_miles(dato.cantidad),
                    dato.motivo,
                    dato.baja.funcionario.get_full_name()
                ])

            titulos=[ 'Fecha', 'Deposito', 'Material', 'Cantidad', 'Motivo','Funcionario' ]
            return listview_to_excel(lista_datos,'Bajas',titulos)
        
        return super(BajaListView, self).render_to_response(context, **response_kwargs)

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(BajaListView, self).dispatch(*args, **kwargs)

class RetiroListView(ListView):
    model = DetalleRetiro
    template_name = "retiro_list.html"
    paginate_by = 30

    def get_queryset(self):
        retiros = DetalleRetiro.objects.all().order_by('-id')

        funcionario_id = self.request.GET.get('funcionario_id', '')
        if funcionario_id != '':
            retiros = retiros.filter(retiro__funcionario_id=funcionario_id)

        deposito_id = self.request.GET.get('deposito_id', '')
        if deposito_id != '':
            retiros = retiros.filter(deposito_id=deposito_id)

        material = self.request.GET.get('material', '')
        if material != '':
            retiros = retiros.filter( 
                Q(material__descripcion__icontains=material) | Q(material__id__istartswith=material) 
            )

        orden_de_trabajo = self.request.GET.get('orden_de_trabajo', '')
        if orden_de_trabajo != '':
            retiros = retiros.filter( 
                #Q(orden_de_trabajo__nombre__icontains=orden_de_trabajo) | Q(orden_de_trabajo__id__istartswith=orden_de_trabajo) 
                orden_de_trabajo__id=orden_de_trabajo
            )


        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            retiros = retiros.filter(retiro__fecha__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            retiros = retiros.filter(retiro__fecha__lte=fecha)


        return retiros

    def get_context_data(self, **kwargs):
        context = super(RetiroListView, self).get_context_data(**kwargs)
        context['material'] = self.request.GET.get('material','')
        context['orden_de_trabajo'] = self.request.GET.get('orden_de_trabajo','')
        context['funcionarios'] = Funcionario.objects.all()
        context['funcionario_id'] = int(self.request.GET.get('funcionario_id','')) if (self.request.GET.get('funcionario_id','') != '') else ''
        context['depositos'] = Deposito.objects.all()
        context['deposito_id'] = int(self.request.GET.get('deposito_id','')) if (self.request.GET.get('deposito_id','') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')

        return context

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''): 

            lista_datos=[]
            datos = self.get_queryset()
            for dato in datos:
                lista_datos.append([
                    dato.retiro.fecha.strftime('%d/%m/%Y'),
                    dato.deposito.nombre,
                    str(dato.material),
                    separador_de_miles(dato.cantidad),
                    dato.retiro.funcionario.get_full_name()
                ])

            titulos=[ 'Fecha', 'Deposito', 'Material', 'Cantidad','Funcionario' ]
            return listview_to_excel(lista_datos,'Retiros',titulos)
        
        return super(RetiroListView, self).render_to_response(context, **response_kwargs)

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(RetiroListView, self).dispatch(*args, **kwargs)

class DevolucionListView(ListView):
    model = DetalleDevolucion
    template_name = "devolucion_list.html"
    paginate_by = 30

    def get_queryset(self):
        devoluciones = DetalleDevolucion.objects.all().order_by('-id')

        funcionario_id = self.request.GET.get('funcionario_id', '')
        if funcionario_id != '':
            devoluciones = devoluciones.filter(devolucion__funcionario_id=funcionario_id)

        deposito_id = self.request.GET.get('deposito_id', '')
        if deposito_id != '':
            devoluciones = devoluciones.filter(deposito_id=deposito_id)

        material = self.request.GET.get('material', '')
        if material != '':
            devoluciones = devoluciones.filter(Q(detalle_retiro__material__descripcion__icontains=material) | Q(detalle_retiro__material__id__istartswith=material))

        retiro = self.request.GET.get('retiro', '')
        if retiro != '':
            devoluciones = devoluciones.filter( 
                #Q(retiro__nombre__icontains=retiro) | Q(retiro__id__istartswith=retiro) 
                devolucion__retiro__id=retiro
            )

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde != '':
            vector = fecha_desde.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            devoluciones = devoluciones.filter(devolucion__fecha__gte=fecha)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta != '':
            vector = fecha_hasta.split("/")
            fecha = vector[2] + "-" + vector[1] + "-" + vector[0]
            devoluciones = devoluciones.filter(devolucion__fecha__lte=fecha)

        return devoluciones

    def get_context_data(self, **kwargs):
        context = super(DevolucionListView, self).get_context_data(**kwargs)
        context['material'] = self.request.GET.get('material','')
        context['retiro'] = self.request.GET.get('retiro','')
        context['funcionarios'] = Funcionario.objects.all()
        context['funcionario_id'] = int(self.request.GET.get('funcionario_id','')) if (self.request.GET.get('funcionario_id','') != '') else ''
        context['depositos'] = Deposito.objects.all()
        context['deposito_id'] = int(self.request.GET.get('deposito_id','')) if (self.request.GET.get('deposito_id','') != '') else ''
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''): 

            lista_datos=[]
            datos = self.get_queryset()
            for dato in datos:
                lista_datos.append([
                    dato.id,
                    dato.devolucion.retiro.id,
                    dato.detalle_retiro.retiro.fecha.strftime('%d/%m/%Y'),
                    dato.devolucion.fecha.strftime('%d/%m/%Y'),
                    dato.detalle_retiro.deposito.nombre,
                    dato.deposito.nombre,
                    str(dato.detalle_retiro.material),
                    separador_de_miles(dato.detalle_retiro.cantidad),
                    separador_de_miles(dato.cantidad),
                    dato.detalle_retiro.retiro.funcionario.get_full_name(),
                    dato.devolucion.funcionario.get_full_name()
                ])

            titulos=[ 
                'Nro. de devolucion', 
                'Nro. de retiro', 
                'Fecha de detiro', 
                'Fecha de devolucion',  
                'Deposito de retiro', 
                'Deposito de devolucion', 
                'Material', 
                'Cantidad retirada', 
                'Cantidad depositada',
                'Funcionario de retiro',
                'Funcionario de devolucion'
            ]

            return listview_to_excel(lista_datos,'Devoluciones',titulos)
        
        return super(DevolucionListView, self).render_to_response(context, **response_kwargs)

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(DevolucionListView, self).dispatch(*args, **kwargs)

class AltaDeleteView(DeleteView):
    model = DetalleAlta
    template_name = "alta_confirm_delete.html"
    success_url = '/admin/depositos/alta/'

class BajaDeleteView(DeleteView):
    model = DetalleBaja
    template_name = "baja_confirm_delete.html"
    success_url = '/admin/depositos/baja/'

class RetiroDeleteView(DeleteView):
    model = DetalleRetiro
    template_name = "retiro_confirm_delete.html"
    success_url = '/admin/depositos/retiro/'

class DevolucionDeleteView(DeleteView):
    model = DetalleDevolucion
    template_name = "devolucion_confirm_delete.html"
    success_url = '/admin/depositos/devolucion/'



# ---------------------------------------------------------------------------
# Detalle de movimientos (alta, baja, retiro, devolución): cabecera + materiales
# ---------------------------------------------------------------------------

class MovimientoDetailView(DetailView):
    template_name = "movimiento_detail.html"
    titulo = ""
    url_lista = ""
    columnas = ()

    def get_cabecera(self):
        """Lista de (etiqueta, valor) con los datos generales del movimiento."""
        m = self.object
        return [("Número", m.id), ("Fecha", m.fecha.strftime("%d/%m/%Y")),
                ("Funcionario", m.funcionario or "-")]

    def get_filas(self):
        """Lista de filas (tuplas alineadas con self.columnas)."""
        return []

    def get_context_data(self, **kwargs):
        context = super(MovimientoDetailView, self).get_context_data(**kwargs)
        filas = self.get_filas()
        context.update({
            'titulo': self.titulo,
            'url_lista': self.url_lista,
            'cabecera': self.get_cabecera(),
            'columnas': self.columnas,
            'filas': filas,
            'total_cantidad': sum(f[-1] for f in filas) if filas else 0,
        })
        return context


class AltaDetailView(MovimientoDetailView):
    model = Alta
    titulo = "Alta de materiales"
    url_lista = "/admin/depositos/alta/"
    columnas = ("Material", "Motivo", "Cantidad")

    def get_cabecera(self):
        return super(AltaDetailView, self).get_cabecera() + [("Depósito", self.object.deposito)]

    def get_filas(self):
        return [(str(d.material), d.motivo or "", d.cantidad)
                for d in DetalleAlta.objects.filter(alta=self.object).select_related('material')]


class BajaDetailView(MovimientoDetailView):
    model = Baja
    titulo = "Baja de materiales"
    url_lista = "/admin/depositos/baja/"
    columnas = ("Material", "Motivo", "Cantidad")

    def get_cabecera(self):
        return super(BajaDetailView, self).get_cabecera() + [("Depósito", self.object.deposito)]

    def get_filas(self):
        return [(str(d.material), d.motivo or "", d.cantidad)
                for d in DetalleBaja.objects.filter(baja=self.object).select_related('material')]


class RetiroDetailView(MovimientoDetailView):
    model = Retiro
    titulo = "Retiro de materiales"
    url_lista = "/admin/depositos/retiro/"
    columnas = ("Material", "Depósito", "OT", "Factura", "Cantidad")

    def get_context_data(self, **kwargs):
        context = super(RetiroDetailView, self).get_context_data(**kwargs)
        context['url_imprimir'] = "/admin/depositos/retiro/%s/print/" % self.object.id
        return context

    def get_filas(self):
        detalles = DetalleRetiro.objects.filter(retiro=self.object).select_related(
            'material', 'deposito', 'orden_de_trabajo', 'factura')
        return [(str(d.material), str(d.deposito),
                 d.orden_de_trabajo_id or "", d.factura.get_numero_de_factura() if d.factura else "",
                 d.cantidad) for d in detalles]


class DevolucionDetailView(MovimientoDetailView):
    model = Devolucion
    titulo = "Devolución de materiales"
    url_lista = "/admin/depositos/devolucion/"
    columnas = ("Material", "Depósito", "Cantidad")

    def get_cabecera(self):
        retiro = self.object.retiro
        return super(DevolucionDetailView, self).get_cabecera() + [("Retiro", retiro or "-")]

    def get_filas(self):
        detalles = DetalleDevolucion.objects.filter(devolucion=self.object).select_related(
            'detalle_retiro__material', 'deposito')
        return [(str(d.detalle_retiro.material) if d.detalle_retiro else "-", str(d.deposito), d.cantidad)
                for d in detalles]
