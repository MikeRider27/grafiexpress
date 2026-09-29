from dal import autocomplete
from django.db.models import Q
from ventas.models import *


class RemisionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        cliente = self.forwarded.get('cliente', None)

        if not self.request.user.is_authenticated() or not cliente:
            return Remision.objects.none()

        qs = Remision.objects.filter(cliente_id=cliente).exclude(pk__in=[i.remision_id for i in VentaRemision.objects.all()])

        if self.q:
            qs = qs.filter(numero_de_remision__istartswith=self.q)

        return qs.order_by("-id")


class VentaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):

        if not self.request.user.is_authenticated():
            return Venta.objects.none()

        qs = Venta.objects.all()

        if self.q:
            qs = qs.filter(numero_de_factura__istartswith=self.q)

        return qs.order_by("-id")


class FacturaCobroAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        cliente = self.forwarded.get('cliente', None)

        if not self.request.user.is_authenticated() or not cliente:
            return Venta.objects.none()

        qs = Venta.objects.filter(cliente_id=cliente).exclude(saldo=0).exclude(estado=ANULADO)

        if self.q:
            qs = qs.filter(numero_de_factura__icontains=self.q)

        return qs.order_by("-id")

class FacturaNotaCreditoAutocomplete(autocomplete.Select2QuerySetView):
    """Facturas no anuladas del cliente elegido en la nota de crédito."""
    def get_queryset(self):
        cliente = self.forwarded.get('cliente', None)

        if not self.request.user.is_authenticated() or not cliente:
            return Venta.objects.none()

        qs = Venta.objects.filter(cliente_id=cliente).exclude(estado=ANULADO)

        if self.q:
            qs = qs.filter(numero_de_factura__icontains=self.q)

        return qs.order_by("-id")
