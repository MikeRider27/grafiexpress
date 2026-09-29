from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from reportlab import pdfbase

from ventas.ajax import *
from ventas.autocomplete import *
from ventas.views import *
from ventas.reports import *

urlpatterns = patterns('',

    url(
        'facturanotacreditoautocomplete/$',
        FacturaNotaCreditoAutocomplete.as_view(),
        name='facturanotacredito-autocomplete',
    ),

    url(
        'facturacobroautocomplete/$',
        FacturaCobroAutocomplete.as_view(),
        name='facturacobro-autocomplete',
    ),

    url(
        'remisionautocomplete/$',
        RemisionAutocomplete.as_view(),
        name="remision-autocomplete",
    ),

    url(
        'ventaautocomplete/$',
        VentaAutocomplete.as_view(),
        name="venta-autocomplete",
    ),

    url(r'^remision/$', RemisionListView.as_view(), name='remision_lis'),
    url(r'^remision/(?P<pk>\d+)/detail/$', RemisionDetailView.as_view(), name='remision_det'),
    url(r'^venta/$', VentaListView.as_view(), name='venta_lis'),
    url(r'^venta/(?P<pk>\d+)/detail/$', VentaDetailView.as_view(), name='venta_det'),

    url(r'^venta/(?P<pk>\d+)/print/$', imprimir_venta, name='venta_print'),

    url(r'^notadecredito/(?P<pk>\d+)/print/$', imprimir_nota_de_credito, name='notadecredito_print'),
    url(r'^notadecredito/(?P<pk>\d+)/cancel/$', anular_nota_de_credito, name='notadecredito_cancel'),
    # print_confirm.html abre el PDF reemplazando "print" por el reporte de la empresa
    url(r'^notadecredito/(?P<pk>\d+)/(grafiexpress_report|gesa_report|pdf)/$', pdf_nota_de_credito,
        name='notadecredito_pdf'),
    url(r'^venta/(?P<pk>\d+)/cancel/$', anular_venta, name='venta_cancel'),
    url(r'^venta/(?P<pk>\d+)/revert/$', cancelar_anular_venta, name='venta_revert'),

    url(r'^remision/(?P<pk>\d+)/print/$', imprimir_remision, name='remision_print'),
    url(r'^remision/(?P<pk>\d+)/cancel/$', anular_remision, name='remision_cancel'),
    url(r'^remision/(?P<pk>\d+)/revert/$', cancelar_anular_remision, name='remision_revert'),

    url(r'^remision/(?P<pk>\d+)/grafiexpress_report/$', pdf_remision, name='remision_grafiexpress_report'),
    url(r'^venta/(?P<pk>\d+)/grafiexpress_report/$', pdf_factura, name='venta_grafiexpress_report'),

    url(r'^remision/(?P<pk>\d+)/gesa_report/$', pdf_remision, name='remision_gesa_report'),
    url(r'^venta/(?P<pk>\d+)/gesa_report/$', pdf_factura, name='venta_gesa_report'),

    url('get_detalle_de_remision/$', get_detalle_de_remision),
    url('get_detalle2_de_remision/$', get_detalle2_de_remision),
    url('getventa/$', get_venta),
    url('get_plazo_credito/$', get_plazo_credito),

    url(r'^$', ventas_presentacion),
    url(r'^venta/remisiones/(?P<pk>\d+)/$',VentaRemisionesView.as_view(),name='venta_remisiones'),
)
