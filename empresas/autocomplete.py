from dal import autocomplete
from django.db.models import Q
from empresas.models import *
from datetime import date


class EmpresaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Empresa.objects.none()

        qs = Empresa.objects.all()

        if self.q:
            qs = qs.filter( Q(nombre__icontains=self.q) | Q(ruc__istartswith=self.q) )

        return qs

class SucursalAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        empresa = self.forwarded.get('empresa', None)

        # No olvides que los resultados dependen de quien los requiera!!
        if not self.request.user.is_authenticated() or not empresa:
            return Sucursal.objects.none()

        qs = Sucursal.objects.filter(empresa_id=empresa)

        if self.q:
            qs = qs.filter( nombre__icontains=self.q )

        return qs.order_by("-id")


class TalonarioRemisionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Talonario.objects.none

        qs = Talonario.objects.filter(fecha_de_caducidad__gte=date.today(), agotado=False, activo=True, tipo_de_talonario=REMISION)

        if self.q:
            qs = qs.filter(descripcion__icontains=self.q)

        return qs


class TalonarioFacturaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Talonario.objects.none

        qs = Talonario.objects.filter(fecha_de_caducidad__gte=date.today(), agotado=False, activo=True, tipo_de_talonario=FACTURA)

        if self.q:
            qs = qs.filter(descripcion__icontains=self.q)

        return qs


class TalonarioReciboAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Talonario.objects.none

        qs = Talonario.objects.filter(fecha_de_caducidad__gte=date.today(), agotado=False, activo=True, tipo_de_talonario=RECIBO)

        if self.q:
            qs = qs.filter(descripcion__icontains=self.q)

        return qs


class TimbradoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Timbrado.objects.none()

        qs = Timbrado.objects.all()
        
        if self.q:
            qs = qs.filter(numero__istartswith=self.q)

        return qs

