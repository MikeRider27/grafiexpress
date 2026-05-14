from dal import autocomplete
from django import forms

from depositos.models import *


class AltaForm(forms.ModelForm):
    class Meta:
        model = Alta
        fields = ('__all__')
        widgets = {
            "funcionario": autocomplete.ModelSelect2(url='/admin/funcionarios/funcionarioautocomplete/'),
        }


class DetalleAltaForm(forms.ModelForm):
    class Meta:
        model = DetalleAlta
        fields = ('__all__')
        widgets = {
            "material": autocomplete.ModelSelect2(url='/admin/materiales/materialautocomplete/'),
            "cantidad": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
        }


class BajaForm(forms.ModelForm):
    class Meta:
        model = Baja
        fields = ('__all__')
        widgets = {
            "funcionario": autocomplete.ModelSelect2(url='/admin/funcionarios/funcionarioautocomplete/'),
        }


class DetalleBajaForm(forms.ModelForm):
    class Meta:
        model = DetalleBaja
        fields = ('__all__')
        widgets = {
            "material": autocomplete.ModelSelect2(url='/admin/materiales/materialautocomplete/'),
            "cantidad": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
        }


class RetiroForm(forms.ModelForm):
    class Meta:
        model = Retiro
        fields = ('__all__')
        widgets = {
            "funcionario": autocomplete.ModelSelect2(url='/admin/funcionarios/funcionarioautocomplete/'),
        }


class DetalleRetiroForm(forms.ModelForm):
    class Meta:
        model = DetalleRetiro
        fields = ('__all__')

        widgets = {
            "orden_de_trabajo": autocomplete.ModelSelect2(url='/admin/produccion/ordendetrabajoautocomplete/'),
            "material": autocomplete.ModelSelect2(url='/admin/materiales/materialautocomplete/',
                                                  forward=['factura']),
            "cantidad": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            "factura": autocomplete.ModelSelect2(url='venta-autocomplete')
        }

    saldo = forms.CharField(
        required=False,
        label='saldo',
    )

    def __init__(self,*args,**kwargs):
        super(DetalleRetiroForm, self).__init__(*args,**kwargs)
        self.fields['saldo'].widget.attrs['readonly'] = True


    def clean(self):
        cleaned_data = super(DetalleRetiroForm, self).clean()
        material = cleaned_data.get("material")
        orden_de_trabajo = cleaned_data.get("orden_de_trabajo")
        print (orden_de_trabajo)

        if material.retiro_ot == True and orden_de_trabajo == None:
            self.add_error('material', "Material requiere orden de trabajo para el retiro")


class DevolucionForm(forms.ModelForm):
    class Meta:
        model = Devolucion
        fields = ('__all__')
        widgets = {
            "funcionario": autocomplete.ModelSelect2(url='/admin/funcionarios/funcionarioautocomplete/'),
        }

    retiro = forms.ModelChoiceField(
        queryset=Retiro.objects.all(),
        widget=autocomplete.ModelSelect2(url='retiro-autocomplete'),
        label="Retiro"
    )


class DetalleDevolucionForm(forms.ModelForm):
    class Meta:
        model = DetalleDevolucion
        fields = ('__all__')
        widgets = {
            "detalle_retiro": autocomplete.ModelSelect2(url='detalleretiro-autocomplete', forward=['retiro']),
            "cantidad": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
        }
