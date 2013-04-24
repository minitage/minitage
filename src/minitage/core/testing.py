import sys
import os
import tempfile
import tarfile
import shutil
import subprocess
from StringIO import StringIO
import pkg_resources
from zc.buildout import buildout as bo

from distutils.dir_util import copy_tree
from minitage.core.common import first_run

from minitage.core.api import get_minimerge

from plone.testing.layer import Layer as Base
from zc.buildout.testing import (
    remove,
    _start_server,
    stop_server,
)


B = os.path.basename
D = os.path.dirname
J = os.path.join


SETUP = """
from setuptools import setup
%s
setup(name='%s',
      version='%s',
      py_modules=['toto'])
"""
MODULE = """
def f():
    print "foo"
"""


MINITAGE_CFG = """
[buildout]
parts=part
index=%(index)s
find-links=%(index)s
[part]
recipe=minitage.recipe.scripts
eggs=minitage
"""


def get_uname():
    if 'linux' in sys.platform:
        return 'linux'
    else:
        return sys.platform

uname = get_uname()


def get_args(args):
    res = []
    for arg in args:
        if isinstance(arg, str):
            res.append(arg)
        if isinstance(arg, list) or isinstance(arg, tuple):
            res.extend(get_args(arg))
    return res


def get_joined_args(args):
    res = get_args(args)
    return J(*res)


current_dir = os.path.abspath(D(__file__))


def mkdir(*args):
    a = get_joined_args(args)
    if not os.path.isdir(a):
        os.makedirs(a)


def rmdir(*args):
    a = get_joined_args(args)
    if os.path.isdir(a):
        shutil.rmtree(a)


def sh(cmd, in_data=None, out=None):
    if out is not None:
        if isinstance(out, bool):
            out = StringIO()
    _cmd = cmd
    if out is None:
        print cmd
    elif out:
        out.write(cmd)
    p = subprocess.Popen([_cmd], shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=True)

    if in_data is not None:
        p.stdin.write(in_data)

    p.stdin.close()

    if out is None:
        print p.stdout.read()
        print p.stderr.read()
    elif out:
        out.write(p.stdout.read())
        out.write(p.stderr.read())


def ls(*args):
    a = get_joined_args(args)
    if os.path.isdir(a):
        filenames = os.listdir(a)
        for filename in sorted(filenames):
            print filename
    else:
        print 'No directory named %s' % args


def cd(*args):
    a = get_joined_args(args)
    os.chdir(a)


def config(filename):
    return J(current_dir, filename)


def install(dist, destination):
    if isinstance(dist, str):
        dist = pkg_resources.working_set.find(
            pkg_resources.Requirement.parse(dist))
    if dist.location.endswith('.egg'):
        destination = J(destination,
                                   os.path.basename(dist.location),
                                   )
        if not os.path.exists(destination):
            if os.path.isdir(dist.location):
                shutil.copytree(dist.location, destination)
            else:
                shutil.copyfile(dist.location, destination)
    else:
        open(J(
            destination, dist.project_name + '.egg-link'), 'w'
        ).write(dist.location)


def install_develop(dist, destination):
    if not isinstance(destination, str):
        destination = J(destination.globs['sample_buildout'],
                                   'develop-eggs')
    if isinstance(dist, str):
        dist = pkg_resources.working_set.find(
            pkg_resources.Requirement.parse(dist))
    open(
        J(destination,
                     dist.project_name + '.egg-link'), 'w'
    ).write(dist.location)


def install_buildout(destination=".", requirements=None,
                     cfg='buildout.cfg', buildout=None):
    destination = os.path.abspath(destination)
    if not requirements:
        requirements = ['minitage[test]']
    if not os.path.exists(destination):
        os.makedirs(destination)
    develop_path = J(
        destination, 'develop-eggs')
    eggs_path = J(
        destination, 'eggs')
    for p in [eggs_path, develop_path]:
        if not os.path.exists(p):
            os.makedirs(p)
    if not isinstance(requirements, (list, tuple)):
        requirements = [requirements]
    env = pkg_resources.Environment()
    ws = pkg_resources.WorkingSet()
    rs = []
    for req in requirements:
        rs.append(pkg_resources.Requirement.parse(req))
    dists = ws.resolve(rs, env)
    todo = {}
    for dist in dists:
        todo.setdefault(dist.precedence, [])
        todo[dist.precedence].append(dist)
    for p in [pkg_resources.DEVELOP_DIST,
              pkg_resources.EGG_DIST]:
        for dist in todo.get(p, []):
            install(dist, eggs_path)
    bootstrap(destination)
    if buildout:
        touch(destination, cfg, data=buildout)


