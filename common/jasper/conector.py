"""
Cliente del servicio de reportes JasperReports (contenedor "jasper",
ver docker/jasper/). Reemplaza al antiguo puente por socket + pickle, que no
funcionaba en Python 3.
"""
import os
import urllib.error
import urllib.parse
import urllib.request

JASPER_URL = os.environ.get('JASPER_URL', 'http://jasper:8080').rstrip('/')
JASPER_TIMEOUT = int(os.environ.get('JASPER_TIMEOUT', '60'))


class JasperError(Exception):
    pass


def generar_pdf(reporte, parametros):
    """Devuelve los bytes del PDF de `reporte` (ej. "factura_triplicado.jasper")."""
    datos = urllib.parse.urlencode({k: '' if v is None else str(v) for k, v in parametros.items()})
    url = '%s/report/%s' % (JASPER_URL, urllib.parse.quote(reporte))
    peticion = urllib.request.Request(url, data=datos.encode('utf-8'), method='POST',
                                      headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(peticion, timeout=JASPER_TIMEOUT) as respuesta:
            return respuesta.read()
    except urllib.error.HTTPError as e:
        raise JasperError('El servicio de reportes respondió %s: %s'
                          % (e.code, e.read().decode('utf-8', 'replace')[:500]))
    except (urllib.error.URLError, OSError) as e:
        raise JasperError('No se pudo conectar al servicio de reportes en %s: %s' % (JASPER_URL, e))
