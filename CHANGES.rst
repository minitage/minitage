Changelog for minitage.core
===============================


2.0.56 (unreleased)
-------------------

- Nothing changed yet.


2.0.55 (2013-04-01)
-------------------

- Nothing changed yet.


2.0.54 (2013-04-01)
-------------------

- test layer bugfix


2.0.53 (2013-04-01)
-------------------
- Documentation


2.0.51 (2013-04-01)
-------------------

- minitage.core is not tied to sys.prefix, 
  IOW you can install it in any location, 
  and the config file will be resolved relative 
  to the minimerge script.
- QA release, now you have test statuses on travis ci.
- tests are now based on plone.testing


2.0.50 (2013-03-28)
-------------------

- Better offline bootstrap assumptions
- minitagify script installs now minilay with a symlink
- better buildout maker (offline mode)
- returns a correct exit code (before we intentionnaly hide an error)


2.0.49 (2013-03-28)
-------------------

- offline mode, enhanced


2.0.48 (2013-03-25)
-------------------

- Better minitagify template (travis, qa)


2.0.47 (2013-03-23)
-------------------

- Better minitagify script


2.0.46 (2013-03-16)
-------------------

- try to detect buildout infra < 1 & run a buildout1 boostrap in case


2.0.45 (2013-02-13)
-------------------

- buildout 2.0 second round


2.0.44 (2013-02-13)
-------------------

- buildout 2.0 first pass


2.0.43 (2012-09-12)
-------------------

- better update support


2.0.42 (2012-09-12)
-------------------

- trigger pil rebuild


2.0.41 (2012-09-11)
-------------------

- Fix pil version


2.0.40 (2012-08-28)
-------------------

- Fix minitage base buildouts


2.0.39 (2012-08-28)
-------------------

- doc


2.0.37 (2012-08-28)
-------------------

- doc


2.0.36 (2012-08-28)
-------------------

- Fix minitage base buildouts


2.0.35 (2012-08-28)
-------------------

- fix category minibuild in minitagify


2.0.34 (2012-08-28)
-------------------

- Added the minitagify command see: `this doc <http://www.minitage.org/usecases/maintain_project.html#minitagify-an-existing-project>`_


2.0.33 (2012-05-09)
-------------------

- revert Download helper subdir patch and handle it in buildout recipes



2.0.32 (2012-05-06)
-------------------

- Fix all tests
- Dowload helper now downloads in downloadcache/netloc+urlpath/filename


2.0.31 (2012-03-26)
-------------------

- py27 deepcopy bugfix


2.0.30 (2012-03-24)
-------------------

- support py27
- Force run buildout in upgrade mode for dependencies and eggs packages


2.0.29 (2012-03-05)
-------------------

- handle pil migration


2.0.28 (2012-01-23)
-------------------

- Support for in place git branches [kiorky]

2.0.27 (2011-02-25)
-------------------
- proper release


2.0.24
---------------------------

    - fix bug in pretend
    - move to github
    - add mercurial to dependencies to facillitate buildout integration
    - add python versions for pretend and 'eggs' packages 
    - rebuild 'eggs' packages only if they need to be (markers are now in place for the particular python version)
    - remove useless mercurial dep

2.0
-----

FEATURES;

    - Auto Update system.
      When minimerge upgrade (easy_install -U), we have now the infrastructure to run update callbacks.
    - Now minibuilds have revisions, this can facilitate their reinstallation as reverse dependencies
    - give means to select the python to build against for python modules (--all-python-versions or specify python to use along with the package (minimerge -pv foo python-2.4)
    - force eggs category reinstallation
    - add an only dependencies switch to buld only dependencies
    - win32 compatibility (first rush, alpha quality)
    - add replace/per/os/dependencies mecanism in minibuilds
    - allow minibuild names with only major as version

BUGS:

    - support symlink in remove_path (API)
    - enhance remove_path function
    - fix a bug in bootstrapping buildout
    - rewrite fetchers
    - improve proxy handling
    - fix some tests
    - make parts shut up
    - test incomplete downloads and redownload them (package level)
    - make minibuild name more permissive
    - fix bug in new checkouts
    - fix a bug insde the get_from_cache helper when a fragmented url is used and the upstream server does not understand them
    - add a special exception for search_latest when error happen.
    - fake user agent in urlopen calls to prevent mad sysadmins restrictions on python useragent.
    - explicit error when the buildout configuration file is not there
    - use setuptools package_index.download helper funtion instead of directly urllib2 to avoid sourceforge download errors

1.0.19
-----------

    - distribute fix

1.0.18
--------

    - remove deprecationwarning

1.0.17
---------

    - remove deprecationwarning

1.0.16
-------


    - oups, left print

1.0.15
--------

    - let the default minilay be at lower priority among all

1.0.14
-------

    - desactivating updates manager for more tests.

-> 1.0.13
----------

    - Minitage now allows binaries to be used instead of compiling programs,
      in the gentoo -k way.
    - Minitage has now also an update manager to run udpate functions on
      upgrade.

1.0.5
-------

    - bugfix on url md5sum fragments

1.0.4
---------

    - make conditionnal weither we are offline or not the download in the get_from_cache function.

1.0.0 -> 1.0.3
------------------

    - x64 enlightments
    - add optionnal force switch to the download cache function


1.0
-----

    - some API adds like 'search_latest' and 'which'
    - bugfix in interfaces for configuration handling
    - buildout maker can be given an optionnal config to build
    - code stabilization and sync with other minitage components
    - official documentation on http://www.minitage.org


0.32
-----

    - Fetch by default over http

0.4.30
--------
    - Bind buildout newest mode with -u option


0.4.30
-------

    - do not delete directories but overwrite when the package src uri change.


0.4.29
-------

    - Make minitage lives on git

0.4.28
-------

    - Make minitage git aware both in recipes and in core.

0.4.27
-------

    - force setuptools version

0.4.26
-------

    - bugfix on common functions (API)

0.4.21
-------

    - quiet mode is now optionnal are there are numerous bugs with it.

0.4.8
-----------
    - Maintenance release

        - testruner
        - buildoutified
        - some refactor and code cleanings
        - logging is now better handled and your minimerge sessions will be as
          quiet as possible.

0.4.5
-----------
    - Bug in fetchers (not critical ...)

0.4.4
------------
    - Add an option (-f)
        - when set : fetch all before build
        - when not set : fetch and build each package one after another

0.4.2
------------
    - Remove the category check

0.4.2
------------
    - Remove the backtrace from the launcher when minimerge fails

0.4.1
------------
    - Release version

0.4_alpha12
------------
    - Fix scm type validator

0.4_alpha11
------------
    - bzr DVCS integration

0.4_alpha10
------------
    - Add support for variables in minibuilds setted in minitage configuration
      file. Use $name in minibuilds and set it in the [minitage.variables]
      section.

0.4_alpha9
-----------
    - reinforce buildout code

0.4_alpha8
-----------
    - restore previous version scheme

a0.4_alpha5
------------
    - add mercurial explicit dependency

0.4_alpha4
------------
    - remove old minilay

0.4_alpha1
------------

This is a pre release, minitage is working. But it is not empty from bugs.
Feel free to give your feedback :)

    - Minimerge totally rewritten in python
    - Support for conditionnal dependencies toward python version
    - Support for eggs in addition of site-packages added to the PYTHONPATH
    - Support for conditionnal (OS) dependencies
    - Lot of improvments on error handling
    - Logging mode
    - Configuration via a file is now possible


up to 0.3
----------

- not public, nothing to see there.



