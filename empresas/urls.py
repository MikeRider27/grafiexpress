from django.conf.urls import patterns, include, url
from empresas.autocomplete import *
from empresas.ajax import *
from empresas.views import *

urlpatterns = [
    url(
        'talonarionotacreditoautocomplete/$',
        TalonarioNotaCreditoAutocomplete.as_view(),
        name='talonarionotacredito-autocomplete',
    ),

    url(
        'empresaautocomplete/$',
        EmpresaAutocomplete.as_view(),
        name='empresa-autocomplete',
    ),

    url(
        'timbradoautocomplete/$',
        TimbradoAutocomplete.as_view(),
        name='timbrado-autocomplete',
    ),


    url(
        'sucursalautocomplete/$',
        SucursalAutocomplete.as_view(),
        name='sucursal-autocomplete',
    ),

    url(
        'talonarioreciboautocomplete/$',
        TalonarioReciboAutocomplete.as_view(),
        name='talonariorecibo-autocomplete',
    ),

    url(
        'talonarioremisionautocomplete/$',
        TalonarioRemisionAutocomplete.as_view(),
        name='talonarioremision-autocomplete',
    ),

    url(
        'talonariofacturaautocomplete/$',
        TalonarioFacturaAutocomplete.as_view(),
        name='talonariofactura-autocomplete',
    ),

    url('gettalonario/$',get_talonario),

    url(r'^empresa/(?P<pk>\d+)/detail/$', EmpresaDetailView.as_view(), name='empresa_det'),
    url(r'^empresa/$', EmpresaListView.as_view(), name='empresa_lis'),

    url(r'^talonario/(?P<pk>\d+)/detail/$', TalonarioDetailView.as_view(), name='talonario_det'),
    url(r'^talonario/$', TalonarioListView.as_view(), name='talonario_lis'),

    url(r'^timbrado/$', TimbradoListView.as_view(), name='timbrado_lis'),


]

