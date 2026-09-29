# -*- coding: utf-8 -*-
"""Validación de archivos subidos por los usuarios."""
import os

from django.core.exceptions import ValidationError

# Solo tipos de documento/imagen; se excluyen HTML, SVG, JS y ejecutables, que
# servidos desde /media/ (mismo origen) podrían ejecutar código en el navegador.
EXTENSIONES_PERMITIDAS = (
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff',
    '.doc', '.docx', '.xls', '.xlsx', '.csv', '.odt', '.ods', '.txt', '.zip', '.rar',
)


def validar_archivo_subido(archivo):
    extension = os.path.splitext(archivo.name)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValidationError(
            'Tipo de archivo no permitido (%s). Permitidos: %s.'
            % (extension or 'sin extensión', ', '.join(EXTENSIONES_PERMITIDAS)))
