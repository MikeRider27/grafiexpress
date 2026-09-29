from django.shortcuts import get_object_or_404
from django.shortcuts import render, render_to_response, redirect

# Create your views here.
from django.template.context import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from django.db.models import Q

from proveedores.models import Proveedor
from extra.globals import *
# Create your views here.


class ProveedorListView(ListView):
    model = Proveedor
    template_name = "proveedor_list.html"

    def get_queryset(self):
        proveedores = Proveedor.objects.all()

        q = self.request.GET.get('q', '')
        if q!='':
            proveedores = proveedores.filter( Q(razon_social__icontains=q) | Q(ruc__startswith=q) )

        #return proveedores
        proveedores_ordenados_por_deuda = sorted(proveedores, key=lambda t: t.get_total_deuda(), reverse=True)

        activo = self.request.GET.get('activo', 'ACTIVOS')
        if (activo != 'TODOS'):
            if activo == 'ACTIVOS':
                proveedores_ordenados_por_deuda = proveedores.filter(activo=True)
            else:
                proveedores_ordenados_por_deuda = proveedores.filter(activo=False)

        return proveedores_ordenados_por_deuda

    def get_context_data(self, **kwargs):
        context = super(ProveedorListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')

        context['activo'] = self.request.GET.get('activo', 'ACTIVOS')
        return context

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''): 

            lista_datos=[]
            datos = self.get_queryset()
            for dato in datos:
                lista_datos.append([
                    dato.razon_social,
                    dato.ruc,
                    dato.direccion,
                    dato.telefono,
                    dato.celular,
                    dato.email,
                    dato.get_condicion_de_compra_display(),
                    dato.plazo_de_credito
                ])

            titulos=[ 'Razon social', 'RUC', 'Direccion', 'Telefono', 'Celular','Email', 'Condicion de compra', 'Plazo de credito' ]
            return listview_to_excel(lista_datos,'Proveedores',titulos)
        
        return super(ProveedorListView, self).render_to_response(context, **response_kwargs)

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(ProveedorListView, self).dispatch(*args, **kwargs)


class ProveedorDetailView(DetailView):
    model = Proveedor
    template_name = "proveedor_detail.html"


def proveedores_presentacion(request):
    context = RequestContext(request)
    titulo="PROVEEDORES"
    descripcion=".."
    return render_to_response('admin/presentacion.html', {'titulo': titulo, 'descripcion': descripcion}, context)


def desactivar_proveedor(request, proveedor_id):
    context = RequestContext(request)
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    if request.method == 'POST':
        proveedor.activo = False
        proveedor.save()
        return redirect('/admin/proveedores/proveedor/')

    mensaje = "Desea inactivar al proveedor " + proveedor.razon_social + " ?"
    return render_to_response('admin/confirm.html', {'mensaje': mensaje}, context)


def activar_proveedor(request, proveedor_id):
    context = RequestContext(request)
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    if request.method == 'POST':
        proveedor.activo = True
        proveedor.save()
        return redirect('/admin/proveedores/proveedor/')

    mensaje = "Desea activar al proveedor " + proveedor.razon_social + " ?"
    return render_to_response('admin/confirm.html', {'mensaje': mensaje}, context)