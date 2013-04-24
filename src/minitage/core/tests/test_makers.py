__docformat__ = 'restructuredtext en'

import unittest
from minitage.core.tests.makers import (
    test_interfaces,
    test_buildout,
)


def test_suite():
    suite = unittest.TestSuite()
    for m in (test_interfaces,
              test_buildout,
             ):
        suite.addTest(m.test_suite())
    return suite

