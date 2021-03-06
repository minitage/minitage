Test of minitage Git fetcher
=================================

::

    >>> globals().update(layer['globs'])

This fetcher can fetch something over git.

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

    >>> git = scmm.GitFetcher()

Make a file available for download::

    >>> dest = os.path.join(p, 'git/d')
    >>> path = os.path.join(p, 'git/p')
    >>> path2 = os.path.join(p, 'git/p2')
    >>> path3 = os.path.join(p, 'git/p3')
    >>> wc = os.path.join(p, 'git/wc')
    >>> gituri = 'file://%s' % path2
    >>> gituri2= 'file://%s' % path3
    >>> opts = {'path': path, 'dest': dest, 'wc': wc}
    >>> opts.update({'path2': path2})
    >>> noecho = os.system("""
    ...          mkdir -p %(path2)s
    ...          rm -rf %(path)s
    ...          cd %(path2)s
    ...          echo '666'>file
    ...          git init
    ...          git add .
    ...          git commit -a -m 'initial import'
    ...          echo '666'>file2
    ...          git add .
    ...          git commit -m 'second revision'
    ...          git clone %(path2)s %(path)s
    ...          """ % opts)
    >>> noecho = copy_tree(path2, path3)

Checking our working copy is up and running
Fine.
Beginning simple, checkouting the code somewhere::

    >>> git.fetch(wc, gituri)
    >>> ls(wc)
    .git
    file
    file2
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm INFO
      Checkouted .../wc / .../p2 (HEAD) [git].
    >>> sh('cd %s&&git show|head -5|tail -n1'%wc)
    cd ...&&git show|head -5|tail -n1
        second revision
    <BLANKLINE>


Calling fetch on an already fetched clone.::

    >>> touch(os.path.join(wc, 'foo'))
    >>> git.fetch(wc, gituri)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm WARNING
      Destination .../wc already exists and is not empty, moving it away in ...wc/wc.old... for further user examination
    minitage.fetchers.scm WARNING
      Checkout directory is not the same as the destination, copying content to it. This may happen when you say to download to somwhere where it exists files before doing the checkout
    minitage.fetchers.scm INFO
      Checkouted .../wc / file:///.../p2 (HEAD) [git].
    >>> oldp =  [os.path.join(wc, f) for f in os.listdir(wc) if f != '.git' and os.path.isdir(os.path.join(wc, f))][0]
    >>> oldp, ls(oldp)
    .git
    file
    file2
    foo
    ('...wc/wc.old...', None)


Calling fetch from another repository::

    >>> git.fetch(wc, gituri2)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm WARNING
      Destination .../wc already exists and is not empty, moving it away in ...wc/wc.old... for further user examination
    minitage.fetchers.scm WARNING
      Checkout directory is not the same as the destination, copying content to it. This may happen when you say to download to somwhere where it exists files before doing the checkout
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p3 (HEAD) [git].

Going into past, revision 1::

    >>> commits = [a.replace('commit ', '') for a  in subprocess.Popen(['cd %s;git log'%wc], shell=True, stdout=subprocess.PIPE).stdout.read().splitlines() if 'commit' in a]
    >>> git.get_uri(wc)
    'file://.../p3'
    >>> git._has_uri_changed(wc, gituri2)
    False
    >>> git._has_uri_changed(wc, gituri)
    True
    >>> git.update(wc, gituri2, {"revision": commits[1]})
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p3
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p3 (...) [git].
    >>> sh('cd %s&&git show|head -5|tail -n1'%wc)
    cd .../wc&&git show|head -5|tail -n1
        initial import
    <BLANKLINE>

Going head, update without arguments sticks to HEAD::

    >>> git.update(wc, gituri2)
    >>> print log_handler; log_handler.clear() # doctest: +REPORT_NDIFF
    minitage.fetchers.scm DEBUG
      Updating .../wc / .../p3
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p3 (HEAD) [git].
    >>> sh('cd %s&&git show|head -5|tail -n1'%wc)
    cd .../wc&&git show|head -5|tail -n1
        second revision
    <BLANKLINE>


Cleaning

    >>> shutil.rmtree(wc)

Test the fech or update method which clones or update a working copy::

    >>> git.fetch_or_update(wc, gituri, {"revision": commits[1]})
    >>> sh('cd %s&&git show|head -5|tail -n1'%wc)
    cd .../wc&&git show|head -5|tail -n1
        initial import
    <BLANKLINE>
    >>> git.fetch_or_update(wc, gituri)
    >>> git.get_uri(wc)
    'file:///.../p2'
    >>> sh('cd %s&&git show|head -5|tail -n1'%wc)
    cd .../wc&&git show|head -5|tail -n1
        second revision
    <BLANKLINE>
    >>> log_handler.clear()


Problem in older version, trailing slash cause API to have troubles::

    >>> shutil.rmtree(wc)
    >>> git.fetch_or_update(wc, '%s/' % gituri)
    >>> log_handler.clear()
    >>> git.fetch_or_update(wc, '%s/' % gituri)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p2/
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p2/ (HEAD) [git].

Other problem; update on an empty directory may fail on older version of this code::

    >>> shutil.rmtree(wc); mkdir(wc)
    >>> git.update(wc, gituri)
    >>> print log_handler; log_handler.clear()
    minitage.fetchers.scm DEBUG
      Updating .../wc / file://.../p2
    minitage.fetchers.scm WARNING
      The working copy seems not to be a git repository. Getting a new working copy.
    minitage.fetchers.scm INFO
      Checkouted .../wc / file://.../p2 (HEAD) [git].
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm DEBUG
      Running git config --get remote.origin.url in .../wc
    minitage.fetchers.scm INFO
      Updated .../wc / file://.../p2 (HEAD) [git].

.. vim: set ft=doctest :

