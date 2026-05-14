from dal import autocomplete
from django import forms
from django.forms.widgets import HiddenInput

from funcionarios.models import Funcionario
from produccion.models import *
from decimal import Decimal
from django.db.models import Max
from extra.globals import separador_de_miles

# El campo "cantidad" del detalle tiene que copiarse del encabezado por defecto.
#
# En caso de que se marque "cambios" se tiene que validar que la suma de las cantidades de los detalles, sea igual a la cantidad del encabezado.
#
# En caso de que se marque "materiales compuestos" la cantidad debe ser la misma que el encabezado en cada detalle.


class OrdenDeTrabajoForm(forms.ModelForm):
    class Meta:
        model = OrdenDeTrabajo
        fields = ('__all__' )
        widgets = {
            "cliente": autocomplete.ModelSelect2(url='/admin/clientes/cliente/clienteautocomplete/'),
            #"vendedor": autocomplete.ModelSelect2(url='/admin/funcionarios/funcionarioautocomplete/'),
            "orden_de_compra_del_cliente":forms.TextInput(attrs={'style':'text-align:right','size':'12'}),
            "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
        }

    numero = forms.IntegerField(widget=forms.TextInput(attrs={'style':'text-align:right'}),required=False)
    automatico = forms.BooleanField(required=False)

    total = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),required=False)
    suma_cantidad = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}))
    limite_de_credito = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),required=False)

    def __init__(self, *args, **kwargs):
        super(OrdenDeTrabajoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['numero'] = instance.id
            self.fields['numero'].widget.attrs['readonly'] = True
            self.fields['automatico'].widget = forms.HiddenInput()

            self.initial['total'] = instance.get_total()
            self.initial['limite_de_credito'] = instance.cliente.limite_de_credito


            detalles = DetalleOrdenDeTrabajo.objects.filter(orden_de_trabajo_id=instance.id)
            suma = 0
            for detalle in detalles:
                suma = suma + detalle.cantidad
            self.initial['suma_cantidad'] = suma

            
        self.fields['total'].widget.attrs['readonly'] = True
        self.fields['limite_de_credito'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super(OrdenDeTrabajoForm, self).clean()
        cantidad = cleaned_data.get("cantidad")
        suma_cantidad = cleaned_data.get("suma_cantidad")
        cambios = cleaned_data.get("cambios")

        if((cambios == True) and (Decimal(cantidad) != Decimal(suma_cantidad))):
            self.add_error('cantidad', "Cambios esta marcado, verifique suma del campo cantidad en los detalles")

        # limite_de_credito = cleaned_data.get("limite_de_credito")
        # total = cleaned_data.get("total")
        # if(limite_de_credito != '' and total != ''):
        #     if(Decimal(limite_de_credito) < Decimal(total)):
        #         self.add_error('total', "Monto total supera el limite de credito del cliente")

        nombre_cliente = cleaned_data.get("cliente")
        if nombre_cliente != None:
            cliente =  Cliente.objects.filter(razon_social= nombre_cliente)[0]
            orden_de_compra_del_cliente = cleaned_data.get("orden_de_compra_del_cliente")
            if( (cliente.requiere_orden_de_compra_del_proveedor == True) and (orden_de_compra_del_cliente == '') ):
                self.add_error('orden_de_compra_del_cliente', "Cliente require orden de compra")

        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            pass
        else:
            automatico = cleaned_data.get("automatico")
            numero = cleaned_data.get("numero")
            print(numero)

            if automatico==False:
                if numero=='' or numero==None:
                    self.add_error('numero', "Ingrese numero o seleccione automatico")
                else:
                    try:
                       ot = OrdenDeTrabajo.objects.get(id=numero)
                       self.add_error('numero', "OT con este numero ya existe")
                    except OrdenDeTrabajo.DoesNotExist:
                       pass                

    def save(self, commit=True):
        orden_de_trabajo = super(OrdenDeTrabajoForm, self).save(commit=False)

        automatico = self.cleaned_data.get("automatico")
        if automatico==False:
            orden_de_trabajo.id = self.cleaned_data.get("numero")
        else:
            res = OrdenDeTrabajo.objects.all().aggregate(max_id=Max('pk'))
            max_id = res.get('max_id')
            orden_de_trabajo.id = max_id + 1

        if commit:
            orden_de_trabajo.save()
        return orden_de_trabajo


class DetalleOrdenDeTrabajoForm(forms.ModelForm):
    class Meta:
        model = DetalleOrdenDeTrabajo
        fields = ('__all__')
        widgets = {
            "material": autocomplete.ModelSelect2(url='/admin/materiales/material/materialautocomplete/'),
            "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto cantidad_iterable','data-a-sep':'.','data-a-dec':','}),
            "dimensiones_x":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "dimensiones_y":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "dimensiones_z":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
        }
    resma = forms.CharField(max_length=100, required=False)
    gramaje = forms.CharField(max_length=100, required=False)
    marca = forms.CharField(max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        super(DetalleOrdenDeTrabajoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['resma'] = instance.material.resma.descripcion if instance.material.resma != None else ''
            self.initial['gramaje'] = instance.material.gramaje.descripcion if instance.material.gramaje != None else ''
            self.initial['marca'] = instance.material.marca

        self.fields['resma'].widget.attrs['readonly'] = True
        self.fields['gramaje'].widget.attrs['readonly'] = True
        self.fields['marca'].widget.attrs['readonly'] = True


class CostoForm(forms.ModelForm):
    class Meta:
        model = Costo
        fields = ('__all__')
        widgets = {
            "detalle_orden_de_trabajo": autocomplete.ModelSelect2(url='/admin/produccion/detalleordendetrabajoautocomplete/'),
            #"vendedor": autocomplete.ModelSelect2(url='/admin/funcionarios/funcionario/funcionarioautocomplete/'),
        }

    orden_de_trabajo = forms.CharField(label='OT', max_length=100, required=False)
    cantidad = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),required=False)
    presupuesto = forms.CharField(max_length=100, required=False)
    cliente = forms.CharField(max_length=100, required=False)
    fecha = forms.CharField(max_length=100, required=False)

    #totales
    total_papel = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_preprensa = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_troquel = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_posprensaservicio = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_posprensamaterial = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_posprensaotroservicio = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_datosdebolsa = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_revista = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_compuesto = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_plastificado = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())

    total_general = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())
    total_iva = forms.CharField(max_length=100, required=False, widget = forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(CostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['orden_de_trabajo'] = instance.detalle_orden_de_trabajo.orden_de_trabajo.id
            self.initial['cantidad'] = instance.detalle_orden_de_trabajo.orden_de_trabajo.cantidad
            self.initial['presupuesto'] = instance.detalle_orden_de_trabajo.orden_de_trabajo.presupuesto_numero
            self.initial['cliente'] = instance.detalle_orden_de_trabajo.orden_de_trabajo.cliente.razon_social
            self.initial['fecha'] = instance.detalle_orden_de_trabajo.orden_de_trabajo.fecha_de_ingreso.strftime("%d/%m/%Y")

            #seterar totales ocultos
            self.initial['total_papel'] = separador_de_miles( instance.get_total_papel() )
            self.initial['total_preprensa'] = separador_de_miles( instance.get_total_preprensa() )
            self.initial['total_troquel'] = separador_de_miles( instance.get_total_troquel() )
            self.initial['total_posprensaservicio'] = separador_de_miles( instance.get_total_posprensaservicio() )
            self.initial['total_posprensamaterial'] = separador_de_miles( instance.get_total_posprensamaterial() )
            self.initial['total_posprensaotroservicio'] = separador_de_miles( instance.get_total_posprensaotroservicio() )
            self.initial['total_datosdebolsa'] = separador_de_miles( instance.get_total_datosdebolsa() )
            self.initial['total_revista'] = separador_de_miles( instance.get_total_revista() )
            self.initial['total_compuesto'] = separador_de_miles( instance.get_total_compuesto() )
            self.initial['total_plastificado'] = separador_de_miles( instance.get_total_plastificado() )

            total = instance.get_total_general()
            self.initial['total_general'] = separador_de_miles( total )
            total_iva = (total / 11)
            self.initial['total_iva'] = separador_de_miles( int(total_iva) )

        self.fields['orden_de_trabajo'].widget.attrs['readonly'] = True
        self.fields['cantidad'].widget.attrs['readonly'] = True
        self.fields['presupuesto'].widget.attrs['readonly'] = True
        self.fields['cliente'].widget.attrs['readonly'] = True
        self.fields['fecha'].widget.attrs['readonly'] = True


class PapelCostoForm(forms.ModelForm):
    class Meta:
        model = PapelCosto
        fields = ('__all__')
        widgets = {
            "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "color":forms.TextInput(attrs={'size':'12'}),
            "gramaje":forms.TextInput(attrs={'size':'12'}),
            "resma":forms.TextInput(attrs={'size':'12'}),
            "cantidad_en_oc":forms.HiddenInput(),
            "oc_incompletas":forms.HiddenInput(),
        }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto papel_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(PapelCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class PreprensaCostoForm(forms.ModelForm):
    class Meta:
        model = PreprensaCosto
        fields = ('__all__')
        widgets = {
            "maquina": autocomplete.ModelSelect2(url='/admin/maquinaria/maquina/maquinaautocomplete/'),
            "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "cantidad_en_oc": forms.HiddenInput(),
            "oc_incompletas": forms.HiddenInput(),
        }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto preprensa_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(PreprensaCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class TroquelCostoForm(forms.ModelForm):
    class Meta:
        model = TroquelCosto
        fields = ('__all__')
        widgets = {
            "precio":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto troquel_iterable','data-a-sep':'.','data-a-dec':','}),
        }


class PosprensaServicioCostoForm(forms.ModelForm):
    class Meta:
        model = PosprensaServicioCosto
        fields = ('__all__')
        widgets = {
            "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "cantidad_en_oc": forms.HiddenInput(),
            "oc_incompletas": forms.HiddenInput(),
        }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto posprensaservicio_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(PosprensaServicioCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class PosprensaMaterialCostoForm(forms.ModelForm):
    class Meta:
        model = PosprensaMaterialCosto
        fields = ('__all__')
        widgets = {
            "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
            "cantidad_en_oc": forms.HiddenInput(),
            "oc_incompletas": forms.HiddenInput(),
        }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto posprensamaterial_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(PosprensaMaterialCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class PosprensaOtroServicioCostoForm(forms.ModelForm):
    class Meta:
        model = PosprensaOtroServicioCosto
        fields = ('__all__')
        widgets = { "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "cantidad_en_oc": forms.HiddenInput(),
                    "oc_incompletas": forms.HiddenInput(),
                  }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto posprensaotroservicio_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(PosprensaOtroServicioCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class DatosDeBolsaCostoForm(forms.ModelForm):
    class Meta:
        model = DatosDeBolsaCosto
        fields = ('__all__')
        widgets = { "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "cantidad_en_oc": forms.HiddenInput(),
                    "oc_incompletas": forms.HiddenInput(),
                  }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto datosdebolsa_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(DatosDeBolsaCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class RevistaCostoForm(forms.ModelForm):
    class Meta:
        model = RevistaCosto
        fields = ('__all__')
        widgets = { "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "cantidad_en_oc": forms.HiddenInput(),
                    "oc_incompletas": forms.HiddenInput(),
                  }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto revista_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(RevistaCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class CompuestoCostoForm(forms.ModelForm):
    class Meta:
        model = CompuestoCosto
        fields = ('__all__')
        widgets = { "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "cantidad_en_oc": forms.HiddenInput(),
                    "oc_incompletas": forms.HiddenInput(),
                  }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto compuesto_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(CompuestoCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class PlastificadoCostoForm(forms.ModelForm):
    class Meta:
        model = PlastificadoCosto
        fields = ('__all__')
        widgets = { "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "cantidad_en_oc": forms.HiddenInput(),
                    "oc_incompletas": forms.HiddenInput(),
                  }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto plastificado_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(PlastificadoCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class OtroGastoCostoForm(forms.ModelForm):
    class Meta:
        model = OtroGastoCosto
        fields = ('__all__')
        widgets = { "cantidad":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "precio_unitario":forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto','data-a-sep':'.','data-a-dec':','}),
                    "cantidad_en_oc": forms.HiddenInput(),
                    "oc_incompletas": forms.HiddenInput(),
                  }

    subtotal = forms.CharField(widget=forms.TextInput(attrs={'style':'text-align:right','size':'12','class':'auto otrogasto_iterable','data-a-sep':'.','data-a-dec':','}),label='SUBTOTAL',required=False)

    def __init__(self, *args, **kwargs):
        super(OtroGastoCostoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['subtotal'] = instance.get_subtotal()
        self.fields['subtotal'].widget.attrs['readonly'] = True


class ProcesoForm(forms.ModelForm):
    class Meta:
        model = Proceso
        fields = '__all__'

    orden_de_trabajo = forms.ModelChoiceField(
        queryset=OrdenDeTrabajo.objects.exclude(estado_produccion=EstadoProceso.FINALIZADO),
        widget=autocomplete.ModelSelect2(url='ordendetrabajoproceso-autocomplete'),
        label="ORDEN DE TRABAJO"
    )


class DetalleProcesoForm(forms.ModelForm):
    class Meta:
        model = DetalleProceso
        fields = ('tipo', 'maquina', 'pasadas_por_hora', 'pasadas_por_pliego', 'horas_por_dia', 'fecha_de_inicio', 'hora_de_inicio', 'pliegos_a_realizar',
                  'fecha_de_finalizacion', 'hora_de_finalizacion')

        widgets = {
            "maquina": autocomplete.ModelSelect2(url='maquina-proceso-autocomplete', forward=['tipo']),
            'hora_de_inicio': forms.TimeInput(format='%H:%M'),
            'hora_de_finalizacion': forms.TimeInput(format='%H:%M'),
        }

    pasadas_por_hora = forms.CharField(
        widget=forms.TextInput(
            attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto'}),
        required=False,
        label="Pasadas/hr"
    )
    tercerizado = forms.CharField(
        widget=forms.HiddenInput(
            attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(DetalleProcesoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['pasadas_por_hora'] = instance.maquina.pasadas_por_hora
            self.initial['tercerizado'] = instance.maquina.tercerizado
        self.fields['pasadas_por_hora'].widget.attrs['readonly'] = True
        self.fields['tercerizado'].widget.attrs['readonly'] = True


class ProgramacionForm(forms.ModelForm):
    class Meta:
        model = Programacion
        fields = '__all__'

        widgets = {
            "maquina": autocomplete.ModelSelect2(url='maquina-autocomplete'),
        }


class DetalleProgramacionForm(forms.ModelForm):
    class Meta:
        model = DetalleProgramacion
        fields = '__all__'

        widgets = {
            'hora_de_inicio': forms.TimeInput(format='%H:%M'),
            'hora_de_finalizacion': forms.TimeInput(format='%H:%M'),
            "detalle_proceso": autocomplete.ModelSelect2(url='detalleproceso-programacion-autocomplete', forward=['maquina']),
        }

    duracion = forms.CharField(
        widget=forms.HiddenInput(
            attrs={'style': 'text-align:right', 'size': '12', 'class': 'auto', 'data-a-sep': '.'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(DetalleProgramacionForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial['duracion'] = instance.detalle_proceso.get_duracion
        self.fields['duracion'].widget.attrs['readonly'] = True
        self.fields['hora_de_finalizacion'].widget.attrs['readonly'] = True
        self.fields['pliegos'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super(DetalleProgramacionForm, self).clean()
        proceso = cleaned_data.get('detalle_proceso')
        proceso_anterior = DetalleProceso.objects.filter(maquina=proceso.maquina).exclude(id=proceso.id).last()
        fecha_de_inicio = cleaned_data.get('fecha_de_inicio')
        hora_de_inicio = cleaned_data.get('hora_de_inicio')
        fechahora_programa = datetime.datetime(year=fecha_de_inicio.year, month=fecha_de_inicio.month,
                                               day=fecha_de_inicio.day, hour=hora_de_inicio.hour)
        fechahora_maquina = datetime.datetime(year=proceso_anterior.fecha_de_finalizacion.year,
                                              month=proceso_anterior.fecha_de_finalizacion.month,
                                               day=proceso_anterior.fecha_de_finalizacion.day,
                                              hour=proceso_anterior.hora_de_finalizacion.hour)
        if proceso_anterior.proceso.urgente:
            if fechahora_maquina > fechahora_programa:
                self.add_error('hora_de_inicio', "Entra en conflicto con Proceso Urgente")
        else:
            pass


class ProduccionForm(forms.ModelForm):
    class Meta:
        model = Produccion
        fields = '__all__'

        widgets = {
            "programacion": autocomplete.ModelSelect2(url='programacion-autocomplete'),
        }


class DetalleProduccionForm(forms.ModelForm):
    class Meta:
        model = DetalleProduccion
        fields = '__all__'

        widgets = {
            'hora_de_inicio': forms.TimeInput(format='%H:%M'),
            'hora_de_finalizacion': forms.TimeInput(format='%H:%M'),
            "detalle_programacion": autocomplete.ModelSelect2(url='detalleprogramacion-produccion-autocomplete', forward=['programacion']),
        }

    def clean(self):
        cleaned_data = super(DetalleProduccionForm, self).clean()
        detalle_programacion = cleaned_data.get('detalle_programacion')
        pliegos_realizados = cleaned_data.get('pliegos_realizados')
        total_pliegos_realizados = detalle_programacion.detalle_proceso.pliegos_realizados + pliegos_realizados
        if total_pliegos_realizados > detalle_programacion.detalle_proceso.pliegos_a_realizar:
            self.add_error('pliegos_realizados', "Numero superior al total")