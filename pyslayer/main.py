#std
from __future__ import with_statement
from os import sep,path
from optparse import OptionParser
import sys,logging,logging.handlers,traceback
#fix path
sys.path.append(sep.join(path.dirname(path.abspath(__file__)).split(sep)[:-1]))

from pyslayer import db,stats

BASE_PATH = path.dirname(path.abspath(__file__))
logger = logging.getLogger("pyslayer")


def wsgi_main(env, start_response):
  try:
    if env['PATH_INFO'].startswith('/db') and env['QUERY_STRING'] != "":
      return db.handle(env,start_response)
    elif env['PATH_INFO'].startswith('/stats'):
      return stats.handle(env,start_response)
    else:
      start_response('404 Not Found', [('Content-Type', 'text/plain')])
      return 'Not Found\r\n'
  except GeneratorExit:#Python 2.5 fix
    pass
  except Exception,e:
    logger.error(traceback.format_exc())
    start_response('500 Internal server error', [('Content-Type', 'text/plain')])
    return 'Internal server error\r\n'

def main(options):
  from wsgiref.simple_server import make_server, demo_app
  cherrypy = True
  try:
    from cherrypy import wsgiserver
  except ImportError:
    cherrypy = False

  if cherrypy:  
    server = wsgiserver.CherryPyWSGIServer((options.listen, options.port), wsgi_main)
  else:
    server = make_server(options.listen,options.port,wsgi_main)

  db.set_options(options)
  try:
    if cherrypy:
      server.start()
    else:
      server.serve_forever()
  except KeyboardInterrupt:
    server.stop()

def maxfd():
    import resource
    return resource.getrlimit(resource.RLIMIT_NOFILE)[1]

def setprocname(name):
  try:
    from setproctitle import setproctitle
    setproctitle(name)
  except:
    pass

def cli_start():
  setprocname("pyslayer")
  parser = OptionParser(usage="usage: %prog [options]")
  parser.add_option("-d", "--daemon", dest="daemon",help="ruan as daemon",action="store_true",default=False)
  parser.add_option("-p", "--port", dest="port",help="listen port",action="store_int",default=9090)
  parser.add_option("-i", "--ip-address", dest="listen",help="listen ip",default='0.0.0.0')
  parser.add_option("-l", "--log", dest="log",help="log path",default=path.expanduser('~/pyslayer.log'))
  parser.add_option("-t", "--number-threads", dest="num_threads",help="number of threads",action="store_int",default=10)
  parser.add_option("--user", dest="user",help="user of the db",default='')
  parser.add_option("--password", dest="password",help="pass of the db",default='')
  parser.add_option("--host", dest="host",help="db host address",default='')
  parser.add_option("--db-name", dest="db",help="db name",default='')
  parser.add_option("--db-type", dest="db_type",help="name of database",default='mysql')
    
  (options, args) = parser.parse_args()
  
  formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
  #setup handlers
  fh = logging.handlers.RotatingFileHandler(options.log,maxBytes = 1024 * 1024,backupCount=3)
  ch = logging.StreamHandler()
  #set formmaters
  fh.setFormatter(formatter)
  ch.setFormatter(formatter)
  logger.setLevel(logging.INFO)

  if options.daemon:
    from daemon import DaemonContext
    with DaemonContext(files_preserve=range(maxfd() + 2)):      
        logger.addHandler(fh)
        logger.info("starting daemon..")
        main(options)
  else:
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    main(options)

if __name__ == "__main__":
  cli_start()
  
