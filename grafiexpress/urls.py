# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/admin/', permanent=False)),
    url(r'^admin/auth/', include('sistema.urls')),
    url(r'^admin/sistema/', include('sistema.urls')),
    url(r'^admin/clientes/', include('clientes.urls')),
    url(r'^admin/comercial/', include('comercial.urls')),
    url(r'^admin/funcionarios/', include('funcionarios.urls')),
    url(r'^admin/proveedores/', include('proveedores.urls')),
    url(r'^admin/materiales/', include('materiales.urls')),
    url(r'^admin/maquinaria/', include('maquinaria.urls')),
    url(r'^admin/produccion/', include('produccion.urls')),
    url(r'^admin/compras/', include('compras.urls')),
    url(r'^admin/ventas/', include('ventas.urls')),
    url(r'^admin/empresas/', include('empresas.urls')),
    url(r'^admin/ciudades/', include('ciudades.urls')),
    url(r'^admin/depositos/', include('depositos.urls')),
    url(r'^admin/automoviles/', include('automoviles.urls')),
    url(r'^admin/cheques/', include('cheques.urls')),
    url(r'^admin/bancos/', include('bancos.urls')),
    url(r'^admin/cobros/', include('cobros.urls')),
    url(r'^admin/pagos/', include('pagos.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^chaining/', include('smart_selects.urls')),
]

# Servir archivos estáticos y multimedia en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "GRAFI EXPRESS"
admin.site.site_title = "Industria gráfica"