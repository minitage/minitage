# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import unittest
import os
import tempfile
from cStringIO import StringIO

from minitage.core.core import newline
from minitage.core.testing import LAYER


def write(file, content):
    fic = open(file, 'w')
    fic.write(content)
    fic.flush()
    fic.close()

class testNewLine(unittest.TestCase):
    """testNewLine"""
    layer = LAYER

    def setUp(self):
        """."""
        self.file = tempfile.mkstemp()[1]

    def tearDown(self):
        """."""
        if os.path.exists(self.file):
            os.unlink(self.file)

    def testNewLine(self):
        """testNewLine"""
        write(self.file,
"""
tata
test
"""
        )
        newline(self.file)
        self.assertEquals(
            '\ntata\ntest\n\n',
            open(self.file).read()
        )
        write(self.file,
"""
tata
test"""
        )
        newline(self.file)
        self.assertEquals(
            '\ntata\ntest\n\n',
            open(self.file).read()
        )


    def testEmptyFile(self):
        """testEmptyFile"""
        write(self.file,
              """"""
        )
        newline(self.file)
        self.assertEquals(
            '\n',
            open(self.file).read()
        )

    def testUtf8(self):
        """tUtf8"""
        write(self.file,
              """çà@~#ø€ç±ø"""
        )
        newline(self.file)
        self.assertEquals(
            '\xc3\xa7\xc3\xa0@~#\xc3\xb8\xe2\x82\xac\xc3\xa7\xc2\xb1\xc3\xb8\n\n',
            open(self.file).read()
        )

    def multipleLines(self):
        """multipleLines"""
        write(self.file,
"""
tata
test




"""
        )
        newline(self.file)
        self.assertEquals(
            '\ntata\ntest\n\n',
            open(self.file).read()
        )



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testNewLine))
    return suite

