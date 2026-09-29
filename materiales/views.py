from django.shortcuts import render, render_to_response

from django.template.context import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from django.db.models import Q
from django.apps import apps

from materiales.models import UnidadDeMedida, CategoriaDeMaterial, Material
from extra.globals import *
# Create your views here.

class UnidadDeMedidaListView(ListView):
    model = UnidadDeMedida
    template_name = "unidaddemedida_list.html"
    paginate_by = 30

    def get_queryset(self):
        udemedidas = UnidadDeMedida.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            udemedidas = udemedidas.filter(nombre__icontains=q)

        return udemedidas

    def get_context_data(self, **kwargs):
        context = super(UnidadDeMedidaListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q','')
        return context

class UnidadDeMedidaDetailView(DetailView):
    model = UnidadDeMedida
    template_name = "unidaddemedida_detail.html"


class CategoriaDeMaterialListView(ListView):
    model = CategoriaDeMaterial
    template_name = "categoriadematerial_list.html"
    paginate_by = 30

    def get_queryset(self):
        categoriasdemateriales = CategoriaDeMaterial.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            categoriasdemateriales = categoriasdemateriales.filter( Q(nombre__icontains=q) | Q(id__startswith=q) )
        return categoriasdemateriales

    def get_context_data(self, **kwargs):
        context = super(CategoriaDeMaterialListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q','')
        return context

class CategoriaDeMaterialDetailView(DetailView):
    model = CategoriaDeMaterial
    template_name = "categoriadematerial_detail.html"


class MaterialListView(ListView):
    model = Material
    template_name = "material_list.html"
    paginate_by = 30

    def get_queryset(self):
        materiales = Material.objects.all()

        q = self.request.GET.get('q', '')
        if q != '':
            materiales = materiales.filter( Q(descripcion__icontains=q) | Q(codigo__startswith=q) )

        categoria_id=self.request.GET.get('categoria_id','')
        if categoria_id !='':
            materiales = materiales.filter(categoria_id = categoria_id)

        materiales = materiales.order_by('-stock_actual')
        return materiales

    def get_context_data(self, **kwargs):
        context = super(MaterialListView, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q','')
        context['categorias'] = CategoriaDeMaterial.objects.all()
        context['categoria_id'] = int(self.request.GET.get('categoria_id','')) if (self.request.GET.get('categoria_id','') != '') else ''
        return context

    def render_to_response(self, context, **response_kwargs):
        if 'excel' in self.request.GET.get('excel', ''): 

            lista_datos=[]
            datos = self.get_queryset()
            for dato in datos:
                lista_datos.append([
                    str(dato),
                    dato.codigo,
                    dato.unidad_de_medida.nombre if dato.unidad_de_medida != None else '',
                    dato.categoria.nombre if dato.categoria != None else '',
                    separador_de_miles(dato.stock_actual),
                    separador_de_miles(dato.costo_actual),
                    dato.gramaje.descripcion if dato.gramaje != None else '',
                    dato.resma.descripcion if dato.resma != None else '',
                    dato.marca
                ])

            titulos=[ 
                'Descripcion', 
                'Codigo', 
                'Unidad de medida', 
                'Categoria', 
                'Stock actual',
                'Costo actual', 
                'Gramaje', 
                'Resma',
                'Marca'
            ]
            return listview_to_excel(lista_datos,'Materiales',titulos)
        
        return super(MaterialListView, self).render_to_response(context, **response_kwargs)

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(MaterialListView, self).dispatch(*args, **kwargs)

class MaterialDetailView(DetailView):
    model = Material
    template_name = "material_detail.html"


def materiales_presentacion(request):
    context = RequestContext(request)
    titulo="MATERIALES"
    descripcion=".."
    return render_to_response('admin/presentacion.html', {'titulo': titulo, 'descripcion': descripcion}, context)