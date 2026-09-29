from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext

from django.views.generic.edit import CreateView
from django.contrib.auth.models import User
from sistema.forms import *

# Create your views here.
class UsuarioCreateView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "usuario_form.html"

    def get_success_url(self):
        return ("/admin/auth/user/" + str(self.object.id) )


def sistema_presentacion(request):
	context = RequestContext(request)
	titulo="SISTEMA"
	descripcion="."
	return render_to_response('admin/presentacion.html', {'titulo':titulo,'descripcion':descripcion}, context)


# ---------------------------------------------------------------------------
# Descarga protegida de archivos subidos (/media/)
# ---------------------------------------------------------------------------
import os
import posixpath

from django.conf import settings
from django.http import Http404, HttpResponse


def servir_media(request, path):
    """
    Sirve un archivo de MEDIA solo a usuarios logueados (staff).

    Los archivos subidos (documentos de clientes, adjuntos de presupuestos y
    OT) estaban accesibles por su URL sin iniciar sesión. Esta vista exige
    sesión y delega el envío a nginx con X-Accel-Redirect (nginx sirve los
    bytes desde una location interna); si no hay nginx (desarrollo), los envía
    Django.
    """
    user = request.user
    if not (user.is_authenticated() and user.is_active and user.is_staff):
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

    # Normaliza la ruta y evita salir de MEDIA_ROOT (path traversal)
    ruta_rel = posixpath.normpath(path).lstrip('/')
    ruta_abs = os.path.join(settings.MEDIA_ROOT, ruta_rel)
    if not os.path.abspath(ruta_abs).startswith(os.path.abspath(settings.MEDIA_ROOT) + os.sep):
        raise Http404()
    if not os.path.isfile(ruta_abs):
        raise Http404()

    if os.environ.get('USAR_X_ACCEL', 'True') == 'True':
        respuesta = HttpResponse()
        # nginx intercepta este header y sirve el archivo desde /_media_protegido/
        respuesta['X-Accel-Redirect'] = '/_media_protegido/' + ruta_rel
        del respuesta['Content-Type']  # que nginx determine el tipo
        return respuesta

    from django.views.static import serve
    return serve(request, ruta_rel, document_root=settings.MEDIA_ROOT)
