Getting Started
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

To install, you can use PyPI: ::

    pip install pewtils

Or you can install from source: ::

    git clone https://github.com/pewresearch/pewtils.git
    cd pewtils
    python setup.py install

.. note::
    This is a Python 3 package. Though it is compatible with Python 2, many of its dependencies are \
    planning to drop support for earlier versions if they haven't already. We highly recommend \
    you upgrade to Python 3.

