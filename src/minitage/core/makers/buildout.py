__docformat__ = 'restructuredtext en'

import os
import sys
import logging
import re
re_f = re.S|re.M|re.U
import copy

import pkg_resources
import urllib2

from minitage.core.makers  import interfaces
from iniparse import ConfigParser
from minitage.core.unpackers  import interfaces as uinterfaces
import minitage.core.core
import minitage.core.common
import subprocess
import traceback

from threading  import Thread
import fcntl

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names
def run_boot_setup():
    ret = subprocess.Popen(['bin/buildout', 'setup', '.minitage/setup.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    return ret


def enqueue_output(ret, queue):
    while True:
        out = ret.stdout.read()
        eout = ret.stderr.read()
        if (eout == '') and  (out == '') and (ret.returncode != None):
            break
        queue.put(out)
        queue.put(eout)
        sys.stdout.write(out)
        sys.stdout.write(eout)
    ret.stdout.close()
    ret.stderr.close()


class BuildoutError(interfaces.IMakerError):
    """General Buildout Error."""

__logger__ = 'minitage.makers.buildout'


class MrDeveloperError(BuildoutError): pass

def select_fl(fl):
    found = False
    ret = None
    for d in fl:
        if os.path.exists(d):
            files = os.listdir(d)
            has_st = True in [True
             for a in files
             if (a.startswith('setuptools')
                 and (a.endswith('gz')
                     or a.endswith('zip')
                     or a.endswith('egg')
                 ))]
            has_ds = True in [True
             for a in files
             if (a.startswith('distribute')
                 and (a.endswith('gz')
                     or a.endswith('zip')
                     or a.endswith('egg')
                 ))]
            has_buildout = True in [True
             for a in files
             if (a.startswith('zc.buildout')
                 and (a.endswith('gz')
                     or a.endswith('zip')
                     or a.endswith('egg')
                 ))]
            if has_buildout and (has_st or has_ds):
                ret = d
                found = True
                break
    return ret



def get_offline(opts):
    minimerge_offline = (True=='minimerge' in opts) and opts['minimerge']._offline or False
    offline = (opts.get('offline', False) or minimerge_offline)
    return offline


class BuildoutMaker(interfaces.IMaker):
    """Buildout Maker.
    """
    def select_ds(self, distribute_setup_places, py = None):
        mfile = 'distribute_setup.py'
        if self.has_setuptools7(py):
            mfile = 'ez_setup.py'
        ds = None
        for i in distribute_setup_places:
            ds = os.path.join(i, mfile)
            if os.path.exists(ds):
                break
            else:
                ds = None
        return ds

    def __init__(self, config = None, verbose=False):
        """Init a buildout maker object.
        Arguments
            - config keys:

                - options: cli args for buildout
        """
        if not config:
            config = {}
        self.logger = logging.getLogger(__logger__)
        self.config = config
        self.cwd = os.getcwd()
        self.buildout_config = 'buildout.cfg'
        interfaces.IMaker.__init__(self)

    def match(self, switch):
        """See interface."""
        if switch == 'buildout':
            return True
        return False

    def has_setuptools7(self, py=None):
        new_st = False
        if not py:
            py = sys.executable
        try:
            cmd = [py,
                   "-c",
                   "import pkg_resources;print not pkg_resources.get_distribution('distribute').version.startswith('0.6')"]
            #self.logger.debug('Run %s' % " ".join(cmd))
            ret = subprocess.Popen(
               cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,)
            if ret.wait() == 0:
                if 'true' in ret.stdout.read().lower():
                    new_st = True
        except Exception, e:
            new_st = False
        return new_st

    def upgrade_code(self, opts):
        """try to run mr.developer but not as a fail element"""
        if (
            not opts['offline']
            and os.path.isfile('bin/develop')
            and opts['minimerge'].is_package_to_be_updated(
                opts['minibuild'])
        ):
            content  = open('bin/develop').read()
            if 'mr.developer' in content:
                self.logger.info(
                    'Running mr.developer update')
                helpret = subprocess.Popen(
                    ['bin/develop', 'up', '--help'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                )
                outputs = []
                while helpret.poll() is None:
                    outputs.append(helpret.communicate())
                if helpret.wait() != 0:
                    raise MrDeveloperError('error with help')
                else:
                    content = ''.join([a[0] for a in outputs])
                    cmd = ['bin/develop', 'up', '-v']
                    if '--force' in content:
                        cmd.append('--force')
                    self.logger.info(
                        'Running %s' % ' '.join(cmd))
                    ret = subprocess.Popen(
                        cmd, bufsize=-1,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,)
                    #for i in (ret.stdout, ret.stderr):
                    #    fd = i.fileno()
                    #    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                    #    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                    q = Queue()
                    t = Thread(target=enqueue_output, args=(ret, q,))
                    t.daemon = True
                    t.start()
                    outputs = []
                    ret.wait()
                    buf = ''
                    while not q.empty():
                        buf += q.get()
                    q.join()
                    if t and t.is_alive(): #wait for thread to finish
                        t.join()
                    if ret.returncode == 0:
                        self.logger.info('mr.developer successfuly updated code')
                    else:
                        raise MrDeveloperError('mr.developer failed to update code')

    def upgrade_bootstrap(self, minimerge, offline, directory=".", py=None):
        buildout1 = False
        try:
            def findcfgs(path, cfgs=None):
                ignored = ['var', 'parts']
                dirs = []
                if not cfgs: cfgs=[]
                for i in os.listdir(path):
                    fi = os.path.join(path, i)
                    if fi.endswith('.cfg') and os.path.isfile(fi):
                        cfgs.append(fi)
                    if os.path.isdir(fi) and (not i in ignored):
                        dirs.append(fi)
                for fpath in dirs:
                    for p, ids, ifs in os.walk(fpath):
                        for i in ifs:
                            if i.endswith('.cfg'):
                                cfgs.append(os.path.join(p, i))
                return cfgs
            files = findcfgs(directory)
            for f in files:
                fic = open(f)
                buildout1re = re.compile('^zc\.buildout\s*=\s*1', re_f)
                dfic = fic.read()
                if (
                        ('buildout.dumppick' in dfic)
                        or
                        (buildout1re.search(dfic))
                ):
                    buildout1 = True
                fic.close()
            adirectory = os.path.abspath(directory)
            if (
                ('dependencies/' in adirectory)
                or ('eggs/' in adirectory)
            ):
                buildout1 = True

        except Exception, e:
            pass
        if buildout1:
            booturl = 'http://downloads.buildout.org/1/bootstrap.py'
        else:
            #if self.has_setuptools7(py=py):
            #    booturl = 'https://raw.github.com/tseaver/buildout/use-setuptools-0.7/bootstrap/bootstrap.py'

            #else:
            booturl = 'http://downloads.buildout.org/2/bootstrap.py'
        self.logger.debug('Using %s' % booturl)
        # try to donwload an uptodate bootstrap
        # set defaulttimeout
        # and add possible content
        try:
            try:
                fic = open('bootstrap.py')
                oldcontent = fic.read()
                fic.close()
            except:
                oldcontent = ""
            data = oldcontent
            updated = False
            dled = False
            if not offline:
                try:
                    open(
                        os.path.join(minimerge.history_dir,
                                     'updated_bootstrap'))
                except:
                    self.logger.info('Bootstrap updated')
                    data = urllib2.urlopen(booturl).read()
                    updated = True
                    dled = True
            if not 'socket.setdefaulttimeout' in data:
                updated = True
                ldata = data.splitlines()
                ldata.insert(1, 'import socket;socket.setdefaulttimeout(2)')
                data = '\n'.join(ldata)
            if updated:
                self.logger.info('Bootstrap updated')
                fic = open('bootstrap.py', 'w')
                fic.write(data)
                fic.close()
            if dled:
                afic = open(os.path.join(
                    minimerge.history_dir, 'updated_bootstrap'), 'w')
                afic.write('foo')
                afic.close()
        except:
            if oldcontent:
                fic = open('bootstrap.py', 'w')
                fic.write(oldcontent)
                fic.close()

    def reinstall(self, directory, opts=None):
        """Rebuild a package.
        Warning this will erase .installed.cfg forcing buildout to rebuild.
        Problem is that underlying recipes must know how to handle the part
        directory to be already there.
        This will be fine for minitage recipes in there. But maybe that will
        need boiler plate for other recipes.
        Exceptions
            - ReinstallError
        Arguments
            - directory : directory where the packge is
            - opts : arguments for the maker
        """
        mypath = os.path.join(
            directory,
            '.installed.cfg'
        )
        if os.path.exists(mypath):
            os.remove(mypath)
        self.install(directory, opts)

    def install(self, directory, opts=None):
        """Make a package.
        Exceptions
            - MakeError
        Arguments
            - dir : directory where the packge is
            - opts : arguments for the maker
        """
        if opts is None:
            opts = {}
        self.logger.info(
            'Running buildout in %s (%s)' % (directory,
                                             self.buildout_config))
        os.chdir(directory)
        minibuild = opts.get('minibuild', None)
        installed_cfg = os.path.join(directory, '.installed.cfg')
        if not opts:
            opts = {}
        try:
            try:
                parts = opts.get('parts', False)
                if isinstance(parts, str):
                    parts = parts.split()
                category = ''
                if minibuild: category = minibuild.category
                # Try to upgrade only if we need to
                # (we chech only when we have a .installed.cfg file
                if (not opts.get('upgrade', True)
                    and os.path.exists(installed_cfg)
                    and (not category=='eggs')):
                    self.logger.info(
                        'Buildout will not run in %s'
                        ' as there is a .installed.cfg file'
                        ' indicating us that the software is already'
                        ' installed but minimerge is running in'
                        ' no-update mode. If you want to try'
                        ' to update/rebuild it unconditionnaly,'
                        ' please relaunch with -uUR.' % directory)
                else:
                    self.upgrade_code(opts)
                    self.buildout_bootstrap(directory, opts)
                    self.buildout(directory, parts, opts)
            except Exception, instance:
                trace = traceback.format_exc()
                raise BuildoutError(
                    'Buildout failed:\n\t%s' % trace)
        finally:
            os.chdir(self.cwd)

    def buildout_bootstrap(self, directory, opts):
        offline = get_offline(opts)
        dcfg = os.path.expanduser('~/.buildout/default.cfg')
        minimerge = opts.get('minimerge', None)
        py = self.choose_python(directory, opts)
        new_st = self.has_setuptools7(py=py)
        downloads_caches = [
            os.path.abspath('../../downloads/dist'),
            os.path.abspath('../../downloads/minitage/eggs'),
            os.path.abspath('../../downloads/minitage'),
            os.path.abspath('../../download/dist'),
            os.path.abspath('../../download/minitage/eggs'),
        ]
        if os.path.exists(dcfg):
            try:
                cfg = ConfigParser()
                cfg.read(dcfg)
                buildout = dict(cfg.items('buildout'))
                for k in ['download-directory', 'download-cache']:
                    if k in buildout:
                        places = [k,
                                  '%s/dist' % k,
                                  '%s/minitage/eggs'%k]
                        for k in places:
                            if not k in downloads_caches:
                                downloads_caches.append(k)
            except Exception, e:
                pass
        find_links = []
        cache = os.path.abspath(
            os.path.join(directory, ('../../eggs/cache'))
        )
        for c in [cache] + downloads_caches:
            if os.path.exists(c) and not c in find_links:
                find_links.append(c)
        distribute_setup_places = find_links[:] + downloads_caches + [
            os.path.join(directory, 'downloads/minitage/eggs'),
            os.path.join(directory, 'downloads/dist'),
            os.path.join(directory, 'downloads'),
            os.path.join(directory, 'download/minitage/eggs'),
            os.path.join(directory, 'download/dist'),
            os.path.join(directory, 'download'),
            os.path.join(directory),
            os.path.expanduser('~/.buildout'),
            os.path.expanduser('~/.buildout/download'),
            os.path.expanduser('~/.buildout/download/dist'),
            os.path.expanduser('~/.buildout/download/minitage'),
            os.path.expanduser('~/.buildout/download/minitage/eggs'),
            os.path.expanduser('~/.buildout/downloads'),
            os.path.expanduser('~/.buildout/downloads/dist'),
            os.path.expanduser('~/.buildout/downloads/minitage'),
            os.path.expanduser('~/.buildout/downloads/minitage/eggs'),
            os.path.expanduser('~/'),
        ]

        bootstrap_args = ''
        st_bootstrap_args = ''
        self.upgrade_bootstrap(minimerge, offline, py=py)
        # be sure which buildout bootstrap we have
        fic = open('bootstrap.py')
        content = fic.read()
        fic.close()
        if '--distribute' in content:
            if not new_st:
                bootstrap_args += ' %s' % '--distribute'
        if new_st:
            self.logger.warning('Forcing to use setuptools')
        has_buildout2, has_buildout1 = False, False
        if offline:
            if ' --accept-buildout-test-releases' in content:
                bootstrap_args += ' --accept-buildout-test-releases'
        if ('--setup-source' in content
            and not "--find-links" in content):
            ds = self.select_ds(distribute_setup_places, py=py)
            if not ds and offline:
                raise Exception(
                    'Bootstrap failed, '
                    'no distribute_setup.py '
                    'found in %s '
                    '' % ' '.join(
                            distribute_setup_places))
            if ds:
                for eggc in  (
                    os.path.abspath(os.path.abspath('../../downloads/minitage/eggs')),
                    os.path.abspath(os.path.abspath('../../eggs/cache')),
                ):
                    if os.path.exists(eggc):
                        break
                bootstrap_args += ' --setup-source %s' % ds
                bootstrap_args += ' --eggs %s' % (eggc)
                st_bootstrap_args += ' --setup-source %s' % ds.replace('distribute_setup.py', 'ez_setup.py')
                st_bootstrap_args += ' --eggs %s' % (eggc)
        try:
            eggs_base = select_fl(find_links)
        except:
            eggs_base = None
            if offline:
                raise Exception(
                    'Missing either '
                    'zc.buildout or distribute/setuptools source')
        bare_bootstrap_args = bootstrap_args
        st_bare_bootstrap_args = st_bootstrap_args
        boot_can_continue = False
        if not os.path.isdir(".minitage"):
            os.makedirs(".minitage")
        # Be sure to have an unzipped eggs
        SCRIPT = """
import pkg_resources
for i in ['setuptools', 'zc.buildout']:
    print pkg_resources.get_distribution(i).location

        """
        fic = open('.minitage/setup.py', 'w')
        fic.write(SCRIPT)
        fic.close()
        if eggs_base is not None:
            arg = ""
            if '--download-base' in content:
                arg = "--download-base"
            if '--find-links' in content:
                arg = "--find-links"
            if arg:
                bootstrap_args += ' %s "%s"' % (
                    arg, eggs_base)
        if self.buildout_config and '"-c"' in content:
            bootstrap_args += " -c %s" % self.buildout_config
            bare_bootstrap_args += " -c %s" % self.buildout_config
            st_bootstrap_args += " -c %s" % self.buildout_config
            st_bare_bootstrap_args += " -c %s" % self.buildout_config
        BARGS = [(st_bootstrap_args, st_bare_bootstrap_args)]
        if '--distribute' in content:
            BARGS.append((bootstrap_args, bare_bootstrap_args))
        for ix, bargs in enumerate(BARGS):
            bootstrap_args, bare_bootstrap_args = bargs
            try:
                cmd = '%s bootstrap.py %s ' % (py, bootstrap_args,)
                self.logger.info('Running %s' % cmd)
                if '--distribute' in cmd:
                    self.logger.warning('Using distribute !')
                minitage.core.common.Popen(cmd , opts.get('verbose', False))
                boot_setup = run_boot_setup()
                if boot_setup.wait() == 0:
                    boot_can_continue = True
            except Exception, e:
                self.logger.error('Buildout bootstrap failed, trying online !')
                cmd = '%s bootstrap.py %s ' % (py, bare_bootstrap_args,)
                self.logger.info('Running %s' % cmd)
                try:
                    if '--distribute' in cmd:
                        self.logger.warning('Using distribute !')
                    minitage.core.common.Popen(cmd, opts.get('verbose', False))
                    boot_setup = run_boot_setup()
                    if boot_setup.wait() == 0:
                        boot_can_continue = True
                except Exception, ex:
                    if ix < len(BARGS) -1:
                        continue
                    else:
                        raise
            if boot_can_continue:
                break
        if boot_can_continue:
            output = [a for a in boot_setup.stdout.read().splitlines()
                      if os.path.exists(a)]
            for a in output:
                if os.path.isfile(a):
                    # unpack
                    self.logger.info('Unpack to dir: %s' % a)
                    f = uinterfaces.IUnpackerFactory()
                    n = 1
                    while True:
                        n += 1
                        orig = '%s.old.%s' % (a, n)
                        try:
                            os.rename(a, orig)
                            break
                        except:
                            if n > 100:
                                raise
                            else:
                                pass
                    zipf = f(orig)
                    zipf.unpack(orig, a,)
        else:
            raise BuildoutError(
                'Buildout not bootstrapped')

    def buildout(self,
                 directory=".",
                 parts=None,
                 opts=None):
        offline = get_offline(opts)
        bcmd = os.path.normpath('./bin/buildout')
        minibuild = opts.get('minibuild', None)
        dependency_or_egg = (getattr(minibuild, 'category', None)
                             in ['dependencies', 'eggs'])
        offline = get_offline(opts)
        argv = []
        if not parts:
            parts = []
        if not opts:
            opts = {}
        if opts.get('verbose', False):
            self.logger.debug(
                'Buildout is running in verbose mode!')
            argv.append('-vvvvvvv')
        installed_cfg = os.path.join(directory, '.installed.cfg')
        if (not opts.get('upgrade', True)
            and not dependency_or_egg
            and not os.path.exists(installed_cfg)):
            argv.append('-N')
        if opts.get('upgrade', False) or dependency_or_egg:
            self.logger.debug(
                'Buildout is running in newest mode!')
            argv.append('-n')
        if offline:
            self.logger.debug(
                'Buildout is running in offline mode!')
            argv.append('-o')
        if opts.get('debug', False):
            self.logger.debug(
                'Buildout is running in debug mode!')
            argv.append('-D')
        if parts:
            for part in parts:
                self.logger.info(
                    'Installing single part: %s' % part)
                minitage.core.common.Popen(
                    '%s -c %s %s install %s ' % (
                        bcmd,
                        self.buildout_config,
                        ' '.join(argv),
                        part
                    ),
                    opts.get('verbose', False)
                )
        else:
            self.logger.debug('Installing parts')
            cmd = '%s -c %s %s ' % (
                bcmd,
                self.buildout_config,
                ' '.join(argv))
            minitage.core.common.Popen(
                cmd,
                opts.get('verbose', False)
            )

    def choose_python(self, directory, opts):
        python = sys.executable
        mb =  opts.get('minibuild', None)
        if mb:
            if os.path.exists(mb.python):
                python = mb.python
        return python

    def get_options(self, minimerge, minibuild, **kwargs):
        """Get python options according to the minibuild and minimerge instance.
        For eggs buildouts, we need to know which versions of python we
        will build site-packages for
        For parts, we force to install only the 'part' buildout part.
        Arguments
            - we can force parts with settings 'buildout_parts' in minibuild
            - minimerge a minitage.core.Minimerge instance
            - minibuild a minitage.core.object.Minibuild instance
            - kwargs:

                - 'python_versions' : list of major.minor versions of
                  python to compile against.
        """
        options = {}
        parts = self.buildout_config = [
            a.strip()
            for a in minibuild.minibuild_config._sections[
                'minibuild'].get('buildout_parts', '').split()]
        if kwargs is None:
            kwargs = {}

        # if it s an egg, we must install just the needed
        # site-packages if selected
        if minibuild.category == 'eggs':
            vers = kwargs.get('python_versions', None)
            if not vers:
                vers = minitage.core.core.PYTHON_VERSIONS
            parts = ['site-packages-%s' % ver for ver in vers]
        self.buildout_config = minibuild.minibuild_config._sections[
            'minibuild'].get('buildout_config',
                             'buildout.cfg')
        content = ''
        if minibuild.category == 'eggs':
            try:
                fic = open(os.path.join(minimerge.get_install_path(minibuild), self.buildout_config))
                content = fic.read()
                fic.close()
            except:
                pass
            parts = [p for p in parts+['site-packages'] if '[%s]'%p in content]

        options['parts'] = parts
        # prevent buildout from running if we have already installed stuff
        # and do not want to upgrade.
        options['upgrade'] = minimerge.getUpgrade()
        if minimerge.has_new_revision(minibuild):
            options['upgrade'] = True
        return options

# vim:set et sts=4 ts=4 tw=80:
