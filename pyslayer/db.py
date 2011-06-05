from json import dumps,loads
from Queue import Queue,Empty
from threading import Event,Thread
from urllib import unquote_plus
import datetime

_options = {}
_pool = None

class SqlCommand(object):
  def __init__(self,sql):
    self.sql = sql
    self.ev = Event()
    self.res = None
    self.exc = None

class ThreadPool(object):
  def __init__(self,num_threads):
    self.threads = []
    self.queue = Queue()
    for i in xrange(num_threads):
      t = DbWorker(self.queue)
      t.start()

  def execute(self,sql):
    cmd = SqlCommand(sql)
    self.queue.put(cmd)
    cmd.ev.wait()
    return cmd.res + [(False,cmd.exc)]


class DbWorker(Thread):
  def __init__(self,queue):
    self.queue = queue
    self.alive = True
    self.connection,self.dbmodule = _get_conn()
    Thread.__init__(self)

  def run(self):
    while self.alive:
      try:
        cmd = self.queue.get(True,10)
      except Empty:
        continue
      cur = self.connection.cursor()
      res = []
      try:
        cur.execute(cmd.sql)
        res.append((cur.description,cur.fetchall() if cur.description else cur.rowcount))
        while cur.nextset():
          res.append((cur.description,cur.fetchall() if cur.description else cur.rowcount))
        cmd.res = res
      except self.dbmodule.Error,e:
        cmd.exc = e
        cmd.res = res
      except:
        #TODO:log
        cmd.exc = e
        cmd.res = []
      cmd.ev.set()
      cur.close()

def set_options(options):
  global _options,_pool
  _options = options
  _pool = ThreadPool(_options.num_threads)

def _get_conn():
  db_module = {
    "mysql":"MySQLdb",
  }[_options.db_type]
  module = __import__(db_module)
  return module.connect(user = _options.user,passwd = _options.password,host = _options.host,db = _options.db),module

def _encode_result(desc,rows):
  if desc:
    return {
        "TYPES":[d[1] for d in desc],
        "HEADER":[d[0] for d in desc],
        "ROWS" : rows
      }
  else:
    if isinstance(rows,Exception):
      return {"MYSQL_ERRNO" : rows.args[0] , "MYSQL_ERROR" : rows.args[1]}
    return {"SUCCESS":True,"ROWCOUNT":rows}

def handle(env,start_response):
  try:
    qs = loads(unquote_plus(env['QUERY_STRING']))
    sql = qs["SQL"]
  except Exception,e:
    #TODO:log exception
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return '{"ERROR" : "we got problems -  couldn`t parse your incoming json"}'


  results = _pool.execute(sql)
  start_response('200 OK', [('Content-Type', 'text/plain')])
  res = {
    "RESULT":[_encode_result(desc,rows) for desc,rows in results if rows is not None]
  }
  if len(res["RESULT"]) == 1:
    res["RESULT"] = res["RESULT"][0]
  return [dumps(res,ensure_ascii=False,default = lambda obj:obj.strftime("%Y-%m-%d %H:%M:%S") if isinstance(obj, datetime.datetime) else obj)]
  