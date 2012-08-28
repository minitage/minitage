# Copyright (C) 2009, Mathieu PASQUET <kiorky@cryptelium.net>
# All rights reserved.

import os
import sys
from setuptools import setup, find_packages

name = 'minitage.core'
version = '2.0.36'
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
        read('README.txt')
        + '\n' +
        read('INSTALL.txt')
        + '\n' +
        read('CHANGES.txt')
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
    namespace_packages = [ 'minitage', name, ],
    install_requires = ['iniparse', 'zc.buildout', 'minitage.paste >= 1.3.1850', 'ordereddict', 'setuptools'],
    zip_safe = False,
    include_package_data = True,
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    extras_require={'test': ['IPython', 'zope.testing', 'mocker', 'httplib2']},
    data_files = [
        ('etc', ['src/etc/minimerge.cfg']),
        ('minilays', []),
        ('share/minitage', ['README.txt', 'INSTALL.txt', 'CHANGES.txt']),
    ],
    entry_points = {
        'console_scripts': [
            'minimerge = minitage.core.launchers.minimerge:launch',
            'minitagify = minitage.core.minitagize:main',
        ],
    }

)


