#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import unittest2 as unittest
import sys

from minitage.core import cli, api
from minitage.core.testing import LAYER


class TestCase(unittest.TestCase):

    layer = LAYER

    @property
    def minimerge(self):
        return self.layer['minimerge']

    def fminimerge(self, opts):
        sys.argv = opts
        opts = cli.do_read_options(read_options=True)
        minimerge = api.Minimerge(opts)
        return minimerge

# vim:set et sts=4 ts=4 tw=80:
