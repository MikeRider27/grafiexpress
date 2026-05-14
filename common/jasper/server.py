import SocketServer
import pickle
import sys
import os,inspect
mypath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+'/'

sys.path.append(mypath+'postgresql-9.3-1102.jdbc41.jar')
sys.path.append(mypath+'jasperreports-3.0.0.jar')
sys.path.append(mypath+'commons-logging-1.0.2.jar')
sys.path.append(mypath+'commons-collections-2.1.jar')
sys.path.append(mypath+'itext-1.3.1.jar')
sys.path.append(mypath+'iReport-utils-2.0.1.jar')

from java.util import Properties
import org.postgresql.Driver as Driver
from java.sql.DriverManager import *

import os.path
import traceback

PATH = (os.path.abspath(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(PATH+"/../")


from java.util import HashMap;
from net.sf.jasperreports.engine import JasperFillManager,JasperExportManager
import java.io.ByteArrayOutputStream
import java.io.FileOutputStream
import java.util.Locale


class BridgeRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            size = int(self._readline())
            data = self._readbytes(size)
            params = pickle.loads(data)

            props = Properties()
            props.put('user', 'postgres')
            props.put('password', 'postgres')
            
            conn = Driver().connect('jdbc:postgresql:grafiexpress', props)
            h = HashMap()
            for k, v in params["params"].items():

                h.put(k,v)
                
            #h.put(JRParameter.REPORT_LOCALE, java.util.Locale(""))
            print (params)
            print (params["report"])
            print (h)
            print (conn)
            report = JasperFillManager.fillReport(params["report"], h, conn)
            output = java.io.ByteArrayOutputStream()
            JasperExportManager.exportReportToPdfStream(report, output)
            output.close()
            data = output.toByteArray()

        except:
            print '\nexcept \n'
            self.request.send("0\n")
            print traceback.print_exc()
        else:
            print '\nelse \n'
            self.request.send(str(len(data))+"\n")
            self.request.send(data)
            print '\nelse \n'

    def _readline(self):
        chars = []
        while 1:
            try:
                char = self.request.recv(1)
            except:
                char = ''
            if not char:
                self._logException(4, "failed to read response line")
                raise ServerError("Failed to read server reply header")
            if char == '\n':
                break
            chars.append(char)
        return "".join(chars)
    
    def _readbytes(self, n):
        chunks = []
    
        while n > 0:
            try:
                chunk = self.request.recv(1)
            except:
                chunk = None
            if not chunk:
                raise ServerError("Failed to read response from server")
            chunks.append(chunk)
            n -= len(chunk)
        return "".join(chunks)

#server host is a tuple ('host', port)
server = SocketServer.TCPServer(('localhost', 5000), BridgeRequestHandler)
server.serve_forever()
