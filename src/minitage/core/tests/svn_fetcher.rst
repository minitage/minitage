
Test of minitage Subversion fetcher
========================================

This fetcher can fetch something over subversion.

::

    >>> globals().update(layer['globs'])

Initial imports::

    >>> lang, lcall = os.environ.get('LANG', ''), os.environ.get('LC_ALL', '')
    >>> os.environ['LANG'], os.environ['LC_ALL'] = 'C', 'C'
    >>> from minitage.core.fetchers import interfaces
    >>> from minitage.core.common import md5sum
    >>> from minitage.core.fetchers import scm as scmm
    >>> n = scmm.__logger__

Install some magic to get the fetcher logs::

    >>> from zope.testing.loggingsupport import InstalledHandler
    >>> log_handler = InstalledHandler(n)

Instantiate our fetcher::

    >>> svn = scmm.SvnFetcher()

Make a file available for download::

    >>> dest = os.path.join(p, 'svn/d')
    >>> path = os.path.join(p, 'svn/p')
    >>> wc = os.path.join(p, 'wc')
    >>> svnuri = 'file://%s' % path
    >>> opts = {'path': path, 'dest': dest, 'wc': wc}
    >>> noecho = os.system("""
    ...          mkdir -p  %(path)s                  2>&1 >> /dev/null
    ...          cd %(path)s                         2>&1 >> /dev/null
    ...          svnadmin create .                   2>&1 >> /dev/null
    ...          mkdir -p  %(dest)s                  2>&1 >> /dev/null
    ...          svn co file://%(path)s %(dest)s     2>&1 >> /dev/null
    ...          cd %(dest)s                         2>&1 >> /dev/null
    ...          echo '666'>file                     2>&1 >> /dev/null
    ...          svn add file                        2>&1 >> /dev/null
    ...          svn ci -m 'initial import'          2>&1 >> /dev/null
    ...          cho '666'>file2                     2>&1 >> /dev/null
    ...          svn add file2                       2>&1 >> /dev/null
    ...          svn ci -m 'second revision'         2>&1 >> /dev/null
    ...          svn up                              2>&1 >> /dev/null
    ...          """ % opts)



 Checking our working copy is up and running::

    >>> sh('svn info %s' % opts['dest'])
    svn info .../d
    Path: .../d...
    URL: file:///.../p...

Fine.
Beginning simple, checkouting the code somewhere::

    >>> svn.fetch(wc, svnuri)
    >>> ls(wc)
    .svn
    file
    file2
    >>> sh('svn info %s|grep Revision' % wc)
    svn info /tmp/.../wc|grep Revision
    Revision: 2
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p (HEAD) [subversion].

Going into past, revision 1::

    >>> svn.update(wc, svnuri, {"revision": 1})
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p (1) [subversion].
    >>> sh('svn info %s|grep Revision' % wc)
    svn info /tmp/.../wc|grep Revision
    Revision: 1

Going head, update without arguments sticks to HEAD::

    >>> svn.update(wc, svnuri)
    >>> sh('svn info %s|grep Revision' % wc)
    svn info /tmp/.../wc|grep Revision
    Revision: 2
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p (HEAD) [subversion].

Cleaning::

    >>> shutil.rmtree(wc)

Test the fech or update method which clones or update a working copy::

    >>> svn.fetch_or_update(wc, svnuri, {"revision": 1})
    >>> sh('svn info %s|grep Revision' % wc)
    svn info /tmp/.../wc|grep Revision
    Revision: 1
    >>> svn.fetch_or_update(wc, svnuri)
    >>> svn.get_uri(wc)
    'file:///.../p'
    >>> sh('svn info %s|grep Revision' % wc)
    svn info /tmp/.../wc|grep Revision
    Revision: 2
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p (1) [subversion].
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p (HEAD) [subversion].

Problem in older version, trailing slash cause API to have troubles::

    >>> shutil.rmtree(wc)
    >>> svn.fetch_or_update(wc, '%s/' % svnuri)
    >>> log_handler.clear()
    >>> svn.fetch_or_update(wc, '%s/' % svnuri)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p/
    minitage.fetchers.scm WARNING
      It seems that the url given do not need the trailing slash (file://.../p/). You would have better not to keep trailing slash in your urls if you don't have to.
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p/ (HEAD) [subversion].


Other problem; update on an empty directory may fail on older version of this code::

    >>> shutil.rmtree(wc); mkdir(wc)
    >>> svn.update(wc, svnuri)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p
    minitage.fetchers.scm WARNING
      The working copy seems not to be a subversion repository. Getting a new working copy.
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p (HEAD) [subversion].
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p (HEAD) [subversion].

.. vim: set ft=doctest :

