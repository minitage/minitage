# Copyright (C) 2009, Mathieu PASQUET <kiorky@cryptelium.net>
# All rights reserved.

import os
import sys
from setuptools import setup, find_packages

name = 'minitage'
version = '2.0.67'
def read(rnames):
    setupdir =  os.path.dirname( os.path.abspath(__file__))
    return open(
        os.path.join(setupdir, rnames)
    ).read()

setup(
    name = name,
    version = version,
    description="A meta package-manager to deploy projects on UNIX Systemes sponsored by Makina Corpus.",
    long_description = (
        read('README.rst')
        + '\n' +
        read('INSTALL.rst')
        + '\n' +
        read('CHANGES.rst')
        + '\n'
    ),
    classifiers=[
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    #keywords = 'development buildout',
    author = 'Mathieu Le Marec - Pasquet',
    author_email = 'kiorky@cryptelium.net',
    url = 'http://cheeseshop.python.org/pypi/%s' % name,
    license = 'BSD',
    namespace_packages = [ 'minitage', 'minitage.core', ],
    install_requires = ['iniparse', 
                        'setuptools',
                        'minitage.paste >= 1.4.6',
#                        'minitage.core >= 2.0.57',
                        'ordereddict', 'setuptools'],
    zip_safe = False,
    include_package_data = True,
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    extras_require={'test': ['plone.testing', 
                             'mocker', 
                             'httplib2', 
                             'minitage.recipe.scripts',
                             'minitage.recipe.egg',
                             'minitage.recipe.common',
                             ]},
    data_files = [
        ('etc', ['src/etc/minimerge.cfg']),
        ('minilays', []),
        ('share/minitage', ['README.rst', 'INSTALL.rst', 'CHANGES.rst']),
    ],
    entry_points = {
        'console_scripts': [
            'minimerge = minitage.core.launchers.minimerge:launch',
            'minitagify = minitage.core.launchers.minitagize:main',
        ],
    }

)

