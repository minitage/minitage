
Test of minitage Bazaar fetcher
====================================

This fetcher can fetch something over mercurial.

::

    >>> globals().update(layer['globs'])


Initial imports::

    >>> lang, lcall = os.environ.get('LANG', ''), os.environ.get('LC_ALL', '')
    >>> os.environ['LANG'], os.environ['LC_ALL'] = 'C', 'C'
    >>> from minitage.core.fetchers import interfaces
    >>> from minitage.core.common import md5sum
    >>> from minitage.core.fetchers import scm as scmm
    >>> n = scmm.__logger__

Install some magic to get the fetcher logs

    >>> from zope.testing.loggingsupport import InstalledHandler
    >>> log_handler = InstalledHandler(n)

Instantiate our fetcher::

    >>> bzr = scmm.BzrFetcher()

Make a file available for download::

    >>> dest = os.path.join(p, 'bzr§d')
    >>> path = os.path.join(p, 'bzr§p')
    >>> path1 = os.path.join(p, 'bzr/p1')
    >>> path2 = os.path.join(p, 'bzr/p2')
    >>> path3 = os.path.join(p, 'bzr/p3')
    >>> wc = os.path.join(p, 'bzr/wc')
    >>> bzruri = 'file://%s' % path2
    >>> bzruri2= 'file://%s' % path3
    >>> opts = {'path': path, 'dest': dest, 'wc': wc}
    >>> opts.update({'path2': path2})
    >>> noecho = os.system("""
    ...          mkdir -p  %(path2)s
    ...          cd %(path2)s
    ...          echo '666'>file
    ...          bzr init
    ...          bzr add .
    ...          bzr ci -m 'initial import'
    ...          echo '666'>file2
    ...          bzr add
    ...          bzr ci -m 'second revision'
    ...          """ % opts)
    >>> noecho = copy_tree(path2, path3)

Checking our working copy is up and running
Fine.
Beginning simple, checkouting the code somewhere:
::

    >>> bzr.fetch(wc, bzruri)
    >>> ls(wc)
    .bzr
    file
    file2
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p2 (last:1) [bazaar].
    >>> sh('cd %s&&bzr version-info'%wc)
    cd .../wc&&bzr version-info...
    revno: 2
    branch-nick: p2
    <BLANKLINE>


Calling fetch on an already fetched clone.
::

    >>> touch(os.path.join(wc, 'foo'))
    >>> bzr.fetch(wc, bzruri)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm WARNING
      Destination .../wc already exists and is not empty, moving it away in .../wc/wc.old... for further user examination
    minitage.fetchers.scm WARNING
      Checkout directory is not the same as the destination, copying content to it. This may happen when you say to download to somwhere where it exists files before doing the checkout
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p2 (last:1) [bazaar].
    >>> oldp =  [os.path.join(wc, f) for f in os.listdir(wc) if f != '.bzr' and os.path.isdir(os.path.join(wc, f))][0]
    >>> oldp, ls(oldp)
    .bzr
    file
    file2
    foo
    ('...wc/wc.old...', None)


Calling fetch from another repository
::

    >>> bzr.fetch(wc, bzruri2)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm WARNING
      Destination .../wc already exists and is not empty, moving it away in .../wc/wc.old... for further user examination
    minitage.fetchers.scm WARNING
      Checkout directory is not the same as the destination, copying content to it. This may happen when you say to download to somwhere where it exists files before doing the checkout
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p3 (last:1) [bazaar].


Going into past, revision 1
::

    >>> bzr.get_uri(wc)
    '.../p3'
    >>> bzr._has_uri_changed(wc, bzruri2)
    False
    >>> bzr._has_uri_changed(wc, bzruri)
    True
    >>> log_handler.clear()
    >>> bzr.update(wc, bzruri2, {"revision": 1})
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p3
    minitage.fetchers.scm DEBUG
      Running bzr  info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3 in .../wc
    minitage.fetchers.scm DEBUG
      Running bzr  info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3 in .../wc
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p3 (1) [bazaar].
    >>> sh('cd %s&&bzr version-info'%wc)
    cd .../wc&&bzr version-info...
    revno: 1
    branch-nick: p3
    <BLANKLINE>

Going head, update without arguments sticks to HEAD
::

    >>> bzr.update(wc, bzruri2)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p3
    minitage.fetchers.scm DEBUG
      Running bzr  info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3 in .../wc
    minitage.fetchers.scm DEBUG
      Running bzr  info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3 in .../wc
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p3 (last:1) [bazaar].
    >>> sh('cd %s&&bzr version-info'%wc)
    cd .../wc&&bzr version-info...
    revno: 2
    branch-nick: p3
    <BLANKLINE>


Cleaning::

    >>> shutil.rmtree(wc)

Test the fech or update method which clones or update a working copy::

    >>> bzr.fetch_or_update(wc, bzruri, {"revision": '1'})
    >>> sh('cd %s&&bzr version-info'%wc)
    cd .../wc&&bzr version-info...
    revno: 1
    branch-nick: p2
    <BLANKLINE>
    >>> bzr.fetch_or_update(wc, bzruri)
    >>> sh('cd %s&&bzr version-info'%wc)
    cd .../wc&&bzr version-info...
    revno: 2
    branch-nick: p2
    <BLANKLINE>
    >>> log_handler.clear()


Problem in older version, trailing slash cause API to have troubles::

    >>> shutil.rmtree(wc)
    >>> bzr.fetch_or_update(wc, '%s/' % bzruri)
    >>> log_handler.clear()
    >>> bzr.fetch_or_update(wc, '%s/' % bzruri)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p2/
    minitage.fetchers.scm DEBUG
      Running bzr  info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3 in .../wc
    minitage.fetchers.scm DEBUG
      Running bzr  info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3 in .../wc
    minitage.fetchers.scm WARNING
      It seems that the url given do not need the trailing slash (.../p2/). You would have better not to keep trailing slash in your urls if you don't have to.
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p2/ (last:1) [bazaar].

Other problem; update on an empty directory may fail on older version of this code::

    >>> shutil.rmtree(wc); mkdir(wc)
    >>> bzr.update(wc, bzruri)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p2
    minitage.fetchers.scm WARNING
      The working copy seems not to be a bazaar repository. Getting a new working copy.
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p2 (last:1) [bazaar].
    minitage.fetchers.scm DEBUG
      Running bzr  info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3 in .../wc
    minitage.fetchers.scm DEBUG
      Running bzr  info 2>&1|egrep "(checkout of branch|parent branch)"|cut -d:  -f 2,3 in .../wc
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p2 (last:1) [bazaar].

.. vim: set ft=doctest :

