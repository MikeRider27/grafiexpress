import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import net.sf.jasperreports.engine.JRParameter;
import net.sf.jasperreports.engine.JasperExportManager;
import net.sf.jasperreports.engine.JasperFillManager;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.util.JRLoader;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.math.BigDecimal;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.regex.Pattern;

/**
 * Servicio HTTP que genera PDFs con los reportes JasperReports de common/jasper.
 * Reemplaza al antiguo server.py (Jython + socket + pickle).
 *
 *   GET  /health                         -> 200 "ok" (y prueba la conexión a la base)
 *   POST /report/{nombre}.jasper         -> application/pdf
 *        cuerpo: application/x-www-form-urlencoded con los parámetros del reporte
 *
 * Los valores llegan como texto y se convierten al tipo que declara cada
 * parámetro en el reporte (String, Integer, BigDecimal, ...). SUBREPORT_DIR lo
 * fija el servidor. Configuración por entorno: REPORTS_DIR, DB_HOST, DB_PORT,
 * DB_NAME, DB_USER, DB_PASSWORD, PORT.
 */
public class ReportServer {

    private static final Pattern REPORT_NAME = Pattern.compile("[A-Za-z0-9_]+\\.jasper");
    private static final Map<String, JasperReport> CACHE = new ConcurrentHashMap<String, JasperReport>();

    private static String reportsDir;
    private static String jdbcUrl;
    private static String dbUser;
    private static String dbPassword;

    public static void main(String[] args) throws Exception {
        reportsDir = env("REPORTS_DIR", "/reports");
        if (!reportsDir.endsWith("/")) {
            reportsDir += "/";
        }
        jdbcUrl = "jdbc:postgresql://" + env("DB_HOST", "db") + ":" + env("DB_PORT", "5432") + "/" + env("DB_NAME", "grafiexpress");
        dbUser = env("DB_USER", "grafiexpress");
        dbPassword = env("DB_PASSWORD", "");
        Class.forName("org.postgresql.Driver");

        int port = Integer.parseInt(env("PORT", "8080"));
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/health", ReportServer::health);
        server.createContext("/report/", ReportServer::report);
        server.setExecutor(Executors.newFixedThreadPool(Integer.parseInt(env("WORKERS", "4"))));
        server.start();
        log("Servidor de reportes escuchando en :" + port + " (reportes en " + reportsDir + ")");
    }

    private static void health(HttpExchange ex) throws IOException {
        try (Connection c = connect()) {
            send(ex, 200, "text/plain", "ok".getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            send(ex, 503, "text/plain", ("db: " + e.getMessage()).getBytes(StandardCharsets.UTF_8));
        }
    }

    private static void report(HttpExchange ex) throws IOException {
        long start = System.currentTimeMillis();
        String name = ex.getRequestURI().getPath().substring("/report/".length());
        try {
            if (!"POST".equals(ex.getRequestMethod())) {
                send(ex, 405, "text/plain", "usar POST".getBytes(StandardCharsets.UTF_8));
                return;
            }
            if (!REPORT_NAME.matcher(name).matches() || !new File(reportsDir + name).isFile()) {
                send(ex, 404, "text/plain", ("reporte inexistente: " + name).getBytes(StandardCharsets.UTF_8));
                return;
            }
            JasperReport report = load(name);
            Map<String, String> raw = parseForm(readAll(ex.getRequestBody()));

            Map<String, Object> params = new HashMap<String, Object>();
            for (JRParameter p : report.getParameters()) {
                if (!p.isSystemDefined() && raw.containsKey(p.getName())) {
                    params.put(p.getName(), convert(raw.get(p.getName()), p.getValueClassName()));
                }
            }
            params.put("SUBREPORT_DIR", reportsDir);

            byte[] pdf;
            try (Connection c = connect()) {
                JasperPrint print = JasperFillManager.fillReport(report, params, c);
                pdf = JasperExportManager.exportReportToPdf(print);
            }
            send(ex, 200, "application/pdf", pdf);
            log("OK " + name + " " + raw + " " + pdf.length + " bytes en " + (System.currentTimeMillis() - start) + " ms");
        } catch (Throwable t) {
            log("ERROR " + name + ": " + t);
            t.printStackTrace();
            send(ex, 500, "text/plain", ("error generando " + name + ": " + t).getBytes(StandardCharsets.UTF_8));
        }
    }

    private static JasperReport load(String name) throws Exception {
        JasperReport report = CACHE.get(name);
        if (report == null) {
            report = (JasperReport) JRLoader.loadObject(new File(reportsDir + name));
            CACHE.put(name, report);
        }
        return report;
    }

    private static Object convert(String value, String className) {
        if (value == null || value.isEmpty()) {
            return "java.lang.String".equals(className) ? value : null;
        }
        switch (className) {
            case "java.lang.Integer":    return new BigDecimal(value).intValue();
            case "java.lang.Long":       return new BigDecimal(value).longValue();
            case "java.lang.Double":     return new BigDecimal(value).doubleValue();
            case "java.lang.Float":      return new BigDecimal(value).floatValue();
            case "java.math.BigDecimal": return new BigDecimal(value);
            case "java.lang.Boolean":    return Boolean.valueOf(value);
            default:                     return value;
        }
    }

    private static Connection connect() throws Exception {
        return DriverManager.getConnection(jdbcUrl, dbUser, dbPassword);
    }

    private static Map<String, String> parseForm(String body) throws IOException {
        Map<String, String> out = new HashMap<String, String>();
        if (body.isEmpty()) {
            return out;
        }
        for (String pair : body.split("&")) {
            int i = pair.indexOf('=');
            String k = URLDecoder.decode(i < 0 ? pair : pair.substring(0, i), "UTF-8");
            String v = i < 0 ? "" : URLDecoder.decode(pair.substring(i + 1), "UTF-8");
            out.put(k, v);
        }
        return out;
    }

    private static String readAll(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte[] b = new byte[8192];
        int n;
        while ((n = in.read(b)) > 0) {
            buf.write(b, 0, n);
        }
        return new String(buf.toByteArray(), StandardCharsets.UTF_8);
    }

    private static void send(HttpExchange ex, int status, String type, byte[] body) throws IOException {
        ex.getResponseHeaders().set("Content-Type", type);
        ex.sendResponseHeaders(status, body.length);
        try (OutputStream os = ex.getResponseBody()) {
            os.write(body);
        }
    }

    private static String env(String key, String def) {
        String v = System.getenv(key);
        return v == null || v.isEmpty() ? def : v;
    }

    private static void log(String msg) {
        System.out.println("[jasper] " + msg);
        System.out.flush();
    }
}