def cat(*args, **kwargs):
    filename = J(*args)
    if os.path.isfile(filename):
        data = open(filename).read()
        if kwargs.get('returndata', False):
            return data
        print data
    else:
        print 'No file named %s' % filename


def touch(*args, **kwargs):
    filename = J(*args)
    open(filename, 'w').write(kwargs.get('data', ''))


def buildout(*args):
    argv = sys.argv[:]
    sys.argv = ["foo"] + list(args)
    ret = bo.main()
    sys.argv = argv
    return ret

_dists = []

def clean():
    for cache in ['eggs', '../../eggs/cache']:
        if os.path.exists(cache):
            noecho = [remove(J(cache, egg))
                      for egg in os.listdir(cache)
                      if True in [
                          d in egg for d in _dists
                      ]
                     ]


def cleandist():
    if os.path.exists('minitage/eggs'):
        noecho = [os.remove(J('minitage/eggs', d))
                  for d in os.listdir('minitage/eggs') if '.tar.gz' in d]
    if os.path.exists('eggs'):
        noecho = [os.remove(J('eggs', d))
                  for d in os.listdir('eggs') if '.tar.gz' in d]
    noecho = [os.remove(d)
              for d in os.listdir('.') if '.tar.gz' in d]


def bootstrap(bp=None):
    cwd = os.getcwd()
    try:
        if bp and os.path.exists(bp):
            os.chdir(bp)
        if not os.path.exists('buildout.cfg'):
            touch('buildout.cfg')
        sh('buildout -o bootstrap', out=StringIO())
    finally:
        os.chdir(cwd)


def create_package(supath):
    dest = os.path.join(supath, 'buildout-package')
    tarp = os.path.abspath(os.path.join(supath, '../buildout-package.tgz'))
    make_dummy_buildoutdir(dest)
    tar = tarfile.open(tarp, "w:gz")
    tar.add(dest, '.')
    tar.close()
    return tarp


def makedist(name="foo", version="1.0", module=MODULE, setup=''):
    if not name in _dists:
        _dists.append(name)
    if not os.path.exists(name):
        os.makedirs(name)
    touch('%s/setup.py' % name,
          data=SETUP % (setup, name, version))
    touch('%s/toto.py' % name, data=MODULE)
    os.chdir(name)
    sh('python setup.py sdist', out=False)
    noecho = [shutil.copy(
        J('dist', d), J('..', d))
        for d in os.listdir('dist')]
    os.chdir('..')


def create_minitage_env(directory, requirements=None):
    """Initialise a minitage in a particular directory."""
    install_buildout(directory, cfg='b.cfg',
                     requirements=requirements,
                     buildout=MINITAGE_CFG % LAYER['bsettings'])
    cwd = os.getcwd()
    try:
        os.chdir(directory)
        sh(directory + '/bin/buildout -Nc b.cfg')
        sh(directory + '/bin/minimerge')
    finally:
        os.chdir(cwd)


