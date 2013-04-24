import pkg_resources
import re

re_flags = re.U | re.M | re.S | re.X

rdevsub = re.compile('\.dev.*$').sub
devsub = lambda x:rdevsub('', x)

__docformat__ = 'restructuredtext en'
__version__ = pkg_resources.require(
    'minitage')[0].version
version = devsub(__version__)
# vim:set et sts=4 ts=4 tw=80:
