from setuptools import setup

setup(name='pyslayer',
      version='0.1',
      packages=['pyslayer'],
      scripts=['scripts/pyslayer'],
      install_requires = ['MySQLdb'],
      extras_require = {'process title': ["setproctitle"],'daemonize':["python-daemon"]},
      author = "Uriel Katz",
      author_email = "uriel.katz@gmail.com",
      description = "a python clone of dbslayer - JSON HTTP abstraction for DBAPI",
      license = "MIT",
      keywords = "dbslayer json dbapi",
      url = "https://github.com/urielka/pyslayer",
      download_url = "https://github.com/urielka/pyslayer/downloads",
      zip_safe = False,
      entry_points = '''
      [console_scripts]
      pyslayer = pyslayer.main:cli_start
      ''',
)