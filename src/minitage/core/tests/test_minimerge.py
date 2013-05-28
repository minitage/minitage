__docformat__ = 'restructuredtext en'

import unittest
import os
import sys
import shutil
import optparse
import ConfigParser
import tempfile

from minitage.core import api, cli, objects, core
from minitage.core import update
from minitage.core import tests
from minitage.core.tests.base import TestCase
from minitage.core.api import get_minimerge

from minitage.core.testing import (
    touch,
    J, D, B,
    create_package,
    rmdir,
    make_dummy_buildoutdir,
    LAYER,
    Base,
)

__cwd__ = os.getcwd()

minilay_base = '%(p)s/minilays/myminilay1'
path_base = '%(p)s/test'


class Layer(Base):

    defaultBases = (LAYER,)

    def sync(self, force=False):
        return LAYER.sync(force)

    def setUp(self):
        """."""
        self['minilay'] = self.minilay = minilay_base % LAYER
        self['path'] = self.path = path_base % LAYER
        self['package'] = self.package = create_package(self.path)
        if not os.path.exists(self.minilay):
            os.makedirs(self.minilay)
        minibuilds = [
"""
[minibuild]
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-0
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-4 minibuild-1
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-2
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-0
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-7
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-5
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-6
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-8
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-0 minibuild-3
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-11
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-12
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-13
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
"""
[minibuild]
dependencies=minibuild-10
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""" ]

        pythonmbs = [
#1000
"""
[minibuild]
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=dependencies
""", #1001
"""
[minibuild]
dependencies=meta-python minibuild-1005
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=dependencies
""", #1002
"""
[minibuild]
dependencies=python-2.4 minibuild-1005
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=dependencies
""", #1003
"""
[minibuild]
dependencies=python-2.5 minibuild-1005
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=dependencies
""", #1004
"""
[minibuild]
dependencies=minibuild-1005
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=dependencies
""", #1005
"""
[minibuild]
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=eggs
""",
]
        for index, minibuild in enumerate(minibuilds):
            touch('%s/minibuild-%s' % (self.minilay, index),
                  data=minibuild%LAYER['bsettings'])

        os.system("""cd %s ;
                  hg init;
                  hg add ;
                  hg ci -m 1;""" % self.minilay)
        for index, minibuild in enumerate(pythonmbs):
            touch('%s/minibuild-100%s' % (self.minilay, index),
                  data=minibuild%LAYER['bsettings'])

        # fake 3 pythons.
        for minibuild in ['python-2.4', 'python-2.5', 'python-2.6']:
            touch('%s/%s' % (self.minilay, minibuild), data="""
[minibuild]
src_uri=%(index)s/buildout-package.tgz
src_type=static
install_method=buildout
category=dependencies"""%LAYER['bsettings'])

        touch('%s/%s' % (self.minilay, 'meta-python'), data="""
[minibuild]
dependencies=python-2.4 python-2.5 python-2.6
src_uri=%(index)s/buildout-package.tgz
src_type=static
category=meta
install_method=buildout"""%LAYER['bsettings'])
        os.system("""
                  cd %s ;
                  echo "[paths]">.hg/hgrc
                  echo "default = %s">>.hg/hgrc
                  hg add;
                  hg ci -m 2;""" % (self.minilay, self.minilay))
        self['minimerge'].load_minilays()

    def tearDown(self):
         if os.path.exists(self.minilay):
             rmdir(self.minilay)


    def testTearDown(self):
        paths = [
            self['p'] + '/eggs/minibuild-0',
            self['p'] + '/dependencies/python-2.4',
        ]
        for p in paths:
            if os.path.exists(p):
                rmdir(p)


class TestMinimerge(TestCase):
    """testMinimerge"""
    layer = Layer()

    def setUp(self):
        self.minilay = self.layer['minilay']
        self.path = self.layer['path']
        self.package = self.layer['package']
        self.minimerge._offline = True
        os.chdir(self.layer['p'])

    def test100GetInstalledPackage(self):
        """testGetInstalledPackage"""
        package = self.package
        path = D(self.path)
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        if os.path.exists(py24p): shutil.rmtree(py24p)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        os.makedirs(py24p)
        minimerge.record_minibuild(py24)
        mb = minimerge.get_installed_minibuild(py24)
        # packasdge is not installed properly
        self.assertTrue(mb is None)
        if os.path.exists(py24p): shutil.rmtree(py24p)
        minimerge._fetch(py24)
        minimerge._do_action('install', [py24])
        # package is installed
        mb = minimerge.get_installed_minibuild(py24)
        self.assertEquals(os.path.join(py24p, '.minitage', 'minibuild'), mb.path)

    def test101RecordMinibuild(self):
        """testRecordMinibuild"""
        package = self.package
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        if os.path.exists(py24p): shutil.rmtree(py24p)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        os.makedirs(py24p)
        minimerge.record_minibuild(py24)
        self.assertTrue(
            '[minibuild]' in open(
                os.path.join(py24p, '.minitage', 'minibuild')
            ).read()
        )

    def test102IsPackageToBeInstalled(self):
        """testIsPackageToBeInstalled"""
        package = self.package
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        if os.path.exists(py24p): shutil.rmtree(py24p)
        minimerge._action = 'delete'
        self.assertFalse(minimerge.is_package_to_be_installed(py24))
        minimerge._action = 'install'
        self.assertTrue(minimerge.is_package_to_be_installed(py24))
        minimerge._fetch(py24)
        self.assertTrue(minimerge.is_package_to_be_installed(py24))
        minimerge._do_action('install', [py24])
        self.assertFalse(minimerge.is_package_to_be_installed(py24))

    def test103IsPackageToBeReInstalled(self):
        """testIsPackageToBeReInstalled"""
        package = self.package
        path = D(self.path)
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        if os.path.exists(py24p): shutil.rmtree(py24p)
        minimerge._action = 'reinstall'
        self.assertTrue(minimerge.is_package_to_be_installed(py24))
        self.assertFalse(minimerge.is_package_to_be_reinstalled(py24))
        # we cant reinstall as it is not installed
        minimerge._fetch(py24)
        self.assertTrue(minimerge.is_package_to_be_installed(py24))
        self.assertFalse(minimerge.is_package_to_be_reinstalled(py24))
        # we cant reinstall as it is not the wanted action
        minimerge._do_action('install', [py24])
        minimerge._action = 'install'
        self.assertFalse(minimerge.is_package_to_be_reinstalled(py24))
        self.assertFalse(minimerge.is_package_to_be_installed(py24))
        # reinstalling
        minimerge._action = 'reinstall'
        self.assertTrue(minimerge.is_package_to_be_reinstalled(py24))
        self.assertFalse(minimerge.is_package_to_be_installed(py24))
        # reinstall will run always
        minimerge._do_action('reinstall', [py24])
        self.assertTrue(minimerge.is_package_to_be_reinstalled(py24))
        self.assertFalse(minimerge.is_package_to_be_installed(py24))

    def test104IsPackageToBeUpdated(self):
        """testIsPackageToBeUpdated"""
        package = self.package
        path = D(self.path)
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        if os.path.exists(py24p): shutil.rmtree(py24p)
        minimerge._action = 'install'
        minimerge._fetch(py24)
        # package is not installed or just installed, no update
        self.assertFalse(minimerge.is_package_to_be_updated(py24))
        minimerge._do_action('install', [py24])
        self.assertFalse(minimerge.is_package_to_be_updated(py24))
        minimerge._action = 'install'
        self.assertFalse(minimerge.is_package_to_be_updated(py24))
        # we have enabled update unconditionnally
        minimerge._update = True
        self.assertTrue(minimerge.is_package_to_be_updated(py24))
        minimerge._do_action('install', [py24])
        self.assertTrue(minimerge.is_package_to_be_updated(py24))
        # new revision
        minimerge._action = 'install'
        minimerge._update = False
        content = open(py24.path).read()
        self.assertFalse(minimerge.is_package_to_be_updated(py24))
        fic = open(py24.path, 'w')
        fic.write(content+'\nrevision=668\n')
        fic.close()
        py24 = api.Minibuild(path=py24.path, minitage_config=minimerge._config)
        self.assertTrue(minimerge.is_package_to_be_updated(py24))
        # new revision is installed, no update
        minimerge._do_action('install', [py24])
        self.assertFalse(minimerge.is_package_to_be_updated(py24))

    def test105IsPackageToBeDeleted(self):
        """testIsPackageToBeDeleted"""
        package = self.package
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        if os.path.exists(py24p):
            shutil.rmtree(py24p)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        minimerge._action = None
        # package is not install, no delete
        self.assertFalse(minimerge.is_package_to_be_deleted(py24))
        minimerge._fetch(py24)
        self.assertFalse(minimerge.is_package_to_be_deleted(py24))
        minimerge._do_action('install', [py24])
        # action is not delete
        self.assertFalse(minimerge.is_package_to_be_deleted(py24))
        # package must be deleted
        minimerge._action = 'delete'
        self.assertTrue(minimerge.is_package_to_be_deleted(py24))
        minimerge._do_action('delete', [py24])
        # package is not installed no more, no delete
        self.assertFalse(minimerge.is_package_to_be_deleted(py24))

    def test106IsPackageToBeFetched(self):
        """testIsPackageToBeFetched"""
        package = self.package
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        if os.path.exists(py24p): shutil.rmtree(py24p)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        self.assertTrue(minimerge.is_package_src_to_be_fetched(py24))
        os.makedirs(py24p)
        # package is not installed and unrelated
        self.assertTrue(minimerge.is_package_src_to_be_fetched(py24))
        fic = open(os.path.join(py24p, 'foo'), 'w')
        fic.write('foo')
        fic.close()
        self.assertRaises(core.MinimergeError, minimerge.is_package_src_to_be_fetched, py24)
        #fic = open(os.path.join(py24p, 'buildout.cfg'), 'w')
        #fic.write()
        #fic.close()
        # package is incomplete
        #self.assertTrue(minimerge.is_package_src_to_be_fetched(py24))
        if os.path.exists(py24p): shutil.rmtree(py24p)
        minimerge._fetch(py24)
        minimerge._do_action('install', [py24])
        # user package is fetched / up to date
        self.assertFalse(minimerge.is_package_src_to_be_fetched(py24))
        # user needs update
        minimerge._update = True
        self.assertFalse(minimerge.is_package_src_to_be_fetched(py24))
        # package has new revision
        minimerge._update = False
        content = open(py24.path).read()
        fic = open(py24.path, 'w')
        fic.write(content+'\nrevision=670\n')
        fic.close()
        py24 = api.Minibuild(path=py24.path, minitage_config=minimerge._config)
        self.assertFalse(minimerge.is_package_src_to_be_fetched(py24))

    def test107IsPackageToBeSrcUpdated(self):
        """testIsPackageToBeSrcUpdated"""
        package = self.package
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        os.makedirs(py24p)
        # package is not installed
        self.assertTrue(minimerge.is_package_src_to_be_updated(py24))
        if os.path.exists(py24p): shutil.rmtree(py24p)
        minimerge._fetch(py24)
        minimerge._do_action('install', [py24])
        # user package is fetched / up to date
        self.assertFalse(minimerge.is_package_src_to_be_updated(py24))
        # user needs update
        minimerge._update = True
        self.assertTrue(minimerge.is_package_src_to_be_updated(py24))
        # package has new revision
        minimerge._update = False
        content = open(py24.path).read()
        fic = open(py24.path, 'w')
        fic.write(content+'\nrevision=766\n')
        fic.close()
        py24 = api.Minibuild(path=py24.path, minitage_config=minimerge._config)
        self.assertTrue(minimerge.is_package_src_to_be_updated(py24))

    def test108GetRevisionAndHasNewRevision(self):
        package = self.package
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        if os.path.exists(py24p): shutil.rmtree(py24p)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        minimerge._fetch(py24)
        minimerge._do_action('install', [py24])
        # first install version 1
        rev = minimerge.get_installed_revision(py24)
        self.assertEquals(rev, 766)
        self.assertFalse(minimerge.has_new_revision(py24))
        content = open(py24.path).read()
        fic = open(py24.path, 'w')
        fic.write(content)
        fic.write('\nrevision=800\n')
        fic.close()
        py24 = api.Minibuild(path=py24.path, minitage_config=minimerge._config)
        self.assertTrue(minimerge.has_new_revision(py24))
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        minimerge._fetch(py24)
        minimerge._do_action('install', [py24])
        rev = minimerge.get_installed_revision(py24)
        self.assertEquals(rev, 800)
        py24 = api.Minibuild(path=py24.path, minitage_config=minimerge._config)
        self.assertFalse(minimerge.has_new_revision(py24))

    def test109PackageMark(self):
        """testPackageMark"""
        package = self.package
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        if os.path.exists(py24p): shutil.rmtree(py24p)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        self.assertFalse(minimerge.get_package_mark(py24, 'fetched'))
        minimerge.set_package_mark(py24, 'fetched', 'iamatest')
        self.assertTrue(minimerge.is_package_marked(py24, 'fetched'))
        self.assertTrue(
            isinstance(
                minimerge.get_package_mark_as_file(py24, 'fetched'),
                file
            )
        )
        self.assertEquals(minimerge.get_package_mark(py24, 'fetched'), 'iamatest')

    def test110FetchPackageMark(self):
        """testFetchPackageMark"""
        package = self.package
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        py24p = minimerge.get_install_path(py24)
        if os.path.exists(py24p): shutil.rmtree(py24p)
        py24.src_uri = 'file://%s' % package
        py24.src_type = 'static'
        self.assertFalse(minimerge.get_package_mark(py24, 'fetch'))
        minimerge._fetch(py24)
        self.assertTrue(minimerge.get_package_mark(py24, 'fetch'))

    def test111IsInstalled(self):
       """testIsInstalled"""
       package = self.package
       path = D(self.path)
       minimerge = self.minimerge
       py24 = minimerge._find_minibuild('python-2.4')
       py24p = minimerge.get_install_path(py24)
       if os.path.exists(py24p): shutil.rmtree(py24p)
       mb = minimerge._find_minibuild('minibuild-0')
       py24.src_uri = 'file://%s' % package
       py24.src_type = 'static'
       self.assertFalse(minimerge.is_installed(py24))
       minimerge._fetch(py24)
       self.assertFalse(minimerge.is_installed(py24))
       minimerge._do_action('install', [py24])
       self.assertTrue(minimerge.is_installed(py24))
       # test reinstall
       minimerge._do_action('install', [py24])
       self.assertTrue(minimerge.is_installed(py24))

    def test112FindMinibuild(self):
        """testFindMinibuild"""
        # create minilays in the minilays dir, seeing if they get putted in
        minimerge = self.minimerge
        mb = minimerge._find_minibuild('minibuild-0')
        self.assertEquals('minibuild-0', mb.name)

    def test113ComputeDepsWithNoDeps(self):
        """testComputeDepsWithNoDeps
        m0 depends on nothing"""
        minimerge = self.minimerge
        computed_packages = minimerge._compute_dependencies(['minibuild-0'])
        mb = computed_packages[0]
        self.assertEquals('minibuild-0', mb.name)

    def test114SimpleDeps(self):
        """testSimpleDeps
        test m1 -> m0"""
        package = self.package
        path = D(self.path)
        minimerge = self.layer['minimerge']
        computed_packages = minimerge._compute_dependencies(['minibuild-1'])
        mb = computed_packages[0]
        self.assertEquals(mb.name, 'minibuild-0')
        mb = computed_packages[1]
        self.assertEquals(mb.name, 'minibuild-1')

    def test115ChainedandTreeDeps(self):
        """testChainedandTreeDeps
        Will test that this tree is safe:
              -       m3
                      /
                     m2
                     / \
                    m4 m1
                     \/
                     m0

               -   m9
                  / \
                 m0 m3
        """
        package = self.package
        path = D(self.path)
        minimerge = self.layer['minimerge']
        computed_packages = minimerge._compute_dependencies(['minibuild-3'])
        wanted_list = ['minibuild-0', 'minibuild-4',
                       'minibuild-1', 'minibuild-2', 'minibuild-3']
        self.assertEquals([mb.name for mb in computed_packages], wanted_list)
        computed_packages = minimerge._compute_dependencies(['minibuild-9'])
        wanted_list = ['minibuild-0', 'minibuild-4', 'minibuild-1',
                       'minibuild-2', 'minibuild-3', 'minibuild-9']
        self.assertEquals([mb.name for mb in computed_packages], wanted_list)

    def test117Recursivity(self):
        """testRecursivity
        check that:
             - m5  -> m6 -> m7
             - m8  -> m8
             - m10 -> m11 -> m12 -> m13 -> m10
        will throw some recursity problems.
        """
        package = self.package
        path = D(self.path)
        minimerge = self.minimerge
        self.assertRaises(core.CircurlarDependencyError,
                          minimerge._compute_dependencies, ['minibuild-6'])
        self.assertRaises(core.CircurlarDependencyError,
                          minimerge._compute_dependencies, ['minibuild-8'])
        self.assertRaises(core.CircurlarDependencyError,
                          minimerge._compute_dependencies, ['minibuild-13'])

    def test118MinibuildNotFound(self):
        """testMinibuildNotFound
        INOTINANYMINILAY does not exist"""
        package = self.package
        path = D(self.path)
        argv = [sys.argv[0], '--config',
                    '%s/etc/minimerge.cfg' % path, 'foo']
        minimerge = self.layer['minimerge']
        self.assertRaises(core.MinibuildNotFoundError,
                          minimerge._find_minibuild, 'INOTINANYMINILAY')

    def test119CutDeps(self):
        """testCutDeps"""
        package = self.package
        path = D(self.path)
        argv = [sys.argv[0], '--config',
                    '%s/etc/minimerge.cfg' % path,
                    '--jump', 'minibuild-2',
                    'minibuild-1', 'minibuild-2', 'minibuild-3']
        minimerge = self.fminimerge(argv)
        p =  minimerge._cut_jumped_packages(
            minimerge._find_minibuilds(
                ['minibuild-1', 'minibuild-2', 'minibuild-3']
            )
        )
        self.assertEquals(
            p,
            minimerge._find_minibuilds(['minibuild-2', 'minibuild-3'])
        )
        minimerge._jump = '666'
        q =  minimerge._cut_jumped_packages(
            minimerge._find_minibuilds(
                ['minibuild-1', 'minibuild-2', 'minibuild-3'])
        )
        self.assertEquals(
            q,
            minimerge._find_minibuilds(
                ['minibuild-1', 'minibuild-2', 'minibuild-3']
            )
        )


    @property
    def mb(self):
        return self.minimerge._find_minibuilds(['minibuild-0'])[0]

    def test120FetchOffline(self):
        """testFetchOffline"""
        minimerge = self.minimerge
        self.assertTrue(minimerge._offline)
        self.assertTrue(
            not os.path.exists(self.minimerge.get_install_path(self.mb)))
        minimerge._fetch(self.mb)
        self.assertTrue(
            os.path.exists(self.minimerge.get_install_path(self.mb)))

    def test121SelectPython(self):
        """testSelectPython.
        Goal of this test is to prevent uneccesary python versions
        to be built.
        """
        package = self.package
        path = D(self.path)
        minimerge = self.minimerge
        self.layer.sync()
        #self.assertTrue(minimerge._action, 'install')

        # we install a dependency which is not a egg
        # result is false, no eggs dict in return.
        computed_packages0, p0 = minimerge._select_pythons(
            minimerge._compute_dependencies(['minibuild-1000']))
        self.assertFalse(p0)

        # we install a dep that require meta-python
        # the dict must contains eggs 2.6
        # available python = 2.4/2.5/2.6
        self._packages = ['minibuild-1001']
        computed_packages1, p1 = minimerge._select_pythons(
            minimerge._compute_dependencies(['minibuild-1001']))
        for i in ['2.7']:
            self.assertTrue(i in p1['minibuild-1005'])
            self.assertTrue('python-%s' % i
                            in [c.name for c in computed_packages1]
                           )
        # we fake a python-2.4 installation
        os.makedirs(
            os.path.join(minimerge._prefix, 'dependencies', 'python-2.4')
        )

        # we install a dep that require meta-python
        # the dict must contains eggs 2.4 as there is
        # a python2.4 allready installed
        self._packages = ['minibuild-1001']
        computed_packages1, p1 = minimerge._select_pythons(
            minimerge._compute_dependencies(['minibuild-1001']))
        for i in ['2.4']:
            self.assertTrue(i in p1['minibuild-1005'])
            self.assertTrue('python-%s' % i
                            in [c.name for c in computed_packages1]
                           )

        # we install a dep that require python-2.4 but depends
        # on a python egg 'minibuild-1005'
        # the dict must contains eggs part againts 2.4
        # available python = 2.4
        deps = minimerge._compute_dependencies(['minibuild-1002'])
        self._packages = ['minibuild-1002']
        computed_packages2, p2 = minimerge._select_pythons(deps)
        self.assertTrue('python-2.4'
                        in [c.name for c in computed_packages2]
                       )
        self.assertTrue('python-2.5'
                        not in [c.name for c in computed_packages2]
                       )

    def test123ActionDelete(self):
        """testActionDelete."""
        package = self.package
        path = D(self.path)
        minimerge = self.minimerge
        py24 = minimerge._find_minibuild('python-2.4')
        minimerge.set_package_mark(py24, 'install')
        self.assertTrue(os.path.isdir(minimerge.get_install_path(py24)))
        minimerge._do_action('delete', [py24])
        self.assertTrue(not os.path.isdir(minimerge.get_install_path(py24)))

    def test124InvalidAction(self):
        package = self.package
        minimerge = self.minimerge
        py = minimerge._find_minibuild('python-2.4')
        self.assertRaises(
            core.ActionError, minimerge._do_action,
            'invalid', [py]
        )

    def test001Sync(self):
        """testSync."""
        path = D(self.path)
        minimerge = self.minimerge
        os.system("cd %s;hg up -r 0" % self.minilay)
        self.assertFalse(os.path.isfile('%s/%s' % (self.minilay, 'minibuild-1000')))
        minimerge._sync()
        self.assertTrue(
            os.path.isdir(
                '%s/minilays/%s' %
                (path, 'dependencies')
            )
        )
        self.assertTrue(os.path.isfile('%s/%s' % (self.minilay, 'minibuild-1000')))

    def test126FetchOnline(self):
        """testFetchOnline"""
        minimerge = self.minimerge
        minimerge._offline = False
        self.assertFalse(minimerge._offline)
        mb = minimerge._find_minibuild('minibuild-0')
        self.assertFalse(os.path.exists(
            '%s/eggs/minibuild-0/buildout.cfg' % LAYER['p']))
        minimerge._fetch(mb)
        self.assertTrue(os.path.exists(
            '%s/eggs/minibuild-0/buildout.cfg' % LAYER['p']))
        minimerge._offline = True

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMinimerge))
    return suite

