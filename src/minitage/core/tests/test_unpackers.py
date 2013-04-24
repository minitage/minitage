__docformat__ = 'restructuredtext en'

import unittest
from minitage.core.tests.unpackers import (
    test_interfaces,
    test_tar,
    test_zip,
)


def test_suite():
    suite = unittest.TestSuite()
    for m in (test_interfaces,
              test_tar,
              test_zip,
             ):
        suite.addTest(m.test_suite())
    return suite

# vim:set et sts=4 ts=4 tw=80:
