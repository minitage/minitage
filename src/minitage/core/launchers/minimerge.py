#!/usr/bin/env python
__docformat__ = 'restructuredtext en'

import sys

from minitage.core.cli import get_minimerge
import traceback

def launch():
    debug = False
    try:
        minimerge = get_minimerge(read_options=True)
        debug = minimerge._debug
        minimerge.main()
        debug = minimerge._debug
    except Exception, e:
        trace = traceback.format_exc()
        sys.stderr.write('Minimerge executation failed:\n')
        if debug:
            sys.stderr.write('\t%s\n' % trace)
        else:
            sys.stderr.write('\t%s\n' % e)
        sys.exit(-1)
# vim:set ft=python sts=4 ts=4 tw=80 et:
