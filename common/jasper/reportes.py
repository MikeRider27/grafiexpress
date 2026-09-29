from common.jasper import conector


def get_report(report, params):
    # SUBREPORT_DIR lo fija el servicio de reportes (sus .jasper viven en su imagen)
    return conector.generar_pdf(report, params or {})
