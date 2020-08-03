Pewtils
===================================================================

Pewtils is a package of useful programming utilities developed at the Pew Research Center \
over the years. Most of the functions in Pewtils can be found in the root module, while a \
handful of submodules contain more specialized utilities for working with files, web \
resources, and regular expressions.

.. toctree::
   :maxdepth: 1
   :caption: Table of Contents:

   Core Functions <pewtils_core>
   HTTP Utilities <http>
   I/O Tools <io>
   Regex Patterns <regex>
   Examples <examples>

Installation
---------------

To install, you can use ``pip``:

    .. code-block:: bash

        pip install git+https://github.com/pewresearch/pewtils#egg=pewtils

Or you can install from source:

    .. code-block:: bash

        git clone https://github.com/pewresearch/pewtils.git
        cd pewtils
        python setup.py install

.. note::
    This is a Python 3 package. Though it is compatible with Python 2, many of its dependencies are \
    planning to drop support for earlier versions if they haven't already. We highly recommend \
    you upgrade to Python 3.

Installation Troubleshooting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using 64-bit Python
""""""""""""""""""""

Some of our libraries require the use of 64-bit Python. If you encounter errors during installation \
that are related to missing libraries, you may be using 32-bit Python. We recommend that you uninstall \
this version and switch to a 64-bit version instead. On Windows, these will be marked with ``x86-64``; you \
can find the latest 64-bit versions of Python `here <http://www.python.org/downloads>`_.

Installing ssdeep on Mac OS
""""""""""""""""""""""""""""

ssdeep is an optional dependency that can be used by the :py:func:`pewtils.get_hash` function in Pewtils. \
Installing it on Mac OS may involve a few additional steps, detailed below:

1. Install Homebrew

2. Install xcode

    .. code-block:: bash

        xcode-select --install

3. Install system dependencies

    .. code-block:: bash

        brew install pkg-config libffi libtool automake
        ln -s /usr/local/bin/glibtoolize /usr/local/bin/libtoolize

4. Install ssdeep with an additional flag to build the required libraries

    .. code-block:: bash

        BUILD_LIB=1 pip install ssdeep

5. If step 4 fails, you may need to redirect your system to the new libraries by setting the following flags:

    .. code-block:: bash

        export LIBTOOL=`which glibtool`
        export LIBTOOLIZE=`which glibtoolize`

    Do this and try step 4 again.

6. Now you should be able to run the main installation process detailed above.

