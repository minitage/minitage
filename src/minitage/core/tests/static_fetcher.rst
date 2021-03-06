Test of minitage Static fetcher
=================================

::

    >>> globals().update(layer['globs'])

This fetcher can fetch something over urllib and manage some md5 mecanism to avoid useless redownload
All you need to do is to have something like that::

    http://foo.file
    http://foo.file.md5

Where file.md5 contains only the md5.

Initial imports::

    >>> from minitage.core.fetchers import interfaces
    >>> from minitage.core.common import md5sum
    >>> from minitage.core.fetchers import static as staticm
    >>> n = 'minitage.static.fetcher'

Install some magic to get the fetcher logs::

    >>> from zope.testing.loggingsupport import InstalledHandler
    >>> log_handler = InstalledHandler(n)

Instantiate our fetcher::

    >>> static = staticm.StaticFetcher()

Make a file available for download::

    >>> testfile = os.path.join(p, 'testfile')
    >>> touch(testfile, **{'data': 'data'})
    >>> md51 = '8d777f385d3dfec8815d20f7496026dc'
    >>> touch("%s.md5" % testfile, **{'data': md51})
    >>> cat (testfile)
    data

Download it::

    >>> d = os.path.join(p, 'result')
    >>> p1 = os.path.join(p, 'result/p1')
    >>> p2 = os.path.join(p, 'result/p2')
    >>> p3 = os.path.join(p, 'result/p3')
    >>> wc = os.path.join(p, 'result/wc')
    >>> static.fetch(d, 'file://%s' % testfile)
    >>> print log_handler; log_handler.clear()
    minitage.static.fetcher ...
        Downloading ...testfile from file:///.../testfile.

The file is present in the destination directory, in the download cache and
a md5 has been generated::

    >>> cat(d, 'testfile')
    data
    >>> cat(d, '.download', 'testfile')
    data
    >>> md51 in open(os.path.join(d, '.download', 'testfile.md5')).read()
    True

Try to reownload it::

    >>> static.fetch(d, 'file://%s' % testfile)
    >>> print log_handler; log_handler.clear()
    minitage.static.fetcher WARNING
      File /.../result/.download/testfile is already downloaded
    minitage.static.fetcher DEBUG
      MD5 has not changed, download is aborted.

The file is present in the destination directory, in the download cache and
a md5 has been generated::

    >>> cat(d, 'testfile')
    data
    >>> cat(d, '.download', 'testfile')
    data
    >>> md51 in open(os.path.join(d, '.download', 'testfile.md5')).read()
    True

Change the file and redownload it::

    >>> touch(testfile, **{'data': 'titi'})
    >>> md51 = '5d933eef19aee7da192608de61b6c23d'
    >>> touch("%s.md5" % testfile, **{'data': md51})
    >>> cat (testfile)
    titi
    >>> static.fetch(d, 'file://%s' % testfile)
    >>> print log_handler; log_handler.clear()
    minitage.static.fetcher ...
       File .../testfile is already downloaded
     minitage.static.fetcher ...
       Its md5 has changed: 8d777f385d3dfec8815d20f7496026dc != 5d933eef19aee7da192608de61b6c23d, redownloading
     minitage.static.fetcher ...
       Downloading ...testfile from file://.../testfile.

The file is present in the destination directory, in the download cache and
a md5 has been generated::

    >>> cat(d, 'testfile')
    titi
    >>> cat(d, '.download', 'testfile')
    titi
    >>> md51 in open(os.path.join(d, '.download', 'testfile.md5')).read()
    True

Test mecanism with a file without associated md5::

    >>> testfile2 = os.path.join(p, 'testfile2')
    >>> touch(testfile2, **{'data': 'titi'})
    >>> cat (testfile2)
    titi
    >>> static.fetch(d, 'file://%s' % testfile2)
    >>> print log_handler; log_handler.clear()
    minitage.static.fetcher ...
        Downloading ...testfile2 from file:///.../testfile2.
    >>> static.fetch(d, 'file://%s' % testfile2)
    >>> print log_handler; log_handler.clear()
    minitage.static.fetcher INFO
      MD5 not found at file://.../testfile2.md5, integrity will not be checked.
    minitage.static.fetcher INFO
      Downloading .../result/.download/testfile2 from file://.../testfile2.

Test that the unpack mecanism just ovverides what's already there but not delete anything::

    - Make a tarbball ::

        >>> td = os.path.join(p, 'testdir')
        >>> md5p = os.path.join(p, 'test.tbz2.md5')
        >>> package = os.path.join(p, 'test.tbz2')
        >>> mkdir(td)
        >>> touch(os.path.join(td, 'file1'), **{'data': 'toto'})
        >>> touch(os.path.join(td, 'file2'), **{'data': 'tata'})
        >>> sh('cd %s;tar cjpvf ../test.tbz2 .;cd ..'%td)
        cd /tmp/...;tar cjpvf ../test.tbz2 .;cd ..
        ./
        ...
        <BLANKLINE>
        >>> md5 = md5sum(package)
        >>> touch(md5p, **{'data': md5})

    - Try the classical download and redownload dance::

        >>> static.fetch(d, 'file://%s' % package)
        >>> print log_handler; log_handler.clear()
        minitage.static.fetcher ...
          Downloading .../result/.download/test.tbz2 from file:///.../test.tbz2.
        >>> static.fetch(d, 'file://%s' % package)
        >>> print log_handler; log_handler.clear()
        minitage.static.fetcher WARNING
          File .../.download/test.tbz2 is already downloaded
        minitage.static.fetcher DEBUG
          MD5 has not changed, download is aborted.

    - Observe what's there::

        >>> ls(p, 'result')
        .download
        file1
        file2
        testfile
        testfile2

    - As we can see, the previous files have not been wiped out, good :).

    - Now change the archive content and see if our changes are there::

        >>> touch(os.path.join(td, 'file1'), **{'data': 'tutu'})
        >>> touch(os.path.join(td, 'file2'), **{'data': 'titi'})
        >>> sh('cd %s;tar cjpvf ../test.tbz2 .;cd ..'%td)
        cd /tmp/...;tar cjpvf ../test.tbz2 .;cd ..
        ./
        ...
        <BLANKLINE>
        >>> md5 = md5sum(package)
        >>> touch(md5p, **{'data': md5})
        >>> static.fetch(d, 'file://%s' % package)
        >>> cat(d, 'file2')
        titi
        >>> cat(d, 'file1')
        tutu

.. vim: set ft=doctest :
