from dal import autocomplete
from django import forms
from django.db.models.query_utils import Q

from empresas.models import *
from ventas.models import *
from produccion.models import *


class RemisionForm(forms.ModelForm):
    class Meta:
        model = Remision
        exclude = ['codigo_de_establecimiento', 'punto_de_expedicion', 'numero_de_remision', 'empresa', 'sucursal']
        widgets = {
            "talonario": autocomplete.ModelSelect2(url='/admin/empresas/talonarioremisionautocomplete/'),
            "cliente": autocomplete.ModelSelect2(url='/admin/clientes/cliente/clienteautocomplete/'),
            "kilometros_estimados_de_recorrido": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.','data-a-dec': ','}),
            "chofer": autocomplete.ModelSelect2(url='funcionario-autocomplete'),
            "vehiculo": autocomplete.ModelSelect2(url='/admin/automoviles/automovilautocomplete/'),
        }

    numero_de_remision = forms.CharField(widget=forms.TextInput(attrs={'size': '12', 'placeholder': '000-000-0000000'}),required=True)
    empresa = forms.CharField(widget=forms.TextInput(), required=True)
    sucursal = forms.CharField(widget=forms.TextInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(RemisionForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['numero_de_remision'] = instance.get_numero_de_remision()
            self.initial['empresa'] = instance.talonario.sucursal.empresa.nombre
            self.initial['sucursal'] = instance.talonario.sucursal.nombre
            self.fields['talonario'].widget = forms.HiddenInput()

        self.fields['numero_de_remision'].widget.attrs['readonly'] = True
        self.fields['empresa'].widget.attrs['readonly'] = True
        self.fields['sucursal'].widget.attrs['readonly'] = True
        self.fields['timbrado'].widget.attrs['readonly'] = True

    def clean(self):
        instance = getattr(self, 'instance', None)
        if not (instance and instance.pk):
            cleaned_data = super(RemisionForm, self).clean()
            numero_de_remision = cleaned_data.get("numero_de_remision")
            timbrado = cleaned_data.get("timbrado")
            if numero_de_remision is not None:
                vector = numero_de_remision.split("-")
                codigo_de_establecimiento = vector[0]
                punto_de_expedicion = vector[1]
                numero_factura = vector[2]

                conflictos = Remision.objects.filter(Q(codigo_de_establecimiento=codigo_de_establecimiento) &
                                                     Q(punto_de_expedicion=punto_de_expedicion) &
                                                     Q(numero_de_remision=numero_factura) &
                                                     Q(timbrado=timbrado))

                if conflictos:
                    msg = "Ya existe una remision con este numero"
                    self.add_error('numero_de_remision', msg)

    def save(self, commit=True):
        remision = super(RemisionForm, self).save(commit=False)

        numero_de_remision = self.cleaned_data.get('numero_de_remision')
        vector = numero_de_remision.split("-")

        remision.codigo_de_establecimiento = vector[0]
        remision.punto_de_expedicion = vector[1]
        remision.numero_de_remision = vector[2]

        remision.empresa = remision.talonario.sucursal.empresa
        remision.sucursal = remision.talonario.sucursal

        if commit:
            remision.save()
        return remision


class DetalleDeRemisionForm(forms.ModelForm):
    class Meta:
        model = DetalleDeRemision
        fields = ('__all__')
        widgets = {
            #"orden_de_trabajo": autocomplete.ModelSelect2(url='/admin/produccion/ordendetrabajoremisionautocomplete/'),
            "unidad_de_medida": autocomplete.ModelSelect2(url='/admin/materiales/material/unidaddemedidaautocomplete/'),
            "cantidad": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            }
    orden_de_trabajo = forms.ModelChoiceField(
        queryset=OrdenDeTrabajo.objects.all(),
        widget=autocomplete.ModelSelect2(url='ordendetrabajoremision-autocomplete', forward=['cliente']),
        label="ORDEN DE TRABAJO"
    )


class DetalleDeRemision2Form(forms.ModelForm):
    class Meta:
        model = DetalleDeRemision2
        fields = ('__all__')
        widgets = {
            #"detalle_orden_de_trabajo": autocomplete.ModelSelect2(url='/admin/produccion/detalleordendetrabajoremisionautocomplete/'),
            "unidad_de_medida": autocomplete.ModelSelect2(url='/admin/materiales/material/unidaddemedidaautocomplete/'),
            "cantidad": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            }
    detalle_orden_de_trabajo = forms.ModelChoiceField(
        queryset=DetalleOrdenDeTrabajo.objects.all(),
        widget=autocomplete.ModelSelect2(url='detalleordendetrabajoremision-autocomplete', forward=['cliente']),
        required=False, label='DETALLE ORDEN DE TRABAJO'
    )


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        exclude = ['estado', 'fecha_de_anulacion', 'codigo_de_establecimiento', 'punto_de_expedicion','numero_de_factura', 'empresa', 'sucursal']
        widgets = {
            "cliente": autocomplete.ModelSelect2(url='/admin/clientes/cliente/clienteautocomplete/'),
            "talonario": autocomplete.ModelSelect2(url='/admin/empresas/talonariofacturaautocomplete/'),
            "remision": autocomplete.ModelSelect2Multiple(url='admin/ventas/remisionautocomplete/', forward=['cliente']),
            "timbrado": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12'}),
            "descuento": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.', 'data-a-dec': ','}),
            "total": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.', 'data-a-dec': ','}),
        }

    numero_de_factura = forms.CharField(widget=forms.TextInput(attrs={'size': '12', 'placeholder': '000-000-0000000'}), required=True)
    empresa = forms.CharField(widget=forms.TextInput(), required=True)
    sucursal = forms.CharField(widget=forms.TextInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(VentaForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['numero_de_factura'] = instance.get_numero_de_factura()
            self.initial['empresa'] = instance.talonario.sucursal.empresa.nombre
            self.initial['sucursal'] = instance.talonario.sucursal.nombre
            self.fields['talonario'].widget = forms.HiddenInput()

        self.fields['numero_de_factura'].widget.attrs['readonly'] = True
        self.fields['empresa'].widget.attrs['readonly'] = True
        self.fields['sucursal'].widget.attrs['readonly'] = True
        self.fields['timbrado'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super(VentaForm, self).clean()

        condicion = cleaned_data.get("condicion")
        fecha_de_vencimiento = cleaned_data.get("fecha_de_vencimiento")
        fecha_de_emision = cleaned_data.get("fecha_de_emision")

        if ((condicion == CREDITO) and (fecha_de_vencimiento == fecha_de_emision)):
            msg = "Factura es CREDITO, la fecha de vencimiento no puede ser igual a la fecha de emision"
            self.add_error('fecha_de_vencimiento', msg)

        if ((condicion == CONTADO) and (fecha_de_vencimiento != fecha_de_emision)):
            msg = "Factura es CONTADO, la fecha de vencimiento no puede ser distinta a la fecha de emision"
            self.add_error('fecha_de_vencimiento', msg)

        instance = getattr(self, 'instance', None)
        if not (instance and instance.pk):
            numero_de_factura = cleaned_data.get("numero_de_factura")
            timbrado = cleaned_data.get("timbrado")
            if numero_de_factura is not None:
                vector = numero_de_factura.split("-")
                codigo_de_establecimiento = vector[0]
                punto_de_expedicion = vector[1]
                numero_factura = vector[2]

                conflictos = Venta.objects.filter(Q(codigo_de_establecimiento=codigo_de_establecimiento) &
                                                  Q(punto_de_expedicion=punto_de_expedicion) &
                                                  Q(numero_de_factura=numero_factura) &
                                                  Q(timbrado=timbrado))

                if conflictos:
                    msg = "Ya existe una factura con este numero"
                    self.add_error('numero_de_factura', msg)

    def save(self, commit=True):
        venta = super(VentaForm, self).save(commit=False)
        numero_de_factura = self.cleaned_data.get('numero_de_factura')
        vector = numero_de_factura.split("-")
        venta.codigo_de_establecimiento = vector[0]
        venta.punto_de_expedicion = vector[1]
        venta.numero_de_factura = vector[2]
        venta.empresa = venta.talonario.sucursal.empresa
        venta.sucursal = venta.talonario.sucursal

        if commit:
            venta.save()
        return venta


class DetalleDeVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleDeVenta
        fields = '__all__'
        widgets = {
            "descripcion_extra": forms.TextInput(attrs={'style': 'text-align:right', 'size': '8'}),
            "cantidad": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.','data-a-dec': ','}),
            "precio_unitario": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.','data-a-dec': ','}),
            "subtotal": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto subtotal_iterable', 'data-a-sep': '.','data-a-dec': ','}),
        }

    orden_de_trabajo = forms.ModelChoiceField(
        queryset=OrdenDeTrabajo.objects.exclude(cantidad_no_facturada=0),
        widget=autocomplete.ModelSelect2(url='ordendetrabajoventa-autocomplete', forward=['cliente']),
        label="ORDEN DE TRABAJO"
    )

    def __init__(self, *args, **kwargs):
        super(DetalleDeVentaForm, self).__init__(*args, **kwargs)
        self.fields['subtotal'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super(DetalleDeVentaForm, self).clean()
        cantidad = cleaned_data.get('cantidad')

        if cantidad > cleaned_data.get('orden_de_trabajo').cantidad:
            msg = "Cantidad no puede ser superior a cantidad de orden de trabajo"
            self.add_error('cantidad', msg)


class DetalleDeVentaChangeForm(forms.ModelForm):
    class Meta:
        model = DetalleDeVenta
        fields = '__all__'
        widgets = {
            "descripcion_extra": forms.TextInput(attrs={'style': 'text-align:right', 'size': '8'}),
            "cantidad": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.','data-a-dec': ','}),
            "precio_unitario": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.','data-a-dec': ','}),
            "subtotal": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto subtotal_iterable', 'data-a-sep': '.','data-a-dec': ','}),
        }

    orden_de_trabajo = forms.ModelChoiceField(
        queryset=OrdenDeTrabajo.objects.all(),
        widget=autocomplete.ModelSelect2(url='ordendetrabajoventachange-autocomplete', forward=['cliente']),
        label="ORDEN DE TRABAJO"
    )

    def __init__(self, *args, **kwargs):
        super(DetalleDeVentaChangeForm, self).__init__(*args, **kwargs)
        self.fields['subtotal'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super(DetalleDeVentaChangeForm, self).clean()
        cantidad_form = cleaned_data.get('cantidad')
        detalles = DetalleDeVenta.objects.filter(orden_de_trabajo=cleaned_data.get('orden_de_trabajo'))
        cantidad_facturada = 0
        for detalle in detalles:
            cantidad_facturada += detalle.cantidad

        if cantidad_form > (cleaned_data.get('orden_de_trabajo').cantidad - cantidad_facturada):
            msg = "Cantidad invalida"
            self.add_error('cantidad', msg)


class DetalleDeVenta2Form(forms.ModelForm):
    class Meta:
        model = DetalleDeVenta2
        fields = '__all__'
        widgets = {
            "descripcion_extra": forms.TextInput(attrs={'style': 'text-align:right', 'size': '8'}),
            "cantidad": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            "precio_unitario": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            "subtotal": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto subtotal_iterable', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            }
    detalle_orden_de_trabajo = forms.ModelChoiceField(
        queryset=DetalleOrdenDeTrabajo.objects.exclude(cantidad_no_facturada=0),
        widget=autocomplete.ModelSelect2(url='detalleordendetrabajoventa-autocomplete', forward=['cliente']),
        required=False, label='DETALLE ORDEN DE TRABAJO'
    )

    def __init__(self, *args, **kwargs):
        super(DetalleDeVenta2Form, self).__init__(*args, **kwargs)
        self.fields['subtotal'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super(DetalleDeVenta2Form, self).clean()
        cantidad = cleaned_data.get('cantidad')

        if cantidad > cleaned_data.get('detalle_orden_de_trabajo').cantidad:
            msg = "Cantidad no puede ser superior a cantidad de orden de trabajo"
            self.add_error('cantidad', msg)


class DetalleDeVenta2ChangeForm(DetalleDeVenta2Form):
    detalle_orden_de_trabajo = forms.ModelChoiceField(
        queryset=DetalleOrdenDeTrabajo.objects.all(),
        widget=autocomplete.ModelSelect2(url='detalleordendetrabajoventachange-autocomplete', forward=['cliente']),
        required=False, label='DETALLE ORDEN DE TRABAJO'
    )

    def __init__(self, *args, **kwargs):
        super(DetalleDeVenta2ChangeForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(DetalleDeVenta2Form, self).clean()
        cantidad_form = cleaned_data.get('cantidad')
        detalles = DetalleDeVenta2.objects.filter(detalle_orden_de_trabajo_id=cleaned_data.get(
            'detalle_orden_de_trabajo_id')).exclude(detalle_orden_de_trabajo_id=cleaned_data.get('detalle_orden_de_trabajo_id'))
        cantidad_facturada = 0
        for detalle in detalles:
            cantidad_facturada += detalle.cantidad

        if cantidad_form > (cleaned_data.get('detalle_orden_de_trabajo').cantidad - cantidad_facturada):
            msg = "Cantidad invalida"
            self.add_error('cantidad', msg)


class DetalleVentaMaterialForm(forms.ModelForm):
    class Meta:
        model = DetalleVentaMateriales
        fields = '__all__'
        widgets = {
            "material": autocomplete.ModelSelect2(url='material-retiro_factura-autocomplete', ),
            "cantidad": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            "precio_unitario": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            "subtotal": forms.TextInput(
                attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto subtotal_iterable', 'data-a-sep': '.',
                       'data-a-dec': ','}),
            }

    def __init__(self, *args, **kwargs):
        super(DetalleVentaMaterialForm, self).__init__(*args, **kwargs)
        self.fields['subtotal'].widget.attrs['readonly'] = True


class RemisionAntiguoForm(forms.ModelForm):
    class Meta:
        model = Remision
        exclude = ['codigo_de_establecimiento', 'punto_de_expedicion', 'numero_de_remision', 'empresa', 'sucursal']
        widgets = {
            #"talonario": autocomplete.ModelSelect2(url='/admin/empresas/todostalonarioremisionautocomplete/'),
            "cliente": autocomplete.ModelSelect2(url='/admin/clientes/cliente/clienteautocomplete/'),
            "kilometros_estimados_de_recorrido": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.','data-a-dec': ','}),
            "chofer": autocomplete.ModelSelect2(url='funcionario-autocomplete'),
            "vehiculo": autocomplete.ModelSelect2(url='/admin/automoviles/automovilautocomplete/'),
        }

    numero_de_remision = forms.CharField(widget=forms.TextInput(attrs={'size': '12', 'placeholder': '000-000-0000000'}),required=True)
    empresa = forms.CharField(widget=forms.TextInput(), required=True)
    sucursal = forms.CharField(widget=forms.TextInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(RemisionAntiguoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['numero_de_remision'] = instance.get_numero_de_remision()
            self.initial['empresa'] = instance.talonario.sucursal.empresa.nombre
            self.initial['sucursal'] = instance.talonario.sucursal.nombre
            self.fields['talonario'].widget = forms.HiddenInput()

        #self.fields['numero_de_remision'].widget.attrs['readonly'] = True
        self.fields['empresa'].widget.attrs['readonly'] = True
        self.fields['sucursal'].widget.attrs['readonly'] = True
        self.fields['timbrado'].widget.attrs['readonly'] = True
        self.fields['talonario'].queryset = Talonario.objects.filter(tipo_de_talonario=REMISION, activo=False)

    def clean(self):
        instance = getattr(self, 'instance', None)
        if not (instance and instance.pk):
            cleaned_data = super(RemisionAntiguoForm, self).clean()
            numero_de_remision = cleaned_data.get("numero_de_remision")
            timbrado = cleaned_data.get("timbrado")
            if numero_de_remision is not None:
                vector = numero_de_remision.split("-")
                codigo_de_establecimiento = vector[0]
                punto_de_expedicion = vector[1]
                numero_factura = vector[2]

                conflictos = Remision.objects.filter(Q(codigo_de_establecimiento=codigo_de_establecimiento) &
                                                     Q(punto_de_expedicion=punto_de_expedicion) &
                                                     Q(numero_de_remision=numero_factura) &
                                                     Q(timbrado=timbrado))

                if conflictos:
                    msg = "Ya existe una remision con este numero"
                    self.add_error('numero_de_remision', msg)

    def save(self, commit=True):
        remision = super(RemisionAntiguoForm, self).save(commit=False)

        numero_de_remision = self.cleaned_data.get('numero_de_remision')
        vector = numero_de_remision.split("-")

        remision.codigo_de_establecimiento = vector[0]
        remision.punto_de_expedicion = vector[1]
        remision.numero_de_remision = vector[2]

        remision.empresa = remision.talonario.sucursal.empresa
        remision.sucursal = remision.talonario.sucursal

        if commit:
            remision.save()
        return remision


class VentaAntiguoForm(forms.ModelForm):
    class Meta:
        model = Venta
        exclude = ['estado', 'fecha_de_anulacion', 'codigo_de_establecimiento', 'punto_de_expedicion',
                   'numero_de_factura', 'empresa', 'sucursal']
        widgets = {"cliente": autocomplete.ModelSelect2(url='/admin/clientes/cliente/clienteautocomplete/'),
                   #"talonario": autocomplete.ModelSelect2(url='/admin/empresas/talonariofacturaautocomplete/'),
                   "remision": autocomplete.ModelSelect2Multiple(url='admin/ventas/remisionautocomplete/',forward=['cliente']),
                   "timbrado": forms.TextInput(attrs={'style': 'text-align:right', 'size': '12'}),
                   "descuento": forms.TextInput(
                       attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                              'data-a-dec': ','}),
                   "total": forms.TextInput(
                       attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.',
                              'data-a-dec': ','}),
                   }

    numero_de_factura = forms.CharField(widget=forms.TextInput(attrs={'size': '12', 'placeholder': '000-000-0000000'}), required=True)
    empresa = forms.CharField(widget=forms.TextInput(), required=True)
    sucursal = forms.CharField(widget=forms.TextInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(VentaAntiguoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['numero_de_factura'] = instance.get_numero_de_factura()
            self.initial['empresa'] = instance.talonario.sucursal.empresa.nombre
            self.initial['sucursal'] = instance.talonario.sucursal.nombre
            self.fields['talonario'].widget = forms.HiddenInput()

        #self.fields['remision'].queryset = Remision.objects.exclude(pk__in=[i.remision_id for i in Venta.objects.all()])
        #self.fields['numero_de_factura'].widget.attrs['readonly'] = True
        self.fields['empresa'].widget.attrs['readonly'] = True
        self.fields['sucursal'].widget.attrs['readonly'] = True
        self.fields['timbrado'].widget.attrs['readonly'] = True
        self.fields['talonario'].queryset = Talonario.objects.filter(tipo_de_talonario=FACTURA, activo=False)

    def clean(self):
        cleaned_data = super(VentaAntiguoForm, self).clean()

        condicion = cleaned_data.get("condicion")
        fecha_de_vencimiento = cleaned_data.get("fecha_de_vencimiento")
        fecha_de_emision = cleaned_data.get("fecha_de_emision")

        if ((condicion == CREDITO) and (fecha_de_vencimiento == fecha_de_emision)):
            msg = "Factura es CREDITO, la fecha de vencimiento no puede ser igual a la fecha de emision"
            self.add_error('fecha_de_vencimiento', msg)

        if ((condicion == CONTADO) and (fecha_de_vencimiento != fecha_de_emision)):
            msg = "Factura es CONTADO, la fecha de vencimiento no puede ser distinta a la fecha de emision"
            self.add_error('fecha_de_vencimiento', msg)

        instance = getattr(self, 'instance', None)
        if not (instance and instance.pk):
            numero_de_factura = cleaned_data.get("numero_de_factura")
            timbrado = cleaned_data.get("timbrado")
            if numero_de_factura is not None:
                vector = numero_de_factura.split("-")
                codigo_de_establecimiento = vector[0]
                punto_de_expedicion = vector[1]
                numero_factura = vector[2]

                conflictos = Venta.objects.filter(Q(codigo_de_establecimiento=codigo_de_establecimiento) &
                                                  Q(punto_de_expedicion=punto_de_expedicion) &
                                                  Q(numero_de_factura=numero_factura) &
                                                  Q(timbrado=timbrado))

                if conflictos:
                    msg = "Ya existe una factura con este numero"
                    self.add_error('numero_de_factura', msg)

    def save(self, commit=True):
        venta = super(VentaAntiguoForm, self).save(commit=False)

        numero_de_factura = self.cleaned_data.get('numero_de_factura')
        vector = numero_de_factura.split("-")

        venta.codigo_de_establecimiento = vector[0]
        venta.punto_de_expedicion = vector[1]
        venta.numero_de_factura = vector[2]

        venta.empresa = venta.talonario.sucursal.empresa
        venta.sucursal = venta.talonario.sucursal

        if commit:
            venta.save()
        return venta


class SearchRemisionOTForm(forms.Form):
    nombre = forms.CharField(max_length=20,
                              required=False,
                              widget=forms.TextInput(
                                     attrs={'placeholder': 'Nombre de OT'}
                                )
                              )

    numero = forms.IntegerField(required=False,
                                widget=forms.TextInput(
                                    attrs={'placeholder': 'Numero de OT', 'style': 'width:120px;'}
                                    )
                                )