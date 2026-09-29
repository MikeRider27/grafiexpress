# Servicio de reportes JasperReports (reemplaza a common/jasper/server.py).
# Build context: raíz del repo (usa los .jar y .jasper de common/jasper).
#
# Java 8: los scriptlets (.class) están compilados para Java 7 y los .jasper
# con JasperReports 3.0.0, que no corre bien en JVMs modernas.

FROM eclipse-temurin:8-jdk AS build
WORKDIR /build
COPY common/jasper/jasperreports-3.0.0.jar lib/
COPY docker/jasper/ReportServer.java .
RUN mkdir classes && javac -encoding UTF-8 -cp "lib/*" -d classes ReportServer.java

FROM eclipse-temurin:8-jre
# fontconfig + fuentes: JasperReports mide el texto con AWT aunque exporte a PDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends fontconfig fonts-dejavu-core fonts-liberation wget && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -r -u 10001 jasper

WORKDIR /app
# Solo las librerías que usaba el servidor original (misma versión de Jasper/iText)
COPY common/jasper/jasperreports-3.0.0.jar \
     common/jasper/commons-logging-1.0.2.jar \
     common/jasper/commons-collections-2.1.jar \
     common/jasper/commons-beanutils-1.8.2.jar \
     common/jasper/commons-digester-2.1.jar \
     common/jasper/itext-1.3.1.jar \
     common/jasper/iReport-utils-2.0.1.jar \
     common/jasper/postgresql-9.3-1102.jdbc41.jar \
     lib/
COPY common/jasper/*.jasper common/jasper/*.class /reports/
COPY --from=build /build/classes/ classes/

ENV REPORTS_DIR=/reports \
    PORT=8080 \
    JAVA_TOOL_OPTIONS="-Djava.awt.headless=true -Xmx512m -Duser.language=es -Duser.country=PY"

USER jasper
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -qO /dev/null http://127.0.0.1:8080/health || exit 1

# /reports va en el classpath para que Jasper encuentre las clases Scriptlet
CMD ["java", "-cp", "classes:lib/*:/reports", "ReportServer"]
