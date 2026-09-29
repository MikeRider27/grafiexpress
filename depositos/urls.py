from django.conf.urls import patterns, include, url

from depositos.ajax import  get_stock_material_deposito
from depositos.autocomplete import *
from depositos.views import *
from depositos.reports import *
#from materiales.views import MaterialListView


urlpatterns = [


    url(
        'detalleretiroautocomplete/$',
        DetalleRetiroAutocomplete.as_view(),
        name='detalleretiro-autocomplete',
    ),

url(
        'get_stock_material_deposito/$',
    get_stock_material_deposito,
        name='get_stock_material_deposito',
    ),


    url(r'^deposito/$', DepositoListView.as_view(), name='deposito_lis'),
    url(r'^alta/$', AltaListView.as_view(), name='alta_lis'),
    url(r'^baja/$', BajaListView.as_view(), name='baja_lis'),
    url(r'^retiro/$', RetiroListView.as_view(), name='retiro_lis'),
    url(r'^devolucion/$', DevolucionListView.as_view(), name='devolucion_lis'),

    url(r'^alta/(?P<pk>\d+)/delete/$', AltaDeleteView.as_view(), name='alta_del'),
    url(r'^baja/(?P<pk>\d+)/delete/$', BajaDeleteView.as_view(), name='baja_del'),
    url(r'^retiro/(?P<pk>\d+)/delete/$', RetiroDeleteView.as_view(), name='retiro_del'),
    url(r'^retiro/(?P<retiro_id>\d+)/print/$', reporte_retiro, name='retiro_print'),

    url(r'^devolucion/(?P<pk>\d+)/delete/$', DevolucionDeleteView.as_view(), name='devolucion_del'),

    url(r'^alta/(?P<pk>\d+)/detail/$', AltaDetailView.as_view(), name='alta_det'),
    url(r'^baja/(?P<pk>\d+)/detail/$', BajaDetailView.as_view(), name='baja_det'),
    url(r'^retiro/(?P<pk>\d+)/detail/$', RetiroDetailView.as_view(), name='retiro_det'),
    url(r'^devolucion/(?P<pk>\d+)/detail/$', DevolucionDetailView.as_view(), name='devolucion_det'),

    url(r'^stock/$', StockListView.as_view(), name='stock_lis'),

    url(
        'retiroautocomplete/$',
        RetiroAutocomplete.as_view(),
        name='retiro-autocomplete',
    ),


]