class Layer(Base):

    defaultBases = tuple()
    requirements = ('minitage[test]',)

    def setUp(self):
        self['pathes'] = []
        root = p = self["p"] = self["tempdir"] = self['bp'] = (
            tempfile.mkdtemp()
        )
        self['path2'] = J(root, 'p2')
        self['path3'] = J(root, 'p3')
        self['wc'] = J(root, 'wc')
        if not os.path.exists(root):
            os.makedirs(root)
        self['__tear_downs'] = __tear_downs = []
        self['register_teardown'] = __tear_downs.append

        def start_index(pt):
            port, thread = _start_server(pt, name=pt)
            url = 'http://localhost:%s/' % port
            self['register_teardown'](
                lambda: stop_server(url, thread))
            return url
        self['start_index'] = start_index
        self['index_url'] = start_index(root)
        self['bsettings'] = {
            'index': self['index_url'],}
        self['dl'] = J(root, 'dl')
        self['eggp'] = J(root, 'foo')
        self['opath'] = os.environ['PATH']
        self.add_path()
        self.set_path()
        create_minitage_env(root, self.requirements)
        self['minimerge'] = get_minimerge(
            config='%(p)s/etc/minimerge.cfg' % LAYER)
        self['globs'] = globals()
        self['globs'].update(locals())

    _synced = False
    def sync(self, force=False):
        if not self._synced or force:
            self['minimerge']._sync()
            self['minimerge'].load_minilays()

    def add_path(self, requirements=None):
        if not requirements:
            requirements = self.requirements
        for i in requirements:
            cwd = pkg_resources.resource_filename(
                pkg_resources.Requirement.parse(i), 'tests')
            for root in [
                D(D(D(D(D(cwd))))) ,
                D(D(D(D(cwd)))),
                D(D(D(cwd))) ,
                D(D(cwd)) ,
                D(cwd) ,
            ]:
                rbin = J(root, 'bin')
                if os.path.exists(rbin):
                    self['pathes'].append(rbin)

    def tearDown(self):
        for f in self['__tear_downs']:
            f()

    def set_path(self):
        for rbin in self['pathes']:
            if not rbin in self['opath']:
                os.environ['PATH'] = ":".join(
                    [rbin, self['opath']])

    def testSetUp(self):
        for p in (self['eggp'], self['dl']):
            ep = self['bp'] + p
            if not os.path.exists(ep):
                mkdir(ep)

    def testTearDown(self):
        os.environ['PATH'] = self['opath']

def make_dummy_buildoutdir(ipath):
    if not os.path.exists(ipath):
        os.makedirs(ipath)
    touch(ipath, 'buildout.cfg', data="""
[makers]
[buildout]
download-directory=${buildout:directory}/../../eggs/cache
download-cache=${buildout:directory}/../../eggs/cache
options = -c buildout.cfg  -vvvvvv
index = %(index)s
find-links=%(index)s
parts = x
        z
develop = .
[part]
recipe = toto:part
[site-packages-2.4]
recipe = toto:py24
[site-packages-2.5]
recipe = toto:py25
[z]
recipe = toto:luu
[y]
recipe = toto:bar
[x]
recipe = toto """ % LAYER['bsettings'])
    touch(ipath, 'setup.py', data="""
from setuptools import setup
setup(
          name='toto',
          entry_points= {
          'zc.buildout': [
              'default = toto:test',
              'luu = tutu:test',
              'bar = tata:test',
              'py25 = py25:test',
              'py24 = py24:test',
              'part = part:test',
             ]
         }
) """)

    touch(ipath,'toto.py', data="""
class test:
    def __init__(self,a, b, c):
        pass

    def install(a):
        print "foo" """)
    touch(ipath,'tata.py', data="""
class test:
    def __init__(self,a, b, c):
        pass

    def install(a):
        open('testbar','w').write('foo') """)
    touch(ipath,'tutu.py', data="""
class test:
    def __init__(self,a, b, c):
        pass

    def install(a):
        open('testres','w').write('bar') """)

    touch(ipath,'py25.py', data="""
class test:
    def __init__(self,a, b, c):
        pass

    def install(a):
        open('testres2.5','w').twrite('2.5') """)

    touch(ipath,'py24.py', data="""
class test:
    def __init__(self,a, b, c):
        pass

    def install(a):
        open('testres2.4','w').write('2.4') """)
    ds = open(
            pkg_resources.resource_filename(
                pkg_resources.Requirement.parse('minitage'),'minitage/core/distribute_setup.py')
    ).read()
    boot = open(
        J(D(
            pkg_resources.resource_filename(
                pkg_resources.Requirement.parse('minitage'), '')), 'bootstrap.py')
    ).read()
    touch(ipath, 'bootstrap.py', data=boot)
    touch(ipath, 'distribute_setup.py', data=boot)
    touch(ipath,'part.py', data="""
class test:
    def __init__(self,a, b, c):
        pass

    def install(a):
        open('testres','w').write('part')
          """)


LAYER = Layer()
